// Renders index.html with headless Chromium and writes the composited PNG.
// Usage: node render.cjs [output.png]   (needs playwright resolvable, e.g. via NODE_PATH)
const { chromium } = require('playwright');
const { writeFileSync } = require('node:fs');
const { resolve } = require('node:path');

(async () => {
  const outPath = resolve(process.argv[2] || resolve(__dirname, 'carta-senna-livery.png'));
  const browser = await chromium.launch({ args: ['--allow-file-access-from-files'] });
  const page = await browser.newPage();
  page.on('console', (m) => console.log('[page]', m.text()));
  await page.goto('file://' + resolve(__dirname, 'index.html'));
  await page.evaluate(() => document.fonts.ready);
  const dataUrl = await page.evaluate(() => window.renderLivery());
  writeFileSync(outPath, Buffer.from(dataUrl.split(',')[1], 'base64'));
  if (process.argv.includes('--transparent')) {
    const tPath = outPath.replace(/\.png$/, '-transparent.png');
    const t = await page.evaluate(() => window.renderLivery({ transparent: true }));
    writeFileSync(tPath, Buffer.from(t.split(',')[1], 'base64'));
    console.log('wrote', tPath);
    const mPath = outPath.replace(/\.png$/, '-transparent-mirror.png');
    const m = await page.evaluate(() => window.renderLivery({ transparent: true, mirrorText: true }));
    writeFileSync(mPath, Buffer.from(m.split(',')[1], 'base64'));
    console.log('wrote', mPath);
  }
  await browser.close();
  console.log('wrote', outPath);
})().catch((e) => { console.error(e); process.exit(1); });
