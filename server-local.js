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

current.version = 'week4-local-shell-v2-decision-chain-2026-10-04';
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
  const ffBy=Object.fromEntries((ff.games||[]).map(x=>[x.game,x]));
  const atsRows=(atsLedger.games||atsLedger.entries||atsLedger.predictions||[]);
  const atsBy=Object.fromEntries(atsRows.map(x=>[x.game,x]));

  function leanTeam(g){return g.lean==='NO TAKE'?null:String(g.lean||'').split(' ')[0];}
  function pickTeam(v){const m=String(v||'').match(/^([A-Z]{2,4})\b/);return m?m[1]:null;}
  function priceRead(g){
    const team=leanTeam(g); if(!team) return {kind:'neutral',headline:'No primary side',detail:'No price comparison because the primary system has no take.'};
    const s=lineForTeam(g.sly,team), c=lineForTeam(g.current,team);
    if(s==null||c==null) return {kind:'neutral',headline:'Price unclear',detail:'Current market format does not support a clean numeric Sly comparison.'};
    const edge=+(s-c).toFixed(1);
    const abs=Math.abs(s); const key=[3,7,10,14].includes(abs)?' · key '+abs:'';
    if(edge>0) return {kind:'good',headline:'Sly '+edge.toFixed(1)+' pt better'+key,detail:'Sly '+signed(s)+' vs current '+signed(c)+' for '+team+'.'};
    if(edge<0) return {kind:'bad',headline:'Sly '+Math.abs(edge).toFixed(1)+' pt worse'+key,detail:'Sly '+signed(s)+' vs current '+signed(c)+' for '+team+'.'};
    return {kind:'neutral',headline:'Market equal',detail:'Sly and current market are both '+signed(s)+' for '+team+'.'};
  }
  function externalRead(g){
    const team=leanTeam(g), rows=[];
    const sp=pickTeam(g.sportsline?.visiblePick);
    rows.push({name:'SportsLine',side:sp||'—',state:!sp?'na':sp===team?'support':'oppose',detail:g.sportsline?.visiblePick||g.sportsline?.kind||'No ATS side'});
    const gr=g.gridiron?.bestSide && g.gridiron.bestSide!=='NO TAKE'?g.gridiron.bestSide:null;
    rows.push({name:'Gridiron',side:gr||'—',state:!gr?'na':gr===team?'support':'oppose',detail:gr?gr+' '+g.gridiron.bestPct+'%':'No edge'});
    const nfside=g.nfelo?.positiveEdge?g.nfelo.bestSide:null;
    rows.push({name:'nfelo',side:nfside||'—',state:!nfside?'na':nfside===team?'support':'oppose',detail:nfside?nfside+' EV '+signed(g.nfelo.bestEv)+'%':'Neutral'});
    rows.push({name:'4for4',side:'—',state:'context',detail:'Context only · not an ATS vote'});
    rows.push({name:'Lucas',side:'—',state:'na',detail:'Unverified / not supplied'});
    return rows;
  }
  function flat(obj,prefix='',out=[]){
    if(obj==null) return out;
    if(typeof obj!=='object'){out.push([prefix,obj]);return out;}
    for(const [k,v] of Object.entries(obj)){const p=prefix?prefix+'.'+k:k;if(v&&typeof v==='object')flat(v,p,out);else out.push([p,v]);}
    return out;
  }
  function fiveRead(g){
    const row=ffBy[g.game];
    const cmp=row?.mainSystemComparison?.status||'UNAVAILABLE';
    const state=cmp==='AGREES'?'support':cmp==='DISAGREES'?'oppose':'mixed';
    const all=flat(row?.fiveFactor||row||{});
    const money=all.find(([k,v])=>typeof v==='number'&&/(money|handle).*(pct|percent)|(pct|percent).*(money|handle)/i.test(k));
    const ranks=all.filter(([k,v])=>typeof v==='number'&&/defen.*rank|rank.*defen/i.test(k)).slice(0,2);
    const ats=atsBy[g.game]||{};
    const v1=ats.v1Lean||ats.v1?.lean||ats.v1_pick||ats.v1Side||'—';
    const v2=ats.v2Lean||ats.v2?.lean||ats.v2_pick||ats.v2Side||'—';
    const details=[g.open?'Open '+g.open+' → current '+g.current:null,money?'Money '+money[1]+'%':null,ranks.length?('Defense '+ranks.map(x=>String(x[1])).join(' vs ')):null,'ATS v1 '+v1+' · v2 '+v2].filter(Boolean);
    return {state,headline:state==='support'?'Supportive diagnostic':state==='oppose'?'Opposing diagnostic':'Mixed diagnostic',detail:details.join(' · '),cmp};
  }
  function contextRead(g){
    const injury=g.news?.[0]?.detail||'No material verified injury note in current state.';
    const weather=g.weather||'No material weather flag.';
    return injury+' Weather: '+weather;
  }
  function decisionLabel(g,p,ext,five){
    const support=ext.filter(x=>x.state==='support').length, oppose=ext.filter(x=>x.state==='oppose').length;
    if(g.decision==='PLAY'){
      if(p.kind==='good'&&support>=1) return 'PLAY — Model + Price';
      if(support>=2) return 'PLAY — Broad Confirmation';
      if(p.kind==='good') return 'PLAY — Price Opportunity';
      return 'PLAY — Model Edge';
    }
    if(g.decision==='WATCH'){
      if(p.kind==='bad') return 'MIXED — Price Penalty';
      if(oppose>0||five.state==='oppose') return 'MIXED — Model Conflict';
      return 'MIXED — Needs Confirmation';
    }
    if(p.kind==='bad') return 'PASS — Bad Price';
    if(oppose>=1||five.state==='oppose') return 'PASS — Major Contradiction';
    return 'PASS — Insufficient Edge';
  }
  function sourceHtml(x){const icon=x.state==='support'?'✓':x.state==='oppose'?'×':'—';return '<div class="dc-source '+(x.state==='support'?'mc':x.state==='oppose'?'gr':'')+'"><small>'+esc(x.name)+'</small><b>'+icon+' '+esc(x.side)+'</b><span>'+esc(x.detail)+'</span></div>';}
  function chainCard(g){
    const p=priceRead(g), ext=externalRead(g), five=fiveRead(g), label=decisionLabel(g,p,ext,five);
    const cls=g.decision==='PLAY'?'play':g.decision==='WATCH'?'watch':'pass';
    return '<article class="panel decision-chain-card" data-game="'+esc(g.game)+'">'+
      '<div class="chain-head"><div><div class="eyebrow">#'+g.rank+' · '+esc(g.game)+' · '+esc(g.time)+'</div><h3>'+esc(g.lean)+'</h3></div><span class="decision-chip '+cls+'">'+esc(label)+'</span></div>'+
      '<div class="decision-chain">'+
        '<div class="chain-step"><small>1 · Prediction</small><b>'+esc(g.lean)+'</b><span>'+esc(g.confidence)+' · '+esc(g.role)+'</span></div>'+
        '<div class="chain-step '+p.kind+'"><small>2 · Price</small><b>'+esc(p.headline)+'</b><span>'+esc(p.detail)+'</span></div>'+
        '<div class="chain-step"><small>3 · Independent confirmation</small><div class="chain-sources">'+ext.map(sourceHtml).join('')+'</div></div>'+
        '<div class="chain-step '+five.state+'"><small>4 · 5-Factor diagnostic</small><b>'+esc(five.headline)+'</b><span>'+esc(five.detail||'Raw factor details available on 5-Factor page.')+'</span><em>Diagnostic only · 100-point score is audit-only, not another vote.</em></div>'+
        '<div class="chain-step"><small>5 · Material context</small><b>'+esc(g.against||'No material contradiction')+'</b><span>'+esc(contextRead(g))+'</span></div>'+
        '<div class="chain-step final"><small>6 · Decision</small><b>'+esc(label)+'</b><span>'+esc(g.whyPlay)+'</span></div>'+
      '</div>'+
      '<div class="chain-stake"><small>Stake comes last</small><b>'+esc(allocation(g))+'</b><span>Portfolio sizing is downstream of the decision; it is not evidence for the pick.</span></div>'+
    '</article>';
  }

  const cards=games.map(chainCard).join('');
  const styles='<style id="decision-chain-styles">.today-rule{margin:10px 0 16px;padding:11px 12px;border:1px solid #214055;background:#0b1b29;border-radius:11px;font-size:10px;color:#9eb3c4}.today-rule b{color:#fff}.decision-chain-list{display:grid;gap:10px}.decision-chain-card{padding:13px}.chain-head{display:flex;justify-content:space-between;gap:10px;align-items:flex-start}.chain-head h3{font-size:20px;margin:3px 0 0}.decision-chain{display:grid;grid-template-columns:1fr 1fr;gap:7px;margin-top:11px}.chain-step{background:#091725;border:1px solid #1d3549;border-radius:9px;padding:9px;min-width:0}.chain-step small,.chain-stake small{display:block;color:#718ca1;font-size:7px;text-transform:uppercase;font-weight:950;letter-spacing:.05em}.chain-step b{display:block;font-size:11px;margin-top:3px}.chain-step span{display:block;font-size:9px;color:#91a7b9;margin-top:3px;line-height:1.35}.chain-step em{display:block;font-size:8px;color:#70879a;font-style:normal;margin-top:5px}.chain-step.good{border-color:#285844}.chain-step.bad,.chain-step.oppose{border-color:#5a3436}.chain-step.support{border-color:#285844}.chain-step.final{background:#0d2430;border-color:#31536a}.chain-sources{display:grid;grid-template-columns:repeat(5,minmax(0,1fr));gap:5px;margin-top:6px}.chain-sources .dc-source{padding:6px}.chain-sources .dc-source small{font-size:7px}.chain-sources .dc-source b{font-size:9px}.chain-sources .dc-source span{font-size:7px}.chain-stake{display:grid;grid-template-columns:130px 1fr 2fr;gap:10px;align-items:center;border-top:1px solid #1b3146;margin-top:9px;padding-top:9px}.chain-stake b{font-size:11px;color:#70dda8}.chain-stake span{font-size:9px;color:#8198aa}@media(max-width:800px){.decision-chain{grid-template-columns:1fr}.chain-sources{grid-template-columns:1fr 1fr}.chain-stake{grid-template-columns:1fr}.chain-head{display:grid}.decision-chip{width:max-content}}</style>';
  return '<section class="view active" id="today" data-week="4" data-render-source="server-local" data-decision-framework="prediction-price-confirmation-fivefactor-context-decision">'+styles+
    '<div class="hero-grid"><div class="panel slate-state"><div class="eyebrow">Current operating picture</div><div class="state-title">Week 4 · Saturday night</div><div class="state-sub">Interpret every game in the same order: prediction → price → confirmation → diagnostic evidence → material context → decision → stake.</div><div class="kpis"><div class="kpi"><small>Catherine</small><b>'+money(current.balances.Catherine)+'</b><span>#28 after Week 3</span></div><div class="kpi"><small>Amanda</small><b>'+money(current.balances.Amanda)+'</b><span>#65 after Week 3</span></div><div class="kpi"><small>Household outlay</small><b>'+money(current.working_portfolio.household_outlay)+'</b><span>current working portfolio</span></div><div class="kpi"><small>Market snapshot</small><b>9:45 PM ET</b><span>'+esc(latest.source)+'</span></div></div></div><div class="panel"><div class="eyebrow">How to read Today</div><div class="alerts"><div class="alert green"><span class="dot"></span><div><b>Prediction starts the chain.</b><br/>Our primary system establishes the side; the other evidence does not get one equal vote each.</div></div><div class="alert"><span class="dot"></span><div><b>Price is a gate, not a vote.</b><br/>Sly versus current market can upgrade or degrade an otherwise attractive side.</div></div><div class="alert"><span class="dot"></span><div><b>5-Factor is diagnostic.</b><br/>Raw line movement, money, defense and ATS context explain the bet; the 100-point score stays audit-only.</div></div></div></div></div>'+
    '<div class="today-rule"><b>No master consensus score.</b> SportsLine, Gridiron, nfelo, 4for4 and Lucas are shown separately so correlated or unavailable evidence cannot masquerade as independent certainty.</div>'+
    '<div class="section-head"><div><div class="eyebrow">Decision chain</div><h2>All 15 games</h2><p>Ranked by the current primary system. Open a game for the full evidence trail.</p></div></div><div class="decision-chain-list" id="todayDecisionChain">'+cards+'</div></section>';
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
    const checks={localShell:true,noRemoteFetch:true,games15:current.games.length===15,latestMarket:current.captured_at_local===latest.capturedAt,week4Today:today.includes('Week 4 · Saturday night'),noStaleWeek3Today:!today.includes('Week 3 · Saturday'),balances:today.includes('$10,800')&&today.includes('$8,700'),portfolio:current.working_portfolio.household_outlay===3800,overviewPatch:patches.includes('week4-overview-page-script'),fiveFactor15:ff.games.length===15,decisionChain:today.includes('Prediction')&&today.includes('2 · Price')&&today.includes('3 · Independent confirmation')&&today.includes('4 · 5-Factor diagnostic')&&today.includes('5 · Material context')&&today.includes('6 · Decision')&&today.includes('Stake comes last')};
    const ok=Object.values(checks).every(Boolean);
    res.writeHead(ok?200:503,{'content-type':'application/json','cache-control':'no-store'});
    return res.end(JSON.stringify({status:ok?'ok':'error',version:current.version,architecture:'local-shell-v1',checks}));
  }
  res.writeHead(200,{'content-type':'text/html; charset=utf-8','cache-control':'no-store, no-cache, must-revalidate, max-age=0','pragma':'no-cache','expires':'0','x-command-center-architecture':'local-shell-v1','x-command-center-week':'4'});
  res.end(appHtml);
});
server.listen(port,'0.0.0.0',()=>console.log(`Command Center ${current.version} local-shell-v1 on ${port}`));
