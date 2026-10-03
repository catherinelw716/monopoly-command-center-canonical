const fs=require('fs');
const vm=require('vm');
function read(p){return fs.readFileSync(p,'utf8');}
function json(p){return JSON.parse(read(p));}
function assert(cond,msg){if(!cond)throw new Error(msg);}
function setEq(a,b){return a.size===b.size&&[...a].every(x=>b.has(x));}
function extractObject(text,startMarker,endMarker){
 const start=text.indexOf(startMarker);assert(start>=0,`Missing marker ${startMarker}`);
 const bodyStart=start+startMarker.length;const end=text.indexOf(endMarker,bodyStart);assert(end>bodyStart,`Missing end marker ${endMarker}`);
 return vm.runInNewContext('('+text.slice(bodyStart,end)+')');
}
function signed(n){return n>0?`+${n}`:`${n}`;}
function gridironExpected(snapshot){
 const out={};for(const [id,d] of Object.entries(snapshot.games))out[id]={spread:`${d.home} ${signed(d.home_spread)}`,away:d.away,awayPct:d.away_cover_pct,home:d.home,homePct:d.home_cover_pct};return out;
}
function sameGridiron(a,b){
 const ak=new Set(Object.keys(a)),bk=new Set(Object.keys(b));assert(setEq(ak,bk),'Gridiron hard-coded game set differs from canonical snapshot');
 for(const id of ak){for(const k of ['spread','away','awayPct','home','homePct'])assert(a[id][k]===b[id][k],`Gridiron drift ${id} ${k}: ${a[id][k]} != ${b[id][k]}`);}
}
const state=json('week4-current-data.json');
const sl=json('week4-sportsline-2026-10-03-1611ET.json');
const ga=json('week4-gridiron-2026-10-03.json');
const viewMap=json('command-center-view-map.json');
const mobile=read('mobile-patch.html');
const detail=read('game-detail-ui-patch.html');
const sportsPatch=read('week4-sportsline-integration-patch.html');
const server=read('server.js');
const ids=new Set(state.games.map(g=>g.game));
assert(ids.size===15,'Week 4 state must contain exactly 15 eligible games');
assert(state.sourceData.length===15,'sourceData must contain exactly 15 rows');
assert(setEq(ids,new Set(state.sourceData.map(x=>x.game))),'games/sourceData game sets differ');
assert(setEq(ids,new Set(Object.keys(sl.games))),'SportsLine snapshot does not cover exactly the 15 eligible games');
assert(setEq(ids,new Set(Object.keys(ga.games))),'Gridiron snapshot does not cover exactly the 15 eligible games');
assert(!ids.has('PIT @ CLE'),'PIT @ CLE must remain excluded without an official Sly line');
for(const [name,v] of Object.entries(viewMap.views)){assert(v.selector&&v.required?.length,`View map incomplete for ${name}`);}
assert(mobile.includes('#recommendedPlays'),'Decision Board recommended selector missing from mobile patch');
assert(mobile.includes('document.getElementById(\'games\')'),'Decision Board all-games selector missing from mobile patch');
assert(mobile.includes('sourceCompareBody'),'Source table selector missing from Gridiron patch');
assert(detail.includes('gridironGameRead'),'Gridiron deep-dive component missing');
assert(detail.includes('slGameRead'),'SportsLine deep-dive dependency missing');
assert(sportsPatch.includes('sourceCompareBody'),'SportsLine source-table integration missing');
assert(server.includes("week4-sportsline-2026-10-03-1611ET.json"),'Server is not loading canonical SportsLine snapshot');
assert(mobile.includes("p>=55?'A':p>=52?'B':p>=51?'C':'N'"),'Gridiron grade bands changed without contract update');
const mobileG=extractObject(mobile,'const G=',';\n function norm');
const expected=gridironExpected(ga);sameGridiron(mobileG,expected);
const detailG=extractObject(detail,'const DATA=',';\n window.WEEK4_GRIDIRON_SPREADS');
for(const id of ids){const d=detailG[id],e=ga.games[id];assert(d,`Deep-dive Gridiron missing ${id}`);assert(d.away===e.away&&d.home===e.home&&d.homeSpread===e.home_spread&&d.awayPct===e.away_cover_pct&&d.homePct===e.home_cover_pct,`Deep-dive Gridiron drift for ${id}`);}
const requiredTokens=['gridiron-games-chip','gridiron-grade','Gridiron AI · grade / cover %'];for(const t of requiredTokens)assert(mobile.includes(t),`Missing Decision Board/source-table Gridiron token: ${t}`);
console.log('Command Center consistency QA passed');
console.log(`15/15 games consistent across Week4 state, SportsLine and Gridiron snapshots.`);
console.log(`View contract covers ${Object.keys(viewMap.views).length} major surfaces.`);
