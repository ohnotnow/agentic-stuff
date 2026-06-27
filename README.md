# LLM coding skills and agents

Skills and agents I use with AI coding tools. Mostly Laravel/Livewire, but some are general-purpose.

---

> **Heads up (5th April 2026):** The Livewire/Flux skills and agents have been reorganised. `frontend-fluxui` is now `flux-ui`, `livewire-principles` is now `modern-livewire`, and the `livewire-flux-simplifier` agent has been replaced by `livewire-flux-reviewer`. There are also three new skills: `feature-workflow` (ait-driven feature development), `ui-to-flux` (migration helper), and `quality-gate` (post-feature review).
>
> If you've been using `./sync`, run `./migrate` to clean up the old names and pull in the new ones. If you copied files manually, have a read through the migrate script to see what's changed — it's short and commented.

---

## Skills

- `ait` -- Local-first [issue tracker for coding agents](https://github.com/ohnotnow/agent-issue-tracker). Tracks tasks, models dependencies, and helps agents pick up where they left off after session loss.
- `ait-recap` -- Generates a friendly markdown recap of recent `ait` activity for the current project or across a directory of projects. Handy for weekly status updates, "what shipped recently?" questions, and quick memory refreshers.
- `ant` -- Local-first [notebook for the *why*](https://github.com/ohnotnow/agent-note-tracker) behind project work. Captures decisions, alternatives rejected, pivots, and foundation context as a sibling to `ait`'s task tracking.
- `audience-credibility` -- Defensive review pass for audience-facing deliverables. Verifies named places, institutions, personas, and other local details before writing, then checks finished copy and visuals for recognisable AI-generated tells.
- `changelog` -- Analyses git tags and diffs to draft `CHANGELOG.md` entries in Keep a Changelog format. Proposes changes for review rather than writing them directly.
- `conversation-to-ait` -- Synthesises a feature discussion into a reviewed markdown brief, then hands it to the `plan-to-ait` agent to create `ait` issues.
- `conversation-to-html` -- Turns Claude Code or Codex session logs into single-file HTML transcripts you can share or present.
- `cruft-or-keep` -- Conversational second pair of eyes for reachable-but-dormant code. Builds evidence-grounded case files for suspect jobs, mailables, listeners, routes, commands, and asks the developer `cruft or keep?` rather than deleting anything.
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
- `quality-gate` -- Runs review agents (test quality, complexity, security, Livewire/Flux patterns) after feature work. Confirms before running due to token cost.
- `ui-to-flux` -- Migration skill for converting older Laravel apps (Bulma, Bootstrap, Tailwind) to Flux UI. References `flux-ui` and `modern-livewire` for target patterns rather than duplicating them.
- `ui-migration-screenshots` -- Captures full-page reference screenshots of existing app UIs before or during frontend migrations. Uses Playwright for authenticated, role-gated, and interactive flows so rebuilt pages can keep a familiar 1:1 mapping.
- `readme` -- Generates a README from the actual codebase so claims stay grounded.
- `technical-overview` -- Generates a `TECHNICAL_OVERVIEW.md` covering stack, architecture, domain model, routes, and key logic. Useful for onboarding.
- `uofg-design-system` -- University of Glasgow web design system. Brand tokens, layout rules, and component patterns for HTML, CSS, React, Tailwind, and FluxUI.
- `shell-function` -- Creates a shell function (bash, zsh, fish, etc.) that does what you describe.
- `sop-creator` -- Writes Standard Operating Procedure documents from user outlines. Asks minimal clarifying questions, then generates a clean Markdown SOP with purpose, prerequisites, procedure, and verification steps.

## Agents

- `ait-audit.md` -- Reviews open `ait` issues against the codebase and flags work that looks done but hasn't been closed.
- `fresh-eyes.md` -- Fresh pair of eyes for when you're stuck or looping. Suggests one or two things to try rather than editing code directly.
- `humaniser.md` -- Removes common AI-writing patterns from text files like READMEs and docs.
- `laravel-owasp-reporter.md` -- OWASP-aligned security sweep of a Laravel app. Reports actual exploitable findings with concrete fixes.
- `livewire-flux-reviewer.md` -- Reviews Livewire/Flux code for simplification opportunities. Quick wins, things worth considering, and what looks good. References `flux-ui` and `modern-livewire` skills for pattern details.
- `phpmetrics-check.md` -- Runs phpmetrics on a PHP/Laravel codebase, flags complexity hotspots, and compares against a saved baseline.
- `plan-reconciler.md` -- Reconciles a plan document against the conversation that produced it. Reports what was captured, missed, glossed over, or drifted without editing the plan.
- `plan-to-ait.md` -- Turns approved plans into `ait` epics and issues that a fresh coding agent can execute without context.
- `test-debug.md` -- Debugging assistant for stubborn failing tests. Uses `dump()` instrumentation rather than speculative rewrites.
- `test-quality-checker.md` -- Reviews Laravel tests for false-confidence patterns and coverage gaps.

## Syncing to your tools

Different AI coding tools (Claude Code, Codex, Gemini, Cursor, etc.) each have their own config directories for skills, agents and commands. The `sync` script copies everything from this repo into the right places.

1. Copy the example config: `cp sync.yaml.example sync.yaml`
2. Enable the tools you use and adjust paths if needed (`sync.yaml` is gitignored).
3. Run `./sync` (requires [uv](https://docs.astral.sh/uv/)).

If a destination file is **newer** than the repo source, the script will warn you and offer a diff before overwriting — handy if you've been editing skills in-place. Skipped files are listed at the end for easy copy-back.

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
