const http = require('http');
const fs = require('fs');

const port = process.env.PORT || 10000;
const BASE_URL = process.env.BASE_URL || 'https://monopoly-command-center-v67.floot.app/_cdn/static/f4ebb851-c03c-451c-81c5-343be9983db0-command-center-v67-all3-currentmodel.txt';

const gameDetailUiPatch = fs.readFileSync('game-detail-ui-patch.html', 'utf8');
const mobilePatch = fs.readFileSync('mobile-patch.html', 'utf8');
const mobileNavFix = fs.readFileSync('mobile-nav-fix.html', 'utf8');
const saturdayPatch = fs.readFileSync('week4-saturday-integration-patch.html', 'utf8');
const current = JSON.parse(fs.readFileSync('week4-current-data.json', 'utf8'));

let cachedHtml = null;
let loadError = null;

function replaceConstArray(html, name, value) {
  const needle = `const ${name}=`;
  const decl = html.indexOf(needle);
  if (decl < 0) throw new Error(`Unable to locate native ${name} declaration`);
  const start = html.indexOf('[', decl + needle.length);
  if (start < 0) throw new Error(`Unable to locate ${name} array start`);

  let depth = 0;
  let quote = null;
  let escaped = false;
  let end = -1;
  for (let i = start; i < html.length; i++) {
    const ch = html[i];
    if (quote) {
      if (escaped) escaped = false;
      else if (ch === '\\') escaped = true;
      else if (ch === quote) quote = null;
      continue;
    }
    if (ch === '"' || ch === "'" || ch === '`') { quote = ch; continue; }
    if (ch === '[') depth++;
    else if (ch === ']') {
      depth--;
      if (depth === 0) { end = i + 1; break; }
    }
  }
  if (end < 0) throw new Error(`Unable to locate ${name} array end`);
  return html.slice(0, start) + JSON.stringify(value) + html.slice(end);
}

async function loadApp() {
  if (cachedHtml) return cachedHtml;
  const response = await fetch(BASE_URL, {redirect:'follow'});
  if (!response.ok) throw new Error(`Base app fetch failed: ${response.status} ${response.statusText}`);
  let base = await response.text();
  if (!base.includes('<html') && !base.includes('<!DOCTYPE')) throw new Error('Base app response is not HTML');

  base = replaceConstArray(base, 'games', current.games);
  base = replaceConstArray(base, 'sourceData', current.sourceData);

  const publicState = `<script id="week4-current-public-state">window.WEEK4_CURRENT_META=${JSON.stringify({version:current.version,captured_at_local:current.captured_at_local,snapshot_label:current.snapshot_label,balances:current.balances,working_portfolio:current.working_portfolio})};window.WEEK4_CURRENT_PUBLIC=${JSON.stringify(current.games)};window.WEEK4_SOURCE_PUBLIC=${JSON.stringify(current.sourceData)};</script>`;
  const combinedPatch = `${publicState}\n${gameDetailUiPatch}\n${mobilePatch}\n${mobileNavFix}\n${saturdayPatch}`;
  cachedHtml = base.includes('</body>') ? base.replace('</body>', `${combinedPatch}\n</body>`) : `${base}\n${combinedPatch}`;
  return cachedHtml;
}

const server = http.createServer(async (req, res) => {
  if (req.url === '/_version') {
    res.writeHead(200, {'content-type':'application/json; charset=utf-8','cache-control':'no-store'});
    return res.end(JSON.stringify({
      status:'ok',
      version:current.version,
      captured_at_local:current.captured_at_local,
      top_board:current.games.slice(0,6).map(g=>({rank:g.rank,game:g.game,lean:g.lean,decision:g.decision,current:g.current,sly:g.sly,catherine:g.catherine,amanda:g.amanda})),
      working_portfolio:current.working_portfolio
    }));
  }
  if (req.url === '/healthz') {
    try {
      const html = await loadApp();
      const checks = {
        week4DataInjected: html.includes('DEN @ SF') && html.includes('LAC @ SEA') && !html.includes('const games=[{"rank":2,"game":"NYJ @ DET"'),
        sourceDataInjected: html.includes('2 verified signals support SEA'),
        saturdayPatch: html.includes('week4-saturday-layer')
      };
      const ok = Object.values(checks).every(Boolean);
      res.writeHead(ok ? 200 : 503, {'content-type':'application/json; charset=utf-8','cache-control':'no-store'});
      return res.end(JSON.stringify({status:ok?'ok':'error',version:current.version,bytes:Buffer.byteLength(html),checks}));
    } catch (err) {
      loadError = String(err && err.message ? err.message : err);
      res.writeHead(503, {'content-type':'application/json; charset=utf-8'});
      return res.end(JSON.stringify({status:'error',error:loadError}));
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
    console.log(`Loaded ${current.version}: ${Buffer.byteLength(html)} bytes; Saturday Week 4 native arrays injected`);
    console.log(`Saturday top board: ${current.games.slice(0,6).map(g=>`${g.rank}:${g.lean}`).join(' | ')}`);
  } catch (err) {
    console.error('Initial canonical app load failed:', err);
  }
});
