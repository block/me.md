// Text helpers: normalization (S6.11), line handling (S2.3), time.

// Unicode White_Space.
const WS = '[\\t\\n\\u000b\\f\\r \\u0085\\u00a0\\u1680\\u2000-\\u200a\\u2028\\u2029\\u202f\\u205f\\u3000]';
const WS_ENDS = new RegExp(`^${WS}+|${WS}+$`, 'g');
const WS_RUN = new RegExp(`${WS}+`, 'g');

// S6.11: NFC, trim, collapse runs of white space to one space.
export function normalizeBody(s) {
  return s.normalize('NFC').replace(WS_ENDS, '').replace(WS_RUN, ' ');
}

// Split into lines. text has no terminator and no CR of a CRLF.
export function splitLines(s) {
  const out = [];
  let i = 0;
  while (i < s.length) {
    const nl = s.indexOf('\n', i);
    if (nl === -1) {
      out.push({ text: s.slice(i), term: '', start: i, next: s.length });
      break;
    }
    let end = nl;
    let term = '\n';
    if (nl > i && s[nl - 1] === '\r') {
      end = nl - 1;
      term = '\r\n';
    }
    out.push({ text: s.slice(i, end), term, start: i, next: nl + 1 });
    i = nl + 1;
  }
  return out;
}

// The file's line break: CRLF if its first line break is CRLF, else LF.
export function breakStyle(buf) {
  const i = buf.indexOf(0x0a);
  return i > 0 && buf[i - 1] === 0x0d ? '\r\n' : '\n';
}

export function toStyle(text, style) {
  const lf = text.replace(/\r\n/g, '\n');
  return style === '\n' ? lf : lf.replace(/\n/g, '\r\n');
}

export function stripTrailingBreaks(s) {
  return s.replace(/(?:\r?\n)+$/, '');
}

export function isoSeconds(d) {
  return d.toISOString().slice(0, 19) + 'Z';
}

export function idStamp(d) {
  return isoSeconds(d).replace(/[-:]/g, '');
}

function daysIn(y, m) {
  if (m === 2) return (y % 4 === 0 && y % 100 !== 0) || y % 400 === 0 ? 29 : 28;
  return [4, 6, 9, 11].includes(m) ? 30 : 31;
}

// RFC 3339 UTC with Z and whole seconds.
export function validTime(s) {
  const m = /^(\d{4})-(\d{2})-(\d{2})T(\d{2}):(\d{2}):(\d{2})Z$/.exec(s);
  if (!m) return false;
  const [y, mo, d, h, mi, se] = m.slice(1).map(Number);
  if (mo < 1 || mo > 12 || d < 1 || d > daysIn(y, mo)) return false;
  return h <= 23 && mi <= 59 && se <= 60;
}

export const isWellFormed = (s) => (typeof s.isWellFormed === 'function' ? s.isWellFormed() : true);

// Fixed host strings go in the journal and in proposals: no | and no line breaks (S7.2).
export function cleanField(s) {
  return s.replace(/[|\r\n\u2028\u2029\u0085]/g, ' ').replace(/ +/g, ' ').trim().slice(0, 200);
}
