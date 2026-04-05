---
name: ui-to-flux
description: Migrate older Laravel apps to modern Livewire + Flux UI. Source-framework mappings, checklists, and gotchas. References flux-ui and modern-livewire skills for target patterns.
---

# UI to Flux Migration

Migrate older Laravel applications to modern Livewire + Flux UI. This skill covers **what to change and in what order**. For the target patterns themselves, see:

- **flux-ui** skill - Flux component syntax and conventions
- **modern-livewire** skill - Livewire component patterns and testing

## Approach

1. **Templates only first** - don't convert routes to Livewire components unless explicitly asked
2. **Layout first**, then major components, then refinements
3. Work systematically - one template at a time
4. If laravel-boost MCP tool is available, use it for up-to-date Flux documentation

---

## Source Framework Mappings

### From Bulma
| Bulma | Flux UI |
|-------|---------|
| `table.table` | `<flux:table>` with columns/rows wrappers |
| `button.button` | `<flux:button>` |
| `input.input` | `<flux:input label="...">` |
| `field` / `control` | `<flux:input label="..." description="...">` |
| `columns` / `column` | CSS Grid (`grid grid-cols-1 lg:grid-cols-2 gap-6`) |
| `box` | `<flux:card>` |
| `title` / `subtitle` | `<flux:heading>` with sizes |
| `notification` | `<flux:callout>` |

### From Bootstrap
| Bootstrap | Flux UI |
|-----------|---------|
| `table` | `<flux:table>` with columns/rows wrappers |
| `btn btn-primary` | `<flux:button variant="primary">` |
| `form-control` | `<flux:input label="...">` |
| `form-group` / `form-label` | `<flux:input label="..." description="...">` |
| `row` / `col-*` | CSS Grid (`grid grid-cols-1 lg:grid-cols-2 gap-6`) |
| `card` | `<flux:card>` |
| `alert` | `<flux:callout>` |

### From plain Tailwind
Replace hand-styled HTML with Flux components. The main change is deleting Tailwind classes that Flux now handles internally.

---

## Layout & Structure

- Remove complex sidebars for simple apps - use clean `<main>` with responsive containers
- Use `w-full md:w-3/4 mx-auto` for main content containers
- Move shared header elements to layout files
- Use `<flux:separator class="mb-6" />` instead of `<hr>`
- Update `@extends` / `@section('content')` to `<x-layouts.app>` component syntax

## Attribute Binding

Replace Blade directives in attributes with Laravel binding syntax:

```blade
{{-- OLD --}}
class="@if ($condition) some-classes @endif"

{{-- NEW --}}
:class="$condition ? 'some-classes' : ''"
```

This applies to all attributes: `:class`, `:title`, `:disabled`, `:href`, etc.

## UI Refinements

- **Delete buttons**: Icon-only with `icon="trash"`, `variant="danger"`, `size="sm"`, `inset="top bottom"`
- **Search inputs**: Constrain width with `max-w-md` wrapper, add magnifying glass icon
- **Input groups**: Use `iconTrailing` slots for buttons attached to inputs
- **Spacing**: Margin classes following "We Style, You Space" (see flux-ui skill)

## Livewire Integration

- Ensure `@livewireStyles` in `<head>` and `@livewireScripts` before `</body>`
- Remove `.prevent` modifiers from `wire:click` that may interfere with Flux buttons
- Use `wire:model.live` for real-time filtering/search (see modern-livewire skill for wire:model behaviour)

## Common Issues

| Problem | Fix |
|---------|-----|
| Livewire functionality breaks | Check for missing scripts, remove `.prevent` modifiers |
| Layout too wide | Add responsive containers with `max-w-5xl` |
| Buttons too aggressive | Use icon-only delete buttons with subtle styling |
| Input groups disconnected | Use Flux's `iconTrailing` slot pattern |
| "Component not found" errors | Check `vendor/livewire/flux-pro/` exists - run `php artisan flux:activate` if not |

---

## Migration Checklists

### Component (.php)
- [ ] Add `use Flux\Flux;` import
- [ ] Remove boolean modal properties (`$showEditModal`, etc.)
- [ ] Remove cancel/close methods (if only toggling boolean)
- [ ] Replace modal show/close with `Flux::modal('name')->show()/close()`
- [ ] Replace `$this->emit()` with `$this->dispatch()`
- [ ] Consolidate form properties to single array or Form object
- [ ] Simplify create/update with `findOrNew` + `fill` + `save`
- [ ] Update namespace if still `App\Http\Livewire`

### Template (.blade.php)
- [ ] Change `wire:model="showModal"` to `name="modal-name"` on modals
- [ ] Change cancel buttons to `x-on:click="$flux.modal('name').close()"`
- [ ] Add `wire:key` to loop items
- [ ] Check `wire:model` - add `.live` if real-time updates needed
- [ ] Update `@extends`/`@section` to `<x-layouts.app>`

### Tests
- [ ] Auth tests via route, not `Livewire::test()->assertForbidden()`
- [ ] Eloquent assertions instead of `assertDatabaseMissing()`
- [ ] Remove modal state assertions
- [ ] Remove tests for removed cancel/close methods
- [ ] Update property paths if using array state (`editing.name`)
- [ ] Keep all functional assertions (data state, validation, side effects)
