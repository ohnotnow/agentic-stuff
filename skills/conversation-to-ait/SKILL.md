---
name: conversation-to-ait
description: >
  Synthesise the current session into a brief, get user approval, then hand off
  to the plan-to-ait agent. Use towards the end of a chat where a feature has
  been discussed but no formal plan-mode plan was made.
allowed-tools: "Read,Write,Bash,Agent"
version: "0.1.0"
author: "ohnotnow"
license: "MIT"
---

# Conversation-to-ait

We've just had a conversation about a feature — maybe took some `ant` notes, maybe sketched an `ait` epic — but never made a formal plan-mode plan. This skill captures the load-bearing parts of that conversation as a brief and hands it to the `plan-to-ait` agent to turn into consultant-ready ait issues.

## Core idea

The value of a plan-mode plan was never the back-and-forth — it was the **distillation**. What survived, what got rejected, what the phases are. Replaying the whole conversation to a sub-agent makes it do archaeology I've already done in my head.

So: I synthesise the brief myself, the user reviews it (this is the gate that replaces ExitPlanMode approval), then we hand off.

## Workflow

### Step 1: Draft the brief

Write a single markdown document using the template below. Synthesise from what's actually in the session — don't pad. If a section is genuinely empty (e.g. nothing was rejected), drop it rather than filling it with "N/A".

```markdown
# [Feature Name]

## Goal
[1-2 sentences. What are we building and for whom?]

## What we decided
- [Concrete decision]
- [Concrete decision]

## What we rejected (and why)
- [Path not taken] — [why it was rejected]

## Existing context to wire in
- **ant entries**: [slug] — [one-line summary]
- **ait epics/issues**: [id] — [one-line summary]
- **Docs to read**: foundation, README, [anything else load-bearing]

## Phase breakdown (rough)
1. **[Phase]** — [what it covers]
2. **[Phase]** — [what it covers]

## Sharp edges
- [Tricky bit noticed in the conversation that isn't obvious from the code]
- [Constraint a fresh agent wouldn't spot]

## Testing mode hint
[Strict TDD / Standard / No tests — or "let plan-to-ait decide from project signals"]
```

### Step 2: Present for review

Show the brief to the user in a fenced code block. Ask:

> "Does this capture it? Anything missed, mis-weighted, or that I should drop?"

Iterate until they're happy. **Do not skip this step** — it's the gate, and the user is the one who knows which exploratory branches mattered and which were dead ends.

### Step 2.5 (optional but recommended): Reconcile against the transcript

Benchmarks (and the user's own testing) suggest written plans drop roughly 10–15% of requirements that *were* discussed — passing decisions, "we'll come back to that"s, the reasoning behind a chosen path. Neither I nor the user reliably spots these in a single read-through.

Offer this:

> "Before I save and hand off, want me to run `plan-reconciler` over the draft against the current session? It'll flag anything from the chat that didn't make it into the brief."

If the user says yes:

1. Save the current draft to a temp path (e.g. `~/.claude/plans/.draft-<slug>-<date>.md`) so the reconciler has a file to point at.
2. Invoke the `plan-reconciler` agent. Give it the draft path and tell it to use the current session file at `~/.claude/projects/<encoded-cwd>/<session-id>.jsonl` (encoded-cwd is the absolute working directory with `/` replaced by `-`).
3. Present the reconciler's report to the user.
4. Fold in whatever the user wants kept, drop the rest, then re-show the brief for final approval before moving on.

Skip this step for small/obvious briefs where the reconciler would just say "captured well" — it has a token cost. Lean on it for anything multi-phase or where the conversation wandered.

### Step 3: Save and hand off

Once approved:

1. Make sure `~/.claude/plans/` exists (create if not).
2. Save the brief as `~/.claude/plans/conversation-<short-kebab-slug>-<YYYY-MM-DD>.md`.
3. Invoke the `plan-to-ait` agent, pointing it at the saved file. Mention in the prompt that this brief came from a conversation (not a formal plan-mode plan) so the agent knows it might want to ask clarifying questions through the parent if a section feels thin.

## Guidelines for a good brief

- **Shorter than the conversation, longer than a tweet.** If it fits in your head, it's about right.
- **Leave out tangents.** If we noticed a small bug and fixed it on the way to the main feature, that fix doesn't belong in the brief — it's already done.
- **Keep "what we rejected" honest.** A fresh agent reading the brief shouldn't reach for a path we already ruled out. One line each is enough.
- **Don't paraphrase ant/ait entries** — reference them by slug/id so `plan-to-ait` can read the canonical source.
- **Sharp edges earn their place.** Only include things that would surprise a competent agent reading the code cold.

## When to skip this skill

- A plan-mode plan already exists in `~/.claude/plans/` — just invoke `plan-to-ait` directly.
- The scope is one issue, not a multi-phase feature — just create the ait issue inline.
- The conversation hasn't actually settled on a direction yet — finish the discussion first.

## Refining over time

This skill is a starting point. After a few runs, expect to tweak:
- The section list (maybe "Out of scope" deserves its own header)
- How much detail goes into phases vs. left for `plan-to-ait` to expand
- How aggressively to summarise ant/ait references

Edit this file when patterns emerge — the whole point is a consistent, evolvable shape.
