'use strict';
const assert=require('assert');
const fs=require('fs');
const {scoreSlate,config}=require('./five-factor-scorecard-engine');
const input=require('./five-factor-scorecard-data-week04.json');
const sly=require('./v2/season_2026/week_04_sly_freeze.json');
assert.equal(input.games.length,15,'expected 15 eligible games');
const slyBy=Object.fromEntries(sly.games.map(g=>[g.game,g]));
for(const g of input.games){
  assert(slyBy[g.game],`missing Sly game ${g.game}`);
  const expectedAway=-slyBy[g.game].sly_home_spread;
  assert.equal(g.slyAway,expectedAway,`${g.game} Sly mismatch`);
  assert(g.market&&g.market.source&&g.market.capturedAt,`${g.game} market provenance missing`);
  assert(g.trends&&g.trends.source&&g.trends.capturedAt,`${g.game} trends provenance missing`);
  assert(g.money&&config.money.allowedMetricTypes.includes(g.money.metricType),`${g.game} Money factor is not verified handle/money`);
  assert(g.money.source&&g.money.capturedAt&&g.money.referenceAway!=null,`${g.game} money provenance/reference line missing`);
  assert(Math.abs(g.money.awayPct+g.money.homePct-100)<=1,`${g.game} handle split invalid`);
  assert(g.defense&&g.defense.sameMethodology&&g.defense.source,`${g.game} defense provenance/methodology missing`);
}
const recomputed=scoreSlate(input);
for(const g of recomputed.games){
  const ff=g.fiveFactor;
  for(const k of ['lineMovement','trends','money','defense','keyNumbers']){
    assert(ff[k],`${g.game} missing factor ${k}`);
    assert.equal(ff[k].scores.away+ff[k].scores.home,20,`${g.game} ${k} pair must sum to 20`);
    assert(['verified','degraded','unavailable'].includes(ff[k].status),`${g.game} ${k} invalid status`);
  }
  assert.equal(ff.overall.awayScore+ff.overall.homeScore,100,`${g.game} overall pair must sum to 100`);
  assert(ff.overall.displayGrade,`${g.game} missing display grade`);
}
if(fs.existsSync('five-factor-scorecard-week04.json')){
  const snapshot=require('./five-factor-scorecard-week04.json');
  assert.equal(snapshot.games.length,15,'snapshot must contain 15 games');
  const out=JSON.stringify(snapshot);
  for(const bad of ['undefined','[object Object]'])assert(!out.includes(bad),`snapshot contains ${bad}`);
  for(const g of snapshot.games){
    const r=recomputed.games.find(x=>x.game===g.game);
    assert(r,`snapshot has unknown game ${g.game}`);
    for(const k of ['lineMovement','trends','money','defense','keyNumbers'])assert.deepStrictEqual(g.fiveFactor[k],r.fiveFactor[k],`${g.game} ${k} drifted from engine`);
    const a=g.fiveFactor.overall,b=r.fiveFactor.overall;
    for(const k of ['awayScore','homeScore','lean','leanSide','rawGrade','displayGrade','verifiedFactors','availableFactors'])assert.deepStrictEqual(a[k],b[k],`${g.game} overall ${k} drifted`);
    assert(a.whyThisSide&&a.whatArguesAgainst,`${g.game} plain-English rationale missing`);
    assert(a.mainSystem&&['AGREES','DISAGREES','MAIN SYSTEM NO TAKE','FIVE-FACTOR NO EDGE'].includes(a.mainSystem.comparison),`${g.game} invalid main-system comparison`);
  }
}
console.log('Five-factor scorecard QA passed: 15/15 games, Sly immutable, handle-only money, deterministic scoring.');
