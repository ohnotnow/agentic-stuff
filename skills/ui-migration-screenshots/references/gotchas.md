# Gotchas & tips

The things that cost time the first time round. Read before adapting the
scripts to a new app.

## Contents

1. Why the in-browser Chrome tool fails for this
2. Hiding the Laravel debugbar (and other overlays)
3. Authentication: forms, SSO, LDAP
4. Scoping: CLI/tinker IDs vs the web session
5. Impersonation, and the rules it quietly bypasses
6. Representative IDs, 404s and 500s
7. Screenshot quality settings
8. The npm-install permission hook
9. Lando / database access

---

## 1. Why the in-browser Chrome tool fails for this

If an MCP/in-browser Chrome screenshot tool is available, you'll be tempted to
use it. For full-page reference capture it has two blocking problems:

- **Viewport-only capture.** The rendered viewport is clamped to the visible
  screen height. On a 2560×1440 display the usable viewport tops out around
  ~1000 CSS px. Resizing the window taller is rejected once it would extend more
  than ~50% off-screen, and even a tall window doesn't enlarge the captured
  viewport — the off-screen part isn't rendered. So anything below the fold is
  lost.
- **No reachable file path.** Its "save to disk" writes somewhere your shell
  can't see (different sandbox), and the path isn't returned in a usable form.
  So you can't move, rename, or stitch the output.

Scroll-and-stitch would work around the height limit, but you can't stitch files
you can't read, and it's fiddly (sticky headers repeat, last-slice overlap).

**Playwright `page.screenshot({ fullPage: true })` is the right tool**: it
renders the whole scrollable page off-screen and writes a PNG to a path you
choose, at your chosen `deviceScaleFactor`. No stitching, no clamping.

## 2. Hiding the Laravel debugbar (and other overlays)

With `APP_DEBUG=true`, the Laravel debugbar renders a bar across the bottom of
every page — noise in a reference shot. Two traps:

- Closing it via its own UI **doesn't persist** — it re-injects on the next
  navigation.
- Don't disable it by editing `.env` or `config/debugbar.php` — that's a change
  to the app you're only screenshotting.

Instead inject CSS to hide it **after every navigation** (the scripts do this via
`addStyleTag` with `.phpdebugbar { display:none !important }`). Same approach for
any dev-only banner or cookie bar you don't want in the shot. A "test
site/test data" banner that's part of the real local UI is fine to leave in.

## 3. Authentication: forms, SSO, LDAP

A fresh Playwright browser has no session and must log in. Before scripting,
establish:

- **Is the login a form or SSO-only?** Many apps show the username/password form
  only when SSO is disabled. In Laravel check `config('sso.enabled')` and look at
  the login view: does it render `<input>` fields or just a "Login with SSO"
  button? **SSO generally can't be scripted** (external IdP, MFA). Options if
  it's SSO-only: temporarily enable a local password route in dev, seed an
  authenticated session/cookie, or ask the user to provide a storage-state.
- **Is the password actually verified in dev?** If LDAP/remote auth is off
  locally, the login action may just look up the username and log in without
  checking the password. You still must fill the password field (it's usually
  `required`), but any value works.
- **Note the exact selectors** (`#username`, `#password`) and the submit button
  text/selector, and confirm the user has the role whose pages you want.

For Livewire login forms: `wire:model` is deferred by default, but Playwright
`fill()` fires real input events and the values are sent with the submit
request, so a normal fill + click works.

## 4. Scoping: CLI/tinker IDs vs the web session

The sharpest trap. Models are often constrained by a **global scope tied to
session/tenant state** — e.g. an academic-session scope:
`where('session_id', session('academic_session'))`.

In CLI/`tinker` (and host-side DB tools) there's **no web session**, so
`session('...')` is null, the scope is skipped, and a query returns records from
*any* tenant/session. An id you found that way (e.g. id 1) then **404s in the
browser**, because the browser's session pins a specific tenant and the
route-model binding applies the scope.

Fixes:
- Find ids the browser will actually see — query `withoutGlobalScopes()` and add
  the **correct scope value explicitly** (e.g. `where('session_id', 3)` for the
  active session), or read them off an index page that already rendered.
- Treat a 404 on a detail page as "wrong id for this scope", not "page broken" —
  re-check the scope before anything else.

## 5. Impersonation, and the rules it quietly bypasses

If the app lets an admin impersonate a user, that's the way to reach role-gated
pages and flows. Trigger it through the real UI (a button/dropdown item) so you
also exercise the normal path and handle CSRF automatically.

Watch for **eligibility rules that are deliberately relaxed during
impersonation.** Real example: `isTooLate()` returns `false` when impersonating
(there was a literal "ignore the rules they asked for" comment), so an
impersonating admin can use controls a real, past-deadline user couldn't. Great
for capturing the flow — but the captured state can be *more permissive* than a
real user's, so note it.

Impersonation may also switch the active tenant/session (e.g. to "latest") on
entry — which interacts with §4. Check the impersonation controller.

## 6. Representative IDs, 404s and 500s

- Detail/edit/show pages need a real id; pick one representative record per type
  that exists in the browser's scope (§4).
- A **404** on a detail page → almost always the wrong id for the current scope.
- A **500** is usually **pre-existing breakage in the legacy app**, not your
  problem to fix (real example: a view extending a layout that doesn't exist).
  Capture the error page anyway — it's a useful finding — and flag it to the
  user. Don't "fix" the app you were only asked to screenshot.

## 7. Screenshot quality settings

- `deviceScaleFactor: 2` gives crisp, retina-quality text — worth it for
  reference shots you'll squint at while rebuilding.
- A `viewport.width` of ~1440 matches a typical desktop; centred/max-width
  containers will show their normal side margins.
- `fullPage: true` handles tall pages and relative-positioned navbars cleanly.
  (If a page has a `position: fixed` header, full-page capture still works in
  Playwright — no repeated headers, unlike scroll-and-stitch.)

## 8. The npm-install permission hook

`npm install` is frequently blocked by a pre-tool hook. **Ask the user to run it
(or approve it)** rather than retrying — and use `--no-save` so migration tooling
doesn't churn the target app's `package.json`/lockfile:

```bash
npm install --no-save playwright
npx playwright install chromium    # Chromium downloads to a cache outside the repo
```

To remove later: `rm -rf node_modules/playwright`.

## 9. Lando / database access

For Lando-based apps, run artisan/tinker through Lando: `lando artisan tinker
--execute '...'`. Host-side DB/MCP tools often can't resolve Lando's internal
`database` host, so go through Lando for any DB reconnaissance (finding ids,
checking config like `sso.enabled`/`ldap.authentication`).
