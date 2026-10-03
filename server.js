const http = require('http');
const fs = require('fs');

const port = process.env.PORT || 10000;
const BASE_URL = process.env.BASE_URL || 'https://monopoly-command-center-v67.floot.app/_cdn/static/f4ebb851-c03c-451c-81c5-343be9983db0-command-center-v67-all3-currentmodel.txt';

const gameDetailUiPatch = fs.readFileSync('game-detail-ui-patch.html', 'utf8');
const mobilePatch = fs.readFileSync('mobile-patch.html', 'utf8');
const mobileNavFix = fs.readFileSync('mobile-nav-fix.html', 'utf8');
const sportslinePatch = fs.readFileSync('week4-sportsline-integration-patch.html', 'utf8');
const current = JSON.parse(fs.readFileSync('week4-current-data.json', 'utf8'));
const sportslineSnapshot = JSON.parse(fs.readFileSync('week4-sportsline-2026-10-03-1611ET.json', 'utf8'));

current.version = 'week4-native-v5-2026-10-03-1611ET';
current.captured_at_local = sportslineSnapshot.captured_at_local;
current.snapshot_label = 'Week 4 Saturday · Oct 3 · 4:11 PM ET · SportsLine full slate reconciled';

const byGame = Object.fromEntries(current.games.map(g => [g.game, g]));
const sourceByGame = Object.fromEntries(current.sourceData.map(g => [g.game, g]));
function patchGame(id, patch) { if (byGame[id]) Object.assign(byGame[id], patch); }

// Preserve SportsLine as its own source. Do not overwrite the immutable Sly line or
// canonical opener with source-specific SportsLine values.
for (const [id, sl] of Object.entries(sportslineSnapshot.games)) {
  const g = byGame[id];
  if (!g) continue;
  const score = Object.entries(sl.projected).map(([team,pts]) => `${team} ${pts}`).join(' · ');
  g.sportsline = {
    side: sl.sim_type === 'Spread' ? sl.sim_pick : null,
    grade: sl.sim_grade,
    strength: `Visible SIM ${sl.sim_grade}: ${sl.sim_pick}`,
    modelProb: null,
    marketProb: null,
    openPrice: sl.open_spread,
    currentPrice: sl.current_spread,
    refLine: g.sly,
    note: `User-provided SportsLine screenshot; ${sl.sportsline_pick_count} SportsLine picks displayed`,
    kind: sl.sim_type,
    pickCount: sl.sportsline_pick_count,
    visiblePick: sl.sim_pick,
    openTotal: sl.open_total,
    currentTotal: sl.current_total,
    projectedScore: score
  };
  const s = sourceByGame[id];
  if (s) {
    s.sportsGrade = sl.sim_grade;
    s.sportsPick = sl.sim_pick;
    s.sportsType = sl.sim_type;
    s.sportsScore = `Projected ${score}`;
    s.sportsCurrent = sl.current_spread;
    s.sportsPickCount = sl.sportsline_pick_count;
  }
}

// Re-rank after the full SportsLine slate correction. The ranking separates:
// 1) Sly-vs-market price value, 2) visible SportsLine spread SIM support,
// 3) injury/QB/context risk. Total and moneyline SIMs are not ATS votes.
patchGame('DEN @ SF', {
  rank:1, state:'PLAY', decision:'PLAY', lean:'DEN +3', confidence:'High relative to slate', catherine:800, amanda:400,
  role:'Core broad-market price value',
  current:'DEN +2.5', diff:'+0.5',
  evidence:'SportsLine current is SF -2.5 / DEN +2.5, matching the -2.5 market reference. Sly DEN +3 keeps the valuable half-point through key 3. SportsLine SIM is Under 48, not an ATS side.',
  why:'The Sly number is genuinely better than the current SportsLine/Action reference around the key 3, while San Francisco defensive absences support the risk case.',
  against:'SportsLine does not provide an ATS side signal here; this remains primarily a price-value play against a strong San Francisco team.',
  verdict:'Best current price-value play; core but not an all-model consensus.',
  whyPlay:'Sly +3 versus SportsLine/Action +2.5 is the cleanest current number advantage.',
  marketNote:'SportsLine SF -2.5; Action/DK around SF -2.5. Sly DEN +3 retains a half-point through key 3.'
});
patchGame('LAC @ SEA', {
  rank:2, state:'PLAY', decision:'PLAY', lean:'SEA -7', confidence:'Medium+', catherine:500, amanda:600,
  role:'SportsLine football-model core',
  current:'SEA -7', diff:'0.0',
  evidence:'SportsLine current is SEA -7 and its visible SIM pick is SEA -7 with a B grade. Sly is market-equal, so there is no frozen-V2 price edge.',
  why:'This is explicit football-model support at the exact contest line, the evidence lane V2 itself does not provide.',
  against:'There is no Sly-vs-market price advantage and 7 is a key push number.',
  verdict:'Core secondary to DEN because the case is football-model support rather than line value.',
  whyPlay:'SportsLine B spread SIM explicitly backs SEA -7 at the exact Sly line.',
  marketNote:'SportsLine open SEA -6.5, current SEA -7; Sly SEA -7 is market-equal.'
});
patchGame('IND @ WAS', {
  rank:3, state:'PLAY', decision:'PLAY', lean:'IND -3.5', confidence:'Medium', catherine:0, amanda:300,
  role:'Source-sensitive price value + context',
  current:'IND -3.5 to -4.5', diff:'0 to -1.0',
  evidence:'SportsLine current is IND -4.5 while Sly is IND -3.5, a full-point advantage at this source. The visible SportsLine SIM pick is Over 46.5, not an ATS side.',
  why:'The SportsLine price makes Sly attractive and Washington QB/OL absences independently support Indianapolis context.',
  against:'Other books have been closer to IND -3.5, so the price edge is source-sensitive rather than broad-market unanimous.',
  verdict:'Promoted from watch to a modest play; do not size like DEN or SEA unless the broader market consolidates at -4/-4.5.',
  whyPlay:'Full point of SportsLine line value plus Washington injury context, with source disagreement keeping the stake modest.',
  marketNote:'SportsLine IND -4.5; other books have shown -3.5 to -4.5. Sly IND -3.5 is favorable versus SportsLine.'
});
patchGame('JAX @ CIN', {
  rank:4, state:'PLAY', decision:'PLAY', lean:'JAX +2.5', confidence:'Medium', catherine:300, amanda:0,
  role:'SportsLine ATS secondary',
  current:'CIN -2.5', diff:'0.0',
  evidence:'SportsLine current equals Sly at CIN -2.5, but its visible SIM pick is JAX +2.5 with a B grade and a projected score of JAX 28, CIN 27.',
  why:'Explicit independent spread-model support at the exact Sly number adds a matchup signal despite no price edge.',
  against:'Frozen V2 is market-equal and this is one external football-model signal, not cross-source consensus.',
  verdict:'New secondary play; modest stake only.',
  whyPlay:'SportsLine B spread SIM explicitly backs JAX +2.5 at the exact contest line.',
  marketNote:'SportsLine open/current CIN -2.5; Sly is equal. SportsLine SIM: JAX +2.5 (B).'
});
patchGame('DAL @ HOU', {
  rank:5, state:'PLAY', decision:'PLAY', lean:'HOU -3', confidence:'Medium-', catherine:300, amanda:0,
  role:'SportsLine ATS secondary',
  current:'HOU -3', diff:'0.0',
  evidence:'SportsLine current equals Sly at HOU -3 and its visible SIM pick is HOU -3 with a B grade; projected score is HOU 30, DAL 23.',
  why:'The Friday stale-line thesis is gone, but a separate SportsLine football-model signal now supports Houston at the exact Sly line.',
  against:'There is no current price advantage, so this should not be sized like a robust market-value edge.',
  verdict:'Reintroduced only as a small football-model play, not as the former Friday price-edge core.',
  whyPlay:'SportsLine B spread SIM backs HOU -3; no Sly price edge.',
  marketNote:'SportsLine HOU -3, equal to Sly. Treat as football-model support only.'
});
patchGame('KC @ LV', {
  rank:6, state:'WATCH', decision:'WATCH', lean:'KC -4.5', confidence:'Low-Med', catherine:0, amanda:200,
  role:'Small SportsLine ATS position',
  current:'KC -4.5', diff:'0.0',
  evidence:'SportsLine current equals Sly at KC -4.5 and its visible SIM pick is KC -4.5 with a B grade; projected score is KC 28, LV 21.',
  why:'Independent spread-model support exists at the exact Sly line.',
  against:'No price edge and no verified Gridiron/Lucas confirmation; keep exposure small.',
  verdict:'Small fourth-game position for Amanda, below the top five in conviction.',
  whyPlay:'SportsLine B spread SIM at the exact Sly line, but no market-value edge.',
  marketNote:'SportsLine open/current KC -4.5; Sly equal.'
});
patchGame('NE @ BUF', {
  rank:7, state:'WATCH', decision:'WATCH', lean:'NE +7', confidence:'Low-Med', catherine:0, amanda:0,
  role:'Source-sensitive key-number watch',
  current:'NE +6.5 to +7', diff:'0 to +0.5',
  evidence:'SportsLine current is BUF -7, exactly equal to Sly. The visible SportsLine SIM is NE +264 moneyline, not an ATS pick. Action/DK have shown NE +6.5, creating source-sensitive key-7 value only.',
  why:'The +7 can still matter against books at +6.5 and the SportsLine moneyline SIM is directionally interesting.',
  against:'SportsLine itself removes the price edge and New England has significant injury absences. Moneyline is not an ATS vote.',
  verdict:'Downgraded from play to watch; no working stake.',
  whyPlay:'Potential key-number value exists only at part of the market and is offset by injuries.',
  marketNote:'SportsLine BUF -7 = Sly; Action/DK have shown BUF -6.5. Source-sensitive only.'
});
patchGame('ATL @ NO', {
  rank:8, state:'WATCH', decision:'WATCH', lean:'ATL +2.5', confidence:'Low', catherine:0, amanda:0,
  role:'Low-priority SportsLine ATS watch',
  current:'NO -2.5', diff:'0.0',
  evidence:'SportsLine current equals Sly at NO -2.5 and its visible SIM pick is ATL +2.5 with a C grade.',
  why:'There is a visible SportsLine ATS signal at the exact Sly number.',
  against:'Only a C grade and no price advantage; insufficient for current portfolio sizing.',
  verdict:'Watch only.',
  whyPlay:'SportsLine C spread SIM supports ATL +2.5, but evidence is weak.',
  marketNote:'SportsLine open/current NO -2.5; SIM ATL +2.5 (C).'
});
patchGame('ARI @ NYG', {
  rank:9, state:'WATCH', decision:'WATCH', lean:'NYG +2.5', confidence:'Low', catherine:0, amanda:0,
  role:'Market-equal watch',
  current:'NYG +2.5', diff:'0.0',
  evidence:'SportsLine current is ARI -2.5 / NYG +2.5, equal to Sly. The visible SportsLine SIM pick is Over 44.5, not NYG +2.5.',
  why:'Sly is not worse than SportsLine, but there is no visible SportsLine ATS side support in the supplied screenshot.',
  against:'The prior NYG SportsLine ATS attribution was incorrect; the screenshot shows a total SIM. Jameis Winston starts with Jaxson Dart on IR.',
  verdict:'Downgraded from play to watch and removed from the working portfolio.',
  whyPlay:'No validated ATS edge after correcting the SportsLine attribution.',
  marketNote:'SportsLine NYG +2.5 equals Sly; visible SIM is Over 44.5 (C), not an ATS side.'
});
patchGame('LAR @ PHI', {
  rank:10, state:'WATCH', decision:'WATCH', lean:'PHI +3.5', confidence:'Low', catherine:0, amanda:0,
  role:'Non-ATS directional watch',
  current:'PHI +3.5', diff:'0.0',
  evidence:'SportsLine current equals Sly at PHI +3.5. Its visible SIM selection is PHI +160 moneyline, not an ATS pick.',
  why:'The moneyline model direction favors Philadelphia, but it cannot be counted as spread confirmation.',
  against:'No price edge and no visible SportsLine ATS selection.',
  verdict:'Watch only.',
  whyPlay:'Directional ML support only; not an ATS vote.',
  marketNote:'SportsLine PHI +3.5 equals Sly; SIM PHI +160 (C moneyline).'
});
patchGame('MIA @ MIN', {
  rank:11, state:'PASS', decision:'PASS', lean:'NO TAKE', confidence:'Conflict', catherine:0, amanda:0,
  role:'Line-mismatch pass',
  current:'MIN -9.5', diff:'Sly worse by 1.0',
  evidence:'SportsLine visible SIM pick is MIN -9.5 with an A grade, but Sly requires MIN -10.5. The football-model signal is therefore not at our contest price.',
  why:'SportsLine strongly likes Minnesota at -9.5, but that does not automatically transfer through an extra point to -10.5.',
  against:'Sly is a full point worse than the SportsLine current spread; Justin Jefferson is also out.',
  verdict:'Pass at Sly -10.5 unless later evidence explicitly supports the worse number.',
  whyPlay:'Strong SportsLine signal exists at a materially better line than Sly, so do not chase.',
  marketNote:'SportsLine MIN -9.5 vs Sly MIN -10.5; SIM MIN -9.5 (A).'
});
patchGame('GB @ TB', {
  rank:12, state:'PASS', decision:'PASS', lean:'NO TAKE', confidence:'Negative', catherine:0, amanda:0,
  role:'Price/context conflict',
  current:'GB -3', diff:'Sly worse by 0.5',
  evidence:'SportsLine current is GB -3 while Sly is GB -3.5, so the contest line is worse for Green Bay. SportsLine SIM is TB +143 moneyline, not an ATS pick.',
  why:'There is no price reason to lay the extra half-point with Green Bay.',
  against:'SportsLine market and moneyline model both argue against treating GB -3.5 as a preferred wager despite Tampa QB news.',
  verdict:'Removed from Amanda portfolio.',
  whyPlay:'Sly is worse than SportsLine and the visible SIM leans Tampa moneyline.',
  marketNote:'SportsLine TB +3 / GB -3; Sly GB -3.5 is half a point worse.'
});
patchGame('NYJ @ CHI', {rank:13, state:'PASS', decision:'PASS', lean:'NO TAKE', catherine:0, amanda:0, evidence:'SportsLine current CHI -3.5 equals Sly. Visible SIM is Over 43.5 (B), not an ATS side.', whyPlay:'No SportsLine ATS signal and no price edge.', marketNote:'SportsLine CHI -3.5; SIM Over 43.5 (B).'});
patchGame('DET @ CAR', {rank:14, state:'PASS', decision:'PASS', lean:'NO TAKE', catherine:0, amanda:0, evidence:'SportsLine current CAR +3.5 / DET -3.5 equals Sly. Visible SIM is CAR +163 moneyline (B), not ATS.', whyPlay:'No spread price edge; moneyline signal is not an ATS vote.', marketNote:'SportsLine CAR +3.5; SIM CAR +163 (B moneyline).'});
patchGame('TEN @ BAL', {rank:15, state:'PASS', decision:'PASS', lean:'NO TAKE', catherine:0, amanda:0, evidence:'SportsLine current BAL -11.5 equals Sly. Visible SIM is Over 42.5 (B), not an ATS side.', whyPlay:'No SportsLine ATS signal and no price edge.', marketNote:'SportsLine BAL -11.5; SIM Over 42.5 (B).'});

current.games.sort((a,b) => a.rank - b.rank);

current.working_portfolio = {
  household_outlay: 3400,
  deployment_fraction: Number((3400 / 19500).toFixed(4)),
  Catherine: [
    {pick:'DEN +3',amount:800,role:'core market-value edge'},
    {pick:'SEA -7',amount:500,role:'SportsLine B spread core'},
    {pick:'JAX +2.5',amount:300,role:'SportsLine B spread secondary'},
    {pick:'HOU -3',amount:300,role:'SportsLine B spread secondary'}
  ],
  Amanda: [
    {pick:'SEA -7',amount:600,role:'SportsLine B spread core'},
    {pick:'DEN +3',amount:400,role:'core market-value edge'},
    {pick:'IND -3.5',amount:300,role:'source-sensitive line value + context'},
    {pick:'KC -4.5',amount:200,role:'small SportsLine B spread position'}
  ]
};

const gradeByRank = r => r <= 2 ? 'A-' : r <= 5 ? 'B' : r <= 8 ? 'C+' : '—';
for (const g of current.games) {
  const s = sourceByGame[g.game];
  if (!s) continue;
  s.ourRank = g.rank;
  s.ourGrade = gradeByRank(g.rank);
  s.ourPick = g.lean === 'NO TAKE' ? 'NO TAKE' : g.lean;
  s.ourState = g.decision;
  const sl = g.sportsline;
  const ats = sl && sl.kind === 'Spread';
  if (ats) {
    const same = g.lean !== 'NO TAKE' && sl.visiblePick === g.lean;
    s.agreement = same ? 'Our side + SportsLine spread SIM align' : `SportsLine ATS: ${sl.visiblePick}`;
  } else if (sl) {
    s.agreement = `${sl.kind} SIM only · not ATS evidence`;
  } else {
    s.agreement = 'SportsLine unavailable';
  }
}
current.sourceData.sort((a,b) => a.ourRank - b.ourRank);

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
  const combinedPatch = `${publicState}\n${gameDetailUiPatch}\n${mobilePatch}\n${mobileNavFix}\n${sportslinePatch}`;
  cachedHtml = base.includes('</body>') ? base.replace('</body>', `${combinedPatch}\n</body>`) : `${base}\n${combinedPatch}`;
  return cachedHtml;
}

const server = http.createServer(async (req, res) => {
  if (req.url === '/_version') {
    res.writeHead(200, {'content-type':'application/json; charset=utf-8','cache-control':'no-store'});
    return res.end(JSON.stringify({status:'ok',version:current.version,captured_at_local:current.captured_at_local,snapshot_label:current.snapshot_label,top_board:current.games.slice(0,8).map(g=>({rank:g.rank,game:g.game,lean:g.lean,decision:g.decision,current:g.current,sly:g.sly,sportsline:g.sportsline?.visiblePick,catherine:g.catherine,amanda:g.amanda})),working_portfolio:current.working_portfolio}));
  }
  if (req.url === '/healthz') {
    try {
      const html = await loadApp();
      const checks = {
        week4DataInjected: html.includes('DEN @ SF') && html.includes('LAC @ SEA') && !html.includes('const games=[{"rank":2,"game":"NYJ @ DET"'),
        sportslineFullSlate: current.games.every(g => g.sportsline && g.sportsline.currentPrice),
        sportslineSourceRows: current.sourceData.length === 15 && current.sourceData.every(s => s.sportsCurrent && s.sportsCurrent !== '—'),
        correctedNygAttribution: byGame['ARI @ NYG'].sportsline.kind === 'Total' && byGame['ARI @ NYG'].sportsline.visiblePick === 'OVER 44.5',
        correctedNeAttribution: byGame['NE @ BUF'].sportsline.kind === 'Moneyline',
        newPatchLoaded: html.includes('week4-sportsline-layer'),
        latestVersion: current.version === 'week4-native-v5-2026-10-03-1611ET'
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
    console.log(`Loaded ${current.version}: ${Buffer.byteLength(html)} bytes; SportsLine full slate reconciled`);
    console.log(`Top board: ${current.games.slice(0,8).map(g=>`${g.rank}:${g.lean}`).join(' | ')}`);
  } catch (err) {
    console.error('Initial canonical app load failed:', err);
  }
});
