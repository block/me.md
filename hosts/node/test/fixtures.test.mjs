// Run the host over the shared example stores (read-only: each is copied first).
import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { tmpCtx } from './helpers.mjs';

const ROOT = fileURLToPath(new URL('../../../conformance/fixtures/', import.meta.url));
const names = fs.existsSync(ROOT) ? fs.readdirSync(ROOT).filter((n) => fs.existsSync(path.join(ROOT, n, 'expect.json'))) : [];

for (const name of names) {
  test(`fixture ${name}`, () => {
    const exp = JSON.parse(fs.readFileSync(path.join(ROOT, name, 'expect.json'), 'utf8'));
    const c = tmpCtx({});
    fs.cpSync(path.join(ROOT, name, 'store'), c.me, { recursive: true });
    const h = c.host();
    const m = h.mount();
    assert.equal(m.memory, exp.policy_state === null ? 'absent' : exp.policy_state, JSON.stringify(m));
    if (m.memory === 'on') {
      const me = fs.readFileSync(c.p('me.md'), 'utf8');
      assert.equal(m.files[0].text, me);
      const p = h.pending();
      const counts = exp.counts || {};
      if ('proposals_pending' in counts) assert.equal(p.proposals.length, counts.proposals_pending);
      if ('proposals_invalid' in counts) assert.equal(p.invalid.length, counts.proposals_invalid);
      const l = h.list();
      if ('topics' in counts) assert.equal(l.topics.length, counts.topics);
      if ('projects' in counts) assert.equal(l.projects.length, counts.projects);
      assert.equal(l.watches, (counts.watches ?? 0) > 0);
      const spec = fs.existsSync(c.p('policy.json')) ? JSON.parse(c.text('policy.json')).spec : undefined;
      assert.equal(m.writable === false, spec !== undefined && spec !== '0.1');
    }
    c.cleanup();
  });
}

test('fixtures: refused-again blocks the refused and the invalid body', () => {
  if (!names.includes('refused-again')) return;
  const c = tmpCtx({});
  fs.cpSync(path.join(ROOT, 'refused-again', 'store'), c.me, { recursive: true });
  const h = c.host();
  assert.throws(() => h.propose({ target: 'topics/x.md', body: 'Prefers aisle seats.', basis: 'b' }), { code: 'refused' });
  assert.throws(() => h.propose({ target: 'topics/x.md', body: 'Never schedule anything before 10am.', basis: 'b' }), { code: 'refused' });
  c.cleanup();
});

test('fixtures: crlf proposal can be accepted, bytes preserved', () => {
  if (!names.includes('crlf')) return;
  const c = tmpCtx({});
  fs.cpSync(path.join(ROOT, 'crlf', 'store'), c.me, { recursive: true });
  const id = '20261112T170301Z-7f3a';
  const before = c.text('journal.md');
  const r = c.host().decide({ proposal: id, decision: 'accept' });
  assert.equal(r.applied, 'added');
  assert.equal(c.text('topics/travel.md'), 'Prefers aisle seats.\n');
  assert.ok(c.text(`proposals/${id}.md`).includes('status: accepted\r\ndecided-at: '));
  assert.ok(c.text('journal.md').startsWith(before));
  c.cleanup();
});
