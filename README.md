# LLM coding skills and agents

Skills and agents I use with AI coding tools. Mostly Laravel/Livewire, but some are general-purpose.

---

> **Heads up (11th July 2026):** The plan-to-ait pipeline has been restructured for stronger main agents. The issue-crafting knowledge (epic/issue templates, testing modes, the amnesia test) now lives in a new `ait-crafting` skill, so the main agent can create issues straight from a feature conversation; the `plan-to-ait` agent is now a thin shell that loads that skill. There's also a new `ait-amnesia-check` agent — a fresh-context checker that *demonstrates* what it would build from newly created issues (never a verdict), so the caller can diff its reading against the real intent. The `conversation-to-ait` skill has been absorbed into `ait-crafting` and removed — if you'd previously synced it, delete it from your tool config (e.g. `rm -rf ~/.claude/skills/conversation-to-ait`).

---

> **Heads up (3rd July 2026):** `quality-gate` has grown into a two-tier review stack: free deterministic checks first (a section-order checker for Eloquent models and Livewire components in `skills/quality-gate/scripts/`, plus a drop-in Pest architecture test in `skills/quality-gate/arch/`), then the reviewer agents, all briefed via `skills/quality-gate/briefing.md` with whole-file reading rules. There's a new `laravel-conventions-reviewer` agent, and `test-quality-checker` now also hunts tautological tests, unit-tests-that-should-be-feature-tests, and test proliferation. The section order, arch rules, and conventions checklist encode *our* house style — read through and tweak them to yours before adopting.

---

> **Heads up (5th April 2026):** The Livewire/Flux skills and agents have been reorganised. `frontend-fluxui` is now `flux-ui`, `livewire-principles` is now `modern-livewire`, and the `livewire-flux-simplifier` agent has been replaced by `livewire-flux-reviewer`. There are also three new skills: `feature-workflow` (ait-driven feature development), `ui-to-flux` (migration helper), and `quality-gate` (post-feature review).
>
> If you've been using `./sync`, run `./migrate` to clean up the old names and pull in the new ones. If you copied files manually, have a read through the migrate script to see what's changed — it's short and commented.

---

## Skills

- `ait` -- Local-first [issue tracker for coding agents](https://github.com/ohnotnow/agent-issue-tracker). Tracks tasks, models dependencies, and helps agents pick up where they left off after session loss.
- `ait-crafting` -- Turns a settled feature discussion or plan document into consultant-ready `ait` issues: an initiative/epic vision document plus implementation specs a fresh agent could pick up cold. Includes a "does this capture it?" review gate for conversation-sourced work, and pairs with the `ait-amnesia-check` agent for a fresh-eyes conveyance check. Also the knowledge base for the `plan-to-ait` agent.
- `ait-recap` -- Generates a friendly markdown recap of recent `ait` activity for the current project or across a directory of projects. Handy for weekly status updates, "what shipped recently?" questions, and quick memory refreshers.
- `ant` -- Local-first [notebook for the *why*](https://github.com/ohnotnow/agent-note-tracker) behind project work. Captures decisions, alternatives rejected, pivots, and foundation context as a sibling to `ait`'s task tracking.
- `audience-credibility` -- Defensive review pass for audience-facing deliverables. Verifies named places, institutions, personas, and other local details before writing, then checks finished copy and visuals for recognisable AI-generated tells.
- `changelog` -- Analyses git tags and diffs to draft `CHANGELOG.md` entries in Keep a Changelog format. Proposes changes for review rather than writing them directly.
- `conversation-to-html` -- Turns Claude Code or Codex session logs into single-file HTML transcripts you can share or present.
- `cruft-or-keep` -- Conversational second pair of eyes for reachable-but-dormant code. Builds evidence-grounded case files for suspect jobs, mailables, listeners, routes, commands, and asks the developer `cruft or keep?` rather than deleting anything.
- `expand-issue` -- Fleshes out a terse "note to self" `ait` issue into a proper plan. Explores the codebase to work out what past-you meant, makes reasonable assumptions (and lists them for correction), and produces a plan document ready for `plan-to-ait`. Handy for drive-by brain dumps you want to pick up properly the next day.
- `feature-workflow` -- Streamlined workflow for building features with `ait` issue tracking. Handles orientation, planning (via plan mode), issue creation (via `plan-to-ait`), implementation with acceptance criteria checking, and optional quality gate at the end.
- `flux-ui` -- Flux UI v2 component reference for Laravel/Livewire. Covers syntax, patterns, common mistakes, and modal/form/table patterns.
- `github-create` -- Creates a new GitHub repo from the current project, pushes code, and sorts out the README, licence, and metadata.
- `golang` -- Conventions and patterns for Go CLI/TUI projects. Covers project layout, SQLite storage, Bubble Tea TUIs, embedded web UIs, flag parsing, migrations, error handling, and testing.
- `grounded-recommendation` -- Makes the agent investigate before recommending. Present findings first, then a recommendation with explicit uncertainty.
- `homebrew-spring-clean` -- Walks developers through tidying `/opt/homebrew` (or `/usr/local` on Intel Macs). Surveys Homebrew disk usage, ranks cleanup targets, and handles cleanup, leaves, casks, stale logs, and autoremove without auto-deleting anything.
- `i-impeccable` -- Distinctive frontend/design implementation skill. Establishes design context, commits to a bold visual direction, and builds polished interfaces that avoid generic AI aesthetics. Supports `teach` for context setup, `craft` for shape-then-build, and `extract` for pulling reusable design tokens and components into the system.
- `i-shape` -- UX/UI shaping skill for planning a feature before code. Runs a structured discovery interview, then produces a design brief covering direction, layout strategy, key states, interactions, content, and the most relevant `i-impeccable` references for implementation.
- `improve` -- Senior-advisor audit and handoff-planning skill. Surveys codebases for bugs, security, performance, tests, tech debt, dependencies, DX, docs, and direction, then writes self-contained plans for other agents to execute while staying read-only on source.
- `larastan` -- Installs and runs PHPStan + Larastan, separates framework false positives from real defects, and iterates through analysis levels.
- `livewire-v4-upgrade` -- Audit-first workflow for upgrading production Laravel apps from Livewire v3 to v4. Covers app-shape triage, `wire:model` changes, layout/config traps, legacy model binding remediation, test baselines, browser smoke tests, and deploy pipeline gotchas.
- `marp-presentation` -- Guided workflow for creating Marp slide decks. Asks about audience and source material, picks from three bundled themes, and handles setup, compilation, and preview. Turns notes, CSVs, or just a topic into polished slides.
- `marp-theme-creator` -- Creates custom Marp presentation themes from a vibe or description. Walks through palette, font, and layout decisions, then generates production-ready CSS with a themed sample deck. Detects the `i-impeccable` skill for enhanced design thinking.
- `laravel-cloud` -- Deploy, update, and tear down demo apps on Laravel Cloud using the `cloud` CLI.
- `modern-livewire` -- How we write Livewire components: principles, patterns, form state, testing. Covers everything from `findOrNew`+`fill`+`save` to named modals and `wire:model` behaviour.
- `plan-to-html` -- Converts markdown plans, design docs, and issue writeups into self-contained HTML documents for sharing with non-technical stakeholders. Includes a stylesheet you can customise, optional author/title metadata, print-friendly output, and an optional Background preamble for context.
- `practical-laravel-api` -- Conventions for practical, consumer-friendly Laravel JSON APIs with Sanctum. Covers self-describing response shapes, loud query failures, slugs, date windows, filtering, Scramble docs, and tests for API contracts.
- `quality-gate` -- One-stop post-feature review: free deterministic checks first (model/Livewire section-order script, drop-in Pest arch test), then fresh-eyes review agents. Two scopes — recent work, or a whole legacy codebase chunked by model orbit and delegated to a sub-orchestrator. Confirms before spending agent tokens.  (Note: it likes to ask you to commit a lot - if you don't trust your agent to do git stuff, have a look at [agent-commit](https://github.com/ohnotnow/agent-commit)).
- `ui-to-flux` -- Migration skill for converting older Laravel apps (Bulma, Bootstrap, Tailwind) to Flux UI. References `flux-ui` and `modern-livewire` for target patterns rather than duplicating them.
- `ui-migration-screenshots` -- Captures full-page reference screenshots of existing app UIs before or during frontend migrations. Uses Playwright for authenticated, role-gated, and interactive flows so rebuilt pages can keep a familiar 1:1 mapping.
- `readme` -- Generates a README from the actual codebase so claims stay grounded.
- `technical-overview` -- Generates a `TECHNICAL_OVERVIEW.md` covering stack, architecture, domain model, routes, and key logic. Useful for onboarding.
- `uofg-design-system` -- University of Glasgow web design system. Brand tokens, layout rules, and component patterns for HTML, CSS, React, Tailwind, and FluxUI.
- `shell-function` -- Creates a shell function (bash, zsh, fish, etc.) that does what you describe.
- `sop-creator` -- Writes Standard Operating Procedure documents from user outlines. Asks minimal clarifying questions, then generates a clean Markdown SOP with purpose, prerequisites, procedure, and verification steps.

## Agents

- `ait-amnesia-check.md` -- Fresh-eyes amnesia test for newly created `ait` issues. With no conversation context it demonstrates what it would build from each spec — restated goal, files, first failing test, every guess and dead end marked — so the caller can diff its reading against the real intent. Never gives a verdict.
- `ait-audit.md` -- Reviews open `ait` issues against the codebase and flags work that looks done but hasn't been closed.
- `fresh-eyes.md` -- Fresh pair of eyes for when you're stuck or looping. Suggests one or two things to try rather than editing code directly.
- `humaniser.md` -- Removes common AI-writing patterns from text files like READMEs and docs.
- `laravel-conventions-reviewer.md` -- Reviews Laravel code against team conventions: readable model helpers over raw column checks, fat models, Eloquent over query-building, enums over strings, duplicate-purpose methods. Seeded with real before/after examples — swap in your own house style before adopting.
- `laravel-owasp-reporter.md` -- OWASP-aligned security sweep of a Laravel app. Reports actual exploitable findings with concrete fixes.
- `livewire-flux-reviewer.md` -- Reviews Livewire/Flux code for simplification opportunities. Quick wins, things worth considering, and what looks good. References `flux-ui` and `modern-livewire` skills for pattern details.
- `phpmetrics-check.md` -- Runs phpmetrics on a PHP/Laravel codebase, flags complexity hotspots, and compares against a saved baseline.
- `plan-reconciler.md` -- Reconciles a plan document against the conversation that produced it. Reports what was captured, missed, glossed over, or drifted without editing the plan.
- `plan-to-ait.md` -- Turns approved plan documents into `ait` epics and issues that a fresh coding agent can execute without context. Now a thin shell around the `ait-crafting` skill, which holds the templates and quality bar.
- `test-debug.md` -- Debugging assistant for stubborn failing tests. Uses `dump()` instrumentation rather than speculative rewrites.
- `test-quality-checker.md` -- Reviews Laravel tests for false-confidence patterns and coverage gaps: tautologies, weak assertions, missing control records, unit tests that should be feature tests.

## Syncing to your tools

Different AI coding tools (Claude Code, Codex, Gemini, Cursor, etc.) each have their own config directories for skills, agents and commands. The `sync` script copies everything from this repo into the right places.

1. Copy the example config: `cp sync.yaml.example sync.yaml`
2. Enable the tools you use and adjust paths if needed (`sync.yaml` is gitignored).
3. Run `./sync` (requires [uv](https://docs.astral.sh/uv/)).

If a destination file is **newer** than the repo source *and actually differs*, the script will warn you and offer a diff before overwriting — handy if you've been editing skills in-place. Identical files are left alone whatever their timestamps say. Skipped files are listed at the end for easy copy-back.

To skip specific items entirely (e.g. you have your own `readme` skill), add an `ignore` block globally or per-target in `sync.yaml`:

```yaml
# Never sync these to any target
ignore:
  skills: [readme]

targets:
  claude:
    enabled: true
    skills: ~/.claude/skills/
    # Also skip these for claude specifically
    ignore:
      skills: [uofg-design-system]
```

```
./sync             # sync with prompts for newer destinations
./sync --dry-run   # preview only
./sync --force     # overwrite everything without asking
```

### Pulling in sibling repos with `sources`

Not everything lives in this repo — some tools ship as standalone repos that carry their own skills and agents alongside their code. Rather than remembering a separate install step for each, `sync.yaml` can list extra source directories and `./sync` treats their contents as if they lived here:

```yaml
sources:
  - ~/code/ux-agent/claude
  - ~/code/a11y-agent/claude
```

Each entry points at a directory that itself contains `skills/`, `agents/` and/or `commands/`. Every mode sees the merged set — the full sync, `--dry-run`, `pick`, and `preset` bundles can all draw from sources. On a name collision the first provider wins (this repo beats sources, earlier sources beat later ones) and the shadowed copy is reported, so nothing disappears quietly. `ignore` blocks apply to sourced items like anything else.

### Project-local skills with `pick` and `preset`

The default `./sync` is a full reconcile against your global tool config. But quite often you want the opposite — a fresh project where only a *handful* of skills/agents are relevant, dropped into the project's own `./.claude/` directory. Two modes for that:

```
./sync pick --to ~/code/my-project/.claude/           # interactive fuzzy picker
./sync preset go --to ~/code/my-project/.claude/      # named bundle from sync.yaml
```

Both treat `--to` as a base path — items land in `PATH/skills/<name>`, `PATH/agents/<name>`, etc. Neither touches `sync.yaml`'s `targets` block, so global syncs are unaffected.

#### `pick` — fuzzy picker with preview

Opens an [fzf](https://github.com/junegunn/fzf) multi-select across every available skill, agent and command. Type to filter, Tab to toggle, Enter to copy. The preview pane on the right shows each skill's `SKILL.md` (or the file itself for agents/commands), so you can browse and pick in one motion instead of remembering what each name does.

Items are tagged so the filter doubles as a scope:
- `[s]` skills
- `[a]` agents
- `[c]` commands

Typing `s golang` finds the Go skill; typing `[a]` shows all agents.

Requires `fzf` on PATH. If you don't have it, install via [the fzf docs](https://github.com/junegunn/fzf#installation) or use `preset` mode below.

#### `preset` — named bundles for shell aliases

For the "every Go project gets these three skills" case, declare a bundle in `sync.yaml`:

```yaml
presets:
  go:
    skills: [golang, github-create, changelog]
    agents: [test-debug]
  laravel:
    skills: [flux-ui, modern-livewire, larastan]
    agents: [livewire-flux-reviewer]
```

Then a one-line shell function gets you a zero-friction alias:

```bash
gopick() { /path/to/agentic-stuff/sync preset go --to "$PWD/.claude/"; }
```

`cd` into a fresh repo, type `gopick`, done.

`--dry-run` previews either mode without writing anything; `--force` skips the "destination is newer than repo source" prompts.

`--dry-run` and `--force` work for both modes.

## You might also be interested in

Two standalone repos that pair well with this collection — the `quality-gate` skill knows how to call on both, and the `sources:` block above will sync their skills and agents alongside these:

- [a11y-agent](https://github.com/ohnotnow/a11y-agent) — a deterministic accessibility CLI (axe scan, keyboard tab-order walk, screen-reader transcript) with its own Claude Code skill and background checker agent. Makes the a11y audit nobody gets time for nearly free.
- [ux-agent](https://github.com/ohnotnow/ux-agent) — skills that drive a real browser against your local app to produce bug-reproduction videos, user-guide videos that re-film themselves, and cold UX journey reports from a code-blind probe agent.
