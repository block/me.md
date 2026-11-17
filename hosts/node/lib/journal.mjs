// The journal grammar (S7.1 to S7.4).
import { validTime } from './text.mjs';

export function formatEntry({ time, path, change, host, authority }) {
  for (const [k, v] of Object.entries({ path, change, host, authority })) {
    if (/[\r\n]/.test(v)) throw new Error(`journal field ${k} has a line break`);
  }
  if (/\|/.test(change) || /\|/.test(host)) throw new Error('change and host must not contain |');
  return `- ${time} | ${path} | ${change} | host: ${host} | authority: ${authority}`;
}

// Returns { ok: true, entry } or { ok: false, reason }. Only for lines that start with "- ".
export function parseEntry(line) {
  const l = line.replace(/\r$/, '');
  const parts = l.slice(2).split(' | ');
  if (parts.length !== 5) return { ok: false, reason: `expected 5 fields separated by ' | ', found ${parts.length}` };
  const [time, path, change, host, authority] = parts;
  if (!validTime(time)) return { ok: false, reason: 'time must be RFC 3339 UTC with Z' };
  if (path === '' || change === '') return { ok: false, reason: 'empty field' };
  if (!host.startsWith('host: ') || host.length <= 6) return { ok: false, reason: 'host field' };
  if (!authority.startsWith('authority: ')) return { ok: false, reason: 'authority field' };
  const a = authority.slice(11);
  if (!(a === 'person direct' || a === 'external edit' || /^accepted proposal \S+$/.test(a))) {
    return { ok: false, reason: 'authority value' };
  }
  return { ok: true, entry: { time, path, change, host: host.slice(6), authority: a } };
}

// Check a whole journal. Lines that do not start with "- " are ignored.
export function checkJournal(text) {
  const entries = [];
  const malformed = [];
  text.split('\n').forEach((raw, i) => {
    if (!raw.startsWith('- ')) return;
    const r = parseEntry(raw);
    if (r.ok) entries.push(r.entry);
    else malformed.push({ line: i + 1, reason: r.reason });
  });
  return { entries, malformed };
}
