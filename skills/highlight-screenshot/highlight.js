// Draws a ring and a label round one element, then takes a viewport screenshot.
// Run with: playwright-cli -s=highlight run-code --filename=<absolute path to your copy>
async page => {
  // --- edit these three ---
  const target = page.getByRole('button', { name: 'Copy next', disabled: true }).first();
  const label = 'This one: Copy next, Monday 5th';
  const out = '/absolute/path/to/app/screenshots/copy-next-2026-09-28.png'; // relative paths resolve against the daemon, not the project

  await target.evaluate(n => n.scrollIntoView({ block: 'center' }));
  await target.evaluate((node, label) => {
    document.querySelectorAll('[data-pointer]').forEach(e => e.remove());
    // The ring is its own element, not an outline on the target: a disabled
    // button's opacity would fade an outline drawn on it.
    const r = node.getBoundingClientRect(), pad = 6, colour = '#e4003b';
    const ring = document.createElement('div');
    const tag = document.createElement('div');
    ring.dataset.pointer = tag.dataset.pointer = '';
    Object.assign(ring.style, { position: 'fixed', left: r.left - pad + 'px', top: r.top - pad + 'px',
      width: r.width + pad * 2 + 'px', height: r.height + pad * 2 + 'px', border: '4px solid ' + colour,
      borderRadius: '8px', boxSizing: 'border-box', zIndex: 2147483647, pointerEvents: 'none' });
    tag.textContent = label;
    Object.assign(tag.style, { position: 'fixed', background: colour, color: '#fff',
      font: '600 16px system-ui, sans-serif', padding: '6px 10px', borderRadius: '6px', maxWidth: '360px',
      zIndex: 2147483647, pointerEvents: 'none' });
    document.body.append(ring, tag);
    // Above the ring if there is room, else below; right edges aligned so it stays on screen.
    const t = tag.getBoundingClientRect();
    const above = r.top - pad - t.height - 8;
    tag.style.top = (above > 8 ? above : r.bottom + pad + 8) + 'px';
    tag.style.left = Math.max(8, Math.min(r.right + pad - t.width, innerWidth - t.width - 8)) + 'px';
  }, label);
  await page.screenshot({ path: out });
  return out;
}
