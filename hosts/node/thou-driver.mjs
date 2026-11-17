#!/usr/bin/env node
// The conformance driver (conformance/DRIVER.md). JSON Lines on stdin and
// stdout, one process per session. Runs the same library that serves a person.
import readline from 'node:readline';
import { Thou, ThouError } from './lib/index.mjs';

// THOU_LOCK_WAIT_MS is a test knob: how long to wait for .me.lock.
const wait = Number(process.env.THOU_LOCK_WAIT_MS);
const host = new Thou({ lockWaitMs: Number.isFinite(wait) && wait >= 0 && process.env.THOU_LOCK_WAIT_MS !== '' ? wait : 3000 });

const OPS = {
  host: () => host.info(),
  mount: () => host.mount(),
  list: () => host.list(),
  recall: (r) => host.recall(r),
  pending: () => host.pending(),
  propose: (r) => host.propose(r),
  decide: (r) => host.decide(r),
  revise: (r) => host.revise(r),
  edit: (r) => host.edit(r),
  forget: (r) => host.forget(r),
  policy: (r) => host.policy(r),
};

function respond(obj) {
  process.stdout.write(JSON.stringify(obj) + '\n');
}

function handle(line) {
  let req;
  try {
    req = JSON.parse(line);
  } catch {
    return { id: null, ok: false, error: 'bad_request', message: 'The request is not valid JSON.' };
  }
  if (req === null || typeof req !== 'object' || Array.isArray(req)) {
    return { id: null, ok: false, error: 'bad_request', message: 'The request is not a JSON object.' };
  }
  const id = Object.hasOwn(req, 'id') ? req.id : null;
  if (typeof req.op !== 'string') return { id, ok: false, error: 'bad_request', message: 'The request has no op.' };
  if (!Object.hasOwn(OPS, req.op)) {
    return { id, ok: false, error: 'unsupported_op', message: `This host does not support the operation ${JSON.stringify(req.op)}.` };
  }
  try {
    return { id, ok: true, ...OPS[req.op](req) };
  } catch (e) {
    if (e instanceof ThouError) {
      const out = { id, ok: false, error: e.code, message: e.message, ...e.extra };
      if (e.notices.length) out.notices = e.notices;
      return out;
    }
    process.stderr.write(`${e.stack || e}\n`);
    return { id, ok: false, error: 'io_error', message: `The host hit a file error: ${e.code || e.message}.` };
  }
}

process.stdout.on('error', () => process.exit(0));
const rl = readline.createInterface({ input: process.stdin, crlfDelay: Infinity });
rl.on('line', (line) => {
  if (line.trim() === '') return;
  respond(handle(line));
});
