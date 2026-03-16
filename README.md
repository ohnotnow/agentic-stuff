# LLM Coding Skills and Agents

A curated set of reusable skills and task-focused agents for technical LLM coding workflows (Laravel/Livewire-heavy, but with some general-purpose patterns).

## Skills

- **ait** (`skills/ait/SKILL.md`): Local-first issue tracker for coding agents, useful for planning work, tracking multi-step tasks, modelling dependencies, coordinating between agents, and resuming after session loss or compaction.
- **frontend-design-with-flux** (`skills/frontend-fluxui/SKILL.md`): Practical Flux UI v2 + Livewire design guidance for building production-grade interfaces with consistent component patterns and sane defaults.
- **github-create** (`skills/github-create/SKILL.md`): Workflow for creating a brand-new GitHub repository from the current project, pushing code, and handling finishing touches like README, LICENSE, and repo metadata.
- **grounded-recommendation** (`skills/grounded-recommendation/SKILL.md`): Structured decision-making process for technical recommendations: investigate first, present findings, then make a recommendation with explicit uncertainty.
- **larastan** (`skills/larastan/SKILL.md`): Playbook for installing/configuring/running PHPStan + Larastan in Laravel projects, separating framework false positives from real defects and iterating analysis levels.
- **laravel-cloud** (`skills/laravel-cloud/SKILL.md`): Demo-app deployment and lifecycle workflow for Laravel Cloud using the `cloud` CLI, covering first deploys, updates, and teardown.
- **laravel-livewire-principles** (`skills/livewire-principles/SKILL.md`): Engineering principles for simpler Livewire code and tests, emphasizing framework trust, behavior-driven tests, and avoiding defensive over-engineering.
- **readme** (`skills/readme/SKILL.md`): README generator workflow that reads the real codebase, writes a GitHub-style `README.md`, and keeps claims grounded in the project.
- **technical-overview** (`skills/technical-overview/SKILL.md`): Generator workflow for creating concise `TECHNICAL_OVERVIEW.md` docs that map stack, architecture, domain model, routes, and key logic for rapid onboarding.
- **uofg-design-system** (`skills/uofg-design-system/SKILL.md`): University of Glasgow web design system guidance for HTML, CSS, React, Tailwind, FluxUI and general UI work using official UofG brand tokens, layout rules, and component patterns.
- **shell-function** (`skills/shell-function/SKILL.md`): Create a shell function appropriate for your shell (bash, zsh, fish, etc.) that does what you ask.

## Agents

- **ait-audit** (`agents/ait-audit.md`): Audit agent for reviewing open `ait` issues against the current codebase and reporting work that appears complete but has not been closed.
- **humaniser** (`agents/humaniser.md`): Editorial pass agent for removing common AI-writing patterns from generated text files like READMEs and docs.
- **modern-livewire** (`agents/modern-livewire.md`): Refactoring guide agent for modern Livewire v4/Flux v2 patterns that reduce component complexity and cognitive load.
- **plan-to-ait** (`agents/plan-to-ait.md`): Conversion agent for turning approved plan-mode plans or specific planning documents into consultant-ready `ait` epics and issues that a fresh coding agent can execute.
- **test-debug** (`agents/test-debug.md`): Lightweight debugging assistant for stubborn failing tests that prioritizes strategic `dump()` instrumentation over speculative rewrites.
- **test-quality-checker** (`agents/test-quality-checker.md`): Test-review agent that evaluates robustness and realism of Laravel tests, highlighting false-confidence patterns and practical coverage gaps.

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
