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
  after a rebuild re-prompts. Expected, not a bug. Privacy (TCC) grants such
  as Apple Music access are tied to the signature the same way. For people
  who just want to run the app, give the Makefile a `make install` that
  builds once, `ditto`s the bundle into `/Applications` and opens it; that
  copy keeps its grant when quit and reopened (verified in Streamer; not yet
  checked across a reboot or after a plain rebuild). A
  stable `SIGN` certificate in an untracked `local.mk` is the fix for
  developers who rebuild often.
- A TCC usage string is not optional decoration: without it macOS may refuse
  **silently, with no prompt at all**. See the Streamer gotchas for how to get
  the real reason out of `tccd`.

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

Mostly from Naiku (`https://github.com/ohnotnow/naiku`), macOS 26 / Xcode 26.1.1,
plus blether and Streamer where marked. Symptom → fix.

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
  geometry, and `orderOut` yourself. Geometry test that works for "fullscreen
  window": full display width, bottom at display bottom, top within ~40pt of
  display top (the tolerance covers notched MacBooks, where fullscreen content
  sits below the camera housing). Known accepted limitation: a maximised
  window with the Dock auto-hidden is geometrically indistinguishable from
  notched fullscreen.
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
- **swift-frontend crashes in IRGen (`report_at_maximum_capacity` inside a
  reabstraction thunk) when a `@MainActor` view method is passed directly as
  a `Binding` setter**, e.g. `Binding(get: { id }, set: select)`. Wrapping it
  in a closure, `set: { select($0) }`, builds fine. Seen in blether
  (`Settings/VoicesSection.swift`, the Profile picker) on Xcode 26.1.1 with
  strict concurrency on. A compiler crash with no diagnostic; if the build
  dies in IRGen, look for a bare method reference handed to a `Binding`.
- **`MainActor.assumeIsolated` inside a closure that a background task calls
  crashes at runtime with SIGTRAP** in `dispatch_assert_queue_fail` under
  `_swift_task_checkIsolatedSwift`; no diagnostic at compile time. The
  temptation: a `@MainActor @Observable` settings object holds a value (an
  API key) and a `Sendable` service needs it at call time, so you wrap the
  read in `assumeIsolated` and reason that "every caller starts from the main
  actor". They do not: a nonisolated `async` method on a `Sendable` type hops
  to the global executor the moment it is awaited, even from a SwiftUI
  `.task`. Fix: give the settings object a `nonisolated` reader over the
  thread-safe store underneath (Keychain, a `Mutex`) and hand *that* closure
  to the service, or pass the value into the snapshot on the main actor
  before the hop. Seen in blether (`AppSettings.apiKeyReader(for:)`), macOS
  26.6 / Xcode 26.1.1. A `Task.detached { read() }` in a test catches it.

### From Streamer

Streamer (`https://github.com/ohnotnow/streamer`), a menubar app that serves
a playlist as an AAC stream. macOS 27, Swift 6.4, strict concurrency.

- **`AVAssetReader`'s classic calls are deprecated on macOS 27** (`add`,
  `startReading`, `copyNextSampleBuffer`). The replacement, available since
  macOS 26, is `reader.outputProvider(for: output)` (returns
  `AVAssetReaderOutput.Provider<CMReadySampleBuffer<CMSampleBuffer.DynamicContent>>`),
  `try reader.start()`, and `try await provider.next()`, which is **async**
  and returns nil at the end of the track. Get PCM out with
  `sample.withUnsafeSampleBuffer { CMSampleBufferCopyPCMDataIntoAudioBufferList(...) }`.
  Also use `loadTracks(withMediaType:)`, not `tracks(withMediaType:)`.
- **Swift-only APIs are not in the Objective-C headers.** When a deprecation
  names a replacement you cannot find, search the SDK's Swift interfaces:
  `rg -n 'outputProvider' "$(xcrun --show-sdk-path)/usr/lib/swift/AVFoundation.swiftmodule/arm64e-apple-macos.swiftinterface"`.
  CoreMedia's lives under
  `System/Library/Frameworks/CoreMedia.framework/Versions/A/Modules/CoreMedia.swiftmodule/`.
- **An async decoder cannot feed `AVAudioConverter` directly**: the
  converter's `convert(to:error:withInputFrom:)` input block is synchronous.
  Queue decoded PCM buffers and let the block pull from the queue. When the
  queue is momentarily empty, set the status to `.noDataNow` and return nil,
  **never `.endOfStream`**, which flushes the encoder and leaves a gap. Keep
  one converter for the whole run and track changes are gapless. Verified by
  a test that encodes a tone split across a dry spell, decodes the AAC back,
  and checks for silent runs; injecting a real 1024-sample gap made that test
  fail, so it does detect gaps.
- **"sending 'x' risks causing data races"** when a `@MainActor` type owns a
  non-Sendable helper and awaits its async method: in Swift 6 mode a
  nonisolated async method runs off the actor, so calling it sends the helper
  away. Mark the helper's async `init` and methods `nonisolated(nonsending)`
  so they run on the caller's actor (Apple's own `Provider.next()` is
  declared this way).
- **Wrapping an `NWListener`'s readiness in a continuation**: capturing a
  local `settle` function in the listener's handlers fails strict
  concurrency ("concurrently-executed local function must be marked as
  '@Sendable'"). Store the `CheckedContinuation` as a property on the
  `@MainActor` server, start the listener on `.main`, and resume it from
  handlers wrapped in `MainActor.assumeIsolated`. That is safe here because
  the handlers really do run on the main queue (contrast the `assumeIsolated`
  crash above, where they did not). Blether's `HookServer` waits on a
  semaphore instead, which only works because its listener has its own
  queue; on the main queue that wait would deadlock (reasoned, not seen).
- **Music library access fails with NSCocoaError 4097 "connection to service
  named com.apple.amp.library.framework" and no prompt ever appears** →
  Info.plist lacks `NSAppleMusicUsageDescription`. Hardened runtime needs no
  entitlement for it. The reason is only in the privacy daemon's log:
  `log show --last 5m --predicate '(process == "tccd" OR sender == "TCC") AND eventMessage CONTAINS[c] "<app name>"'`,
  which said "Refusing authorization request for service
  kTCCServiceMediaLibrary ... without NSAppleMusicUsageDescription". Try that
  log first for any silent permission failure.
- **Loading data into a `@State` model from `App.init` loses it**: reading a
  `@State` property in `init` can hand back a temporary instance, so the data
  lands in an object the view never uses, with no error. Do the work in the
  property's initialiser instead:
  `@State private var model: AppModel = { let m = AppModel(); m.load(); return m }()`.
- **iTunesLibrary in Swift**: distinguished playlist kinds are spelt
  `.kindMovies`, `.kindPodcasts` and so on; `isPrimary` (the top-level
  Library playlist) replaces the deprecated `isMaster`.
- **A free-form app icon gets a grey rounded-square frame on macOS 26 and
  later.** A transparent PNG of an arbitrary shape is shown inside a grey
  plate. Fix: composite the artwork onto your own rounded square on Apple's
  grid (an 824-point square inset 100 in a 1024 canvas, corner radius about
  185), then generate the ten `mac` sizes (16 to 512, at 1x and 2x) with
  `sips -z` into `Assets.xcassets/AppIcon.appiconset` and set
  `ASSETCATALOG_COMPILER_APPICON_NAME: AppIcon` in `project.yml`. The
  `mac-app-icon` skill does all of this with a tested script; use it rather
  than re-deriving the ImageMagick commands. Icon Composer would not open a
  plain PNG for the user.

## Out of scope (so far)

- iOS / iPadOS.
- App Store or notarised distribution — no project has shipped a public
  binary yet; add conventions when the first one does.
- Large document-based AppKit/SwiftUI apps.
