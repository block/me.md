// Proposal files (STORE.md section 6): names, front matter, validity, rewriting.
import { splitLines, validTime, toStyle, stripTrailingBreaks, normalizeBody } from './text.mjs';

const strict = new TextDecoder('utf-8', { fatal: true, ignoreBOM: true });

// S2.1
export function validName(n) {
  return /^[a-z0-9][a-z0-9._-]*\.md$/.test(n) && n.length - 3 <= 64;
}

// S6.1. The id is checked as a format, not as a calendar date.
export function isProposalName(name) {
  const m = /^(\d{8}T\d{6}Z-[a-z0-9]{4,})\.md$/.exec(name);
  return !!m && m[1].length <= 64;
}

// me.md, topics/<name>.md or projects/<name>.md, else null.
export function parseTarget(t) {
  if (t === 'me.md') return { dir: null, name: 'me.md' };
  const m = /^(topics|projects)\/(.+)$/.exec(t);
  if (!m || !validName(m[2])) return null;
  return { dir: m[1], name: m[2] };
}

const REQUIRED = ['status', 'target', 'proposed-by', 'proposed-at', 'basis'];

function parseValue(raw) {
  const v = raw.replace(/^ +| +$/g, '');
  if (!v.startsWith('"')) return { ok: true, value: v };
  let out = '';
  let i = 1;
  for (;;) {
    if (i >= v.length) return { ok: false };
    const c = v[i];
    if (c === '"') return i === v.length - 1 ? { ok: true, value: out } : { ok: false };
    if (c === '\\') {
      const n = v[i + 1];
      if (n === '"' || n === '\\') {
        out += n;
        i += 2;
        continue;
      }
      return { ok: false };
    }
    out += c;
    i++;
  }
}

const isBlank = (s) => /^[ \t]*$/.test(s);

// S6.14: the body of an invalid proposal, for refusal matching.
// Everything after the first closing ---, or the whole file if there is none.
function looseBody(buf) {
  const text = buf.toString('utf8');
  const lines = splitLines(text);
  if (lines.length && lines[0].text === '---') {
    for (let i = 1; i < lines.length; i++) if (lines[i].text === '---') return text.slice(lines[i].next);
  }
  return text;
}

// Parse a proposal file. Returns { valid: true, ... } or { valid: false, reason, looseBody }.
export function parseProposal(name, buf) {
  const loose = looseBody(buf);
  const fail = (reason) => ({ valid: false, reason, looseBody: loose });
  if (!isProposalName(name)) return fail('the file name does not follow S6.1');
  let text;
  try {
    text = strict.decode(buf);
  } catch {
    return fail('the file is not valid UTF-8');
  }
  const lines = splitLines(text);
  if (!lines.length || lines[0].text !== '---') return fail('line 1 is not exactly ---');
  let close = -1;
  for (let i = 1; i < lines.length; i++) {
    if (lines[i].text === '---') {
      close = i;
      break;
    }
  }
  if (close < 0) return fail('the front matter has no closing ---');
  const fm = {};
  const keyLine = {};
  for (let i = 1; i < close; i++) {
    const t = lines[i].text;
    if (isBlank(t) || t.startsWith('#')) continue;
    const m = /^([a-z][a-z-]*):(?: ([\s\S]*))?$/.exec(t);
    if (!m) return fail(`front matter line ${i + 1} is not "key: value"`);
    if (Object.hasOwn(fm, m[1])) return fail(`the key ${m[1]} appears more than once`);
    const v = parseValue(m[2] ?? '');
    if (!v.ok) return fail(`front matter line ${i + 1} has a bad quoted value`);
    fm[m[1]] = v.value;
    keyLine[m[1]] = i;
  }
  for (const k of REQUIRED) {
    if (!Object.hasOwn(fm, k)) return fail(`missing required key: ${k}`);
    if (fm[k] === '') return fail(`required key ${k} is empty`);
  }
  if (!['pending', 'accepted', 'refused'].includes(fm.status)) return fail('status must be pending, accepted or refused');
  if (!parseTarget(fm.target)) return fail('target must be me.md, topics/<name>.md or projects/<name>.md');
  if (fm['proposed-by'].includes('|')) return fail('proposed-by must not contain |');
  if (!validTime(fm['proposed-at'])) return fail('proposed-at must be RFC 3339 UTC with Z');
  if (Object.hasOwn(fm, 'decided-at') && !validTime(fm['decided-at'])) return fail('decided-at must be RFC 3339 UTC with Z');
  // Body: after the closing line, one blank line skipped.
  let bodyStart = lines[close].next;
  const after = lines[close + 1];
  if (after && isBlank(after.text)) bodyStart = after.next;
  const raw = text.slice(bodyStart);
  const body = stripTrailingBreaks(raw);
  if (normalizeBody(body) === '') return fail('the body is empty');
  const first = lines.find((l) => l.term);
  return {
    valid: true,
    fm,
    keyLine,
    lines,
    text,
    close,
    bodyStart,
    body,
    status: fm.status,
    target: fm.target,
    style: first ? first.term : '\n',
  };
}

// A front-matter value, quoted only when it has to be.
function fmValue(v) {
  const flat = v.replace(/[\r\n]/g, ' ').replace(/^ +| +$/g, '');
  if (flat === '' || flat.startsWith('"')) return `"${flat.replace(/\\/g, '\\\\').replace(/"/g, '\\"')}"`;
  return flat;
}

// A new proposal file. New files use LF.
export function formatProposal({ target, proposedBy, proposedAt, basis, body }) {
  const b = stripTrailingBreaks(toStyle(body, '\n'));
  return [
    '---',
    'status: pending',
    `target: ${target}`,
    `proposed-by: ${fmValue(proposedBy)}`,
    `proposed-at: ${proposedAt}`,
    `basis: ${fmValue(basis)}`,
    '---',
    '',
    b,
    '',
  ].join('\n');
}

// Set status and decided-at (S8.6). Every other byte stays. Inserted lines use the file's line break.
export function withDecision(p, status, decidedAt, decidedVia) {
  const kl = p.keyLine;
  const repl = new Map([[kl.status, `status: ${status}`]]);
  const ins = new Map();
  const add = (idx, s) => ins.set(idx, [...(ins.get(idx) || []), s]);
  if (Object.hasOwn(kl, 'decided-at')) repl.set(kl['decided-at'], `decided-at: ${decidedAt}`);
  else add(kl.status, `decided-at: ${decidedAt}`);
  const viaAnchor = Object.hasOwn(kl, 'decided-at') ? kl['decided-at'] : kl.status;
  if (Object.hasOwn(kl, 'decided-via')) repl.set(kl['decided-via'], `decided-via: ${decidedVia}`);
  else add(viaAnchor, `decided-via: ${decidedVia}`);
  let out = '';
  p.lines.forEach((l, i) => {
    out += (repl.get(i) ?? l.text) + l.term;
    for (const s of ins.get(i) || []) out += s + p.style;
  });
  return out;
}

// Replace the body, keep the front matter (S6.15).
export function withBody(p, newBody) {
  const head = p.text.slice(0, p.lines[p.close].next);
  return head + p.style + stripTrailingBreaks(toStyle(newBody, p.style)) + p.style;
}
