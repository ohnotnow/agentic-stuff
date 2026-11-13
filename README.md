# LLM coding skills and agents

Skills and agents I use with AI coding tools. Mostly Laravel/Livewire, but some are general-purpose.

---

> **Heads up (12th November 2026):** The `i-impeccable` and `i-shape` skills are no longer shipped here; they're maintained upstream at [impeccable](https://github.com/pbakaus/impeccable). The `improve` skill (a modified copy of shadcn's) has gone too. If you already have them, nothing deletes them: `./migrate` just prints a `[Deprecated]` notice, and you can remove the folders yourself whenever you're done with them.

---

> **Heads up (7th November 2026):** The `ait` and `ant` skills and agents now ship inside their own binaries: run `ait install-skills` and `ant install-skills` instead of syncing them from here. `ait-crafting` is replaced by the tracker-agnostic `spec-crafting` skill below (the ait-specific parts moved into the `ait` skill), and there's a generic `amnesia-check` agent alongside the `ait-amnesia-check` that `ait` ships. `expand-issue` and `feature-workflow` have moved into `ait` too, renamed `ait-expand-issue` and `ait-feature-workflow`. `./sync` never deletes anything, so if you'd synced any of the old names, run `./migrate` to remove them (it offers a backup first). Update ait to v1.20.0 or later (`ait self-update`) and run `ait install-skills` *before* `./migrate`, or you'll be left without the renamed skills.

---

> **Heads up (19th August 2026):** The marp-* skills have moved to their own project in [marp-themes](https://github.com/UoGSoE/marp-themes).

---

> **Heads up (11th July 2026):** The plan-to-ait pipeline has been restructured for stronger main agents. The issue-crafting knowledge (epic/issue templates, testing modes, the amnesia test) now lives in a new `ait-crafting` skill, so the main agent can create issues straight from a feature conversation; the `plan-to-ait` agent is now a thin shell that loads that skill. There's also a new `ait-amnesia-check` agent — a fresh-context checker that *demonstrates* what it would build from newly created issues (never a verdict), so the caller can diff its reading against the real intent. The `conversation-to-ait` skill has been absorbed into `ait-crafting` and removed — if you'd previously synced it, delete it from your tool config (e.g. `rm -rf ~/.claude/skills/conversation-to-ait`).

---

> **Heads up (3rd July 2026):** `quality-gate` has grown into a two-tier review stack: free deterministic checks first (a section-order checker for Eloquent models and Livewire components in `skills/quality-gate/scripts/`, plus a drop-in Pest architecture test in `skills/quality-gate/arch/`), then the reviewer agents, all briefed via `skills/quality-gate/briefing.md` with whole-file reading rules. There's a new `laravel-conventions-reviewer` agent, and `test-quality-checker` now also hunts tautological tests, unit-tests-that-should-be-feature-tests, and test proliferation. The section order, arch rules, and conventions checklist encode *our* house style — read through and tweak them to yours before adopting.

---

> **Heads up (5th April 2026):** The Livewire/Flux skills and agents have been reorganised. `frontend-fluxui` is now `flux-ui`, `livewire-principles` is now `modern-livewire`, and the `livewire-flux-simplifier` agent has been replaced by `livewire-flux-reviewer`. There are also three new skills: `feature-workflow` (ait-driven feature development), `ui-to-flux` (migration helper), and `quality-gate` (post-feature review).
>
> If you've been using `./sync`, run `./migrate` to clean up the old names and pull in the new ones. If you copied files manually, have a read through the migrate script to see what's changed — it's short and commented.

---

## Skills

- `architecture-diagram` -- Builds an interactive architecture diagram of an app as one self-contained HTML file for non-technical managers: the app in its world first, then click a box to zoom into what's inside it. Reads the code (mostly Laravel, but Go, Python and others work too), groups it by what it does for people rather than how it's built, flags confirmed problems on the diagram, and keeps its report to a few lines. Bundles [elkjs](https://github.com/kieler/elkjs) for layout.
- `audience-credibility` -- Defensive review pass for audience-facing deliverables. Verifies named places, institutions, personas, and other local details before writing, then checks finished copy and visuals for recognisable AI-generated tells.
- `changelog` -- Analyses git tags and diffs to draft `CHANGELOG.md` entries in Keep a Changelog format. Proposes changes for review rather than writing them directly.
- `conversation-to-html` -- Turns Claude Code or Codex session logs into single-file HTML transcripts you can share or present.
- `cruft-or-keep` -- Conversational second pair of eyes for reachable-but-dormant code. Builds evidence-grounded case files for suspect jobs, mailables, listeners, routes, commands, and asks the developer `cruft or keep?` rather than deleting anything.
- `flux-ui` -- Flux UI v2 component reference for Laravel/Livewire. Covers syntax, patterns, common mistakes, and modal/form/table patterns.
- `github-create` -- Creates a new GitHub repo from the current project, pushes code, and sorts out the README, licence, and metadata. Uses the safe git/gh wrappers from [agent-commit](https://github.com/ohnotnow/agent-commit) if they're installed, falling back to plain `git`/`gh` otherwise.
- `golang` -- Conventions and patterns for Go CLI/TUI projects. Covers project layout, SQLite storage, Bubble Tea TUIs, embedded web UIs, flag parsing, migrations, error handling, and testing.
- `grounded-recommendation` -- Makes the agent investigate before recommending. It first searches for what else depends on the thing being changed, checks with you, then gives a recommendation with explicit uncertainty.
- `highlight-screenshot` -- Answers "which button is that?": logs in to a locally running app with playwright-cli, draws a red ring and a short label round the element behind a file:line (for example from a `devtools-rummage` finding), and hands back a checked screenshot. Local URLs only, uses Playwright's own Chromium, and closes the browser straight after.
- `homebrew-spring-clean` -- Walks developers through tidying `/opt/homebrew` (or `/usr/local` on Intel Macs). Surveys Homebrew disk usage, ranks cleanup targets, and handles cleanup, leaves, casks, stale logs, and autoremove without auto-deleting anything.
- `house-style` -- Teaches a personal editor agent the user's own editing taste by comparing an AI draft with their hand-edited version. Turns the differences into concrete editing procedures, then verifies them with controlled re-runs rather than trusting the agent's report.
- `larastan` -- Installs and runs PHPStan + Larastan, separates framework false positives from real defects, and iterates through analysis levels.
- `laravel-cloud` -- Deploy, update, and tear down demo apps on Laravel Cloud using the `cloud` CLI.
- `laravel-upgrade` -- Checks for a Laravel major-version upgrade (especially a Laravel Shift PR) that the upgrade guide and a green test suite both miss, plus a guide (`user-journeys.md`) to walking the upgraded app as each kind of user before it ships: finding the roles from the code, agreeing the journeys with the developer, and sorting regressions from things that were always broken. Learned on one Laravel 9 to 13 upgrade so far.
- `livewire-v4-upgrade` -- Audit-first workflow for upgrading production Laravel apps from Livewire v3 to v4. Covers app-shape triage, `wire:model` changes, layout/config traps, legacy model binding remediation, test baselines, browser smoke tests, and deploy pipeline gotchas.
- `mac-app-icon` -- Turns one square PNG into a macOS app icon: puts the artwork on a rounded square matching Apple's icon grid (so macOS 26 and later don't shrink it into a grey plate), shows the user background choices side by side, and generates an Xcode `AppIcon.appiconset` with a tested script. Needs ImageMagick.
- `mac-disk-hunter` -- Tracks down where disk space has gone on macOS, including misleading System Data, Time Machine local snapshots, developer caches, Docker, Xcode, and local ML models. Surveys and ranks the likely culprits first, then suggests appropriately cautious cleanup commands without deleting anything until you confirm.
- `mac-migration` -- Plans a developer's move to a new Mac: surveys the home directory by name and size (never by content), sorts it into copy / rebuilds itself / syncs itself / reinstall, and produces a re-runnable, dry-run-by-default rsync script that leaves the caches behind. Covers the non-file bits (Brewfile, uv tools, Docker volumes, DB data) and the Apple openrsync traps. Ships a template script to regenerate per machine.
- `modern-livewire` -- How we write Livewire components: principles, patterns, form state, testing. Covers everything from `findOrNew`+`fill`+`save` to named modals and `wire:model` behaviour.
- `plan-to-html` -- Converts markdown plans, design docs, and issue writeups into self-contained HTML documents for sharing with non-technical stakeholders. Includes a stylesheet you can customise, optional author/title metadata, print-friendly output, and an optional Background preamble for context.
- `playwright-cli-quirks` -- Hard-won failure modes of [playwright-cli](https://github.com/microsoft/playwright-cli), each stamped with the version and date it was verified: screenshots that come out blank or miss things, probes that silently do nothing, selectors and form fields that do something other than you meant, `run-code` not being a sandbox, a config file quietly swapping Chrome for a Chromium that renders WebGL in software, and the browser daemons left running afterwards. Load it alongside the vendor playwright-cli skill whenever an agent drives a browser.
- `practical-laravel-api` -- Conventions for practical, consumer-friendly Laravel JSON APIs with Sanctum. Covers self-describing response shapes, loud query failures, slugs, date windows, filtering, Scramble docs, and tests for API contracts.
- `quality-gate` -- One-stop post-feature review: free deterministic checks first (model/Livewire section-order script, drop-in Pest arch test), then fresh-eyes review agents. Two scopes — recent work, or a whole legacy codebase chunked by model orbit and delegated to a sub-orchestrator. Confirms before spending agent tokens.  (Note: it likes to ask you to commit a lot - if you don't trust your agent to do git stuff, have a look at [agent-commit](https://github.com/ohnotnow/agent-commit)).
- `readme` -- Generates a README from the actual codebase so claims stay grounded. To add your own conventions (tone, sections, stack tooling, licence attribution), create `~/.claude/skills/readme/assets/guidelines.md`; it isn't shipped, so syncing never overwrites it.
- `shell-function` -- Creates a shell function (bash, zsh, fish, etc.) that does what you describe.
- `sop-creator` -- Writes Standard Operating Procedure documents from user outlines. Asks minimal clarifying questions, then generates a clean Markdown SOP with purpose, prerequisites, procedure, and verification steps.
- `spec-crafting` -- Turns a settled feature discussion or plan document into consultant-ready issues in any tracker: a vision document plus implementation specs a fresh agent could pick up cold. Includes a "does this capture it?" review gate for conversation-sourced work, a referent check, testing modes, and pairs with the `amnesia-check` agent. If `ait` is available it records the work there; the `plan-to-ait` agent that `ait` ships loads this skill.
- `swift` -- Conventions and patterns for native macOS Swift apps. Young sibling of `golang`: XcodeGen workflow, sandbox-first permissions posture, fixture-backed testing, headless verification tricks, and a growing list of hard-won AppKit/SwiftUI gotchas.
- `technical-overview` -- Generates a `TECHNICAL_OVERVIEW.md` covering stack, architecture, domain model, routes, and key logic. Useful for onboarding.
- `threejs-quirks` -- Hard-won three.js and WebGL failure modes, each stamped with the version and date it was verified: shaders quietly recompiling when the last material using them is disposed, one NaN pixel blacking out a bloomed screen, colours converted twice, shader errors hiding from the console, and GPU timings that lie. A sibling of `playwright-cli-quirks`.
- `ui-migration-screenshots` -- Captures full-page reference screenshots of existing app UIs before or during frontend migrations. Uses Playwright for authenticated, role-gated, and interactive flows so rebuilt pages can keep a familiar 1:1 mapping.
- `ui-to-flux` -- Migration skill for converting older Laravel apps (Bulma, Bootstrap, Tailwind) to Flux UI. References `flux-ui` and `modern-livewire` for target patterns rather than duplicating them.
- `uofg-design-system` -- University of Glasgow web design system. Brand tokens, layout rules, and component patterns for HTML, CSS, React, Tailwind, and FluxUI.
- `wut` -- Ask the model to rewrite it's response in a more human-friendly and less jargon-laden way.

## Agents

- `amnesia-check.md` -- Fresh-eyes amnesia test for newly written specs, in any tracker or as files. With no conversation context it demonstrates what it would build from each one (restated goal, files, first failing test, every guess and dead end marked) so the caller can diff its reading against the real intent. Never gives a verdict. `ait` ships its own `ait-amnesia-check` for ait issues.
- `devtools-rummage.md` -- Reads a Laravel app the way a helpful desktop agent with browser devtools would, hunting for places where the frontend promises a restriction the server never checks: `:disabled` buttons with no matching check in the action, unlocked Livewire properties, API routes no page uses, spreadsheet uploads trusted row by row. Friendly colleague tone, read-only. Complements `laravel-owasp-reporter`.
- `fresh-eyes.md` -- Fresh pair of eyes for when you're stuck or looping. Suggests one or two things to try rather than editing code directly.
- `humaniser.md` -- Removes common AI-writing patterns from text files like READMEs and docs.
- `laravel-conventions-reviewer.md` -- Reviews Laravel code against team conventions: readable model helpers over raw column checks, fat models, Eloquent over query-building, enums over strings, duplicate-purpose methods. Seeded with real before/after examples — swap in your own house style before adopting.
- `laravel-owasp-reporter.md` -- OWASP-aligned security sweep of a Laravel app. Reports actual exploitable findings with concrete fixes.
- `livewire-flux-reviewer.md` -- Reviews Livewire/Flux code for simplification opportunities. Quick wins, things worth considering, and what looks good. References `flux-ui` and `modern-livewire` skills for pattern details.
- `phpmetrics-check.md` -- Runs phpmetrics on a PHP/Laravel codebase, flags complexity hotspots, and compares against a saved baseline.
- `plan-reconciler.md` -- Reconciles a plan document against the conversation that produced it. Reports what was captured, missed, glossed over, or drifted without editing the plan.
- `readme-editor.md` -- Deletion-first editor for READMEs and other text files. Cuts padding and applies the owner's house style, learned from their own hand edits of past documents, then reports what it cut. Leaves the owner's voice and slips alone, flagging rather than fixing them.
- `test-debug.md` -- Debugging assistant for stubborn failing tests. Uses `dump()` instrumentation rather than speculative rewrites.
- `test-quality-checker.md` -- Reviews Laravel tests for false-confidence patterns and coverage gaps: tautologies, weak assertions, missing control records, unit tests that should be feature tests.

## Syncing to your tools

Different AI coding tools (Claude Code, Codex, Gemini, Cursor, etc.) each have their own config directories for skills, agents and commands. The `sync` script copies everything from this repo into the right places.

1. Copy the example config: `cp sync.yaml.example sync.yaml`
2. Enable the tools you use and adjust paths if needed (`sync.yaml` is gitignored).
3. Run `./sync` (requires [uv](https://docs.astral.sh/uv/)).

If an installed file **differs** from the repo copy, the script asks before overwriting, regardless of timestamps — handy if you've been editing skills in-place. Choose overwrite the installed copy (`y`), leave both alone (the default), view a diff (`d`), or copy the installed version back into the repo (`b`). Identical files are left alone and missing files are copied without prompting. Items containing skipped files are listed at the end. Copy-back only covers files the repo already has: a file you added to an installed skill is never noticed, so copy that across by hand.

`./sync` refuses to run (`pick` and `preset` included) while `skills/`, `agents/` or `commands/` have uncommitted changes, in this repo or in any `sources:` directory. Commit or stash them first. That keeps unreviewed work from being installed, and means anything copied back with `b` can be undone with git. `--dry-run` still works, and `--force` does not bypass the check. A copy-back leaves the repo with uncommitted changes, so review and commit them before the next sync.

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
./sync             # prompt before overwriting differing files
./sync --dry-run   # preview only
./sync --force     # overwrite everything without asking
```

### Pulling in sibling repos with `sources`

Not everything lives in this repo — some tools ship as standalone repos that carry their own skills and agents alongside their code. Rather than remembering a separate install step for each, `sync.yaml` can list extra source directories and `./sync` treats their contents as if they lived here:

```yaml
sources:
  - ~/code/ux-agent/claude
  - ~/code/a11y-agent/claude
```

Each entry points at a directory that itself contains `skills/`, `agents/` and/or `commands/`. Every mode sees the merged set — the full sync, `--dry-run`, `pick`, and `preset` bundles can all draw from sources. On a name collision the first provider wins (this repo beats sources, earlier sources beat later ones) and the shadowed copy is reported, so nothing disappears quietly. `ignore` blocks apply to sourced items like anything else.

### Project-local skills with `pick` and `preset`

The default `./sync` is a full reconcile against your global tool config. But quite often you want the opposite — a fresh project where only a *handful* of skills/agents are relevant, dropped into the project's own `./.claude/` directory. Two modes for that:

```
./sync pick --to ~/code/my-project/.claude/           # interactive fuzzy picker
./sync preset go --to ~/code/my-project/.claude/      # named bundle from sync.yaml
```

Both treat `--to` as a base path — items land in `PATH/skills/<name>`, `PATH/agents/<name>`, etc. Neither touches `sync.yaml`'s `targets` block, so global syncs are unaffected.

#### `pick` — fuzzy picker with preview

Opens an [fzf](https://github.com/junegunn/fzf) multi-select across every available skill, agent and command. Type to filter, Tab to toggle, Enter to copy. The preview pane on the right shows each skill's `SKILL.md` (or the file itself for agents/commands), so you can browse and pick in one motion instead of remembering what each name does.

Items are tagged so the filter doubles as a scope:
- `[s]` skills
- `[a]` agents
- `[c]` commands

Typing `s golang` finds the Go skill; typing `[a]` shows all agents.

Requires `fzf` on PATH. If you don't have it, install via [the fzf docs](https://github.com/junegunn/fzf#installation) or use `preset` mode below.

#### `preset` — named bundles for shell aliases

For the "every Go project gets these three skills" case, declare a bundle in `sync.yaml`:

```yaml
presets:
  go:
    skills: [golang, github-create, changelog]
    agents: [test-debug]
  laravel:
    skills: [flux-ui, modern-livewire, larastan]
    agents: [livewire-flux-reviewer]
```

Then a one-line shell function gets you a zero-friction alias:

```bash
gopick() { /path/to/agentic-stuff/sync preset go --to "$PWD/.claude/"; }
```

`cd` into a fresh repo, type `gopick`, done.

`--dry-run` previews either mode without writing anything; `--force` overwrites differing files without prompting.

## You might also be interested in

Standalone repos and tools that pair well with this collection - the `quality-gate` skill knows how to call on the first two, and the `sources:` block above will sync their skills and agents alongside these:

- [a11y-agent](https://github.com/ohnotnow/a11y-agent) — a deterministic accessibility CLI (axe scan, keyboard tab-order walk, screen-reader transcript) with its own Claude Code skill and background checker agent. Makes the a11y audit nobody gets time for nearly free.
- [ux-agent](https://github.com/ohnotnow/ux-agent) — skills that drive a real browser against your local app to produce bug-reproduction videos, user-guide videos that re-film themselves, and cold UX journey reports from a code-blind probe agent.
- [playwright-cli](https://github.com/microsoft/playwright-cli) - Microsoft's browser-automation CLI, a good add-on for any UI/browser work. It ships its own Claude Code skill (installed via `playwright-cli install --skills`), and the `flux-ui` skill here leans on it to verify rendered pages rather than trusting that compiling Blade means correct pixels.
