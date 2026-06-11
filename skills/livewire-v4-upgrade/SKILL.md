---
name: livewire-v4-upgrade
description: Walk a developer through upgrading a production Laravel app from Livewire v3 to v4. Use when the user asks to upgrade Livewire, mentions the Livewire 4 upgrade guide, or wants to assess whether an app is ready for Livewire v4. Audit-first - establishes the lay of the land before any dependency changes.
---

# Livewire v3 → v4 Upgrade

> **Draft v2.** Ground-truthed on two production apps: a modern one (Laravel 13, Flux Pro
> 2.14, class components, full-page routes, Pest - full upgrade completed and verified)
> and a long-lived hybrid (Laravel 12, Flux 2.4, 120 components, PHPUnit, much churn -
> Phases 0-2 plus legacy-binding remediation completed; stopped before the composer
> bump). Steps marked **[extrapolated]** have not yet been exercised on a real app -
> treat them with extra care and update this skill when you learn something.

This skill walks an upgrade in phases. Do not skip the audit phase - it is what tells you
whether you're in 20-minute-upgrade territory or two-day-migration territory. The official
upgrade guide describes what changed; this skill covers what the guide doesn't: invisible
config defaults, layouts with two jobs, stale agent context, and bugs the upgrade *surfaces*
but didn't cause.

## Phase 0 — Establish which world you're in

Before anything else, work out which app shape you have. They differ hugely in
upgrade surface:

1. **Modern shape**: full-page Livewire components (`Route::get('/x', Component::class)`),
   Flux UI, layout resolved via Livewire's config. The layout question (Phase 2) applies.
2. **Hybrid shape** (common in long-lived apps that migrated through Blade → Vue →
   Livewire or similar churn): *no* full-page component routes - pages are plain Blade
   consuming the layout as `<x-layouts.app>`, with Livewire components embedded via
   `<livewire:...>` / `@livewire(...)`. Livewire's layout config is never consulted at
   runtime, so the Phase 2 layout trap does not apply - but a *published*
   `config/livewire.php` makes the v3→v4 config key renames matter (Phase 3).
3. **Older shape** [extrapolated]: Blade pages using `@extends('layouts.app')` /
   `@section('content')` (or `'main'`). Audit greps all apply; layout trap doesn't.
   Mongrel variant seen in the field: `@extends()` *targeting a component file*
   (`@extends('components.layouts.app')`) leaves `$slot` undefined - that's pre-existing
   breakage, not something the upgrade caused or will fix.

Check: `grep -rn "Route::get.*Component\|Route::livewire" routes/` (**beware: matches
commented-out routes** - eyeball the hits) and `grep -rn "@extends" resources/views/ | head`.

Then gather context the docs can't give you:

- **Recent git log.** A Livewire upgrade often follows hot on the heels of a Laravel
  upgrade - look for tells like "Composer update to L13" in `git log --oneline -10`.
  If found, assume generated agent context is stale (next point).
- **CLAUDE.md / Boost guidelines may lie.** Verify the framework version from
  `composer.lock`, not from CLAUDE.md. (Real example: CLAUDE.md said Laravel 12;
  the lock file said 13.15.) If Boost is installed, a full `php artisan boost:install`
  regenerates the guidelines; `boost:update` has been observed doing nothing right
  after a framework upgrade.
- **If `config/livewire.php` is published, read it now.** Two keys decide your workload:
  `'legacy_model_binding' => true` is the single biggest blocker this skill knows about
  (dedicated section below - do not skip it); and the presence of the old `'layout'` key
  means the app leans on a config v4 renames wholesale - plan to re-publish fresh in
  Phase 3 and carry values across, never hand-rename keys in place.
- **Flux compatibility is a lock-file check, not a guess.** Flux ≥ 2.14.1 declares
  `"livewire/livewire": "^3.7.4|^4.0"`. Confirm with:
  `grep -A1 '"name": "livewire/flux"' composer.lock`. At or above the floor: no Flux
  work needed. **Below the floor, treat the Flux bump as a sibling task** with its own
  smoke test, not a checkbox: many minor versions of Flux is its own change surface,
  Flux Pro needs auth against the private `composer.fluxui.dev` repo (user-run), and
  long-lived apps may contain views written for a *newer* Flux than the lock file
  provides (field case: `<flux:button variant="warning">` blowing up Flux 2.4's button
  with `Unhandled match case` - two tests failing *before* any upgrade work began).
- **Laravel version constraint.** Settle it with a dry run before promising anything:
  `composer require livewire/livewire:^4.0 --dry-run` (verified fine against Laravel 13).

## Phase 1 — The audit sweep

Run every one of these before touching composer. Most will come back clean on a modern
app - the point is *knowing*, not assuming. (If your shell aborts on grep's no-match
exit code, append `| cat` to each.)

| What | Grep | If it hits |
|---|---|---|
| Unclosed component tags | `grep -rn '<livewire:' resources/views` then eyeball each for `/>` or a closing tag | v4 treats following content as slot content; component silently won't render. Close them. |
| `wire:model` modifiers | `grep -rEn 'wire:model\.(blur|change)' resources/views` | Behaviour changed silently - see "The wire:model changes, explained" below. |
| `wire:model` on containers | `grep -rEn '<(div\|section\|ul)[^>]*wire:model' resources/views` | Behaviour changed silently - see below. |
| `wire:scroll` | `grep -rn 'wire:scroll' resources/views` | Becomes `wire:navigate:scroll`. |
| `wire:transition` modifiers | `grep -rn 'wire:transition\.' resources/views` | Modifiers removed (now View Transitions API). Bare `wire:transition` still fine. |
| JS hooks | `grep -rn "Livewire.hook" resources/` | `commit`/`request` hooks deprecated → interceptors. Still work in v4; note for later. |
| `$js` usage | `grep -rn '\$js(' resources/` | Deprecated syntax; still works. Note for later. |
| `stream()` | `grep -rn '->stream(' app/` | Signature changed: v3 `$this->stream(to: '#el', content: 'Hi')` becomes v4 `$this->stream(content: 'Hi', el: '#el')` - `to:` renamed `el:`, content now first positionally. |
| Custom update route | `grep -rn 'setUpdateRoute' app/ bootstrap/` | Closure gains a `$path` param carrying the new hashed endpoint. |
| Hardcoded endpoint URLs | `grep -rn '/livewire/' app/ config/ resources/js/` | v4 prefix is `/livewire-{hash}/`. Also flag **infra outside the repo**: proxy, firewall, CDN rules referencing `/livewire/` paths. Ask the user - this is invisible from the repo. |
| Volt | `grep -rn 'Livewire\\\\Volt' app/ composer.json` | Follow the Volt section of the official guide. |
| Legacy model binding | `grep -n legacy_model_binding config/livewire.php` | If published and `true`, this is your biggest job - see the dedicated section below. |
| `wire:model.defer` | `grep -rn 'wire:model.defer' resources/views` | v2-era syntax, silently ignored since v3. Harmless, but delete it while you're here - it misleads readers about when the property syncs. |

Also inventory: component count (`find app/Livewire -name '*.php' | wc -l`), test files
using `Livewire::test` (these need no changes - the testing API is unchanged), and any
`WithFileUploads` usage (the upload endpoint moves with the hash prefix but Livewire
handles it internally - no action, just smoke-test uploads afterwards).

### The `wire:model` changes, explained

You will not have read the upgrade guide. These two changes are the most dangerous on
the list because they are *silent*: nothing errors, no console warning fires, no test
fails. The UI just behaves differently for real users.

**1. Modifiers now control client-side sync, not just network timing.**

In v3, modifiers like `.blur` and `.change` only decided when the *network request*
was sent. The input's value still synced into client-side state (`$wire.property`)
immediately, keystroke by keystroke. In v4 (firmed up in v4.1), those modifiers delay
the client-side sync as well - `$wire.property` doesn't update until the user blurs
or the change event fires.

Who gets hurt: anything reading client-side state while the user is mid-typing -
Alpine expressions bound to `$wire`, character counters, live previews, a disabled
submit button watching a field. They all go stale until blur. To keep exact v3
behaviour, add `.live` before the modifier:

| v3 | v4 equivalent |
|---|---|
| `wire:model.blur="title"` | `wire:model.live.blur="title"` |
| `wire:model.change="status"` | `wire:model.live.change="status"` |
| `wire:model.lazy="note"` | unchanged - `.lazy` is backwards compatible |
| `wire:model` / `wire:model.live` | unchanged |

Don't blanket-rewrite: the new behaviour may actually be what the UI wants (it's how
you build "only update when the user finishes typing" inputs now). Judge each hit -
is anything *consuming* this property client-side before the sync would fire? If the
property is only read server-side on submit, the change is harmless. Concrete check
per hit (field-tested - one command per view):

```
grep -En '\$wire|x-data|x-bind|x-show|x-text' path/to/the-view.blade.php
```

No matches means nothing reads the property mid-typing; verdict "harmless".

**2. `wire:model` on a container no longer hears its children.**

In v3, `wire:model` on a non-input element (a `div` wrapping a modal or accordion,
say) responded to `input`/`change` events bubbling up from form fields inside it.
Classic symptom this existed to fix: clearing an input inside a modal would bubble up
and close the modal. In v4 the binding only listens for events on the element itself
(as if `.self` were applied). If a container binding *relies* on hearing its children,
add `.deep` to restore v3 behaviour:

```blade
<div wire:model.deep="value">
    <input type="text">
</div>
```

Standard bindings on actual form controls (inputs, selects, textareas - including via
Flux components) are unaffected by both changes; in the ground-truthed app every
binding was either `.live` or a Flux form control, and the answer to both greps was
"no hits, nothing to do". That will often be the case - but *know*, don't assume.

### Legacy model binding - the blocker to find early

The v2-era shim letting `wire:model` write directly into Eloquent model attributes
(`wire:model="booking.holder_id"`) lives behind `legacy_model_binding` in v3 and is
**gone entirely in v4** - flag and feature both. On a long-lived app this can be the
bulk of the whole upgrade (it was, in the field run that added this section). Audit:

1. `grep -n legacy_model_binding config/livewire.php`. Published and `true`? Assume
   trouble until proven otherwise. Unpublished config means the v3 default (`false`)
   applies and the app is safe - skip the rest of this section.
2. Find every dot-notation binding:
   `grep -rEln 'wire:model[^=]*="[a-zA-Z_]+\.[a-zA-Z_]' resources/views`
   then **triage each root property in its component class** - the view alone cannot
   tell you. Plain arrays (`$form`, `$dates`) are fine; Eloquent models are the
   problem. Untyped `public $booking` properties need a read of `mount()` to classify.
   Expect mostly false alarms (field ratio: 14 views with dot-bindings, only 3 real
   model bindings).
3. Sneaky variant: a typed `?Collection` of Eloquent models with bindings like
   `wire:model="answers.{{ $key }}.body"` - the root being a Collection rather than a
   Model makes it easy to misclassify as a plain array.
4. Tests ride the same synthesizer: `grep -rEn "->set\('[a-z_]+\.[a-z_]" tests/` and
   triage the roots the same way (expect noise from `config()->set(...)`).
5. Orphaned-view false positives: a view full of model-style bindings may have **no
   component class at all** (leftover churn). Verify the class exists before
   refactoring a view that nothing renders.

**Remediation recipes** - three patterns covered every real case; all are applied on
v3, *before* any composer bump:

- **Model with many bound fields / computed values**: keep the model property for
  id/relations/display; add `public array $form = []`, fill it in `mount()`, copy back
  onto the model in `save()`. Rename together: view bindings, validation rule keys,
  `@error()` keys, and test `->set()` paths. And audit the whole element while you're
  in the view - non-`wire:model` attributes (a date-picker's `value="..."`) may read
  the same model attributes you're removing, and no test will catch those.
- **Single bound attribute**: one plain property, initialised in `mount()`, copied back
  on save. Smallest possible diff - prefer this when there's only one binding.
- **Collection of models**: convert to an array of `['id' => ..., 'field' => ...]`
  rows; actions re-find the model by id (`$this->question->answers()->findOrFail($id)`)
  instead of calling `->save()` on a bound model.

**Expect to write tests first.** Code still using magic model binding is old code, and
old code is undertested - in the field run, both methods needing refactor had zero
coverage. Budget for that; don't refactor blind.

**The proof step - cheap, decisive, reversible:** after remediating, flip
`legacy_model_binding => false` *while still on v3* and run the full suite. The flag
exists in v3, so you get v4's behaviour with v3's error messages -
`CannotBindToModelDataWithoutValidationRuleException` names the exact
component/property you missed. Green here means this blocker is genuinely cleared
before the bump, not hopefully cleared.

## Phase 2 — The layout trap (modern shape only)

This is the highest-risk change and the guide undersells it.

**If `config/livewire.php` is not published, the app runs on invisible defaults - and v4
changes the default layout** from `components.layouts.app` to `layouts::app`
(`resources/views/layouts/app.blade.php`). A bare composer bump breaks every full-page
component route at once.

**Before deciding to move the layout file, check whether it has two jobs:**

```
grep -rn '<x-layouts\.' resources/views
```

If anything (commonly auth pages) uses the layout as a Blade anonymous component, its
location under `resources/views/components/` is load-bearing for *Blade*, independent of
anything in Livewire's config. Moving it then requires `Blade::anonymousComponentPath()`
registration plus edits to every consuming view - a separate PR's worth of churn.

**Recommended resolution:** keep the file where it is and point v4 at it via config
(Phase 3). Smallest diff, no muscle-memory breakage, discoverable by any agent that
reads the published config. **Do not offer a symlink at the old path** - if the layout
is Blade-consumed, the symlink is load-bearing while looking optional, which is a trap
for whoever tidies up later.

**Close the coverage gap while you're here.** Plain-Blade pages (login, logged-out) are
exactly the pages component tests don't cover and exactly the ones consuming the layout
as `<x-layouts.app>`. If there's no test for them, propose adding one *now*, before the
upgrade, so a layout misresolution is a red test rather than a production surprise:

```php
it('renders the login page', function () {
    $this->get(route('login'))->assertOk();
});
```

(Hybrid-shape apps: field-confirmed that the layout trap doesn't apply - but run the
`<x-layouts.` grep anyway, because it's how you *prove* you're in the hybrid shape
rather than assume it.)

## Phase 3 — Baseline, bump, publish, configure

1. **Baseline first - the full suite, before *any* remediation edits, not just before
   the bump.** A field run baselined only the directly-affected test files, met 36
   unrelated failures late, and paid extra attribution work untangling them. A
   couple of minutes up front is cheaper. Record the failure *list*, not just the
   count - pre-existing failures are also your watch-list for Phase 4 (some may be
   *fixed* by the upgrade).
2. **The user runs the composer commands** (agents in sandboxes typically can't, and
   house permission hooks may block even `--dry-run` - expect the hand-off to start at
   the dry-run, not the real bump): `composer require livewire/livewire:^4.0`.
3. **Publish the real config; never hand-write or hand-rename it:**
   `php artisan livewire:publish --config` (command unchanged from v3). The published
   file contains options the upgrade guide never mentions (`release_token`, `payload`
   guards, `make_command.with`) - working from the real file means no guessed keys.
   If the app already had a published v3 config, *still* re-publish fresh and carry the
   old values across by diffing old against new - the v3→v4 key renames are wholesale
   (`layout` → `component_layout` and friends) and hand-renaming in place will miss
   new keys and changed defaults.
4. **Make the deliberate edits** to the published file. Team defaults:
   - `'component_layout' => 'components.layouts.app'` - dot-notation view names verified
     working in v4.3.1; keeps the layout where developers expect it (modern shape only).
   - `'make_command' => ['type' => 'class', 'emoji' => false, ...]` - we use class-based
     components and we do not put ⚡ in filenames.
5. `php artisan optimize:clear`.
6. **Full suite again.** On the ground-truthed app: 348/348 before and after, including
   `get(route(...))->assertOk()` tests that render full pages through the layout - which
   is what *proves* the layout config resolves. If your suite has no such test, add one
   rather than trusting the config edit.

Verified along the way: plain Blade views living in `resources/views/livewire/` do not
confuse v4's `component_locations` discovery - class components resolve as before.

## Phase 4 — Browser smoke test, console open

Tests can't see everything. Have the user (or a browser tool) walk:

- Login and logged-out pages (the Blade-consumed layout path)
- One full-page component route, poking something interactive (`wire:model.live` fields)
- A couple of `wire:navigate` links
- A file upload, if `WithFileUploads` is used anywhere (exercises the new hashed endpoint)
- **Browser console open throughout.**

**Treat v4's console warnings as a diagnostic, not noise.** v4 warns at bind time when
`wire:model` targets a property that doesn't exist on the component. What it surfaces
may be an ancient pre-existing bug masquerading as an upgrade regression. Triage:

1. Does the property exist on the component class? (Watch for near-misses like
   `newUserDefaultLocation` vs `newUserDefaultLocationId`.)
2. `git log -S 'the-binding-string'` - if the mismatch predates the upgrade, it's a
   surfaced bug, not a regression. Tell the user which it is; the distinction matters.
3. **Audit the whole element, not just the property name.** Real case: the same select
   also rendered `value="{{ $location->value }}"` against an Eloquent model with no
   `value` attribute - a copy-paste from an enum options loop. Mistakes travel in pairs.
4. Why tests missed it: `Livewire::test()->set()` sets properties directly, bypassing
   the view binding. A component test can pin the binding with
   `->assertSeeHtml('wire:model="theProperty"')`; only a browser test truly exercises it.

Note the binding warnings are also *statically findable before the upgrade* - the
Phase 1 greps plus a read of the component class catch them on v3, where they're
silent. And remember the mirror image: some failures on your Phase 3 baseline list
may simply *vanish* after the bump (field case: views written for a newer Flux than
the old lock file provided). Anything that goes red → green is worth a line in the
upgrade notes too - "fixed by upgrade" is information, not luck.

## Phase 5 — Aftercare

- Re-run `php artisan boost:install` so generated guidelines pick up the livewire/v4
  rules instead of coaching future agents in v3 idioms. (Composer's post-update hooks
  may have already done this - verify the version line in CLAUDE.md rather than assume.)
- **Check the deploy pipeline for build-time `route:cache` - field-confirmed 404 source.**
  v4's routes embed a hash derived from `APP_KEY` *at route-registration time*. If the
  Dockerfile or CI runs `route:cache` during image build - where secrets don't exist and
  `APP_KEY` is empty or a placeholder - the baked route table holds one hash while
  rendered pages emit another, and every Livewire asset/endpoint 404s. Audit:
  `grep -rn 'route:cache' Dockerfile docker/ .github/ .gitlab-ci.yml 2>/dev/null`.
  Fix: move `route:cache` to container start, next to the `config:cache` that's almost
  certainly already there (config is env-dependent; v4 made routes env-dependent too).
  Diagnosis pattern if you meet the 404 live: `curl -sI` the asset URL to confirm the
  app (not a proxy) is answering, then `php artisan route:list --path=livewire` in the
  container and compare its hash against the page's asset URLs. Treacherous detail from
  the field: this was *invisible on QA* because the QA image target happened to run
  `optimize:clear` last, wiping the poisoned cache - prod was the only environment that
  kept it. And it's a latent pre-v4 pattern: v3's static Livewire paths made build-time
  route caching safe by accident, so expect it across a whole fleet of apps sharing a
  Dockerfile lineage. A manual `route:clear` in the running container is a stopgap only -
  the next deploy or container reschedule restores the stale cache from the image.
- Confirm with the user whether anything *outside* the repo references `/livewire/`
  paths (proxy/firewall/CDN rules) - the `{hash}` prefix change breaks those silently.
- Optional, when convenient rather than now: migrate deprecated `$js('name', fn)` to
  the v4 form `$wire.$js.name = fn`, and `Livewire.hook('commit'|'request', ...)` to the
  new interceptors (`Livewire.interceptMessage(...)` / `Livewire.interceptRequest(...)` -
  see the v4 JavaScript docs for the callback shapes); consider `Route::livewire()` for
  full-page routes. All the old forms still work in v4 - this is tidiness, not necessity.
- Deferred-but-still-true: anything the audit found that "still works in v4" should be
  recorded somewhere it won't be forgotten (issue tracker), not left as tribal memory.

## Field notes for agents (environment gotchas)

- **Temp or copied checkouts break Lando**: `.lando.yml` names an app whose container
  was built for a different directory (`chdir to cwd ... no such file or directory`).
  Fallback that worked: bare `php artisan test` - check whether phpunit.xml already
  uses in-memory sqlite before assuming you need the container at all.
- **`CACHE_STORE=array` does not cover direct `Redis::` facade calls** (e.g. a lock
  acquired in `mount()`). Field fix: a throwaway
  `docker run -d --rm -p 6379:6379 redis:alpine` plus `REDIS_HOST=127.0.0.1` prefixed
  to the test command - works because phpdotenv doesn't override real environment
  variables. Tell the user about any container you leave running.
- **Expect house-style permission hooks** - blocked composer commands, blocked
  raw-database test assertions. They are conventions doing their job, not obstacles:
  ask the user, never route around them.

## Things this skill does not yet know

Honest gaps, to be filled by future runs:

- Anything past the composer bump on the *hybrid* shape: v4 runtime there, `wire:poll`
  under v4 (five views waiting in the field app), the hashed endpoint behind proxies.
- Whether Flux ≥ 2.14 actually adds the button `warning` variant - assumed when
  predicting two pre-existing failures would be fixed by the Flux bump; unconfirmed.
- The pure `@extends('layouts.app')` older shape end-to-end (everything marked
  [extrapolated]).
- Apps using islands, lazy/deferred components, or pagination themes under v4 - no
  real-world observations yet.
- Whether `smart_wire_keys => true` (new v4 default) bites deeply nested components
  in practice - neither ground-truth app had issues, but neither nests deeply.
