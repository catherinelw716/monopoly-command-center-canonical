'use strict';
const fs=require('fs'),assert=require('assert');
const page=fs.readFileSync('five-factor-scorecard-page.html','utf8');
const server=fs.readFileSync('server-v7.js','utf8');
const input=JSON.parse(fs.readFileSync('five-factor-scorecard-data-week04.json','utf8'));
const engine=require('./five-factor-scorecard-engine');
const slate=engine.scoreSlate(input);
assert.equal(slate.games.length,15,'15 eligible games required');
for(const g of slate.games){for(const k of ['lineMovement','trends','money','defense','keyNumbers'])assert(g.fiveFactor[k],`${g.game} missing ${k}`);assert(!JSON.stringify(g.fiveFactor).includes('undefined'),`${g.game} contains undefined`);}
assert(page.includes("location.pathname==='/spread-scorecard'"),'direct /spread-scorecard route renderer missing');
assert(/Money \/ Handle/i.test(page),'money/handle label missing');
assert(/Line Movement/i.test(page)&&/ATS Trends/i.test(page)&&/Defense/i.test(page)&&/Key Numbers/i.test(page),'factor labels missing');
assert(page.includes('DISAGREES')||page.includes('mainSystemComparison'),'main-system comparison renderer missing');
assert(/Line movement and money.*(correlat|related)/i.test(page),'correlation disclosure missing');
assert(server.includes("fs.readFileSync('five-factor-scorecard-page.html'"),'server does not inject scorecard page');
assert(server.includes('window.FIVE_FACTOR_PUBLIC'),'server does not expose canonical scorecard state');
assert(server.includes('fiveFactor15')&&server.includes('fiveFactorHandleOnly'),'health contract missing scorecard checks');
for(const bad of ['undefined','[object Object]'])assert(!page.includes(`>${bad}<`),`literal ${bad} in page`);
console.log('Five-factor page/render contract QA passed');
