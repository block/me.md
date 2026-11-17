// The host: STORE.md and HOST.md, up to the Steward level.
// Everything is synchronous. Nothing is cached between calls (H1.3, H1.6, H5.2).
import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import crypto from 'node:crypto';
import { ThouError, badRequest } from './errors.mjs';
import {
  classify, readRegular, ensureDir, createExclusive, safeReplace, acquireLock, appendJournal,
} from './fsx.mjs';
import { readPolicy, evaluatePolicy, rewritePolicy, SPEC } from './policy.mjs';
import { parseProposal, parseTarget, formatProposal, withDecision, withBody, isProposalName } from './proposal.mjs';
import { applyAppend } from './append.mjs';
import { formatEntry } from './journal.mjs';
import {
  normalizeBody, splitLines, breakStyle, toStyle, stripTrailingBreaks, isoSeconds, idStamp,
  isWellFormed, cleanField,
} from './text.mjs';

export const HOST_NAME = 'nodehost';
export const HOST_VERSION = '0.1.0';
export const LEVEL = 'steward';
const FORGET_NOTICE =
  'I cannot delete what I do not control: copies your model provider may have kept, and anything already exported or copied elsewhere. Accepted proposals in proposals/ still hold their own text; delete those files too if you want that gone.';
const strict = new TextDecoder('utf-8', { fatal: true, ignoreBOM: true });
const ALNUM = 'abcdefghijklmnopqrstuvwxyz0123456789';

// S1.1. An empty ME_HOME counts as unset.
export function storeRoot(env) {
  const me = env.ME_HOME;
  if (me !== undefined && me !== '') return path.resolve(me);
  const home = (process.platform === 'win32' ? env.USERPROFILE : env.HOME) || os.homedir();
  return path.join(home, '.me');
}

const str = (req, k, { optional = false, nonEmpty = false } = {}) => {
  const v = req[k];
  if (v === undefined || v === null) {
    if (optional) return undefined;
    throw badRequest(`Missing field: ${k}.`);
  }
  if (typeof v !== 'string' || !isWellFormed(v)) throw badRequest(`Field ${k} must be a string.`);
  if (nonEmpty && v === '') throw badRequest(`Field ${k} must not be empty.`);
  return v;
};

// Bytes as latin1 text: one char per byte, so matching stays byte exact.
const lat = (buf) => buf.toString('latin1');
const unlat = (s) => Buffer.from(s, 'latin1');
const enc = (s) => lat(Buffer.from(s, 'utf8'));

export class Thou {
  constructor({ env = process.env, now = () => new Date(), lockWaitMs = 3000 } = {}) {
    this.env = env;
    this.now = now;
    this.lockWaitMs = lockWaitMs;
  }

  get root() {
    return storeRoot(this.env);
  }

  hostString(agent, withAgent = true) {
    const base = `${HOST_NAME} ${HOST_VERSION}`;
    const a = withAgent && agent ? cleanField(agent) : '';
    return a ? `${base} (${a})` : base;
  }

  info() {
    return { name: HOST_NAME, version: HOST_VERSION, spec: SPEC, level: LEVEL, enforcement: 'code' };
  }

  // H1.5: policy.json first, alone. Then me.md.
  state() {
    const root = this.root;
    const pol = readPolicy(root);
    const notices = [];
    if (pol.state === 'off') {
      notices.push(`Memory is off: policy.json ${pol.reason}.`);
      return { root, memory: 'off', writable: false, pol, notices };
    }
    const me = classify(path.join(root, 'me.md'));
    if (me.kind !== 'file') {
      notices.push(
        me.kind === 'link'
          ? 'me.md is a symbolic link, so the store counts as absent. A link to the whole store works.'
          : 'There is no me.md here, so there is no store.',
      );
      return { root, memory: 'absent', writable: false, pol, notices };
    }
    if (!pol.specSupported) {
      notices.push(
        `policy.json names spec ${JSON.stringify(pol.specValue)}. This host supports only "${SPEC}", so it will not write, except to turn memory off.`,
      );
    }
    return { root, memory: 'on', writable: pol.specSupported, pol, notices };
  }

  #ok(st, fields = {}, notices = []) {
    const out = { memory: st.memory };
    if (st.memory === 'on' && !st.writable) out.writable = false;
    Object.assign(out, fields);
    const all = [...st.notices, ...notices];
    if (all.length) out.notices = all;
    return out;
  }

  #gate(st) {
    const extra = { memory: st.memory };
    if (st.memory === 'absent') {
      throw new ThouError('absent', 'There is no store here, so nothing was written.', { notices: st.notices, extra });
    }
    if (st.memory === 'off') {
      throw new ThouError('memory_off', `Memory is off. ${st.notices[0] || ''} Nothing was written.`, { notices: st.notices, extra });
    }
    if (!st.writable) {
      throw new ThouError('unsupported_spec', 'policy.json names a spec this host does not support, so it wrote nothing.', {
        notices: st.notices, extra,
      });
    }
  }

  // Take the store lock, check the switch again, run fn, release (S8.2, H1.6).
  #locked(st, fn) {
    let lock;
    try {
      lock = acquireLock(st.root, { hostName: HOST_NAME, waitMs: this.lockWaitMs, now: this.now });
    } catch (e) {
      if (e instanceof ThouError) e.extra = { memory: st.memory };
      throw e;
    }
    try {
      const st2 = this.state();
      this.#gate(st2);
      return fn(st2);
    } finally {
      lock.release();
    }
  }

  // S8.7. Append entries after the lock is released.
  #journal(root, entries) {
    const lines = [];
    const notices = [];
    for (const e of entries) {
      const line = formatEntry({ time: isoSeconds(this.now()), ...e });
      const err = appendJournal(root, line);
      if (err) notices.push(`The change to ${e.path} was made, but it has no receipt in the journal. ${err}`);
      else lines.push(line);
    }
    return { lines, notices };
  }

  #readText(root, rel) {
    const dir = path.dirname(rel);
    if (dir !== '.') {
      const d = classify(path.join(root, dir));
      if (d.kind === 'none') return { skip: 'missing' };
      if (d.kind !== 'dir') return { skip: d.kind === 'link' ? 'symbolic link' : 'not a plain directory' };
    }
    const abs = path.join(root, rel);
    const f = classify(abs);
    if (f.kind === 'none') return { skip: 'missing' };
    if (f.kind === 'link') return { skip: 'symbolic link' };
    if (f.kind !== 'file') return { skip: 'not a regular file' };
    let buf;
    try {
      buf = readRegular(abs);
    } catch {
      return { skip: 'cannot be read' };
    }
    try {
      return { text: strict.decode(buf) };
    } catch {
      return { skip: 'not valid UTF-8' };
    }
  }

  mount() {
    const st = this.state();
    const files = [];
    const notices = [];
    if (st.memory === 'on') {
      const r = this.#readText(st.root, 'me.md');
      if (r.text !== undefined) files.push({ path: 'me.md', text: r.text });
      else notices.push(`me.md was not recalled: ${r.skip}.`);
    }
    return this.#ok(st, { store: st.root, files }, notices);
  }

  list() {
    const st = this.state();
    const out = { topics: [], projects: [], watches: false };
    const notices = [];
    if (st.memory === 'on') {
      for (const dir of ['topics', 'projects']) {
        const abs = path.join(st.root, dir);
        const d = classify(abs);
        if (d.kind === 'link') notices.push(`${dir}/ is a symbolic link, so it is ignored.`);
        if (d.kind !== 'dir') continue;
        let names = [];
        try {
          names = fs.readdirSync(abs).sort();
        } catch {
          /* unreadable: list nothing */
        }
        for (const n of names) {
          if (n.startsWith('.')) continue;
          const t = parseTarget(`${dir}/${n}`);
          const f = classify(path.join(abs, n));
          if (t && f.kind === 'file') out[dir].push(n);
          else notices.push(`Ignored ${dir}/${n}: ${t ? 'it is not a plain file' : 'its name breaks the naming rule'}.`);
        }
      }
      out.watches = classify(path.join(st.root, 'watches.md')).kind === 'file';
    }
    return this.#ok(st, out, notices);
  }

  recall(req) {
    if (!Array.isArray(req.paths) || req.paths.some((p) => typeof p !== 'string' || !isWellFormed(p))) {
      throw badRequest('Field paths must be a list of strings.');
    }
    const purpose = req.purpose === undefined ? 'task' : req.purpose;
    if (!['task', 'briefing', 'watches'].includes(purpose)) throw badRequest('Field purpose is not one of task, briefing, watches.');
    const st = this.state();
    const files = [];
    const skipped = [];
    for (const p of req.paths) {
      if (st.memory !== 'on') {
        skipped.push({ path: p, reason: `memory is ${st.memory}` });
        continue;
      }
      let r;
      if (p === 'watches.md') {
        r = purpose === 'task' ? { skip: 'watches.md is read only for a briefing or when asked (S4.3)' } : this.#readText(st.root, p);
      } else if (!parseTarget(p)) {
        r = { skip: p.split('/').some((s) => s.startsWith('.')) ? 'hidden or relative path' : 'not a path a host recalls' };
      } else r = this.#readText(st.root, p);
      if (r.text !== undefined) files.push({ path: p, text: r.text });
      else skipped.push({ path: p, reason: r.skip });
    }
    return this.#ok(st, { files, skipped });
  }

  // Read every proposal. Hidden files, other names and links are ignored (S2.1, S2.2, S2.4).
  #scan(root) {
    const items = [];
    const notices = [];
    const dir = path.join(root, 'proposals');
    const d = classify(dir);
    if (d.kind === 'link') notices.push('proposals/ is a symbolic link, so it is ignored.');
    if (d.kind !== 'dir') return { items, notices };
    let names = [];
    try {
      names = fs.readdirSync(dir).sort();
    } catch {
      return { items, notices };
    }
    for (const name of names) {
      if (name.startsWith('.') || !name.endsWith('.md')) continue;
      const abs = path.join(dir, name);
      if (classify(abs).kind !== 'file') continue;
      let buf;
      try {
        buf = readRegular(abs);
      } catch (e) {
        items.push({ name, valid: false, reason: `the file cannot be read (${e.code})`, looseBody: '' });
        continue;
      }
      items.push({ name, ...parseProposal(name, buf) });
    }
    return { items, notices };
  }

  pending() {
    const st = this.state();
    const out = { proposals: [], invalid: [] };
    const notices = [];
    if (st.memory === 'on') {
      const { items, notices: n } = this.#scan(st.root);
      notices.push(...n);
      for (const it of items) {
        const id = it.name.slice(0, -3);
        if (!it.valid) {
          out.invalid.push({ file: `proposals/${it.name}`, reason: it.reason });
          notices.push(`proposals/${it.name} is invalid: ${it.reason}. It is not applied, and it counts as refused.`);
        } else if (it.status === 'pending') {
          out.proposals.push({
            id,
            file: `proposals/${it.name}`,
            target: it.fm.target,
            'proposed-by': it.fm['proposed-by'],
            'proposed-at': it.fm['proposed-at'],
            basis: it.fm.basis,
            body: it.body,
          });
        }
      }
    }
    return this.#ok(st, out, notices);
  }

  propose(req) {
    const target = str(req, 'target');
    const body = str(req, 'body');
    const basis = str(req, 'basis');
    const agent = str(req, 'agent', { optional: true });
    const st = this.state();
    this.#gate(st);
    if (!parseTarget(target)) {
      throw new ThouError('bad_target', 'The target must be me.md, topics/<name>.md or projects/<name>.md.', { extra: { memory: st.memory } });
    }
    if (normalizeBody(body) === '') {
      throw new ThouError('empty_body', 'The proposal has no words in it.', { extra: { memory: st.memory } });
    }
    if (basis.replace(/[\s]/g, '') === '') throw badRequest('Field basis must not be empty.');
    // S6.11: refused and invalid proposals both count.
    const { items, notices } = this.#scan(st.root);
    const want = normalizeBody(body);
    for (const it of items) {
      const refusedBody = it.valid ? (it.status === 'refused' ? it.body : null) : it.looseBody;
      if (refusedBody !== null && normalizeBody(refusedBody) === want) {
        throw new ThouError('refused', `This was refused before (proposals/${it.name}), so it was not proposed again.`, {
          notices: it.valid ? [] : [`proposals/${it.name} is invalid: ${it.reason}. It counts as refused.`],
          extra: { memory: st.memory },
        });
      }
    }
    const dir = path.join(st.root, 'proposals');
    ensureDir(dir, 'proposals');
    const now = this.now();
    const content = formatProposal({
      target,
      proposedBy: this.hostString(agent),
      proposedAt: isoSeconds(now),
      basis,
      body,
    });
    for (let n = 0; n < 200; n++) {
      const suffix = Array.from(crypto.randomBytes(4), (b) => ALNUM[b % 36]).join('');
      const id = `${idStamp(now)}-${suffix}`;
      if (createExclusive(path.join(dir, `${id}.md`), Buffer.from(content, 'utf8'))) {
        return this.#ok(st, { proposal: id, file: `proposals/${id}.md` }, notices.filter((x) => x.includes('symbolic')));
      }
    }
    throw new ThouError('io_error', 'Could not find a free proposal name.');
  }

  // Look up a proposal by id, with the lock held.
  #loadProposal(root, id) {
    const bad = !id || id.length > 200 || /[\\/\0]/.test(id) || id.startsWith('.');
    const name = `${id}.md`;
    const abs = path.join(root, 'proposals', name);
    if (bad || classify(path.join(root, 'proposals')).kind !== 'dir' || classify(abs).kind !== 'file') {
      throw new ThouError('not_found', `There is no proposal ${id}.`, { extra: { memory: 'on' } });
    }
    const p = parseProposal(name, readRegular(abs));
    if (!p.valid) throw new ThouError('invalid_proposal', `proposals/${name} is invalid: ${p.reason}. It was not applied or changed.`, { extra: { memory: 'on' } });
    return { name, abs, p };
  }

  #checkTargetDir(root, t, code = 'bad_path') {
    if (!t.dir) return;
    const d = classify(path.join(root, t.dir));
    if (d.kind === 'link' || d.kind === 'file' || d.kind === 'other') {
      throw new ThouError(code, `${t.dir}/ is not a plain directory in the store.`, { extra: { memory: 'on' } });
    }
  }

  decide(req) {
    const id = str(req, 'proposal');
    const decision = str(req, 'decision');
    const agent = str(req, 'agent', { optional: true });
    if (decision !== 'accept' && decision !== 'refuse') throw badRequest('Field decision must be accept or refuse.');
    const st = this.state();
    this.#gate(st);
    const now = this.now();
    const host = this.hostString(agent);
    let applied = null;
    let created = false;
    let target;
    this.#locked(st, (st2) => {
      const { name, abs, p } = this.#loadProposal(st2.root, id);
      if (p.status !== 'pending') throw new ThouError('not_pending', `Proposal ${id} was already ${p.status}.`, { extra: { memory: 'on' } });
      target = p.target;
      if (decision === 'accept') {
        const t = parseTarget(p.target);
        this.#checkTargetDir(st2.root, t, 'bad_target');
        if (t.dir) ensureDir(path.join(st2.root, t.dir), t.dir);
        // Step 2: apply the body.
        const r = safeReplace(path.join(st2.root, p.target), (snap) => {
          if (snap.kind === 'none') return applyAppend(null, p.body);
          if (snap.kind !== 'file') throw new ThouError('bad_target', `${p.target} is not a plain file in the store, so it was not written.`, { extra: { memory: 'on' } });
          return applyAppend(snap.bytes, p.body);
        });
        applied = r === 'already' ? 'already' : 'added';
        created = r === 'created';
      }
      // Step 3: status and decided-at.
      const status = decision === 'accept' ? 'accepted' : 'refused';
      safeReplace(abs, (snap) => {
        const cur = snap.kind === 'file' ? parseProposal(name, snap.bytes) : { valid: false, reason: 'the file changed' };
        if (!cur.valid) throw new ThouError('invalid_proposal', `proposals/${name} changed and is now invalid: ${cur.reason}.`, { extra: { memory: 'on' } });
        if (cur.status !== 'pending') throw new ThouError('not_pending', `Proposal ${id} was already ${cur.status}.`, { extra: { memory: 'on' } });
        return { content: Buffer.from(withDecision(cur, status, isoSeconds(now), this.hostString(undefined, false)), 'utf8') };
      });
    });
    // Step 5: journal, decision first.
    const entries = [{ path: `proposals/${id}.md`, change: decision === 'accept' ? 'accepted' : 'refused', host, authority: 'person direct' }];
    if (decision === 'accept') {
      entries.push({
        path: target,
        change: applied === 'already' ? 'found the proposed text already at the end' : created ? 'created the file with proposed text' : 'added proposed text',
        host,
        authority: `accepted proposal ${id}`,
      });
    }
    const j = this.#journal(st.root, entries);
    return this.#ok({ ...st, notices: [] }, { status: decision === 'accept' ? 'accepted' : 'refused', applied, journal: j.lines }, j.notices);
  }

  revise(req) {
    const id = str(req, 'proposal');
    const body = str(req, 'body');
    const st = this.state();
    this.#gate(st);
    this.#locked(st, (st2) => {
      const { name, abs, p } = this.#loadProposal(st2.root, id);
      if (p.status !== 'pending') throw new ThouError('not_pending', `Proposal ${id} was already ${p.status}.`, { extra: { memory: 'on' } });
      if (normalizeBody(body) === '') throw new ThouError('empty_body', 'The new body has no words in it.', { extra: { memory: 'on' } });
      safeReplace(abs, (snap) => {
        const cur = snap.kind === 'file' ? parseProposal(name, snap.bytes) : { valid: false, reason: 'the file changed' };
        if (!cur.valid) throw new ThouError('invalid_proposal', `proposals/${name} changed and is now invalid: ${cur.reason}.`, { extra: { memory: 'on' } });
        if (cur.status !== 'pending') throw new ThouError('not_pending', `Proposal ${id} was already ${cur.status}.`, { extra: { memory: 'on' } });
        return { content: Buffer.from(withBody(cur, body), 'utf8') };
      });
    });
    return this.#ok({ ...st, notices: [] });
  }

  // me.md, watches.md, topics/<n>.md, projects/<n>.md.
  #personalPath(p) {
    const t = p === 'watches.md' ? { dir: null, name: p } : parseTarget(p);
    if (!t) throw new ThouError('bad_path', `${p} is not a file this operation may change.`);
    return t;
  }

  edit(req) {
    const p = str(req, 'path');
    const action = str(req, 'action');
    const agent = str(req, 'agent', { optional: true });
    if (action !== 'append' && action !== 'replace') throw badRequest('Field action must be append or replace.');
    let text, old, neu;
    if (action === 'append') {
      text = str(req, 'text');
      if (stripTrailingBreaks(text) === '') throw badRequest('Field text must not be empty.');
    } else {
      old = str(req, 'old', { nonEmpty: true });
      neu = str(req, 'new');
    }
    const t = this.#personalPath(p);
    const st = this.state();
    this.#gate(st);
    let change;
    this.#locked(st, (st2) => {
      this.#checkTargetDir(st2.root, t);
      const abs = path.join(st2.root, p);
      if (action === 'append') {
        if (t.dir) ensureDir(path.join(st2.root, t.dir), t.dir);
        safeReplace(abs, (snap) => {
          if (snap.kind === 'none') {
            if (p === 'me.md') throw new ThouError('absent', 'me.md is gone, and the host does not create it.', { extra: { memory: 'absent' } });
            change = 'created the file and added text';
            return applyAppend(null, text);
          }
          if (snap.kind !== 'file') throw new ThouError('bad_path', `${p} is not a plain file in the store.`);
          change = 'added text';
          return applyAppend(snap.bytes, text, { idempotent: false });
        });
      } else {
        safeReplace(abs, (snap) => {
          if (snap.kind === 'none') throw new ThouError('not_found', `${p} does not exist.`, { extra: { memory: 'on' } });
          if (snap.kind !== 'file') throw new ThouError('bad_path', `${p} is not a plain file in the store.`);
          const style = breakStyle(snap.bytes);
          const hay = lat(snap.bytes);
          const needle = enc(toStyle(old, style));
          const first = hay.indexOf(needle);
          if (first < 0) throw new ThouError('no_match', 'That text is not in the file.', { extra: { memory: 'on' } });
          if (hay.indexOf(needle, first + 1) >= 0) throw new ThouError('ambiguous', 'That text occurs more than once.', { extra: { memory: 'on' } });
          change = 'replaced text';
          const out = hay.slice(0, first) + enc(toStyle(neu, style)) + hay.slice(first + needle.length);
          return { content: unlat(out) };
        });
      }
    });
    const j = this.#journal(st.root, [{ path: p, change, host: this.hostString(agent), authority: 'person direct' }]);
    return this.#ok({ ...st, notices: [] }, { journal: j.lines }, j.notices);
  }

  forget(req) {
    const p = str(req, 'path');
    const text = str(req, 'text', { optional: true });
    const agent = str(req, 'agent', { optional: true });
    if (text !== undefined && stripTrailingBreaks(text) === '') throw badRequest('Field text must not be empty.');
    const t = this.#personalPath(p);
    const st = this.state();
    this.#gate(st);
    let removed = 0;
    let change;
    this.#locked(st, (st2) => {
      this.#checkTargetDir(st2.root, t);
      const abs = path.join(st2.root, p);
      if (text === undefined) {
        const c = classify(abs);
        if (c.kind === 'none') throw new ThouError('not_found', `${p} does not exist.`, { extra: { memory: 'on' } });
        if (c.kind !== 'file') throw new ThouError('bad_path', `${p} is not a plain file in the store.`);
        fs.unlinkSync(abs);
        removed = 1;
        change = 'removed the file';
        return;
      }
      safeReplace(abs, (snap) => {
        if (snap.kind === 'none') throw new ThouError('not_found', `${p} does not exist.`, { extra: { memory: 'on' } });
        if (snap.kind !== 'file') throw new ThouError('bad_path', `${p} is not a plain file in the store.`);
        const want = splitLines(stripTrailingBreaks(enc(text))).map((l) => l.text);
        const lines = splitLines(lat(snap.bytes));
        const keep = [];
        let n = 0;
        for (let i = 0; i < lines.length; ) {
          let hit = i + want.length <= lines.length;
          for (let k = 0; hit && k < want.length; k++) if (lines[i + k].text !== want[k]) hit = false;
          if (hit) {
            n++;
            i += want.length;
          } else keep.push(lines[i++].text + lines[i - 1].term);
        }
        if (n === 0) throw new ThouError('no_match', 'That text is not in the file as whole lines.', { extra: { memory: 'on' } });
        removed = n;
        change = 'removed text';
        return { content: unlat(keep.join('')) };
      });
    });
    const j = this.#journal(st.root, [{ path: p, change, host: this.hostString(agent), authority: 'person direct' }]);
    return this.#ok(this.state(), { removed, journal: j.lines }, [...j.notices, FORGET_NOTICE]);
  }

  // S5.6. Works while memory is off.
  policy(req) {
    const state = str(req, 'state');
    const agent = str(req, 'agent', { optional: true });
    if (state !== 'on' && state !== 'off') throw badRequest('Field state must be on or off.');
    const root = this.root;
    const me = classify(path.join(root, 'me.md'));
    if (me.kind !== 'file') {
      throw new ThouError('absent', 'There is no store here, and the host does not create one.', { extra: { memory: 'absent' } });
    }
    let lock;
    try {
      lock = acquireLock(root, { hostName: HOST_NAME, waitMs: this.lockWaitMs, now: this.now });
    } catch (e) {
      if (e instanceof ThouError) e.extra = { memory: this.state().memory };
      throw e;
    }
    try {
      safeReplace(path.join(root, 'policy.json'), (snap) => {
        if (snap.kind === 'dir' || snap.kind === 'other') {
          throw new ThouError('io_error', 'policy.json is not a file, so the host cannot replace it.');
        }
        const pol = evaluatePolicy(snap);
        if (state === 'on' && pol.objectOk && !pol.specSupported) {
          throw new ThouError('unsupported_spec', 'policy.json names a spec this host does not support, so it may only turn memory off.', {
            notices: [`policy.json names spec ${JSON.stringify(pol.specValue)}.`],
            extra: { memory: this.state().memory },
          });
        }
        return { content: Buffer.from(rewritePolicy(pol, state), 'utf8') };
      });
    } finally {
      lock.release();
    }
    const j = this.#journal(root, [
      { path: 'policy.json', change: `turned memory ${state}`, host: this.hostString(agent), authority: 'person direct' },
    ]);
    const after = this.state();
    const extra = state === 'off' ? ['Memory is off. This host enforces that in its own code, below the model. Software that ignores policy.json is not stopped.'] : [];
    return this.#ok({ ...after, notices: [] }, { journal: j.lines }, [...extra, ...j.notices]);
  }
}
