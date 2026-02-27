# University of Glasgow + Flux UI Integration Guide

A practical guide to theming Flux (v2, Tailwind v4) to align with the University of Glasgow Design System. Works for both internal admin tools and more public-facing apps.

## Philosophy

The UofG brand has two key blues. The "University blue" (#011451) is an extremely dark navy — almost black — used mainly for large background areas and the footer. In practice, most teams reach for the "Dark blue" (#005398) for interactive elements like buttons, links, and accents because it actually reads as *blue* rather than *very dark*. Flux's theming system makes it straightforward to bring that identity into your Laravel/Livewire apps.

The approach here is:

- Noto Sans as the typeface (the UofG standard)
- Dark blue (#005398) as the accent colour — what people actually use day-to-day
- University blue (#011451) available for footers, dark headers, and anywhere you want that deep navy
- Slate as the base grey (its cool blue undertone pairs naturally with both blues)
- UofG spacing scale and accessibility standards

Flux's component library is already excellent. The goal is to dress it in the right colours and let it do its thing.

## The Theme CSS

Add this to your `resources/css/app.css`:

```css
/* ================================================
   University of Glasgow — Flux Theme
   ================================================ */

@import url('https://fonts.googleapis.com/css2?family=Noto+Sans:ital,wght@0,100..900;1,100..900&display=swap');

/* --- Base colour: Slate ---
   Slate has a cool blue undertone that pairs naturally
   with UofG blue. Much better than zinc for this. */
@theme {
    --color-zinc-50: var(--color-slate-50);
    --color-zinc-100: var(--color-slate-100);
    --color-zinc-200: var(--color-slate-200);
    --color-zinc-300: var(--color-slate-300);
    --color-zinc-400: var(--color-slate-400);
    --color-zinc-500: var(--color-slate-500);
    --color-zinc-600: var(--color-slate-600);
    --color-zinc-700: var(--color-slate-700);
    --color-zinc-800: var(--color-slate-800);
    --color-zinc-900: var(--color-slate-900);
    --color-zinc-950: var(--color-slate-950);
}

/* --- Accent colour: UofG Dark Blue ---
   #005398 is the "Dark blue" from the UofG brand palette.
   In practice this is what most teams use for buttons, links,
   and interactive elements — it reads as a proper blue rather
   than the near-black of University blue (#011451).
   #011451 is still available below for footers and dark headers. */
@theme {
    --color-accent: #005398;           /* UofG dark blue — buttons, active states */
    --color-accent-content: #003865;   /* Slightly darker for text links */
    --color-accent-foreground: #FFFFFF;

    /* UofG brand colour tokens */
    --color-uofg-dark-blue: #005398;
    --color-uofg-university-blue: #011451;
    --color-uofg-blue-80: #344374;
    --color-uofg-blue-60: #677297;
    --color-uofg-blue-40: #99A1B9;
    --color-uofg-blue-20: #CCD0DC;
    --color-uofg-blue-10: #E6E7EE;

    /* UofG UI colours (for alerts/validation — matches design system) */
    --color-uofg-error: #D4351C;
    --color-uofg-success: #8BC34A;
    --color-uofg-highlight: #FFDD00;

    /* Font */
    --font-sans: 'Noto Sans', system-ui, -apple-system, sans-serif;
}

/* Dark mode accents */
@layer theme {
    .dark {
        --color-accent: #5BA0D9;           /* Lighter blue for dark backgrounds */
        --color-accent-content: #7DB8E8;   /* Even lighter for readable text on dark */
        --color-accent-foreground: #FFFFFF;
    }
}

/*
   Option B: Sky palette
   If you want something lighter and more modern for internal
   admin tools, Tailwind's sky palette is a decent match for
   the UofG blue family without needing custom hex values.

@theme {
    --color-accent: var(--color-sky-600);
    --color-accent-content: var(--color-sky-700);
    --color-accent-foreground: var(--color-white);
}

@layer theme {
    .dark {
        --color-accent: var(--color-sky-500);
        --color-accent-content: var(--color-sky-400);
        --color-accent-foreground: var(--color-white);
    }
}
*/

/* --- Focus ring: UofG yellow highlight ---
   The design system specifies #FFDD00 for focus indicators.
   This is optional — Flux's default focus styles are already
   accessible. But this adds a distinctly Glasgow touch. */
/*
*:focus-visible {
    outline-color: #FFDD00 !important;
}
*/
```

## Component Mapping: UofG Design System → Flux

Here's how UofG design system components map onto Flux. For back-office tools, Flux's components are generally richer and more interactive than what the public-facing design system specifies — that's fine. The key is getting the *tokens* right (colour, font, spacing) and then letting Flux do its thing.

### Buttons

| UofG                | Flux equivalent                           |
|---------------------|-------------------------------------------|
| Primary button      | `<flux:button variant="primary">`         |
| Secondary button    | `<flux:button variant="filled">`          |
| Outline button      | `<flux:button>` (default is outline)      |
| Disabled/ghost      | `<flux:button disabled>`                  |

UofG rule: max 1 primary button per page. Button text max 4 words/20 chars. Use active verbs.

```html
<!-- Primary action -->
<flux:button variant="primary" wire:click="save">Save changes</flux:button>

<!-- Secondary alongside primary -->
<flux:button variant="filled" wire:click="preview">Preview</flux:button>

<!-- Low emphasis -->
<flux:button wire:click="cancel">Cancel</flux:button>
```

### Form Inputs

Flux's `<flux:input>` with `label` prop maps directly to UofG's "label above input" pattern. The `badge="Required"` pattern is a nice alternative to UofG's asterisk convention.

```html
<!-- Standard field (UofG: label above, mandatory asterisk) -->
<flux:input wire:model="firstName" label="First name" />

<!-- Optional field -->
<flux:input wire:model="phone" label="Phone number">
    <x-slot:label>
        <flux:label badge="Optional">Phone number</flux:label>
    </x-slot:label>
</flux:input>

<!-- With validation error (matches UofG: clear, specific error messages) -->
<flux:field>
    <flux:label badge="Required">Email</flux:label>
    <flux:input wire:model="email" type="email" />
    <flux:error name="email" />
</flux:field>
```

### Tables

Flux's `<flux:table>` maps cleanly to UofG tables. The design system says: column headers clearly differentiated, keep text short, order data meaningfully.

```html
<flux:table :paginate="$this->records">
    <flux:table.columns>
        <flux:table.column sortable :sorted="$sortBy === 'name'" :direction="$sortDirection" wire:click="sort('name')">Name</flux:table.column>
        <flux:table.column sortable :sorted="$sortBy === 'date'" :direction="$sortDirection" wire:click="sort('date')">Date</flux:table.column>
        <flux:table.column>Status</flux:table.column>
    </flux:table.columns>

    <flux:table.rows>
        @foreach ($this->records as $record)
            <flux:table.row :key="$record->id">
                <flux:table.cell variant="strong">{{ $record->name }}</flux:table.cell>
                <flux:table.cell>{{ $record->date->format('j M Y') }}</flux:table.cell>
                <flux:table.cell>
                    <flux:badge size="sm" :color="$record->status_color" inset="top bottom">
                        {{ $record->status }}
                    </flux:badge>
                </flux:table.cell>
            </flux:table.row>
        @endforeach
    </flux:table.rows>
</flux:table>
```

### Accordions

Direct mapping. UofG says: label max 50 chars, keep content brief, don't fill a page with them.

```html
<flux:accordion transition>
    <flux:accordion.item heading="Entry requirements">
        Standard entry requirements apply. See the prospectus for details.
    </flux:accordion.item>
    <flux:accordion.item heading="Fees and funding">
        Tuition fees for 2025/26 are listed on the university fees page.
    </flux:accordion.item>
</flux:accordion>
```

### Cards (≈ UofG Tiles)

UofG "tiles" are navigation cards. Flux's `<flux:card>` serves the same purpose but is more flexible.

```html
<!-- UofG tile pattern: image + title + description, max 3 across -->
<div class="grid grid-cols-1 md:grid-cols-3 gap-6">
    <a href="/admissions" class="block">
        <flux:card class="hover:shadow-md transition-shadow">
            <flux:heading size="lg" class="text-accent-content">Admissions</flux:heading>
            <flux:text class="mt-2">Manage applications and offers for the current cycle.</flux:text>
        </flux:card>
    </a>
    <!-- repeat for other tiles -->
</div>
```

### Navigation

For admin tools, Flux's sidebar layout with `<flux:navlist>` is ideal. UofG's top navigation pattern is more suited to public sites.

```html
<!-- Sidebar nav for admin tools -->
<flux:navlist>
    <flux:navlist.group heading="Administration">
        <flux:navlist.item href="/dashboard" icon="home">Dashboard</flux:navlist.item>
        <flux:navlist.item href="/students" icon="academic-cap">Students</flux:navlist.item>
        <flux:navlist.item href="/courses" icon="book-open">Courses</flux:navlist.item>
        <flux:navlist.item href="/reports" icon="chart-bar">Reports</flux:navlist.item>
    </flux:navlist.group>
</flux:navlist>
```

### Alerts / Callouts (≈ UofG Breakouts)

Use Flux's `<flux:callout>` for status messages and warnings, with UofG's UI colours:

```html
<flux:callout variant="danger" icon="exclamation-triangle">
    This action cannot be undone.
</flux:callout>

<flux:callout variant="success" icon="check-circle">
    Record saved successfully.
</flux:callout>
```

## Spacing

The UofG spacing scale (4, 8, 12, 16, 20, 24, 32, 40, 48, 56, 64, 96px) aligns well with Tailwind's default scale. The most commonly used value is 24px (`p-6` / `gap-6`). Flux components already use sensible internal spacing, so you mainly need to think about spacing *between* components:

- Between form fields: `space-y-6` (24px — matches UofG spec)
- Between sections: `space-y-8` or `space-y-12`
- Card/tile grid gaps: `gap-6`

## Accessibility Checklist

These come from the UofG design system and apply regardless of whether you're using Flux:

- Colour contrast: WCAG AA minimum for all text and interactive elements
- Focus indicators: visible on all interactive elements (Flux handles this well by default)
- Keyboard navigation: all interactive elements reachable via keyboard
- Semantic HTML: proper heading hierarchy, landmarks, ARIA where needed
- Responsive reflow: no horizontal scrolling at 320px+ width
- Form labels: always above inputs, never inside (Flux's `label` prop does this correctly)

## Quick Decision Guide

| Situation | Recommendation |
|-----------|---------------|
| Public-facing UofG page | Use the full UofG design system CSS, not Flux |
| Internal admin tool | Use Flux + this theme |
| Student/staff portal | Flux + this theme, consider adding UofG header/footer |
| Prototype or MVP | Flux defaults + just the font and accent colour |
| Dark mode needed? | Flux supports it natively — the theme CSS above includes dark mode tokens |
