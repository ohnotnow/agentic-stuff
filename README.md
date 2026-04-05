# LLM coding skills and agents

Skills and agents I use with AI coding tools. Mostly Laravel/Livewire, but some are general-purpose.

---

> **Heads up (5th April 2026):** The Livewire/Flux skills and agents have been reorganised. `frontend-fluxui` is now `flux-ui`, `livewire-principles` is now `modern-livewire`, and the `livewire-flux-simplifier` agent has been replaced by `livewire-flux-reviewer`. There are also three new skills: `feature-workflow` (ait-driven feature development), `ui-to-flux` (migration helper), and `quality-gate` (post-feature review).
>
> If you've been using `./sync`, run `./migrate` to clean up the old names and pull in the new ones. If you copied files manually, have a read through the migrate script to see what's changed — it's short and commented.

---

## Skills

- `ait` -- Local-first [issue tracker for coding agents](https://github.com/ohnotnow/agent-issue-tracker). Tracks tasks, models dependencies, and helps agents pick up where they left off after session loss.
- `changelog` -- Analyses git tags and diffs to draft `CHANGELOG.md` entries in Keep a Changelog format. Proposes changes for review rather than writing them directly.
- `conversation-to-html` -- Turns Claude Code or Codex session logs into single-file HTML transcripts you can share or present.
- `feature-workflow` -- Streamlined workflow for building features with `ait` issue tracking. Handles orientation, planning (via plan mode), issue creation (via `plan-to-ait`), implementation with acceptance criteria checking, and optional quality gate at the end.
- `flux-ui` -- Flux UI v2 component reference for Laravel/Livewire. Covers syntax, patterns, common mistakes, and modal/form/table patterns.
- `github-create` -- Creates a new GitHub repo from the current project, pushes code, and sorts out the README, licence, and metadata.
- `golang` -- Conventions and patterns for Go CLI/TUI projects. Covers project layout, SQLite storage, Bubble Tea TUIs, embedded web UIs, flag parsing, migrations, error handling, and testing.
- `grounded-recommendation` -- Makes the agent investigate before recommending. Present findings first, then a recommendation with explicit uncertainty.
- `larastan` -- Installs and runs PHPStan + Larastan, separates framework false positives from real defects, and iterates through analysis levels.
- `laravel-cloud` -- Deploy, update, and tear down demo apps on Laravel Cloud using the `cloud` CLI.
- `modern-livewire` -- How we write Livewire components: principles, patterns, form state, testing. Covers everything from `findOrNew`+`fill`+`save` to named modals and `wire:model` behaviour.
- `quality-gate` -- Runs review agents (test quality, complexity, security, Livewire/Flux patterns) after feature work. Confirms before running due to token cost.
- `ui-to-flux` -- Migration skill for converting older Laravel apps (Bulma, Bootstrap, Tailwind) to Flux UI. References `flux-ui` and `modern-livewire` for target patterns rather than duplicating them.
- `readme` -- Generates a README from the actual codebase so claims stay grounded.
- `technical-overview` -- Generates a `TECHNICAL_OVERVIEW.md` covering stack, architecture, domain model, routes, and key logic. Useful for onboarding.
- `uofg-design-system` -- University of Glasgow web design system. Brand tokens, layout rules, and component patterns for HTML, CSS, React, Tailwind, and FluxUI.
- `shell-function` -- Creates a shell function (bash, zsh, fish, etc.) that does what you describe.
- `sop-creator` -- Writes Standard Operating Procedure documents from user outlines. Asks minimal clarifying questions, then generates a clean Markdown SOP with purpose, prerequisites, procedure, and verification steps.

## Agents

- `ait-audit.md` -- Reviews open `ait` issues against the codebase and flags work that looks done but hasn't been closed.
- `humaniser.md` -- Removes common AI-writing patterns from text files like READMEs and docs.
- `laravel-owasp-reporter.md` -- OWASP-aligned security sweep of a Laravel app. Reports actual exploitable findings with concrete fixes.
- `livewire-flux-reviewer.md` -- Reviews Livewire/Flux code for simplification opportunities. Quick wins, things worth considering, and what looks good. References `flux-ui` and `modern-livewire` skills for pattern details.
- `phpmetrics-check.md` -- Runs phpmetrics on a PHP/Laravel codebase, flags complexity hotspots, and compares against a saved baseline.
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
