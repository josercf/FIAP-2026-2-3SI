// server.js
const http = require('http');

http.createServer((req, res) => {
  if (req.url === '/events') {
    res.writeHead(200, {
      'Content-Type': 'text/event-stream',
      'Cache-Control': 'no-cache',
      'Connection': 'keep-alive'
    });
    setInterval(() => {
      res.write(`data: ${JSON.stringify({ status: 'Em trânsito', lat: -23.5, lng: -46.6 })}\n\n`);
    }, 2000);
  }
}).listen(3000, () => console.log('SSE Server na porta 3000'));
