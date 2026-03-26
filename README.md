# LLM coding skills and agents

Skills and agents I use with AI coding tools. Mostly Laravel/Livewire, but some are general-purpose.

## Skills

- `skills/ait/SKILL.md` -- Local-first [issue tracker for coding agents](https://github.com/ohnotnow/agent-issue-tracker). Tracks tasks, models dependencies, and helps agents pick up where they left off after session loss.
- `skills/changelog/SKILL.md` -- Analyses git tags and diffs to draft `CHANGELOG.md` entries in Keep a Changelog format. Proposes changes for review rather than writing them directly.
- `skills/conversation-to-html/SKILL.md` -- Turns Claude Code or Codex session logs into single-file HTML transcripts you can share or present.
- `skills/frontend-fluxui/SKILL.md` -- Flux UI v2 + Livewire design guidance. Consistent component patterns, sensible defaults.
- `skills/github-create/SKILL.md` -- Creates a new GitHub repo from the current project, pushes code, and sorts out the README, licence, and metadata.
- `skills/grounded-recommendation/SKILL.md` -- Makes the agent investigate before recommending. Present findings first, then a recommendation with explicit uncertainty.
- `skills/larastan/SKILL.md` -- Installs and runs PHPStan + Larastan, separates framework false positives from real defects, and iterates through analysis levels.
- `skills/laravel-cloud/SKILL.md` -- Deploy, update, and tear down demo apps on Laravel Cloud using the `cloud` CLI.
- `skills/livewire-principles/SKILL.md` -- Principles for simpler Livewire code and tests. Trust the framework, test behaviour not implementation, don't over-engineer.
- `skills/readme/SKILL.md` -- Generates a README from the actual codebase so claims stay grounded.
- `skills/technical-overview/SKILL.md` -- Generates a `TECHNICAL_OVERVIEW.md` covering stack, architecture, domain model, routes, and key logic. Useful for onboarding.
- `skills/uofg-design-system/SKILL.md` -- University of Glasgow web design system. Brand tokens, layout rules, and component patterns for HTML, CSS, React, Tailwind, and FluxUI.
- `skills/shell-function/SKILL.md` -- Creates a shell function (bash, zsh, fish, etc.) that does what you describe.

## Agents

- `agents/ait-audit.md` -- Reviews open `ait` issues against the codebase and flags work that looks done but hasn't been closed.
- `agents/humaniser.md` -- Removes common AI-writing patterns from text files like READMEs and docs.
- `agents/laravel-owasp-reporter.md` -- OWASP-aligned security sweep of a Laravel app. Reports actual exploitable findings with concrete fixes.
- `agents/modern-livewire.md` -- Refactors towards modern Livewire v4/Flux v2 patterns to cut component complexity.
- `agents/plan-to-ait.md` -- Turns approved plans into `ait` epics and issues that a fresh coding agent can execute without context.
- `agents/test-debug.md` -- Debugging assistant for stubborn failing tests. Uses `dump()` instrumentation rather than speculative rewrites.
- `agents/test-quality-checker.md` -- Reviews Laravel tests for false-confidence patterns and coverage gaps.

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
