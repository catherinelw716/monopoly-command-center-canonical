'use strict';
const http = require('http');
const fs = require('fs');

const port = Number(process.env.PORT || 10000);
const shellTemplate = fs.readFileSync('command-center-shell.html', 'utf8');
const patches = [
  'game-detail-ui-patch.html',
  'mobile-patch.html',
  'mobile-nav-fix.html',
  'week4-sportsline-integration-patch.html',
  'week4-overview-page.html',
  'five-factor-scorecard-page.html',
  'ats-trends-v2-ui-patch.html'
].map(f => fs.readFileSync(f, 'utf8')).join('\n');

const latest = JSON.parse(fs.readFileSync('week4-market-lines-latest.json', 'utf8'));
const current = JSON.parse(fs.readFileSync('week4-current-data.json', 'utf8'));
const sl = JSON.parse(fs.readFileSync('week4-sportsline-2026-10-03-1611ET.json', 'utf8'));
const ga = JSON.parse(fs.readFileSync('week4-gridiron-2026-10-03.json', 'utf8'));
const nf = JSON.parse(fs.readFileSync('week4-nfelo-2026-10-03-1720ET.json', 'utf8'));
const live = JSON.parse(fs.readFileSync('week4-live-market-context-2026-10-03-1710ET.json', 'utf8'));
const opt = JSON.parse(fs.readFileSync('v2/results/week_04_nfelo_optimizer_rerun_2026-10-03.json', 'utf8'));
const atsV2 = JSON.parse(fs.readFileSync('ats-trends-v2-week04-results.json', 'utf8'));
const atsLedger = JSON.parse(fs.readFileSync('ats-trends-prospective-ledger.json', 'utf8'));
const ffEngine = require('./five-factor-scorecard-engine');
const ffInput = JSON.parse(fs.readFileSync('five-factor-scorecard-data-week04.json', 'utf8'));

function esc(v) {
  return String(v ?? '').replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
}
function money(v) { return '$' + Number(v || 0).toLocaleString(); }
function signed(v) { return v > 0 ? `+${v}` : `${v}`; }
function gradeForPct(p) { return p >= 55 ? 'A' : p >= 52 ? 'B' : p >= 51 ? 'C' : 'N'; }
function gridBest(d) {
  if (d.away_cover_pct === d.home_cover_pct) return {side:'NO TAKE', pct:50};
  return d.away_cover_pct > d.home_cover_pct ? {side:d.away,pct:d.away_cover_pct} : {side:d.home,pct:d.home_cover_pct};
}
function nfeloBest(d) {
  const a = {side:d.away, ev:d.ev_away_pct, cur:d.current_away, mod:d.model_away};
  const h = {side:d.home, ev:d.ev_home_pct, cur:d.current_home, mod:d.model_home};
  return a.ev >= h.ev ? a : h;
}
function parseDisplayedLine(text) {
  const m = String(text || '').trim().match(/^([A-Z]{2,4})\s+([+-]?\d+(?:\.5)?)/);
  return m ? {team:m[1], value:Number(m[2])} : null;
}
function lineForTeam(text, team) {
  const p = parseDisplayedLine(text);
  if (!p) return null;
  return p.team === team ? p.value : -p.value;
}
function liveDiff(g) {
  const sly = parseDisplayedLine(g.sly);
  if (!sly) return null;
  const cur = lineForTeam(g.current, sly.team);
  return cur == null ? null : +(cur - sly.value).toFixed(1);
}

// Normalize latest market once, before any view is rendered.
live.captured_at_local = latest.capturedAt;
live.snapshot_type = 'LATEST_MARKET_CONTEXT';
live.market_source = latest.source + ' · ' + latest.sourceNote;
for (const [game, m] of Object.entries(latest.games)) {
  if (!live.games[game]) throw new Error(`latest market game missing from live context: ${game}`);
  live.games[game].action_spread = m.display;
  live.games[game].market_note = `Latest market: ${m.display} (${latest.source}, ${latest.capturedAt}). ${live.games[game].market_note || ''}`;
}
ffInput.capturedAt = latest.capturedAt;
ffInput.sources = ffInput.sources || {};
ffInput.sources.market = latest.source + ' · ' + latest.sourceNote;
for (const g of ffInput.games || []) {
  const m = latest.games[g.game];
  if (!m) continue;
  g.market = g.market || {};
  g.market.currentAway = m.currentAway;
  g.market.source = latest.source;
  g.market.capturedAt = latest.capturedAt;
}
const ff = ffEngine.scoreSlate(ffInput);

current.version = 'week4-local-shell-v1-2026-10-04';
current.captured_at_local = latest.capturedAt;
current.snapshot_label = 'Week 4 · Saturday night · latest market Oct 3 9:45 PM ET';
const by = Object.fromEntries(current.games.map(g => [g.game, g]));

for (const g of current.games) {
  const a = sl.games[g.game], b = ga.games[g.game], c = nf.games[g.game], d = live.games[g.game];
  if (!a || !b || !c || !d) throw new Error(`missing source data for ${g.game}`);
  const x = gridBest(b), y = nfeloBest(c);
  g.current = d.action_spread;
  const diff = liveDiff(g);
  g.diff = diff == null ? '—' : `${diff > 0 ? '+' : ''}${diff.toFixed(1)}`;
  g.weather = d.weather;
  g.marketNote = d.market_note;
  g.sportsline = {
    grade:a.sim_grade, currentPrice:a.current_spread, openPrice:a.open_spread,
    visiblePick:a.sim_pick, kind:a.sim_type, pickCount:a.sportsline_pick_count,
    moneyPct:a.money_pct, simPct:a.sim_pct,
    projectedScore:Object.entries(a.projected).map(([t,p]) => `${t} ${p}`).join(' · ')
  };
  g.gridiron = {
    line:`${b.home} ${signed(b.home_spread)}`,
    away:b.away, awayPct:b.away_cover_pct, home:b.home, homePct:b.home_cover_pct,
    bestSide:x.side, bestPct:x.pct, grade:gradeForPct(x.pct)
  };
  g.nfelo = {
    away:c.away, home:c.home, currentAway:c.current_away, currentHome:c.current_home,
    modelAway:c.model_away, modelHome:c.model_home, evAway:c.ev_away_pct, evHome:c.ev_home_pct,
    bestSide:y.side, bestEv:y.ev, bestCurrent:y.cur, bestModel:y.mod, positiveEdge:y.ev > 0
  };
  g.news = [{detail:d.injuries}];
  g.sources = {sportsline:g.sportsline, gridiron:g.gridiron, nfelo:g.nfelo};
}

const D = {
  'DEN @ SF':['High','Core key-number price value','Best current Sly key-number advantage; nfelo neutral.','External spread models do not independently confirm Denver.'],
  'KC @ LV':['Medium+','Exact-line cross-model alignment','SportsLine B + Gridiron A/57% align exactly on KC -4.5.','No market price edge; nfelo is neutral.'],
  'LAR @ PHI':['Medium+','nfelo model-gap value with injury cap','nfelo PHI +3.5 vs +2.5 model, +14% displayed EV; Sly keeps hook through 3.','Substantial Philadelphia injuries cap exposure.'],
  'ARI @ NYG':['Medium+','Cross-model dog value','Gridiron likes NYG at +1.5 and nfelo models +0.5 vs current +2.5.','SportsLine is total-only here.'],
  'LAC @ SEA':['Medium+','SportsLine football-model core','SportsLine B and ≈60% public cover support at SEA -7.','Current market is now SEA -7.5; Sly -7 is the better contest price.'],
  'IND @ WAS':['Medium','SportsLine price + injury context','Sly -3.5 is now one point better than current IND -4.5 plus Washington QB/OL absences.','Large move has already priced substantial injury news.'],
  'DET @ CAR':['Conflict','nfelo contradiction watch','nfelo CAR +3 vs +3.5 and +5.9% EV make Carolina a real watch.','Gridiron leans DET 51%.'],
  'TEN @ BAL':['Low-Med','Gridiron exact-line watch','Gridiron TEN 52% at +11.5.','Only one spread-model signal.'],
  'JAX @ CIN':['Conflict','External-model disagreement','SportsLine B supports JAX +2.5.','Gridiron leans CIN 51%; nfelo neutral.'],
  'GB @ TB':['Low','Underdog directional watch','Gridiron 51% TB plus SportsLine TB moneyline direction.','SportsLine is not ATS; QB context adverse.'],
  'NE @ BUF':['Low-Med','Key-number value with injury conflict','Sly +7 beats current NE +6.5.','Gridiron BUF 51% and injuries argue against NE.'],
  'ATL @ NO':['Low','Weak external support','SportsLine C and Gridiron direction support ATL.','Gridiron probability is at +3, not Sly +2.5.'],
  'DAL @ HOU':['Conflict','Direct source conflict','Gridiron prefers DAL while SportsLine backs HOU.','No clean side.'],
  'MIA @ MIN':['Line penalty','Strong model at contest price','Gridiron likes MIN -10.5.','Jefferson out; no market price improvement versus Sly.'],
  'NYJ @ CHI':['Mixed','Market-equal injury conflict','Gridiron CHI 52% only.','No price edge; injuries messy.']
};
for (const r of opt.ranking) {
  const g = by[r.game];
  if (!g) throw new Error(`optimizer game missing from current state: ${r.game}`);
  const [confidence, role, whyPlay, against] = D[r.game] || [g.confidence || '—', g.role || '—', g.whyPlay || r.reason, g.against || '—'];
  Object.assign(g, {rank:r.rank, state:r.decision, decision:r.decision, lean:r.pick, confidence, role, whyPlay, against, evidence:r.reason, catherine:0, amanda:0});
}
for (const w of opt.portfolio.Catherine || []) {
  const g = current.games.find(x => x.lean === w.pick); if (g) g.catherine = w.amount;
}
for (const w of opt.portfolio.Amanda || []) {
  const g = current.games.find(x => x.lean === w.pick); if (g) g.amanda = w.amount;
}
current.games.sort((a,b) => a.rank - b.rank);
current.working_portfolio = {...opt.portfolio, status:'SATURDAY_NFELO_RERUN_NOT_SUBMISSION_FINAL'};

const mainSide = Object.fromEntries(current.games.map(g => [g.game, g.lean === 'NO TAKE' ? null : (g.lean || '').split(' ')[0]]));
for (const g of ff.games) {
  const o = g.fiveFactor.overall, m = mainSide[g.game];
  g.mainSystemComparison = {mainSide:m, status:!m ? 'MAIN SYSTEM NO TAKE' : o.leanSide === 'neutral' ? 'FIVE-FACTOR NO EDGE' : o.lean === m ? 'AGREES' : 'DISAGREES'};
}
ff.review = {
  status:'ADVERSARIAL_REVIEWED_WITH_CAVEATS',
  reviewedAt:'2026-10-03T20:40:00-04:00',
  moneySemantics:'DraftKings Spread % Handle only; Bets % excluded',
  defenseCutoff:'Week 4 pregame snapshot',
  correlation:'Line movement and handle can be correlated; raw values remain primary display evidence.',
  atsTrends:'v1 remains locked official Week 4 factor; v2 challenger is shown side-by-side and tracked prospectively.'
};

const grades = {1:'A',2:'A-',3:'A-',4:'B+',5:'B+',6:'B',7:'C+',8:'C+',9:'C',10:'C',11:'C-',12:'C-',13:'—',14:'—',15:'—'};
current.sourceData = current.games.map(g => {
  const a=g.sportsline,b=g.gridiron,c=g.nfelo;
  return {
    game:g.game,time:g.time,sly:g.sly,current:g.current,ourGrade:grades[g.rank],ourPick:g.lean,ourState:g.decision,ourRank:g.rank,
    sportsGrade:a.grade,sportsPick:a.visiblePick,sportsType:a.kind,sportsCurrent:a.currentPrice,
    sportsMoney:Object.entries(a.moneyPct||{}).map(([t,p])=>`${t} ${p}%`).join(' · '),
    sportsSimPct:a.simPct?`${a.simPct.cover_pct}% ${a.simPct.team}`:'not publicly exposed',
    gridGrade:b.grade,gridPick:b.bestSide==='NO TAKE'?'50/50':`${b.bestSide} ${b.bestPct}%`,gridLine:b.line,gridOther:`${b.away} ${b.awayPct}% / ${b.home} ${b.homePct}%`,
    nfeloBest:c.positiveEdge?`${c.bestSide} ${signed(c.bestCurrent)} · model ${signed(c.bestModel)} · EV ${signed(c.bestEv)}%`:'Neutral',
    lucas:'UNVERIFIED / NOT SUPPLIED',agreement:g.evidence
  };
});

function replaceArray(html, name, value) {
  const needle = `const ${name}=`;
  const d = html.indexOf(needle);
  if (d < 0) throw new Error(`local shell missing ${needle}`);
  const start = html.indexOf('[', d + needle.length);
  let depth=0, quote=null, escape=false, end=-1;
  for (let i=start;i<html.length;i++) {
    const ch=html[i];
    if (quote) { if (escape) escape=false; else if (ch==='\\') escape=true; else if (ch===quote) quote=null; continue; }
    if (ch==='"'||ch==="'"||ch==='`') { quote=ch; continue; }
    if (ch==='[') depth++;
    else if (ch===']' && --depth===0) { end=i+1; break; }
  }
  if (end < 0) throw new Error(`could not replace ${name}`);
  return html.slice(0,start) + JSON.stringify(value) + html.slice(end);
}
function allocation(g) {
  const parts=[];
  if (g.catherine) parts.push(`Catherine ${money(g.catherine)}`);
  if (g.amanda) parts.push(`Amanda ${money(g.amanda)}`);
  return parts.join(' · ') || 'No working allocation';
}
function decisionClass(d) { return d==='PLAY' ? 'play' : d==='WATCH' ? 'watch' : 'pass'; }
function renderToday() {
  const games=current.games;
  const top=games.slice(0,6);
  const alerts=games.slice(0,4).map(g => `<div class="alert ${g.decision==='PLAY'?'green':g.decision==='PASS'?'red':''}"><span class="dot"></span><div><b>${esc(g.lean)} · ${esc(g.decision)}</b><br/>Sly ${esc(g.sly)} · latest market ${esc(g.current)} · ${esc(g.whyPlay)}</div></div>`).join('');
  const cards=top.map(g => `<button class="play-card" data-game="${esc(g.game)}"><div class="play-top"><span class="rank-badge">#${g.rank}</span><span class="decision-chip ${decisionClass(g.decision)}">${esc(g.decision)} · ${esc(g.confidence)}</span></div><h3>${esc(g.lean)}</h3><div class="matchup">${esc(g.game)} · ${esc(g.time)}</div><div class="mini-line"><span>Sly <b>${esc(g.sly)}</b></span><span>Market <b>${esc(g.current)}</b></span><span>DIFF <b>${esc(g.diff)}</b></span></div><p><b>Why:</b> ${esc(g.whyPlay)}</p><p class="risk"><b>Risk:</b> ${esc(g.against)}</p><div class="alloc-line">${esc(allocation(g))}</div><div class="open-link">Open game →</div></button>`).join('');
  return `<section class="view active" id="today" data-week="4" data-render-source="server-local">
<div class="hero-grid"><div class="panel slate-state"><div class="eyebrow">Current operating picture</div><div class="state-title">Week 4 · Saturday night</div><div class="state-sub">15 Sly lines frozen · latest market captured Oct 3 at 9:45 PM ET · model/source layers reconciled</div>
<div class="kpis"><div class="kpi"><small>Catherine</small><b>${money(current.balances.Catherine)}</b><span>#28 after Week 3</span></div><div class="kpi"><small>Amanda</small><b>${money(current.balances.Amanda)}</b><span>#65 after Week 3</span></div><div class="kpi"><small>Household outlay</small><b>${money(current.working_portfolio.household_outlay)}</b><span>current working portfolio</span></div><div class="kpi"><small>Market snapshot</small><b>9:45 PM ET</b><span>${esc(latest.source)}</span></div></div>
</div><div class="panel"><div class="eyebrow">Needs attention</div><div class="alerts">${alerts}<div class="alert"><span class="dot"></span><div><b>Sly remains the contest line.</b><br/>Current market is context only; Sunday inactive/news checks remain before submission.</div></div></div></div></div>
<div class="section-head"><div><div class="eyebrow">Recommended plays</div><h2>Decision board</h2><p>Week 4 ranking using current model, price and source evidence.</p></div></div>
<div class="play-grid" id="recommendedPlays">${cards}</div>
<div class="section-head news-intel-head"><div><div class="eyebrow">News intelligence</div><h2>What changed / what matters</h2><p>Latest verified Week 4 context; use game detail for full source comparison.</p></div><div class="news-freshness">Latest market · Oct 3 9:45 PM ET<br/><b>Sunday inactives / late movement remain</b></div></div>
<div class="today-news-intel" id="todayNewsIntel"></div>
</section>`;
}
function renderPortfolio() {
  const p=current.working_portfolio;
  const card=(name,arr)=>`<div class="panel entry-card"><div class="eyebrow">${name}</div><h3>${money((arr||[]).reduce((s,w)=>s+w.amount,0))} · ${(arr||[]).length} games</h3><div class="wager-list">${(arr||[]).map(w=>`<div class="wager"><b>${esc(w.pick)}</b><span>${money(w.amount)}</span></div>`).join('')}</div></div>`;
  return `<section class="view" id="portfolio"><div class="section-head"><div><div class="eyebrow">Household strategy</div><h2>Portfolio</h2><p>Week 4 working sizing · two entries, one coordinated risk picture.</p></div></div><div class="panel" style="margin-bottom:10px;border-color:#315d52;background:#0d211d"><div class="eyebrow">Current working portfolio</div><b style="display:block;font-size:18px;margin-top:3px">${money(p.household_outlay)} household outlay</b><p style="font-size:10px;color:#9db3aa;margin:5px 0 0">Sizing remains downstream of the current recommendation board and has not been silently changed by the latest market refresh.</p></div><div class="portfolio-grid">${card('Catherine',p.Catherine)}${card('Amanda',p.Amanda)}</div></section>`;
}
function replaceCoreViews(html) {
  html = html.replace(/<div class="snapshot">[\s\S]*?<\/div><\/div>\s*<nav class="primary-nav">/, `<div class="snapshot"><b>Week 4 · Saturday night</b><br/>Sly frozen · latest market Oct 3 · 9:45 PM ET · local canonical shell</div></div>\n<nav class="primary-nav">`);
  html = html.replace(/<section class="view active" id="today">[\s\S]*?<\/section>\s*<section class="view" id="games">/, `${renderToday()}\n<section class="view" id="games">`);
  html = html.replace(/<section class="view" id="portfolio">[\s\S]*?<\/section>\s*<section class="view" id="lab">/, `${renderPortfolio()}\n<section class="view" id="lab">`);
  return html;
}

let cache=null;
function buildApp() {
  if (cache) return cache;
  let html=shellTemplate;
  html=replaceArray(html,'games',current.games);
  html=replaceArray(html,'sourceData',current.sourceData);
  html=replaceCoreViews(html);
  const globals=`<script>window.COMMAND_CENTER_ARCHITECTURE='local-shell-v1';window.WEEK4_CURRENT_META=${JSON.stringify({version:current.version,captured_at_local:current.captured_at_local,snapshot_label:current.snapshot_label,balances:current.balances,working_portfolio:current.working_portfolio})};window.WEEK4_CURRENT_PUBLIC=${JSON.stringify(current.games)};window.WEEK4_SOURCE_PUBLIC=${JSON.stringify(current.sourceData)};window.FIVE_FACTOR_PUBLIC=${JSON.stringify(ff)};window.ATS_TRENDS_V2_PUBLIC=${JSON.stringify(atsV2)};window.ATS_TRENDS_LEDGER_PUBLIC=${JSON.stringify(atsLedger)};</script>`;
  html=html.replace('</body>',`${globals}\n${patches}\n</body>`);
  const today=html.match(/<section class="view active" id="today"[\s\S]*?<\/section>/)?.[0] || '';
  if (!today.includes('Week 4 · Saturday night')) throw new Error('Week 4 Today render contract failed');
  if (today.includes('Week 3 · Saturday')) throw new Error('stale Week 3 Today content survived server render');
  cache=html;
  return cache;
}

const appHtml=buildApp();
const server=http.createServer((req,res)=>{
  const url=new URL(req.url,'http://local');
  if (url.pathname==='/_version') {
    res.writeHead(200,{'content-type':'application/json','cache-control':'no-store'});
    return res.end(JSON.stringify({status:'ok',version:current.version,architecture:'local-shell-v1',shell:'command-center-shell.html',remoteShellFetch:false,week:4,marketCapturedAt:latest.capturedAt,householdOutlay:current.working_portfolio.household_outlay}));
  }
  if (url.pathname==='/healthz') {
    const today=appHtml.match(/<section class="view active" id="today"[\s\S]*?<\/section>/)?.[0] || '';
    const checks={localShell:true,noRemoteFetch:true,games15:current.games.length===15,latestMarket:current.captured_at_local===latest.capturedAt,week4Today:today.includes('Week 4 · Saturday night'),noStaleWeek3Today:!today.includes('Week 3 · Saturday'),balances:today.includes('$10,800')&&today.includes('$8,700'),portfolio:current.working_portfolio.household_outlay===3800,overviewPatch:patches.includes('week4-overview-page-script'),fiveFactor15:ff.games.length===15};
    const ok=Object.values(checks).every(Boolean);
    res.writeHead(ok?200:503,{'content-type':'application/json','cache-control':'no-store'});
    return res.end(JSON.stringify({status:ok?'ok':'error',version:current.version,architecture:'local-shell-v1',checks}));
  }
  res.writeHead(200,{'content-type':'text/html; charset=utf-8','cache-control':'no-store, no-cache, must-revalidate, max-age=0','pragma':'no-cache','expires':'0','x-command-center-architecture':'local-shell-v1','x-command-center-week':'4'});
  res.end(appHtml);
});
server.listen(port,'0.0.0.0',()=>console.log(`Command Center ${current.version} local-shell-v1 on ${port}`));
