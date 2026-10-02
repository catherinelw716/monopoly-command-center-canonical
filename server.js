const http = require('http');
const fs = require('fs');

const port = process.env.PORT || 10000;
const BASE_URL = process.env.BASE_URL || 'https://monopoly-command-center-v67.floot.app/_cdn/static/f4ebb851-c03c-451c-81c5-343be9983db0-command-center-v67-all3-currentmodel.txt';
const patch = fs.readFileSync('canonical-patch.html', 'utf8');
const lucasTablePatch = fs.readFileSync('lucas-table-patch.html', 'utf8');
const sourceScreenshotPatch = fs.readFileSync('source-screenshot-data-patch.html', 'utf8');
const gameDetailUiPatch = fs.readFileSync('game-detail-ui-patch.html', 'utf8');
const consistencyPatch = fs.readFileSync('consistency-patch.html', 'utf8');
const mobilePatch = fs.readFileSync('mobile-patch.html', 'utf8');
const mobileNavFix = fs.readFileSync('mobile-nav-fix.html', 'utf8');
const wagerSizingPatch = fs.readFileSync('wager-sizing-patch.html', 'utf8');
const consensusModelFix = fs.readFileSync('consensus-model-fix.html', 'utf8');
const week4DataRefreshPatch = fs.readFileSync('week4-data-refresh-patch.html', 'utf8');
let cachedHtml = null;
let loadError = null;
let diagnosticsLogged = false;

function logBaseDiagnostics(base) {
  if (diagnosticsLogged) return;
  diagnosticsLogged = true;
  const needles = ['const games', 'function gameRowHTML', 'function playCardHTML', 'function renderBoards', 'function renderGame', 'function pane', 'gamePanes', 'const sourceData', 'function renderSourceComparison', 'sourceCompareBody', 'id="games"', 'id="portfolio"', 'id="lab"'];
  for (const needle of needles) {
    const i = base.indexOf(needle);
    if (i >= 0) {
      const snippet = base.slice(Math.max(0, i - 250), Math.min(base.length, i + 3500)).replace(/\s+/g, ' ');
      console.log(`[BASE_DIAG2:${needle}] ${snippet}`);
    } else {
      console.log(`[BASE_DIAG2:${needle}] NOT_FOUND`);
    }
  }
}

async function loadApp() {
  if (cachedHtml) return cachedHtml;
  const response = await fetch(BASE_URL, { redirect: 'follow' });
  if (!response.ok) throw new Error(`Base app fetch failed: ${response.status} ${response.statusText}`);
  const base = await response.text();
  if (!base.includes('<html') && !base.includes('<!DOCTYPE')) throw new Error('Base app response is not HTML');
  logBaseDiagnostics(base);

  const combinedPatch = `${patch}\n${lucasTablePatch}\n${sourceScreenshotPatch}\n${gameDetailUiPatch}\n${consistencyPatch}\n${mobilePatch}\n${mobileNavFix}\n${wagerSizingPatch}\n${consensusModelFix}\n${week4DataRefreshPatch}`;
  cachedHtml = base.includes('</body>') ? base.replace('</body>', `${combinedPatch}\n</body>`) : `${base}\n${combinedPatch}`;
  return cachedHtml;
}

const server = http.createServer(async (req, res) => {
  if (req.url === '/healthz') {
    try {
      const html = await loadApp();
      res.writeHead(200, {'content-type':'application/json; charset=utf-8'});
      return res.end(JSON.stringify({status:'ok', bytes:Buffer.byteLength(html), source:'canonical-week4-existing-ux-data-refresh-diag2'}));
    } catch (err) {
      loadError = String(err && err.message ? err.message : err);
      res.writeHead(503, {'content-type':'application/json; charset=utf-8'});
      return res.end(JSON.stringify({status:'error', error:loadError}));
    }
  }
  try {
    const html = await loadApp();
    res.writeHead(200, {'content-type':'text/html; charset=utf-8','cache-control':'no-store, max-age=0'});
    res.end(html);
  } catch (err) {
    loadError = String(err && err.message ? err.message : err);
    res.writeHead(503, {'content-type':'text/plain; charset=utf-8'});
    res.end(`Command Center failed to load: ${loadError}`);
  }
});

server.listen(port, '0.0.0.0', async () => {
  console.log(`Command Center listening on ${port}`);
  try {
    const html = await loadApp();
    console.log(`Canonical app loaded: ${Buffer.byteLength(html)} bytes; Week 4 data refresh uses existing UX components`);
  } catch (err) {
    console.error('Initial canonical app load failed:', err);
  }
});