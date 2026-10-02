const http = require('http');
const fs = require('fs');

const port = process.env.PORT || 10000;
const BASE_URL = process.env.BASE_URL || 'https://monopoly-command-center-v67.floot.app/_cdn/static/f4ebb851-c03c-451c-81c5-343be9983db0-command-center-v67-all3-currentmodel.txt';
const gameDetailUiPatch = fs.readFileSync('game-detail-ui-patch.html', 'utf8');
const mobilePatch = fs.readFileSync('mobile-patch.html', 'utf8');
const mobileNavFix = fs.readFileSync('mobile-nav-fix.html', 'utf8');
const week4IntegrationPatch = fs.readFileSync('week4-native-integration-patch.html', 'utf8');

const VERSION = 'week4-native-v2-2026-10-02';

function game(rank, gameName, time, sly, open, current, diff, lean, decision, confidence, catherine, amanda, evidence, why, against, verdict, role, news) {
  return {
    rank,
    game: gameName,
    sly,
    open,
    current,
    diff,
    public: 'Not captured for Week 4 Friday snapshot',
    evidence,
    risk: against,
    state: decision,
    lean,
    catherine,
    amanda,
    role,
    decision,
    confidence,
    why,
    against,
    verdict,
    time,
    whyPlay: verdict,
    sportsline: null,
    gridiron: null,
    news,
    publicSide: null,
    publicPct: null,
    moneyPct: null,
    moneySide: null,
    change: diff === '0.0' ? 'MARKET_EQUAL' : 'SOURCE_SENSITIVE_OR_DISPUTED',
    sportslineMeta: null,
    marketNote: evidence
  };
}

const WEEK4_GAMES = [
  game(1,'DAL @ HOU','Sun 1:00 PM','HOU -3','HOU -2.5','HOU -3.5','-0.5','HOU -3','PLAY','Medium',900,700,
    'Frozen V2: HOU -3 is source-sensitive. VegasInsider was HOU -3 while Action was HOU -3.5; modeled net edge ranges from roughly +0.2% to +3.2% depending on anchor.',
    'Dallas secondary/LB availability concerns are directionally compatible with Houston, and Action showed a half-point of Sly price value.',
    'VegasInsider remained exactly HOU -3, so this is not a broad-market stale line. Roof status and final Dallas/Houston inactives still need Sunday verification.',
    'Conditional Friday candidate. Keep sized exposure only while the Sunday multi-book market supports a worse Houston number than Sly -3.','Conditional source-sensitive edge',[
      {initials:'INJ',name:'Friday injury context',team:'DAL–HOU',time:'Fri Oct 2',headline:'Dallas secondary/LB availability is the main personnel flag',detail:'Dallas CB Cobie Durant, LB DeMarvion Overshown and CB Shavon Revel Jr. were DNP in the Friday research snapshot. Houston LB Azeez Al-Shaair was DNP; Will Anderson Jr. was full.',source:'Official NFL/team Friday reports'},
      {initials:'WX',name:'Weather / venue',team:'HOU',time:'Fri snapshot',headline:'Retractable-roof game',detail:'Outdoor Houston heat is secondary unless roof status changes; confirm roof status Sunday.',source:'Friday weather review'}
    ]),
  game(2,'LAC @ SEA','Sun 4:25 PM','SEA -7','SEA -3','SEA -7.5','-0.5','SEA -7','PLAY','Medium',900,700,
    'Frozen V2: SEA -7 is source-sensitive. VegasInsider was SEA -7 while Action was SEA -7.5; modeled net edge ranges from roughly +0.2% to +3.3% depending on anchor.',
    'Chargers injury concerns and Seattle’s improving health trend align with the Seattle side, while Action showed a half-point of Sly price value.',
    'VegasInsider remained exactly SEA -7, and 7 is a key number. The case weakens materially if the broader market centers at -7.',
    'Conditional Friday candidate. Preserve the key-number advantage only if Sunday books broadly move to SEA -7.5 or worse.','Conditional source-sensitive edge',[
      {initials:'INJ',name:'Friday injury context',team:'LAC–SEA',time:'Fri Oct 2',headline:'Chargers carried key DNPs while Seattle health trended better',detail:'LAC WR Ladd McConkey and DT Dalvin Tomlinson were DNP in the Friday snapshot. Seattle had several key players full while Julian Love remained limited.',source:'Official NFL/team Friday reports'},
      {initials:'WX',name:'Weather',team:'SEA',time:'Fri snapshot',headline:'Benign Seattle forecast',detail:'Mostly sunny around 68–70F with light wind in the Friday forecast.',source:'Friday weather review'}
    ]),
  game(3,'IND @ WAS','Sun 9:30 AM ET · London','IND -3.5','WAS -1.5','IND -3.5','source split','NO ROBUST TAKE','WATCH','Low-Med',0,0,
    'Frozen V2 is source-disputed at Sly IND -3.5: VegasInsider was IND -4.5 while Action was IND -3.5. Context strongly favors Indianapolis, but context does not become a model vote.',
    'Jayden Daniels was ruled out and Marcus Mariota was set to start; Washington also had an OL starter out. VI already showed a full point of value to Sly.',
    'Action remained exactly at Sly -3.5, creating a high double-counting risk if the Daniels news is already fully priced.',
    'Highest-priority Sunday watch. Upgrade only if the broad market consolidates around IND -4/-4.5 or worse while Sly remains -3.5.','High-priority market watch',[
      {initials:'QB',name:'Quarterback status',team:'WAS',time:'Fri Oct 2',headline:'Jayden Daniels ruled out; Marcus Mariota to start',detail:'Washington’s starting-QB absence is the largest contextual item in the matchup.',source:'NFL official Friday news'},
      {initials:'INJ',name:'Washington availability',team:'WAS',time:'Fri Oct 2',headline:'Sam Cosmi and Nick Cross ruled out',detail:'Washington also entered the London game without an OL starter and a safety.',source:'Official team injury report'},
      {initials:'WX',name:'London weather',team:'IND–WAS',time:'Fri snapshot',headline:'Benign game-window weather',detail:'Around 72F and dry in the Friday forecast.',source:'Met Office Friday review'}
    ]),
  game(4,'DEN @ SF','Sun 4:25 PM','SF -3','SF -2.5','SF -2.5','+0.5','NO ROBUST TAKE','WATCH','Low-Med',0,0,
    'Frozen V2 is source-disputed at DEN +3 / SF -3: VegasInsider was SF -3 while Action was SF -2.5.',
    'San Francisco carried heavy injury volume, which qualitatively strengthens the Denver case, and Sly DEN +3 is better than an Action DEN +2.5.',
    'The exact distribution around the key number 3 matters. VegasInsider remained market-equal to Sly, so this is not a confirmed broad-market edge.',
    'Source-disputed hold. Reassess the multi-book share at SF -2.5 vs -3 after final inactives.','Source-disputed hold',[
      {initials:'INJ',name:'49ers injury context',team:'SF',time:'Fri Oct 2',headline:'San Francisco carried heavy Friday injury volume',detail:'Nick Bosa, Dre Greenlaw and several others were among Friday DNPs in the research snapshot; Trent Williams was limited and Christian McCaffrey was full.',source:'Official NFL/team Friday reports'},
      {initials:'WX',name:'Weather',team:'SF',time:'Fri snapshot',headline:'Heat advisory',detail:'Hot and mostly sunny, upper 80s, with a heat advisory active in the Friday forecast.',source:'NWS Friday review'}
    ]),
  game(5,'NE @ BUF','Sun 1:00 PM','BUF -7','BUF -3','BUF -6.5','+0.5','NO ROBUST TAKE','WATCH','Low-Med',0,0,
    'Frozen V2 is source-disputed at Sly NE +7 / BUF -7: VegasInsider was BUF -7 while Action was BUF -6.5.',
    'The key-number +7 can be valuable to New England versus a -6.5 market.',
    'New England’s Friday injury context points the opposite way, and VI remained exactly at Sly -7.',
    'Source-disputed hold. Require broad-market evidence around 6.5/7 plus final Patriots defensive/OL statuses.','Source-disputed hold',[
      {initials:'INJ',name:'Patriots injury context',team:'NE',time:'Fri Oct 2',headline:'Multiple high-value New England DNPs',detail:'Christian Barmore, Christian Gonzalez and Morgan Moses were DNP in the latest Friday research snapshot.',source:'Official Patriots/NFL Friday report'},
      {initials:'WX',name:'Weather',team:'BUF',time:'Fri snapshot',headline:'Benign Orchard Park forecast',detail:'Mostly sunny around 66–68F with light wind.',source:'Friday weather review'}
    ]),
  game(6,'ARI @ NYG','Sun 1:00 PM','ARI -2.5','NYG -7','ARI -2.5','0.0','NO TAKE','PASS','Neutral',0,0,
    'Sly and both preserved Friday market sources were ARI -2.5 after an extreme favorite flip from NYG -7.',
    'The opener-to-Friday move is important history, and New York LT Andrew Thomas was DNP.',
    'Current price is market-equal; the opener is not a decision-time edge signal.',
    'Pass for now. Revisit only on new QB/personnel news or material Sunday market divergence.','Friday pass',[
      {initials:'INJ',name:'Giants injury context',team:'NYG',time:'Fri Oct 2',headline:'Andrew Thomas DNP; Tyrone Tracy limited',detail:'New York’s left tackle status is the main Friday personnel item.',source:'Official Friday injury research'},
      {initials:'WX',name:'Weather',team:'NYG',time:'Fri snapshot',headline:'Possible later showers',detail:'Around 66F with shower risk increasing after 2 PM.',source:'Friday weather review'}
    ]),
  game(7,'ATL @ NO','Mon 8:15 PM','NO -2.5','NO -2.5','NO -2.5','0.0','NO -2.5','WATCH','Minimum filler',100,100,
    'Sly and preserved Friday market sources were all NO -2.5. Frozen V2 has no material price edge.',
    'Indoor game; no major QB change was flagged in the Friday research.',
    'This side is included only to satisfy portfolio minimum-game requirements, not because the model found an ATS edge.',
    '$100 minimum filler only. Do not increase without new Sunday evidence.','Minimum-wager filler; no validated edge',[
      {initials:'INJ',name:'Friday injury context',team:'ATL–NO',time:'Fri Oct 2',headline:'Edge-defender availability to monitor',detail:'Several defensive front-seven players were DNP/limited across the two teams in the Friday snapshot.',source:'Official Friday injury research'},
      {initials:'WX',name:'Venue',team:'NO',time:'Fri snapshot',headline:'Indoor game',detail:'Weather is not expected to materially affect play.',source:'Venue/weather review'}
    ]),
  game(8,'TEN @ BAL','Sun 1:00 PM','BAL -11.5','BAL -8.5','BAL -11.5','0.0','NO TAKE','PASS','Neutral',0,0,
    'Sly and both Friday market sources were BAL -11.5 after a large move through 10.',
    'Lamar Jackson progressed to full participation Friday.',
    'The current number is market-equal and rain risk may add variance rather than side edge.',
    'Pass for now. Refresh weather and any movement away from -11.5 Sunday.','Friday pass',[
      {initials:'QB',name:'Quarterback status',team:'BAL',time:'Fri Oct 2',headline:'Lamar Jackson full Friday',detail:'Friday participation reduced quarterback uncertainty.',source:'Official Friday injury report'},
      {initials:'WX',name:'Weather',team:'BAL',time:'Fri snapshot',headline:'Rain risk',detail:'Showers likely with roughly a 70% precipitation chance in the Friday forecast.',source:'Friday weather review'}
    ]),
  game(9,'DET @ CAR','Sun 8:20 PM','DET -3.5','DET -3','DET -3.5','0.0','NO TAKE','PASS','Neutral',0,0,
    'Sly and both Friday market sources were DET -3.5.',
    'Carolina ruled out WR Xavier Legette and LG Damien Lewis; weather carried substantial rain risk.',
    'The line is already market-equal despite those known contextual negatives; rain may increase variance.',
    'Pass for now. Refresh weather severity and any move off 3.5.','Friday pass',[
      {initials:'INJ',name:'Panthers availability',team:'CAR',time:'Fri Oct 2',headline:'Two Carolina starters ruled out',detail:'WR Xavier Legette and LG Damien Lewis were ruled out in the Friday snapshot.',source:'Official Panthers Friday report'},
      {initials:'WX',name:'Weather',team:'CAR',time:'Fri snapshot',headline:'High rain materiality',detail:'Friday forecast showed roughly 80% precipitation risk.',source:'Friday weather review'}
    ]),
  game(10,'NYJ @ CHI','Sun 1:00 PM','CHI -3.5','CHI -8.5','CHI -3.5','0.0','NO TAKE','PASS','Neutral',0,0,
    'Sly and both Friday market sources were CHI -3.5 after a major move from CHI -8.5.',
    'The Jets had multiple offensive starters out while Chicago carried QB uncertainty and multiple DNPs.',
    'High-impact context exists on both sides and is already associated with a major market adjustment.',
    'Pass for now. Confirm Chicago’s starter and final OL/skill statuses Sunday.','Friday pass',[
      {initials:'INJ',name:'Jets availability',team:'NYJ',time:'Fri Oct 2',headline:'Multiple offensive starters ruled out',detail:'Breece Hall, Adonai Mitchell, Mason Taylor and Dylan Parham were among Jets players ruled out in the Friday research snapshot.',source:'Official Friday injury research'},
      {initials:'QB',name:'Chicago QB status',team:'CHI',time:'Fri Oct 2',headline:'Starting-QB uncertainty remained Friday',detail:'Caleb Williams remained DNP with a hamstring issue in the Friday research snapshot.',source:'Official Bears/NFL Friday research'}
    ]),
  game(11,'JAX @ CIN','Sun 1:00 PM','CIN -2.5','CIN -2.5','CIN -2.5','0.0','CIN -2.5','WATCH','Minimum filler',100,100,
    'Sly and both Friday market sources were CIN -2.5. Frozen V2 has no material price edge.',
    'Weather is benign and Cincinnati carried some interior defense/OL DNPs.',
    'No verified multi-source ATS convergence exists; this is not a validated edge.',
    '$100 minimum filler only. Do not increase without new evidence.','Minimum-wager filler; no validated edge',[
      {initials:'INJ',name:'Friday injury context',team:'JAX–CIN',time:'Fri Oct 2',headline:'Cincinnati interior defense/OL DNPs',detail:'Kyle Dugger, B.J. Hill and Dalton Risner were DNP in the Friday research snapshot; Jacksonville had several limited participants.',source:'Official Friday injury research'},
      {initials:'WX',name:'Weather',team:'CIN',time:'Fri snapshot',headline:'Benign forecast',detail:'Mostly sunny around 74F with calm wind.',source:'Friday weather review'}
    ]),
  game(12,'GB @ TB','Sun 1:00 PM','GB -3.5','GB -1.5','GB -3.5','0.0','NO TAKE','PASS','Neutral',0,0,
    'Sly and both Friday market sources were GB -3.5 after a major QB/news-driven adjustment.',
    'Friday research recorded Tampa Bay starting-QB news as the dominant matchup change.',
    'The market had already adjusted materially, creating a high risk of double-counting known news.',
    'Pass for now. Revisit only on QB/status reversal or renewed market divergence.','Friday pass',[
      {initials:'QB',name:'Friday quarterback context',team:'TB',time:'Fri Oct 2',headline:'Major Tampa Bay QB news drove the matchup context',detail:'The Friday research snapshot treated Tampa’s quarterback situation as already materially reflected in the market.',source:'NFL Friday research snapshot'},
      {initials:'WX',name:'Weather',team:'TB',time:'Fri snapshot',headline:'Heat and thunderstorm risk',detail:'Near 90F with scattered showers/thunderstorms possible in the Friday forecast.',source:'Friday weather review'}
    ]),
  game(13,'KC @ LV','Sun 4:25 PM','KC -4.5','KC -5.5','KC -4.5','0.0','LV +4.5','WATCH','Minimum filler',100,100,
    'Sly and both Friday market sources were KC -4.5. Frozen V2 has no material price edge.',
    'Indoor game; offensive-line availability was the main Friday context.',
    'LV +4.5 is included only as a minimum portfolio filler, not a validated model edge.',
    '$100 minimum filler only. Do not increase without material Sunday evidence.','Minimum-wager filler; no validated edge',[
      {initials:'INJ',name:'Friday OL context',team:'KC–LV',time:'Fri Oct 2',headline:'Offensive-line availability to monitor',detail:'KC T Josh Simmons and LV G Jackson Powers-Johnson were among the Friday availability items in the research snapshot.',source:'Official Friday injury research'},
      {initials:'WX',name:'Venue',team:'LV',time:'Fri snapshot',headline:'Indoor game',detail:'Outdoor Las Vegas heat is not expected to affect play.',source:'Venue/weather review'}
    ]),
  game(14,'LAR @ PHI','Sun 1:00 PM','LAR -3.5','LAR -1.5','LAR -3.5','0.0','NO TAKE','PASS','Neutral',0,0,
    'Sly and both Friday market sources were LAR -3.5.',
    'Both teams carried meaningful injury uncertainty and Philadelphia weather required a Sunday refresh.',
    'Current price is market-equal and the Friday contextual picture is mixed.',
    'Pass for now. Recheck final injury designations, wind/precipitation, and whether the market settles at -3 or -3.5.','Friday pass',[
      {initials:'INJ',name:'Friday injury context',team:'LAR–PHI',time:'Fri Oct 2',headline:'Multiple Philadelphia DNPs; Rams skill player limited',detail:'Philadelphia carried several DNPs while Puka Nacua was limited in the Friday research snapshot.',source:'Official Friday injury research'},
      {initials:'WX',name:'Weather',team:'PHI',time:'Fri snapshot',headline:'Sunday refresh required',detail:'Cool/cloudy conditions with precipitation timing requiring a Sunday update.',source:'Friday weather review'}
    ]),
  game(15,'MIA @ MIN','Sun 4:05 PM','MIN -10.5','MIN -7.5','MIN -10.5','0.0','NO TAKE','PASS','Neutral',0,0,
    'Sly and both Friday market sources were MIN -10.5 after a large move from -7.5.',
    'The Friday research snapshot included major Minnesota skill-position news, but the current Sly line already matched the preserved market.',
    'Known personnel news appears substantially priced and the large number leaves little reason to manufacture an edge.',
    'Pass for now. Revisit only on material movement away from MIN -10.5 or new skill-position news.','Friday pass',[
      {initials:'INJ',name:'Friday skill-position context',team:'MIA–MIN',time:'Fri Oct 2',headline:'Major skill-position availability already reflected in price',detail:'The Friday research snapshot treated Minnesota’s top-receiver availability and Miami backfield absences as known market information.',source:'NFL Friday research snapshot'},
      {initials:'WX',name:'Venue',team:'MIN',time:'Fri snapshot',headline:'Indoor game',detail:'Weather is not a game factor.',source:'Venue/weather review'}
    ])
];

function sourceRow(rank, gameName, time, sly, ourPick, ourState, ourGrade) {
  return {
    game: gameName,
    time,
    sly,
    ourGrade,
    ourPick,
    ourState,
    ourRank: rank,
    sportsGrade: '—',
    sportsPick: 'UNVERIFIED',
    sportsType: 'Unavailable',
    sportsScore: 'Full Week 4 ATS slate not publicly verified',
    sportsCurrent: '—',
    sportsPickCount: 0,
    gridGrade: '—',
    gridPick: 'UNVERIFIED',
    gridProb: 0,
    gridLine: '—',
    gridOther: 'No authoritative Week 4 table verified',
    agreement: '0/0 incomplete'
  };
}

const WEEK4_SOURCE_DATA = WEEK4_GAMES.map(g => sourceRow(
  g.rank,
  g.game,
  g.time,
  g.sly,
  (g.game === 'DAL @ HOU' ? 'HOU -3' : g.game === 'LAC @ SEA' ? 'SEA -7' : 'NO ROBUST TAKE'),
  g.decision,
  (g.game === 'DAL @ HOU' || g.game === 'LAC @ SEA') ? 'B' : '—'
));

function replaceConstArray(source, marker, value) {
  const markerIndex = source.indexOf(marker);
  if (markerIndex < 0) throw new Error(`Base app missing ${marker}`);
  const start = source.indexOf('[', markerIndex + marker.length);
  if (start < 0) throw new Error(`Base app missing array after ${marker}`);
  let depth = 0;
  let quote = null;
  let escaped = false;
  for (let i = start; i < source.length; i++) {
    const ch = source[i];
    if (quote) {
      if (escaped) escaped = false;
      else if (ch === '\\') escaped = true;
      else if (ch === quote) quote = null;
      continue;
    }
    if (ch === '"' || ch === "'" || ch === '`') { quote = ch; continue; }
    if (ch === '[') depth++;
    else if (ch === ']') {
      depth--;
      if (depth === 0) return source.slice(0, start) + JSON.stringify(value) + source.slice(i + 1);
    }
  }
  throw new Error(`Unterminated array after ${marker}`);
}

let cachedHtml = null;
let loadError = null;
let healthState = null;

async function loadApp() {
  if (cachedHtml) return cachedHtml;
  const response = await fetch(BASE_URL, { redirect: 'follow' });
  if (!response.ok) throw new Error(`Base app fetch failed: ${response.status} ${response.statusText}`);
  let base = await response.text();
  if (!base.includes('<html') && !base.includes('<!DOCTYPE')) throw new Error('Base app response is not HTML');

  // Critical: the upstream app keeps games/sourceData in lexical `const` arrays.
  // Replace those arrays before the original app executes so every native component
  // (Games, game detail, source comparison, search/filtering, recommended plays)
  // reads Week 4 directly rather than a disconnected window.* shadow object.
  base = replaceConstArray(base, 'const games=', WEEK4_GAMES);
  base = replaceConstArray(base, 'const sourceData=', WEEK4_SOURCE_DATA);

  const combinedPatch = `${gameDetailUiPatch}\n${mobilePatch}\n${mobileNavFix}\n${week4IntegrationPatch}`;
  cachedHtml = base.includes('</body>') ? base.replace('</body>', `${combinedPatch}\n</body>`) : `${base}\n${combinedPatch}`;

  healthState = {
    status: 'ok',
    version: VERSION,
    bytes: Buffer.byteLength(cachedHtml),
    nativeWeek4GamesInjected: cachedHtml.includes('const games=[{"rank":1,"game":"DAL @ HOU"'),
    nativeWeek4SourcesInjected: cachedHtml.includes('const sourceData=[{"game":"DAL @ HOU"'),
    week4IntegrationPatchLoaded: cachedHtml.includes('week4-native-integration-layer'),
    expectedEligibleGames: WEEK4_GAMES.length,
    source: 'native-week4-data-injection-preserving-existing-ux'
  };
  return cachedHtml;
}

const server = http.createServer(async (req, res) => {
  if (req.url === '/healthz' || req.url === '/_version') {
    try {
      await loadApp();
      res.writeHead(200, {'content-type':'application/json; charset=utf-8','cache-control':'no-store'});
      return res.end(JSON.stringify(healthState));
    } catch (err) {
      loadError = String(err && err.message ? err.message : err);
      res.writeHead(503, {'content-type':'application/json; charset=utf-8'});
      return res.end(JSON.stringify({status:'error', version:VERSION, error:loadError}));
    }
  }
  try {
    const html = await loadApp();
    res.writeHead(200, {'content-type':'text/html; charset=utf-8','cache-control':'no-store, max-age=0'});
    res.end(html);
  } catch (err) {
    loadError = String(err && err.message ? err.message : err);
    res.writeHead(503, {'content-type':'text/plain; charset=utf-8'});
    res.end(`Command Center failed to load: ${loadError}`);
  }
});

server.listen(port, '0.0.0.0', async () => {
  console.log(`Command Center listening on ${port}`);
  try {
    const html = await loadApp();
    console.log(`Loaded ${VERSION}: ${Buffer.byteLength(html)} bytes; native Week 4 game/source arrays injected`);
  } catch (err) {
    console.error('Initial canonical app load failed:', err);
  }
});