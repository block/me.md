import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import { tmpCtx, PROP, ID1, ID2, startDriver } from './helpers.mjs';
import { checkJournal } from '../lib/index.mjs';

const FOREIGN = 'deadbeefdeadbeefdeadbeefdeadbeef otherhost 2026-11-17T00:00:00Z\n';

test('a foreign lock is never removed; the host reports locked and changes nothing (S8.3)', () => {
  const c = tmpCtx({ 'topics/travel.md': 'x\n', [`proposals/${ID1}.md`]: PROP() });
  fs.writeFileSync(c.p('.me.lock'), FOREIGN);
  const h = c.host({ lockWaitMs: 100 });
  const before = c.tree();
  const checks = [
    () => h.decide({ proposal: ID1, decision: 'accept' }),
    () => h.decide({ proposal: ID1, decision: 'refuse' }),
    () => h.revise({ proposal: ID1, body: 'new' }),
    () => h.edit({ path: 'me.md', action: 'append', text: 'x' }),
    () => h.forget({ path: 'topics/travel.md' }),
    () => h.policy({ state: 'off' }),
  ];
  for (const f of checks) {
    const t0 = Date.now();
    assert.throws(f, (e) => {
      assert.equal(e.code, 'locked');
      assert.ok(e.notices.join(' ').includes('.me.lock'));
      return true;
    });
    assert.ok(Date.now() - t0 >= 90, 'it waits before giving up');
  }
  assert.equal(c.text('.me.lock'), FOREIGN);
  assert.deepEqual(c.tree(), before);
  c.cleanup();
});

test('propose needs no lock (S8.5)', () => {
  const c = tmpCtx();
  fs.writeFileSync(c.p('.me.lock'), FOREIGN);
  assert.ok(c.host().propose({ target: 'me.md', body: 'x', basis: 'b' }).proposal);
  assert.equal(c.text('.me.lock'), FOREIGN);
  c.cleanup();
});

test('journal-only appends do not need the lock, and reads never do', () => {
  const c = tmpCtx();
  fs.writeFileSync(c.p('.me.lock'), FOREIGN);
  const h = c.host();
  assert.equal(h.mount().memory, 'on');
  assert.equal(h.pending().memory, 'on');
  c.cleanup();
});

test('a lock created while the host waits is honored; one released in time lets the change through', async () => {
  const c = tmpCtx({ [`proposals/${ID1}.md`]: PROP() });
  fs.writeFileSync(c.p('.me.lock'), FOREIGN);
  const d = startDriver(c, { THOU_LOCK_WAIT_MS: '3000' });
  await d.send({ id: 0, op: 'mount' });
  const p = d.fire({ id: 1, op: 'decide', proposal: ID1, decision: 'accept' });
  await new Promise((r) => setTimeout(r, 300));
  fs.unlinkSync(c.p('.me.lock')); // the other host finishes
  const r = await p;
  assert.equal(r.ok, true, JSON.stringify(r));
  assert.ok(!c.exists('.me.lock'), 'our own lock is released');
  await d.end();
  c.cleanup();
});

test('driver: locked answer carries a notice naming .me.lock, lock stays', async () => {
  const c = tmpCtx({ [`proposals/${ID1}.md`]: PROP() });
  fs.writeFileSync(c.p('.me.lock'), FOREIGN);
  const d = startDriver(c, { THOU_LOCK_WAIT_MS: '100' });
  await d.send({ id: 0, op: 'mount' });
  const r = await d.send({ id: 1, op: 'decide', proposal: ID1, decision: 'accept' });
  assert.equal(r.ok, false);
  assert.equal(r.error, 'locked');
  assert.ok(r.notices.some((n) => n.includes('.me.lock')));
  assert.equal(c.text('.me.lock'), FOREIGN);
  await d.end();
  c.cleanup();
});

// T15: two driver processes accept different proposals with the same target at the same time.
test('two driver processes accepting at the same time: both bodies land once, journal whole (T15)', async () => {
  const ROUNDS = 40;
  for (let round = 0; round < ROUNDS; round++) {
    const c = tmpCtx({ 'topics/shared.md': 'seed\n' });
    c.write(`proposals/${ID1}.md`, PROP({ target: 'topics/shared.md', body: `First body ${round}` }));
    c.write(`proposals/${ID2}.md`, PROP({ target: 'topics/shared.md', body: `Second body ${round}` }));
    const a = startDriver(c);
    const b = startDriver(c);
    await Promise.all([a.send({ id: 0, op: 'mount' }), b.send({ id: 0, op: 'mount' })]);
    const [ra, rb] = await Promise.all([
      a.fire({ id: 1, op: 'decide', proposal: ID1, decision: 'accept', agent: 'A' }),
      b.fire({ id: 1, op: 'decide', proposal: ID2, decision: 'accept', agent: 'B' }),
    ]);
    await Promise.all([a.end(), b.end()]);
    assert.equal(ra.ok, true, JSON.stringify(ra));
    assert.equal(rb.ok, true, JSON.stringify(rb));
    const text = c.text('topics/shared.md');
    assert.equal(text.split(`First body ${round}\n`).length - 1, 1, text);
    assert.equal(text.split(`Second body ${round}\n`).length - 1, 1, text);
    assert.ok(text.startsWith('seed\n'));
    const j = checkJournal(c.text('journal.md'));
    assert.equal(j.malformed.length, 0, c.text('journal.md'));
    assert.equal(j.entries.length, 4);
    assert.equal(c.text('journal.md').split('\n').filter(Boolean).length, 4);
    assert.match(c.text(`proposals/${ID1}.md`), /status: accepted/);
    assert.match(c.text(`proposals/${ID2}.md`), /status: accepted/);
    assert.ok(!c.exists('.me.lock'));
    c.cleanup();
  }
});

test('two drivers: many appends to one journal never tear an entry', async () => {
  const c = tmpCtx();
  const a = startDriver(c);
  const b = startDriver(c);
  await Promise.all([a.send({ id: 0, op: 'mount' }), b.send({ id: 0, op: 'mount' })]);
  const reqs = (d, tag) => Promise.all(Array.from({ length: 25 }, (_, i) => d.fire({ id: i, op: 'edit', path: 'topics/t.md', action: 'append', text: `${tag} ${i}`, agent: tag })));
  const [ra, rb] = await Promise.all([reqs(a, 'A'), reqs(b, 'B')]);
  await Promise.all([a.end(), b.end()]);
  assert.ok([...ra, ...rb].every((r) => r.ok), JSON.stringify([...ra, ...rb].filter((r) => !r.ok)));
  const j = checkJournal(c.text('journal.md'));
  assert.equal(j.malformed.length, 0);
  assert.equal(j.entries.length, 50);
  assert.equal(c.text('topics/t.md').split('\n').filter(Boolean).length, 50);
  c.cleanup();
});
