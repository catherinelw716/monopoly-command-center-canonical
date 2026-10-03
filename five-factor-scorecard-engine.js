'use strict';
const config=require('./five-factor-scorecard-config.json');
const clamp=(n,a,b)=>Math.max(a,Math.min(b,n));
const pair=(supported,side)=>side==='away'?{away:supported,home:20-supported}:side==='home'?{away:20-supported,home:supported}:{away:10,home:10};
const band=(x,bands,key='supported')=>(bands.find(b=>x<b.maxExclusive)||bands[bands.length-1])[key];
const formatSpread=(team,n)=>`${team} ${n>0?'+':''}${Number(n)}`;
const sideName=(game,side)=>side==='away'?game.away:game.home;
function factorState(score){return score>=12?'supports':score>=9?'neutral':'opposes';}
function rawRateRating(rate){return config.trends.rawRateBands.find(b=>rate>=b.min).rating;}
function sampleMultiplier(n){return n>=5?1:(config.trends.sampleMultipliers[String(n)]||0);}
function adjustedAts(record,isH2H=false){
  if(!record||record.w==null||record.l==null||record.w+record.l===0)return null;
  const n=record.w+record.l, raw=rawRateRating(record.w/n);
  let mult=sampleMultiplier(n);
  if(isH2H){const age=record.mostRecentSeasonsAgo??99;mult*=age<=2?1:age<=5?.75:.5;}
  return 10+(raw-10)*mult;
}
function scoreLineMovement(game){
  const m=game.market;
  if(!m||m.openAway==null||m.currentAway==null)return unavailable('Line movement','Opening or current market spread is unavailable.');
  const movement=m.openAway-m.currentAway, abs=Math.abs(movement);
  let supported=band(abs,config.lineMovement.bands), side=abs<.5?'neutral':movement>0?'away':'home', status='verified', flags=[];
  if(m.crossCheckDirectionDisagreement){supported=Math.min(supported,config.lineMovement.crossSourceDirectionDisagreementCap);status='degraded';flags.push('cross-source movement disagreement');}
  const scores=pair(supported,side);
  const lean=side==='neutral'?'neutral':sideName(game,side);
  const exp=side==='neutral'?`Market is essentially unchanged from ${formatSpread(game.away,m.openAway)} to ${formatSpread(game.away,m.currentAway)}.`:`Market moved ${abs.toFixed(1)} point${abs===1?'':'s'} toward ${lean}: ${formatSpread(game.away,m.openAway)} → ${formatSpread(game.away,m.currentAway)}.`;
  return {status,scores,lean,raw:{openAway:m.openAway,currentAway:m.currentAway,movementTowardAway:movement,source:m.source,capturedAt:m.capturedAt},flags,explanation:exp};
}
function trendIndex(rec){
  const parts={h2h:adjustedAts(rec?.h2h,true),season:adjustedAts(rec?.season,false),recent:adjustedAts(rec?.recent,false)};
  const avail=Object.entries(parts).filter(([,v])=>v!=null);
  if(!avail.length)return {index:null,parts,available:0};
  const den=avail.reduce((s,[k])=>s+config.trends.weights[k],0);
  const index=avail.reduce((s,[k,v])=>s+v*config.trends.weights[k]/den,0);
  return {index,parts,available:avail.length};
}
function scoreTrends(game){
  const a=trendIndex(game.trends?.away),h=trendIndex(game.trends?.home);
  if(a.index==null&&h.index==null)return unavailable('ATS trends','No usable ATS trend components are available.');
  if(a.index==null||h.index==null)return unavailable('ATS trends','One team lacks usable ATS trend data, so the matchup comparison is unavailable.');
  const diff=a.index-h.index, abs=Math.abs(diff), side=abs<1?'neutral':diff>0?'away':'home';
  let supported=band(abs,config.trends.diffBands), status='verified',flags=[];
  const minAvail=Math.min(a.available,h.available);
  if(minAvail===1){supported=Math.min(supported,config.trends.oneComponentCap);status='degraded';flags.push('only one ATS component available for at least one team');}
  if(game.trends?.recentOverlapsSeason){flags.push('recent ATS window overlaps current-season ATS');}
  const scores=pair(supported,side),lean=side==='neutral'?'neutral':sideName(game,side);
  const exp=side==='neutral'?`The weighted ATS profiles are effectively even (${a.index.toFixed(1)} vs ${h.index.toFixed(1)}).`:`${lean} has the stronger weighted ATS profile (${Math.max(a.index,h.index).toFixed(1)} vs ${Math.min(a.index,h.index).toFixed(1)}).`;
  return {status,scores,lean,raw:{awayIndex:+a.index.toFixed(2),homeIndex:+h.index.toFixed(2),awayParts:a.parts,homeParts:h.parts,source:game.trends?.source,capturedAt:game.trends?.capturedAt},flags,explanation:exp};
}
function crossesKey(a,b){return config.keyNumbers.some(k=>(a<k.key&&b>=k.key)||(b<k.key&&a>=k.key));}
function scoreMoney(game,captureTime){
  const m=game.money;
  if(!m||!config.money.allowedMetricTypes.includes(m.metricType)||m.awayPct==null||m.homePct==null)return unavailable('Money','Verified spread handle/money percentage is unavailable; tickets are not substituted.');
  if(Math.abs((m.awayPct+m.homePct)-100)>1)return unavailable('Money','Handle percentages do not form a valid two-sided split.');
  const hi=Math.max(m.awayPct,m.homePct)/100, side=m.awayPct===m.homePct?'neutral':m.awayPct>m.homePct?'away':'home';
  let supported=config.money.bands.find(b=>hi>=b.min).supported,status='verified',flags=[];
  const sly=game.slyAway, ref=m.referenceAway;
  if(ref==null)return unavailable('Money','Handle percentage has no exact reference spread.');
  if(Math.abs(ref-sly)>=config.money.lineMismatchPoints||crossesKey(Math.abs(ref),Math.abs(sly))){supported=Math.min(supported,config.money.referenceMismatchCap);status='degraded';flags.push('handle reference line differs materially from Sly');}
  if(captureTime&&m.capturedAt){const hrs=(new Date(captureTime)-new Date(m.capturedAt))/36e5;if(hrs>config.money.staleHours)return unavailable('Money','Handle snapshot is more than 24 hours old.');if(hrs>config.money.freshHours){supported=Math.min(supported,config.money.staleCap);status='degraded';flags.push('handle snapshot is stale but usable');}}
  const scores=pair(supported,side),lean=side==='neutral'?'neutral':sideName(game,side),pct=side==='away'?m.awayPct:side==='home'?m.homePct:50;
  const exp=side==='neutral'?`Verified spread handle is balanced 50/50 at ${formatSpread(game.away,ref)}.`:`${pct}% of verified spread handle is on ${lean} at ${formatSpread(game.away,ref)}.`;
  return {status,scores,lean,raw:{awayPct:m.awayPct,homePct:m.homePct,metricType:m.metricType,referenceAway:ref,source:m.source,capturedAt:m.capturedAt},flags,explanation:exp};
}
function defenseValue(rank){const r=config.defense.rankTiers.find(x=>rank>=x.min&&rank<=x.max);return r?r.value:null;}
function scoreDefense(game){
  const d=game.defense;if(!d||d.awayRank==null||d.homeRank==null||!d.sameMethodology)return unavailable('Defense','Comparable defensive EPA/play ranks are unavailable for both teams.');
  const mult=config.defense.spreadMultipliers.find(x=>Math.abs(game.slyAway)<=x.max).value;
  const diff=(defenseValue(d.awayRank)-defenseValue(d.homeRank))*mult,abs=Math.abs(diff),side=abs<1?'neutral':diff>0?'away':'home',supported=band(abs,config.defense.diffBands),scores=pair(supported,side),lean=side==='neutral'?'neutral':sideName(game,side);
  const exp=side==='neutral'?`Defensive EPA/play tiers are effectively neutral for this ${Math.abs(game.slyAway)}-point spread.`:`${lean} has the stronger spread-adjusted defensive profile (${side==='away'?'#'+d.awayRank:' #'+d.homeRank} vs ${side==='away'?'#'+d.homeRank:'#'+d.awayRank}).`;
  return {status:'verified',scores,lean,raw:{awayRank:d.awayRank,homeRank:d.homeRank,awayEpa:d.awayEpa,homeEpa:d.homeEpa,spreadMultiplier:mult,source:d.source,capturedAt:d.capturedAt,throughWeek:d.throughWeek},flags:[],explanation:exp};
}
function scoreKeyNumbers(game){
  const s=game.slyAway,c=game.market?.currentAway;let advantage=0,notes=[];
  for(const k of config.keyNumbers){const a=Math.abs(s),dist=Math.abs(a-k.key),boost=Math.ceil(k.hookStrength/2);
    if(dist<1e-9){
      if(c!=null){const better=s>c; if(better){advantage+=boost;notes.push(`Sly improves ${game.away} onto key ${k.key} versus market`);}else if(s<c){advantage-=boost;notes.push(`Sly is worse for ${game.away} around key ${k.key}`);}}
      continue;
    }
    if(Math.abs(dist-.5)>1e-9)continue;
    const favorable=(s<0&&a===k.key-.5)||(s>0&&a===k.key+.5);advantage+=favorable?k.hookStrength:-k.hookStrength;notes.push(`${formatSpread(game.away,s)} sits on the ${favorable?'favorable':'unfavorable'} hook around ${k.key}`);
    if(c!=null){if(favorable&&((s>0&&c<=k.key-.5)||(s<0&&c<=-(k.key+.5))))advantage+=boost;else if(!favorable&&((s>0&&c>=k.key+.5)||(s<0&&c>=-(k.key-.5))))advantage-=boost;}
  }
  advantage=clamp(advantage,-10,10);const scores={away:10+advantage,home:10-advantage},side=advantage>0?'away':advantage<0?'home':'neutral',lean=side==='neutral'?'neutral':sideName(game,side);
  const exp=side==='neutral'?`Sly ${formatSpread(game.away,s)} has no directional hook advantage under the configured key-number rules.`:`Key-number structure favors ${lean}: ${notes.join('; ')}.`;
  return {status:'verified',scores,lean,raw:{slyAway:s,currentAway:c,keys:config.keyNumbers.map(k=>k.key)},flags:c==null?['current market unavailable for relative key-number context']:[],explanation:exp};
}
function unavailable(name,msg){return {status:'unavailable',scores:{away:10,home:10},lean:'neutral',raw:{},flags:[`${name} unavailable`],explanation:msg};}
const gradeRank=['INSUFFICIENT DATA','N','C','C+','B-','B','B+','A-','A','A+'];
function rawGrade(score){return config.grades.find(g=>score>=g.min)?.grade||'N';}
function capGrade(grade,cap){if(cap==='INSUFFICIENT DATA')return cap;return gradeRank.indexOf(grade)>gradeRank.indexOf(cap)?cap:grade;}
function overall(game,factors){
  const away=Object.values(factors).reduce((s,f)=>s+f.scores.away,0),home=100-away,side=away===home?'neutral':away>home?'away':'home',score=Math.max(away,home),lean=side==='neutral'?'NO EDGE':sideName(game,side),idx=side==='away'?'away':'home';
  let grade=rawGrade(score),caps=[];const verified=Object.values(factors).filter(f=>f.status==='verified').length,available=Object.values(factors).filter(f=>f.status!=='unavailable').length;
  if(factors.money.status==='unavailable'){grade=capGrade(grade,'B+');caps.push('money unavailable → max B+');}
  if(verified<4){grade=capGrade(grade,'B');caps.push('<4 verified factors → max B');}
  if(verified<3){grade=capGrade(grade,'C+');caps.push('<3 verified factors → max C+');}
  const vals=Object.values(factors).map(f=>f.scores[idx]),strong=vals.filter(v=>v<=6).length;
  if(strong>=2){grade=capGrade(grade,'B');caps.push('2+ strongly opposing factors → max B');}
  if(available<=2){grade='INSUFFICIENT DATA';caps.push('≤2 available factors');}
  const alignment={supports:vals.filter(v=>v>=12).length,neutral:vals.filter(v=>v>=9&&v<=11).length,opposes:vals.filter(v=>v<=8).length,stronglyOpposes:strong};
  return {awayScore:away,homeScore:home,lean,leanSide:side,rawGrade:rawGrade(score),displayGrade:grade,alignment,verifiedFactors:verified,availableFactors:available,confidenceCaps:caps};
}
function scoreGame(game,captureTime){const factors={lineMovement:scoreLineMovement(game),trends:scoreTrends(game),money:scoreMoney(game,captureTime),defense:scoreDefense(game),keyNumbers:scoreKeyNumbers(game)};return {...game,fiveFactor:{...factors,overall:overall(game,factors)}};}
function scoreSlate(data){return {...data,engineVersion:config.version,games:data.games.map(g=>scoreGame(g,data.capturedAt))};}
module.exports={config,scoreLineMovement,scoreTrends,scoreMoney,scoreDefense,scoreKeyNumbers,scoreGame,scoreSlate,formatSpread};
