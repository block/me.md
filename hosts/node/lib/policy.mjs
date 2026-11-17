// policy.json (STORE.md section 5). It is read alone, before any other file.
import path from 'node:path';
import { classify, snapshot } from './fsx.mjs';
import { parseJson } from './json.mjs';

export const SPEC = '0.1';

const strict = new TextDecoder('utf-8', { fatal: true, ignoreBOM: true });
const MAX_POLICY = 1024 * 1024;

// Decide from a snapshot of policy.json.
// Returns { state, reason, specSupported, specValue, objectOk, members, text }.
export function evaluatePolicy(snap) {
  const base = { state: 'off', reason: '', specSupported: true, specValue: undefined, objectOk: false, members: null };
  if (snap.kind === 'none') return { ...base, state: 'on', reason: 'missing (S5.1)' };
  if (snap.kind === 'link') return { ...base, reason: 'is a symbolic link' };
  if (snap.kind !== 'file') return { ...base, reason: 'cannot be read' };
  if (snap.bytes.length > MAX_POLICY) return { ...base, reason: 'is too large to read' };
  let text;
  try {
    text = strict.decode(snap.bytes);
  } catch {
    return { ...base, reason: 'is not valid JSON (not UTF-8)' };
  }
  const j = parseJson(text);
  if (!j.ok) return { ...base, reason: 'is not valid JSON' };
  if (!(j.value instanceof Map)) return { ...base, reason: 'is not a JSON object' };
  if (j.duplicate) return { ...base, reason: 'repeats a member name' };
  const out = { ...base, objectOk: true, members: j.members };
  if (j.value.has('spec')) {
    out.specValue = j.value.get('spec');
    out.specSupported = out.specValue === SPEC;
  }
  if (j.value.get('state') === 'on') return { ...out, state: 'on', reason: 'state is "on"' };
  return { ...out, reason: 'state is not exactly "on"' };
}

export function readPolicy(root) {
  const p = path.join(root, 'policy.json');
  const c = classify(p);
  if (c.kind === 'error') return { ...evaluatePolicy({ kind: 'other' }) };
  let snap;
  try {
    snap = snapshot(p);
  } catch {
    snap = { kind: 'other' };
  }
  return evaluatePolicy(snap);
}

// New text for policy.json with `state` set (S5.6). Other members keep their
// exact values. A file that is not a usable object is replaced.
export function rewritePolicy(pol, newState) {
  if (!pol.objectOk) return `{"state": "${newState}", "spec": "${SPEC}"}\n`;
  const parts = [];
  let seen = false;
  for (const m of pol.members) {
    if (m.name === 'state') {
      seen = true;
      parts.push(`${m.rawKey}: "${newState}"`);
    } else parts.push(`${m.rawKey}: ${m.rawValue}`);
  }
  if (!seen) parts.unshift(`"state": "${newState}"`);
  return `{${parts.join(', ')}}\n`;
}
