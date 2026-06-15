// ---------------------------------------------------------------------------
// capture-pages.cjs  —  bulk full-page screenshots of an app's pages.
//
// Part of the `ui-migration-screenshots` skill. Copy this into the target app
// repo (or run it from there) and adapt the three marked sections:
//   1. CONFIG          — base URL, output dir, viewport, overlays to hide
//   2. login(page)     — how to authenticate (selectors / credentials)
//   3. pages           — the list of [name, url] to capture
//
// Setup (ask the user / get permission for the install):
//   npm install --no-save playwright
//   npx playwright install chromium
//
// Run from the app repo root:
//   node capture-pages.cjs
// ---------------------------------------------------------------------------

const { chromium } = require('playwright');
const path = require('path');
const fs = require('fs');

// --- 1. CONFIG -------------------------------------------------------------
const CONFIG = {
  base: 'https://your-app.lndo.site',            // no trailing slash
  outDir: path.resolve('screenshots/before'),    // relative to where you run node
  viewport: { width: 1440, height: 1000 },        // a typical desktop width
  deviceScaleFactor: 2,                            // 2 = crisp/retina text
  ignoreHTTPSErrors: true,                         // local certs (lndo.site etc.)
  // CSS selectors for chrome that isn't part of the real UI and should be
  // hidden before each shot. The Laravel debugbar re-injects on every page
  // load, so hiding it per-navigation (which this script does) is required.
  hideSelectors: ['.phpdebugbar', '.phpdebugbar-closed'],
  settleMs: 400,                                   // pause for late-rendering JS
};

// --- 2. login --------------------------------------------------------------
// A fresh browser has no session, so authenticate here. ADAPT to the app:
// different field selectors, a different submit button, or remove entirely if
// the pages are public. If the app is SSO-only you usually cannot script this —
// see references/gotchas.md for options.
async function login(page) {
  await page.goto(`${CONFIG.base}/login`, { waitUntil: 'domcontentloaded' });
  await page.waitForSelector('#username', { timeout: 15000 });
  await page.fill('#username', 'admin');
  await page.fill('#password', 'secret');
  await Promise.all([
    page.waitForURL((u) => !u.pathname.includes('/login'), { timeout: 20000 }),
    page.click('button:has-text("Login")'),
  ]);
  if (page.url().includes('/login')) {
    throw new Error('Login failed — still on /login');
  }
}

// --- 3. pages --------------------------------------------------------------
// [filename, url path]. The filename becomes <name>.png. Use the route name so
// the files are self-documenting. Detail/edit pages need ids that exist in the
// browser's context (see the scoping gotcha). Skip exports/downloads, JSON
// APIs, auth/redirect/toggle routes, and any test route that throws or sends
// real notifications.
const pages = [
  ['home',              '/'],
  ['users.index',       '/admin/users'],
  ['user.show',         '/admin/user/1'],
  ['user.edit',         '/admin/user/1/edit'],
  // ...add the rest of the route list here...
];

// ---------------------------------------------------------------------------
// Engine — you normally don't need to touch below here.
// ---------------------------------------------------------------------------
const hideCss = CONFIG.hideSelectors.length
  ? `${CONFIG.hideSelectors.join(', ')} { display: none !important; }`
  : '';

(async () => {
  fs.mkdirSync(CONFIG.outDir, { recursive: true });
  const browser = await chromium.launch();
  const context = await browser.newContext({
    viewport: CONFIG.viewport,
    deviceScaleFactor: CONFIG.deviceScaleFactor,
    ignoreHTTPSErrors: CONFIG.ignoreHTTPSErrors,
  });
  const page = await context.newPage();

  console.log('Logging in...');
  await login(page);
  console.log('Logged in, landed on', page.url(), '\n');

  const results = [];
  for (const [name, url] of pages) {
    let status = '?';
    try {
      const resp = await page.goto(`${CONFIG.base}${url}`, {
        waitUntil: 'domcontentloaded',
        timeout: 30000,
      });
      status = resp ? resp.status() : 'no-response';
      // allow async (SPA/Livewire/Vue) content to settle, but never hang on it
      await page.waitForLoadState('networkidle', { timeout: 6000 }).catch(() => {});
      if (hideCss) await page.addStyleTag({ content: hideCss }).catch(() => {});
      await page.waitForTimeout(CONFIG.settleMs);
      await page.screenshot({ path: path.join(CONFIG.outDir, `${name}.png`), fullPage: true });
      const flag = typeof status === 'number' && status >= 400 ? '  <-- non-2xx' : '';
      console.log(`OK  ${status}  ${name.padEnd(34)} ${url}${flag}`);
      results.push({ name, url, status, ok: true });
    } catch (e) {
      const msg = String(e.message).split('\n')[0];
      console.log(`ERR ${status}  ${name.padEnd(34)} ${url}  ${msg}`);
      // capture whatever rendered anyway — an error page is still informative
      try {
        await page.screenshot({ path: path.join(CONFIG.outDir, `${name}.png`), fullPage: true });
      } catch {}
      results.push({ name, url, status, ok: false, error: msg });
    }
  }

  await browser.close();

  const issues = results.filter((r) => !r.ok || (typeof r.status === 'number' && r.status >= 400));
  console.log(`\n=== Captured ${results.length} pages -> ${CONFIG.outDir} ===`);
  if (issues.length) {
    console.log(`${issues.length} page(s) need a look (wrong id = 404, pre-existing breakage = 500):`);
    issues.forEach((r) => console.log(`  - ${r.name} [${r.status}] ${r.error || ''}`));
  } else {
    console.log('No errors or non-2xx responses.');
  }
})().catch((e) => {
  console.error('FATAL', e);
  process.exit(1);
});
