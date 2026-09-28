---
name: highlight-screenshot
description: Take a screenshot of a page in a locally running app with a red ring and a short label round one element, so a developer can see exactly which button, link or field a finding is about. Use when the user asks "which button is that?", "show me where that is", or wants a screenshot pointing at the element behind a file:line from a review (for example a devtools-rummage finding). Local apps only; uses playwright-cli with Playwright's own Chromium.
---

# Highlight screenshot

A finding says `choose-project.blade.php:24`, and the page has twenty buttons. The developer wants a picture with "this one" on it. This skill logs in to their local app, rings the element, and hands back a screenshot.

It is a pointer, not a test. Navigate and look; never click anything that saves, sends or deletes.

Load the `playwright-cli` and `playwright-cli-quirks` skills alongside this one.

## 1. Work out the page and the element

Start from the file and line.

- **The page.** Find the Livewire component or controller that renders the view, then the route that reaches it (`routes/web.php`, or `lando artisan route:list`). If the route needs a record id, find one that the logged-in user can actually see.
- **The element.** Read the Blade around the line: its text, `wire:click`, label, and whether it sits in a `@foreach` or inside a modal. Turn that into a Playwright locator, preferring role and name (`getByRole('button', { name: 'Accept' })`).
- **Repeated elements.** One Blade line in a loop can render a dozen identical buttons. Ring one, the first that fits the finding (for example the first disabled one), and name it in the label ("Copy next, Monday 5th"). Ringing all of them brings back the "which one?" problem.
- **Not rendered.** If the element is behind `@if`/`@can` and the user you log in as never sees it, say so. That is often the point of the finding. Don't hunt for another account without asking.

## 2. Check the URL is local

Only `localhost`, `127.0.0.1` and `*.lndo.site`. Anything else: stop and ask. This is a guard against pointing a browser at a real service by mistake, not a security boundary.

## 3. Open the browser

Ask the user for a login if they haven't given one. Don't read `.env` or seeders to find one.

Work from the app's root. If `.playwright/cli.config.json` doesn't exist there, create it:

```json
{
  "browser": {
    "browserName": "chromium",
    "launchOptions": { "channel": "chromium" },
    "contextOptions": { "ignoreHTTPSErrors": true, "viewport": { "width": 1280, "height": 800 } }
  }
}
```

The `channel` matters: without it playwright-cli drives the user's installed Google Chrome, and macOS may then pop up a prompt asking to let the terminal modify apps. If the bundled Chromium is missing, `playwright-cli install-browser chromium` fetches the build playwright-cli expects (the revision must match, so an `npx playwright install` from a different Playwright version won't do).

```bash
playwright-cli -s=highlight open --idle-timeout=600000 https://<app>.lndo.site/login
```

The idle timeout closes a forgotten session after ten minutes instead of the default hour.

Log in with `run-code`, using the form's labels:

```bash
playwright-cli -s=highlight run-code "async page => { await page.getByLabel('Username').fill('<user>'); await page.getByLabel('Password').fill('<password>'); await page.getByRole('button', { name: 'Log In' }).click(); await page.waitForURL(u => !u.pathname.startsWith('/login')); return page.url(); }"
```

Then `goto` the page. If the element lives in a modal or a tab, open it; that click must be one that only shows something.

## 4. Ring it and take the shot

Copy `highlight.js` (next to this file) somewhere outside the app, edit its three constants (locator, label, output path) and run it:

```bash
playwright-cli -s=highlight run-code --filename=/absolute/path/to/your/highlight.js
```

- Target elements with locators in the script, not snapshot refs: disabled elements get no `ref` in playwright-cli's snapshot.
- Save to `screenshots/<short-slug>-<yyyy-mm-dd>.png` in the app's root, as an absolute path.
- Keep the label short: "This one: Save", plus which instance if it repeats.
- If the Laravel debugbar covers the element, hide it (`.phpdebugbar { display: none !important; }`) and say so.

Then **look at the image** with the Read tool before handing it over. Is the ring round the right element, solid red, with the label clear of it? A screenshot can come back blank or show the wrong page (see `playwright-cli-quirks`).

## 5. Close up straight away

As soon as the shot is checked, before you report:

```bash
playwright-cli -s=highlight close
ps -axo pid,command | rg -i 'cliDaemon|playwright_|ms-playwright'
```

Nothing should be left. Don't leave a browser open while you talk to the user.

## 6. Report

Give the full path of the screenshot (the user's terminal hides link targets, so write the path out), the page URL, and which instance you ringed if the element repeats. If the element wasn't rendered for that user, say that instead of producing a screenshot of the wrong thing.
