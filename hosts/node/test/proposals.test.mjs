import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import { tmpCtx, PROP, ID1, ID2 } from './helpers.mjs';
import { parseProposal } from '../lib/index.mjs';

const body = 'Prefer aisle seats.';
const propose = (h, o = {}) => h.propose({ target: 'topics/travel.md', body, basis: 'You asked twice.', ...o });

test('propose writes one valid proposal and changes nothing else (T8)', () => {
  const c = tmpCtx({ 'me.md': 'x\n', 'topics/travel.md': 'old\n' });
  const before = c.tree();
  const r = propose(c.host(), { agent: 'trip-helper' });
  assert.match(r.proposal, /^\d{8}T\d{6}Z-[a-z0-9]{4}$/);
  assert.equal(r.file, `proposals/${r.proposal}.md`);
  const after = c.tree();
  assert.equal(after.length, before.length + 1);
  const p = parseProposal(`${r.proposal}.md`, c.read(r.file));
  assert.equal(p.valid, true);
  assert.equal(p.fm['proposed-by'], 'nodehost 0.1.0 (trip-helper)');
  assert.equal(p.status, 'pending');
  assert.equal(p.body, body);
  assert.ok(!c.exists('journal.md'), 'creating a proposal is not journaled (S6.13)');
  c.cleanup();
});

test('propose: names stay unique and files are never overwritten (S6.2)', () => {
  const c = tmpCtx();
  const h = c.host();
  const ids = new Set();
  for (let i = 0; i < 25; i++) ids.add(propose(h, { body: `body ${i}` }).proposal);
  assert.equal(ids.size, 25);
  assert.equal(h.pending().proposals.length, 25);
  c.cleanup();
});

test('propose: basis and agent with odd characters stay valid', () => {
  const c = tmpCtx();
  const h = c.host();
  const r = h.propose({ target: 'me.md', body: 'x', basis: '"quoted" start\nsecond line', agent: 'a | b\nc' });
  const p = parseProposal(`${r.proposal}.md`, c.read(r.file));
  assert.equal(p.valid, true);
  assert.equal(p.fm.basis, '"quoted" start second line');
  assert.equal(p.fm['proposed-by'], 'nodehost 0.1.0 (a b c)');
  c.cleanup();
});

test('propose errors: bad_target, empty_body (S4.2)', () => {
  const c = tmpCtx();
  const h = c.host();
  for (const target of ['watches.md', '../x.md', 'topics/Bad.md', 'topics/a.txt', 'policy.json', 'proposals/x.md', '/me.md', 'topics/.h.md', 'topics/a/b.md']) {
    assert.throws(() => h.propose({ target, body, basis: 'b' }), { code: 'bad_target' }, target);
  }
  for (const b of ['', '   \n\t ', ' 　']) {
    assert.throws(() => h.propose({ target: 'me.md', body: b, basis: 'b' }), { code: 'empty_body' });
  }
  assert.deepEqual(c.tree().filter((t) => t.startsWith('proposals')), []);
  c.cleanup();
});

test('refusal: a refused body is never proposed again, to any target (S6.11)', () => {
  const c = tmpCtx({ [`proposals/${ID1}.md`]: PROP({ status: 'refused', body }) });
  const h = c.host();
  for (const b of [body, `  ${body}\n\n`, 'Prefer   aisle\tseats.', 'Prefer\naisle seats.', 'Prefer aisle seats.\r\n']) {
    for (const target of ['topics/travel.md', 'me.md', 'projects/x.md']) {
      assert.throws(() => h.propose({ target, body: b, basis: 'b' }), { code: 'refused' });
    }
  }
  // Another body is fine.
  assert.ok(h.propose({ target: 'me.md', body: 'Prefer window seats.', basis: 'b' }).proposal);
  c.cleanup();
});

test('refusal: NFC normalization', () => {
  const c = tmpCtx({ [`proposals/${ID1}.md`]: PROP({ status: 'refused', body: 'Café' }) });
  assert.throws(() => c.host().propose({ target: 'me.md', body: 'Café', basis: 'b' }), { code: 'refused' });
  c.cleanup();
});

test('refusal: a pending or accepted proposal does not block', () => {
  const c = tmpCtx({
    [`proposals/${ID1}.md`]: PROP({ status: 'pending', body }),
    [`proposals/${ID2}.md`]: PROP({ status: 'accepted', body }),
  });
  assert.ok(c.host().propose({ target: 'me.md', body, basis: 'b' }).proposal);
  c.cleanup();
});

test('refusal: a hand-typed "Status: Refused" is invalid and still holds (S6.14, T9)', () => {
  const c = tmpCtx({
    [`proposals/${ID1}.md`]: PROP({ body }).replace('status: pending', 'Status: Refused'),
  });
  const h = c.host();
  const p = h.pending();
  assert.deepEqual(p.proposals, []);
  assert.equal(p.invalid.length, 1);
  assert.equal(p.invalid[0].file, `proposals/${ID1}.md`);
  assert.throws(() => h.propose({ target: 'projects/other.md', body: '  Prefer aisle   seats. ', basis: 'b' }), { code: 'refused' });
  c.cleanup();
});

test('refusal: an invalid file with no front matter at all counts as refused (whole file)', () => {
  const c = tmpCtx({ [`proposals/${ID1}.md`]: 'Never schedule anything before 10am.\n' });
  assert.throws(() => c.host().propose({ target: 'me.md', body: 'Never schedule anything before 10am.', basis: 'b' }), { code: 'refused' });
  c.cleanup();
});

test('refusal: a conflict copy in proposals/ is invalid and counts as refused (S8.8)', () => {
  const c = tmpCtx({ [`proposals/${ID1} (conflict copy).md`]: PROP({ status: 'pending', body }) });
  const h = c.host();
  assert.equal(h.pending().invalid.length, 1);
  assert.throws(() => h.propose({ target: 'me.md', body, basis: 'b' }), { code: 'refused' });
  c.cleanup();
});

test('refusal: invalid-name proposal bodies count; hidden and non-.md files do not', () => {
  const c = tmpCtx({
    'proposals/.hidden.md': PROP({ status: 'refused', body: 'hidden body' }),
    [`proposals/${ID1}.md.bak`]: PROP({ status: 'refused', body: 'bak body' }),
    'proposals/Notes.md': PROP({ status: 'refused', body: 'notes body' }),
  });
  const h = c.host();
  assert.ok(h.propose({ target: 'me.md', body: 'hidden body', basis: 'b' }).proposal);
  assert.ok(h.propose({ target: 'me.md', body: 'bak body', basis: 'b' }).proposal);
  assert.throws(() => h.propose({ target: 'me.md', body: 'notes body', basis: 'b' }), { code: 'refused' });
  c.cleanup();
});

test('deleting a refused proposal ends the refusal (S6.10)', () => {
  const c = tmpCtx({ [`proposals/${ID1}.md`]: PROP({ status: 'refused', body }) });
  const h = c.host();
  assert.throws(() => propose(h), { code: 'refused' });
  fs.unlinkSync(c.p(`proposals/${ID1}.md`));
  assert.ok(propose(h).proposal);
  c.cleanup();
});

test('self-approval: a "status: accepted" line in the body is content (T10, S6.7)', () => {
  const c = tmpCtx({ [`proposals/${ID1}.md`]: PROP({ body: `${body}\n\nstatus: accepted` }) });
  const p = c.host().pending();
  assert.equal(p.proposals.length, 1);
  assert.equal(p.proposals[0].body, `${body}\n\nstatus: accepted`);
  c.cleanup();
});

test('duplicate keys make a proposal invalid; accept says so and changes nothing (T17)', () => {
  const dup = PROP({ extra: ['status: accepted'] });
  const c = tmpCtx({ [`proposals/${ID1}.md`]: dup, 'topics/travel.md': 'old\n' });
  const h = c.host();
  const before = c.tree();
  const p = h.pending();
  assert.equal(p.proposals.length, 0);
  assert.equal(p.invalid.length, 1);
  assert.match(p.invalid[0].reason, /more than once/);
  assert.throws(() => h.decide({ proposal: ID1, decision: 'accept' }), { code: 'invalid_proposal' });
  assert.throws(() => h.decide({ proposal: ID1, decision: 'refuse' }), { code: 'invalid_proposal' });
  assert.throws(() => h.revise({ proposal: ID1, body: 'new' }), { code: 'invalid_proposal' });
  assert.deepEqual(c.tree(), before);
  c.cleanup();
});

const INVALID = {
  'missing basis': PROP().replace('basis: because\n', ''),
  'empty basis': PROP().replace('basis: because', 'basis:'),
  'bad status': PROP({ status: 'Pending' }),
  'target watches.md': PROP({ target: 'watches.md' }),
  'target outside': PROP({ target: '../x.md' }),
  'bad time': PROP().replace('2026-11-12T17:03:01Z', '2026-11-12 17:03:01'),
  'impossible date': PROP().replace('2026-11-12T17:03:01Z', '2026-02-30T17:03:01Z'),
  'fractional seconds': PROP().replace('17:03:01Z', '17:03:01.5Z'),
  'uppercase key': PROP().replace('basis:', 'Basis:'),
  'no space after colon': PROP().replace('basis: because', 'basis:because'),
  'unterminated quote': PROP().replace('basis: because', 'basis: "because'),
  'bad escape': PROP().replace('basis: because', 'basis: "be\\nbecause"'),
  'text after quote': PROP().replace('basis: because', 'basis: "because" and'),
  'not closed': '---\nstatus: pending\n',
  'no opening': 'status: pending\n---\n\nbody\n',
  'leading blank line': '\n' + PROP(),
  'trailing space on fence': PROP().replace('---\nstatus', '--- \nstatus'),
  'empty body': PROP({ body: '  ' }),
  'no body': PROP().split('---\n\n')[0] + '---\n',
  'pipe in proposed-by': PROP().replace('testhost 1.0', 'test|host'),
  'bad decided-at': PROP({ extra: ['decided-at: yesterday'] }),
  'list-like line': PROP({ extra: ['- item'] }),
  'BOM': '﻿' + PROP(),
};
for (const [name, text] of Object.entries(INVALID)) {
  test(`invalid proposal: ${name}`, () => {
    const c = tmpCtx({ [`proposals/${ID1}.md`]: text });
    const p = c.host().pending();
    assert.equal(p.proposals.length, 0, JSON.stringify(p));
    assert.equal(p.invalid.length, 1);
    c.cleanup();
  });
}

const VALID = {
  'quoted values': PROP().replace('basis: because', 'basis: "because \\"x\\" \\\\ y"'),
  'comment and blank lines in front matter': PROP({ extra: ['', '# a comment', 'x-unknown: yes'] }),
  'empty unknown value': PROP({ extra: ['note:'] }),
  'CRLF': PROP({ eol: '\r\n' }),
  'no blank line after the fence': PROP().replace('---\n\nPrefer', '---\nPrefer'),
  'no final newline': PROP().replace(/\n$/, ''),
  'spaces around value': PROP().replace('basis: because', 'basis:    because   '),
  'decided-at on a pending one': PROP({ extra: ['decided-at: 2026-11-12T18:00:00Z'] }),
  'leap second': PROP().replace('17:03:01Z', '23:59:60Z'),
};
for (const [name, text] of Object.entries(VALID)) {
  test(`valid proposal: ${name}`, () => {
    const c = tmpCtx({ [`proposals/${ID1}.md`]: text });
    const p = c.host().pending();
    assert.equal(p.invalid.length, 0, JSON.stringify(p));
    assert.equal(p.proposals.length, 1);
    assert.equal(p.proposals[0].body, 'Prefer aisle seats.');
    c.cleanup();
  });
}

test('quoted values are unquoted in pending', () => {
  const c = tmpCtx({ [`proposals/${ID1}.md`]: PROP().replace('basis: because', 'basis: "because \\"x\\" \\\\ y"') });
  assert.equal(c.host().pending().proposals[0].basis, 'because "x" \\ y');
  c.cleanup();
});

test('revise changes only the body, keeps front matter and unknown keys (S6.15)', () => {
  const orig = PROP({ extra: ['x-unknown: keep me'] });
  const c = tmpCtx({ [`proposals/${ID1}.md`]: orig });
  const h = c.host();
  assert.deepEqual(h.revise({ proposal: ID1, body: 'Prefer window seats.\n' }), { memory: 'on' });
  assert.equal(c.text(`proposals/${ID1}.md`), orig.replace('Prefer aisle seats.', 'Prefer window seats.'));
  assert.equal(h.pending().proposals[0].body, 'Prefer window seats.');
  assert.throws(() => h.revise({ proposal: ID1, body: ' ' }), { code: 'empty_body' });
  assert.throws(() => h.revise({ proposal: 'nope', body: 'x' }), { code: 'not_found' });
  assert.ok(!c.exists('journal.md'));
  // Accepting applies the body as it is at that moment.
  h.decide({ proposal: ID1, decision: 'accept' });
  assert.equal(c.text('topics/travel.md'), 'Prefer window seats.\n');
  assert.throws(() => h.revise({ proposal: ID1, body: 'late' }), { code: 'not_pending' });
  c.cleanup();
});

test('revise keeps CRLF in a CRLF proposal', () => {
  const c = tmpCtx({ [`proposals/${ID1}.md`]: PROP({ eol: '\r\n' }) });
  c.host().revise({ proposal: ID1, body: 'a\nb' });
  assert.ok(c.text(`proposals/${ID1}.md`).endsWith('---\r\n\r\na\r\nb\r\n'));
  c.cleanup();
});

test('decide errors', () => {
  const c = tmpCtx({ [`proposals/${ID1}.md`]: PROP({ status: 'refused' }) });
  const h = c.host();
  assert.throws(() => h.decide({ proposal: ID1, decision: 'accept' }), { code: 'not_pending' });
  assert.throws(() => h.decide({ proposal: ID1, decision: 'refuse' }), { code: 'not_pending' });
  for (const id of ['nope', '../me', '', '.x', 'a/b', ID1 + '.md']) {
    assert.throws(() => h.decide({ proposal: id, decision: 'accept' }), { code: 'not_found' }, id);
  }
  c.cleanup();
});
