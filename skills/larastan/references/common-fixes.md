# Common PHPStan Fixes for Laravel Projects

Detailed examples of fixes for errors that surface at each level. These are all patterns encountered in real Laravel projects.

## Casts declared in the `casts()` method are invisible by default (any level)

**What happens:** A cast declared in the Laravel 11+ `casts()` *method* (rather than the `protected $casts` property) is not seen by Larastan in its default configuration. The attribute is typed as the raw column type instead, so an enum-cast attribute is `string`, and `$model->status->value` errors with `property.nonObject` ("Cannot access property $value on string"). Enum comparisons can also produce bogus `identical.alwaysFalse` errors.

Easy to misdiagnose because *some* casts appear to work: boolean and datetime attributes come back correctly typed. That information comes from Larastan's migration parsing and its built-in timestamp handling, not from `casts()`. Only casts that *transform* the column type (enums, custom cast classes) expose the gap.

**Root cause** (verified on larastan 3.10.0 / phpstan 2.2.8 / Laravel 13.26 by reading `vendor/larastan/larastan/src/Properties/ModelCastHelper.php` and the framework's `HasAttributes` trait):

1. Larastan discovers casts by instantiating the model with `newInstanceWithoutConstructor()` and calling `getCasts()` on it.
2. Since Laravel 11 (where the `casts()` method was introduced), the framework merges `casts()` into `$this->casts` inside `initializeHasAttributes()`, a trait initializer run by the Model **constructor**. `getCasts()` itself only reads `$this->casts`.
3. The constructor was skipped, so the merge never ran: `getCasts()` returns only the `$casts` property, and anything declared in the `casts()` method is lost.
4. Larastan's static fallback reads the *declared return type* of `casts()`, and the conventional signatures (`: array`, `@return array<string, string>`) are not constant arrays, so it learns nothing from them either.

**Fix:** enable Larastan's AST parsing of the `casts()` method body:

```yaml
parameters:
    parseModelCastsMethod: true
```

Verified: with the flag on, the enum-cast attribute types as the enum, and `->value` narrows to the literal union of the case values. The flag is documented in Larastan's docs/custom-config-parameters.md and is off by default because parsing the model source file is slower. This is a deliberate, documented trade-off upstream, not a bug to report.

**Fallback** if the flag can't be used for some reason: a targeted `@property` on the model class docblock (never a global ignore):

```php
/** @property ActivityAction $action */
class Activity extends Model
```

**Not chased:** whether upstream would consider flipping the default, and whether the dead runtime path (point 1 above can never see `casts()` on Laravel 11+) is known to the Larastan maintainers in those terms.

## Level 5 fixes

### Enum comparisons through collections (`identical.alwaysFalse` / `notIdentical.alwaysTrue`)

**What happens:** Collection operations like `groupBy()`, `last()`, `filter()` lose the concrete model type. So `$item->event_type` is typed as `string` (the DB column type) instead of the cast enum. PHPStan then flags `$item->event_type === SomeEnum::Value` as "always false" because it thinks you're comparing a string to an enum.

**How to verify it's a false positive:** Check the model's `casts()` method. If the field is cast to the enum, the comparison works correctly at runtime.

**Fix:** Inline ignore with an explanation:
```php
if ($latest->event_type !== SkillHistoryEvent::Removed) { /** @phpstan-ignore notIdentical.alwaysTrue (event_type is cast to enum but collection groupBy/last loses the SkillHistory type) */
```

**Why not global ignore:** The same identifier fires for genuinely wrong comparisons — e.g. code that compares a raw string from `request()->input()` to an enum without casting. That's a real bug.

### Relationship `create()` / `firstOrCreate()` return types (`return.type`)

**What happens:** `$relation->create([...])` returns `Illuminate\Database\Eloquent\Model`, not the concrete type. If the method declares a concrete return type, PHPStan flags the mismatch.

**Fix:** Extract to a typed variable:
```php
/** @var CoachMessage $message */
$message = $conversation->messages()->create([
    'role' => CoachMessageRole::Assistant,
    'content' => $responseText,
]);

return $message;
```

### Pivot model relationship access (`argument.type`)

**What happens:** Accessing a relationship through a custom pivot model (e.g. `$enrollment->trainingCourse`) returns `Model|null` instead of the concrete related model type. When this is passed to a method expecting the concrete type, PHPStan flags it.

**Fix:** Same `@var` pattern:
```php
/** @var \App\Models\TrainingCourse $course */
$course = $enrollment->trainingCourse;
Mail::to($enrollment->user)->send(new TrainingRequestApproved($course, Auth::user()));
```

### Closure type hints on collections (`argument.type`)

**What happens:** A `->map()` closure with a concrete type hint like `fn (User $user)` conflicts with the collection's generic type of `Model`.

**Fix — option A:** Leave parameter untyped, add `@var` inside:
```php
$users->map(function ($user) use ($skills) { /** @var User $user */
    $row = [$user->full_name];
    // ...
});
```

**Fix — option B:** Inline ignore (better for arrow functions):
```php
$collection->map(fn (CoachMessage $msg) => [ /** @phpstan-ignore argument.type (collection loses concrete type) */
    'role' => $msg->role->value,
    'content' => $msg->content,
]);
```

**Trap to avoid:** Do NOT "fix" by adding a concrete type hint to the closure parameter — this creates a *new* `argument.type` error because PHPStan sees `Closure(User)` being passed where `callable(Model)` is expected.

### Unused return types (`return.unusedType`)

**What happens:** A union return type like `RedirectResponse|LivewireRedirector` includes a type that the method never actually returns. Often left over from copy-paste or a refactor that removed one code path.

**Fix:** Remove the unused type from the declaration and clean up the `use` import:
```php
// Before
use Livewire\Features\SupportRedirects\Redirector as LivewireRedirector;
private function getSuccessRedirect(): RedirectResponse|LivewireRedirector

// After
private function getSuccessRedirect(): RedirectResponse
```

Check all methods in the file that use the removed type — they likely need the same cleanup.

### PHPDoc `@return` shape mismatches (`return.type`)

**What happens:** A method's PHPDoc `@return` declares an array shape that doesn't match what the code actually returns. Common when a key was added to the returned array but the PHPDoc wasn't updated.

**Fix:** Update the PHPDoc to match the actual return:
```php
// Before — missing eventText key
/** @return array<int, array{month: string, points: int, events: array<string>}> */

// After — matches what the code actually builds
/** @return array<int, array{month: string, points: int, events: array<string>, eventText: string}> */
```

Always check which is correct — the PHPDoc or the code. Sometimes the PHPDoc is the intended contract and the code has a bug.

### Method not found through closures (`method.notFound`)

**What happens:** A `->map()` closure calls a method on a model, but the collection's generic type is `Model` so PHPStan doesn't know the method exists.

**Fix:** `@var` annotation inside the closure (same as the property pattern):
```php
$users->map(function ($user) use ($skills) { /** @var User $user */
    $level = $user->getSkillLevel($skill);
    // ...
});
```

**Why not globally ignore `method.notFound` on `Model::`:** Unlike properties (which are almost always dynamic attributes), a missing method call is more likely a real typo. Globally ignoring it would hide bugs like `$user->getSkilLevel($skill)` (typo in method name).
