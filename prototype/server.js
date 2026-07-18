const http = require('http');
const fs = require('fs');
const path = require('path');
const { spawn } = require('child_process');

// Поддержка аргументов: node server.js --port 7100 --host 127.0.0.1
function arg(name, fallback) {
  const i = process.argv.indexOf('--' + name);
  return i !== -1 && process.argv[i + 1] ? process.argv[i + 1] : fallback;
}
const PORT = Number(arg('port', process.env.PORT || 7100));
const HOST = arg('host', process.env.HOST || '127.0.0.1');
const ROOT = __dirname;
const REPO = path.join(ROOT, '..');

const mime = {
  '.html': 'text/html; charset=utf-8',
  '.js': 'application/javascript; charset=utf-8',
  '.css': 'text/css; charset=utf-8',
  '.json': 'application/json; charset=utf-8',
  '.png': 'image/png',
  '.jpg': 'image/jpeg',
  '.gif': 'image/gif',
  '.svg': 'image/svg+xml',
  '.ico': 'image/x-icon',
};

/* ===== Авто-пересборка при изменении источников ===== */
// ponytail: пересобираем index.html из шаблона/content через tools/build.py,
// если меняется что-то из источников. Рестарт процесса не нужен — сервер всегда
// читает index.html с диска, а браузер получает no-cache.
let building = false;
let buildQueued = false;
function rebuild(reason) {
  if (building) { buildQueued = true; return; }
  building = true;
  const py = spawn('python', [path.join(REPO, 'tools', 'build.py')], { cwd: REPO });
  let out = '';
  py.stdout.on('data', d => out += d);
  py.stderr.on('data', d => out += d);
  py.on('close', code => {
    building = false;
    console.log(`[build] ${reason || 'init'} → ${code === 0 ? 'ok' : 'ERROR'}` + (code === 0 ? '' : '\n' + out));
    if (buildQueued) { buildQueued = false; rebuild('изменения во время сборки'); }
  });
}

// следим за источниками
[path.join(ROOT, 'index.template.html'), path.join(REPO, 'tools', 'build.py')].forEach(f =>
  fs.watch(f, { persistent: false }, () => rebuild(path.basename(f)))
);
// следим за папкой контента (recursive для вложенных json)
fs.watch(path.join(REPO, 'content'), { persistent: false, recursive: true }, () => rebuild('content/*'));

rebuild('старт');

http.createServer((req, res) => {
  let urlPath = req.url.split('?')[0];
  try {
    urlPath = decodeURIComponent(urlPath);
  } catch (e) {
    // некоторые клиенты шлют URL с неэкранированными символами — используем как есть
  }

  // === Приём записанных образцов: POST /upload-sample?word=мама ===
  if (req.method === 'POST' && urlPath === '/upload-sample') {
    const word = (new URL(req.url, `http://${HOST}`).searchParams.get('word') || 'unknown')
      .replace(/[^\wа-яё-]/gi, '_');
    const dir = path.join(ROOT, '..', 'samples');
    fs.mkdirSync(dir, { recursive: true });
    const n = fs.readdirSync(dir).filter(f => f.startsWith(word + '_')).length + 1;
    const file = path.join(dir, `${word}_${String(n).padStart(2, '0')}.wav`);
    const chunks = [];
    req.on('data', c => chunks.push(c));
    req.on('end', () => {
      const buf = Buffer.concat(chunks);
      // минимальная проверка WAV-заголовка: RIFF....WAVE
      if (buf.length < 12 || buf.toString('ascii', 0, 4) !== 'RIFF' || buf.toString('ascii', 8, 12) !== 'WAVE') {
        res.writeHead(400, { 'Content-Type': 'text/plain; charset=utf-8' });
        res.end('invalid wav');
        return;
      }
      fs.writeFile(file, buf, err => {
        res.writeHead(err ? 500 : 200, { 'Content-Type': 'text/plain; charset=utf-8' });
        res.end(err ? 'error' : 'saved:' + path.basename(file));
      });
    });
    return;
  }

  let filePath = path.join(ROOT, urlPath === '/' ? 'index.html' : urlPath);
  if (!filePath.startsWith(ROOT)) { res.writeHead(403); res.end(); return; }
  fs.readFile(filePath, (err, data) => {
    if (err) { res.writeHead(404); res.end('Not found'); return; }
    const ext = path.extname(filePath).toLowerCase();
    const headers = { 'Content-Type': mime[ext] || 'application/octet-stream' };
    // не кешируем html/js/json — всегда отдаём свежую сборку (иначе браузер показывает старую версию)
    if (ext === '.html' || ext === '.js' || ext === '.json') {
      headers['Cache-Control'] = 'no-cache';
    }
    res.writeHead(200, headers);
    res.end(data);
  });
}).listen(PORT, HOST, () => console.log(`Собери слово: http://${HOST}:${PORT}`));
