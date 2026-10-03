'use strict';
const base=require('./five-factor-scorecard-data-week04.json');
const overrides=require('./five-factor-scorecard-verified-overrides-week04.json');
function load(){
  const out=structuredClone(base);
  out.capturedAt=overrides.capturedAt||out.capturedAt;
  out.verification=overrides.verification;
  for(const g of out.games){
    const o=overrides.games[g.game];if(!o)continue;
    if(o.market)Object.assign(g.market,o.market,{capturedAt:out.capturedAt});
    if(o.money)Object.assign(g.money,o.money,{capturedAt:out.capturedAt});
    if(o.trends?.awaySeason)g.trends.away.season=o.trends.awaySeason;
    if(o.trends?.homeSeason)g.trends.home.season=o.trends.homeSeason;
  }
  return out;
}
module.exports=load;
