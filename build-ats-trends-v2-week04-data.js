'use strict';

const fs=require('fs');
const challenger=require('./ats-trends-v2-challenger');
const fiveFactor=require('./five-factor-scorecard-engine');

const NFLVERSE_URL='https://raw.githubusercontent.com/nflverse/nfldata/master/data/games.csv';
const TARGET_SEASON=2026;
const TARGET_WEEK=4;
const PRIOR_SEASON=2025;
const NFLVERSE_TEAM={LAR:'LA'};

function parseCsvLine(line){
  const out=[];let cur='',quoted=false;
  for(let i=0;i<line.length;i++){
    const c=line[i];
    if(c==='"'){
      if(quoted&&line[i+1]==='"'){cur+='"';i++;}
      else quoted=!quoted;
    }else if(c===','&&!quoted){out.push(cur);cur='';}
    else cur+=c;
  }
  out.push(cur);return out;
}
function parseCsv(text){
  const lines=text.trim().split(/\r?\n/),header=parseCsvLine(lines[0]);
  return lines.slice(1).map(line=>{const cells=parseCsvLine(line),r={};header.forEach((h,i)=>r[h]=cells[i]??'');return r;});
}
function num(v){const n=Number(v);return v===''||!Number.isFinite(n)?null:n;}
function sourceTeam(team){return NFLVERSE_TEAM[team]||team;}
function completedReg(row,season){return Number(row.season)===season&&row.game_type==='REG'&&num(row.away_score)!=null&&num(row.home_score)!=null&&num(row.spread_line)!=null;}
function teamMargin(row,team){
  const result=num(row.home_score)-num(row.away_score),spread=num(row.spread_line);
  if(team===row.home_team)return +(result-spread).toFixed(2);
  if(team===row.away_team)return +((-result)+spread).toFixed(2);
  throw new Error(`${team} not found in ${row.game_id}`);
}
function historyFor(rows,team,season,filterFn){
  return rows.filter(r=>completedReg(r,season)&&(r.home_team===team||r.away_team===team)&&filterFn(r))
    .sort((a,b)=>String(a.gameday).localeCompare(String(b.gameday))||Number(a.week)-Number(b.week));
}
function recordFromMargins(margins){return {w:margins.filter(x=>x>0).length,l:margins.filter(x=>x<0).length,p:margins.filter(x=>x===0).length};}
function sameRecord(a,b){return Boolean(a&&b&&a.w===b.w&&a.l===b.l&&(a.p||0)===(b.p||0));}
function teamSide(rows,team,h2h){
  const srcTeam=sourceTeam(team);
  const current=historyFor(rows,srcTeam,TARGET_SEASON,r=>Number(r.week)<TARGET_WEEK);
  const prior=historyFor(rows,srcTeam,PRIOR_SEASON,()=>true).slice(-8);
  if(current.length!==3)throw new Error(`${team}: expected 3 completed ${TARGET_SEASON} games before Week ${TARGET_WEEK}, found ${current.length}`);
  if(prior.length!==8)throw new Error(`${team}: expected 8 prior-form ${PRIOR_SEASON} games, found ${prior.length}`);
  return {
    currentSeasonMargins:current.map(r=>teamMargin(r,srcTeam)),
    priorFormMargins:prior.map(r=>teamMargin(r,srcTeam)),
    h2h:h2h||null,
    provenance:{
      sourceTeam:srcTeam,
      currentSeasonGames:current.map(r=>({gameId:r.game_id,date:r.gameday,week:Number(r.week),opponent:r.home_team===srcTeam?r.away_team:r.home_team,site:r.home_team===srcTeam?'home':'away',spreadLine:num(r.spread_line),teamCoverMargin:teamMargin(r,srcTeam)})),
      priorFormGames:prior.map(r=>({gameId:r.game_id,date:r.gameday,week:Number(r.week),opponent:r.home_team===srcTeam?r.away_team:r.home_team,site:r.home_team===srcTeam?'home':'away',spreadLine:num(r.spread_line),teamCoverMargin:teamMargin(r,srcTeam)}))
    }
  };
}
function v2TeamLabel(game,lean){return lean==='away'?game.away:lean==='home'?game.home:'NO EDGE';}
function v1SideLabel(game,v1){if(v1.scores.away===v1.scores.home)return 'NO EDGE';return v1.scores.away>v1.scores.home?game.away:game.home;}

async function main(){
  const res=await fetch(NFLVERSE_URL,{headers:{'user-agent':'nfl-monopoly-command-center/1.0'}});
  if(!res.ok)throw new Error(`nflverse fetch failed: ${res.status} ${res.statusText}`);
  const csv=await res.text(),rows=parseCsv(csv),base=JSON.parse(fs.readFileSync('five-factor-scorecard-data-week04.json','utf8'));
  const generatedAt=new Date().toISOString();
  const games=base.games.map(g=>{
    const input={away:teamSide(rows,g.away,g.trends?.away?.h2h),home:teamSide(rows,g.home,g.trends?.home?.h2h)};
    const v2=challenger.scoreMatchup(input),v1=fiveFactor.scoreTrends(g),v2Side=v2TeamLabel(g,v2.lean),v1Side=v1SideLabel(g,v1);
    const sourceAlignment={};
    for(const side of ['away','home']){
      const implied=recordFromMargins(input[side].currentSeasonMargins),reference=g.trends?.[side]?.season||null;
      sourceAlignment[side]={team:g[side],nflverseImplied:implied,v1Reference:reference,matchesV1SeasonRecord:sameRecord(implied,reference)};
    }
    return {
      game:g.game,away:g.away,home:g.home,slyAway:g.slyAway,
      input,
      v1:{status:v1.status,lean:v1Side,scores:v1.scores,awayIndex:v1.raw?.awayIndex,homeIndex:v1.raw?.homeIndex},
      v2:{...v2,leanTeam:v2Side},
      sourceAlignment,
      comparison:v1Side==='NO EDGE'||v2Side==='NO EDGE'?'NEUTRAL_INVOLVED':v1Side===v2Side?'AGREE':'DISAGREE'
    };
  });
  const alignmentSides=games.flatMap(g=>Object.values(g.sourceAlignment));
  const inputOut={season:TARGET_SEASON,week:TARGET_WEEK,generatedAt,status:'SOURCE_BACKED_CHALLENGER_INPUT',source:{name:'nflverse/nfldata games.csv',url:NFLVERSE_URL,field:'spread_line',interpretation:'positive spread_line means home team favored; team cover margin derived as actual team scoring margin minus team closing/reference spread',fetchedAt:generatedAt},policy:{challengerOnly:true,doesNotModifyFiveFactorV1:true,doesNotFeedV2OrOptimizer:true,currentSeasonWindow:`${TARGET_SEASON} completed regular-season games before Week ${TARGET_WEEK}`,priorFormWindow:`last 8 ${PRIOR_SEASON} regular-season games per team`},games:games.map(({game,away,home,slyAway,input})=>({game,away,home,slyAway,trendsV2:input}))};
  const results={season:TARGET_SEASON,week:TARGET_WEEK,generatedAt,engine:'ats-trends-v2-challenger',weights:challenger.WEIGHTS,sourceAlignmentPolicy:'v2 margins use nflverse spread_line; v1 season ATS records use the scorecard reference source. Mismatches are surfaced as a source-definition confounder, not silently reconciled.',games:games.map(({input,...rest})=>rest),summary:{agree:games.filter(g=>g.comparison==='AGREE').length,disagree:games.filter(g=>g.comparison==='DISAGREE').length,neutralInvolved:games.filter(g=>g.comparison==='NEUTRAL_INVOLVED').length,sourceRecordMatches:alignmentSides.filter(x=>x.matchesV1SeasonRecord).length,sourceRecordMismatches:alignmentSides.filter(x=>!x.matchesV1SeasonRecord).length}};
  fs.writeFileSync('ats-trends-v2-week04-input.json',JSON.stringify(inputOut,null,2)+'\n');
  fs.writeFileSync('ats-trends-v2-week04-results.json',JSON.stringify(results,null,2)+'\n');
  console.log(JSON.stringify(results.summary));
}

main().catch(err=>{console.error(err);process.exit(1);});
