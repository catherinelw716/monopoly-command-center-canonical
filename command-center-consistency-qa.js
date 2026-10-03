const fs=require('fs');
const vm=require('vm');
function read(p){return fs.readFileSync(p,'utf8');}
function json(p){return JSON.parse(read(p));}
function assert(cond,msg){if(!cond)throw new Error(msg);}
function setEq(a,b){return a.size===b.size&&[...a].every(x=>b.has(x));}
function extractObject(text,startMarker,endMarker){const start=text.indexOf(startMarker);assert(start>=0,`Missing marker ${startMarker}`);const bodyStart=start+startMarker.length;const end=text.indexOf(endMarker,bodyStart);assert(end>bodyStart,`Missing end marker ${endMarker}`);return vm.runInNewContext('('+text.slice(bodyStart,end)+')');}
function signed(n){return n>0?`+${n}`:`${n}`;}
function gridironExpected(snapshot){const out={};for(const [id,d] of Object.entries(snapshot.games))out[id]={spread:`${d.home} ${signed(d.home_spread)}`,away:d.away,awayPct:d.away_cover_pct,home:d.home,homePct:d.home_cover_pct};return out;}
function sameGridiron(a,b){const ak=new Set(Object.keys(a)),bk=new Set(Object.keys(b));assert(setEq(ak,bk),'Gridiron hard-coded game set differs from canonical snapshot');for(const id of ak){for(const k of ['spread','away','awayPct','home','homePct'])assert(a[id][k]===b[id][k],`Gridiron drift ${id} ${k}: ${a[id][k]} != ${b[id][k]}`);}}
function gridGrade(p){return p>=55?'A':p>=52?'B':p>=51?'C':'N';}
function renderedGridiron(id,d){const pct=Math.max(d.away_cover_pct,d.home_cover_pct);const tie=d.away_cover_pct===d.home_cover_pct;const side=tie?'50/50 · no model edge':(d.away_cover_pct>d.home_cover_pct?`${d.away} ${d.away_cover_pct}% cover`:`${d.home} ${d.home_cover_pct}% cover`);return `Gridiron ${gridGrade(pct)} · ${side} · ${d.home} ${signed(d.home_spread)} · ${d.away} ${d.away_cover_pct}% / ${d.home} ${d.home_cover_pct}%`;}

const state=json('week4-current-data.json');
const sl=json('week4-sportsline-2026-10-03-1611ET.json');
const ga=json('week4-gridiron-2026-10-03.json');
const live=json('week4-live-market-context-2026-10-03-1710ET.json');
const viewMap=json('command-center-view-map.json');
const mobile=read('mobile-patch.html');
const mobileNav=read('mobile-nav-fix.html');
const detail=read('game-detail-ui-patch.html');
const sportsPatch=read('week4-sportsline-integration-patch.html');
const server=read('server.js');
const ids=new Set(state.games.map(g=>g.game));

assert(ids.size===15,'Week 4 state must contain exactly 15 eligible games');
assert(setEq(ids,new Set(Object.keys(sl.games))),'SportsLine snapshot does not cover exactly 15 eligible games');
assert(setEq(ids,new Set(Object.keys(ga.games))),'Gridiron snapshot does not cover exactly 15 eligible games');
assert(setEq(ids,new Set(Object.keys(live.games))),'Live market/context snapshot does not cover exactly 15 eligible games');
assert(!ids.has('PIT @ CLE'),'PIT @ CLE must remain excluded without an official Sly line');

for(const [id,d] of Object.entries(sl.games)){
  assert(d.current_spread,`SportsLine current spread missing ${id}`);
  assert(d.money_pct&&Object.values(d.money_pct).reduce((a,b)=>a+b,0)===100,`SportsLine money % invalid ${id}`);
  assert(['Spread','Moneyline','Total'].includes(d.sim_type),`SportsLine SIM type invalid ${id}`);
}
assert(sl.games['LAC @ SEA'].sim_pct?.cover_pct===60,'Verified SEA SportsLine numeric SIM % missing');
for(const [id,d] of Object.entries(live.games)){
  assert(d.action_spread,`Live Action spread missing ${id}`);
  assert(d.weather,`Weather missing ${id}`);
  assert(d.injuries,`Official injury summary missing ${id}`);
  assert(d.market_note,`Market note missing ${id}`);
}

for(const [name,v] of Object.entries(viewMap.views))assert(v.selector&&v.required?.length,`View map incomplete for ${name}`);
assert(server.includes("week4-live-market-context-2026-10-03-1710ET.json"),'Server not loading latest live snapshot');
assert(server.includes("week4-gridiron-2026-10-03.json"),'Server not loading canonical Gridiron snapshot');
assert(server.includes("week4-sportsline-2026-10-03-1611ET.json"),'Server not loading canonical SportsLine snapshot');
assert(server.includes("week4-native-v6-2026-10-03-1710ET"),'Server version is stale');
assert(server.includes('moneyPct: sl.money_pct'),'SportsLine money % not normalized into game state');
assert(server.includes('gridiron: g.gridiron'),'Gridiron not normalized into game.sources');
assert(server.includes('weather:g.weather'),'Source rows do not retain weather/current state');

assert(sportsPatch.includes('SportsLine · spread / money / SIM'),'Source table missing SportsLine spread/money/SIM contract');
assert(sportsPatch.includes('Gridiron · grade / cover %'),'Source table missing Gridiron grade/cover contract');
assert(sportsPatch.includes('moneyText(sl)'),'Deep dive not reading normalized SportsLine money %');
assert(sportsPatch.includes('simPctText(sl)'),'Deep dive not reading normalized SportsLine SIM %');
assert(sportsPatch.includes('x.weather'),'Deep dive not reading normalized weather');
assert(sportsPatch.includes('x.news?.[0]?.detail'),'Deep dive not reading normalized injuries');

assert(mobile.includes('#recommendedPlays'),'Decision Board recommended selector missing');
assert(mobile.includes("document.getElementById('games')"),'Decision Board all-games selector missing');
assert(mobile.includes('sourceCompareBody'),'Source table selector missing from Gridiron patch');
assert(detail.includes('gridironGameRead'),'Gridiron deep-dive component missing');
assert(detail.includes('slGameRead'),'SportsLine deep-dive dependency missing');
assert(mobile.includes("p>=55?'A':p>=52?'B':p>=51?'C':'N'"),'Gridiron grade bands changed without contract update');

const mobileG=extractObject(mobile,'const G=',';\n function norm');
const expected=gridironExpected(ga);sameGridiron(mobileG,expected);
const detailG=extractObject(detail,'const DATA=',';\n window.WEEK4_GRIDIRON_SPREADS');
for(const id of ids){const d=detailG[id],e=ga.games[id];assert(d,`Deep-dive Gridiron missing ${id}`);assert(d.away===e.away&&d.home===e.home&&d.homeSpread===e.home_spread&&d.awayPct===e.away_cover_pct&&d.homePct===e.home_cover_pct,`Deep-dive Gridiron drift ${id}`);}

for(const token of ['gridiron-games-chip','gridiron-grade','Gridiron AI · grade / cover %'])assert(mobile.includes(token),`Missing Decision Board/source-table Gridiron token: ${token}`);

// Render-contract protection: source consistency is not enough. Every canonical Gridiron
// record must produce a complete display string, ties must have an explicit neutral label,
// and the runtime guard must repair stale-schema/undefined renderers after any re-render.
for(const [id,d] of Object.entries(ga.games)){
  const out=renderedGridiron(id,d);
  assert(!/undefined|null|\[object Object\]/i.test(out),`Gridiron render contract emits invalid token for ${id}: ${out}`);
  assert(/\d+%/.test(out),`Gridiron render contract missing percentage for ${id}`);
  assert(out.includes(d.home)&&out.includes(d.away),`Gridiron render contract missing teams for ${id}`);
  if(d.away_cover_pct===d.home_cover_pct)assert(out.includes('N · 50/50 · no model edge'),`Tie game must render neutral state for ${id}`);
}
assert(renderedGridiron('DEN @ SF',ga.games['DEN @ SF']).includes('N · 50/50 · no model edge'),'DEN/SF edge-case render failed');
assert(renderedGridiron('KC @ LV',ga.games['KC @ LV']).includes('A · KC 57% cover'),'KC/LV directional render failed');
assert(mobileNav.includes('gridiron-render-contract-guard'),'Runtime Gridiron render guard missing');
assert(mobileNav.includes("const BAD=/\\b(undefined|null|\\[object Object\\])\\b/i"),'Runtime invalid-token guard missing');
assert(mobileNav.includes('window.runGridironRenderContractQA'),'Runtime Gridiron QA hook missing');
assert(mobileNav.includes('sourceRowsValid'),'Runtime source-table completeness check missing');
assert(mobileNav.includes('MutationObserver'),'Gridiron guard must survive tab/card re-renders');

console.log('Command Center consistency + render-contract QA passed');
console.log('15/15 games consistent across Sly state, SportsLine, Gridiron and live market/context snapshots.');
console.log('15/15 Gridiron records have deterministic non-undefined render strings, including 50/50 and directional edge cases.');
