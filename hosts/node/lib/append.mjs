// The append rule (S6.8), on bytes so that nothing else in the target changes.
import { breakStyle, toStyle, stripTrailingBreaks } from './text.mjs';

const LF = 0x0a;

function endsWithText(target, textBuf) {
  let end = target.length;
  if (end === 0 || target[end - 1] !== LF) return false;
  end--;
  // The closing break may be CRLF or LF. See SPEC_NOTES.
  if (end > 0 && target[end - 1] === 0x0d) end--;
  const start = end - textBuf.length;
  if (start < 0) return false;
  if (!target.subarray(start, end).equals(textBuf)) return false;
  return start === 0 || target[start - 1] === LF;
}

// target: Buffer or null (missing). Returns { content: Buffer | null, result }.
// result is 'created', 'added' or 'already'. content is null for 'already'.
// With idempotent false, step 2 of S6.8 is skipped.
export function applyAppend(target, body, { idempotent = true } = {}) {
  const style = target ? breakStyle(target) : '\n';
  const text = toStyle(stripTrailingBreaks(body), style);
  const textBuf = Buffer.from(text, 'utf8');
  const nl = Buffer.from(style);
  if (target === null) return { content: Buffer.concat([textBuf, Buffer.from('\n')]), result: 'created' };
  if (idempotent && endsWithText(target, textBuf)) return { content: null, result: 'already' };
  const parts = [target];
  if (target.length > 0 && target[target.length - 1] !== LF) parts.push(nl);
  parts.push(textBuf, nl);
  return { content: Buffer.concat(parts), result: 'added' };
}
