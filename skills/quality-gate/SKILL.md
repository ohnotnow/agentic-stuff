---
name: quality-gate
description: Run a suite of review agents against the current codebase after completing feature work. Covers test quality, code complexity, security, and Livewire/Flux patterns. Always confirms before running due to token cost.
triggers:
  - /quality-gate
  - /review
  - run the quality gate
  - fresh eyes
---

# Quality Gate

Run independent review agents for a fresh-eyes assessment of recently completed work. Each agent has its own context and reports back without making changes.

**Important:** These agents consume significant tokens. Always confirm with the user before launching them.

## Available Reviewers

| Agent | What it checks | When to run |
|-------|---------------|-------------|
| `test-quality-checker` | Test robustness, weak assertions, missing edge cases | Always for Laravel work |
| `phpmetrics-check` | Code complexity hotspots, maintainability index | Always for Laravel work |
| `laravel-owasp-reporter` | Security: broken access control, mass assignment, IDOR, secrets | Always for Laravel work |
| `livewire-flux-reviewer` | Livewire/Flux modernisation opportunities | When significant Livewire/Flux code was written or modified |

## Process

### 1. Confirm scope and budget

Before running anything, tell the user what you'd recommend and ask:

> "The feature work looks substantial enough for a quality gate. I'd suggest running [list relevant agents]. These run in parallel but do burn through tokens - want to go ahead now, or save it for later?"

If the work was trivial (a config change, a one-liner fix, a copy tweak), don't suggest it at all.

### 2. Launch agents in parallel

All four agents are independent - launch them simultaneously in a single message. Each gets its own context and explores the codebase fresh.

### 3. Triage the findings

When the agents report back, **apply your context**. You were there for the implementation - you know why certain decisions were made. For each finding:

- **Agree and fix**: Genuine issues - security problems, weak tests, unnecessary complexity
- **Acknowledge but defer**: Valid points that aren't worth addressing right now (note them as ait issues for later)
- **Dismiss with reasoning**: Things the agent flagged that were deliberate choices - explain why to the user so they can confirm

Present a consolidated summary rather than dumping four raw reports. Group by severity, lead with anything that needs immediate attention.

## Selecting Agents

Not every review needs all four agents. Use judgement:

- **Small feature, no Livewire**: test-quality-checker + phpmetrics-check
- **API work**: test-quality-checker + laravel-owasp-reporter
- **Livewire-heavy feature**: all four
- **Refactoring only**: phpmetrics-check (complexity) + test-quality-checker (tests still passing for the right reasons)

Always let the user make the final call on which to run.
