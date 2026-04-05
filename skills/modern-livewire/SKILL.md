---
name: modern-livewire
description: How we write Livewire components - principles, patterns, and testing. Use when building or reviewing Livewire components, tests, or Blade views.
---

# Modern Livewire

How we write Livewire components. Principles first, then patterns, then testing.

---

## Principles

> The right mindset prevents over-engineering before it starts.

### 1. Trust the Framework

Laravel validation works. Livewire form binding works. Eloquent relationships work. Don't rebuild what's already there.

**Ask yourself:** "Does the framework already handle this?"

```php
// The framework handles this - you don't need to
public function save(): void
{
    $this->validate(); // Laravel validates
    $this->form->save(); // Done
}
```

### 2. Test Behaviour, Not Implementation

Test what users see and what data changes. If a test would break when you refactor (without changing behaviour), it's testing implementation details.

```php
// Test behaviour: what changed in the world?
it('creates a new role', function () {
    Livewire::test(RolesList::class)
        ->set('roleName', 'Editor')
        ->call('saveRole');

    expect(Role::where('name', 'Editor')->exists())->toBeTrue();
});

// Not implementation: what happened inside the component?
// (Don't test that $isModalOpen became false)
```

### 3. Let Errors Surface

Don't hide problems with defensive guards and silent returns. On a trusted network with error monitoring, exceptions are helpful.

```php
// Let it fail - this tells you something's wrong
public function updateLevel(int $skillId, SkillLevel $level): void
{
    $this->user->skills()->updateExistingPivot($skillId, [
        'level' => $level->value,
    ]);
}
```

### 4. Simple Over Clever

Three similar lines are better than a premature abstraction. A button that's always visible is simpler than one that tracks whether it "should" be visible.

### 5. The Happy Path is Enough (Usually)

Trusted staff won't manipulate URLs. Students might - there's always one who'll try it on. Test accordingly.

### Questions Before You Code

1. Does the framework already handle this?
2. Am I testing what users see, or component internals?
3. Would this test break if I refactored without changing behaviour?
4. Am I adding this "just in case"?
5. Who would actually do this? Trusted staff or students?

---

## Component Patterns

### Named Modals with Flux Facade

Don't use boolean properties for modal state. Use the Flux facade.

```php
use Flux\Flux;

// Open
Flux::modal('item-editor')->show();

// Close (typically after saving)
Flux::modal('item-editor')->close();
```

Cancel buttons close directly from Alpine - no server roundtrip:
```blade
<flux:button x-on:click="$flux.modal('item-editor').close()">Cancel</flux:button>
```

No `$showModal` properties. No `cancelEdit()` methods that just toggle a boolean.

### Form State - Single Array

For components with a handful of fields, use a single array:

```php
public array $editing = [
    'id' => null,
    'name' => '',
    'description' => '',
    'cost' => '',
    'is_active' => false,
];

public function openCreate(): void {
    $this->reset('editing');
}

public function openEdit(int $id): void {
    $model = Model::findOrFail($id);
    $this->editing = $model->toArray();
}
```

```blade
<flux:input wire:model="editing.name" label="Name" />
```

Validation uses dot notation:
```php
$this->validate([
    'editing.name' => ['required', 'string', 'max:255'],
    'editing.description' => ['nullable', 'string'],
]);
```

For components with many fields, extract to a Livewire Form object:

```php
class CreatePostComponent extends Component
{
    public PostForm $form;

    public function save(): void
    {
        $post = $this->form->save();
        Flux::toast('Post created');
        $this->redirectRoute('posts.edit', $post);
    }
}
```

### Create/Update - findOrNew + fill + save

```php
$model = Model::findOrNew($this->editing['id']);
$model->fill($this->editing)->save();

Flux::toast('Saved.', variant: 'success');
```

`fill()` only uses `$fillable` attributes - non-fillable keys like `id`, `created_at` are automatically ignored.

If you need separate messages:
```php
$action = $model->wasRecentlyCreated ? 'created' : 'updated';
Flux::toast("Item {$action}.", variant: 'success');
```

### Model Mutators for Data Normalisation

When form fields send empty strings but the database expects `null`:

```php
// In your Model
protected function supplierId(): Attribute
{
    return Attribute::make(
        set: fn ($value) => $value ?: null,
    );
}
```

### Sentinel Values

Use `null` for "creating new", not `-1` or other magic numbers:
```php
public ?int $editingId = null;
if ($this->editingId === null) { /* create */ }
```

### Event Dispatching

```php
$this->dispatch('item-saved');
$this->dispatch('refresh')->to(OtherComponent::class);
```

### wire:model Behaviour

Livewire defers `wire:model` by default. Use `.live` for real-time, `.blur` for on-blur:

| Modifier | Behaviour |
|---|---|
| `wire:model` | Deferred (default) |
| `wire:model.live` | Real-time sync |
| `wire:model.blur` | Sync on blur |

### Unnecessary Ternaries

```php
// Unnecessary - (string) null already gives ''
$this->editing['supplier_id'] = (string) $model->supplier_id;

// Only use ?: null if the distinction actually matters
'cost' => $this->editing['cost'],
```

---

## Testing

### Test Behaviour, Not Mechanics

```php
// GOOD: tests what changed in the world
it('creates a role', function () {
    Livewire::test(RoleManager::class)
        ->call('openCreateModal')
        ->set('roleName', 'Editor')
        ->call('save')
        ->assertHasNoErrors();

    expect(Role::where('name', 'Editor')->exists())->toBeTrue();
});

// BAD: tests component internals
->assertSet('isCreating', true)
->assertSet('showModal', false)
->call('resetModal')
```

### Auth via Route, Not Component

```php
// Test the full HTTP stack including middleware
$this->actingAs($user)->get(route('admin.items'))->assertForbidden();

// Not the component's internal auth check
// Livewire::test(AdminItems::class)->assertForbidden();
```

### Eloquent Assertions

```php
expect(Item::find($item->id))->toBeNull();
expect($item->users()->count())->toBe(0);

// Not raw database assertions
// $this->assertDatabaseMissing('items', ['id' => $item->id]);
```

### Validation - Test That It Exists, Not Every Rule

```php
it('validates required fields', function () {
    Livewire::test(CreateUser::class)
        ->set('name', '')
        ->set('email', 'invalid')
        ->call('save')
        ->assertHasErrors(['name', 'email']);

    expect(User::count())->toBe(0);
});
```

### The Refactoring Test

Before committing a test, ask: **"If I refactored the component tomorrow without changing behaviour, would this test break?"**

- If yes - you're testing implementation. Reconsider.
- If no - you're testing behaviour. Good.

### Staff vs Students

- **Staff apps on trusted LAN:** Happy path is enough. Don't test URL manipulation.
- **Student-facing features:** Test that students can't access others' data, can't manipulate IDs in forms.

---

## Detailed Examples

For more thorough side-by-side comparisons:

- **[Component Examples](component-examples.md)** - Form delegation, validation, modal patterns, Blade templates
- **[Test Examples](test-examples.md)** - Behaviour vs implementation tests, the refactoring test, staff vs student apps
