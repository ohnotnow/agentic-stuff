---
name: house-style
description: Teach a personal editor agent the user's own editing taste by reading the diff between an AI-drafted document and the user's hand-edit of it, encoding the lessons as procedures in the agent, and verifying with controlled re-runs. Use whenever the user has edited an AI-written document (README, docs, blog post) and wants their editor agent to learn from it, wants to build a personal editor agent from scratch, or says things like "teach my editor", "learn my house style", "train the humaniser on my edits", "make the editor agent edit more like me", or asks to compare what their editor agent would do against their own edit of the same document.
---

# house-style — teach your editor agent your taste

You are coaching a personal editor agent (a "humaniser" — the agent that
edits AI-drafted text to read like the user wrote it). The training data is
the user's own hand-edit of an AI draft. The diff between what the user did
and what the agent would have done is the lesson. This skill exists because
of three hard-won findings — they shape every step below:

1. **Procedures get followed; prohibitions get rationalised away.** An agent
   told "cut the flourishes — all of them" kept them across three runs and
   praised them as "the good human lines". The same rule rebuilt as a
   checklist pass ("list every constructed metaphor; delete each item")
   worked first time. When you encode a lesson, encode it as a procedure.
2. **The agent cannot judge "sounds human" — that judgement is the failure
   mode.** LLM-written whimsy is exactly what an LLM's taste says "human"
   looks like. Telling the agent the text is AI-generated (in the brief, or
   in its own system prompt) changes nothing. Rules must classify by
   category, not judge by charm.
3. **Agents misreport their own edits.** One run claimed it kept a phrase it
   had deleted. Verify every claim about the file with `grep`/`git diff`,
   never from the agent's summary.

## Pre-flight — establish the two inputs

Nothing works without these. Check them before doing anything else.

**1. The training material: an original + the user's edit of it.**

- In a git repo where the target document has uncommitted modifications:
  the HEAD version is the original, the working tree is the user's edit.
  Confirm with the user that the working-tree changes are theirs, and ask
  whether the pass is *complete*. A half-finished edit teaches a poisonous
  lesson — every section the user hasn't reached reads as "this prose is
  approved". If it isn't complete, either wait for them to finish or scope
  the learning to the hunks they confirm are done.
- If the target document is **clean** (or the user hasn't said which document):
  the user has probably not made their edit yet. Stop here and explain the
  process: *their* hand-edit is the entire input — ask them to edit the
  document in their own style first (however long that takes), then rerun
  this skill. Do not offer to edit it for them; that would train the agent
  on your taste, which is precisely the disease.
- No git? Accept any before/after pair of files the user points at.

Then ask the mess question, once, early: the user's edit may contain
typos, broken list numbering, doubled spaces. Is copy-correctness still
the agent's job, or is the mess part of the voice? A good default: leave
rhythm and word choice alone; report — never silently fix — anything that
looks genuinely broken. Encode whichever they choose.

**2. The editor agent.**

- Ask which agent file is theirs if not obvious (a common default:
  `~/.claude/agents/humaniser.md`). If their agents are synced from a
  source repo, edit the source copy and remind them to sync afterwards.
- If they have no editor agent, create one from
  `references/seed-agent.md` (ask what to name it), then continue — the
  first coaching session both creates and tunes it.
- Convention: a personal style file at `~/.claude/house-style-user.md`
  (`references/example-user.md` shows the shape) carries the user's
  standing taste — locale, punctuation habits, register. Fold its rules
  into any agent you create, and treat it as ground truth when reading
  diffs. It lives outside this skill's directory on purpose: the skill may
  be synced to other people, and the taste must not travel with it. Agents
  never read it at run time — bake the rules in, so each agent stays
  self-contained and controlled runs stay attributable to one file.

## Read the diff as taste data

Get the diff (`git diff <file>`, or diff the pair). You are not reviewing
their edit — they are the oracle; the diff is ground truth about their
taste. Look for:

- **Cut vs reword ratio.** Human editors delete; agents reword. Whole
  sections gone is a louder signal than any wording change.
- **Information architecture.** Did detail move out to sibling docs
  (README → technical overview / runbook)? Did they add pointers?
- **Flourishes.** Constructed metaphors, whimsy, punchy taglines — kept,
  cut, or replaced with plain idiom?
- **Register.** Confident → humble? Polished → relaxed? Jargon → layman's
  terms (e.g. "the mic arms" → "the mic turns on")?
- **Recurring pet peeves.** Patterns worth naming with a before/after
  (e.g. reassurance-by-negation: "only when X, never otherwise" — the food
  processor manual promising the blades never start by themselves).

Then read the agent's current prompt and ask of each observation: would the
agent, as instructed today, have done this? The gaps are the lesson list.

While you read the prompt, treat unsourced taste-claims already in it as
suspect: "the owner keeps plenty of them" may have been minted by whichever
model drafted the rule, not learned from any diff. Field example: an agent
confidently protected single em dashes as the owner's taste; the owner's
actual habit was a shell alias that strips every one. A rule that cites no
diff gets checked against one before it survives the session.

## Discuss, then encode — one lesson at a time

Talk it through with the user; don't table a report. Raise the biggest gap
first, with your read on it, and let them respond. Two rules:

- **Ask about torn calls.** If a cut looks like it could be a one-off
  ("you cut the Components section — rule, or specific to this doc?"),
  ask. Never promote a single casual decision into a cast-iron rule.
- **Encode as procedures.** Every accepted lesson becomes either a
  checklist pass the agent must *do* (the strongest form: "list every X;
  delete each item; after rewording, re-check your own new sentences"),
  or a named pattern with words-to-watch and a before/after example.
  If you catch yourself writing a value statement ("prefer plain
  language", "don't overdo it"), stop and convert it — see finding 1.
- **State precedence when passes can collide.** An early "keep" rule
  silently exempts material from every later delete pass. Field example:
  a "protect explanations of foot-guns" test fired first and shielded
  exactly the reassurance a later sweep existed to remove. Make tests
  directional, not subject-based — "here is what will go wrong" is
  protected; "here is why you're safe" is not, however alarming the
  subject — and say outright that surviving one pass exempts nothing
  from the next.
- **A report-only step needs a mandatory artefact.** A pass whose entire
  output is conditional silently doesn't happen — in field testing it
  evaporated until its working (the list, the count) was made
  unconditional. If the honest conclusion is "nothing to report", the
  artefact is the one line that says so; no note is indistinguishable
  from the pass never having run.
- **Watch the pass budget.** Cut quality declined monotonically as passes
  were bolted onto one agent (218 → 202 → 187 lines cut across otherwise
  equal runs). When the new job is diagnosis rather than editing —
  document structure, say — prefer a second report-only agent over a
  fifth pass on the editor.

Apply the edits to the agent file.

## Verify with a controlled run

The prompt edit is a hypothesis until a fresh agent run confirms it.

1. **The user makes the copy and does the revert — not you.** Ask them to
   run, themselves:

   ```bash
   cp README.md ../SAFE_README.md    # their edit, kept outside the repo
   git checkout -- README.md         # working tree back to the original
   ```

   Doing this silently on their behalf was field-tested and cost five
   turns of "who edited what?" — a person cannot get lost about file moves
   they made with their own hands. The copy living *outside* the repo also
   means later runs can't read it. If they want to keep an agent run for
   comparison, same trick: `cp README.md ../agent-run1.md`.
2. **Record the exact brief** in a file outside the repo too, and reuse it
   verbatim: minimal and neutral — file path, tone, one line of context.
   Do not coach it towards the lessons; a hint in the brief invalidates
   the test.
3. **Run the editor agent on the real file** with that brief. Prefer an
   editor agent with no Bash so it can't reach git history, and make sure
   no previous run's output is lying about in the repo — an agent will
   happily read one "for context" and contaminate the experiment.
4. **Verify with grep/diff, not the report** (finding 3). `git diff` now
   honestly shows the agent's changes against the original — the user did
   the revert, so they know exactly whose work they're reading. Did the
   known problem phrases actually go? Did it mint new ones? And verify the
   verification — a grep that misses because a phrase wraps across a line
   break will have you accusing the agent of a false report it never made.
5. **Compare against the user's edit** —
   `git diff --no-index ../SAFE_README.md README.md` answers "what did the
   agent do differently from me" directly. Report divergences
   conversationally, biggest first, and ask which are rules versus one-off
   taste. Divergences inside sections the user never reached are unknowns,
   not disagreements.
6. **Iterate single-variable.** One prompt change per re-run; the user
   reverts again (`git checkout -- README.md`), same brief word for word,
   so behaviour changes are attributable.
7. **Afterwards, the user restores whichever version they want** —
   usually `cp ../SAFE_README.md README.md`. Their copy, their command,
   their call.

## Wrap-up

- Remind the user to sync the agent if it's distributed from a repo.
- Remind the user which `../` copies exist (their edit, any kept agent
  runs, the brief) so they can tidy or keep them deliberately.
- If a lesson from this session is about the user rather than about one
  document type — a punctuation habit, a locale, a register preference —
  offer to add it to `~/.claude/house-style-user.md` as well as the agent
  under coaching: that is how the next agent inherits it.
- Offer to note genuinely unresolved divergences somewhere durable
  (their tracker or notes tool) rather than leaving them as loose ends.
- This is a coaching loop, not a one-shot: each future hand-edit of an
  AI draft is fresh training data. Suggest rerunning house-style when
  the user next finds themselves reworking the agent's output by hand.
