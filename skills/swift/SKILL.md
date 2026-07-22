---
name: swift-user-conventions
description: >
  User's conventions and patterns for native macOS Swift apps. Use when working
  on a Swift or macOS app project
allowed-tools: "Read,Write,Edit,Bash,Glob,Grep"
version: "0.1.0"
author: "ohnotnow <https://github.com/ohnotnow>"
license: "MIT"
---

# Swift / macOS App Conventions

Standards for small native macOS apps — menu-bar utilities, desktop companions,
focused tools. These are opinionated defaults, not laws. This skill is young
(much younger than its golang sibling): a handful of conventions and a gotcha
list earned mostly in one project. When a session teaches a new lesson, add it
here rather than leaving it in a transcript.

## Project workflow

- [XcodeGen](https://github.com/yonaskolb/XcodeGen): `project.yml` is the
  source of truth, the generated `.xcodeproj` is checked in. Regenerate with
  `xcodegen generate` after any structural change, before building.
- Build from the terminal with `xcodebuild ... -derivedDataPath build build`;
  run tests with `CODE_SIGNING_ALLOWED=NO`.
- Swift 6 with `SWIFT_STRICT_CONCURRENCY: complete` from day one — far cheaper
  than retrofitting it later.
- Menu-bar / background apps: `LSUIElement: true` in Info.plist properties.
- When the application is ready for testing - offer to write a simple `./build.sh` script
  rather than making users run some (probably unfamiliar) xcode/swift commands.


## Permissions and privacy posture

- App Sandbox and hardened runtime on; entitlements minimal (often just
  `network.client`).
- Design *around* Accessibility, Screen Recording and Automation permissions
  rather than requesting them. Example: `CGWindowListCopyWindowInfo` geometry
  (owner PID/name, bounds, layer, alpha — **not** window titles) needs no
  permission at all and works sandboxed.
- Secrets live in Keychain generic-password items only — never in
  `UserDefaults`, source, test fixtures or logs.
- If the README documents what's stored in `UserDefaults`, keep that list
  truthful when adding features — libraries may write their own defaults (e.g.
  KeyboardShortcuts stores the recorded shortcut there).
- Ad-hoc signed rebuilds look like new apps to Keychain, so the first access
  after a rebuild re-prompts. Expected, not a bug.

## Dependencies

- Start dependency-free. When a problem is fiddly, permission-sensitive and
  already well-solved (e.g. global hotkeys plus a shortcut-recorder control),
  one battle-hardened SPM package beats hand-rolling —
  [sindresorhus/KeyboardShortcuts](https://github.com/sindresorhus/KeyboardShortcuts)
  being the canonical example.
- Pin `from:` a real release tag, and verify the latest with
  `git ls-remote --tags <url>` rather than trusting memory (the model once
  confidently guessed "2.x"; reality was 1.10.0).
- Expect strict-concurrency friction with pre-Swift-6 libraries. Prefer a
  narrow local fix — e.g. `@MainActor` on your own static constant — over a
  blanket `@preconcurrency import`.

## Testing

- XCTest. Network code is fixture-backed via `URLProtocol` stubs; Keychain
  tests use temporary items; the suite never makes live provider calls. Live
  API checks are separate opt-in scripts under `Tools/`.
- Guard app bootstrap with an is-running-unit-tests check (Naiku's
  `AppRuntime.isRunningUnitTests`) so launching the app as a test host spawns
  no UI.
- Put the same guard on anything reading live system state (CGWindowList,
  screen parameters), or the suite inherits whatever happens to be on the
  developer's desktop.

## Verifying beyond a green build

Drive the real app — a compiling binary and passing tests are necessary, not
sufficient. Useful sandboxed, permission-light techniques:

- **Window census**: a five-line Swift script over `CGWindowListCopyWindowInfo`
  listing the app's windows by owner name and bounds proves a panel appeared
  (window *titles* would need Screen Recording; bounds don't).
- **State seeding**: write `UserDefaults` before launch to put the app in the
  state under test — e.g. `KeyboardShortcuts_<name>` takes a JSON string
  `{"carbonKeyCode":N,"carbonModifiers":M}`. Read the library's source to
  confirm a storage format; never guess it.
- **Synthetic input**: `osascript -e 'tell application "System Events" to key
  code ...'` (the host terminal needs Accessibility; if it's not granted,
  degrade gracefully and ask the user to press the key).
- The `defaults` CLI transparently follows sandboxed apps into their container
  (`~/Library/Containers/<bundle-id>/...`).
- Terminal-spawned probe apps are denied activation on modern macOS, so
  focus-dependent behaviour (key windows, first responders, focus-only visual
  artefacts) only reproduces in the real app.

## Gotchas, earned the hard way

Mostly from Naiku (`https://github.com/ohnotnow/naiku`), macOS 26 / Xcode 26.1.1.
Symptom → fix.

- **Borderless `NSPanel` refuses key status** → text fields silently
  untypable. Subclass and `override var canBecomeKey: Bool { true }`.
- **`performClose(nil)` on a borderless window is a silent no-op** —
  `.closable` in the style mask is not enough, AppKit wants an actual close
  widget — so `windowShouldClose` delegate logic never fires. Override
  `performClose` to run the delegate contract yourself, then `close()`.
- **Dark rectangular halo around a transparent/glass window that toggles with
  focus** = the key-window shadow. `invalidateShadow()` does not fix it;
  `hasShadow = false` does. Diagnostic tell: content can't paint outside
  window bounds and doesn't change with focus — shadows do both.
- **`NSHostingController`'s default `sizingOptions`** pin the hosting view to
  the SwiftUI *minimum* size, leaving an invisible dead strip inside a larger
  window. Set `sizingOptions = []` and manage window sizing yourself
  (`setContentSize` + `minSize`). One print of `window.frame` vs
  `window.contentView?.frame` settles it.
- **macOS 26: withholding `.fullScreenAuxiliary` does not keep a
  `.canJoinAllSpaces` floating panel out of full-screen Spaces** — it
  gatecrashes anyway. The only working fix is active self-suppression: watch
  Space changes, detect a covering full-screen window via CGWindowList
  geometry, and `orderOut` yourself.
- **`NSWorkspace.activeSpaceDidChangeNotification` fires mid-transition** —
  CGWindowList still shows the departing Space's windows at notification time.
  Treat the notification as a trigger to start converging, not a reliable read
  point: check immediately, re-check ~0.8s later, and poll slowly while in a
  suppressed state so recovery never depends on another notification.
- **A repeating `Timer(target: self)` retains its target until invalidated** —
  a poll timer started only in a rare state is easy to miss in tear-down and
  leaks the controller.
- **Global hotkeys**: Carbon `RegisterEventHotKey` (which KeyboardShortcuts
  wraps) works inside the App Sandbox with no extra permissions.
  `NSEvent.addGlobalMonitorForEvents` needs Input Monitoring — avoid it.
- **KeyboardShortcuts 1.10 under Swift 6**: static `KeyboardShortcuts.Name`
  constants trip strict concurrency (`Name` isn't `Sendable`); isolate them
  with `@MainActor` — both AppKit call sites and SwiftUI `body` are main-actor
  anyway.
- **A sprite atlas (or any repeatedly drawn image) re-decodes its PNG on
  every draw** — `kCGImageSourceShouldCache` / `ShouldCacheImmediately` do
  *not* make the decode stick: the CGImage stays backed by the compressed PNG
  provider and the decoded pixels live in an evictable system cache, so each
  redraw can trigger a full decode plus colour-match (`NSImage.cacheMode =
  .never` guarantees it). Diagnostic tell: CPU tracks the animation frame
  rate, and `/usr/bin/sample` shows `png_read_filter_row_paeth_neon` /
  `CGSImageDataLock` under `CALayer _display`. Fix: at load time, draw the
  image once into an owned `CGContext` (sRGB, premultiplied BGRA,
  `byteOrder32Little`) and keep `context.makeImage()` — nothing PNG-backed
  survives to draw time. Cost is width×height×4 bytes of resident memory.

## Out of scope (so far)

- iOS / iPadOS.
- App Store or notarised distribution — no project has shipped a public
  binary yet; add conventions when the first one does.
- Large document-based AppKit/SwiftUI apps.
