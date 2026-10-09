'use strict';
// Byte-for-method translation of v2/shadow_model.py (V2-0006C global hybrid).
// Frozen coefficients and empirical exact-margin counts are read from the canonical artifact.
const artifact = require('./v2/model_artifacts/v2_global_hybrid_2016_2025.json');
const SQRT2=Math.sqrt(2);
function erf(x) {
 const sign=x<0?-1:1; x=Math.abs(x);
 const t=1/(1+0.3275911*x);
 return sign*(1-(((((1.061405429*t-1.453152027)*t)+1.421413741)*t-0.284496736)*t+0.254829592)*t*Math.exp(-x*x));
}
function cdf(z){return (1+erf(z/SQRT2))/2}
function clamp(x,a,b){return Math.max(a,Math.min(b,x))}
function predict(game) {
 const marketHome=game.marketHomeSpread,slyHome=game.slyHomeSpread;
 const delta=slyHome-marketHome;
 const m=artifact.residual_mu+delta, sigma=artifact.residual_sigma;
 const isInteger=Math.abs(slyHome-Math.round(slyHome))<1e-9;
 let loss,push,cover;
 if(isInteger){const lo=cdf((-.5-m)/sigma),hi=cdf((.5-m)/sigma);loss=lo;push=hi-lo;cover=1-hi;}
 else {loss=cdf(-m/sigma);push=0;cover=1-loss;}
 const normal={p_home_loss:loss,p_push:push,p_home_cover:cover,p_away_cover:loss,p_away_loss:cover};
 if(isInteger){
  const margin=String(Math.round(-slyHome));
  const count=artifact.margin_counts[margin]||0;
  const empirical=clamp((count+artifact.push_shrink*push)/(artifact.n_training_games+artifact.push_shrink),0,1);
  const denom=loss+cover;
  if(denom>1e-12){loss=(1-empirical)*loss/denom;cover=(1-empirical)*cover/denom;push=empirical;}
 }
 const hybrid={p_home_loss:loss,p_push:push,p_home_cover:cover,p_away_cover:loss,p_away_loss:cover};
 const awayValue=loss-cover,homeValue=cover-loss;
 const preferred=awayValue>homeValue?game.away:game.home;
 return {model_version:artifact.model_version,artifact_hash:artifact.artifact_hash,sly_home_spread:slyHome,market_home_spread:marketHome,home_line_advantage:delta,integer_sly_line:isInteger,normal,hybrid,preferred,preferredCoverPct:Math.round(1000*Math.max(loss,cover))/10,preferenceStrength:Math.abs(loss-cover),netPer100Expected:Math.round(100*(Math.abs(loss-cover))),modelStatus:'CHALLENGER_ONLY'};
}
module.exports={predict,cdf};
