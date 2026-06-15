---
name: ui-migration-screenshots
description: >-
  Capture faithful, full-page reference screenshots of an existing web app's UI
  before or during a frontend migration (for example Bulma/Bootstrap + Vue to
  Livewire/Flux + Tailwind), so the rebuilt UI can keep a familiar 1:1 mapping
  for end users who treat the app as a tool. Use this whenever the user wants to
  screenshot or snapshot the current UI, capture every admin/staff/student page
  for reference, grab login-only or role-gated pages (including via
  impersonation), or says things like "screenshot the old UI", "capture the
  current pages", or "reference shots for the migration". Drives a real browser
  with Playwright rather than the in-browser Chrome screenshot tool, which only
  captures the viewport and cannot save full pages to disk. Tuned for Laravel
  apps but the capture technique applies to any web app.
---

# UI migration screenshots

## Why this exists

When you migrate an app's frontend, the safest outcome for the people who use it
is a **1:1 mapping** of the old UI onto the new one. Most users think of the app
as a tool — they don't care about polish, they care that the button is where it
was and the flow works the way it always has. A complete set of full-page
"before" screenshots lets you rebuild each page next to its reference and keep
things familiar.

This skill captures **every page a given role can reach** — including the
interactive, role-gated flows you only ever see while logged in *as that role*
(e.g. a student ranking project choices) — and saves them as full-page PNGs.

## The one big lesson: use Playwright, not the in-browser Chrome tool

If you have an in-browser/MCP Chrome screenshot tool available, it is tempting
to reach for it. Don't, for this job. It has two fatal limitations here:

1. **It captures the viewport only.** The rendered viewport is clamped to the
   visible screen height, so anything below the fold is cut off. You cannot make
   the window tall enough to fit a long page — the OS/browser caps it.
2. **It doesn't give you a file path you can reach.** Its "save to disk" writes
   somewhere your shell can't see, so you can't post-process or stitch.

**Playwright's `page.screenshot({ fullPage: true })` solves both** — it renders
and captures the entire scrollable page to a PNG at a path you choose, at
whatever device-scale-factor you want for crisp text. Install it with the user's
permission (see Setup), then use the scripts in `assets/`.

## Setup

Playwright needs Node and a one-time Chromium download:

```bash
npm install --no-save playwright   # --no-save keeps it out of the app's package.json/lockfile
npx playwright install chromium    # downloads Chromium to a cache outside the repo (~150MB)
```

`npm install` is commonly blocked by a permission hook — **ask the user to run
it** (or to approve it) rather than retrying. `--no-save` matters: migration
tooling shouldn't churn the target app's dependency manifest.

## Workflow

Work through these in order. Steps 1–3 are reconnaissance; 4–6 do the capture.

### 1. Map the pages a role can reach

For Laravel: `php artisan route:list --method=GET --except-vendor`. Then read the
nav/menu partial(s) to see what's actually linked for each role. Sort routes
into:

- **Real pages** to capture: index/list pages, create/edit/show pages, dashboards.
- **Parameterised pages** (`/course/{course}`, `/user/{user}`) — need a real id.
- **Not pages, skip these**: file exports/downloads, JSON API endpoints,
  redirect/auth/logout/toggle routes, and any deliberate test routes (e.g. a
  route that throws to test error reporting, or one that fires real
  notifications/emails — never trigger those).

List the page set explicitly and tell the user what you're skipping and why.

### 2. Find representative record IDs

Detail/edit pages need ids that actually exist **in the context the browser will
be in**. This is the subtle one: an id you find via `tinker`/CLI may 404 in the
browser because of tenant/session global scopes (see `references/gotchas.md` —
"Scoping: CLI vs web"). Derive ids from the active web context, or query with the
correct scope value explicitly. A 404 on a detail page almost always means the
id isn't visible under the current scope, not that the page is broken.

### 3. Work out how to authenticate

A fresh Playwright browser has no session, so it must log in. Check how auth
works before scripting:

- Is there a username/password form, or is it SSO-only? (SSO usually can't be
  automated — see gotchas.) In Laravel, check `config('sso.enabled')` and whether
  the login view renders a form or only an SSO button.
- Does the password get verified locally? (If LDAP/remote auth is off in dev,
  any password may work for a known username — still pass something.)
- Note the field selectors (`#username`, `#password`) and the submit control.

Confirm the chosen user has the role whose pages you want.

### 4. Capture the pages

Use **`assets/capture-pages.cjs`** as the template. Copy it into the target app
repo (or run it from there), then edit the `CONFIG` block, the `login()`
function, and the `pages` list. It:

- logs in, then visits each page and saves a full-page PNG named after the route;
- hides overlays that aren't part of the real UI (the Laravel debugbar
  re-renders on every navigation — hide it per page, see gotchas);
- logs the HTTP status per page and prints a summary of anything non-2xx so you
  can spot 404s (wrong id) and 500s (pre-existing breakage).

Run it from the app repo: `node capture-pages.cjs`. If a page errors, capture it
anyway (the error page is informative) and **flag it — don't fix the old app**;
a pre-existing 500 in the legacy UI is a finding, not your bug.

### 5. Capture role-gated / interactive flows

Some pages and whole journeys only exist for a particular role (student, staff,
applicant). If the app has an **impersonation** feature, an admin can step into a
user and you can capture their journey. Use
**`assets/capture-impersonated-flow.cjs`** as the scaffold — it logs in as admin,
triggers impersonation through the real UI, then walks a multi-step flow taking a
full-page shot at each meaningful state.

Interactive flows are inherently app-specific, so the script carries a fully
worked example (a student expanding projects, ranking 1st–5th preferences, and
submitting) with the reusable patterns called out in comments: deriving element
ids from the DOM, clicking through Vue/Livewire state, waiting on
`waitForURL`/`networkidle`, and screenshotting each state.

Two things to watch (detailed in gotchas):
- **Impersonation can bypass eligibility rules** (deadlines, "already accepted"),
  so the captured state may be more permissive than a real user's. Useful, but
  say so.
- **Completing a flow mutates data** (submitting choices, saving a form). It's
  usually local test data and reversible, but the user asked for the flow — still
  tell them what it wrote and offer to revert.

### 6. Review and report

Spot-check a few PNGs (a detail page, the tallest list, one interactive state) to
confirm full-page capture worked and overlays are gone. Then report: how many
pages, where they're saved, anything that 404'd/500'd and why, any data you
mutated, and the path to the re-runnable script(s) so the user can re-snapshot as
the migration progresses.

## Assets

- `assets/capture-pages.cjs` — template for bulk full-page capture of a route
  list. Edit `CONFIG`, `login()`, and `pages`.
- `assets/capture-impersonated-flow.cjs` — scaffold + worked example for
  capturing a role-gated, multi-step interactive journey via impersonation.

## Gotchas and deeper detail

`references/gotchas.md` collects the hard-won lessons: the Chrome-tool limits in
full, the debugbar, auth/SSO/LDAP, CLI-vs-web scoping, impersonation rule
bypasses, screenshot quality settings, and the npm-install permission hook. Read
it before adapting the scripts to a new app — it'll save you the same dance we
went through the first time.
