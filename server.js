const http = require('http');
const fs = require('fs');
const zlib = require('zlib');

const port = process.env.PORT || 10000;
const packed = fs.readFileSync('app.br.b64', 'utf8').trim();
const html = zlib.brotliDecompressSync(Buffer.from(packed, 'base64'));

const server = http.createServer((req, res) => {
  if (req.url === '/healthz') {
    res.writeHead(200, {'content-type':'text/plain; charset=utf-8'});
    return res.end('ok');
  }
  res.writeHead(200, {
    'content-type': 'text/html; charset=utf-8',
    'cache-control': 'no-store, max-age=0'
  });
  res.end(html);
});

server.listen(port, '0.0.0.0', () => {
  console.log(`Command Center listening on ${port}`);
});
