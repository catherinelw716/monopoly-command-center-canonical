'use strict';

const WEIGHTS={currentSeasonMargins:.45,priorFormMargins:.40,h2h:.15};
const HALF_LIFE={currentSeasonMargins:4,priorFormMargins:6};
const TARGET_N={currentSeasonMargins:8,priorFormMargins:8};
const DIFF_BANDS=[
  {maxExclusive:1,supported:10},
  {maxExclusive:3,supported:12},
  {maxExclusive:5,supported:14},
  {maxExclusive:7,supported:16},
  {maxExclusive:9,supported:18},
  {maxExclusive:Infinity,supported:20},
];
const clamp=(n,a,b)=>Math.max(a,Math.min(b,n));
const pair=(supported,side)=>side==='away'?{away:supported,home:20-supported}:side==='home'?{away:20-supported,home:supported}:{away:10,home:10};

function rawRateRating(rate){
  if(rate>=.70)return 20;if(rate>=.65)return 18;if(rate>=.60)return 16;if(rate>=.55)return 14;if(rate>=.52)return 12;
  if(rate>=.48)return 10;if(rate>=.45)return 8;if(rate>=.40)return 6;if(rate>=.35)return 4;if(rate>=.30)return 2;return 0;
}
function binarySampleMultiplier(n){return n>=5?1:({1:.25,2:.40,3:.60,4:.80}[n]||0);}
function h2hRating(record){
  if(!record||record.w==null||record.l==null||record.w+record.l===0)return null;
  const n=record.w+record.l,raw=rawRateRating(record.w/n),age=record.mostRecentSeasonsAgo??99;
  const ageMult=age<=2?1:age<=5?.75:.5;
  return 10+(raw-10)*binarySampleMultiplier(n)*ageMult;
}
function weightedMeanMargin(values,halfLife){
  if(!Array.isArray(values)||!values.length)return null;
  let num=0,den=0;
  values.forEach((v,i)=>{
    if(typeof v!=='number'||!Number.isFinite(v))throw new Error('ATS margin sequences must contain finite numbers');
    const age=(values.length-1)-i,w=Math.pow(.5,age/halfLife);num+=w*v;den+=w;
  });
  return num/den;
}
function marginRating(values,key){
  if(!Array.isArray(values)||!values.length)return null;
  const rawMean=weightedMeanMargin(values,HALF_LIFE[key]);
  const mult=Math.min(1,values.length/TARGET_N[key]);
  const adjustedMean=rawMean*mult;
  const rating=10+10*Math.tanh(adjustedMean/6);
  return {rating:clamp(rating,0,20),rawMean,adjustedMean,n:values.length,sampleMultiplier:mult};
}
function teamIndex(team){
  const current=marginRating(team?.currentSeasonMargins,'currentSeasonMargins');
  const prior=marginRating(team?.priorFormMargins,'priorFormMargins');
  const h2h=h2hRating(team?.h2h);
  const parts={currentSeasonMargins:current?.rating??null,priorFormMargins:prior?.rating??null,h2h};
  const detail={currentSeasonMargins:current,priorFormMargins:prior,h2h};
  const avail=Object.entries(parts).filter(([,v])=>v!=null);
  if(!avail.length)return {index:null,parts,detail,available:0};
  const den=avail.reduce((s,[k])=>s+WEIGHTS[k],0);
  const index=avail.reduce((s,[k,v])=>s+v*WEIGHTS[k]/den,0);
  return {index,parts,detail,available:avail.length};
}
function scoreMatchup(game){
  const away=teamIndex(game?.away),home=teamIndex(game?.home);
  if(away.index==null||home.index==null)return {status:'DATA_PENDING',scores:{away:10,home:10},lean:'neutral',awayIndex:away.index,homeIndex:home.index,away,home,flags:['both teams require at least one usable ATS Trends v2 component']};
  const diff=away.index-home.index,abs=Math.abs(diff),side=abs<1?'neutral':diff>0?'away':'home';
  let supported=DIFF_BANDS.find(b=>abs<b.maxExclusive).supported;
  const minAvail=Math.min(away.available,home.available),flags=[];
  let status='challenger';
  if(minAvail===1){supported=Math.min(supported,14);status='degraded';flags.push('only one component available for at least one team');}
  const scores=pair(supported,side);
  return {status,scores,lean:side,awayIndex:+away.index.toFixed(3),homeIndex:+home.index.toFixed(3),difference:+diff.toFixed(3),away,home,flags};
}
function inspectLegacyWeek4Input(game){
  const hasMargins=Boolean(game?.trendsV2?.away?.currentSeasonMargins?.length||game?.trendsV2?.away?.priorFormMargins?.length||game?.trendsV2?.home?.currentSeasonMargins?.length||game?.trendsV2?.home?.priorFormMargins?.length);
  return hasMargins?scoreMatchup(game.trendsV2):{status:'DATA_PENDING',scores:{away:10,home:10},lean:'neutral',flags:['source-backed game-level ATS cover margins are not present in the Week 4 input']};
}

module.exports={WEIGHTS,HALF_LIFE,TARGET_N,weightedMeanMargin,marginRating,h2hRating,teamIndex,scoreMatchup,inspectLegacyWeek4Input};
