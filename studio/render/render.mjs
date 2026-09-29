#!/usr/bin/env node
// Render a scene page to a PNG still or an MP4, one frame at a time.
//
//   node studio/render/render.mjs <scene.html> --still 7.5 --out still.png [--format vertical] [--safe]
//   node studio/render/render.mjs <scene.html> --video --out clip.mp4 [--format vertical] [--fps 30] [--from 0 --to 8]
//
// Uses the headless Chromium that Playwright installed (or $CHROME) over the
// DevTools protocol, and ffmpeg for encoding. No npm packages. Writes
// <out>.json with the inputs' hashes so a render can be traced to its data.
import { spawn, execFileSync } from 'node:child_process';
import { createHash } from 'node:crypto';
import { existsSync, mkdtempSync, readFileSync, readdirSync, rmSync, writeFileSync } from 'node:fs';
import { homedir, tmpdir } from 'node:os';
import { dirname, join, resolve } from 'node:path';
import { pathToFileURL } from 'node:url';

function args() {
  const a = process.argv.slice(2), o = { page: null, format: 'landscape', fps: 30, safe: false };
  for (let i = 0; i < a.length; i++) {
    const k = a[i];
    if (k === '--still') o.still = Number(a[++i]);
    else if (k === '--video') o.video = true;
    else if (k === '--out') o.out = resolve(a[++i]);
    else if (k === '--format') o.format = a[++i];
    else if (k === '--fps') o.fps = Number(a[++i]);
    else if (k === '--from') o.from = Number(a[++i]);
    else if (k === '--to') o.to = Number(a[++i]);
    else if (k === '--safe') o.safe = true;
    else if (!o.page) o.page = resolve(k);
    else throw new Error('Unknown argument ' + k);
  }
  if (!o.page || !o.out || (o.still === undefined && !o.video)) {
    throw new Error('Usage: render.mjs <scene.html> (--still T | --video) --out FILE [--format landscape|vertical]');
  }
  return o;
}

function chromePath() {
  if (process.env.CHROME) return process.env.CHROME;
  const base = join(homedir(), 'Library/Caches/ms-playwright');
  for (const d of readdirSync(base).filter((d) => d.startsWith('chromium_headless_shell-')).sort().reverse()) {
    for (const sub of readdirSync(join(base, d))) {
      const p = join(base, d, sub, 'chrome-headless-shell');
      if (existsSync(p)) return p;
    }
  }
  throw new Error('No headless Chromium found; set CHROME');
}

class CDP {
  constructor(url) { this.ws = new WebSocket(url); this.id = 0; this.pending = new Map(); this.listeners = []; }
  open() {
    return new Promise((res, rej) => {
      this.ws.onopen = res;
      this.ws.onerror = rej;
      this.ws.onmessage = (ev) => {
        const msg = JSON.parse(ev.data);
        if (msg.id && this.pending.has(msg.id)) {
          const { resolve: ok, reject } = this.pending.get(msg.id);
          this.pending.delete(msg.id);
          msg.error ? reject(new Error(msg.error.message)) : ok(msg.result);
        } else this.listeners.forEach((l) => l(msg));
      };
    });
  }
  send(method, params = {}, sessionId) {
    const id = ++this.id;
    this.ws.send(JSON.stringify({ id, method, params, sessionId }));
    return new Promise((ok, reject) => this.pending.set(id, { resolve: ok, reject }));
  }
  once(method, sessionId) {
    return new Promise((ok) => {
      const l = (m) => { if (m.method === method && m.sessionId === sessionId) { this.listeners.splice(this.listeners.indexOf(l), 1); ok(m.params); } };
      this.listeners.push(l);
    });
  }
}

const sha256 = (path) => createHash('sha256').update(readFileSync(path)).digest('hex');

async function main() {
  const o = args();
  const profile = mkdtempSync(join(tmpdir(), 'ft-chrome-'));
  const chrome = spawn(chromePath(), ['--headless', '--remote-debugging-port=0', '--hide-scrollbars', '--force-device-scale-factor=1',
    '--font-render-hinting=none', '--user-data-dir=' + profile, 'about:blank'], { stdio: ['ignore', 'ignore', 'pipe'] });
  const endpoint = await new Promise((ok, fail) => {
    let text = '';
    chrome.stderr.on('data', (d) => { text += d; const m = text.match(/DevTools listening on (ws:\/\/\S+)/); if (m) ok(m[1]); });
    chrome.on('exit', () => fail(new Error('Chromium exited: ' + text.slice(-500))));
  });
  const cdp = new CDP(endpoint);
  const errors = [];
  let ffmpeg = null;
  try {
    await cdp.open();
    const { targetId } = await cdp.send('Target.createTarget', { url: 'about:blank' });
    const { sessionId } = await cdp.send('Target.attachToTarget', { targetId, flatten: true });
    cdp.listeners.push((m) => {
      if (m.sessionId !== sessionId) return;
      if (m.method === 'Runtime.exceptionThrown') errors.push(m.params.exceptionDetails.exception?.description || m.params.exceptionDetails.text);
      if (m.method === 'Runtime.consoleAPICalled' && m.params.type === 'error') errors.push(m.params.args.map((a) => a.value).join(' '));
      if (m.method === 'Log.entryAdded' && m.params.entry.level === 'error') errors.push(m.params.entry.text + ' ' + (m.params.entry.url || ''));
    });
    await cdp.send('Page.enable', {}, sessionId);
    await cdp.send('Runtime.enable', {}, sessionId);
    await cdp.send('Log.enable', {}, sessionId);
    const size = o.format === 'vertical' ? { w: 1080, h: 1920 } : { w: 1920, h: 1080 };
    await cdp.send('Emulation.setDeviceMetricsOverride', { width: size.w, height: size.h, deviceScaleFactor: 1, mobile: false }, sessionId);
    const url = pathToFileURL(o.page).href + '?format=' + o.format + (o.safe ? '&safe=1' : '');
    const loaded = cdp.once('Page.loadEventFired', sessionId);
    await cdp.send('Page.navigate', { url }, sessionId);
    await loaded;
    const ready = await cdp.send('Runtime.evaluate', { expression: 'document.fonts.ready.then(() => !!(window.__ft && window.__ft.ready))',
      awaitPromise: true, returnByValue: true }, sessionId);
    if (!ready.result.value || errors.length) throw new Error('Scene failed to load: ' + (errors.join('; ') || 'no window.__ft'));
    const info = (await cdp.send('Runtime.evaluate', { expression: 'JSON.stringify({d: __ft.duration, w: __ft.width, h: __ft.height})',
      returnByValue: true }, sessionId)).result.value;
    const scene = JSON.parse(info);
    const shot = async (t) => {
      const r = await cdp.send('Runtime.evaluate', { expression: '__ft.seek(' + t + ')', returnByValue: true }, sessionId);
      if (r.exceptionDetails || errors.length) throw new Error('Render failed at t=' + t + ': ' + (errors.join('; ') || r.exceptionDetails.text));
      const img = await cdp.send('Page.captureScreenshot', { format: 'png', clip: { x: 0, y: 0, width: scene.w, height: scene.h, scale: 1 } }, sessionId);
      return Buffer.from(img.data, 'base64');
    };
    const manifest = { page: o.page, page_sha256: sha256(o.page), format: o.format, width: scene.w, height: scene.h,
      chromium: chromePath(), rendered_at: new Date().toISOString() };
    const data = join(dirname(o.page), 'data.js');
    if (existsSync(data)) manifest.data_sha256 = sha256(data);
    if (o.video) {
      const from = o.from ?? 0, to = o.to ?? scene.d, frames = Math.round((to - from) * o.fps);
      ffmpeg = spawn('ffmpeg', ['-y', '-loglevel', 'error', '-f', 'image2pipe', '-framerate', String(o.fps), '-i', '-',
        '-c:v', 'libx264', '-pix_fmt', 'yuv420p', '-crf', '16', '-preset', 'medium', '-movflags', '+faststart', o.out],
        { stdio: ['pipe', 'inherit', 'inherit'] });
      const done = new Promise((ok, fail) => ffmpeg.on('exit', (c) => (c === 0 ? ok() : fail(new Error('ffmpeg exited ' + c)))));
      for (let i = 0; i < frames; i++) {
        const png = await shot(from + i / o.fps);
        if (!ffmpeg.stdin.write(png)) await new Promise((ok) => ffmpeg.stdin.once('drain', ok));
      }
      ffmpeg.stdin.end();
      await done;
      Object.assign(manifest, { kind: 'video', fps: o.fps, from, to, frames,
        ffmpeg: execFileSync('ffmpeg', ['-version']).toString().split('\n')[0] });
    } else {
      writeFileSync(o.out, await shot(o.still));
      Object.assign(manifest, { kind: 'still', t: o.still });
    }
    manifest.output_sha256 = sha256(o.out);
    writeFileSync(o.out + '.json', JSON.stringify(manifest, null, 2) + '\n');
    console.log('Wrote ' + o.out);
  } finally {
    if (ffmpeg && ffmpeg.exitCode === null) ffmpeg.kill('SIGKILL');
    try { cdp.ws.close(); } catch (e) { /* already closed */ }
    chrome.kill('SIGKILL');
    rmSync(profile, { recursive: true, force: true });
  }
}

main().catch((e) => { console.error('render: ' + e.message); process.exit(1); });
