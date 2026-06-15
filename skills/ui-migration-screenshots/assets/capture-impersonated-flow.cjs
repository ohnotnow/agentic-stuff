// ---------------------------------------------------------------------------
// capture-impersonated-flow.cjs  —  capture a role-gated, multi-step journey
// by impersonating a user.
//
// Part of the `ui-migration-screenshots` skill. Many pages and whole flows only
// exist for a particular role (student, applicant, staff). If the app has an
// impersonation feature, an admin can step into that user and you can walk and
// screenshot their journey.
//
// Interactive flows are app-specific, so the FLOW section below is a *worked
// example* — a student expanding projects, ranking 1st-5th preferences, and
// submitting. Keep the structure (login -> impersonate -> walk states ->
// screenshot each), and replace the FLOW steps with the target app's journey.
// The reusable patterns are flagged with `PATTERN:` comments.
//
// Run from the app repo root:  node capture-impersonated-flow.cjs
// ---------------------------------------------------------------------------

const { chromium } = require('playwright');
const path = require('path');
const fs = require('fs');

const CONFIG = {
  base: 'https://your-app.lndo.site',
  outDir: path.resolve('screenshots/before/flow'),
  viewport: { width: 1440, height: 1000 },
  deviceScaleFactor: 2,
  ignoreHTTPSErrors: true,
  hideSelectors: ['.phpdebugbar', '.phpdebugbar-closed'],
  settleMs: 400,
};

// The user to impersonate (must already exist and have the role/eligibility you
// want to capture). Pick one whose data lets the whole flow complete.
const IMPERSONATE_USER_ID = 207;

const hideCss = CONFIG.hideSelectors.length
  ? `${CONFIG.hideSelectors.join(', ')} { display: none !important; }`
  : '';

// PATTERN: a screenshot helper that hides overlays and waits for late JS first.
const shot = async (page, name) => {
  if (hideCss) await page.addStyleTag({ content: hideCss }).catch(() => {});
  await page.waitForTimeout(CONFIG.settleMs);
  await page.screenshot({ path: path.join(CONFIG.outDir, `${name}.png`), fullPage: true });
  console.log(`  saved ${name}.png`);
};

// ADAPT: log in as an admin who is allowed to impersonate.
async function loginAsAdmin(page) {
  await page.goto(`${CONFIG.base}/login`, { waitUntil: 'domcontentloaded' });
  await page.waitForSelector('#username', { timeout: 15000 });
  await page.fill('#username', 'admin');
  await page.fill('#password', 'secret');
  await Promise.all([
    page.waitForURL((u) => !u.pathname.includes('/login'), { timeout: 20000 }),
    page.click('button:has-text("Login")'),
  ]);
}

(async () => {
  fs.mkdirSync(CONFIG.outDir, { recursive: true });
  const browser = await chromium.launch();
  const context = await browser.newContext({
    viewport: CONFIG.viewport,
    deviceScaleFactor: CONFIG.deviceScaleFactor,
    ignoreHTTPSErrors: CONFIG.ignoreHTTPSErrors,
  });
  const page = await context.newPage();

  console.log('Logging in as admin...');
  await loginAsAdmin(page);

  // --- Trigger impersonation through the real UI ---------------------------
  // ADAPT: navigate to wherever the impersonate control lives and click it.
  // Here it's an "Impersonate" item inside a hover dropdown on the user page.
  console.log(`Impersonating user ${IMPERSONATE_USER_ID}...`);
  await page.goto(`${CONFIG.base}/admin/user/${IMPERSONATE_USER_ID}`, { waitUntil: 'domcontentloaded' });
  await page.waitForLoadState('networkidle', { timeout: 6000 }).catch(() => {});
  // PATTERN: reveal a hover/CSS dropdown before clicking an item inside it.
  await page.hover('.dropdown-trigger');
  await page.waitForSelector('#dropdown-menu', { state: 'visible', timeout: 5000 }).catch(() => {});
  await shot(page, '01-impersonate-action');
  // PATTERN: a click that causes a server redirect (Livewire/form) — wait for
  // the URL to change rather than guessing a timeout.
  await Promise.all([
    page.waitForURL((u) => u.pathname === '/', { timeout: 20000 }),
    page.click('a:has-text("Impersonate")'),
  ]);
  await page.waitForLoadState('networkidle', { timeout: 8000 }).catch(() => {});

  // =========================================================================
  // FLOW (worked example — replace with the target app's journey)
  // Student dashboard -> expand a project -> rank preferences -> submit.
  // =========================================================================

  // PATTERN: wait for the dynamic component to mount, then derive element ids
  // from the DOM instead of hard-coding them — more robust to data changes.
  // NB: page.$$eval is Playwright's "query-all + map over matched DOM nodes"
  // helper — it is NOT JavaScript's eval() and runs no arbitrary code.
  await page.waitForSelector('[id^="expand-"]', { timeout: 15000 });
  const projectIds = await page.$$eval('[id^="expand-"]', (els) =>
    els.map((e) => Number(e.id.replace('expand-', ''))));
  console.log('Items on the page:', projectIds.join(', '));
  await shot(page, '02-home');

  const chosen = projectIds.slice(0, 5);
  const PREFS = ['first', 'second', 'third', 'fourth', 'fifth'];

  // Expand the first item to reveal its detail + action buttons.
  await page.click(`#expand-${chosen[0]}`);
  await page.waitForTimeout(400);
  await shot(page, '03-expanded');

  // Make a couple of selections, then capture the in-progress state.
  await page.click(`#project-${chosen[0]}-${PREFS[0]}`);
  await page.click(`#expand-${chosen[1]}`);
  await page.waitForTimeout(200);
  await page.click(`#project-${chosen[1]}-${PREFS[1]}`);
  await page.waitForTimeout(300);
  await shot(page, '04-partial');

  // Complete the rest, then capture the ready-to-submit state.
  for (let i = 2; i < 5; i++) {
    await page.click(`#expand-${chosen[i]}`);
    await page.waitForTimeout(150);
    await page.click(`#project-${chosen[i]}-${PREFS[i]}`);
  }
  await page.waitForTimeout(400);
  await shot(page, '05-ready-to-submit');

  // SIDE EFFECT: submitting writes to the database. It's usually local test
  // data and reversible, but tell the user what it wrote.
  console.log('Submitting...');
  await Promise.all([
    page.waitForURL((u) => u.pathname.includes('thank-you'), { timeout: 20000 }),
    page.click('button:has-text("Submit my choices")'),
  ]);
  await page.waitForLoadState('networkidle', { timeout: 8000 }).catch(() => {});
  await shot(page, '06-thank-you');

  // The post-submission state often differs (saved choices now shown).
  await page.goto(`${CONFIG.base}/`, { waitUntil: 'domcontentloaded' });
  await page.waitForLoadState('networkidle', { timeout: 6000 }).catch(() => {});
  await shot(page, '07-home-after-submit');

  await browser.close();
  console.log(`\n=== Flow captured -> ${CONFIG.outDir} ===`);
})().catch((e) => {
  console.error('FATAL', e);
  process.exit(1);
});
