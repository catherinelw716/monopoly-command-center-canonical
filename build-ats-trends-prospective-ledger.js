'use strict';
const fs=require('fs');
const r=JSON.parse(fs.readFileSync('ats-trends-v2-week04-results.json','utf8'));
const out={
  season:r.season,
  createdAt:r.generatedAt,
  purpose:'Prospective comparison of ATS Trends v1 versus v2 challenger. Predictions are frozen before results and must not be rewritten after outcomes.',
  promotionPolicy:'Do not replace v1 based on one week. Compare multiple weeks on directional ATS accuracy, strength-band separation, stability, and incremental value versus other five-factor signals.',
  methodology:{v1:'Locked Week 4 scorecard ATS Trends factor',v2:'45% current-season cover margin + 40% non-overlapping prior-form cover margin + 15% H2H'},
  weeks:[{
    week:r.week,
    predictionFrozenAt:r.generatedAt,
    status:'PENDING_RESULTS',
    games:r.games.map(g=>({
      game:g.game,
      slyAway:g.slyAway,
      v1:{lean:g.v1.lean,scores:g.v1.scores},
      v2:{lean:g.v2.leanTeam,scores:g.v2.scores},
      comparison:g.comparison,
      sourceAlignment:g.sourceAlignment,
      result:null,
      v1Correct:null,
      v2Correct:null
    }))
  }]
};
fs.writeFileSync('ats-trends-prospective-ledger.json',JSON.stringify(out,null,2)+'\n');
console.log(`Frozen ${out.weeks[0].games.length} Week ${r.week} ATS Trends v1/v2 predictions`);
