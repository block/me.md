// A strict JSON parser (RFC 8259). JSON.parse cannot report duplicate member
// names, and S5.2 needs that at any depth. It also records the raw text of
// each top-level member so policy.json can be rewritten without changing the
// other members' values (S5.6).

const MAX_DEPTH = 256;

export function parseJson(text) {
  let i = 0;
  let duplicate = false;
  let members = null;

  const fail = (m) => {
    throw new SyntaxError(`${m} at ${i}`);
  };
  const ws = () => {
    while (i < text.length) {
      const c = text.charCodeAt(i);
      if (c === 0x20 || c === 0x09 || c === 0x0a || c === 0x0d) i++;
      else break;
    }
  };

  function str() {
    i++; // opening quote
    let out = '';
    for (;;) {
      if (i >= text.length) fail('unterminated string');
      const c = text.charCodeAt(i);
      if (c === 0x22) {
        i++;
        return out;
      }
      if (c < 0x20) fail('control character in string');
      if (c === 0x5c) {
        i++;
        const e = text[i];
        if (e === '"' || e === '\\' || e === '/') out += e;
        else if (e === 'b') out += '\b';
        else if (e === 'f') out += '\f';
        else if (e === 'n') out += '\n';
        else if (e === 'r') out += '\r';
        else if (e === 't') out += '\t';
        else if (e === 'u') {
          const h = text.slice(i + 1, i + 5);
          if (!/^[0-9a-fA-F]{4}$/.test(h)) fail('bad \\u escape');
          out += String.fromCharCode(parseInt(h, 16));
          i += 4;
        } else fail('bad escape');
        i++;
      } else {
        out += text[i];
        i++;
      }
    }
  }

  const NUM = /-?(?:0|[1-9][0-9]*)(?:\.[0-9]+)?(?:[eE][+-]?[0-9]+)?/y;

  function val(depth) {
    if (depth > MAX_DEPTH) fail('too deep');
    ws();
    const c = text[i];
    if (c === '{') return obj(depth);
    if (c === '[') return arr(depth);
    if (c === '"') return str();
    if (c === 't' && text.startsWith('true', i)) return ((i += 4), true);
    if (c === 'f' && text.startsWith('false', i)) return ((i += 5), false);
    if (c === 'n' && text.startsWith('null', i)) return ((i += 4), null);
    NUM.lastIndex = i;
    const m = NUM.exec(text);
    if (!m) fail('unexpected character');
    i += m[0].length;
    return Number(m[0]);
  }

  function arr(depth) {
    i++;
    const out = [];
    ws();
    if (text[i] === ']') {
      i++;
      return out;
    }
    for (;;) {
      out.push(val(depth + 1));
      ws();
      if (text[i] === ',') {
        i++;
        continue;
      }
      if (text[i] === ']') {
        i++;
        return out;
      }
      fail('expected , or ]');
    }
  }

  function obj(depth) {
    i++;
    const map = new Map();
    const spans = [];
    ws();
    if (text[i] === '}') {
      i++;
      if (depth === 0) members = spans;
      return map;
    }
    for (;;) {
      ws();
      if (text[i] !== '"') fail('expected a member name');
      const ks = i;
      const k = str();
      const ke = i;
      ws();
      if (text[i] !== ':') fail('expected :');
      i++;
      ws();
      const vs = i;
      const v = val(depth + 1);
      const ve = i;
      if (map.has(k)) duplicate = true;
      map.set(k, v);
      if (depth === 0) spans.push({ name: k, rawKey: text.slice(ks, ke), rawValue: text.slice(vs, ve) });
      ws();
      if (text[i] === ',') {
        i++;
        continue;
      }
      if (text[i] === '}') {
        i++;
        if (depth === 0) members = spans;
        return map;
      }
      fail('expected , or }');
    }
  }

  try {
    const value = val(0);
    ws();
    if (i < text.length) fail('trailing characters');
    return { ok: true, value, duplicate, members };
  } catch (e) {
    // SyntaxError, or RangeError if the stack ran out: both mean "not usable".
    return { ok: false, error: e.message };
  }
}
