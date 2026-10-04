'use strict';
const assert=require('assert');
const v2=require('./ats-trends-v2-challenger');

// Recency weighting: newest observation should matter more.
const a=v2.weightedMeanMargin([8,-8],4);
const b=v2.weightedMeanMargin([-8,8],4);
assert(b>a,'newer positive margin should raise weighted mean');

// Small samples must shrink materially toward neutral.
const one=v2.marginRating([12],'currentSeasonMargins');
const eight=v2.marginRating([12,12,12,12,12,12,12,12],'currentSeasonMargins');
assert(one.sampleMultiplier===.125,'one-game current-season sample should shrink to 1/8');
assert(eight.sampleMultiplier===1,'eight-game current-season sample should receive full weight');
assert(one.rating<eight.rating,'shrunk one-game signal must be weaker than eight-game signal');

// H2H must be a small component, not the dominant input.
assert.strictEqual(v2.WEIGHTS.h2h,.15);
assert(v2.WEIGHTS.currentSeasonMargins>v2.WEIGHTS.h2h);
assert(v2.WEIGHTS.priorFormMargins>v2.WEIGHTS.h2h);

// Non-overlapping components can generate a directional matchup score.
const matchup=v2.scoreMatchup({
  away:{currentSeasonMargins:[3,5,4],priorFormMargins:[1,2,3,2,1,4,2,3],h2h:{w:2,l:3,mostRecentSeasonsAgo:1}},
  home:{currentSeasonMargins:[-3,-5,-4],priorFormMargins:[-1,-2,-3,-2,-1,-4,-2,-3],h2h:{w:3,l:2,mostRecentSeasonsAgo:1}}
});
assert(['challenger','degraded'].includes(matchup.status));
assert(matchup.awayIndex>matchup.homeIndex,'positive cover-margin profile should outrank negative profile');
assert(matchup.scores.away>matchup.scores.home,'away side should receive directional support');

// Current Week 4 legacy aggregate records must never be silently converted into margins.
const legacy=v2.inspectLegacyWeek4Input({trends:{away:{season:{w:3,l:0}},home:{season:{w:0,l:3}}}});
assert.strictEqual(legacy.status,'DATA_PENDING');
assert.deepStrictEqual(legacy.scores,{away:10,home:10});

// Invalid margin data should fail loudly rather than contaminate the signal.
assert.throws(()=>v2.marginRating([1,'bad'],'currentSeasonMargins'));

console.log('ATS Trends v2 challenger QA passed');
