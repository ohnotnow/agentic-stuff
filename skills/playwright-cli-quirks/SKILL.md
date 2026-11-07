---
name: playwright-cli-quirks
description: >
  Hard-won failure modes of playwright-cli, verified in real sessions. Load
  alongside the vendor playwright-cli skill EVERY time you drive a browser -
  before trusting any screenshot, console check or interaction probe - and
  check the cleanup section when finished. Screenshots and probes can silently
  lie; this is the list of known ways.
allowed-tools: "Read,Bash,Glob,Grep"
version: "0.1.0"
author: "ohnotnow <https://github.com/ohnotnow>"
license: "MIT"
---

# playwright-cli quirks

Field notes to sit beside Microsoft's own playwright-cli skill (which gets
overwritten by `playwright-cli install --skills`, hence this separate file).
Every rake below was hit and verified in a real session, and each is stamped
with the version and date it was verified on. Current playwright-cli at the
time of writing: **0.1.18 (2026-08-07)**. If you are on a much newer version,
re-verify a rake before relying on it, and delete any that upstream has fixed.

## Screenshots lie: blank or missing pixels are measurement artefacts

Order of checks before trusting any capture:

1. `goto`/`open` WITH the output visible - did navigation actually happen,
   and what is the page title?
2. Console errors.
3. DOM probe via eval.
4. Only then trust pixels.

- **`file://` URLs are refused outright** ("Error: Access to \"file:\"
  protocol is blocked") - and if you swallow the goto output you will happily
  run checks against `about:blank`: zero console errors, blank-white
  screenshot, empty title, no DOM. Serve the directory over http instead
  (`python3 -m http.server <port>`). A human's real browser opens `file://`
  fine; only the tool blocks it. (Verified 2026-08-05.)
- **A healthy WebGL/three.js page also screenshots blank in headless mode** -
  the drawing buffer is cleared before capture when `preserveDrawingBuffer`
  is false (the default). Blank pixels are a measurement artefact, not a
  broken page. Working probe: force `renderer.render(scene, camera)` then
  measure `renderer.domElement.toDataURL().length` in the SAME evaluate call
  (a real frame is ~34KB; a blank canvas well under 1KB). Handy: classic
  (non-module) scripts put top-level `const` bindings in global lexical
  scope, so evaluate can reach them by bare name. A screenshot taken right
  after such an eval also captures real pixels. (Verified 2026-08-05.)
- **Large translucent overlay divs can render fine in the live DOM yet be
  completely MISSING from screenshots** - DOM, getComputedStyle and
  getBoundingClientRect all look correct while the capture shows the page
  undimmed. ~15 live probes eliminated paint timing, huge z-index, alpha
  itself, pointer-events, cssText-vs-property writes and isolated-vs-main
  world; the root cause was never diagnosed (best guess, clearly a guess:
  Chromium's solid-colour-layer quad optimisation interacting with the CDP
  capture path). Opaque backgrounds on the same elements always captured;
  border/box-shadow siblings always captured. So: if a screenshot must prove
  an overlay exists, verify against the CAPTURED IMAGE, not the DOM, and
  prefer border/box-shadow visuals over large translucent fills. (Headless
  Chromium via CDP, macOS, ~July 2026; abandonment documented in a11y-agent
  `src/observer/highlight.ts`.)

## Interaction probes that silently no-op

Before trusting ANY interaction probe, assert its precondition actually
changed: read scrollTop/DOM state before AND after the input. A verification
that shares the instrument's flaw confirms the artefact, not the behaviour.

- **Negative numeric arguments are eaten by the flag parser** -
  `playwright-cli mousewheel 0 -800` prints "Unknown options: --0, --8" and
  scrolls NOTHING, so a "wheel up" probe is a silent no-op (a trailing
  `| tail -1` on the next command can hide the usage error). This once led to
  rewriting correct page scroll logic based on a probe that never scrolled.
  For negative deltas go through
  `playwright-cli run-code "async page => { await page.mouse.wheel(0, -800); }"`.
  (Verified @playwright/cli 0.1.15, 2026-07-10.)
- **`eval` takes a SINGLE JS expression** - multi-statement strings
  SyntaxError and silently return "undefined". Use the comma operator
  `(a, b, c)` or `run-code`.
- **After a server restart + page reload, the FIRST eval can run in the dead
  pre-reload page context** - mutations lost, return value looks plausible.
  Do a throwaway read-eval first, then read staged state back before
  trusting it.
- **Autonomous actors keep running BETWEEN commands** - per-command latency
  (~0.3s) aliases fast state, and things like enemy AI or rising timers will
  change the world mid-test (a patrolling enemy repeatedly killed an idle
  player between commands). Stage multi-step scenarios in ONE command chain
  and neutralise actors first. For real-time canvas/game apps, expose an
  in-page debug handle (e.g. `globalThis.__app.debug()` returning live
  state) and read state deterministically instead of doing screenshot
  archaeology. (Verified on a Bun-served TypeScript canvas game, 2026-07.)

## Selectors and forms that do something other than you meant

All verified on a Laravel app (Vue 2 plus Livewire 3), @playwright/cli
0.1.21, 2026-11-07.

- **`:has-text()` is a case-insensitive SUBSTRING match, and it can land on a
  destructive button.** `click "button:has-text('All') >> nth=0"`, meant for
  an "All" filter button, clicked "Clear all staff from courses" instead,
  because that button came first in the page. It opened a "remove all staff
  from all courses?" confirmation, which was luckily never confirmed. The
  mistake was only noticed because a later click timed out behind the
  modal. Use `:text-is('All')` (exact match) or a snapshot ref, and always
  near any page that has delete or clear buttons. If a click unexpectedly
  times out with "subtree intercepts pointer events", read the modal before
  doing anything else.
- **`upload` only works while a file chooser is open.** Without one it fails
  with "The tool "browser_file_upload" can only be used when there is related
  modal state present". Clicking a styled file button doesn't reliably open
  one. Set the file directly instead:
  `run-code "async page => { await page.locator('input[type=file]').nth(0).setInputFiles('/abs/path/file.pdf'); }"`.
  This fires the input's change event, so Vue and Livewire see it.
- **`fill` doesn't fire `change`, so `wire:model.change` (and
  `.lazy`/`.blur`) fields don't update until focus leaves.** A Save button
  that is disabled until something changes stays disabled, and a click on it
  does nothing, with no error (output piped to /dev/null hides even the
  timeout). After `fill`, `press Tab` and wait a second before clicking.
- **A select showing one option isn't necessarily selected.** In a Vue
  `v-model` select whose model starts as `""`, the browser displays the only
  option, but the model is still empty. The form's submit then returned
  early with no request and no message. A human hits this too, so it's a
  real finding, but in a probe always `select` the option explicitly, and
  check `playwright-cli requests` to confirm the POST actually went.
- **Switching between http:// and https:// on the same host can log you
  out.** Visiting the https version (to follow a signed link that was
  generated for https) set a new session cookie that replaced the http one,
  and the next http page returned 401. Pick one scheme per session, and
  follow emailed links on the scheme they were generated for (signed URLs
  include the scheme in the signature).

## `run-code` is not a sandbox; `eval` is

Matters whenever an agent's playwright-cli use is meant to be confined (e.g.
a probe that must not read the codebase).

- **`run-code` LOOKS sandboxed but isn't.** It runs in a Node `vm` context:
  `require`, `process` and `import()` are all missing, so the obvious file
  reads fail. But Node's `vm` is not a security boundary: reaching the host
  realm's `Function` constructor through any passed-in object hands back the
  real `process`, i.e. full Node. And Playwright's own page methods read
  files by path with no escape needed: `page.addStyleTag({path})` (or
  `addScriptTag`) injects any file's contents into the page, where an
  evaluate can read them back. Treat `run-code` as arbitrary code execution
  on the host. (Both verified against a scratch canary file, @playwright/cli
  0.1.21, 2026-10-08.)
- **`eval` runs in the page, inside the browser's sandbox**: no `require`, no
  `process`. It can still do most page work, e.g. scroll something into view
  (`document.querySelector(sel).scrollIntoView()`) or scroll up without the
  negative-number rake (`window.scrollBy(0, -800)`). If an agent must be
  confined, allow `eval` and deny `run-code`.

## Driving npm-only browser libraries inside a page

Verified pattern: esbuild-bundle the package via a stdin wrapper to an IIFE
that assigns a window global, then `page.addScriptTag({ path })` and drive it
from evaluate. Concrete case (@guidepup/virtual-screen-reader 0.32.1):
wrapper `import { virtual } from "@guidepup/virtual-screen-reader";
window.__a11yVsr = virtual;` bundled minified (~400KB) with
`platform: "browser"`, which resolves the package's browser condition
automatically - worked first try. Pair with the browser-context option
`bypassCSP: true`, or a strict CSP on the target page blocks the script tag.
(Verified Playwright 1.61 + esbuild 0.28, 2026-07-09.)

## A config file can swap the browser, and the GPU with it

- **`browserName: "chromium"` in a `--config` file silently swaps the
  browser.** A plain `playwright-cli open`, or a config whose `browser` block
  leaves `browserName` out, drives the installed Google Chrome, whose headless
  WebGL runs on the real GPU (ANGLE on Metal). Name `chromium` and you get
  Playwright's own `chromium_headless_shell` instead, which renders WebGL in
  software (SwiftShader): a three.js scene that ran at 60 fps took about a
  second a frame, and every timing from it was meaningless. To pass launch
  flags, put them in `browser.launchOptions.args` and leave `browserName` out;
  they still apply (checked with `--lang=en-GB`). Before trusting any WebGL
  timing, read the renderer string:
  `gl.getParameter(gl.getExtension('WEBGL_debug_renderer_info').UNMASKED_RENDERER_WEBGL)`
  names `ANGLE Metal Renderer` on the GPU and `SwiftShader` in software.
  (Verified @playwright/cli 0.1.21, Chrome 154 against
  chromium_headless_shell-1246, macOS, 2026-10-19.)

## Clean up after yourself

playwright-cli daemons persist after sessions end. Each owns a headless
Chrome process tree (renderer, GPU, audio, network, storage helpers), GPU
helpers can idle at 20%+ CPU each, and `playwright-cli list` does NOT reveal
all of them. (Verified 2026-07-10.)

Diagnose:

```bash
ps -axo pid,ppid,etime,%cpu,command | rg -i 'playwright|playwright_chromiumdev_profile'
```

Resolve (daemons first, then their orphaned Chrome profiles):

```bash
pkill -TERM -f 'playwright-core/lib/entry/cliDaemon.js'
pkill -TERM -f 'playwright_chromiumdev_profile-'
```

Re-run the diagnose line; no output beyond the grep itself means clean.

Prevention after any playwright session: close every named session
explicitly (`playwright-cli -s=NAME close`), run `playwright-cli list`, then
check the actual process table anyway - a handful of Chrome Helpers is
normal for one browser; several abandoned Playwright trees multiply them.
