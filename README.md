# LLM Coding Skills and Agents

A curated set of reusable skills and task-focused agents for technical LLM coding workflows (Laravel/Livewire-heavy, but with some general-purpose patterns).

## Skills

- **beads** (`skills/beads/SKILL.md`): Quick-reference workflow for the `bd` Git-backed issue tracker, including dependencies, epics, and session-to-session continuity.
- **frontend-design-with-flux** (`skills/frontend-fluxui/SKILL.md`): Practical Flux UI v2 + Livewire design guidance for building production-grade interfaces with consistent component patterns and sane defaults.
- **grounded-recommendation** (`skills/grounded-recommendation/SKILL.md`): Structured decision-making process for technical recommendations: investigate first, present findings, then make a recommendation with explicit uncertainty.
- **larastan** (`skills/larastan/SKILL.md`): Playbook for installing/configuring/running PHPStan + Larastan in Laravel projects, separating framework false positives from real defects and iterating analysis levels.
- **laravel-livewire-principles** (`skills/livewire-principles/SKILL.md`): Engineering principles for simpler Livewire code and tests, emphasizing framework trust, behavior-driven tests, and avoiding defensive over-engineering.
- **technical-overview** (`skills/technical-overview/SKILL.md`): Generator workflow for creating concise `TECHNICAL_OVERVIEW.md` docs that map stack, architecture, domain model, routes, and key logic for rapid onboarding.

## Agents

- **beads-audit** (`agents/beads-audit.md`): Audits open Beads issues against the codebase and reports likely-complete vs still-open items with evidence, without mutating issue state.
- **modern-livewire** (`agents/modern-livewire.md`): Refactoring guide agent for modern Livewire v4/Flux v2 patterns that reduce component complexity and cognitive load.
- **plan-to-beads** (`agents/plan-to-beads.md`): Converts approved planning artifacts into consultant-ready Beads epics/issues with dependencies, implementation detail, and handoff quality.
- **test-debug** (`agents/test-debug.md`): Lightweight debugging assistant for stubborn failing tests that prioritizes strategic `dump()` instrumentation over speculative rewrites.
- **test-quality-checker** (`agents/test-quality-checker.md`): Test-review agent that evaluates robustness and realism of Laravel tests, highlighting false-confidence patterns and practical coverage gaps.

