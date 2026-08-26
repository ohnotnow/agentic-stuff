# Flux UI Design Taste

Distilled from the official fluxui.dev demo pages (settings, analytics dashboard, sales
dashboard, kanban board, Q&A feed, login) - screenshot plus source studied together. This
file captures the *judgement calls* the component reference cannot: when to use a card,
how a page breathes, what restraint looks like.

**Read this before building a full page or layout.** For single components, SKILL.md alone
is enough.

**Team conventions in SKILL.md always win over anything here.** In particular: flyout
modals by default, and our denser spacing scale (our apps are tools - `space-y-6` within a
section, `my-8` or so between sections; the demos sometimes stretch to 12).

---

## Cross-cutting habits

### Flux components are atoms, not straitjackets

The demos drop to plain divs + Tailwind whenever the layout is bespoke - kanban columns,
stat tiles, feed items are all hand-rolled containers with Flux atoms inside (`flux:badge`,
`flux:heading`, `flux:button`, `flux:text`). Don't contort a `flux:card` to fit a custom
layout; build the container yourself and keep Flux for the pieces users interact with.

### Chrome is muted, content is not

Sidebars and headers get `bg-zinc-50 dark:bg-zinc-900` plus a `border-zinc-200
dark:border-zinc-700` edge. The main content area keeps the default background. Chrome
recedes; content doesn't compete with it.

### Colour only when it means something

The palette is zinc everywhere. Colour appears solely for semantics: green/red trend
indicators, status badges (`green` paid, `red` failed, `zinc` refunded), a lime moderator
badge, red for destructive. Never decoratively.

### Two levels of vertical rhythm

- **Within a section**: `space-y-6` between controls, `gap-4` horizontally, `gap-2` for
  tightly grouped things.
- **Between sections**: bigger, and explicit. Settings uses `<flux:separator
  variant="subtle" class="my-8" />`; dashboards use an empty spacer div such as
  `<div class="h-8 sm:h-12"></div>` between blocks. Both are deliberate: section breaks
  are their own element, not a margin bolted onto a neighbour.

### Heading scale is shallow

`size="xl"` for the page title (exactly one), `size="lg"` for section titles, default
`flux:heading` for card/item titles. Nothing bigger, nothing decorative. When breadcrumbs
or context make a visible title redundant, the demos still render one for screen readers:
`<flux:heading level="1" class="sr-only">Analytics overview</flux:heading>`.

### The ellipsis pattern for secondary actions

Every card, tile, row, and column gets its overflow actions behind a small quiet button:

```blade
<flux:dropdown>
    <flux:button variant="subtle" size="sm" icon="ellipsis-horizontal" aria-label="More options for {{ $thing }}" />
    <flux:menu>
        <flux:menu.item icon="pencil-square">Edit</flux:menu.item>
        <flux:menu.item icon="trash" variant="danger">Delete</flux:menu.item>
    </flux:menu>
</flux:dropdown>
```

Destructive item last, `variant="danger"`, inside the menu - never a bare red button in
the row. On cards/tiles the button is absolutely positioned top-right with the content
padded to leave room for it.

A menu item can open a confirm modal directly - `flux:modal.trigger` wraps
`flux:menu.item` and works (verified): the classic shape is a danger "Delete..." item
triggering the delete-confirmation modal.

When one of the actions is a CSRF form POST (impersonate, logout), don't lose the form in
the refactor - wrap that item in its form inside the menu, with the item as the submit
button (this is how the official demos do logout):

```blade
<form method="POST" action="{{ route('users.impersonate', $user) }}">
    @csrf
    <flux:menu.item as="button" type="submit" icon="identification" class="w-full">Impersonate</flux:menu.item>
</form>
```

### Toolbars go small and cluster

Everything in a toolbar row is `size="sm"`: buttons, selects, date pickers, segmented
tabs. Related controls cluster with `gap-2`; unrelated clusters are split by
`<flux:separator vertical class="my-2" />` or pushed apart with `flux:spacer`. View
switchers (board/list, chart type, list/grid) are segmented controls - `flux:tabs
variant="segmented" size="sm"` or `flux:radio.group variant="segmented"` - not button
rows.

### Responsive means degrade, not squish

The demos hide gracefully rather than shrink: secondary stat tiles get `max-md:hidden`,
table columns drop one by one (`max-md:hidden` per column), a toolbar Export button
becomes an ellipsis dropdown on mobile, breadcrumbs vanish on small screens. Decide what
mobile users lose; don't let flexbox decide.

### Mobile filter disclosure (field-tested)

When a filter toolbar has more than a search box, don't let it stack into a ragged column
on mobile. Keep the search box always visible and tuck the rest behind an icon toggle:

```blade
<div class="mt-4 flex flex-wrap items-center gap-2"
     x-data="{ showFilters: @js($typeFilter !== '' || $teamFilter !== '') }">
    <flux:input size="sm" class="flex-1 md:flex-none max-w-96" icon="magnifying-glass" ... />
    <flux:toggle x-model="showFilters" icon="funnel" tooltip="Show filters" size="sm" class="md:hidden" />
    <div class="basis-full md:hidden" x-show="showFilters"></div>

    <flux:select size="sm" class="w-fit" x-bind:class="showFilters ? '' : 'max-md:hidden'">...</flux:select>
    {{-- remaining selects the same; a flux:spacer gets max-md:hidden --}}
</div>
```

The judgement calls baked into that snippet:

- **Seed the Alpine state from the active filters** so a shared filtered URL opens with
  its filters visible rather than invisibly applied.
- **The `basis-full` line-break div** puts revealed controls on their own rows below; the
  search row doesn't move a pixel when toggling (no jank). `x-show` stops it adding a
  phantom flex row-gap while collapsed.
- A growing search input competes with `flux:spacer` for free space: `flex-1
  md:flex-none` gives mobile flexibility with a fixed desktop cap.
- This is pure view state: bind the toggle with Alpine `x-model`, not `wire:model` - no
  server roundtrip, and the state survives Livewire morphs.

### Accessibility hygiene (non-negotiable)

The demos are quietly rigorous and so are we: `aria-label` on every icon-only button and
navbar item, labelled `flux:progress` bars, `alt=""` on decorative images, `sr-only` h1
when there's no visible page title, `tabular-nums` on changing counts. Note that the
`tooltip` prop is NOT an accessible name - it only wraps the button in a `flux:tooltip`
(verified in the vendor stub), so icon-only buttons need an explicit `aria-label` even
when they have a tooltip.

---

## Page archetypes

### Settings / form page - flat, no cards

Cards would be noise here. Flat sections divided by subtle separators, each section a
two-column split: fixed-width intro on the left, controls on the right.

```blade
<flux:main container class="max-w-xl lg:max-w-3xl">
    <flux:heading size="xl">Settings</flux:heading>

    <flux:separator variant="subtle" class="my-8" />

    <div class="flex flex-col lg:flex-row gap-4 lg:gap-6">
        <div class="w-80">
            <flux:heading size="lg">Profile</flux:heading>
            <flux:text class="mt-2">This is how others will see you on the site.</flux:text>
        </div>

        <div class="flex-1 space-y-6">
            {{-- inputs, selects, checkbox/radio groups... --}}

            <div class="flex justify-end">
                <flux:button type="submit" variant="primary">Save profile</flux:button>
            </div>
        </div>
    </div>

    <flux:separator variant="subtle" class="my-8" />
    {{-- next section... --}}
</flux:main>
```

- Each section has its own right-aligned save button - no single global save.
- `description` (above the input) defines what the field *is*; `description:trailing`
  (below) tells you what you can do around it ("You can manage verified addresses in...").
- Groups of switches sit in a `flux:fieldset` with `flux:separator variant="subtle"`
  between each - still no cards.

### Dashboard - carded, with a hierarchy of prominence

The one page family where cards earn their keep, and prominence is graded:

- **Stat tiles**: `flux:card variant="soft"` (or a plain div with `bg-zinc-50
  dark:bg-zinc-700 rounded-lg px-6 py-4` - drop to `p-4` when the grid runs five-up).
  Anatomy is always the same regardless of container: muted label (`flux:text
  class="font-medium"`), big value (`flux:heading size="xl" class="mt-1 tabular-nums"`),
  trend line. Semantic state (overdue, failing) colours the **value text** -
  `text-red-600 dark:text-red-400` - never the tile background; tiles stay neutral.

  ```blade
  <flux:text class="font-medium">Visitors</flux:text>
  <flux:heading size="xl" class="mt-1">128.6K</flux:heading>
  <flux:text class="mt-1 flex items-center gap-1 font-medium text-green-600 dark:text-green-400">
      <flux:icon.arrow-trending-up variant="micro" /> 24.7% <span class="font-normal">vs last month</span>
  </flux:text>
  ```

- **The hero chart**: a default (non-soft) `flux:card` - the most prominent thing on the
  page.
- **Secondary list cards** ("Top pages", "Sources"): `flux:card variant="soft"` with
  `class="flex min-w-0 flex-col"`, heading row with the unit label right-aligned
  (`flex items-baseline justify-between`), and a full-width footer link pinned to the
  bottom:

  ```blade
  <div class="mt-auto pt-6">
      <flux:button size="sm" icon:trailing="arrow-right" icon:variant="micro" href="#" class="w-full">View all pages</flux:button>
  </div>
  ```

- Ranked lists inside those cards use thin progress bars: `flux:progress` with
  `class="h-1"`, `color="blue"`, and a proper `aria-label`.
- Toolbar row at the top (compare-select, date range, export), then stat tiles, then hero
  chart, then the secondary card grid (`grid gap-6 md:grid-cols-3`), with spacer divs
  between blocks.
- Neat idiom for client-side state: bind a Livewire property to a data attribute and let
  CSS do the switching - no re-render, no flicker:

  ```blade
  <flux:card wire:bind:data-chart-type="chartType">
      <flux:chart.bar field="visitors" class="in-data-[chart-type=line]:hidden" ... />
      <flux:chart.line field="visitors" class="in-data-[chart-type=bar]:hidden" wire:cloak ... />
  ```

### Data table page

- Status as `flux:badge size="sm" inset="top bottom"` with semantic colours; money/key
  figures in `variant="strong"` cells; customer as avatar + name.
- Badge the exceptional value only. A count column where every zero wears a green badge
  is decoration, not information - render zero as plain muted text (`<span
  class="text-zinc-400">0</span>`) and badge just the non-zero case.
- Numeric columns get `align="end"`.
- Leading checkbox column for bulk selection; trailing cell holds the ellipsis dropdown.
- Columns drop with `max-md:hidden` as the screen narrows.
- `flux:pagination` directly after the table.

### Board / bespoke layout (kanban)

- Columns are plain divs with a barely-there wash: `rounded-lg w-80 bg-zinc-400/5
  dark:bg-zinc-900`. Cards inside are divs too: `bg-white dark:bg-zinc-800 rounded-lg
  shadow-xs border border-zinc-200 dark:border-white/10 p-3 space-y-2`.
- Flux atoms inside: coloured `flux:badge size="sm"` for labels, default `flux:heading`
  for titles, `variant="subtle"` buttons for column menus and "New task".
- Edge-to-edge horizontal scroll without losing page padding:
  `<div class="overflow-x-auto -m-6 p-6">` wrapping the `flex gap-4` of columns.

### Feed / list page (Q&A)

- Content in a narrow centred column (`mx-auto max-w-lg`); the page header is a
  full-width bar with its own background and border, holding the title, count, filter and
  sort listboxes, and the primary action.
- Item state shown as a background wash, not borders or callouts: unapproved items get
  `bg-zinc-50 dark:bg-zinc-700/50` on their rounded container; approved items sit flat.
- Inline actions are quiet: `variant="ghost"` vote button, `variant="subtle"` ellipsis.
  Moderation state uses plain `size="sm"` buttons.

### Auth page

- Split screen: form pane centred, decorative pane as a `rounded-lg` inset image (wrapper
  has `p-4`, image pane `max-lg:hidden`).
- Form is a single `w-80` column, `space-y-6`, everything full-width - the one context
  where `class="w-full"` buttons are the norm.
- Social buttons are default variant with an icon slot; only the submit gets
  `variant="primary"`. `<flux:separator text="or" />` between the two blocks.
- The verbose `flux:field` syntax earns its keep exactly once: when the label row needs
  extra content, like a trailing "Forgot password?" link beside the Password label.
