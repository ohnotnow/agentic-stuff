# Fix Flux logout button pattern

The user has copy-pasted the same broken logout pattern across several Laravel apps and wants it fixed in this one.

## The bug

In the main app layout (usually `resources/views/components/layouts/app.blade.php` or similar), they have a logout that wraps a `<flux:button>` *inside* a `<flux:sidebar.item>` (or `<flux:menu.item>`), like this:

```blade
<flux:sidebar.item tooltip="Logout" icon="arrow-right-start-on-rectangle">
    <form method="post" action="{{ route('auth.logout') }}">
        @csrf
        <flux:button class="w-full" type="submit">
            <span class="hidden sm:block">Logout</span>
        </flux:button>
    </form>
</flux:sidebar.item>
```

This renders the sidebar item *and* a stacked Flux button inside it, so you see an icon row with a big mismatched dark button beneath. It looks broken.

## The fix

A `flux:sidebar.item` (or `flux:menu.item`) without `href` renders as a `<button>`, and attributes like `type="submit"` pass through. So wrap the form around a single item:

```blade
<form method="post" action="{{ route('auth.logout') }}">
    @csrf
    <flux:sidebar.item icon="arrow-right-start-on-rectangle" type="submit">Logout</flux:sidebar.item>
</form>
```

Same pattern for `<flux:menu.item>` inside a dropdown.

## Also remove: the orphan mobile dropdown

The Flux docs sidebar example uses a `<flux:dropdown>` in the mobile `<flux:header>` with a `<flux:profile>` trigger as its first child. The user copy-pasted the structure but never wired the trigger, so the dropdown has no clickable element and the logout inside is unreachable. It looks like this:

```blade
<flux:header class="lg:hidden">
    <flux:sidebar.toggle ... />
    <flux:spacer />
    <flux:dropdown position="top" align="start">
        <flux:menu>
            <!-- logout form here, never visible because dropdown has no trigger -->
        </flux:menu>
    </flux:dropdown>
</flux:header>
```

The sidebar drawer (opened by the hamburger) already contains the Logout item, so this dropdown is dead weight. **Remove the `<flux:dropdown>` block entirely**, along with the `<flux:spacer />` that was only there to push it to the right. The header should end up as just the sidebar toggle:

```blade
<flux:header class="lg:hidden print:hidden">
    <flux:sidebar.toggle class="lg:hidden" icon="bars-2" inset="left" />
</flux:header>
```

## Workflow

1. Grep the app's layouts for `auth.logout` (or `logout` if that's the route name) to find all logout forms.
2. Apply the fix to each.
3. Remove any trigger-less `<flux:dropdown>` block (and its preceding `<flux:spacer />`) in the mobile header — no need to ask.
4. If you have browser access, visit the app and verify the sidebar item now matches the styling of the other nav items (same height, same hover, no nested big button). Test mobile width too (the sidebar drawer opens via the hamburger).
5. Don't run pint — Blade files aren't affected.
