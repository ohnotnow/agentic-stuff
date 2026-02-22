# Global Ignore vs Inline Ignore — Decision Guide

When categorising a PHPStan error as noise, the key question is: **does the identifier + message pattern uniquely identify false positives, or could it also match real bugs?**

## Safe for global `ignoreErrors`

These patterns are narrow enough that they only match Laravel magic false positives:

| Identifier | Message pattern | Why it's safe |
|------------|----------------|---------------|
| `nullsafe.neverNull` | *(no message needed)* | An unnecessary `?->` is harmless code, never a bug |
| `property.notFound` | `#Illuminate\\Database\\Eloquent\\Model::#` | Dynamic model properties in closures — always magic |
| `property.notFound` | `#Illuminate\\Database\\Eloquent\\Relations\\Pivot::#` | Custom pivot properties — always magic |
| `argument.type` | `#Illuminate\\Database\\Eloquent\\Model given#` | Closure passes concrete model but collection expects `Model` |
| `assign.propertyType` | `#does not accept Illuminate\\Database\\Eloquent\\Model#` | Same lost-type pattern on assignment |
| `argument.unresolvableType` | `#contains unresolvable type#` | Laravel internal generics — nothing actionable |
| `method.nonObject` | `#Cannot call method .+\(\) on string#` | Cast columns (Carbon, enums) seen as strings |
| `property.nonObject` | `#Cannot access property \$value on (string\|int)#` | Enum cast value access seen as raw type |
| `property.notFound` | `#Laravel\\Socialite\\Contracts\\User::#` | Socialite returns interface, code uses concrete |
| `method.notFound` | `#Laravel\\Socialite\\Contracts\\Provider::with\(\)#` | Same Socialite contract mismatch |

## Must be inline `@phpstan-ignore` (NEVER global)

These identifiers catch both false positives and real bugs. Globally ignoring them would hide genuine issues:

| Identifier | Why it's dangerous to ignore globally |
|------------|--------------------------------------|
| `identical.alwaysFalse` | Catches real bugs where `$rawString === SomeEnum::Value` silently fails. Only a false positive when the concrete model type is lost through collection operations and the column has a proper cast. |
| `notIdentical.alwaysTrue` | Same as above but for `!==` comparisons. |
| `match.unhandled` | A genuinely incomplete match is a real bug. Only a false positive when the matched value is `mixed` due to lost types. |
| `method.notFound` on `Model::` | A missing method call is more likely a real typo than a missing property. Properties are dynamic (attributes), methods generally aren't. |
| `argument.type` with `Model\|null` | Could hide cases where the wrong nullable type is passed from a relationship. Narrower than the `Model given` pattern above. |

## Decision flowchart

```
Error appears → Read the code around it
  │
  ├─ Is the identifier in the "safe for global" table above?
  │   └─ YES → Add to ignoreErrors (if not already there)
  │
  ├─ Is it clearly a collection/closure losing the concrete model type?
  │   └─ YES → Can you fix with @var annotation inside the closure?
  │       ├─ YES → Do that (preferred — gives IDE help too)
  │       └─ NO → Use inline @phpstan-ignore with a comment
  │
  ├─ Is it a return type or PHPDoc mismatch?
  │   └─ YES → Fix the code or the PHPDoc (check which is wrong)
  │
  ├─ Is it an enum comparison (identical/notIdentical)?
  │   └─ YES → Read the model's casts(). Is the field actually cast?
  │       ├─ YES → Inline @phpstan-ignore (false positive from lost type)
  │       └─ NO → This might be a real bug. Ask the user.
  │
  └─ Not sure?
      └─ Ask the user. Show them the error and the code.
```

## The closure type-hint trap

A common mistake: seeing `argument.type` on a `->map()` closure and "fixing" it by adding a concrete type hint to the closure parameter:

```php
// DON'T do this — it creates a new error
$users->map(function (User $user) { ... });
// PHPStan: "Closure(User) given, callable(Model) expected"

// DO this instead — @var inside the closure body
$users->map(function ($user) {
    /** @var User $user */
    ...
});

// OR for simple cases, inline ignore on the map call
$collection->map(fn (CoachMessage $msg) => [ /** @phpstan-ignore argument.type */
    ...
]);
```

Adding the type hint to the parameter tells PHPStan "this closure only accepts User" but the collection's generic type is `Model`, so PHPStan flags the mismatch. The `@var` approach tells PHPStan "trust me, this variable is a User" without conflicting with the collection's declared type.
