'use strict';
const fs=require('fs'),vm=require('vm');
const html=fs.readFileSync('week4-overview-page.html','utf8');
const required=['Prediction → Price → Confirmation → Context → Decision','1 · Prediction','2 · Sly vs Market','3 · External Confirmation','4 · 5-Factor Evidence','5 · Material Context','6 · Decision','does <b>not</b> create a new master score','legacy 100-point score remains audit-only','Sizing remains downstream'];
for(const x of required)if(!html.includes(x))throw new Error('missing synthesis contract: '+x);
const m=html.match(/<script id="week4-overview-page-script">([\s\S]*?)<\/script>/);
if(!m)throw new Error('missing overview script');
new vm.Script(m[1]);
console.log('Week 4 overview synthesis QA passed');
