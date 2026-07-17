---
name: quality-gate
description: One-stop review after feature work, or for a whole codebase. Runs deterministic checks (section ordering, arch conventions) free of charge, then fresh-eyes reviewer agents. Covers team conventions, test quality, complexity, security, and Livewire/Flux patterns - plus runtime checks (a11y, cold UX probe) when UI changed. Also has a quick mid-session sanity-check mode ("this seem ok?").
triggers:
  - /quality-gate
  - /review
  - run the quality gate
  - code review
  - this seem ok
  - quick sanity check
---

# Quality Gate

One entry point for post-work review. The developer should never have to
remember which reviewer exists - picking them is this skill's job.

Two scopes:

- **Recent work** (default, the common case): commits since the merge-base
  with master/main, plus unstaged and untracked changes.
- **Whole codebase** (explicit opt-in, e.g. "review the whole app"): for
  legacy or inherited apps. Delegated - see below.

And two depths for recent work:

- **Quick check** ("this seem ok?", mid-feature): tier zero plus a
  background a11y pass - see its section below.
- **Full gate** ("I think I'm done"): tier zero, then the reviewer roster.

Code reviewers always receive **file lists, never diffs**. A diff tells a
reviewer where to look; only the whole file tells them what's actually
there. (The runtime checkers are the exception - see the roster note.)

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

## Quick check - mid-session "this seem ok?"

For a cheap sanity check mid-feature - asked for casually, or wanted for
your own peace of mind before building on top of the work:

1. Tier zero, as above - free, always.
2. UI changed and the app running locally? Spawn the `a11y-checker` agent
   in the background (quick mode) on the page(s) just touched, and keep
   working while it runs.

No Opus reviewers and no confirmation ceremony - the spend is small and
the point is not breaking stride. Triage findings with the same three
outcomes as the full gate; anything deferred still becomes an ait issue,
not a verbal "I'll flag that".

## Reviewer roster

| Agent | What it checks | When to run |
|-------|---------------|-------------|
| `laravel-conventions-reviewer` | Readable model helpers, fat models, DB:: query building, enums, duplicate-purpose methods | Always for Laravel work |
| `test-quality-checker` | Weak assertions, tautological tests, unit-vs-feature, proliferation, missing edge cases | Always for Laravel work |
| `phpmetrics-check` | Complexity hotspots, maintainability | Always for Laravel work |
| `laravel-owasp-reporter` | Broken access control, mass assignment, IDOR, secrets | API or auth-touching work |
| `livewire-flux-reviewer` | Livewire/Flux modernisation | When Livewire/Flux code changed |
| `a11y-checker` | Runtime accessibility on the running page: axe scan, tab-order walk, virtual screen reader | UI changed and the app runs locally |
| `ux-journey` probe | Context-free agent attempts the real task the feature enables, cold; reports friction, wrong turns, dead ends | User-facing flow changed - opt-in, ask first |

> **Scoping note — don't route Blade views only to `livewire-flux-reviewer`.**
> The "raw column check → model helper" convention (`@if ($job->alerting_since)`
> → `@if ($job->isAlerting())`) applies to templates too, but the flux reviewer
> is framed for Livewire/Flux modernisation and won't wear that lens. Give
> `laravel-conventions-reviewer` the relevant Blade views — component views, the
> layout, and mail/markdown templates (easy to forget) — alongside the PHP, in
> both recent-work file lists and whole-codebase chunks. (cronmon, July 2026:
> the conventions reviewer got zero blades and the awol email template was in no
> reviewer's list at all — a view-level de-duplication went uncaught until the
> developer spotted it by eye.)

> **The runtime rows are different animals.** They exercise the running
> app, not the code, so neither takes the briefing block or a file list.
> `a11y-checker` gets the app's base URL and the pages to check; its
> findings come back for the same triage. The probe is launched through
> the `ux-journey` skill, which owns its rules - and its briefing must be
> the genuine task the feature enables ("create a silenced cronjob for
> team X"), never "go poke at the app": a probe without a real task
> manufactures findings to justify itself. It also needs a persona and
> login agreed with the developer and costs ~100k subagent tokens, so it
> sits behind the same confirm-before-spending gate as the Opus reviewers.
> If either isn't installed (they come from the a11y-agent and ux-agent
> repos), say so rather than silently skipping the coverage.

## Confirm before spending

Tier zero is free - run it without asking. A background `a11y-checker`
run is cheap - spawn it freely on a quick check. Opus reviewers and the
UX probe are not. Before launching any, tell the user what tier zero
found, which reviewers fit this scope, and ask. If the work was trivial (config change, copy tweak), don't
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

The defer rule covers your own observations too: anything you spot yourself
(during tier zero, or while reading) and promise as a follow-up must be an
ait issue before the final summary - a verbal "I'll flag that" is not a
record. (cronmon, July 2026: a deletion-cascade duplication spotted during
the section-ordering pass was promised out loud as a follow-up and never
logged.)

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

When a coherent set of fixes is in place and you feel like it's a good place to commit the work 
that has been done - give your summary as you would normally, but suggest committing the work
and offer a helpful git commit message following the Conventional Commits spec.

