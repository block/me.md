import test from 'node:test';
import assert from 'node:assert/strict';
import { tmpCtx, runDriver, PROP, ID1 } from './helpers.mjs';

test('host: name, version, level, enforcement', () => {
  const c = tmpCtx();
  const [r] = runDriver(c, [{ id: 'h', op: 'host' }]);
  assert.deepEqual(r, { id: 'h', ok: true, name: 'nodehost', version: '0.1.0', spec: '0.1', level: 'steward', enforcement: 'code' });
  c.cleanup();
});

test('one response per request, in order, ids echoed unchanged', () => {
  const c = tmpCtx();
  const ids = [1, 'two', null, { a: [1] }, 3.5];
  const rs = runDriver(c, ids.map((id) => ({ id, op: 'list' })));
  assert.deepEqual(rs.map((r) => r.id), ids);
  c.cleanup();
});

test('mount: absent, off, on, and the store path', () => {
  const c = tmpCtx({ 'me.md': 'CANARY\r\n' });
  const [m] = runDriver(c, [{ id: 1, op: 'mount' }]);
  assert.equal(m.memory, 'on');
  assert.equal(m.store, c.me);
  assert.deepEqual(m.files, [{ path: 'me.md', text: 'CANARY\r\n' }]);
  c.write('policy.json', '{"state": "off"}');
  const [o] = runDriver(c, [{ id: 1, op: 'mount' }]);
  assert.deepEqual([o.memory, o.files], ['off', []]);
  assert.ok(o.notices.length);
  c.cleanup();
});

test('unset ME_HOME: the store is HOME/.me', () => {
  const c = tmpCtx({});
  c.write('../home/.me/me.md', 'HOME-CANARY\n');
  const [m] = runDriver(c, [{ id: 1, op: 'mount' }], { ME_HOME: '' });
  assert.equal(m.files[0].text, 'HOME-CANARY\n');
  assert.equal(m.store, `${c.home}/.me`);
  c.cleanup();
});

test('bad_request and unsupported_op', () => {
  const c = tmpCtx();
  const rs = runDriver(c, [
    'not json', '[1]', '"x"', '{"id": 7}', '{"id": 8, "op": 5}', { id: 9, op: 'briefing' }, { id: 10, op: 'nope' },
    { id: 11, op: 'recall' }, { id: 12, op: 'propose', target: 'me.md' }, { id: 13, op: 'policy', state: 1 }, '', '   ',
    { id: 14, op: 'toString' }, { id: 15, op: '__proto__' },
  ]);
  assert.deepEqual(rs.map((r) => r.error), [
    'bad_request', 'bad_request', 'bad_request', 'bad_request', 'bad_request', 'unsupported_op', 'unsupported_op',
    'bad_request', 'bad_request', 'bad_request', 'unsupported_op', 'unsupported_op',
  ]);
  assert.deepEqual(rs.map((r) => r.id), [null, null, null, 7, 8, 9, 10, 11, 12, 13, 14, 15]);
  assert.ok(rs.every((r) => r.ok === false && typeof r.message === 'string'));
  c.cleanup();
});

test('a full session: propose, pending, revise, decide, recall, forget, policy', () => {
  const c = tmpCtx();
  const rs = runDriver(c, [
    { id: 1, op: 'mount' },
    { id: 2, op: 'propose', target: 'topics/travel.md', body: 'Prefer aisle seats.', basis: 'You asked twice.', agent: 'trip' },
  ]);
  const pid = rs[1].proposal;
  assert.equal(rs[1].id, 2);
  assert.match(pid, /^\d{8}T\d{6}Z-[a-z0-9]{4}$/);
  const r2 = runDriver(c, [
    { id: 3, op: 'pending' },
    { id: 4, op: 'revise', proposal: pid, body: 'Prefer aisle seats on flights.' },
    { id: 5, op: 'decide', proposal: pid, decision: 'accept' },
    { id: 6, op: 'list' },
    { id: 7, op: 'recall', paths: ['topics/travel.md', 'watches.md'] },
    { id: 8, op: 'decide', proposal: pid, decision: 'accept' },
    { id: 9, op: 'propose', target: 'me.md', body: 'Prefer aisle seats on flights.', basis: 'again' },
    { id: 10, op: 'forget', path: 'topics/travel.md', text: 'Prefer aisle seats on flights.' },
    { id: 11, op: 'policy', state: 'off' },
    { id: 12, op: 'recall', paths: ['me.md'] },
    { id: 13, op: 'policy', state: 'on' },
  ]);
  assert.equal(r2[0].proposals[0].id, pid);
  assert.equal(r2[1].ok, true);
  assert.equal(r2[2].applied, 'added');
  assert.equal(r2[2].journal.length, 2);
  assert.deepEqual(r2[3].topics, ['travel.md']);
  assert.equal(r2[4].files[0].text, 'Prefer aisle seats on flights.\n');
  assert.equal(r2[4].skipped[0].path, 'watches.md');
  assert.equal(r2[5].error, 'not_pending');
  assert.equal(r2[6].ok, true); // an accepted proposal does not block a proposal (only refused ones do)
  assert.equal(r2[7].removed, 1);
  assert.ok(r2[7].notices.length);
  assert.deepEqual([r2[8].memory, r2[8].journal.length], ['off', 1]);
  assert.deepEqual([r2[9].memory, r2[9].files], ['off', []]);
  assert.deepEqual([r2[10].memory, r2[10].journal.length], ['on', 1]);
});
