// File-system helpers. Nothing here follows a symbolic link inside the store.
import fs from 'node:fs';
import path from 'node:path';
import crypto from 'node:crypto';
import { ThouError } from './errors.mjs';
import { isoSeconds } from './text.mjs';

const C = fs.constants;
const NOFOLLOW = C.O_NOFOLLOW || 0;
const NONBLOCK = C.O_NONBLOCK || 0;
const MAX_READ = 64 * 1024 * 1024;

// What is at this path? Never follows a link.
export function classify(p) {
  let st;
  try {
    st = fs.lstatSync(p);
  } catch (e) {
    if (e.code === 'ENOENT' || e.code === 'ENOTDIR') return { kind: 'none' };
    return { kind: 'error', err: e };
  }
  if (st.isSymbolicLink()) return { kind: 'link', st };
  if (st.isFile()) return { kind: 'file', st };
  if (st.isDirectory()) return { kind: 'dir', st };
  return { kind: 'other', st };
}

// Read a regular file. Refuses links and anything that is not a plain file.
export function readRegular(p) {
  const fd = fs.openSync(p, C.O_RDONLY | NOFOLLOW | NONBLOCK);
  try {
    const st = fs.fstatSync(fd);
    if (!st.isFile()) throw Object.assign(new Error('not a regular file'), { code: 'ENOTREG' });
    if (st.size > MAX_READ) throw Object.assign(new Error('file too large'), { code: 'EFBIG' });
    return fs.readFileSync(fd);
  } finally {
    fs.closeSync(fd);
  }
}

// A comparable picture of a path, for the S8.4 re-read.
export function snapshot(p) {
  const c = classify(p);
  if (c.kind === 'file') return { kind: 'file', bytes: readRegular(p), mode: c.st.mode & 0o777 };
  if (c.kind === 'link') return { kind: 'link', link: fs.readlinkSync(p) };
  if (c.kind === 'error') throw c.err;
  return { kind: c.kind };
}

function sameSnapshot(a, b) {
  if (a.kind !== b.kind) return false;
  if (a.kind === 'file') return a.bytes.equals(b.bytes);
  if (a.kind === 'link') return a.link === b.link;
  return true;
}

export function sleep(ms) {
  Atomics.wait(new Int32Array(new SharedArrayBuffer(4)), 0, 0, ms);
}

const rm = (p) => {
  try {
    fs.unlinkSync(p);
  } catch {
    /* already gone */
  }
};

// Create a directory the person's account owns (S2.5). A link or file in the way is refused.
export function ensureDir(abs, rel) {
  let c = classify(abs);
  if (c.kind === 'none') {
    try {
      fs.mkdirSync(abs, { mode: 0o700 });
    } catch (e) {
      if (e.code !== 'EEXIST') throw e;
    }
    c = classify(abs);
  }
  if (c.kind !== 'dir') throw new ThouError('bad_path', `${rel} is not a plain directory in the store.`);
}

function writeNew(p, buf, mode) {
  const fd = fs.openSync(p, C.O_WRONLY | C.O_CREAT | C.O_EXCL, 0o600);
  try {
    fs.fchmodSync(fd, mode);
    fs.writeFileSync(fd, buf);
    fs.fsyncSync(fd);
  } finally {
    fs.closeSync(fd);
  }
}

// Create a file exclusively with all its content in place (S6.2, S8.5).
// Writes a hidden temp file, then hard-links it to the final name. The link
// fails if the name exists, and no reader ever sees a half-written file.
// Returns false if the name exists.
export function createExclusive(abs, buf) {
  const tmp = path.join(path.dirname(abs), `.${path.basename(abs)}.${crypto.randomBytes(6).toString('hex')}.tmp`);
  writeNew(tmp, buf, 0o600);
  try {
    fs.linkSync(tmp, abs);
    return true;
  } catch (e) {
    if (e.code === 'EEXIST') return false;
    if (!['EPERM', 'ENOSYS', 'EOPNOTSUPP', 'EXDEV', 'EACCES'].includes(e.code)) throw e;
    // The file system has no hard links. Fall back to exclusive create.
    try {
      writeNew(abs, buf, 0o600);
      return true;
    } catch (e2) {
      if (e2.code === 'EEXIST') return false;
      throw e2;
    }
  } finally {
    rm(tmp);
  }
}

// S8.4. compute(snapshot) returns { content: Buffer | null, result }.
// A null content writes nothing. Call with the store lock held.
export function safeReplace(abs, compute, { maxTries = 50 } = {}) {
  const tmp = path.join(path.dirname(abs), `.${path.basename(abs)}.tmp`);
  for (let n = 0; n < maxTries; n++) {
    const before = snapshot(abs); // step 1
    const r = compute(before);
    if (r.content == null) return r.result;
    rm(tmp);
    writeNew(tmp, r.content, before.mode ?? 0o600); // step 2
    let ok = false;
    try {
      const after = snapshot(abs); // step 3
      if (sameSnapshot(before, after)) {
        if (before.kind === 'none') {
          // Do not rename over a file that just appeared.
          if (createExclusive(abs, r.content)) ok = true;
        } else {
          fs.renameSync(tmp, abs); // step 4
          ok = true;
        }
      }
    } finally {
      rm(tmp);
    }
    if (ok) return r.result;
  }
  throw new ThouError('io_error', 'The file kept changing under the host, so it made no change.');
}

// S8.2 and S8.3. Returns { release }. Throws ThouError('locked').
export function acquireLock(root, { hostName, waitMs, now }) {
  const p = path.join(root, '.me.lock');
  const token = crypto.randomBytes(16).toString('hex');
  const deadline = Date.now() + waitMs;
  for (;;) {
    let fd;
    try {
      fd = fs.openSync(p, C.O_WRONLY | C.O_CREAT | C.O_EXCL, 0o600);
    } catch (e) {
      if (e.code !== 'EEXIST') throw e;
      if (Date.now() >= deadline) {
        throw new ThouError('locked', 'Another host holds .me.lock, so nothing was changed.', {
          notices: [
            '.me.lock is held. If no host is writing to the store, for example after a host stopped in the middle of a change, you can delete .me.lock and try again.',
          ],
        });
      }
      sleep(10 + Math.floor(Math.random() * 30));
      continue;
    }
    try {
      fs.writeSync(fd, `${token} ${hostName} ${isoSeconds(now())}\n`);
    } catch (e) {
      fs.closeSync(fd);
      rm(p); // we created it, so we may remove it
      throw e;
    }
    fs.closeSync(fd);
    return {
      release() {
        // Remove the file only if it still carries our token.
        try {
          const text = readRegular(p).toString('latin1');
          if (text.split('\n')[0].split(' ')[0] === token) rm(p);
        } catch {
          /* gone or unreadable: not ours to remove */
        }
      },
    };
  }
}

// S8.1. Append one complete entry in a single write. Returns null on success,
// or a sentence saying why there is no receipt.
export function appendJournal(root, line) {
  const p = path.join(root, 'journal.md');
  const c = classify(p);
  if (c.kind === 'link') return 'journal.md is a symbolic link, so the host did not append to it.';
  if (c.kind === 'dir' || c.kind === 'other') return 'journal.md is not a plain file.';
  let fd;
  try {
    fd = fs.openSync(p, C.O_RDWR | C.O_APPEND | C.O_CREAT | NOFOLLOW, 0o600);
    const size = fs.fstatSync(fd).size;
    let prefix = '';
    if (size > 0) {
      const last = Buffer.alloc(1);
      fs.readSync(fd, last, 0, 1, size - 1);
      if (last[0] !== 0x0a) prefix = '\n';
    }
    const buf = Buffer.from(`${prefix}${line}\n`, 'utf8');
    let done = fs.writeSync(fd, buf);
    while (done < buf.length) done += fs.writeSync(fd, buf, done); // a short write is rare
    return null;
  } catch (e) {
    return `The journal write failed (${e.code || e.message}).`;
  } finally {
    if (fd !== undefined) fs.closeSync(fd);
  }
}
