'use strict';
const http=require('http'),fs=require('fs');
const {predict}=require('./week05-model');
const port=Number(process.env.PORT||10000);
const input=JSON.parse(fs.readFileSync('./week05-canonical-data.json','utf8'));
const standings=JSON.parse(fs.readFileSync('./week05-standings.json','utf8'));
const html=fs.readFileSync('./week05-command-center.html','utf8');
const sl=JSON.parse(fs.readFileSync('./week05-sportsline-user-screenshot-2026-10-09.json','utf8'));
function normalizeSportsline(g) {
 const record=sl.games[g.id];
 if(!record)throw Error('SportsLine screenshot match missing: '+g.id);
 const away=g.away,home=g.home;
 const expected=record.sim.side===g.favorite?g.slyFavoriteSpread:-g.slyFavoriteSpread;
 const ats=record.sim.type==='ATS';
 const exact=ats&&Math.abs(record.sim.value-expected)<1e-9;
 return {...record,sim:{...record.sim,exactSlyLine:exact,
  slyReference:ats?record.sim.side+' '+(expected>0?'+':'')+expected:null,
  exactLineStatus:!ats?'NON_ATS_MARKET':exact?'EXACT_SLY':'DIRECTION_ONLY_DIFFERENT_SPREAD'},
  snapshotSource:sl.source,snapshotReceivedDateET:sl.receivedDateET,exactCaptureTimestamp:sl.exactCaptureTimestamp};
}
const games=input.games.map(g=>({...g,model:predict(g),sportsline:normalizeSportsline(g)}));
const sportslineCounts=games.reduce((n,g)=>{n[g.sportsline.sim.type]++;if(g.sportsline.sim.exactSlyLine)n.exactSlyATS++;return n;},{ATS:0,TOTAL:0,MONEYLINE:0,exactSlyATS:0});
const dataQuality={...input.dataQuality,sportsline:'User-provided Week 5 SportsLine screenshots cover all 14 games. SIM: '+sportslineCounts.ATS+' ATS ('+sportslineCounts.exactSlyATS+' exact Sly), '+sportslineCounts.TOTAL+' totals, '+sportslineCounts.MONEYLINE+' moneyline. SIM cover probabilities and handle percentages not shown. Exact capture clock time unavailable.'};
const payload={...input,games,standings,dataQuality,sportslineSummary:{source:sl.source,receivedDateET:sl.receivedDateET,captureTimeVerified:false,screenshotFiles:sl.screenshots,...sportslineCounts},modelVersion:games[0].model.model_version,derivedAt:'2026-10-09',sourceHash:games[0].model.artifact_hash};
function verify(){
 const w=payload.week4.bets;
 const modelProb=games.every(g=>{const p=g.model.hybrid;return [p.p_home_cover,p.p_away_cover,p.p_push].every(x=>Number.isFinite(x)&&x>=0&&x<=1)&&Math.abs(p.p_home_cover+p.p_away_cover+p.p_push-1)<1e-6});
 return {
  week5:payload.week===5,
  solo:payload.settings.mode==='SOLO'&&payload.settings.amandaEnabled===false,
  standings111:standings.rows.length===111,
  playerConfirmed:standings.rows.some(x=>x.name==='Catherine Williams'&&x.rank===17&&x.bankroll===12800),
  historicalAccounting:w.length===6&&w.reduce((s,g)=>s+g.wager,0)===4000&&w.reduce((s,g)=>s+g.net,0)===2000&&payload.week4.startingBankroll===10800&&payload.week4.startingBankroll+payload.week4.net===payload.player.bankroll,
  correctUpcomingCount:games.length===14&&new Set(games.map(g=>g.id)).size===14,
  thursdayFinal:payload.thursday.status==='FINAL'&&payload.thursday.eligible===false,
  freezePreserved:games.every(g=>g.slyFavoriteSpread<0&&g.favorite&&g.slyHomeSpread===(g.favorite===g.home?g.slyFavoriteSpread:-g.slyFavoriteSpread)),
  fiveFactorPage:html.includes('Five-Criteria Spread Scorecard')&&html.includes('Money / Handle')&&html.includes('Defensive EPA'),
  views:html.includes('Catherine — solo portfolio planner')&&html.includes('Four-source comparison')&&html.includes('Official standings'),
  probabilityContract:modelProb,
  sportslineFullSlate:games.every(g=>g.sportsline&&g.sportsline.sim&&g.sportsline.projectedScore&&g.sportsline.currentSpread),
  sportslineTypeIntegrity:sportslineCounts.ATS===5&&sportslineCounts.TOTAL===7&&sportslineCounts.MONEYLINE===2&&sportslineCounts.exactSlyATS===4,
  excludedExternalHallucination:games.every(g=>g.gridiron===null&&g.lucas===null&&g.sportsline.moneyPct===null&&g.sportsline.simCoverPct===null)
 }
}
const checks=verify();if(Object.values(checks).some(x=>!x))throw Error('Week 5 startup integrity check failure: '+JSON.stringify(checks));
const server=http.createServer((req,res)=>{
 const pathname=new URL(req.url,'http://localhost').pathname;
 const headers={'cache-control':'no-store, no-cache, must-revalidate, max-age=0','pragma':'no-cache'};
 if(pathname==='/healthz'){res.writeHead(200,{'content-type':'application/json',...headers});return res.end(JSON.stringify({status:'ok',version:payload.version,checks}))}
 if(pathname==='/_version'){res.writeHead(200,{'content-type':'application/json',...headers});return res.end(JSON.stringify({status:'ok',architecture:'week05-single-source',version:payload.version,week:5,mode:'CATHERINE_SOLO',bankroll:payload.player.bankroll,rank:payload.player.rank,games:games.length,marketCapturedAt:payload.capturedAtET,modelVersion:payload.modelVersion,fiveFactor:'PARTIAL_NO_FABRICATED_GRADES',sourceStatuses:payload.dataQuality}))}
 if(pathname==='/api/week5'){res.writeHead(200,{'content-type':'application/json; charset=utf-8',...headers});return res.end(JSON.stringify(payload))}
 if(pathname==='/favicon.ico'){res.writeHead(204,headers);return res.end()}
 if(pathname==='/week4-archive'){res.writeHead(302,{location:'https://github.com/catherinelw716/monopoly-command-center-canonical/blob/main/PROJECT_STATE.md',...headers});return res.end()}
 res.writeHead(200,{'content-type':'text/html; charset=utf-8','x-command-center-week':'5','x-command-center-scope':'solo',...headers});res.end(html);
});
server.listen(port,'0.0.0.0',()=>console.log('Week 5 Catherine solo Command Center '+payload.version+' listening on '+port));
