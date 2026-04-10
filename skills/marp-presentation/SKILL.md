---
name: marp-presentation
description: "Create Marp markdown presentations through a guided workflow. Asks about audience and source material, picks the right theme, and builds the slides. Self-contained — bundles three custom themes and handles project setup. Triggers on: presentation, slideshow, slides, Marp, deck, talk, or any request to turn notes/data into a presentation."
user-invocable: true
argument-hint: "[topic or path to source material]"
---

# Marp Presentation Skill

Create polished markdown-based slide decks using [Marp](https://marp.app/). This skill is self-contained — it bundles three custom themes and handles all setup. Everything stays in plain text and is version-controllable.

## When to activate

- User asks to make a presentation, slideshow, slide deck, or talk
- User wants to turn notes, data, or ideas into slides
- User mentions Marp
- User says something like "let's make a presentation about X"

---

## Step 0: Project setup

Before doing anything else, silently ensure the working directory is ready to build Marp presentations.

### Install marp-cli if needed

Check if `@marp-team/marp-cli` is available:

```bash
npx @marp-team/marp-cli --version 2>/dev/null
```

If not available, install it:

```bash
npm init -y 2>/dev/null; npm install @marp-team/marp-cli
```

### Install themes

The three theme CSS files are bundled in this skill's `references/` directory. Copy them into the working directory:

```bash
mkdir -p themes
```

Then read each theme file from this skill's references and write it to `themes/`:
- `references/uofg.css` → `themes/uofg.css`
- `references/uofg-creative.css` → `themes/uofg-creative.css`
- `references/personal.css` → `themes/personal.css`

**Only copy if `themes/` doesn't already contain them** — the user may have customised their local copies.

### Create presentations directory

```bash
mkdir -p presentations
```

---

## Step 1: Understand the presentation

If the user hasn't already explained what they need, ask these questions. Skip any that are already obvious from context. Ask them all at once — don't drip-feed.

### What to ask

**Topic & purpose:**
> What's this presentation about, and what's the goal? (inform, persuade, teach, update, etc.)

**Audience:**
> Who will be watching? This determines which theme we use:
> - **Internal UofG / institutional** → `uofg` theme (clean, brand-compliant, Noto Sans, university blues)
> - **Mixed audience or external with UofG connection** → `uofg-creative` theme (UofG palette but with Literata serif headings, warmer surfaces, more visual personality)
> - **Personal, casual, or non-UofG** → `personal` theme (dark warm palette, Bricolage Grotesque headings, terracotta accents)

**Source material:**
> Do you have existing material to work from? For example:
> - Obsidian/markdown notes (give me the file paths or vault location)
> - A CSV or spreadsheet (I'll turn the data into tables and charts)
> - A document, PDF, or web page
> - Bullet points or an outline
> - Just a topic — I'll help structure it from scratch
>
> You can point me at multiple sources. I'll read everything and synthesise.

**Length & format:**
> Roughly how many slides? A 10-minute talk is typically 10–15 slides. A lightning talk is 5–8. A workshop deck might be 30+. If you're unsure, I'll aim for 12–15.

### What NOT to ask

Don't ask about fonts, colours, CSS, or technical Marp details. The themes handle all of that. The user just needs to think about content and audience.

---

## Step 2: Gather source material

Based on what the user said, read and process their source material.

### Obsidian / Markdown notes
- Read the files the user points to
- Look for structure: headings, bullet points, links between notes
- Identify the narrative arc — what order should things appear in?
- Pull out key quotes, data points, and examples

### CSV / Spreadsheet data
- Read the file
- Identify which columns and rows are most relevant
- Decide what belongs in tables vs what should be summarised as bullet points or key figures
- Keep tables concise — slides aren't spreadsheets. Max 5–6 rows per table, 4 columns. If there's more data, pick the most impactful subset and note what was left out

### Documents / PDFs
- Read and extract the key points
- Identify the structure and main arguments
- Pull out quotable lines for blockquote slides

### URLs / web pages
- Fetch and read the content
- Extract relevant information
- Credit the source in the slide footer or notes

### No source material
- Work with the user to build an outline
- Ask what 3–5 key points they want the audience to take away
- Suggest a structure (problem → solution → evidence → next steps, or similar)

---

## Step 3: Build the presentation

### File setup

Create the markdown file at an appropriate location. If the user doesn't specify, use `presentations/YYYY-MM-DD-topic-slug.md`.

### Frontmatter

```yaml
---
marp: true
theme: <chosen-theme>
paginate: true
header: '<contextual header>'
footer: '<contextual footer>'
---
```

Choose appropriate header/footer text. For UofG themes, the header might be the department or project name. For personal, it might be the presenter's name or nothing at all.

### Slide structure principles

**Open strong.** The title slide should make the audience curious, not just state the topic. A question, a surprising number, or a bold claim works better than "Quarterly Update Q3".

**One idea per slide.** If you're tempted to put two things on a slide, make two slides. Slides are free.

**Vary the rhythm.** Don't use the same layout for every slide. Mix:
- Text slides (bullet points, short paragraphs)
- Data slides (tables, key figures)
- Quote slides (blockquotes — good for breaking up dense sections)
- Divider slides (`<!-- _class: divider -->` — for section breaks)
- Lead slides (`<!-- _class: lead -->` — for title and closing)
- Image slides (background images with `![bg](path)`)
- Two-column slides (`<!-- _class: cols -->`)

**Keep text short.** Slides support the speaker, they don't replace the speaker. If a slide has more than ~40 words of body text, it's too much. Move detail to speaker notes (using HTML comments below the slide content).

**End with a clear call to action or takeaway.** Not just "Thanks / Questions?" but what should the audience do or remember?

### Slide classes reference

These CSS classes are available in all three themes:

| Directive | Effect |
|-----------|--------|
| `<!-- _class: lead -->` | Title/closing slides — large heading, themed background |
| `<!-- _class: invert -->` | Inverted colour scheme (UofG themes only) |
| `<!-- _class: divider -->` | Section divider — heading only, subtle background |
| `<!-- _class: cols -->` | Two-column layout (content splits at the heading) |
| `<!-- _class: light -->` | Light background variant (personal theme only) |
| `<!-- _class: accent -->` | Terracotta background for impact (personal theme only) |
| `<!-- _class: highlight -->` | Gold heading on navy for key takeaways (uofg-creative only) |

### Code blocks

For technical presentations, use fenced code blocks with language identifiers. The themes have custom syntax highlighting tuned for readability on their dark code block backgrounds.

### Tables

Keep tables simple. The themes style them with clean headers and no row striping. Don't cram too much data in — summarise instead.

### Speaker notes

Add speaker notes for anything the presenter needs to say but shouldn't be on the slide:
```markdown
<!--
This is where you'd explain the methodology in more detail.
The chart shows a 40% improvement but the sample size caveat is important.
-->
```

---

## Step 4: Build and preview

After creating the markdown file, compile it:

```bash
npx @marp-team/marp-cli --theme-set ./themes/ presentations/your-file.md
```

This produces an HTML file in the same directory. Open it for the user to preview:

```bash
open presentations/your-file.html   # macOS
xdg-open presentations/your-file.html  # Linux
```

If the user wants PDF output:
```bash
npx @marp-team/marp-cli --theme-set ./themes/ --pdf presentations/your-file.md
```

If the user wants to iterate with live preview:
```bash
npx @marp-team/marp-cli --theme-set ./themes/ -p presentations/your-file.md
```

---

## Step 5: Iterate

After showing the first build, ask:

> How does that look? Anything you'd like to change — order, emphasis, more/fewer slides, different tone?

Be ready to:
- Reorder slides
- Add or remove content
- Adjust tone (more formal, more casual, more technical)
- Add speaker notes
- Switch themes if the audience has changed
- Add data slides from additional source material

---

## Important notes

- **Don't over-explain Marp to the user.** They don't need to know about CSS themes or markdown directives. Just make the presentation.
- **Don't ask too many questions.** Get the essentials in Step 1, then produce a first draft. Iteration is cheaper than interrogation.
- **Don't modify the theme CSS.** Use the three themes as they are.
- **Always compile and open the result** so the user can see what they're getting.
- **This skill is self-contained.** The themes are bundled in `references/`. No external project or repo is needed.
