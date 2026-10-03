'use strict';
const fs=require('fs');
const {scoreSlate,formatSpread}=require('./five-factor-scorecard-engine');
const loadInput=require('./load-five-factor-week04');
const input=loadInput();
const main=require('./v2/results/week_04_nfelo_optimizer_rerun_2026-10-03.json');
const factorLabels={lineMovement:'Line movement',trends:'ATS trends',money:'Money',defense:'Defense',keyNumbers:'Key numbers'};
function factorForLean(f,side){return f.scores[side];}
function sideSpread(g,team){if(team===g.away)return g.slyAway;if(team===g.home)return -g.slyAway;return null;}
function enrich(g){
  const o=g.fiveFactor.overall,side=o.leanSide;
  const mainRow=main.ranking.find(r=>r.game===g.game);
  const mainTeam=mainRow&&mainRow.pick!=='NO TAKE'?mainRow.pick.split(' ')[0]:null;
  const comparison=!mainTeam?'MAIN SYSTEM NO TAKE':o.lean==='NO EDGE'?'FIVE-FACTOR NO EDGE':mainTeam===o.lean?'AGREES':'DISAGREES';
  const fscores=['lineMovement','trends','money','defense','keyNumbers'].map(k=>({key:k,label:factorLabels[k],score:side==='neutral'?10:factorForLean(g.fiveFactor[k],side),lean:g.fiveFactor[k].lean,status:g.fiveFactor[k].status,explanation:g.fiveFactor[k].explanation,flags:g.fiveFactor[k].flags}));
  const supports=fscores.filter(x=>x.score>=12),opposes=fscores.filter(x=>x.score<=8),neutral=fscores.filter(x=>x.score>=9&&x.score<=11);
  const pick=o.lean==='NO EDGE'?'NO EDGE':formatSpread(o.lean,sideSpread(g,o.lean));
  const why=o.lean==='NO EDGE'?`The five factors finish tied 50-50, so this framework has no directional edge.`:`${supports.length} of 5 factors support ${o.lean}. ${supports.map(x=>x.label+': '+x.explanation).join(' ')}`;
  const against=opposes.length?opposes.map(x=>`${x.label}: ${x.explanation}`).join(' '):neutral.length?`The remaining ${neutral.length} factor${neutral.length===1?' is':'s are'} neutral rather than additional confirmation.`:`No factor directly opposes the five-factor lean.`;
  return {...g,fiveFactor:{...g.fiveFactor,overall:{...o,pick,whyThisSide:why,whatArguesAgainst:against,mainSystem:{pick:mainRow?.pick||'NO TAKE',decision:mainRow?.decision||'UNKNOWN',comparison}}}};
}
const scoredBase=scoreSlate(input);
const scored=scoredBase.games.map(enrich).sort((a,b)=>Math.max(b.fiveFactor.overall.awayScore,b.fiveFactor.overall.homeScore)-Math.max(a.fiveFactor.overall.awayScore,a.fiveFactor.overall.homeScore)||a.game.localeCompare(b.game));
scored.forEach((g,i)=>g.fiveFactor.overall.scorecardRank=i+1);
const output={season:input.season,week:input.week,status:'PRE_RESULT_FIVE_FACTOR_CHALLENGER',capturedAt:input.capturedAt,engineVersion:scoredBase.engineVersion,challengerOnly:true,feedsV2:false,feedsOptimizer:false,correlationDisclosure:'Line Movement and Money are separate v1.0.1 factors for interpretability but both describe market behavior and are not independent evidence.',sourceInput:['five-factor-scorecard-data-week04.json','five-factor-scorecard-verified-overrides-week04.json'],verification:input.verification,games:scored};
fs.writeFileSync('five-factor-scorecard-week04.json',JSON.stringify(output,null,2)+'\n');
console.log('Generated five-factor-scorecard-week04.json');
for(const g of scored){const o=g.fiveFactor.overall;console.log(`${o.scorecardRank}. ${g.game} | ${o.pick} | ${Math.max(o.awayScore,o.homeScore)} | ${o.displayGrade} | ${o.alignment.supports} support / ${o.alignment.opposes} oppose | ${o.mainSystem.comparison}`);}
