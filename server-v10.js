'use strict';
const http=require('http');
const fs=require('fs');
const {spawn}=require('child_process');

const port=Number(process.env.PORT||10000);
const innerPort=port===10000?10001:port+1;
const todayPatch=fs.readFileSync('week4-today-page.html','utf8');

const child=spawn(process.execPath,['server-v9.js'],{
  env:{...process.env,PORT:String(innerPort)},
  stdio:'inherit'
});
child.on('exit',(code,signal)=>{
  console.error('inner Command Center exited',code,signal);
  process.exit(code||1);
});
process.on('SIGTERM',()=>child.kill('SIGTERM'));
process.on('SIGINT',()=>child.kill('SIGINT'));

function innerRequest(pathname){
  return new Promise((resolve,reject)=>{
    const req=http.request({hostname:'127.0.0.1',port:innerPort,path:pathname,method:'GET'},res=>{
      const chunks=[];
      res.on('data',c=>chunks.push(c));
      res.on('end',()=>resolve({status:res.statusCode||500,headers:res.headers,body:Buffer.concat(chunks)}));
    });
    req.on('error',reject);req.end();
  });
}
async function waitForInner(){
  for(let i=0;i<80;i++){
    try{const r=await innerRequest('/_version');if(r.status===200)return;}catch(e){}
    await new Promise(r=>setTimeout(r,100));
  }
  throw new Error('inner server did not become ready');
}
function globalsFrom(html){
  const m=html.match(/<script>window\.WEEK4_CURRENT_META=[\s\S]*?<\/script>/);
  if(!m)throw new Error('Week 4 globals script missing from inner app');
  return m[0];
}
function standaloneToday(html){
  const globals=globalsFrom(html);
  return `<!doctype html><html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta name="command-center-week" content="4"><title>Today · Week 4 · NFL Monopoly</title>${globals}${todayPatch}</head><body class="w4today-standalone"><div style="padding:24px;font-family:system-ui;color:#e5edf6;background:#07111f;min-height:100vh">Loading Week 4…</div></body></html>`;
}
function navGuard(){return `<script id="today-route-guard">(function(){function go(e){var c=e.target&&e.target.closest&&e.target.closest('[data-view="today"]');if(!c)return;e.preventDefault();e.stopImmediatePropagation();location.assign('/');}document.addEventListener('click',go,true);document.addEventListener('touchend',go,{capture:true,passive:false});})();</script>`;}
async function proxy(req,res,pathOverride){
  const targetPath=pathOverride||req.url;
  const opts={hostname:'127.0.0.1',port:innerPort,path:targetPath,method:req.method,headers:{...req.headers,host:`127.0.0.1:${innerPort}`}};
  const p=http.request(opts,ir=>{
    const chunks=[];ir.on('data',c=>chunks.push(c));ir.on('end',()=>{
      let body=Buffer.concat(chunks);const headers={...ir.headers};delete headers['content-length'];
      const ct=String(headers['content-type']||'');
      if(req.method==='GET'&&ct.includes('text/html')){
        let text=body.toString('utf8');
        text=text.replace('</body>',`${navGuard()}</body>`);
        body=Buffer.from(text);
        headers['cache-control']='no-store, no-cache, must-revalidate, max-age=0';
        headers['pragma']='no-cache';
        headers['expires']='0';
      }
      res.writeHead(ir.statusCode||500,headers);res.end(body);
    });
  });
  p.on('error',e=>{res.writeHead(502,{'content-type':'text/plain'});res.end(String(e));});
  if(req.method==='GET'||req.method==='HEAD')p.end();else req.pipe(p);
}
async function sendWeek4Today(res){
  const root=await innerRequest('/?full=1');
  const html=standaloneToday(root.body.toString('utf8'));
  const ok=html.includes('Today — Week 4')&&!html.includes('Week 3');
  if(!ok)throw new Error('Refusing to serve Today: Week 4 render contract failed');
  res.writeHead(200,{
    'content-type':'text/html; charset=utf-8',
    'cache-control':'no-store, no-cache, must-revalidate, max-age=0',
    'pragma':'no-cache',
    'expires':'0',
    'x-command-center-route':'week4-today-root-v11',
    'x-command-center-week':'4'
  });
  res.end(html);
}

waitForInner().then(()=>{
  const server=http.createServer(async(req,res)=>{
    try{
      const url=new URL(req.url,'http://local');

      // Canonical root is Week 4 Today itself. No redirect and no legacy shell.
      if(req.method==='GET'&&(url.pathname==='/'||url.pathname==='/today'||url.pathname==='/today/')){
        return sendWeek4Today(res);
      }

      // Explicit escape hatch for the older multi-view shell and drill-downs.
      if(req.method==='GET'&&(url.pathname==='/full'||url.pathname==='/full/')){
        return proxy(req,res,'/?full=1');
      }

      if(req.method==='GET'&&url.pathname==='/today-healthz'){
        const root=await innerRequest('/?full=1');
        const html=standaloneToday(root.body.toString('utf8'));
        const checks={
          directRoot:true,
          week4Title:html.includes('Today — Week 4'),
          noWeek3:!html.includes('Week 3'),
          week4Meta:html.includes('name="command-center-week" content="4"'),
          currentGames:html.includes('window.WEEK4_CURRENT_PUBLIC'),
          latestMarketStamp:html.includes('2026-10-03T21:45:00-04:00')
        };
        const ok=Object.values(checks).every(Boolean);
        res.writeHead(ok?200:503,{'content-type':'application/json','cache-control':'no-store'});
        return res.end(JSON.stringify({status:ok?'ok':'error',route:'canonical root + /today server-rendered Week 4',week:4,checks}));
      }

      return proxy(req,res);
    }catch(e){res.writeHead(500,{'content-type':'text/plain','cache-control':'no-store'});res.end(String(e));}
  });
  server.listen(port,'0.0.0.0',()=>console.log(`Command Center root-v11 on ${port}; / and /today directly serve Week 4`));
}).catch(e=>{console.error(e);process.exit(1);});
