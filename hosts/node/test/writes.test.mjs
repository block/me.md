import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import { tmpCtx, PROP, ID1, ID2 } from './helpers.mjs';
import { checkJournal, applyAppend } from '../lib/index.mjs';

const accept = (h, id = ID1) => h.decide({ proposal: id, decision: 'accept' });

test('accept: appends, sets status, journals two entries in order (S8.6, H3.5)', () => {
  const c = tmpCtx({ 'topics/travel.md': 'Likes trains.\n', [`proposals/${ID1}.md`]: PROP() });
  const r = accept(c.host(), ID1);
  assert.equal(r.status, 'accepted');
  assert.equal(r.applied, 'added');
  assert.equal(c.text('topics/travel.md'), 'Likes trains.\nPrefer aisle seats.\n');
  const p = c.text(`proposals/${ID1}.md`);
  assert.match(p, /^---\nstatus: accepted\ndecided-at: \d{4}-\d\d-\d\dT\d\d:\d\d:\d\dZ\ndecided-via: nodehost 0\.1\.0\ntarget: /);
  assert.equal(r.journal.length, 2);
  assert.match(r.journal[0], new RegExp(`\\| proposals/${ID1}\\.md \\| accepted \\| host: nodehost 0\\.1\\.0 \\| authority: person direct$`));
  assert.match(r.journal[1], new RegExp(`\\| topics/travel\\.md \\| .* \\| host: nodehost 0\\.1\\.0 \\| authority: accepted proposal ${ID1}$`));
  assert.equal(c.text('journal.md'), r.journal.join('\n') + '\n');
  const j = checkJournal(c.text('journal.md'));
  assert.equal(j.malformed.length, 0);
  assert.equal(j.entries.length, 2);
  assert.ok(!c.exists('.me.lock'));
  assert.deepEqual(fs.readdirSync(c.p('topics')), ['travel.md']);
  assert.ok(!JSON.stringify(r.journal).includes('aisle'), 'the journal never copies content');
  c.cleanup();
});

test('accept creates a missing target with the text and one LF, and a missing directory', () => {
  const c = tmpCtx({ [`proposals/${ID1}.md`]: PROP({ body: 'line one\nline two\n\n\n' }) });
  const r = accept(c.host());
  assert.equal(r.applied, 'added');
  assert.equal(c.text('topics/travel.md'), 'line one\nline two\n');
  assert.equal(fs.statSync(c.p('topics')).mode & 0o777, 0o700);
  assert.equal(fs.statSync(c.p('topics/travel.md')).mode & 0o777, 0o600);
  c.cleanup();
});

test('append into a CRLF target with no final line break (T16, S6.8)', () => {
  const orig = 'one\r\ntwo';
  const c = tmpCtx({ 'topics/travel.md': orig, [`proposals/${ID1}.md`]: PROP({ body: 'new a\nnew b' }) });
  accept(c.host());
  assert.equal(c.text('topics/travel.md'), 'one\r\ntwo\r\nnew a\r\nnew b\r\n');
  assert.ok(c.read('topics/travel.md').subarray(0, orig.length).equals(Buffer.from(orig)));
  c.cleanup();
});

test('append into an LF target with no final line break', () => {
  const c = tmpCtx({ 'topics/travel.md': 'one\ntwo', [`proposals/${ID1}.md`]: PROP({ body: 'x\r\ny\r\n' }) });
  accept(c.host());
  assert.equal(c.text('topics/travel.md'), 'one\ntwo\nx\ny\n');
  c.cleanup();
});

test('append into an empty target and into a CRLF target with a final break', () => {
  const c = tmpCtx({ 'topics/a.md': '', 'topics/b.md': 'x\r\n', [`proposals/${ID1}.md`]: PROP({ target: 'topics/a.md' }), [`proposals/${ID2}.md`]: PROP({ target: 'topics/b.md', body: 'y' }) });
  const h = c.host();
  accept(h, ID1);
  accept(h, ID2);
  assert.equal(c.text('topics/a.md'), 'Prefer aisle seats.\n');
  assert.equal(c.text('topics/b.md'), 'x\r\ny\r\n');
  c.cleanup();
});

test('append bytes: a target that is not UTF-8 keeps every byte', () => {
  const orig = Buffer.from([0x66, 0xff, 0xfe, 0x0a, 0x67]);
  const c = tmpCtx({ [`proposals/${ID1}.md`]: PROP() });
  c.write('topics/travel.md', orig);
  accept(c.host());
  assert.ok(c.read('topics/travel.md').subarray(0, 5).equals(orig));
  assert.equal(c.read('topics/travel.md').subarray(5).toString(), '\nPrefer aisle seats.\n');
  c.cleanup();
});

test('accept is idempotent: a body already at the end is not added twice (S8.6)', () => {
  for (const existing of ['Prefer aisle seats.\n', 'x\nPrefer aisle seats.\n', 'x\r\nPrefer aisle seats.\r\n']) {
    const c = tmpCtx({ 'topics/travel.md': existing, [`proposals/${ID1}.md`]: PROP() });
    const r = accept(c.host());
    assert.equal(r.applied, 'already');
    assert.equal(c.text('topics/travel.md'), existing);
    assert.equal(r.journal.length, 2, 'both entries are still appended');
    assert.match(c.text(`proposals/${ID1}.md`), /status: accepted/);
    c.cleanup();
  }
});

test('idempotence needs the whole last lines to match, not a suffix of a line', () => {
  const c = tmpCtx({ 'topics/travel.md': 'I said: Prefer aisle seats.\n', [`proposals/${ID1}.md`]: PROP() });
  assert.equal(accept(c.host()).applied, 'added');
  assert.equal(c.text('topics/travel.md'), 'I said: Prefer aisle seats.\nPrefer aisle seats.\n');
  c.cleanup();
});

test('a multi-line body is idempotent too', () => {
  const c = tmpCtx({ 'topics/travel.md': 'a\r\nb\r\nc\r\n', [`proposals/${ID1}.md`]: PROP({ body: 'b\nc' }) });
  assert.equal(accept(c.host()).applied, 'already');
  c.cleanup();
});

test('applyAppend: the S6.8 steps on bytes', () => {
  const t = (target, body, o) => {
    const r = applyAppend(target === null ? null : Buffer.from(target), body, o);
    return [r.result, r.content && r.content.toString()];
  };
  assert.deepEqual(t(null, 'a\nb\n'), ['created', 'a\nb\n']);
  assert.deepEqual(t('x', 'a'), ['added', 'x\na\n']);
  assert.deepEqual(t('x\r\ny', 'a\nb'), ['added', 'x\r\ny\r\na\r\nb\r\n']);
  assert.deepEqual(t('x\n', 'x'), ['already', null]);
  assert.deepEqual(t('x\n', 'x', { idempotent: false }), ['added', 'x\nx\n']);
  assert.deepEqual(t('', 'x'), ['added', 'x\n']);
});

test('refuse: sets status and decided-at, writes no content, journals one entry', () => {
  const c = tmpCtx({ [`proposals/${ID1}.md`]: PROP({ extra: ['x-unknown: keep'] }) });
  const r = c.host().decide({ proposal: ID1, decision: 'refuse', agent: 'me' });
  assert.equal(r.status, 'refused');
  assert.equal(r.applied, null);
  assert.equal(r.journal.length, 1);
  assert.match(r.journal[0], /\| refused \| host: nodehost 0\.1\.0 \(me\) \| authority: person direct$/);
  assert.ok(!c.exists('topics/travel.md'));
  assert.match(c.text(`proposals/${ID1}.md`), /status: refused\ndecided-at: /);
  assert.ok(c.text(`proposals/${ID1}.md`).includes('x-unknown: keep\n'));
  // The refusal now holds.
  assert.throws(() => c.host().propose({ target: 'me.md', body: 'Prefer aisle seats.', basis: 'b' }), { code: 'refused' });
  c.cleanup();
});

test('round-trip: unknown key and CRLF proposal survive accept byte for byte (T16)', () => {
  const orig = PROP({ extra: ['x-unknown: keep   me'], eol: '\r\n' });
  const c = tmpCtx({ [`proposals/${ID1}.md`]: orig, 'topics/travel.md': 'one\r\ntwo' });
  accept(c.host());
  const p = c.text(`proposals/${ID1}.md`);
  assert.ok(p.includes('x-unknown: keep   me\r\n'));
  // Remove the lines the host added and the status change: the rest is identical.
  const restored = p
    .replace('status: accepted\r\ndecided-at: ', 'status: pending\r\nDROP')
    .split('\r\n')
    .filter((l) => !l.startsWith('DROP') && !l.startsWith('decided-via:'))
    .join('\r\n');
  assert.equal(restored, orig);
  assert.ok(!p.replace(/\r\n/g, '').includes('\n'), 'no bare LF was added');
  c.cleanup();
});

test('round-trip: an edit leaves the rest of a CRLF me.md with an unparseable line byte for byte (T16)', () => {
  const orig = 'Aims: travel\r\n\u0001\u0002 weird line \xff ~~~\r\n```\r\nunclosed\r\nEnd';
  const c = tmpCtx({});
  c.write('me.md', Buffer.from(orig, 'latin1'));
  const r = c.host().edit({ path: 'me.md', action: 'replace', old: 'Aims: travel', new: 'Aims: travel and tea' });
  assert.equal(c.read('me.md').toString('latin1'), orig.replace('Aims: travel', 'Aims: travel and tea'));
  assert.equal(r.journal.length, 1);
  c.cleanup();
});

test('edit replace: line breaks follow the file, ambiguity and no match', () => {
  const c = tmpCtx({ 'me.md': 'a\r\nb\r\nc\r\nb\r\n' });
  const h = c.host();
  assert.throws(() => h.edit({ path: 'me.md', action: 'replace', old: 'b', new: 'x' }), { code: 'ambiguous' });
  assert.throws(() => h.edit({ path: 'me.md', action: 'replace', old: 'zzz', new: 'x' }), { code: 'no_match' });
  h.edit({ path: 'me.md', action: 'replace', old: 'a\nb', new: 'A\nB\nB2' });
  assert.equal(c.text('me.md'), 'A\r\nB\r\nB2\r\nc\r\nb\r\n');
  assert.throws(() => h.edit({ path: 'topics/none.md', action: 'replace', old: 'a', new: 'b' }), { code: 'not_found' });
  assert.throws(() => h.edit({ path: 'journal.md', action: 'append', text: 'x' }), { code: 'bad_path' });
  assert.throws(() => h.edit({ path: 'policy.json', action: 'append', text: 'x' }), { code: 'bad_path' });
  assert.throws(() => h.edit({ path: '../x.md', action: 'append', text: 'x' }), { code: 'bad_path' });
  assert.throws(() => h.edit({ path: 'proposals/x.md', action: 'append', text: 'x' }), { code: 'bad_path' });
  c.cleanup();
});

test('edit append (T12): applies at once, journals person direct, creates new files but not me.md', () => {
  const c = tmpCtx({ 'me.md': 'x' });
  const h = c.host();
  const r = h.edit({ path: 'me.md', action: 'append', text: 'I prefer aisle seats.' });
  assert.equal(c.text('me.md'), 'x\nI prefer aisle seats.\n');
  assert.match(r.journal[0], /\| me\.md \| .* \| host: nodehost 0\.1\.0 \| authority: person direct$/);
  assert.ok(!r.journal[0].includes('aisle'));
  h.edit({ path: 'watches.md', action: 'append', text: '- the migration' });
  h.edit({ path: 'projects/garden-plan.md', action: 'append', text: 'Plant peas.' });
  assert.equal(c.text('watches.md'), '- the migration\n');
  assert.equal(c.text('projects/garden-plan.md'), 'Plant peas.\n');
  c.cleanup();
});

test('forget: whole lines, with their line breaks; file; notice (H5.3)', () => {
  const c = tmpCtx({ 'me.md': 'keep\r\nsecret\r\nmid\r\nsecret\r\nlast' });
  const h = c.host();
  assert.throws(() => h.forget({ path: 'me.md', text: 'ecre' }), { code: 'no_match' });
  const r = h.forget({ path: 'me.md', text: 'secret' });
  assert.equal(r.removed, 2);
  assert.equal(c.text('me.md'), 'keep\r\nmid\r\nlast');
  assert.ok(r.notices.join(' ').includes('model provider'));
  assert.equal(r.journal.length, 1);
  assert.ok(!r.journal[0].includes('secret'));
  c.write('topics/a.md', 'one\ntwo\nthree\n');
  assert.equal(h.forget({ path: 'topics/a.md', text: 'one\ntwo' }).removed, 1);
  assert.equal(c.text('topics/a.md'), 'three\n');
  const f = h.forget({ path: 'topics/a.md' });
  assert.equal(f.removed, 1);
  assert.ok(!c.exists('topics/a.md'));
  assert.ok(f.notices.join(' ').includes('model provider'));
  assert.throws(() => h.forget({ path: 'topics/a.md' }), { code: 'not_found' });
  assert.throws(() => h.forget({ path: 'topics/a.md', text: 'x' }), { code: 'not_found' });
  assert.throws(() => h.forget({ path: 'journal.md' }), { code: 'bad_path' });
  assert.equal(checkJournal(c.text('journal.md')).malformed.length, 0);
  c.cleanup();
});

test('forgotten text does not come back in a later session (T14)', () => {
  const c = tmpCtx({ 'topics/travel.md': 'aisle seats\nwindow\n' });
  c.host().forget({ path: 'topics/travel.md', text: 'aisle seats' });
  const h2 = c.host();
  assert.equal(h2.recall({ paths: ['topics/travel.md'] }).files[0].text, 'window\n');
  c.cleanup();
});

test('journal: earlier lines unchanged; missing final LF; CRLF journal gets an LF entry (S8.1, T13)', () => {
  const c = tmpCtx({ [`proposals/${ID1}.md`]: PROP(), [`proposals/${ID2}.md`]: PROP({ body: 'other' }), 'journal.md': '# notes\r\n- 2026-11-12T17:03:01Z | me.md | added an aim | host: x 1 | authority: person direct\r\n- bad line' });
  const before = c.read('journal.md');
  const h = c.host();
  accept(h, ID1);
  const after = c.read('journal.md');
  assert.ok(after.subarray(0, before.length).equals(before));
  assert.equal(after.subarray(before.length, before.length + 1).toString(), '\n', 'starts with LF because the last byte was not LF');
  const added = after.subarray(before.length + 1).toString();
  assert.ok(added.endsWith('\n') && !added.includes('\r'));
  // Now the file ends with LF: no extra LF is added.
  const mid = c.read('journal.md');
  accept(h, ID2);
  const end = c.read('journal.md');
  assert.ok(end.subarray(0, mid.length).equals(mid));
  assert.notEqual(end.subarray(mid.length, mid.length + 1).toString(), '\n');
  const j = checkJournal(c.text('journal.md'));
  assert.deepEqual(j.malformed.map((m) => m.line), [3]);
  assert.equal(j.entries.length, 5);
  c.cleanup();
});

test('journal.md as a symbolic link: not appended to, change reported without a receipt (S2.4, S8.7)', () => {
  const c = tmpCtx({ [`proposals/${ID1}.md`]: PROP() });
  fs.writeFileSync(c.p('..', 'outside-journal.md'), 'OUT\n');
  fs.symlinkSync(c.p('..', 'outside-journal.md'), c.p('journal.md'));
  const r = accept(c.host());
  assert.equal(r.applied, 'added');
  assert.deepEqual(r.journal, []);
  assert.ok(r.notices.join(' ').includes('no receipt'));
  assert.equal(fs.readFileSync(c.p('..', 'outside-journal.md'), 'utf8'), 'OUT\n');
  assert.equal(c.text('topics/travel.md'), 'Prefer aisle seats.\n');
  c.cleanup();
});

test('temp files and locks are never left behind', () => {
  const c = tmpCtx({ [`proposals/${ID1}.md`]: PROP(), 'topics/travel.md': 'x\n' });
  const h = c.host();
  accept(h);
  h.edit({ path: 'topics/travel.md', action: 'append', text: 'y' });
  h.policy({ state: 'on' });
  const names = [];
  const walk = (d) => fs.readdirSync(d, { withFileTypes: true }).forEach((e) => (e.isDirectory() ? walk(`${d}/${e.name}`) : names.push(e.name)));
  walk(c.me);
  assert.deepEqual(names.filter((n) => n.startsWith('.')), []);
  c.cleanup();
});

test('S8.4: a file changed by an outside program during the write is not lost', () => {
  // Simulate the editor race: change the target after the host's first read.
  const c = tmpCtx({ 'topics/travel.md': 'before\n', [`proposals/${ID1}.md`]: PROP() });
  const real = fs.readFileSync;
  let n = 0;
  fs.readFileSync = function (...a) {
    const out = real.apply(this, a);
    // The fd-based reads are the host's snapshots of the target.
    if (typeof a[0] === 'number' && out.toString() === 'before\n' && n++ === 0) fs.writeFileSync(c.p('topics/travel.md'), 'before\nedited by hand\n');
    return out;
  };
  try {
    accept(c.host());
  } finally {
    fs.readFileSync = real;
  }
  assert.equal(c.text('topics/travel.md'), 'before\nedited by hand\nPrefer aisle seats.\n');
  c.cleanup();
});
