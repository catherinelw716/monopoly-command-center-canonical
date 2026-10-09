'use strict';
const http=require('http'),fs=require('fs');
const {predict}=require('./week05-model');
const fiveFactorEngine=require('./five-factor-scorecard-engine');
const port=Number(process.env.PORT||10000);
const input=JSON.parse(fs.readFileSync('./week05-canonical-data.json','utf8'));
const standings=JSON.parse(fs.readFileSync('./week05-standings.json','utf8'));
const html=fs.readFileSync('./week05-command-center.html','utf8');
const sl=JSON.parse(fs.readFileSync('./week05-sportsline-user-screenshot-2026-10-09.json','utf8'));
const grid=JSON.parse(fs.readFileSync('./week05-gridironai-user-screenshot-2026-10-09.json','utf8'));
const lucas=JSON.parse(fs.readFileSync('./week05-lucas-first-thoughts-2026-10-09.json','utf8'));
const ffInput=JSON.parse(fs.readFileSync('./five-factor-scorecard-data-week05.json','utf8'));
const ff=fiveFactorEngine.scoreSlate(ffInput);
const ffBy=Object.fromEntries(ff.games.map(g=>[g.game,g]));
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
function normalizeGridiron(g) {
 const d=grid.games[g.id];
 if(!d)throw Error('GridironAI screenshot game missing: '+g.id);
 if(d.isCompletedThursday)throw Error('Completed Thursday game must not appear in live slate');
 const exact=Math.abs(d.homeSpread-g.slyHomeSpread)<1e-9;
 const noTake=d.awayCoverPct===50 && d.homeCoverPct===50;
 if(d.awayCoverPct+d.homeCoverPct!==100)throw Error('GridironAI paired probabilities invalid: '+g.id);
 const team=noTake?null:d.awayCoverPct>d.homeCoverPct?d.away:d.home;
 const coverPct=noTake?50:Math.max(d.awayCoverPct,d.homeCoverPct);
 const strongerSideNative=team===g.home?d.homeSpread:team===g.away?d.awaySpread:null;
 const strongerSideSly=team===g.home?g.slyHomeSpread:team===g.away?-g.slyHomeSpread:null;
 return {...d,source: 'GridironAI',sourceCaptureET:grid.exactCaptureTimestamp,exactSlyLine:exact,
   strongerSide:team,strongerCoverPct:coverPct,strongerSideNativeLine:strongerSideNative,strongerSideSlyLine:strongerSideSly,
   grade:noTake?'N':coverPct>=55?'A':coverPct>=52?'B':coverPct===51?'C':'N',
   referenceStatus:noTake?'NO_TAKE_50_50':exact?'EXACT_SLY_LINE':'DIRECTIONAL_DIFFERENT_LINE',
   countedAsExactSlyATS:!noTake&&exact,
   interpretation:exact?'Probability applies at exact Sly spread.':'Probability applies to GridironAI native line only; no numerical adjustment has been made to Sly.'};
}
function normalizeLucas(g){
 const record=lucas.games[g.id];
 if(!record)return {source:'Lucas',game:g.id,team:null,status:'NOT_MENTIONED',designation:'NO_TAKE',qualifier:'Lucas did not mention this matchup',numericProbability:null,actionableAsFirmPick:false};
 if(record.team!==g.away&&record.team!==g.home)throw Error('Lucas selected team mismatch '+g.id);
 const sny=record.team===g.home?g.slyHomeSpread:-g.slyHomeSpread;
 return {...record,source:'Lucas',status:record.designation,referenceLinePolicy:'Mapped to Sly for comparison only; Lucas did not provide an official contest spread',slyMappedSpread:sny,slyMappedDisplay:record.team+' '+(sny>0?'+':'')+sny,numericProbability:null};
}
function normalizeFiveFactor(g){
 const x=ffBy[g.id];
 if(!x)throw Error('Five-factor Week 5 game missing: '+g.id);
 const slyAway=g.favorite===g.away?g.slyFavoriteSpread:-g.slyFavoriteSpread;
 if(Math.abs(x.slyAway-slyAway)>1e-9)throw Error('Five-factor cannot alter frozen Sly: '+g.id);
 const record=sl.games[g.id];
 const openAway=record.openSpread.team===g.away?record.openSpread.line:-record.openSpread.line;
 const currentAway=record.currentSpread.team===g.away?record.currentSpread.line:-record.currentSpread.line;
 if(Math.abs(x.market.openAway-openAway)>1e-9||Math.abs(x.market.currentAway-currentAway)>1e-9)throw Error('Five-factor movement input differs from SportsLine source: '+g.id);
 return x.fiveFactor;
}
const games=input.games.map(g=>({...g,model:predict(g),sportsline:normalizeSportsline(g),gridiron:normalizeGridiron(g),lucas:normalizeLucas(g),fiveFactor:normalizeFiveFactor(g)}));
const sportslineCounts=games.reduce((n,g)=>{n[g.sportsline.sim.type]++;if(g.sportsline.sim.exactSlyLine)n.exactSlyATS++;return n;},{ATS:0,TOTAL:0,MONEYLINE:0,exactSlyATS:0});
const gridironCounts=games.reduce((n,g)=>{n.exact+=g.gridiron.exactSlyLine?1:0;n.noTake+=g.gridiron.referenceStatus==='NO_TAKE_50_50'?1:0;n.actionableExact+=g.gridiron.countedAsExactSlyATS?1:0;return n;},{exact:0,noTake:0,actionableExact:0});
const lucasCounts=games.reduce((n,g)=>{n[g.lucas.designation]=(n[g.lucas.designation]||0)+1;return n;},{});
const fiveFactorCounts=games.reduce((a,g)=>{const f=g.fiveFactor;a[f.overall.displayGrade]=(a[f.overall.displayGrade]||0)+1;a.verifiedMovement+=(f.lineMovement.status==='verified'?1:0);a.verifiedKey+=(f.keyNumbers.status==='verified'?1:0);return a;},{verifiedMovement:0,verifiedKey:0});
const dataQuality={...input.dataQuality,fiveFactor:'Week 5 5F v'+ff.engineVersion+' calculated using locked pre-registered rules. SportsLine same-source opener/current supports Line Movement; frozen Sly + SportsLine current supports NFL Key Numbers. ATS trends, verified dollar handle and standardized defensive EPA ranks remain missing (neutral 10/10 placeholders, not evidence). Exactly 2 of 5 verified factors per game => INSUFFICIENT DATA overall, no A/B/C grades or cover probabilities.',lucas:'Lucas first thoughts, user relayed 2026-10-09: 1 LIKE (CHI), 1 CONDITIONAL_LIKE (CIN; Chase/Higgins health and Lucas -7 market note), 4 tentative LEAN with question marks (CLE, IND, BAL, NYG), 1 LEAN_PASS (LAR; probably would not bet), 7 not mentioned. These are directional expressions, not probabilistic or finalized bets. No Sly line is overwritten.',gridiron:'User-provided GridironAI Week 5 screenshot shows 15 games (14 upcoming plus completed Thursday). Native home spreads and both team cover probabilities verified, including 3 50/50 NO TAKE matchups. '+gridironCounts.exact+' exactly match Sly; '+gridironCounts.actionableExact+' actionable exact-line directional reads. Unverified screenshot clock time; different-line percentages must NOT be relabeled as Sly probabilities.',sportsline:'User-provided Week 5 SportsLine screenshots cover all 14 games. SIM: '+sportslineCounts.ATS+' ATS ('+sportslineCounts.exactSlyATS+' exact Sly), '+sportslineCounts.TOTAL+' totals, '+sportslineCounts.MONEYLINE+' moneyline. SIM cover probabilities and handle percentages not shown. Exact capture clock time unavailable.'};
const payload={...input,games,standings,dataQuality,sportslineSummary:{source:sl.source,receivedDateET:sl.receivedDateET,captureTimeVerified:false,screenshotFiles:sl.screenshots,...sportslineCounts},gridironSummary:{source:grid.source,receivedDateET:grid.receivedDateET,captureTimeVerified:false,screenshot:grid.screenshot,gamesShown:grid.gamesShown,upcomingGames:games.length,...gridironCounts},lucasSummary:{source:'Lucas',receivedDateET:lucas.receivedDateET,finalPicks:false,numericProbabilitiesProvided:false,...lucasCounts},fiveFactorSummary:{engineVersion:ff.engineVersion,mode:'TWO_VERIFIED_FACTORS_PARTIAL',source:'five-factor-scorecard-data-week05.json',...fiveFactorCounts,ats:'unavailable',money:'unavailable',defense:'unavailable',authoritativeGrades:false},modelVersion:games[0].model.model_version,derivedAt:'2026-10-09',sourceHash:games[0].model.artifact_hash};
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
  gridironCoverage:grid.gamesShown===15&&games.length===14&&grid.games['TB @ DAL'].isCompletedThursday===true&&games.every(g=>g.gridiron&&g.gridiron.homeCoverPct+g.gridiron.awayCoverPct===100),
  gridironExactAndNoTakes:gridironCounts.exact===4&&gridironCounts.actionableExact===4&&gridironCounts.noTake===3&&games.filter(g=>g.gridiron.referenceStatus==='NO_TAKE_50_50').every(g=>g.gridiron.strongerSide===null),
  gridironLineIntegrity:games.every(g=>g.gridiron.exactSlyLine===(Math.abs(g.gridiron.homeSpread-g.slyHomeSpread)<1e-9)),
  fiveFactorCompleteData:ff.games.length===14&&games.every(g=>g.fiveFactor),
  fiveFactorScoringInvariant:fiveFactorCounts.verifiedMovement===14&&fiveFactorCounts.verifiedKey===14&&fiveFactorCounts['INSUFFICIENT DATA']===14&&games.every(g=>g.fiveFactor.overall.availableFactors===2&&g.fiveFactor.overall.verifiedFactors===2&&g.fiveFactor.trends.status==='unavailable'&&g.fiveFactor.money.status==='unavailable'&&g.fiveFactor.defense.status==='unavailable'&&Object.values({lineMovement:g.fiveFactor.lineMovement,keyNumbers:g.fiveFactor.keyNumbers}).every(f=>f.scores.away+f.scores.home===20)),
  lucasCoverage:games.every(g=>g.lucas&&g.lucas.numericProbability===null)&&lucasCounts.LIKE===1&&lucasCounts.CONDITIONAL_LIKE===1&&lucasCounts.LEAN===4&&lucasCounts.LEAN_PASS===1&&lucasCounts.NO_TAKE===7,
  lucasNoFalseFirmPicks:games.every(g=>g.lucas.actionableAsFirmPick!==true)&&games.find(g=>g.id==='CIN @ MIA').lucas.marketSpreadMention.line===-7&&games.find(g=>g.id==='CIN @ MIA').slyFavoriteSpread===-6.5,
  excludedExternalHallucination:games.every(g=>g.sportsline.moneyPct===null&&g.sportsline.simCoverPct===null)
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
