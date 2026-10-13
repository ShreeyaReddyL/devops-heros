// Minimal static server for the CampusFix production build.
// Mirrors frontend/nginx.conf.template: serves dist/ and proxies /api to the
// FastAPI backend, so the browser exercises the real built bundle.
// Usage: node serve-dist.mjs [port] [backendPort]
import { createServer } from 'node:http';
import { readFile } from 'node:fs/promises';
import { extname, join, normalize } from 'node:path';

const PORT = Number(process.argv[2] ?? 3000);
const BACKEND = `http://127.0.0.1:${process.argv[3] ?? 8000}`;
const ROOT = new URL('./dist/', import.meta.url).pathname.replace(/^\/([A-Za-z]:)/, '$1');

const TYPES = {
  '.html': 'text/html; charset=utf-8',
  '.js': 'text/javascript; charset=utf-8',
  '.css': 'text/css; charset=utf-8',
  '.svg': 'image/svg+xml',
  '.ico': 'image/x-icon',
};

const server = createServer(async (req, res) => {
  const url = new URL(req.url, 'http://localhost');

  if (url.pathname === '/api' || url.pathname.startsWith('/api/')) {
    const chunks = [];
    for await (const c of req) chunks.push(c);
    const body = Buffer.concat(chunks);
    try {
      const upstream = await fetch(BACKEND + url.pathname + url.search, {
        method: req.method,
        headers: { 'Content-Type': req.headers['content-type'] ?? 'application/json' },
        body: ['GET', 'HEAD'].includes(req.method) ? undefined : body,
      });
      const text = await upstream.text();
      res.writeHead(upstream.status, { 'Content-Type': upstream.headers.get('content-type') ?? 'text/plain' });
      res.end(text);
    } catch (err) {
      res.writeHead(502, { 'Content-Type': 'application/json' });
      res.end(JSON.stringify({ detail: `backend unreachable: ${err.message}` }));
    }
    return;
  }

  // SPA fallback: every non-asset path resolves to index.html.
  const rel = normalize(url.pathname).replace(/^(\.\.[/\\])+/, '');
  let file = join(ROOT, rel);
  try {
    let body = await readFile(file);
    if (extname(file) === '') {
      body = await readFile(join(ROOT, 'index.html'));
    }
    res.writeHead(200, { 'Content-Type': TYPES[extname(file)] ?? 'application/octet-stream' });
    res.end(body);
  } catch {
    res.writeHead(200, { 'Content-Type': TYPES['.html'] });
    res.end(await readFile(join(ROOT, 'index.html')));
  }
});

server.listen(PORT, '127.0.0.1', () => console.log(`CampusFix dist on http://127.0.0.1:${PORT} -> API ${BACKEND}`));