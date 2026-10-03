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
const gridironSnapshot = JSON.parse(fs.readFileSync('week4-gridiron-2026-10-03.json', 'utf8'));
const liveSnapshot = JSON.parse(fs.readFileSync('week4-live-market-context-2026-10-03-1710ET.json', 'utf8'));

current.version = 'week4-native-v6-2026-10-03-1710ET';
current.captured_at_local = liveSnapshot.captured_at_local;
current.snapshot_label = 'Week 4 Saturday · Oct 3 · 5:10 PM ET · full Command Center reconciliation';

const byGame = Object.fromEntries(current.games.map(g => [g.game, g]));
function signed(n){ return n > 0 ? `+${n}` : `${n}`; }
function gridGrade(p){ return p >= 55 ? 'A' : p >= 52 ? 'B' : p >= 51 ? 'C' : 'N'; }
function gridBest(d){
  if (d.away_cover_pct === d.home_cover_pct) return {team:'NO TAKE', pct:50, line:'50/50'};
  if (d.away_cover_pct > d.home_cover_pct) return {team:d.away, pct:d.away_cover_pct, line:`${d.away} ${signed(-d.home_spread)}`};
  return {team:d.home, pct:d.home_cover_pct, line:`${d.home} ${signed(d.home_spread)}`};
}
function money(n){ return '$' + Number(n || 0).toLocaleString(); }

// Normalize every source onto the native Week 4 game objects before the legacy app renders.
for (const g of current.games) {
  const sl = sportslineSnapshot.games[g.game];
  const ga = gridironSnapshot.games[g.game];
  const live = liveSnapshot.games[g.game];
  if (!sl || !ga || !live) throw new Error(`Missing normalized Week 4 source data for ${g.game}`);

  const score = Object.entries(sl.projected).map(([team,pts]) => `${team} ${pts}`).join(' · ');
  const simPct = sl.sim_pct && sl.sim_pct.cover_pct != null ? sl.sim_pct.cover_pct : null;
  const gb = gridBest(ga);

  g.current = live.action_spread;
  g.weather = live.weather;
  g.marketNote = live.market_note;
  g.liveMarket = {
    source: 'Action Network',
    spread: live.action_spread,
    total: live.action_total,
    captured_at_local: liveSnapshot.captured_at_local
  };
  g.sportsline = {
    side: sl.sim_type === 'Spread' ? sl.sim_pick : null,
    grade: sl.sim_grade,
    strength: `Visible SIM ${sl.sim_grade}: ${sl.sim_pick}`,
    modelProb: simPct,
    marketProb: null,
    openPrice: sl.open_spread,
    currentPrice: sl.current_spread,
    refLine: g.sly,
    moneyPct: sl.money_pct,
    simPct: sl.sim_pct,
    note: `User-provided SportsLine screenshots · ${sl.sportsline_pick_count} SportsLine picks displayed`,
    kind: sl.sim_type,
    pickCount: sl.sportsline_pick_count,
    visiblePick: sl.sim_pick,
    openTotal: sl.open_total,
    currentTotal: sl.current_total,
    projectedScore: score
  };
  g.gridiron = {
    line: `${ga.home} ${signed(ga.home_spread)}`,
    away: ga.away,
    awayPct: ga.away_cover_pct,
    home: ga.home,
    homePct: ga.home_cover_pct,
    bestSide: gb.team,
    bestPct: gb.pct,
    bestLine: gb.line,
    grade: gridGrade(gb.pct),
    source: 'User-provided Week 4 Gridiron screenshot'
  };
  g.sources = {
    market: g.liveMarket,
    sportsline: g.sportsline,
    gridiron: g.gridiron,
    lucas: null
  };
  g.news = [{
    initials: 'NFL',
    name: 'Official Week 4 injury report',
    team: '',
    time: 'Oct 3 official',
    headline: 'Latest official statuses',
    detail: live.injuries,
    source: 'NFL official Week 4 injury report'
  }];
}

// Latest recommendation synthesis: Sly line value + verified SportsLine ATS/market evidence
// + Gridiron cover model + official injury/weather context. External sources never rewrite
// frozen V2 probabilities; this is the governed decision layer used by the Command Center.
const REC = {
  'DEN @ SF': {rank:1,state:'PLAY',decision:'PLAY',lean:'DEN +3',confidence:'High relative to slate',catherine:800,amanda:400,role:'Core key-number price value',diff:'+0.5 vs Action',evidence:'Action is DEN +2.5 while Sly gives DEN +3 through the key number. San Francisco also has Nick Bosa, James Thompson Jr. and Mykel Williams OUT.',why:'This remains the cleanest current Sly-versus-market number advantage and the injury context does not fight the Denver side.',against:'Gridiron is 50/50 at SF -3 and SportsLine visible SIM is a total, not Denver ATS confirmation.',verdict:'Core play. Best current blend of price value and context.',whyPlay:'Sly +3 versus Action +2.5 preserves the valuable half-point through 3.'},
  'LAC @ SEA': {rank:2,state:'PLAY',decision:'PLAY',lean:'SEA -7',confidence:'High-Med',catherine:500,amanda:600,role:'SportsLine football-model core',diff:'0.0 vs Action',evidence:'Action and Sly are both SEA -7. SportsLine B explicitly backs SEA -7 and a public SportsLine model result puts Seattle at approximately 60% to cover; Gridiron is 50/50.',why:'This is the strongest verified football-model signal at the exact contest line.',against:'There is no Sly price edge and 7 carries push risk.',verdict:'Core play, but for football-model support rather than stale-line value.',whyPlay:'Verified SportsLine ATS support at the exact Sly line.'},
  'KC @ LV': {rank:3,state:'PLAY',decision:'PLAY',lean:'KC -4.5',confidence:'Medium+',catherine:400,amanda:500,role:'Cross-model exact-line alignment',diff:'0.0 vs Action',evidence:'Action equals Sly at KC -4.5. SportsLine B explicitly backs KC -4.5 and Gridiron gives KC a slate-high 57% cover probability at the same -4.5.',why:'This is the strongest exact-line agreement between the two independent football-model sources we currently possess.',against:'No Sly-versus-market price edge; the value comes from model agreement rather than a stale contest number.',verdict:'Promoted to a core secondary play.',whyPlay:'SportsLine B + Gridiron A/57% align on KC -4.5 at the exact Sly line.'},
  'ARI @ NYG': {rank:4,state:'PLAY',decision:'PLAY',lean:'NYG +2.5',confidence:'Medium',catherine:300,amanda:0,role:'Gridiron side with better Sly number',diff:'0.0 vs Action',evidence:'Action is ARI -2.5, equal to Sly. Gridiron gives NYG 52% to cover at only +1.5; Sly gives the same Gridiron-preferred side an extra full point at +2.5.',why:'The strongest part of this case is not SportsLine; it is getting a materially better number than the line on which Gridiron already prefers New York.',against:'SportsLine visible SIM is Over 44.5, not a Giants ATS pick; Arizona is favored in the broader market.',verdict:'Secondary play, below DEN/SEA/KC.',whyPlay:'Gridiron prefers NYG at +1.5 and Sly improves that to +2.5.'},
  'IND @ WAS': {rank:5,state:'PLAY',decision:'PLAY',lean:'IND -3.5',confidence:'Medium',catherine:0,amanda:300,role:'SportsLine line value + injury context',diff:'0.0 Action / +1.0 vs SportsLine',evidence:'Action equals Sly at IND -3.5, but SportsLine is IND -4.5. Washington has Jayden Daniels, Rachaad White, Sam Cosmi and Nick Cross OUT.',why:'Sly is a full point better than SportsLine and the key Washington absences support the same direction.',against:'Gridiron is 50/50 and Action removes the price edge, so this remains source-sensitive rather than broad-market unanimous.',verdict:'Modest play; do not size like the top three.',whyPlay:'One-point SportsLine advantage plus major Washington absences.'},
  'NE @ BUF': {rank:6,state:'WATCH',decision:'WATCH',lean:'NE +7',confidence:'Low-Med',catherine:0,amanda:0,role:'Key-number value with injury conflict',diff:'+0.5 vs Action',evidence:'Action is NE +6.5 while Sly gives +7. SportsLine is BUF -7 and Gridiron leans BUF 51%. New England has Christian Barmore, Christian Gonzalez and Brenden Schooler OUT.',why:'The half-point to the key 7 is real market value.',against:'Both Gridiron and the injury context lean against New England; SportsLine itself is market-equal to Sly.',verdict:'Watch only despite the useful number.',whyPlay:'Key-number value exists, but football evidence conflicts.'},
  'LAR @ PHI': {rank:7,state:'WATCH',decision:'WATCH',lean:'PHI +3.5',confidence:'Low-Med',catherine:0,amanda:0,role:'Key-number watch',diff:'+0.5 vs Action',evidence:'Action is PHI +3 while Sly gives +3.5 through the key 3. SportsLine visible SIM is PHI moneyline and Gridiron is 50/50 at PHI +2.5.',why:'Sly owns a meaningful half-point around 3 and SportsLine ML direction is compatible.',against:'Philadelphia has six notable players OUT, including DeVonta Smith, Dallas Goedert and Zack Baun.',verdict:'Watch; price is attractive but the injury list is substantial.',whyPlay:'Half-point through 3 is valuable, but personnel risk prevents promotion.'},
  'JAX @ CIN': {rank:8,state:'WATCH',decision:'WATCH',lean:'JAX +2.5',confidence:'Low-Med',catherine:0,amanda:0,role:'External-model disagreement',diff:'0.0 vs Action',evidence:'SportsLine B explicitly backs JAX +2.5 at the exact line, while Gridiron gives CIN 51% at -2.5. Action equals Sly.',why:'There is legitimate SportsLine ATS support.',against:'Gridiron points the other way and there is no market price edge.',verdict:'Watch, not a portfolio core.',whyPlay:'One strong ATS model signal is offset by a direct Gridiron disagreement.'},
  'TEN @ BAL': {rank:9,state:'WATCH',decision:'WATCH',lean:'TEN +11.5',confidence:'Low-Med',catherine:0,amanda:0,role:'Gridiron exact-line lean',diff:'0.0 vs Action',evidence:'Action equals Sly. Gridiron gives TEN 52% to cover +11.5; SportsLine visible SIM is the total, not an ATS side.',why:'Gridiron provides a modest exact-line dog signal.',against:'Only one verified spread-model source supports the side and Baltimore remains a large favorite.',verdict:'Watch only.',whyPlay:'Gridiron B/52% at the exact Sly number.'},
  'GB @ TB': {rank:10,state:'WATCH',decision:'WATCH',lean:'TB +3.5',confidence:'Low',catherine:0,amanda:0,role:'Underdog directional support',diff:'0.0 vs Action',evidence:'Action equals Sly at TB +3.5. Gridiron gives TB 51% at +3.5 and SportsLine B visible SIM is TB moneyline.',why:'Two independent directional signals point toward Tampa despite the backup-QB situation.',against:'SportsLine signal is moneyline, not ATS, and Baker Mayfield is OUT.',verdict:'Watch only.',whyPlay:'Directional source agreement is interesting but not strong enough for a wager.'},
  'DAL @ HOU': {rank:11,state:'WATCH',decision:'WATCH',lean:'DAL +3',confidence:'Conflict',catherine:0,amanda:0,role:'Direct source conflict',diff:'Sly +0.0 to +0.5 for DAL',evidence:'Action is around HOU -2.5/-3. SportsLine B backs HOU -3, while Gridiron gives DAL 52% at +2.5; Sly improves Dallas to +3.',why:'The Dallas number is attractive relative to the Gridiron reference.',against:'SportsLine explicitly backs the opposite side at the exact Sly number.',verdict:'Do not force a side until the model conflict resolves or the market moves.',whyPlay:'Contradiction game, not a current wager.'},
  'ATL @ NO': {rank:12,state:'WATCH',decision:'WATCH',lean:'ATL +2.5',confidence:'Low',catherine:0,amanda:0,role:'Weak external support',diff:'0.0 vs Action',evidence:'SportsLine C backs ATL +2.5. Gridiron gives ATL 51%, but at +3 rather than the worse Sly +2.5.',why:'Both sources lean Atlanta directionally.',against:'The Gridiron percentage belongs to a half-point better line than Sly, and the SportsLine grade is only C.',verdict:'Watch only.',whyPlay:'Direction aligns, but line quality and confidence are weak.'},
  'MIA @ MIN': {rank:13,state:'PASS',decision:'PASS',lean:'MIN -10.5',confidence:'Line penalty',catherine:0,amanda:0,role:'Strong model at worse contest price',diff:'0.0 vs Action',evidence:'Gridiron gives MIN 52% at -10.5, but SportsLine A backs MIN only at -9.5 while Sly requires -10.5.',why:'Minnesota has external-model support.',against:'SportsLine support is at a full point better than the contest number and Justin Jefferson is OUT.',verdict:'Pass at Sly -10.5.',whyPlay:'Do not transfer a strong pick through a materially worse number.'},
  'DET @ CAR': {rank:14,state:'PASS',decision:'PASS',lean:'NO TAKE',confidence:'Conflict',catherine:0,amanda:0,role:'Market-equal conflict',diff:'0.0 vs Action',evidence:'Action equals Sly. Gridiron gives DET 51% at -3.5 while SportsLine B visible SIM is Carolina moneyline.',why:'No clean price edge.',against:'The independent directional evidence conflicts.',verdict:'Pass.',whyPlay:'No validated cross-source edge.'},
  'NYJ @ CHI': {rank:15,state:'PASS',decision:'PASS',lean:'NO TAKE',confidence:'Mixed injuries',catherine:0,amanda:0,role:'Market-equal injury conflict',diff:'0.0 vs Action',evidence:'Action equals Sly. Gridiron gives CHI 52% at -3.5; SportsLine visible SIM is the total. Both teams have major absences, including Caleb Williams for Chicago and five Jets starters/contributors.',why:'No Sly price advantage exists.',against:'The injury distribution is too messy to turn a modest Gridiron lean into a bet.',verdict:'Pass.',whyPlay:'No clean spread edge after injuries and source review.'}
};

for (const [id, rec] of Object.entries(REC)) Object.assign(byGame[id], rec);
current.games.sort((a,b) => a.rank - b.rank);

current.working_portfolio = {
  household_outlay: 3800,
  deployment_fraction: Number((3800 / 19500).toFixed(4)),
  status: 'SATURDAY_WORKING_NOT_SUBMISSION_FINAL',
  Catherine: current.games.filter(g => g.catherine > 0).map(g => ({pick:g.lean, amount:g.catherine, role:g.role})),
  Amanda: current.games.filter(g => g.amanda > 0).map(g => ({pick:g.lean, amount:g.amanda, role:g.role}))
};

const OUR_GRADES={1:'A',2:'A-',3:'A-',4:'B+',5:'B',6:'B-',7:'B-',8:'C+',9:'C+',10:'C',11:'C',12:'C-',13:'—',14:'—',15:'—'};
current.sourceData = current.games.map(g => {
  const sl=g.sportsline, ga=g.gridiron;
  const moneyText=Object.entries(sl.moneyPct||{}).map(([t,p])=>`${t} ${p}%`).join(' · ');
  const simPctText=sl.simPct ? `${sl.simPct.qualifier==='approximately'?'≈':''}${sl.simPct.cover_pct}% ${sl.simPct.team}` : 'not publicly exposed';
  let agreement='Mixed / incomplete';
  if(g.game==='KC @ LV') agreement='SportsLine B + Gridiron A align exactly on KC -4.5';
  else if(g.game==='LAC @ SEA') agreement='SportsLine B backs SEA -7; Gridiron 50/50';
  else if(g.game==='ARI @ NYG') agreement='Gridiron B likes NYG at +1.5; Sly improves to +2.5';
  else if(g.game==='DEN @ SF') agreement='Sly price edge; external spread models do not confirm a side';
  else if(g.game==='JAX @ CIN'||g.game==='DAL @ HOU'||g.game==='DET @ CAR') agreement='Verified source conflict';
  return {
    game:g.game,time:g.time,sly:g.sly,current:g.current,weather:g.weather,
    ourGrade:OUR_GRADES[g.rank],ourPick:g.lean,ourState:g.decision,ourRank:g.rank,
    sportsGrade:sl.grade,sportsPick:sl.visiblePick,sportsType:sl.kind,sportsScore:`Projected ${sl.projectedScore}`,
    sportsCurrent:sl.currentPrice,sportsOpen:sl.openPrice,sportsMoney:moneyText,sportsSimPct:simPctText,sportsPickCount:sl.pickCount,
    gridGrade:ga.grade,gridPick:ga.bestSide==='NO TAKE'?'50/50':`${ga.bestSide} ${ga.bestPct}%`,gridProb:ga.bestPct,
    gridLine:ga.line,gridOther:`${ga.away} ${ga.awayPct}% / ${ga.home} ${ga.homePct}%`,
    lucas:'UNVERIFIED / NOT SUPPLIED',agreement
  };
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
  const publicState = `<script id="week4-current-public-state">window.WEEK4_CURRENT_META=${JSON.stringify({version:current.version,captured_at_local:current.captured_at_local,snapshot_label:current.snapshot_label,balances:current.balances,working_portfolio:current.working_portfolio})};window.WEEK4_CURRENT_PUBLIC=${JSON.stringify(current.games)};window.WEEK4_SOURCE_PUBLIC=${JSON.stringify(current.sourceData)};window.WEEK4_LIVE_CONTEXT=${JSON.stringify(liveSnapshot)};</script>`;
  const combinedPatch = `${publicState}\n${gameDetailUiPatch}\n${mobilePatch}\n${mobileNavFix}\n${sportslinePatch}`;
  cachedHtml = base.includes('</body>') ? base.replace('</body>', `${combinedPatch}\n</body>`) : `${base}\n${combinedPatch}`;
  return cachedHtml;
}

const server = http.createServer(async (req, res) => {
  if (req.url === '/_version') {
    res.writeHead(200, {'content-type':'application/json; charset=utf-8','cache-control':'no-store'});
    return res.end(JSON.stringify({
      status:'ok',version:current.version,captured_at_local:current.captured_at_local,snapshot_label:current.snapshot_label,
      top_board:current.games.slice(0,12).map(g=>({rank:g.rank,game:g.game,lean:g.lean,decision:g.decision,current:g.current,sly:g.sly,sportsline:g.sportsline?.visiblePick,gridiron:g.gridiron?.bestSide==='NO TAKE'?'50/50':`${g.gridiron?.bestSide} ${g.gridiron?.bestPct}%`,catherine:g.catherine,amanda:g.amanda})),
      working_portfolio:current.working_portfolio
    }));
  }
  if (req.url === '/healthz') {
    try {
      const html = await loadApp();
      const checks = {
        week4DataInjected: current.games.length===15 && html.includes('DEN @ SF') && html.includes('LAC @ SEA'),
        sportslineFullSlate: current.games.every(g => g.sportsline && g.sportsline.currentPrice && g.sportsline.moneyPct),
        gridironFullSlate: current.games.every(g => g.gridiron && Number.isFinite(g.gridiron.bestPct)),
        liveMarketFullSlate: current.games.every(g => g.liveMarket && g.liveMarket.spread && g.weather),
        sourceRows15: current.sourceData.length===15,
        sourceRowsHaveThreeSources: current.sourceData.every(s => s.sportsCurrent && s.gridLine && s.gridGrade),
        correctedNygAttribution: byGame['ARI @ NYG'].sportsline.kind === 'Total' && byGame['ARI @ NYG'].sportsline.visiblePick === 'OVER 44.5',
        correctedNeAttribution: byGame['NE @ BUF'].sportsline.kind === 'Moneyline',
        kcCrossModelAlignment: byGame['KC @ LV'].sportsline.visiblePick === 'KC -4.5' && byGame['KC @ LV'].gridiron.bestSide === 'KC' && byGame['KC @ LV'].gridiron.bestPct === 57,
        latestVersion: current.version === 'week4-native-v6-2026-10-03-1710ET'
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
    console.log(`Loaded ${current.version}: ${Buffer.byteLength(html)} bytes; all Week 4 source layers reconciled`);
    console.log(`Top board: ${current.games.slice(0,8).map(g=>`${g.rank}:${g.lean}`).join(' | ')}`);
    console.log(`Working portfolio: ${money(current.working_portfolio.household_outlay)} household outlay`);
  } catch (err) {
    console.error('Initial canonical app load failed:', err);
  }
});
