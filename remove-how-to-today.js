'use strict';
const fs = require('fs');
const path = 'server-local.js';
let s = fs.readFileSync(path, 'utf8');

if (!s.includes('How to read Today')) {
  console.log('How to read Today already removed');
  process.exit(0);
}

const start = s.indexOf("    '<div class=\"hero-grid\">");
const end = s.indexOf("    '<div class=\"today-rule\">", start);
if (start < 0 || end < 0) throw new Error('Could not locate Today hero/how-to block');

const compact = "    '<div class=\"panel slate-state\" style=\"margin-bottom:12px\"><div class=\"eyebrow\">Current operating picture</div><div class=\"state-title\">Week 4 · Saturday night</div><div class=\"kpis\"><div class=\"kpi\"><small>Catherine</small><b>'+money(current.balances.Catherine)+'</b><span>#28 after Week 3</span></div><div class=\"kpi\"><small>Amanda</small><b>'+money(current.balances.Amanda)+'</b><span>#65 after Week 3</span></div><div class=\"kpi\"><small>Household outlay</small><b>'+money(current.working_portfolio.household_outlay)+'</b><span>current working portfolio</span></div><div class=\"kpi\"><small>Market snapshot</small><b>9:45 PM ET</b><span>'+esc(latest.source)+'</span></div></div></div>'+\n";
s = s.slice(0, start) + compact + s.slice(end);

const ruleStart = s.indexOf("    '<div class=\"today-rule\"><b>No master consensus score.</b>");
if (ruleStart >= 0) {
  const topStart = s.indexOf('topAlignedHtml+', ruleStart);
  if (topStart < 0) throw new Error('Could not locate Top Aligned block after Today rule');
  s = s.slice(0, ruleStart) + '    ' + s.slice(topStart);
}

s = s.replace("current.version = 'week4-local-shell-v3-top-aligned-2026-10-04';", "current.version = 'week4-local-shell-v4-clean-landing-2026-10-04';");

fs.writeFileSync(path, s);
console.log('Removed How to read Today and redundant rule block');
