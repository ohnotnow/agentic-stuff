---
name: quality-gate
description: One-stop code review after feature work, or for a whole codebase. Runs deterministic checks (section ordering, arch conventions) free of charge, then fresh-eyes Opus reviewer agents. Covers team conventions, test quality, complexity, security, and Livewire/Flux patterns. Always confirms before spending agent tokens.
triggers:
  - /quality-gate
  - /review
  - run the quality gate
  - fresh eyes
---

# Quality Gate

One entry point for post-work review. The developer should never have to
remember which reviewer exists - picking them is this skill's job.

Two scopes:

- **Recent work** (default, the common case): commits since the merge-base
  with master/main, plus unstaged and untracked changes.
- **Whole codebase** (explicit opt-in, e.g. "review the whole app"): for
  legacy or inherited apps. Delegated - see below.

Reviewers always receive **file lists, never diffs**. A diff tells a reviewer
where to look; only the whole file tells them what's actually there.

## Tier zero - deterministic checks (run these before any agent)

Lint what's lintable; spend judgement tokens on judgement.

1. **Section ordering**:
   `php ~/.claude/skills/quality-gate/scripts/section-order-check.php <repo-path>`
   Report-only; exit 1 means violations - put them straight in the final
   report. If it dies on an unloadable class, that IS a finding (a class that
   can't load is the most urgent thing a review can surface).
2. **Arch conventions**: check `tests/` for `TeamConventionsTest.php`. If
   missing, offer to install the canonical copy from
   `~/.claude/skills/quality-gate/arch/TeamConventionsTest.php` into
   `tests/Feature/` - **ask first, never install silently**. On a legacy app,
   adopt with `ignoring()` on current offenders and burn the list down. If
   already installed it runs with the app's own suite; nothing extra to do.

## Reviewer roster

| Agent | What it checks | When to run |
|-------|---------------|-------------|
| `laravel-conventions-reviewer` | Readable model helpers, fat models, DB:: query building, enums, duplicate-purpose methods | Always for Laravel work |
| `test-quality-checker` | Weak assertions, tautological tests, unit-vs-feature, proliferation, missing edge cases | Always for Laravel work |
| `phpmetrics-check` | Complexity hotspots, maintainability | Always for Laravel work |
| `laravel-owasp-reporter` | Broken access control, mass assignment, IDOR, secrets | API or auth-touching work |
| `livewire-flux-reviewer` | Livewire/Flux modernisation | When Livewire/Flux code changed |

## Confirm before spending

Tier zero is free - run it without asking. Opus reviewers are not. Before
launching any, tell the user what tier zero found, which reviewers fit this
scope, and ask. If the work was trivial (config change, copy tweak), don't
suggest reviewers at all.

## Briefing

Every reviewer prompt = the briefing block from
`~/.claude/skills/quality-gate/briefing.md` (verbatim - each rule exists
because of an observed failure mode) + the file list. The briefing governs
what reviewers read and how much they report; their own agent definitions
govern report format.

## Recent-work mode (the common case)

Launch the selected reviewers **in parallel from the main conversation**, each
with briefing + file list. When reports come back, triage with your
implementation context - you were there:

- **Agree and fix**: genuine issues - fix now
- **Acknowledge but defer**: valid but not now - record as ait issues
- **Dismiss with reasoning**: deliberate choices the reviewer couldn't know -
  explain to the user so they can confirm

Present one consolidated summary, severity first, never four raw reports.

## Whole-codebase mode (delegated)

There is no implementation context to lose on a legacy codebase, and the
chunk-review noise would swamp the main conversation - so delegate the lot.
Confirm the token budget with the user first; this is the expensive path.

Launch ONE general-purpose orchestrator agent instructed to:

1. **Chunk by model orbit, deterministically** (a bare "pick the central
   files" judgement call produced unreproducible chunks in the pilot): the
   model + its factory + its policy, then the components/controllers/jobs
   that reference it ranked by reference count (`grep -c`), capped at ~8 app
   files, plus the main feature tests for those files (~4). Always include
   the routes files as shared context in every orbit - they kill false
   positives about authorisation. Files with no model affinity form a final
   misc chunk. Record what was cut from each orbit.
2. **Spawn reviewer agents per chunk** (subagent nesting is supported; the
   orchestrator at depth 1 spawns reviewers at depth 2). Same briefing rules.
3. **Consolidate and record findings as ait issues in the target repo** - one
   epic per review run, one task per actionable finding, each description
   carrying file:line and the before/after sketch. The backlog is the
   deliverable; return only a summary to the main conversation.

## Rinse and repeat

On a grotty codebase, don't aim for one exhaustive pass. Cap the findings
(worst offenders first - the section checker's `--cap` does this natively),
fix, re-run, repeat until the developer says it's up to snuff.
