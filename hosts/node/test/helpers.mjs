// Test helpers. Every store lives in a temp dir. HOME is a temp dir too.
import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import { spawn, spawnSync } from 'node:child_process';
import { fileURLToPath } from 'node:url';
import { Thou } from '../lib/index.mjs';

export const DRIVER = fileURLToPath(new URL('../thou-driver.mjs', import.meta.url));

export function tmpCtx(files = { 'me.md': 'canary-me\n' }) {
  const dir = fs.realpathSync(fs.mkdtempSync(path.join(os.tmpdir(), 'thou-node-')));
  const home = path.join(dir, 'home');
  const me = path.join(dir, 'store');
  fs.mkdirSync(home);
  fs.mkdirSync(me);
  const ctx = {
    dir,
    home,
    me,
    env: { HOME: home, ME_HOME: me, TMPDIR: dir, PATH: process.env.PATH },
    p: (...a) => path.join(me, ...a),
    write(rel, data) {
      fs.mkdirSync(path.dirname(ctx.p(rel)), { recursive: true });
      fs.writeFileSync(ctx.p(rel), data);
    },
    read: (rel) => fs.readFileSync(ctx.p(rel)),
    text: (rel) => fs.readFileSync(ctx.p(rel), 'utf8'),
    exists: (rel) => fs.existsSync(ctx.p(rel)),
    host: (opts = {}) => new Thou({ env: ctx.env, lockWaitMs: 150, ...opts }),
    // The names of everything in the store, for "nothing was written" checks.
    tree() {
      const out = [];
      const walk = (d, pre) => {
        for (const n of fs.readdirSync(d).sort()) {
          const p = path.join(d, n);
          const rel = pre + n;
          const st = fs.lstatSync(p);
          if (st.isDirectory()) walk(p, rel + '/');
          else out.push(`${rel}:${st.isSymbolicLink() ? 'link' : fs.readFileSync(p).toString('base64')}`);
        }
      };
      walk(me, '');
      return out;
    },
    cleanup: () => fs.rmSync(dir, { recursive: true, force: true }),
  };
  // An empty object is an empty store. Otherwise me.md is there unless given (null skips it).
  const all = Object.keys(files).length && !('me.md' in files) ? { 'me.md': 'canary-me\n', ...files } : files;
  for (const [k, v] of Object.entries(all)) if (v !== null) ctx.write(k, v);
  return ctx;
}

const PROP = (o = {}) =>
  [
    '---',
    `status: ${o.status ?? 'pending'}`,
    `target: ${o.target ?? 'topics/travel.md'}`,
    'proposed-by: testhost 1.0',
    'proposed-at: 2026-11-12T17:03:01Z',
    'basis: because',
    ...(o.extra ?? []),
    '---',
    '',
    o.body ?? 'Prefer aisle seats.',
    '',
  ].join(o.eol ?? '\n');
export { PROP };

export const ID1 = '20261112T170301Z-aaaa';
export const ID2 = '20261112T170302Z-bbbb';

export function driverEnv(ctx, extra = {}) {
  return { ...ctx.env, THOU_LOCK_WAIT_MS: '200', ...extra };
}

// Run one driver session synchronously. Returns the responses.
export function runDriver(ctx, requests, extra = {}) {
  const input = requests.map((r) => (typeof r === 'string' ? r : JSON.stringify(r))).join('\n') + '\n';
  const r = spawnSync(process.execPath, [DRIVER], { input, env: driverEnv(ctx, extra), encoding: 'utf8', cwd: ctx.dir, timeout: 60000 });
  if (r.status !== 0) throw new Error(`driver exited ${r.status}: ${r.stderr}`);
  return r.stdout.split('\n').filter(Boolean).map((l) => JSON.parse(l));
}

// A driver session you can feed one line at a time.
export function startDriver(ctx, extra = {}) {
  const child = spawn(process.execPath, [DRIVER], { env: driverEnv(ctx, extra), cwd: ctx.dir, stdio: ['pipe', 'pipe', 'pipe'] });
  let buf = '';
  const waiting = [];
  // A dead or stuck driver fails the test instead of hanging it.
  const limit = (p) => Promise.race([p, new Promise((_, rej) => setTimeout(() => rej(new Error('driver did not answer in 30 s')), 30000).unref())]);
  child.stdout.on('data', (d) => {
    buf += d;
    let i;
    while ((i = buf.indexOf('\n')) >= 0) {
      const line = buf.slice(0, i);
      buf = buf.slice(i + 1);
      waiting.shift()?.(JSON.parse(line));
    }
  });
  const exited = new Promise((res) => child.on('close', res));
  return {
    send(req) {
      return limit(
        new Promise((res) => {
          waiting.push(res);
          child.stdin.write(JSON.stringify(req) + '\n');
        }),
      );
    },
    // Write a request now, and read the answer later.
    fire(req) {
      const p = new Promise((res) => waiting.push(res));
      child.stdin.write(JSON.stringify(req) + '\n');
      return limit(p);
    },
    async end() {
      child.stdin.end();
      return exited;
    },
  };
}
