const http = require('http');
const fs = require('fs');

const port = process.env.PORT || 10000;
const BASE_URL = process.env.BASE_URL || 'https://monopoly-command-center-v67.floot.app/_cdn/static/f4ebb851-c03c-451c-81c5-343be9983db0-command-center-v67-all3-currentmodel.txt';

const gameDetailUiPatch = fs.readFileSync('game-detail-ui-patch.html', 'utf8');
const mobilePatch = fs.readFileSync('mobile-patch.html', 'utf8');
const mobileNavFix = fs.readFileSync('mobile-nav-fix.html', 'utf8');
const saturdayPatch = fs.readFileSync('week4-saturday-integration-patch.html', 'utf8');
const current = JSON.parse(fs.readFileSync('week4-current-data.json', 'utf8'));

// Afternoon cross-check: keep the versioned research snapshot immutable, but normalize
// the displayed current-market field to the newest Action/CBS range where books differ.
current.version = 'week4-native-v4-2026-10-03-afternoon';
current.snapshot_label = 'Week 4 Saturday · Oct 3 · afternoon market cross-check';
const byGame = Object.fromEntries(current.games.map(g => [g.game, g]));
function patchGame(id, patch) { if (byGame[id]) Object.assign(byGame[id], patch); }
patchGame('DEN @ SF', {
  current:'DEN +2.5', diff:'+0.5',
  marketNote:'Action and the latest CBS Week 4 board both show SF -2.5 / DEN +2.5. Sly DEN +3 retains a half-point across key 3.',
  evidence:'Frozen V2: Sly DEN +3 versus a current DEN +2.5 reference produces about +2.76% net scoring edge. The afternoon Action/CBS cross-check both support the -2.5 market reference.'
});
patchGame('LAC @ SEA', {
  current:'SEA -7', diff:'0.0',
  marketNote:'Action and the latest CBS Week 4 board both show SEA -7. No Sly price edge; the case rests on independent football-model support.'
});
patchGame('ARI @ NYG', {
  current:'NYG +2.5', diff:'0.0', role:'SportsLine-supported secondary',
  marketNote:'Action and the latest CBS/SportsLine board show ARI -2.5 / NYG +2.5, equal to Sly. SportsLine independently backs the Giants side.',
  evidence:'The afternoon line is market-equal to Sly NYG +2.5. The reason to retain the Giants is independent SportsLine matchup support, not stale-line value.',
  why:'SportsLine publicly backs NYG +2.5, while the current afternoon market has converged to the same number. This is now a football-model play rather than a price-value play.',
  against:'There is no current Sly-vs-market price edge, and Jameis Winston is starting with Jaxson Dart on injured reserve.',
  verdict:'Secondary only; keep the stake below DEN and SEA because the price edge has disappeared.'
});
patchGame('NE @ BUF', {
  current:'NE +6.5 to +7', diff:'0 to +0.5', role:'Key-number value, source-range capped',
  marketNote:'Action shows NE +6.5; the current CBS odds board also shows +7 available. Sly +7 is at the favorable end of the market, but not uniquely stale.',
  evidence:'Frozen V2 gives about +2.86% net scoring edge if the fair reference is NE +6.5, but that edge falls toward neutral wherever +7 is available. Treat this as source-range sensitive.',
  why:'Sly preserves the key +7 against the core +6.5 market, but the advantage is not universal across books.',
  verdict:'Small only. Keep the injury cap and do not treat this as a broad-market lock.'
});
patchGame('IND @ WAS', {
  current:'IND -3.5 to -4.5', diff:'0 to -1.0', role:'Context + market-range watch',
  marketNote:'Action currently displays IND -3.5, while the broader afternoon board includes -4 and -4.5. Sly -3.5 is favorable versus much of the range but not every book.',
  evidence:'Frozen V2 is neutral against an IND -3.5 reference and materially favorable when the market is -4/-4.5. Because the current book range is wide, this remains a conditional rather than a robust edge.',
  verdict:'High-priority Sunday watch. A broad move to -4/-4.5 while Sly stays -3.5 would justify an upgrade.'
});
patchGame('GB @ TB', {
  current:'GB -3.5', diff:'0.0',
  marketNote:'Action and the latest CBS/SportsLine board show GB -3.5, equal to Sly. Baker Mayfield is out, but that news is already reflected in the current number.',
  evidence:'No current Sly price edge at GB -3.5. This is context only and should not be upgraded by double-counting the quarterback news.',
  verdict:'Small contextual fourth-game option only; otherwise pass.'
});
patchGame('NYJ @ CHI', {
  current:'NYJ +3.5', diff:'0.0',
  marketNote:'Action shows CHI -3.5 / NYJ +3.5, equal to Sly. Mixed high-impact injuries on both teams keep it a watch/pass.'
});
patchGame('LAR @ PHI', {
  current:'PHI +3.5', diff:'0.0',
  marketNote:'Action shows LAR -3.5 / PHI +3.5, equal to Sly. No current price advantage.'
});
patchGame('DAL @ HOU', {
  current:'DAL +2.5 to +3', diff:'0 to +0.5',
  marketNote:'Current sources span HOU -2.5 to -3. Friday HOU -3 no longer owns a favorite-side price advantage; do not force a flip to Dallas from a split range.'
});
patchGame('MIA @ MIN', {
  current:'MIN -10 to -10.5', diff:'0 to +0.5',
  marketNote:'Action is MIN -10.5 while the latest CBS/SportsLine board has shown MIN -10. The market range does not create a clean Sly favorite-side edge.'
});

let cachedHtml = null;
let loadError = null;

function replaceConstArray(html, name, value) {
  const needle = `const ${name}=`;
  const decl = html.indexOf(needle);
  if (decl < 0) throw new Error(`Unable to locate native ${name} declaration`);
  const start = html.indexOf('[', decl + needle.length);
  if (start < 0) throw new Error(`Unable to locate ${name} array start`);
  let depth = 0, quote = null, escaped = false, end = -1;
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
    else if (ch === ']') { depth--; if (depth === 0) { end = i + 1; break; } }
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
    return res.end(JSON.stringify({status:'ok',version:current.version,captured_at_local:current.captured_at_local,snapshot_label:current.snapshot_label,top_board:current.games.slice(0,6).map(g=>({rank:g.rank,game:g.game,lean:g.lean,decision:g.decision,current:g.current,sly:g.sly,catherine:g.catherine,amanda:g.amanda})),working_portfolio:current.working_portfolio}));
  }
  if (req.url === '/healthz') {
    try {
      const html = await loadApp();
      const checks = {
        week4DataInjected: html.includes('DEN @ SF') && html.includes('LAC @ SEA') && !html.includes('const games=[{"rank":2,"game":"NYJ @ DET"'),
        sourceDataInjected: html.includes('2 verified signals support SEA'),
        saturdayPatch: html.includes('week4-saturday-layer'),
        afternoonCrossCheck: html.includes('week4-native-v4-2026-10-03-afternoon') && html.includes('NE +6.5 to +7')
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
    console.log(`Loaded ${current.version}: ${Buffer.byteLength(html)} bytes; Saturday Week 4 arrays injected after afternoon cross-check`);
    console.log(`Saturday top board: ${current.games.slice(0,6).map(g=>`${g.rank}:${g.lean}`).join(' | ')}`);
  } catch (err) {
    console.error('Initial canonical app load failed:', err);
  }
});
