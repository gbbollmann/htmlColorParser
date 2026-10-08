// Serves this folder over HTTP and screenshots the showroom from a few angles with headless Chromium.
// Usage: NODE_PATH=<node_modules with playwright> node screenshot.cjs <outdir>
const { chromium } = require('playwright');
const http = require('node:http'); const fs = require('node:fs'); const path = require('node:path');
const root = __dirname; const outDir = path.resolve(process.argv[2] || root);
const types = { '.html': 'text/html', '.js': 'text/javascript', '.json': 'application/json', '.jpg': 'image/jpeg', '.png': 'image/png' };
const server = http.createServer((req, res) => {
  const p = path.join(root, decodeURIComponent(req.url.split('?')[0]).replace(/\/$/, '/index.html'));
  if (!p.startsWith(root) || !fs.existsSync(p)) { res.writeHead(404); return res.end(); }
  res.writeHead(200, { 'content-type': types[path.extname(p)] || 'application/octet-stream' }); fs.createReadStream(p).pipe(res);
});
(async () => {
  await new Promise(r => server.listen(0, '127.0.0.1', r));
  const port = server.address().port;
  const browser = await chromium.launch({ args: ['--use-gl=angle', '--use-angle=swiftshader', '--enable-unsafe-swiftshader', '--ignore-gpu-blocklist'] });
  const page = await browser.newPage({ viewport: { width: 1400, height: 800 } });
  page.on('console', m => console.log('[page]', m.type(), m.text()));
  page.on('pageerror', e => console.log('[pageerror]', e.message));
  await page.goto(`http://127.0.0.1:${port}/index.html`);
  await page.waitForFunction(() => window.__ready === true, null, { timeout: 60000 });
  const shots = { side: [Math.PI / 2, 1.3, 44], front34: [Math.PI / 2 + 0.95, 1.12, 42], rear34: [Math.PI / 2 - 2.35, 1.12, 42], left: [-Math.PI / 2, 1.3, 44], top: [Math.PI / 2 + 0.35, 0.35, 46] };
  for (const [name, [theta, phi, dist]] of Object.entries(shots)) {
    await page.evaluate(([t, p, d]) => { const s = window.__showroom; s.setSpin(false); s.orbit.theta = t; s.orbit.phi = p; s.orbit.dist = d; s.render(); }, [theta, phi, dist]);
    await page.waitForTimeout(150);
    await page.screenshot({ path: path.join(outDir, `shot-${name}.png`) });
    console.log('shot', name);
  }
  await browser.close(); server.close();
})().catch(e => { console.error(e); process.exit(1); });
