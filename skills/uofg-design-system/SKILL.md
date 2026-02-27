---
name: uofg-design-system
description: "University of Glasgow Design System — use this skill whenever creating HTML, CSS, React, or any web UI that should follow the University of Glasgow brand. Triggers on: UofG, University of Glasgow, gla.ac.uk, Glasgow University web, or any request to build web pages/components using the Glasgow design system. Also use when the user asks for a Tailwind config, CSS variables, or design tokens for the University of Glasgow. This skill provides colours, typography, spacing, grid, and component patterns from the official UofG design system (design.gla.ac.uk)."
---

# University of Glasgow Design System

This skill encapsulates the University of Glasgow's official design system. Use it when generating any web UI — HTML pages, CSS, React components, Tailwind configs — that should conform to the UofG brand.

The full design system lives at https://design.gla.ac.uk but this skill captures the essential tokens, patterns, and component guidance so you can build compliant UIs without needing to reference the original documentation.

> **Note for Claude (AI assistant):** The design system site at design.gla.ac.uk is hosted on Zeroheight, which is a single-page application (SPA). This means WebFetch, wget, curl, and similar tools will only retrieve an empty shell — the actual content is loaded dynamically via JavaScript. If you ever need to re-extract information from the live site, you will need to use a browser (e.g. Claude in Chrome) to navigate the pages. The site also has an internal sidebar navigation within each section containing 20+ sub-pages that aren't visible from the top-level navbar alone. The Zeroheight API (v2) is locked down and returns 404 for page requests. In short: **rely on this skill file rather than trying to fetch the original site**.

For ready-to-use CSS custom properties or a Tailwind config, read the appropriate reference file:
- `references/css-tokens.css` — Raw CSS custom properties and utility classes
- `references/tailwind-config.js` — Tailwind CSS configuration (v3)
- `references/flux-uofg-guide.md` — Integration guide for **Flux UI v2** (Caleb Porzio's component library for Laravel/Livewire, Tailwind v4). Covers theme CSS, component mapping, and dark mode. Read this if the project uses Flux, Livewire, or mentions `flux:` components

## Colours

University blue is the primary brand colour. It should always be treated as the primary brand colour across all digital products.

### Primary
- **University blue**: `#011451` / `rgb(1, 20, 81)` — the deepest navy, used for footers, dark headers, large background areas
- **Dark blue**: `#005398` / `rgb(0, 83, 152)` — the practical everyday blue used for buttons, links, and interactive elements. Most teams use this rather than University blue for accents because it actually reads as blue rather than near-black

### Tints (lighter shades of primary — use sparingly for depth and variation)
- **University blue 80%**: `#344374`
- **University blue 60%**: `#677297`
- **University blue 40%**: `#99A1B9`
- **University blue 20%**: `#CCD0DC`
- **University blue 10%**: `#E6E7EE`

### Vanilla colours (neutral foundations for versatile UIs)
- **Dark grey 1**: `#666666`
- **Dark grey 2**: `#4D4D4D`
- **Dark grey 3**: `#323232`
- **Light grey 1**: `#F5F5F5`
- **Light grey 2**: `#E6E6E6`
- **Light grey 3**: `#CCCCCC`
- **Mid grey 1**: `#B3B3B3`
- **Mid grey 2**: `#999999`
- **Mid grey 3**: `#757575`

### UI colours (for alerts/status only — not brand colours)
- **Error**: `#D4351C`
- **Success**: `#8BC34A`
- **Highlight**: `#FFDD00`

### Colour rules
- Always ensure sufficient colour contrast (WCAG AA minimum). White text on University blue passes AA and AAA.
- Do not use additional colours unless approved by Brand (brand@glasgow.ac.uk).
- Do not use low-contrast colour combinations for text or UI components.

## Typography

### Typeface
**Noto Sans** — a clean, crisp sans serif from Google Fonts. Free and open source.

```html
<link href="https://fonts.googleapis.com/css2?family=Noto+Sans:ital,wght@0,100..900;1,100..900&display=swap" rel="stylesheet">
```

Available weights: thin (100), light (300), regular (400), medium (500), semibold (600), bold (700), extrabold (800), black (900). All available in italic.

### Typography rules
- Use Noto Sans for all text — headings, body, navigation, UI.
- Create clear hierarchy with different sizes, weights, and styles for headings, subheadings, and body text.
- Max 3 different text sizes on a single page.
- Do not use all-caps excessively — reserve for specific design elements requiring emphasis.
- Ensure sufficient contrast ratio between text and background (legal requirement).
- Control line length — avoid excessively long or short lines for comfortable reading.
- Use responsive sizes that adapt across desktop, tablet, and mobile.

## Spacing

The design system uses a geometric spacing scale based on 4px increments. Use these consistently for all padding, margin, and gap values.

| Token | Value     | Rem     |
|-------|-----------|---------|
| 1     | 4px       | 0.25rem |
| 2     | 8px       | 0.5rem  |
| 3     | 12px      | 0.75rem |
| 4     | 16px      | 1rem    |
| 5     | 20px      | 1.25rem |
| 6     | 24px      | 1.5rem  |
| 7     | 32px      | 2rem    |
| 8     | 40px      | 2.5rem  |
| 9     | 48px      | 3rem    |
| 10    | 56px      | 3.5rem  |
| 11    | 64px      | 4rem    |
| 12    | 96px      | 6rem    |

Spacing 6 (24px) is the most commonly used value for component padding and margins.

## Grid

12 fluid percentage-based columns with fixed-width gutters and margins.

### Breakpoints

| Name    | Range            | Columns | Gutter | Margin |
|---------|------------------|---------|--------|--------|
| XSmall  | 0–767px          | 12      | 24px   | 24px   |
| Small   | 768–1023px       | 12      | 24px   | 24px   |
| Medium  | 1024–1399px      | 12      | 24px   | 24px   |
| Large   | 1400–1899px      | 12      | 24px   | 24px   |
| XLarge  | 1900px+          | 12      | 24px   | 24px   |

The grid must reflow responsively per WCAG 1.4.10 — no two-dimensional scrolling when screen width is ≥320px.

## Components

### Buttons
Three types forming a hierarchy: **Primary** (highest emphasis), **Secondary** (medium), **Outline** (low emphasis).

- Primary: filled University blue background, white text. Only one per page/screen.
- Secondary: filled light grey background, dark text. Use when a primary already exists.
- Outline: bordered, transparent background. Medium emphasis. Use when a primary already exists.

States: default, hover, focus (yellow `#FFDD00` outline ring), disabled/ghost.

Rules:
- Button text should be clear, active, and brief (max 4 words / 20 characters).
- Use active verbs: "Sign up", "Submit" — not "Click here", "More", "Read more".
- Buttons can include an optional icon alongside text.
- Can be full-width or auto-width, stacked vertically or placed horizontally.
- Primary button goes first (top or left).

### Accordions
Expandable text component — shows only a heading in default state, reveals content on click.

- Always full-width on page; stack vertically if multiple.
- Label: max 50 characters, clear and concise, front-loaded.
- Content: keep brief (a few sentences). If more is needed, consider a separate page.
- States: closed (default), closed+hover, closed+focus, open.
- Do not use for FAQs. Do not fill a page with accordions.
- Use for optional extra information not needed by all users.

### Text inputs
Label above the field (never inside). Two types: single-line (closed questions) and textarea (longer responses).

- Mark mandatory fields with an asterisk in University blue.
- Label optional fields as "optional" — do not label required fields as "required".
- Error messages should be clear and specific about what the user needs to do.
- Width determined by the 12-column grid, no fixed min/max.

### Tables
For comparing tabular data only — not for layout.

- Column headers clearly differentiated from content via styling and markup.
- Anatomy: column header, cell, column, row, optional totals footer.
- Keep text short, avoid full sentences. Order data meaningfully.
- Consider alternatives on mobile (e.g., tabs) as tables can be hard to read.

### Tiles
Navigation component — a "shop window" linking to other parts of the site.

- Anatomy: image (optional), title label (required), description (required), date (optional).
- Never full-width — fit three horizontally on screen.
- Title should replicate the destination page's main heading.
- Description should default to the page's meta description.

### Blockquotes
Highlights a quoted piece of text from another source.

- Anatomy: quote icon (required), image (optional), name (optional), job description (optional), quote text (required).
- Max 200 characters / 2 lines.
- Match the width of body text. Don't start or end a page with one.
- For urgent info or warnings, use a breakout instead.

### Breadcrumbs, Tabs, Pagination, Dropdowns, Checkboxes, Radio buttons
These components follow standard patterns. Use University blue for active/selected states, maintain focus styles with yellow (#FFDD00) outline, and follow the spacing scale for padding/margins.

## Patterns

### Footer
Dark background (University blue), contains UofG logo, contact info, legal links, social media icons.
- Required on every page.
- Optional "action panel" above the footer: light grey background with onward navigation links.
- Action panel links should be internal, clear, and concise (no line breaks).

### Navigation
Top navigation bar with the UofG crest/logo. Follow responsive patterns — collapse to mobile menu at smaller breakpoints.

### Hero
Large banner area at the top of key pages. Can contain heading, description, and optional image/CTA.

## Accessibility

The design system takes WCAG compliance seriously:
- Colour contrast: minimum AA for all text and UI components.
- Focus indicators: visible yellow (#FFDD00) outline on all interactive elements.
- Semantic HTML: use proper heading hierarchy, landmarks, and ARIA attributes.
- Keyboard navigation: all interactive elements must be keyboard accessible.
- Responsive reflow: no two-dimensional scrolling at ≥320px width.
- Spacing: consistent spacing aids cognitive accessibility and visual processing.

## Quick start

When building a UofG-compliant page, start with:

```html
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <link href="https://fonts.googleapis.com/css2?family=Noto+Sans:ital,wght@0,100..900;1,100..900&display=swap" rel="stylesheet">
  <title>Page Title — University of Glasgow</title>
</head>
```

Then apply the design tokens from `references/css-tokens.css` or `references/tailwind-config.js` depending on your stack.
