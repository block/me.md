import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import { tmpCtx } from './helpers.mjs';

const OFF_CASES = {
  'state off': '{"state": "off"}',
  'invalid JSON': '{"state": "on",',
  'uppercase ON': '{"state": "ON"}',
  'no state': '{}',
  'empty file': '',
  'duplicate state': '{"state": "on", "state": "off"}',
  'duplicate state, on last': '{"state": "off", "state": "on"}',
  'duplicate at depth': '{"state": "on", "x": {"a": 1, "a": 2}}',
  'duplicate inside array': '{"state": "on", "x": [{"a": 1, "a": 2}]}',
  'duplicate by escape': '{"state": "on", "\\u0073tate": "on"}',
  'array': '["state", "on"]',
  'string': '"on"',
  'state is a number': '{"state": 1}',
  'state is true': '{"state": true}',
  'state null': '{"state": null}',
  'trailing comma': '{"state": "on",}',
  'trailing junk': '{"state": "on"} x',
  'single quotes': "{'state': 'on'}",
  'byte order mark': '\ufeff{"state": "on"}',
  'NaN': '{"state": "on", "x": NaN}',
  'leading zero': '{"state": "on", "x": 01}',
};

for (const [name, content] of Object.entries(OFF_CASES)) {
  test(`off: ${name}`, () => {
    const c = tmpCtx({ 'me.md': 'CANARY\n', 'policy.json': content });
    try {
      const h = c.host();
      const before = c.tree();
      assert.equal(h.mount().memory, 'off');
      assert.deepEqual(h.mount().files, []);
      assert.equal(h.list().memory, 'off');
      const r = h.recall({ paths: ['me.md'] });
      assert.deepEqual(r.files, []);
      assert.equal(r.skipped.length, 1);
      assert.throws(() => h.propose({ target: 'me.md', body: 'x', basis: 'y' }), { code: 'memory_off' });
      assert.throws(() => h.edit({ path: 'me.md', action: 'append', text: 'x' }), { code: 'memory_off' });
      assert.deepEqual(c.tree(), before);
    } finally {
      c.cleanup();
    }
  });
}

test('off: invalid UTF-8 policy.json', () => {
  const c = tmpCtx({ 'me.md': 'x\n' });
  fs.writeFileSync(c.p('policy.json'), Buffer.from([0x7b, 0xff, 0x7d]));
  assert.equal(c.host().mount().memory, 'off');
  c.cleanup();
});

test('off: policy.json is a directory', () => {
  const c = tmpCtx();
  fs.mkdirSync(c.p('policy.json'));
  assert.equal(c.host().mount().memory, 'off');
  c.cleanup();
});

test('off: policy.json is a symbolic link to a file that says on', () => {
  const c = tmpCtx({ 'me.md': 'CANARY\n' });
  fs.writeFileSync(c.p('..', 'elsewhere.json'), '{"state": "on"}');
  fs.symlinkSync(c.p('..', 'elsewhere.json'), c.p('policy.json'));
  const h = c.host();
  assert.equal(h.mount().memory, 'off');
  assert.deepEqual(h.mount().files, []);
  c.cleanup();
});

test('off answers off even when me.md is missing (H1.5)', () => {
  const c = tmpCtx({ 'me.md': null, 'policy.json': '{"state": "off"}' });
  assert.equal(c.host().mount().memory, 'off');
  c.cleanup();
});

test('off notice says why', () => {
  const c = tmpCtx({ 'me.md': 'x\n', 'policy.json': '{"state": "ON"}' });
  assert.match(c.host().mount().notices.join(' '), /policy\.json/);
  c.cleanup();
});

const ON_CASES = {
  'missing file': null,
  'plain on': '{"state": "on"}',
  'extra member': '{"state": "on", "note": "x"}',
  'extra nested member': '{"note": {"a": [1, 2, {"b": null}]}, "state": "on"}',
  'spec 0.1': '{"state": "on", "spec": "0.1"}',
  'escaped on': '{"state": "\\u006fn"}',
  'whitespace': ' \n{ "state" : "on" }\n\n',
};
for (const [name, content] of Object.entries(ON_CASES)) {
  test(`on: ${name}`, () => {
    const c = tmpCtx({ 'me.md': 'CANARY\n', ...(content === null ? {} : { 'policy.json': content }) });
    const h = c.host();
    const m = h.mount();
    assert.equal(m.memory, 'on');
    assert.equal(m.files[0].text, 'CANARY\n');
    assert.notEqual(m.writable, false);
    c.cleanup();
  });
}

test('turning memory off between two recalls: the second returns nothing (H1.6)', () => {
  const c = tmpCtx({ 'me.md': 'a\n', 'topics/travel.md': 'CANARY\n' });
  const h = c.host();
  assert.equal(h.recall({ paths: ['topics/travel.md'] }).files.length, 1);
  fs.writeFileSync(c.p('policy.json'), '{"state": "off"}');
  const r = h.recall({ paths: ['topics/travel.md'] });
  assert.equal(r.memory, 'off');
  assert.deepEqual(r.files, []);
  c.cleanup();
});

for (const spec of ['9.0', '0.2', '0.10', '1.0', '', 'x']) {
  test(`unsupported spec ${JSON.stringify(spec)}: reads, no writes`, () => {
    const c = tmpCtx({ 'me.md': 'CANARY\n', 'policy.json': JSON.stringify({ state: 'on', spec }) });
    const h = c.host();
    const m = h.mount();
    assert.equal(m.memory, 'on');
    assert.equal(m.writable, false);
    assert.equal(m.files[0].text, 'CANARY\n');
    assert.ok(m.notices.length);
    const before = c.tree();
    assert.throws(() => h.propose({ target: 'me.md', body: 'x', basis: 'y' }), { code: 'unsupported_spec' });
    assert.throws(() => h.edit({ path: 'me.md', action: 'append', text: 'x' }), { code: 'unsupported_spec' });
    assert.throws(() => h.forget({ path: 'me.md', text: 'CANARY' }), { code: 'unsupported_spec' });
    assert.throws(() => h.policy({ state: 'on' }), { code: 'unsupported_spec' });
    assert.deepEqual(c.tree(), before);
    c.cleanup();
  });
}

test('a spec that is not a string is unsupported', () => {
  const c = tmpCtx({ 'policy.json': '{"state": "on", "spec": 0.1}' });
  assert.equal(c.host().mount().writable, false);
  c.cleanup();
});

test('unsupported spec: turning memory off is allowed and keeps spec', () => {
  const c = tmpCtx({ 'policy.json': '{"state": "on", "spec": "9.0", "n": 12345678901234567890}' });
  const r = c.host().policy({ state: 'off' });
  assert.equal(r.memory, 'off');
  assert.equal(c.text('policy.json'), '{"state": "off", "spec": "9.0", "n": 12345678901234567890}\n');
  assert.match(c.text('journal.md'), /policy\.json \| turned memory off \| host: nodehost 0\.1\.0 \| authority: person direct\n$/);
  c.cleanup();
});

test('policy: off then on, each with a journal entry (T12)', () => {
  const c = tmpCtx({ 'me.md': 'x\n', 'policy.json': '{"state": "on", "note": "keep me"}' });
  const h = c.host();
  const off = h.policy({ state: 'off', agent: 'tester' });
  assert.equal(off.memory, 'off');
  assert.equal(off.journal.length, 1);
  assert.match(off.journal[0], /^- \d{4}-\d\d-\d\dT\d\d:\d\d:\d\dZ \| policy\.json \| turned memory off \| host: nodehost 0\.1\.0 \(tester\) \| authority: person direct$/);
  assert.equal(JSON.parse(c.text('policy.json')).state, 'off');
  assert.equal(JSON.parse(c.text('policy.json')).note, 'keep me');
  // Memory is off, and the switch still works.
  const on = h.policy({ state: 'on' });
  assert.equal(on.memory, 'on');
  assert.equal(JSON.parse(c.text('policy.json')).state, 'on');
  assert.equal(c.text('journal.md').trim().split('\n').length, 2);
  // Nothing else in the store changed.
  assert.equal(c.text('me.md'), 'x\n');
  assert.ok(!c.exists('.me.lock'));
  c.cleanup();
});

test('policy: a file that is not an object is replaced', () => {
  for (const bad of ['{"state": "on",', '[]', '{"state": "on", "state": "on", "keep": 1}']) {
    const c = tmpCtx({ 'policy.json': bad });
    c.host().policy({ state: 'on' });
    assert.equal(c.text('policy.json'), '{"state": "on", "spec": "0.1"}\n');
    c.cleanup();
  }
});

test('policy: a symbolic link is replaced, and its target is not touched', () => {
  const c = tmpCtx();
  fs.writeFileSync(c.p('..', 'elsewhere.json'), '{"state": "off"}');
  fs.symlinkSync(c.p('..', 'elsewhere.json'), c.p('policy.json'));
  const r = c.host().policy({ state: 'on' });
  assert.equal(r.memory, 'on');
  assert.equal(fs.lstatSync(c.p('policy.json')).isSymbolicLink(), false);
  assert.equal(fs.readFileSync(c.p('..', 'elsewhere.json'), 'utf8'), '{"state": "off"}');
  c.cleanup();
});

test('policy: a missing policy.json is created with spec', () => {
  const c = tmpCtx();
  c.host().policy({ state: 'off' });
  assert.equal(c.text('policy.json'), '{"state": "off", "spec": "0.1"}\n');
  c.cleanup();
});

test('policy: no me.md means absent, and nothing is created', () => {
  const c = tmpCtx({});
  assert.throws(() => c.host().policy({ state: 'off' }), { code: 'absent' });
  assert.deepEqual(c.tree(), []);
  c.cleanup();
});
