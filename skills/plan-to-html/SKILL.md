---
name: plan-to-html
description: "Convert a markdown plan (Claude plan-mode output, design doc, ait issue body, etc.) into a single self-contained, regular-user-friendly HTML file styled with the local design system. Use when the user wants to share a plan with non-technical stakeholders, send it for review, attach it to an email, or print it. Triggers on: 'turn this plan into html', 'export this plan', 'make this plan shareable', 'manager-friendly version', 'pretty version of this markdown', 'share this with my manager', or any request to convert a plan/spec/design markdown into a styled web document."
---

# Plan to HTML

Convert a markdown plan into a single self-contained, UofG-themed HTML file.

The whole point of this skill is to bridge the gap between agent-generated markdown plans (which developers love but regular users tend to open in Notepad and recoil from) and a polished document that is comfortable to read, prints well, and feels like a piece of corporate output rather than a code artefact.

## Workflow

### 1. Find the plan

The user may give you:

- **A path** to a markdown file — use it directly.
- **No path, but content from this conversation** (e.g. you just wrote a plan inline, or extracted one from plan mode). Write it to a temporary `.md` file first, then convert.
- **Nothing specific** — ask which file they want converted.

### 2. Pick a title and author

The script auto-derives the title from the first `# Heading` in the markdown, falling back to the filename. If the user has not made the title clear, briefly suggest one based on the content and confirm before generating. Optionally ask whether they want their name (or a team name) in the header.

### 3. Offer a "Background" preamble

The point of this skill is to bridge a gap to non-technical readers. A short collapsed accordion at the top of the page, summarising the **why** behind the plan, often makes the difference between a manager who reads and one who closes the tab.

**Offer to draft a preamble whenever:**

- The conversation that led to this plan is in your context (you and the developer just designed it together), and
- The plan is non-trivial (not a one-line button-move or typo fix).

**Skip the preamble (don't even ask) when:**

- The developer has explicitly said no, or said something like "it's a small thing, just convert it".
- The session is fresh and you have no conversation context to draw on — there's nothing to summarise.
- The plan describes work whose motivation is already obvious from a quick read.

**If you do offer**, ask once, briefly: *"Want me to add a short 'Background' summary at the top, captured from our discussion?"* — then accept the answer and move on.

#### Editorial register for the preamble

The audience is a manager, programme lead, or stakeholder. The register is **Sir Humphrey Appleby, not Malcolm Tucker**: courteous, measured, professional. Aim for a paragraph or two — three at most — that explains why this work is being done and the shape of the trade-offs, in plain language.

Hard rules:

- **Sanitise ruthlessly.** The developer may have vented, sworn, or been indiscreet. None of that goes in. Translate frustration into neutral facts ("the existing approach has been raising support load" rather than "everyone hates the bloody thing").
- **No techno-babble.** Avoid jargon, acronyms, framework names, and class names unless genuinely unavoidable. If you must mention one, gloss it ("the booking middleware — the component that authenticates users between pages").
- **Not ELI5 either.** Don't be condescending. Managers are intelligent generalists; treat them that way.
- **Capture the *why*, not the *what*.** The plan body already covers what is being done. The preamble's job is the motivation, the constraints (legal, deadlines, dependencies on other teams), and what's at stake if it's not done.
- **Acknowledge trade-offs honestly.** If the chosen approach has downsides, name them in one neutral sentence. Don't oversell.
- **Stay short.** A manager who wanted a 2,000-word essay would have asked for one.

If in doubt about whether something belongs, ask: *would I be comfortable if the developer's manager read this aloud in a steering meeting?* If not, leave it out.

#### How to pass the preamble in

Write the markdown to a temp file (`/tmp/plan-preamble-XXXX.md` or similar — never modify the user's plan file), then pass it via `--preamble-file`. The script renders it inside a collapsed `<details>` accordion labelled "Background", placed above the main plan content. It expands automatically when the document is printed.

### 4. Generate the HTML

Run the script via `uv run` (recommended — pulls deps into a cached venv automatically).  (If `uv` is not installed - explain to the user how to install it):

```bash
uv run ~/.claude/skills/plan-to-html/scripts/plan_to_html.py PLAN.md
```

With overrides:

```bash
uv run ~/.claude/skills/plan-to-html/scripts/plan_to_html.py PLAN.md \
  --title "Q2 Compliance Migration" \
  --author "Compliance Team" \
  -o ~/Desktop/q2-compliance.html
```

If the user does not have `uv` but does have a Python with the deps installed (`pip install markdown pymdown-extensions`), the same script works under plain Python:

```bash
python3 ~/.claude/skills/plan-to-html/scripts/plan_to_html.py PLAN.md
```

When `--output` is omitted, the file is written to the current directory as `{title-slug}-{YYYY-MM-DD}.html`.

### 5. Tell the user

Report the output path and suggest they double-click it (or `open` it on macOS) to preview. Mention that it prints cleanly via Cmd-P / Ctrl-P if they want to send a PDF.

## Flags

| Flag | Purpose |
|------|---------|
| `input` (positional) | Path to the markdown file |
| `-o`, `--output` | Output HTML path (default: derived from title + today's date) |
| `-t`, `--title` | Override the title (default: first H1, then filename) |
| `-a`, `--author` | Optional author/team shown in the header band |
| `--preamble-file` | Path to a markdown file rendered into a collapsed "Background" accordion above the plan |
| `--css` | Path to an alternate CSS file (default: bundled `theme.css`) |
| `--date` | Override the date string shown in the header |

## What the output looks like

- Navy gradient header band with a yellow accent rule, document title, date, and optional author
- Generous prose typography (Noto Sans, ~17px, 1.65 line-height, 72ch measure)
- H2 with a light underline; H3 in the brand blue
- Code blocks with a subtle blue left rule
- Tables with a blue header band and zebra striping
- Blockquotes with a left accent and tinted background
- GitHub-style task lists rendered as native checkboxes
- A `@media print` block that strips the dark header, removes the card shadow, and avoids breaking inside tables, code blocks, and blockquotes — so Cmd-P produces a clean PDF

## Customising the theme

The CSS lives at `~/.claude/skills/plan-to-html/theme.css` as a standalone, well-commented stylesheet. Three ways to tweak it:

1. **Edit it in place** — changes apply to every plan generated after the edit.
2. **Copy and pass with `--css`** — point the script at any CSS file you like, e.g. for a different brand or for personal experimentation.
3. **Share it** — the file is self-contained. Hand it to someone who wants the same look in their own tooling.

The colour and typography tokens at the top of `theme.css` are based on the University of Glasgow design system. The `uofg-design-system` skill has the full reference if you need to extend the palette.

## Layout

```
~/.claude/skills/plan-to-html/
├── SKILL.md
├── theme.css          ← edit me to change the look
└── scripts/
    └── plan_to_html.py
```
