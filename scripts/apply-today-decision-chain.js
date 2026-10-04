'use strict';
const fs = require('fs');

const path = 'server-local.js';
let src = fs.readFileSync(path, 'utf8');

const start = src.indexOf('function renderToday() {');
const end = src.indexOf('function renderPortfolio() {');
if (start < 0 || end < 0 || end <= start) throw new Error('renderToday boundaries not found');

const replacement = String.raw`function renderToday() {
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
`;

src = src.slice(0, start) + replacement + '\n' + src.slice(end);
src = src.replace(/week4-local-shell-v1-2026-10-04/g, 'week4-local-shell-v2-decision-chain-2026-10-04');
src = src.replace("fiveFactor15:ff.games.length===15", "fiveFactor15:ff.games.length===15,decisionChain:today.includes('Prediction')&&today.includes('2 · Price')&&today.includes('3 · Independent confirmation')&&today.includes('4 · 5-Factor diagnostic')&&today.includes('5 · Material context')&&today.includes('6 · Decision')&&today.includes('Stake comes last')");
fs.writeFileSync(path, src);
console.log('Applied server-rendered Today decision-chain framework.');
