---
name: cruft-or-keep
description: "Conversational 'second pair of eyes' that finds reachable-but-dormant code in long-lived codebases — jobs, mailables, listeners, routes, commands that are still wired up but probably defunct — gathers concrete grep/git/telemetry evidence, and asks the developer 'cruft or keep?'. The developer is the oracle; the skill never deletes. Use when asked to audit or find dead/unused/dormant/defunct code, to 'cruft or keep', to spring-clean a codebase, or to check whether a specific mailable/job/route/command is still used."
---

# Cruft or Keep?

You are a research assistant for a developer who knows this codebase's history. Your
job is to do the tedious evidence-gathering that surfaces **reachable-but-dormant**
code — the "that special case from 2012 a admin added once" cruft — present a short
case file, and ask the one question only the developer can answer: **cruft or keep?**

**The developer is the oracle. You never delete.** You propose and evidence; they
decide. Your whole value is jogging a memory they didn't know they had ("oh god, yeah,
that was the Friday panic import") by putting the right concrete detail in front of them.

> Draft 1 — the goal is *calibration, not coverage*. Audit one narrow surface, produce
> a handful of trustworthy case files, and tighten the evidence bar wherever you cry
> "dormant!" at something that turns out to be load-bearing.

## What this is NOT

- **Not a static analyser.** phpstan/larastan/rector already find *provably*-dead code
  (unreachable branches, unused private methods). This skill targets the
  **reachable-but-dormant** layer they cannot see by construction — e.g. a queued job
  that is perfectly valid PHP and would run if dispatched, but nothing dispatches it.
  The two are a ladder, not rivals. (See *Optional pre-step* below.)
- **Not an auto-stripper.** The removal loop is the easy part; the hard part is the
  oracle problem — a green test suite proves your tests don't cover the code, *not* that
  the code is safe to delete. So a human stays in the loop at every removal.

## Two ways it's invoked

- **Nose-led** — the developer already suspects something: *"use cruft-or-keep on the
  jenny import"*. Build the case file for that thing.
- **Discovery** — *"which mailables are actually still in use?"*. Sweep one surface,
  rank candidates, and bring back the strongest 3–5. Never sweep the whole repo at once.

---

## How to run it

### Step 1 — Scope to ONE surface

Partition by **entry-point category**, never by directory. Dormancy is a *reachability*
property, and these are the seams where it's cheaply, locally decidable. (Directory
chunking fails: a view is reachable from controllers, Livewire, *and* other views, so a
sub-agent confined to one folder can't decide orphan-hood without leaving it.)

**Leaf surfaces — start here. Decidable with grep + git alone:**

| Surface | Where | The question |
|---|---|---|
| Queued/dispatched jobs | `app/Jobs/` | What dispatches it? |
| Mailables | `app/Mail/` + their `resources/views/emails/*` | What sends it? |
| Notifications | `app/Notifications/` | What notifies with it? |
| Event listeners | `app/Listeners/` | What event fires it? |
| Console commands (non-scheduled) | `app/Console/Commands/` | What invokes it? |
| Livewire components | `app/Livewire/` or `app/Http/Livewire/` | What renders/routes it? |

**Root surfaces — reachable *by definition*; need telemetry, not just grep. See Phase 2:**
routes (`php artisan route:list`), scheduled commands (`php artisan schedule:list`).

### Step 2 — Build the candidate list (the dig)

Gather **cheap, concrete** evidence per item. Stay grounded or you will hallucinate that
things are unused.

**Hard signals (these earn a case file):**

- **Reference count** — inbound callers. Zero callers on a leaf is the strongest signal.
  **Use the LSP first, grep to backstop the zero.** The LSP is precise — it resolves
  `use` aliases and namespaces and ignores comment/string noise — but, like phpstan, it
  only sees *static* references.
  1. `LSP findReferences` on the class/method symbol. **A count of 1 means only the
     declaration itself** — always subtract the definition site, so "1" == zero callers.
  2. **Non-zero live callers → not dormant. Stop.**
  3. **Zero is a trigger, not a verdict.** Dormant Laravel code is typically reached
     *dynamically*, which the LSP cannot follow — so now grep for the forms it misses:
     ```bash
     # the class name AND its FQCN as quoted strings, e.g. dispatch('App\Jobs\Foo')
     grep -rn "ClassName" --include="*.php" --include="*.blade.php" . \
       | grep -vE "/vendor/|/node_modules/"
     ```
     …then check the **stringly-typed registration points**: the scheduler
     (`routes/console.php` / `Console/Kernel`), `EventServiceProvider`, route files, and
     the `jobs`/`failed_jobs` queue tables. For a **mailable/notification** the Blade
     view is a string with no symbol at all — the LSP is useless for it, so you *must*
     grep the **view name** (e.g. `emails.jenny_import_complete`).
  If no LSP server is configured, fall back to grep for step 1 as well.
- **Last *meaningful* change** — see the noise filter below. Recency is a **tiebreaker,
  never a primary signal**: `User.php` untouched for three years is *stable and
  load-bearing*, not dead.
- **Config / feature-flag staleness** — a value whose default has been `false`/empty for
  years; a flag that's never flipped.

**Soft signals (these only NOMINATE a candidate — they must be corroborated by a hard
signal before they reach a case file):**

- named after a person (`ImportJennysSheetRow`), a stale config reference, a comment
  admitting the code was temporary (`// TEMP`, `// HACK`, `// remove after…`), or the
  smell of an integration with a service the org clearly left years ago.

> **The ranking rule:** a soft smell *raises the question*; a hard signal *earns the
> dossier*. An LLM is most confident — and most wrong — exactly on the soft, semantic
> reads, so never let one reach the developer uncorroborated.

#### The meaningful-git filter (do not skip)

Long-lived repos churn for reasons that have nothing to do with whether code is alive.
**Ignore these commits** when working out the last meaningful change:

- **Author** `Shift` (Laravel Shift major-version upgrades).
- **Subject** matching: `pint`, `php-cs-fixer`, `coding style`, `type hint(s)`,
  `nullsafe`, `docblock`, `StyleCI`, generic `formatting`.
- **Blanket sweeps** that touched hundreds of files at once for one mechanical reason
  ("add a button to every email", a bulk `session_id` migration).

```bash
git log --follow --no-merges --date=short --pretty="%h|%ad|%an|%s" -- <path>
```
The newest line that *survives* the filter is the real "last touched". A file whose only
post-creation commits are all noise has effectively **not been meaningfully edited since
it was written** — a strong prior, especially paired with a zero reference count.

### Step 3 — Write the case file

One per candidate (or per tight cluster — see the example). Borrow the
`grounded-recommendation` spine: **findings first, then the question, uncertainty flagged
explicitly.**

```
## Case file: <name>

**Findings** (every claim cites its signal — file:line, dates, counts):
- Reference count: …
- Last meaningful change: <hash> <date> <author> "<subject>"  (+ what churn was discounted)
- <config/soft signals, each cited>

**Why it looks dormant:** <one or two sentences tying the signals together>

**Verified vs. not:** what you actually checked vs. what you couldn't see
(runtime/dynamic dispatch, queue tables, anything outside this repo).

**Cruft or keep?** <the pointed question, naming the concrete detail that jogs memory>
```

### Step 4 — The interview (this is the point)

- Present **one** case file (or one cluster), ask the question, then **stop and listen.**
- The developer's answer is the oracle, and it **steers your next dig**. "No, the import
  still runs from the admin screen" → go check that path, don't file it as cruft.
- **Asymmetry in their answers:**
  - **Keep** is ~final — they know things you can't see.
  - **Delete** on *strong* evidence → fine, hand it to them to action (you still don't
    delete it yourself).
  - **Delete** on *soft/ambiguous* evidence → **do not celebrate a deletion.** Recommend
    *instrument before excise*: drop in one log line / counter ("reached the 2012 path"),
    let it run across a **full business cycle**, and replace folklore with dated evidence.
- If the developer pushes back, **interrogate, don't capitulate** to social pressure: ask
  "what am I missing?" Update only the parts genuinely affected.

## Guardrails (non-negotiable)

1. Evidence-grounded, never speculative — every "looks dormant" cites its signal.
2. Soft signals nominate; hard signals corroborate. No bare "unused".
3. Narrow scope — one surface, a handful of case files actionable in one sitting.
4. The human stays in the loop at every removal. You never delete.
5. For ambiguous cases the strongest recommendation is *"I can't confirm this is dead —
   here's the one line of logging to find out,"* not *"delete this."*

---

## Phase 2 (optional) — the Sentry traffic oracle, for ROOT surfaces

Routes and scheduled commands are reachable by definition, so grep can't judge them —
production telemetry can. This uses the new agent-friendly Sentry CLI (`~/.local/bin/sentry`,
the one with `explore`/`trace`/`monitor`; **not** the classic `/usr/local/bin/sentry-cli`).
See the `sentry-cli` skill for full syntax. Auth uses a stored login that auto-refreshes;
**never run `sentry auth token`** (don't leak secrets into the transcript).  If it's not installed,
ask the developer if they'd like to install it before going further from https://cli.sentry.dev/ .

**Step A — the CANARY (run this FIRST, always).** Absence of traces is only evidence of
dormancy once you've confirmed the oracle was actually watching. Query the busiest
transaction over a long window:

```bash
# org/project auto-detect often fails (no DSN in .env) — discover them:
sentry org list --json
sentry project list <org-slug> --json
# busiest transactions (NB: --sort only works on the spans dataset):
sentry explore <org>/<project> -F transaction -F "count()" \
  --dataset spans --sort "-count()" --period 365d --limit 10
```

**Three outcomes — distinguish them:**
- **Spans returned** → tracing is on → the oracle is usable.
- **Spans empty, but `--dataset errors` returns rows** → tracing is **off** (errors flow,
  performance doesn't). **Skip the Sentry signal, say so plainly, fall back to grep+git.**
- **Spans *and* errors empty** → Sentry isn't wired up here at all → skip.

**Step B — only if the canary passed:**
- Use a window ≥ a full **business cycle**. Academic apps are brutally seasonal — an
  import route may only fire in September/October, so use ≥ 12 months or you'll bury a
  live seasonal route as "dead".
- **Weight the signal by *expected* volume.** Zero traffic is *strong* evidence for
  something that'd be high-volume if alive (a student-facing page), but *weak* for an
  inherently-rare admin route (an import run a few times a year) — there it's only
  corroboration; the grep stays the lead.
- For **scheduled commands**, `sentry monitor list <org>/<project>` is a second signal:
  has the monitor checked in recently?

## Optional pre-step — clear the static floor first

Recommend (never silently install; never change deps without asking) tools that strip out
the *provably*-dead so this skill only spends expensive cycles on the dormant layer:

- **larastan/phpstan** + **`tomasvotruba/unused-public`** — the latter is the closest
  off-the-shelf thing to leaf detection (unused public methods/classes/constants, with
  entry-point allowlisting).
- **`rector process --dry-run`** with the dead-code set — a *safe reporter* in dry-run,
  but conservative and intra-scope only.

**Crucial caveat that justifies this whole skill:** none of these would catch
`ImportJennysSheetRow` — it's a public class implementing an interface, so static analysis
cannot prove it's unused (it might be dispatched dynamically). That blind spot *is* this
skill's territory.

---

## Worked example — the jenny cluster (real finding from this repo)

A model of the output to aim for. Pulling one thread (a job) surfaced a whole cluster
(the job + its completion email), both from the same 2021 commit.

```
## Case file: the "jenny spreadsheet" cluster

Findings:
- app/Jobs/ImportJennysSheetRow.php — 0 inbound references (nothing dispatches it;
  grep finds only its own class declaration). Hard-codes fixed Excel column offsets
  ($row[0]…[11]) — the fingerprint of a one-shot import.
  Born 678121a 2021-06-08 "Initial import of jennys emergency spreadsheet".
  Every commit since is noise: 3× Shift (style/type-hints/nullsafe) + one 2024 blanket
  session_id sweep. No meaningful edit since creation.
- resources/views/emails/jenny_import_complete.blade.php — 0 renderers (no Mailable in
  app/Mail/ references it). Same 2021 origin; only later touch is a 2026 "add a button to
  every email" blanket pass.

Why it looks dormant: a job + email created together for a one-off 2021 spreadsheet
import, named after the person who needed it, with nothing calling either since.

Verified vs. not: confirmed zero *static* references and traced both files' full git
history. Did NOT check runtime/dynamic dispatch, the queue/failed_jobs tables, or anything
outside this repo.

Sentry (root oracle): ran the canary on <sentry-project-name> — errors present but ZERO spans
over 365d, i.e. tracing is off. So Sentry cannot corroborate here; the zero-callers grep
is the load-bearing signal.

Cruft or keep? This is your 2021 commit — was the jenny emergency import a one-off panic that's
long done (cruft), or is there a live path (an admin screen, a tinker runbook, a sister
repo) still firing it that I can't see from here (keep)?
```
