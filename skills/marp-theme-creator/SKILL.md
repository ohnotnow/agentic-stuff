---
name: marp-theme-creator
description: "Create custom Marp presentation themes from a description or vibe. Asks about the aesthetic, audience, and feel, then generates production-ready theme CSS. Detects the i-impeccable skill for enhanced design guidance. Triggers on: marp theme, create a theme, presentation theme, slide theme, or any request to design a custom look for Marp presentations."
user-invocable: true
argument-hint: "[aesthetic description]"
---

# Marp Theme Creator

Create custom Marp presentation themes through a guided conversation. Generates production-ready CSS that works with `@marp-team/marp-cli`.

Before writing any CSS, read `references/marp-theme-anatomy.md` bundled with this skill — it contains hard-won knowledge about Marp's specificity model, CSS variable overrides, and syntax highlighting that will save you from invisible code blocks and stubborn left borders.

## When to activate

- User asks to create a Marp theme
- User wants a custom look for presentations
- User describes a vibe or aesthetic for slides ("early 60s UK sci-fi", "cat lovers", "brutalist architecture")
- User invokes `/marp-theme-creator`

---

## Step 0: Check for design skills

Silently check whether the `i-impeccable` skill (or `impeccable`) is available. You can detect this by checking if it appears in your available skills list.

**If i-impeccable IS available:**
You have access to professional design thinking. Use its principles throughout — especially the font selection procedure (avoid the reflex font list), colour principles (OKLCH, tinted neutrals, 60-30-10), spatial rhythm, and the AI slop test. Do NOT invoke the skill directly or run its teach flow — just apply its principles as you design.

Key i-impeccable principles to apply:
- **Font selection**: Follow the reflex rejection procedure. Don't reach for Inter, DM Sans, Playfair Display, etc. Find something that fits the brief as a *physical object*.
- **Colour**: Use OKLCH thinking. Tint neutrals toward the brand hue. Reduce chroma at extreme lightness. Dominant + sharp accent > timid even distribution.
- **No AI tells**: No left-border accent stripes. No gradient text. No glassmorphism. No identical card grids. No purple-to-blue gradients on dark backgrounds.
- **Theme choice**: Light vs dark should be derived from context, not defaulted.

**If i-impeccable is NOT available:**
You can still make good themes. Focus on clear hierarchy, readable contrast, and a cohesive palette. Avoid the most common AI design tells (left-border stripes, gradient text, cyan-on-dark).

---

## Step 1: Understand the brief

If the user gave a description as an argument (e.g. `/marp-theme-creator fans of early 60s UK sci-fi`), use that as the starting brief. Otherwise ask.

### What to ask (all at once, skip what's obvious)

**The vibe:**
> Describe the feel you're after — a genre, an era, a mood, a reference. "1970s Open University lecture" or "Japanese train station signage" or "cosy bookshop in Edinburgh" all work. The more specific and vivid, the better.

**The audience:**
> Who will see these presentations? Technical developers? University students? A conference audience? Children? This affects type size, density, and tone.

**Light or dark:**
> Any preference? If not, I'll choose based on the vibe. (A noir detective theme wants dark. A summer garden party theme wants light.)

**Anything that must or mustn't appear:**
> Specific colours to include? Logos? Anything to avoid?

### What NOT to ask

Don't ask about CSS, Marp directives, font names, or technical details. That's your job.

---

## Step 2: Design the theme

Work through these decisions before writing any CSS.

### 2a: Name the theme

Pick a short, lowercase, hyphenated name that captures the vibe: `retro-sci-fi`, `cosy-bookshop`, `cat-enthusiast`, `brutalist-concrete`. This becomes the `/* @theme name */` identifier.

### 2b: Choose the palette

Pick 3–5 colours that embody the brief:

1. **Background** — the slide surface. Sets the entire mood.
2. **Foreground** — body text colour. Must have strong contrast against background.
3. **Heading colour** — can be the same as foreground or a distinctive accent.
4. **Accent** — for links, list markers, inline code, highlights. Used sparingly.
5. **Muted** — for secondary text, footers, pagination. Recedes but stays readable.

Also choose:
- **Code block background** — almost always dark regardless of slide background, since syntax highlighting reads best on dark surfaces.
- **Code text colour** — the base colour for unhighlighted code text.

If i-impeccable is available: tint your neutrals toward the dominant hue. Use OKLCH thinking — reduce chroma at extreme lightness values.

### 2c: Choose the fonts

Pick TWO fonts from Google Fonts:
1. **Display font** — for headings. Should have personality that matches the brief.
2. **Body font** — for everything else. Must be highly readable at 20-28px.

Also pick a **monospace font** for code blocks.

If i-impeccable is available: follow the font selection procedure. Write down 3 words for the brief's voice. List the 3 fonts you'd normally reach for. Reject any on the reflex list. Browse further. Cross-check that your pick doesn't just confirm the pattern you're trying to break.

If i-impeccable is NOT available: aim for something distinctive that fits the brief. Avoid Inter, Roboto, Open Sans, and Arial. A serif + sans-serif pairing usually works well. Check Google Fonts for availability.

### 2d: Choose light or dark

Base this on the brief and audience context:
- Night-time, moody, technical, cinematic → dark
- Daytime, cheerful, educational, formal → light
- If the brief is ambiguous, go with your gut — just make a deliberate choice

### 2e: Plan the slide variants

Every theme should provide at minimum:
- **Base slide** — the default look
- **Lead slide** (`section.lead`) — for title and closing slides
- **Inverted slide** (`section.invert` or `section.light`) — the opposite brightness for emphasis
- **Divider slide** (`section.divider`) — section breaks

Optionally, if the brief suggests it, add one or two custom classes that fit the theme's character (e.g. `section.dramatic` for a noir theme, `section.whisper` for a quiet theme).

### 2f: Plan the syntax highlighting

If the code block background is dark (which it usually should be), you need custom `--color-prettylights-syntax-*` variable overrides. Design these to match the theme's palette:

- Keywords and control flow → use the accent colour or a warm/cool variant
- Strings → a complementary colour that reads well on the code background
- Comments → muted, clearly secondary, but still readable
- Functions/entities → a distinguishable third colour
- Variables/constants → a fourth colour if you can manage it without clashing

See `references/marp-theme-anatomy.md` for the full list of variables.

---

## Step 3: Write the CSS

Follow this structure exactly. Read `references/marp-theme-anatomy.md` for the technical details on why each section is needed.

```css
/* @theme theme-name */

@import 'default';
@import url('https://fonts.googleapis.com/css2?family=...');

:root {
  /* Theme palette */
  /* ... colour variables ... */

  /* Override default Marp theme variables */
  --borderColor-default: transparent;
  --bgColor-muted: transparent;
  --bgColor-default: transparent;

  /* Syntax highlighting */
  --color-prettylights-syntax-comment: ...;
  --color-prettylights-syntax-constant: ...;
  --color-prettylights-syntax-entity: ...;
  --color-prettylights-syntax-entity-tag: ...;
  --color-prettylights-syntax-keyword: ...;
  --color-prettylights-syntax-string: ...;
  --color-prettylights-syntax-variable: ...;
  --color-prettylights-syntax-brackethighlighter-angle: ...;
  --color-prettylights-syntax-brackethighlighter-unmatched: ...;
  --color-prettylights-syntax-carriage-return-bg: ...;
  --color-prettylights-syntax-carriage-return-text: ...;
  --color-prettylights-syntax-markup-heading: ...;
  --color-prettylights-syntax-markup-bold: ...;
  --color-prettylights-syntax-markup-italic: ...;
  --color-prettylights-syntax-markup-list: ...;
  --color-prettylights-syntax-storage-modifier-import: ...;
  --color-prettylights-syntax-string-regexp: ...;
}

/* BASE SLIDE */
section { ... }

/* HEADINGS */
section h1 { ... }
section h2 { ... }
section h3 { ... }

/* BODY TEXT & LINKS */
section p { ... }
section a { ... }
section strong { ... }

/* LISTS */
section ul, section ol { ... }
section li { ... }
section li::marker { ... }

/* CODE */
section code { ... }          /* inline code */
section pre { ... }           /* code block container */
section pre code { ... }      /* code block text */

/* BLOCKQUOTES */
section blockquote {
  border: none !important;    /* MUST include this */
  ...
}

/* TABLES */
section table { ... }
section table th { ... }
section table td { ... }
section table tr {
  background-color: transparent !important;  /* MUST include this */
}

/* HEADER & FOOTER */
header { position: absolute; top: 22px; left: 70px; right: 70px; ... }
footer { position: absolute; bottom: 22px; left: 70px; right: 70px; ... }

/* PAGINATION */
section::after { ... }

/* LEAD SLIDES */
section.lead { ... }
section.lead h1 { ... }
section.lead h2 { ... }

/* INVERTED / LIGHT SLIDES */
section.invert { ... }  /* or section.light for dark themes */

/* DIVIDER SLIDES */
section.divider { ... }

/* TWO-COLUMN LAYOUT */
section.cols {
  display: grid;
  grid-template-columns: 1fr 1fr;
  grid-template-rows: auto 1fr;
  gap: 0 48px;
  align-items: start;
}
section.cols h1, section.cols h2 {
  grid-column: 1 / -1;
}

/* Any custom slide classes ... */
```

### Mandatory rules (non-negotiable)

These fix default-theme inheritance issues. Include them in EVERY theme:

1. `:root` must set `--borderColor-default: transparent` — kills blockquote left borders
2. `:root` must set `--bgColor-muted: transparent` — kills table row striping
3. `:root` must set `--bgColor-default: transparent` — kills default background override
4. `section blockquote` must include `border: none !important`
5. `section table tr` must include `background-color: transparent !important`
6. If code blocks have dark backgrounds, ALL `--color-prettylights-syntax-*` variables must be overridden with colours readable on that background
7. Slide dimensions must use px: `width: 1280px; height: 720px`

### Quality checks

Before writing the file, mentally review:
- Is the heading text readable against the slide background?
- Is the body text readable? (Check lead slides too — they often have different backgrounds)
- Is the code block text readable? (Both the base colour AND the syntax highlight colours)
- Do blockquote and table styles look intentional, not like defaults leaked through?
- Does the theme have a clear visual identity, or could it be any theme?
- If i-impeccable is available: would this pass the AI slop test?

---

## Step 4: Set up and build

### Ensure marp-cli is available

```bash
npx @marp-team/marp-cli --version 2>/dev/null
```

If not:
```bash
npm init -y 2>/dev/null; npm install @marp-team/marp-cli
```

### Write the theme file

Save to `themes/<theme-name>.css`.

### Create a sample presentation

Generate a short (5–6 slide) sample presentation that exercises:
- A lead/title slide
- A content slide with bullet points
- A slide with a code block
- A slide with a table
- A blockquote slide
- A divider or custom-class slide

The content should relate to the theme's brief — not generic placeholder text. If the theme is "early 60s UK sci-fi", the sample should be about Daleks and Dan Dare, not "Lorem ipsum". This makes the preview delightful and helps the user evaluate whether the theme captures the vibe.

Save to `presentations/sample-<theme-name>.md`.

### Build and preview

```bash
mkdir -p themes presentations
npx @marp-team/marp-cli --theme-set ./themes/ presentations/sample-<theme-name>.md
open presentations/sample-<theme-name>.html  # macOS
```

---

## Step 5: Review with the user

Show the preview and ask:

> How does that feel? Is the vibe right? Anything you'd like adjusted — colours, fonts, mood, density?

Be ready to iterate on:
- Colour palette (too dark, too bright, wrong mood)
- Font choice (too formal, too playful, hard to read)
- Density (too much whitespace, too cramped)
- Specific elements (code blocks, tables, blockquotes)
- Adding or removing custom slide classes

---

## Important notes

- **Read `references/marp-theme-anatomy.md` before writing any CSS.** It contains critical information about how Marp compiles themes and the mandatory variable overrides.
- **Don't skip the mandatory rules.** Without them, default-theme styles will leak through and make the theme look broken.
- **Always build and preview.** Don't hand over a CSS file without compiling and showing the result.
- **The sample presentation matters.** Thematic content makes the preview compelling. Generic content makes it impossible to judge whether the vibe landed.
- **One theme per invocation.** If the user wants multiple themes, run the flow once for each.
