# phpstan.neon Template for Laravel Projects

Use this as the starting template. Adjust the `level` (start at 1, work up), and add/remove `ignoreErrors` entries as needed for the specific project.

## Includes

Always include the Larastan extension. Include the Carbon extension if `nesbot/carbon` is installed (check `composer.lock`).

```yaml
includes:
    - vendor/larastan/larastan/extension.neon
    # Include if nesbot/carbon is in composer.lock:
    - vendor/nesbot/carbon/extension.neon
```

## Base config

```yaml
parameters:

    paths:
        - app/

    # Start at 1, bump progressively
    level: 1
```

## ignoreErrors — Laravel magic patterns

Add these to filter out known false positives. Each block is independent — include only the ones relevant to the project.

### Eloquent Model properties in closures

When using `->map()`, `->filter()` etc, PHPStan loses the concrete model type and sees `Illuminate\Database\Eloquent\Model` instead of the actual model class.

```yaml
        - identifier: property.notFound
          message: '#Access to an undefined property Illuminate\\Database\\Eloquent\\Model::#'
        - identifier: property.notFound
          message: '#Access to an undefined property Illuminate\\Database\\Eloquent\\Relations\\Pivot::#'
        - identifier: argument.type
          message: '#Illuminate\\Database\\Eloquent\\Model given#'
        - identifier: assign.propertyType
          message: '#does not accept Illuminate\\Database\\Eloquent\\Model#'
        - identifier: argument.unresolvableType
          message: '#contains unresolvable type#'
```

### Eloquent casts (Carbon, enums)

PHPStan doesn't recognise the `casts()` method, so it thinks date columns are strings and enum columns are string/int.

```yaml
        - identifier: method.nonObject
          message: '#Cannot call method .+\(\) on string#'
        - identifier: property.nonObject
          message: '#Cannot access property \$value on (string|int)#'
```

### Eloquent scopes on relations

Calling scopes like `->approved()` on a relation query builder. Add your project's scope names to the pattern.

```yaml
        - identifier: method.notFound
          message: '#Call to an undefined method Illuminate\\Database\\Eloquent\\Relations\\.+::#'
```

Note: the pattern above is broad — it ignores ALL undefined method calls on relations. For a tighter filter, list specific scope names:

```yaml
        - identifier: method.notFound
          message: '#Call to an undefined method Illuminate\\Database\\Eloquent\\Relations\\.+::(approved|pending|active)\(\)#'
```

### Attribute accessors

`Attribute::get()` / `Attribute::set()` style accessors aren't picked up by Larastan. Add each accessor name to the pattern as you encounter them.

```yaml
        - identifier: property.notFound
          message: '#\$(full_name|display_name)#'
```

### Socialite contracts

Socialite returns contract interfaces but code typically accesses concrete properties/methods. Only needed if the project uses Socialite.

```yaml
        - identifier: property.notFound
          message: '#Laravel\\Socialite\\Contracts\\User::#'
        - identifier: method.notFound
          message: '#Laravel\\Socialite\\Contracts\\Provider::with\(\)#'
```

### withCount() dynamic attributes

Eloquent's `withCount()` creates dynamic `_count` attributes that PHPStan can't see. Add each one as encountered.

```yaml
        - identifier: property.notFound
          message: '#\$recent_additions_count#'
```

### Custom pivot model properties

If using custom pivot models, their properties may not be recognised.

```yaml
        - identifier: property.notFound
          message: '#Access to an undefined property Illuminate\\Database\\Eloquent\\Relations\\Pivot::#'
```

### Nullsafe false positives (level 5+)

Larastan incorrectly reports `?->` as unnecessary for nullable `belongsTo` relationships, `first()` returns, `tryFrom()` on enums, and enum property access through pivots/closures. Removing the `?->` would cause runtime crashes. Safe to ignore globally — an unnecessary `?->` is harmless, not a bug.

```yaml
        - identifier: nullsafe.neverNull
```

## Full example

Here is a complete `phpstan.neon` combining all the above:

```yaml
includes:
    - vendor/larastan/larastan/extension.neon
    - vendor/nesbot/carbon/extension.neon

parameters:

    paths:
        - app/

    level: 5

    ignoreErrors:
        # Eloquent Model properties in closures
        - identifier: property.notFound
          message: '#Access to an undefined property Illuminate\\Database\\Eloquent\\Model::#'
        - identifier: property.notFound
          message: '#Access to an undefined property Illuminate\\Database\\Eloquent\\Relations\\Pivot::#'
        - identifier: argument.type
          message: '#Illuminate\\Database\\Eloquent\\Model given#'
        - identifier: assign.propertyType
          message: '#does not accept Illuminate\\Database\\Eloquent\\Model#'
        - identifier: argument.unresolvableType
          message: '#contains unresolvable type#'

        # Eloquent casts (Carbon, enums)
        - identifier: method.nonObject
          message: '#Cannot call method .+\(\) on string#'
        - identifier: property.nonObject
          message: '#Cannot access property \$value on (string|int)#'

        # Eloquent scopes on relations
        - identifier: method.notFound
          message: '#Call to an undefined method Illuminate\\Database\\Eloquent\\Relations\\.+::#'

        # Attribute accessors — add names as encountered
        - identifier: property.notFound
          message: '#\$(full_name)#'

        # Socialite contracts (remove if not using Socialite)
        - identifier: property.notFound
          message: '#Laravel\\Socialite\\Contracts\\User::#'
        - identifier: method.notFound
          message: '#Laravel\\Socialite\\Contracts\\Provider::with\(\)#'

        # withCount() dynamic attributes — add names as encountered
        - identifier: property.notFound
          message: '#\$\w+_count#'

        # Nullsafe false positives (level 5+)
        - identifier: nullsafe.neverNull
```
