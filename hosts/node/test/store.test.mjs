import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import path from 'node:path';
import { tmpCtx } from './helpers.mjs';
import { storeRoot } from '../lib/index.mjs';

test('location: ME_HOME wins, else HOME/.me, empty ME_HOME counts as unset', () => {
  assert.equal(storeRoot({ ME_HOME: '/tmp/x', HOME: '/tmp/h' }), '/tmp/x');
  assert.equal(storeRoot({ HOME: '/tmp/h' }), path.join('/tmp/h', '.me'));
  assert.equal(storeRoot({ ME_HOME: '', HOME: '/tmp/h' }), path.join('/tmp/h', '.me'));
});

test('location: ME_HOME unset uses HOME/.me', () => {
  const c = tmpCtx({});
  fs.mkdirSync(path.join(c.home, '.me'));
  fs.writeFileSync(path.join(c.home, '.me', 'me.md'), 'HOME-CANARY\n');
  const env = { HOME: c.home, PATH: process.env.PATH };
  const h = new (c.host().constructor)({ env });
  assert.equal(h.mount().files[0].text, 'HOME-CANARY\n');
  c.cleanup();
});

test('absence: no store directory, empty directory, missing me.md: nothing is written (T1)', () => {
  const c = tmpCtx({});
  const h = c.host();
  assert.equal(h.mount().memory, 'absent');
  assert.deepEqual(h.mount().files, []);
  assert.equal(h.list().memory, 'absent');
  assert.equal(h.pending().memory, 'absent');
  assert.throws(() => h.propose({ target: 'me.md', body: 'x', basis: 'y' }), { code: 'absent' });
  assert.throws(() => h.edit({ path: 'topics/a.md', action: 'append', text: 'x' }), { code: 'absent' });
  assert.deepEqual(c.tree(), []);
  fs.rmSync(c.me, { recursive: true });
  assert.equal(h.mount().memory, 'absent');
  assert.throws(() => h.propose({ target: 'me.md', body: 'x', basis: 'y' }), { code: 'absent' });
  assert.ok(!fs.existsSync(c.me));
  c.cleanup();
});

test('document mode: only me.md is valid', () => {
  const c = tmpCtx();
  const h = c.host();
  assert.equal(h.mount().memory, 'on');
  assert.deepEqual(h.list(), { memory: 'on', topics: [], projects: [], watches: false });
  assert.deepEqual(h.pending().proposals, []);
  c.cleanup();
});

test('me.md as a symbolic link: the store is absent, the canary never appears (T6)', () => {
  const c = tmpCtx({});
  fs.writeFileSync(path.join(c.dir, 'outside.md'), 'OUTSIDE-CANARY\n');
  fs.symlinkSync(path.join(c.dir, 'outside.md'), c.p('me.md'));
  const h = c.host();
  const m = h.mount();
  assert.equal(m.memory, 'absent');
  assert.deepEqual(m.files, []);
  assert.ok(m.notices.join(' ').includes('symbolic link'));
  assert.equal(JSON.stringify(h.recall({ paths: ['me.md'] })).includes('OUTSIDE'), false);
  assert.throws(() => h.policy({ state: 'off' }), { code: 'absent' });
  c.cleanup();
});

test('the store root may be a symbolic link', () => {
  const c = tmpCtx();
  const link = path.join(c.dir, 'link-to-store');
  fs.symlinkSync(c.me, link);
  const h = new (c.host().constructor)({ env: { ...c.env, ME_HOME: link } });
  assert.equal(h.mount().files[0].text, 'canary-me\n');
  c.cleanup();
});

test('traversal, absolute and hidden paths are skipped (S2.2, S2.7)', () => {
  const c = tmpCtx({ 'me.md': 'x\n', 'topics/.hidden.md': 'HIDDEN\n', 'topics/travel.md': 'ok\n', '.git/config': 'GIT\n' });
  fs.writeFileSync(path.join(c.dir, 'outside.md'), 'OUTSIDE-CANARY\n');
  const paths = [
    '../outside.md', 'topics/../../outside.md', '/etc/hosts', path.join(c.dir, 'outside.md'), 'topics/.hidden.md',
    '.git/config', 'topics//travel.md', './me.md', 'topics/travel.md/', 'policy.json', 'journal.md', 'topics\\travel.md',
    'proposals/x.md', 'ME.md', 'topics/Travel.md', '', 'topics', 'watches.md',
  ];
  const r = c.host().recall({ paths });
  assert.deepEqual(r.files, []);
  assert.equal(r.skipped.length, paths.length);
  assert.deepEqual(r.skipped.map((s) => s.path), paths);
  c.cleanup();
});

test('every requested path lands in exactly one list', () => {
  const c = tmpCtx({ 'me.md': 'x\n', 'topics/travel.md': 'ok\n' });
  const r = c.host().recall({ paths: ['me.md', 'topics/travel.md', 'topics/none.md'] });
  assert.equal(r.files.length + r.skipped.length, 3);
  assert.deepEqual(r.skipped, [{ path: 'topics/none.md', reason: 'missing' }]);
  c.cleanup();
});

test('symbolic links inside the store are never followed (T6)', () => {
  const c = tmpCtx({ 'me.md': 'x\n' });
  const out = path.join(c.dir, 'outside');
  fs.mkdirSync(out);
  fs.writeFileSync(path.join(out, 'secret.md'), 'OUTSIDE-CANARY\n');
  fs.mkdirSync(c.p('topics'));
  fs.symlinkSync(path.join(out, 'secret.md'), c.p('topics', 'link.md'));
  fs.symlinkSync(out, c.p('projects'));
  fs.symlinkSync(path.join(out, 'secret.md'), c.p('watches.md'));
  const h = c.host();
  const l = h.list();
  assert.deepEqual(l.topics, []);
  assert.deepEqual(l.projects, []);
  assert.equal(l.watches, false);
  const r = h.recall({ paths: ['topics/link.md', 'projects/secret.md', 'watches.md'], purpose: 'watches' });
  assert.deepEqual(r.files, []);
  assert.equal(JSON.stringify([l, r]).includes('OUTSIDE'), false);
  // Writes refuse too, and the outside file is unchanged.
  assert.throws(() => h.edit({ path: 'topics/link.md', action: 'append', text: 'x' }), { code: 'bad_path' });
  assert.throws(() => h.edit({ path: 'projects/new.md', action: 'append', text: 'x' }), { code: 'bad_path' });
  assert.throws(() => h.forget({ path: 'topics/link.md' }), { code: 'bad_path' });
  assert.equal(fs.readFileSync(path.join(out, 'secret.md'), 'utf8'), 'OUTSIDE-CANARY\n');
  assert.deepEqual(fs.readdirSync(out), ['secret.md']);
  c.cleanup();
});

test('accepting into a symbolic-link target: bad_target, outside file unchanged', () => {
  const c = tmpCtx({ 'me.md': 'x\n' });
  fs.writeFileSync(path.join(c.dir, 'outside.md'), 'OUTSIDE-CANARY\n');
  fs.mkdirSync(c.p('topics'));
  fs.symlinkSync(path.join(c.dir, 'outside.md'), c.p('topics', 'travel.md'));
  const h = c.host();
  const { proposal } = h.propose({ target: 'topics/travel.md', body: 'Prefer aisle seats.', basis: 'b' });
  assert.throws(() => h.decide({ proposal, decision: 'accept' }), { code: 'bad_target' });
  assert.equal(fs.readFileSync(path.join(c.dir, 'outside.md'), 'utf8'), 'OUTSIDE-CANARY\n');
  assert.equal(h.pending().proposals.length, 1);
  assert.ok(!c.exists('journal.md'));
  c.cleanup();
});

test('hidden files, bad names, directories and links are ignored, with a notice (S2.1)', () => {
  const c = tmpCtx({
    'me.md': 'x\n', 'topics/travel.md': 'a\n', 'topics/My Topic.md': 'b\n', 'topics/.draft.md.tmp': 'c\n',
    'topics/.dot.md': 'd\n', 'topics/notes.txt': 'e\n', 'topics/b.md': 'f\n', 'projects/garden-plan.md': 'g\n',
    [`topics/${'a'.repeat(64)}.md`]: 'h\n', [`topics/${'a'.repeat(65)}.md`]: 'i\n', 'topics/-x.md': 'j\n', 'topics/a_b.md': 'k\n',
    'topics/a.b-c_.md': 'l\n', 'watches.md': '- w\n',
  });
  fs.mkdirSync(c.p('topics', 'dir.md'));
  const l = c.host().list();
  assert.deepEqual(l.topics, ['a.b-c_.md', 'a_b.md', `${'a'.repeat(64)}.md`, 'b.md', 'travel.md']);
  assert.deepEqual(l.projects, ['garden-plan.md']);
  assert.equal(l.watches, true);
  const n = l.notices.join('\n');
  assert.ok(n.includes('My Topic.md'));
  assert.ok(n.includes('notes.txt'));
  assert.ok(n.includes('dir.md'));
  assert.ok(!n.includes('.dot.md'));
  c.cleanup();
});

test('watches.md is recalled only for a briefing or a question about watches (S4.3)', () => {
  const c = tmpCtx({ 'me.md': 'x\n', 'watches.md': '- WATCH-CANARY\n' });
  const h = c.host();
  assert.deepEqual(h.recall({ paths: ['watches.md'] }).files, []);
  assert.deepEqual(h.recall({ paths: ['watches.md'], purpose: 'task' }).files, []);
  assert.equal(h.recall({ paths: ['watches.md'], purpose: 'briefing' }).files.length, 1);
  assert.equal(h.recall({ paths: ['watches.md'], purpose: 'watches' }).files.length, 1);
  assert.equal(JSON.stringify([h.mount(), h.list()]).includes('WATCH-CANARY'), false);
  c.cleanup();
});

test('recall keeps CRLF, skips invalid UTF-8', () => {
  const c = tmpCtx({ 'me.md': 'x\n', 'topics/a.md': 'one\r\ntwo\r\n' });
  fs.writeFileSync(c.p('topics', 'bad.md'), Buffer.from([0xff, 0xfe, 0x41]));
  const r = c.host().recall({ paths: ['topics/a.md', 'topics/bad.md'] });
  assert.equal(r.files[0].text, 'one\r\ntwo\r\n');
  assert.equal(r.skipped[0].reason, 'not valid UTF-8');
  c.cleanup();
});

test('unknown top-level entries and .git are ignored', () => {
  const c = tmpCtx({ 'me.md': 'x\n', '.git/HEAD': 'ref\n', 'random.txt': 'r\n', 'unknown/file.md': 'u\n' });
  const h = c.host();
  assert.equal(h.mount().memory, 'on');
  assert.deepEqual(h.recall({ paths: ['unknown/file.md', 'random.txt', '.git/HEAD'] }).files, []);
  c.cleanup();
});

test('bad_request for wrong types', () => {
  const c = tmpCtx();
  const h = c.host();
  assert.throws(() => h.recall({ paths: 'me.md' }), { code: 'bad_request' });
  assert.throws(() => h.recall({ paths: [], purpose: 'x' }), { code: 'bad_request' });
  assert.throws(() => h.propose({ target: 'me.md', body: 5, basis: 'b' }), { code: 'bad_request' });
  assert.throws(() => h.decide({ proposal: 'x', decision: 'maybe' }), { code: 'bad_request' });
  assert.throws(() => h.policy({ state: 'ON' }), { code: 'bad_request' });
  c.cleanup();
});
