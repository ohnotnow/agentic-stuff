---
name: larastan
description: |
  Set up and run PHPStan/Larastan static analysis on Laravel projects with sensible defaults that filter out Laravel magic noise. Iteratively fix real issues and progressively increase analysis levels. Use when the user asks to: run phpstan, run larastan, set up static analysis, check code quality with phpstan, add phpstan/larastan to a project, or "analyse my code". Also use when the user mentions phpstan.neon configuration.
---

# Larastan - Static Analysis for Laravel

Run PHPStan/Larastan on a Laravel project, filtering out Laravel magic false positives so only genuine issues are surfaced.

## Why the noise filtering matters

PHPStan doesn't understand Laravel's magic — Eloquent attribute accessors, casts, scopes on relations, Livewire `#[Computed]` properties, Socialite contracts, `withCount()` dynamic attributes, and closures that lose concrete model types. Without filtering, 90%+ of errors at levels 1-5 are false positives. This makes developers dismiss PHPStan as useless for Laravel — which is a shame, because the remaining errors are genuinely valuable.

## Process

### 1. Check Larastan is installed

Check `composer.json` for `larastan/larastan`. If missing, offer to install:

```bash
composer require --dev "larastan/larastan:^3.0"
```

### 2. Create or update phpstan.neon

Check if `phpstan.neon` exists in the project root.

- **If missing**: Create one starting at level 1 using the template in [references/phpstan-neon-template.md](references/phpstan-neon-template.md)
- **If exists**: Read it and check the current level and ignoreErrors config. Suggest adding any missing noise filters from the template.

The template includes `ignoreErrors` rules for known Laravel magic patterns. See the reference file for the full template with explanations.

### 3. Fix annotation-based errors first

Before running the main analysis, some Laravel magic patterns are best fixed with lightweight PHPDoc annotations rather than ignored. These annotations also help IDEs, so they have value beyond PHPStan:

**API Resources** — Add `@mixin` to tell PHPStan which model backs the resource:
```php
/** @mixin \App\Models\User */
class UserResource extends JsonResource
```

If the resource accesses `Attribute::get()` style accessors or `$this->pivot`, add `@property` too:
```php
/**
 * @mixin \App\Models\Skill
 * @property \App\Models\SkillUser $pivot
 */
class SkillResource extends JsonResource
```

**Livewire `#[Computed]` properties** — Add `@property` annotations for computed methods accessed as `$this->propertyName`:
```php
/**
 * @property \App\Models\User $user
 * @property array $skillDistribution
 */
class SkillsDashboard extends Component
```

Scan all Livewire components for `#[Computed]` methods and add the corresponding `@property` PHPDoc to each class. Only annotate computed properties actually accessed as `$this->property` within the class (PHPStan doesn't analyse Blade templates).

### 4. Run PHPStan and categorise errors

```bash
./vendor/bin/phpstan analyse --memory-limit=2G
```

Categorise each error into one of three buckets — not two:

- **Global ignore** — Patterns that are *always* false positives in any Laravel project (safe for `ignoreErrors` in the shared template)
- **Inline ignore / annotation fix** — Patterns that *look* like false positives but share an identifier with real bugs (use `@phpstan-ignore` on the specific line, or `@var` / `@return` PHPDoc annotations)
- **Real issue** — Genuine type mismatches, missing methods, logic bugs (fix the code)

**The distinction between the first two buckets is critical.** A global ignore that's too broad will hide real bugs. When in doubt, use an inline ignore — it's more work per occurrence but much safer.

See [references/global-vs-inline-decision-guide.md](references/global-vs-inline-decision-guide.md) for a detailed breakdown of which patterns are safe to ignore globally and which need per-line treatment.

Common real issues by level:

| Level | What surfaces |
|-------|---------------|
| 1-2 | Undefined properties/methods (after filtering magic) |
| 3-4 | Return type mismatches, basic type checking |
| 5 | Argument types, match exhaustiveness, nullsafe redundancy, dead comparisons |
| 6+ | Stricter type checks, missing typehints — much noisier, diminishing returns |

### 5. Fix real issues

Work through genuine issues. Common fixes are documented in [references/common-fixes.md](references/common-fixes.md). Here is a summary:

#### Safe to ignore globally (add to `ignoreErrors` in phpstan.neon)

- **`nullsafe.neverNull`** — Larastan incorrectly claims `?->` is unnecessary for nullable relationships, `first()` / `tryFrom()` returns, etc. An unnecessary `?->` is harmless code, not a bug. Safe to ignore globally.
- **`property.notFound` on `Illuminate\Database\Eloquent\Model::`** — Dynamic properties accessed through collection closures where the concrete type is lost. Safe because the identifier + message pattern is narrow enough.
- **`argument.unresolvableType`** — Genuinely unresolvable generics in Laravel's internals. Safe globally.

#### STOP AND ASK the user — do not ignore globally

- **`identical.alwaysFalse` / `notIdentical.alwaysTrue`** — These fire when comparing an enum to a value that PHPStan thinks is a `string`. This happens as a false positive when collection operations lose the concrete model type (so Larastan sees the raw DB column type instead of the cast enum). **But the same identifiers also catch real bugs** — e.g. genuinely comparing a raw string to an enum without casting, which silently fails. You must read the code and check: is the comparison going through a model with a proper cast, or is it raw? **Use inline `@phpstan-ignore` with a comment explaining why, never a global ignore.**

- **`match.unhandled`** — Do not blindly add a `default` arm. PHPStan reports this when the matched value is `mixed` even though the match is intentionally exhaustive. Adding `default` silences PHP's `UnhandledMatchError` — which is often the *desired* safety net. Show the user the match statement. If deliberate, use inline `@phpstan-ignore match.unhandled` on that specific line.

- **`method.notFound` on `Model::`** — We globally ignore *properties* on `Model::` (dynamic attributes), but *methods* are different. A missing method is more likely a real typo. If it's caused by a closure losing the concrete type, fix with a `@var` annotation inside the closure body. Do not add a broad method ignore.

- **`argument.type` with concrete types in closures** — When a `->map()` closure has a concrete type hint like `fn (User $user)` but the collection's generic is `Model`, PHPStan flags the mismatch. **Do not** fix by adding the type hint to the closure parameter — this can *create* a new error. Instead, leave the parameter untyped and add `/** @var User $user */` inside the closure body, or use an inline `@phpstan-ignore`.

#### Fix in the code

- **`return.type`** — Fix the return type declaration, the PHPDoc `@return`, or the actual return value. Check which one is wrong — the PHPDoc might simply be out of date (missing a key in an array shape, or listing a type the method never actually returns).
- **`return.unusedType`** — A type in a union return type that's never actually returned. Usually harmless cruft from copy-paste or refactoring. Remove the unused type from the declaration and clean up any dead `use` imports.
- **Relationship `create()` / `firstOrCreate()` return types** — These return `Model` not the concrete type. Fix with a `@var` annotation:
  ```php
  /** @var CoachMessage $message */
  $message = $conversation->messages()->create([...]);
  return $message;
  ```
- **Pivot model relationship access** — Accessing `$pivotModel->someRelationship` returns `Model|null` instead of the concrete type. Same fix — `@var` annotation before use.

If new magic noise patterns appear that aren't in the template, **present them to the user before adding to `ignoreErrors`**. Explain what the pattern catches and what it might hide. Let the user decide if it belongs in the global config or as an inline ignore.

### 6. Bump the level

Once the current level passes cleanly, suggest bumping the level by 1 in `phpstan.neon`. Re-run and repeat the categorise/fix cycle.

**Recommended stopping point**: Level 5 is the sweet spot for most Laravel projects. It catches real bugs (type mismatches, dead code, exhaustiveness) without drowning in noise. Levels 6+ add diminishing returns with increasing annotation burden.

Tell the user the recommended stopping point but let them decide.

### 7. Legacy codebase considerations

Older Laravel projects (especially those upgraded through many Laravel/PHP versions) deserve extra caution:

- **Don't assume false positive.** In a greenfield project, a string-vs-enum comparison is almost certainly a lost-type false positive. In an older codebase, it might be a genuine bug where a cast was never added, or a column was changed but the comparison wasn't updated. **Read the model's `casts()` before dismissing.**
- **Return types accumulate cruft.** Union return types like `RedirectResponse|LivewireRedirector` can hang around for years after a refactor removed one code path. `return.unusedType` errors in legacy code are usually genuine cleanup opportunities.
- **PHPDoc `@return` shapes drift.** When methods evolve (adding a key to a returned array, changing a type), the PHPDoc often doesn't get updated. Treat `return.type` errors as a prompt to check which is correct — the PHPDoc or the code — rather than assuming one or the other.

### 8. When explaining to the user

If the user asks why errors are being ignored or what the point is:

- PHPStan catches bugs without running code — it's complementary to tests, not a replacement
- Laravel uses "magic" (dynamic properties, facades, scopes) that PHPStan can't understand
- Larastan adds Laravel-specific intelligence but doesn't cover everything
- The `ignoreErrors` config filters known false positives so you only see real issues
- The `@mixin` and `@property` annotations help both PHPStan and your IDE — zero runtime impact
- The progressive level approach means you start with easy wins and gradually tighten
- Inline `@phpstan-ignore` comments are preferred over global ignores for patterns that *could* hide real bugs — it's more typing but safer
