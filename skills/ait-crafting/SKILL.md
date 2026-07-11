---
name: ait-crafting
description: >
  Turn a settled feature discussion or plan document into consultant-ready ait
  issues — an initiative/epic vision document plus implementation specs a fresh
  agent could pick up cold, tomorrow. Use towards the end of a feature
  conversation ("let's get this into ait"), or when converting a plan file.
  Also the knowledge base for the plan-to-ait agent. For driving the ait CLI
  itself, see the ait skill.
allowed-tools: "Read,Glob,Grep,Bash(ait:*),Agent"
version: "1.0.0"
author: "ohnotnow"
license: "MIT"
---

# Crafting ait issues

The goal: a fresh agent with no prior context could read the epic + issue + README and start work immediately. **Consultant-ready.**

## The Layered Context Model

```
Initiative or Epic (vision document)
├── Background: What exists, context
├── The Problem: Why this is needed
├── The Vision: What we're building
├── Who Benefits: Users and how
├── Success Criteria: Concrete outcomes (and what success is NOT)
├── Key Principles: Guiding constraints
├── Technical Approach: High-level architecture
├── Key Documents: Links to README, TECHNICAL_OVERVIEW, etc.
└── Phases: Overview of work breakdown
        ↓
Issues (implementation specs)
├── File paths to create/modify
├── Code snippets (schemas, signatures, return formats)
├── Pattern references ("Follow X.php for structure")
├── Acceptance criteria
└── Prerequisites by name ("Uses Team model from 3tz.2")
```

**The initiative/epic has the "why". Issues have the "what".**

For larger features with multiple epics, use an `initiative` as the top-level vision document and group epics beneath it. For smaller features, an epic is sufficient.

Issues can be terse on context because the initiative/epic covers it. But they must be complete on implementation details.

## Workflow

### 1. Calibrate to the project

- Read README.md, CLAUDE.md, TECHNICAL_OVERVIEW.md (if they exist), and any docs mentioned in the discussion or plan.
- Pick a testing mode (see below). This shapes how you design issues and what acceptance criteria mean.

### 2. Distil and gate (when the source is a conversation)

When working from a live discussion rather than an approved plan document, distil the load-bearing parts before creating anything:

- **Goal** — what we're building and for whom, 1–2 sentences
- **What we decided** — concrete decisions that survived
- **What we rejected (and why)** — so a fresh agent doesn't reach for a ruled-out path
- **Phases** — rough breakdown
- **Sharp edges** — things noticed in conversation that aren't obvious from the code

Present it in chat and ask:

> "Does this capture it? Anything missed, mis-weighted, or that I should drop?"

Iterate until the user is happy. **Do not skip this** — the user is the one who knows which exploratory branches mattered and which were dead ends.

Record the rejected paths and their reasons as an `ant` note and reference it from the epic — that's what `ant` is for. Don't paraphrase them into issue descriptions.

**Skip the gate** when converting an already-approved plan-mode plan: approval happened at plan acceptance, and the plan document is the distillation.

For a long or wandering conversation, offer one extra pass before creating issues: save the distillation to a temp file and run the `plan-reconciler` agent over it against the current session. Written summaries reliably drop 10–15% of what was actually discussed; the reconciler catches coverage gaps (did what we said make it into what we wrote?), while the amnesia check in step 7 catches conveyance gaps (can a stranger act on what we wrote?). Different failure modes — don't treat one as covering the other.

### 3. Check for overlapping issues

- Run `ait list --all` and `ait search` for potentially related issues.
- If the user named a parent initiative/epic, read it with `ait show <id>`; if its description is thin, enhance it before creating children.
- If overlap is found, ask before proceeding.

### 4. Create or enhance the initiative/epic

Include ALL of these sections in the description:

```markdown
# [Feature Name]

## Background
[What exists already. Link to relevant docs. 1-2 paragraphs.]

## The Problem
[Why this is needed. What pain point it solves. Bullet points work well.]

## The Vision
[What we are building. Be specific about the solution.]

## Who Benefits
**[User type 1]**: [How they benefit]
**[User type 2]**: [How they benefit]

## What Success Looks Like
- [Concrete outcome 1]
- [Concrete outcome 2]
- [Concrete outcome 3]

**Success is NOT**: [What we are explicitly not optimising for]

## Key Principles
1. **[Principle]**: [Explanation]
2. **[Principle]**: [Explanation]

## Technical Approach
- [High-level architectural decision 1]
- [High-level architectural decision 2]

## Key Documents
- README.md - [What it contains relevant to this]
- [Other doc] - [What it contains]

## Phases
1. **[Phase name]** (P1): [Brief description]
2. **[Phase name]** (P2): [Brief description]
```

### 5. Create consultant-ready issues

Each issue must pass the **Amnesia Test** (defined below).

**For implementation tasks, include:**

```markdown
[Brief description of what to build]

## Files to create/modify
- `path/to/file.php` - [what goes here]
- `path/to/other.php` - [what changes]

## Implementation details
[Code snippets, schemas, method signatures, return formats as appropriate]

## Pattern reference
Follow `path/to/existing/similar.php` for [structure/style/approach].

## Acceptance criteria
- [ ] [Specific testable outcome]
- [ ] [Specific testable outcome]

## Prerequisites
Uses [X] from issue [ID] which added [brief description].
```

**For simple tasks** (config changes, small additions):

```markdown
[What to do in 1-2 sentences]

File: `path/to/file`

[Code snippet if helpful]
```

### 6. Wire dependencies

- Phase dependencies: Phase 2 blocked by the Phase 1 tracker.
- Technical dependencies: feature blocked by its foundation.
- **In descriptions**: name what prerequisite issues provide — a cold reader follows the thread by ID.

Create a tracker issue for each phase (e.g., "Phase 2: Service layer"). Trackers:

- Have no implementation details (they are just milestones)
- Block all issues in the next phase
- Help visualise progress

### 7. Amnesia check (multi-phase or gnarly work)

For anything beyond a small epic, spawn the `ait-amnesia-check` agent with a handful of issue IDs — the foundation issues plus one or two deep in the dependency chain, not the lot. It has no conversation context (deliberately) and will *demonstrate* what it would build from each spec: restated goal, files, first failing test, with every guess and dead end marked.

**Never ask it for a verdict** — a "yep, looks great!" costs nothing to emit and means nothing. Instead, diff its demonstration against what you (holding the design context) know was intended. Its wrong guesses point at the exact sentence missing from an issue; its `STUCK` findings usually mean a prerequisite went unnamed. Patch the issues, don't argue with the checker.

Skip this for a three-issue epic — it's a meaty run and small plans don't earn it.

## Testing modes

**Strict TDD** — Laravel projects, or any project whose CLAUDE.md mentions TDD / red-green / one-at-a-time.

- Acceptance criteria are **failing tests, written first**. Each criterion = one behaviour.
- Add this block verbatim to every implementation issue:

  > **TDD — tests come first.** For each acceptance criterion:
  > 1. Write the failing test.
  > 2. Run it. Watch it fail for the right reason.
  > 3. Write the minimum code to make it pass.
  > 4. Refactor.
  > 5. *Then* move to the next criterion.
  >
  > Do **not** scaffold the implementation first and retrofit tests — that is not TDD. Do **not** write multiple tests upfront. One test, one behaviour, one step at a time.

- If an issue has many criteria, split it so the red-green rhythm stays natural.

**Standard testing** — Python, Go, or other serious projects without an explicit TDD policy.

- Acceptance criteria double as tests, written alongside implementation.
- No one-at-a-time requirement; the implementing agent can batch sensibly.

**No tests** — Throwaway JS/TS toys, exploration scripts, personal fun projects.

- Signals: minimal `package.json`, no tests directory, no CI config, no CLAUDE.md TDD language.
- Acceptance criteria are plain observable outcomes ("Button changes colour on click"), not tests.
- Drop TDD language from issues entirely. The user will verify manually.

**If signals are ambiguous, ask once** before creating issues — don't silently guess.

In all modes: **never create standalone "write tests" or "update tests" issues**. If an issue changes behaviour, its acceptance criteria should reflect the new behaviour. No follow-up "fix up the tests afterwards" issue — that invites retrofitting.

## The Amnesia Test

> "If I had amnesia tomorrow and was handed this issue plus the epic plus README, could I start work?"

The test was never "this issue alone on a desert island". Tomorrow's agent legitimately has: the epic, the README, the repo, and any issue named as a prerequisite (whose spec stands in for code that doesn't exist yet). What it does *not* have is the conversation in your head — so nothing load-bearing may live only there.

**FAILS the test:**

```
Create FindMentoringPairs tool

File: app/Services/SkillsCoach/TeamTools/FindMentoringPairs.php

Follow existing pattern.
```

*Problem: What pattern? What does this tool do? What does it return?*

**PASSES the test:**

```
Create tool to suggest High+Low skill pairings for mentoring within a team.

## File to create
`app/Services/SkillsCoach/TeamTools/FindMentoringPairs.php`

## Parameters
- `skill_name` (required): The skill to find mentoring pairs for

## Return format
{
    "skill": "Docker",
    "pairs": [
        {"mentor": {"name": "Alice", "level": "High"}, "learner": {"name": "Bob", "level": "Low"}}
    ]
}

## Implementation
1. Get team from CoachContext::getTeam()
2. Find High-level members (mentors)
3. Find Low/Medium members (learners)
4. Match them, respecting coach_contactable flag

## Pattern reference
Follow `app/Services/SkillsCoach/Tools/FindExperts.php` for Prism tool structure.

## Acceptance criteria
- [ ] Returns valid mentor/learner pairs
- [ ] Respects coach_contactable opt-out
- [ ] Handles "no pairs found" gracefully
```

## Issue guidelines

### Titles

- Imperative form: "Add user authentication" not "Adding..."
- Specific: "Add login form validation" not "Handle validation"
- Under 60 characters

### Priorities

- P1: Foundation work (must be done first)
- P2: Core features (main implementation)
- P3: Polish and non-critical enhancements

## When to skip this skill

- The scope is one issue, not a multi-phase feature — just create the ait issue inline (the issue templates above still apply).
- The conversation hasn't actually settled on a direction yet — finish the discussion first.

## What you do NOT do

- Modify any code files
- Create issues for things that weren't discussed or planned
- Create overly granular issues (one per line of code)
- Create issues without enough detail to execute
- Skip the epic vision document
- Create separate "testing" issues — tests belong inside each implementation issue
