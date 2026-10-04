'use strict';
const fs=require('fs');
const path=require('path');
const originalRead=fs.readFileSync.bind(fs);
const latest=JSON.parse(originalRead(path.join(__dirname,'week4-market-lines-latest.json'),'utf8'));

function patchedJson(filePath,encoding){
  const base=path.basename(String(filePath));
  const raw=originalRead(filePath,encoding);
  if(encoding!=='utf8'&&encoding!=='utf-8')return raw;

  if(base==='ats-trends-v2-ui-patch.html'){
    const today=originalRead(path.join(__dirname,'week4-today-page.html'),'utf8');
    return raw+'\n'+today;
  }

  if(base==='week4-nfelo-2026-10-03-1720ET.json'){
    const data=JSON.parse(raw);
    data.captured_at_local=latest.capturedAt;
    return JSON.stringify(data);
  }

  if(base==='week4-live-market-context-2026-10-03-1710ET.json'){
    const data=JSON.parse(raw);
    data.captured_at_local=latest.capturedAt;
    data.snapshot_type='SATURDAY_LATEST_MARKET_CONTEXT';
    data.market_source=latest.source+' · '+latest.sourceNote;
    for(const [game,m] of Object.entries(latest.games)){
      if(!data.games[game])continue;
      data.games[game].action_spread=m.display;
      data.games[game].market_note=`Latest market: ${m.display} (${latest.source}, ${latest.capturedAt}). ${data.games[game].market_note||''}`;
    }
    return JSON.stringify(data);
  }

  if(base==='five-factor-scorecard-data-week04.json'){
    const data=JSON.parse(raw);
    data.capturedAt=latest.capturedAt;
    data.sources=data.sources||{};
    data.sources.market=latest.source+' · '+latest.sourceNote;
    for(const g of data.games||[]){
      const m=latest.games[g.game];
      if(!m)continue;
      g.market=g.market||{};
      g.market.currentAway=m.currentAway;
      g.market.source=latest.source;
      g.market.capturedAt=latest.capturedAt;
    }
    return JSON.stringify(data);
  }

  return raw;
}

fs.readFileSync=patchedJson;
require('./server-v8.js');
