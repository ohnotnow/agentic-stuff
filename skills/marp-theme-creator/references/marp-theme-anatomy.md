# Marp Theme CSS — What You Actually Need to Know

This is a practical reference for building Marp custom themes. It covers the gotchas that aren't obvious from the documentation.

## Theme declaration

Every Marp theme CSS file MUST begin with this comment:
```css
/* @theme my-theme-name */
```
This is how Marpit registers the theme. Without it, the theme won't load.

## Extending the default theme

```css
@import 'default';
```

This gives you sensible base styles for typography, lists, tables, etc. But it also gives you a LOT of opinionated styling that's hard to override because of how Marp compiles CSS.

### The specificity problem

Marp compiles all theme CSS and wraps selectors with a very long prefix:
```
div#\:\$p > svg > foreignObject > section
```

Both the default theme's rules AND your custom rules get this prefix. So specificity is usually equal between them. **The problem is source order**: some of the default theme's rules appear AFTER your custom rules in the compiled output, so they win by cascade.

### The solution: override CSS variables

The default theme uses CSS custom properties for almost everything. Override these in `:root` rather than fighting selector specificity:

```css
:root {
  /* Kill blockquote left border */
  --borderColor-default: transparent;

  /* Kill table row striping */
  --bgColor-muted: transparent;

  /* Kill default background colour (so yours shows through) */
  --bgColor-default: transparent;
}
```

For properties where variables aren't enough, use `!important` as a last resort:
```css
section blockquote {
  border: none !important;
}
section table tr {
  background-color: transparent !important;
}
```

## Syntax highlighting

Marp uses highlight.js for code blocks. The syntax colours are controlled by `--color-prettylights-syntax-*` CSS variables.

**Critical**: The default theme defines these with `light-dark()`:
```css
--color-prettylights-syntax-keyword: light-dark(#cf222e, #ff7b72);
```

The `light-dark()` function picks the first value for `color-scheme: light` and the second for `color-scheme: dark`. Since the default colour scheme is `light`, you get colours designed for WHITE backgrounds — even if your code block has a dark background.

**You MUST override these variables** if your code blocks have dark backgrounds:

```css
:root {
  /* GitHub dark theme values — good baseline for dark code blocks */
  --color-prettylights-syntax-comment: #8B95A8;
  --color-prettylights-syntax-constant: #79C0FF;
  --color-prettylights-syntax-entity: #D2A8FF;
  --color-prettylights-syntax-entity-tag: #7EE787;
  --color-prettylights-syntax-keyword: #FF7B72;
  --color-prettylights-syntax-string: #A5D6FF;
  --color-prettylights-syntax-variable: #FFA657;
  --color-prettylights-syntax-brackethighlighter-angle: #9198A1;
  --color-prettylights-syntax-brackethighlighter-unmatched: #F85149;
  --color-prettylights-syntax-carriage-return-bg: #B62324;
  --color-prettylights-syntax-carriage-return-text: #F0F6FC;
  --color-prettylights-syntax-markup-heading: #1F6FEB;
  --color-prettylights-syntax-markup-bold: #F0F6FC;
  --color-prettylights-syntax-markup-italic: #F0F6FC;
  --color-prettylights-syntax-markup-list: #F2CC60;
  --color-prettylights-syntax-storage-modifier-import: #D0D8E8;
  --color-prettylights-syntax-string-regexp: #7EE787;
}
```

Adjust these to match your theme's palette for a cohesive feel.

## Core HTML structure

Each slide is a `<section>` element. All selectors work from `section`:

| Selector | Purpose |
|----------|---------|
| `section` | Base slide (background, font, padding, dimensions) |
| `section.lead` | Title/lead slides — apply with `<!-- _class: lead -->` |
| `section.invert` | Inverted colour scheme — `<!-- _class: invert -->` |
| `section.divider` | Section break (custom class, not built-in) |
| `section h1` – `section h6` | Headings |
| `section p` | Paragraphs |
| `section a` | Links |
| `section ul`, `section ol` | Lists |
| `section li` | List items |
| `section blockquote` | Block quotes |
| `section pre` | Code block containers |
| `section pre code` | Code block text |
| `section code` | Inline code |
| `section table` | Tables |
| `section table th` | Table headers |
| `section table td` | Table cells |
| `header` | Slide header (from `header:` frontmatter) |
| `footer` | Slide footer (from `footer:` frontmatter) |
| `section::after` | Pagination (from `paginate: true`) |

## Slide dimensions

Set on `section` using **absolute units only** (px):
```css
section {
  width: 1280px;   /* 16:9 */
  height: 720px;
}
```

## Custom slide classes

You can define any class name and apply it with `<!-- _class: yourclass -->`:
```css
section.fancy {
  background: navy;
  color: white;
}
```

The `lead` and `invert` classes are conventions from the built-in themes, but you can add as many custom classes as you like.

## Header, footer, and pagination

Headers and footers are positioned elements. They have NO default styling from the base — you must position them:
```css
header, footer {
  position: absolute;
  left: 70px;
  right: 70px;
  font-size: 14px;
}
header { top: 22px; }
footer { bottom: 22px; }
```

Pagination renders in `section::after`:
```css
section::after {
  font-size: 13px;
  bottom: 22px;
  right: 70px;
}
```

## Google Fonts

Import fonts with `@import url(...)` AFTER the theme import:
```css
/* @theme my-theme */
@import 'default';
@import url('https://fonts.googleapis.com/css2?family=...');
```

## Building with the theme

```bash
# Single file
npx @marp-team/marp-cli --theme-set ./themes/ slides.md

# Live preview
npx @marp-team/marp-cli --theme-set ./themes/ -p slides.md

# PDF export
npx @marp-team/marp-cli --theme-set ./themes/ --pdf slides.md
```

## Common mistakes

1. **Setting `color` on `pre code` expecting it to change syntax highlighting** — it only sets the fallback colour. The hljs spans override it. Use the `--color-prettylights-syntax-*` variables.
2. **Using `border: none` on blockquotes without `!important`** — the default theme's border-left rule has equal specificity and may appear later in the cascade.
3. **Forgetting to set `--bgColor-muted: transparent`** — this is what the default theme uses for table row striping (`tr:nth-child(2n)`).
4. **Using relative units for slide dimensions** — Marp requires px for width/height.
5. **Not testing both HTML and PDF output** — rendering can differ.
