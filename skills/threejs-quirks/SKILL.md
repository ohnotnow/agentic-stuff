---
name: threejs-quirks
description: >
  Hard-won three.js and WebGL failure modes, verified in real sessions:
  shaders quietly recompiling, one NaN pixel blacking out a bloomed screen,
  colours converted twice, shader errors hiding from the console, and GPU
  timings that lie. Load it whenever you build, debug or tune a three.js
  scene: before trusting a frame time or a colour, and whenever one machine
  stutters where another doesn't.
allowed-tools: "Read,Bash,Glob,Grep"
version: "0.1.0"
author: "ohnotnow <https://github.com/ohnotnow>"
license: "MIT"
---

# three.js quirks

Field notes for three.js work, in the same spirit as playwright-cli-quirks:
every rake below was hit and verified in a real session, and each is stamped
with the three.js version and the date it was verified on. If you are on a
much newer three.js, re-verify a rake before relying on it, and delete any
that upstream has fixed.

## Shaders that recompile behind your back

- **Disposing the last material that uses a shader deletes the compiled
  program, and the next material that needs it compiles it from scratch.**
  three.js shares one compiled program between materials with the same
  settings and counts its users; `releaseProgram` in `WebGLPrograms` deletes
  it when the count reaches zero. At a program's first use three.js reads its
  link status and uniforms, which waits for the compile, so the compile lands
  in that frame. Anything made and thrown away often with its own materials
  (bubbles, shots, particles, a `ShaderMaterial` each for per-object
  uniforms) recompiles its shader whenever none are left and a new one is
  made. Found chasing a split-second freeze reported on an M1 when shooting
  at close-range targets in a game: a bubble that hit something popped within
  a fifth of a second and its materials were disposed, so the next shot
  recompiled the shader; bubbles that missed lived three seconds, so rapid
  fire into the air never did. Fix: keep those materials until the level or
  scene is torn down, instead of disposing them one by one. Per-object
  materials are fine if something long-lived uses the same settings: a parcel
  per enemy with its own `MeshStandardMaterial({ map })` never recompiled,
  because a kept material with the same settings held the program.
  (Verified three.js 0.186.1, Chrome 154 on an Apple M6, 2026-10-19.)
- **Count compiles; don't time frames.** On the M6 each of those recompiles
  cost a few milliseconds and no frame went over 25 ms, so frame timing on a
  fast machine hides the problem entirely. Wrap
  `WebGL2RenderingContext.prototype.linkProgram` in an init script (Playwright's
  `page.addInitScript`) to log each call, and watch
  `renderer.info.programs.length` while repeating the action: after the first
  time nothing should be linked, and the count shouldn't drop and climb back.
  (Verified as above.)

## One NaN pixel, and bloom

- **A NaN pixel plus bloom blacks out huge areas of the screen.** GLSL's
  `pow(x, y)` is undefined for `x < 0`, and here it gave NaN; a base that
  should never be negative but dips a hair below zero through rounding, such
  as `pow(0.5 - 0.5 * cos(a), 1.3)`, is enough. Bloom then spreads that one
  pixel into big black blocks: blowing the first soap bubble in a scene
  blacked out half the screen. Clamp `pow()` bases at zero
  (`pow(max(b, 0.0), e)`). Dropping NaN and infinity in the first bloom pass
  and in the final pass is a useful backstop, but don't lean on it.
  (Verified three.js 0.186.1, 2026-10-16.)

## Colours made too early

- **Top-level code in imported modules runs before the entry script's body,
  so a three.js setting the entry script changes hasn't happened yet.** An
  entry script that sets `THREE.ColorManagement.enabled = false` (to handle
  sRGB itself) does so only after every module it imports has run its top
  level. A colour built at a module's top level with
  `new THREE.Color(hex).convertSRGBToLinear()` is then converted twice (once
  by `THREE.Color`, which turns sRGB hex into linear while colour management
  is still on, and once by hand) and comes out far too dark. Build such
  colours inside functions that run after start-up. (Verified three.js
  0.186.1, 2026-10-16.)

## Shader errors you can't see

- **When a shader fails to compile, read the compiler's message from
  `renderer.info.programs`.** Each program there has
  `diagnostics.fragmentShader.log` and `diagnostics.vertexShader.log`, filled
  in only while `renderer.debug.checkShaderErrors` is on (the default). In one
  project, driven headless through playwright-cli, the console showed only
  repeated `useProgram: program not valid` warnings and never three.js's own
  `THREE.WebGLProgram: Shader Error`. Why was never established; three.js
  0.186 sends that error through its own logger, which
  `THREE.setConsoleFunction` can redirect. (Verified three.js 0.186.1,
  2026-10-16.)

## Timing the GPU

- **Time GPU work with timer queries, not `performance.now()` around
  `gl.finish()`.** In headless Chrome on macOS (ANGLE on Metal), `gl.finish()`
  didn't wait for the GPU, so wall-clock timing around it measured nothing
  useful. `EXT_disjoint_timer_query_webgl2` gave real numbers: moving a 7 x 7
  glow out of a full-screen pass and into the low-resolution picture before
  it was enlarged cut GPU time per frame from 11.5 ms to 3.4 ms at 4K on an
  M6. (Verified three.js 0.186.1, headless Chrome on an Apple M6,
  2026-10-12.)
- **Check which GPU you're on before timing anything.** A headless browser can
  quietly render WebGL in software (SwiftShader), where every timing is
  meaningless; read
  `gl.getParameter(gl.getExtension('WEBGL_debug_renderer_info').UNMASKED_RENDERER_WEBGL)`
  first. playwright-cli-quirks has one way this happens without warning.
  (Verified 2026-10-19.)
