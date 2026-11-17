#!/usr/bin/env python3
"""thou conformance runner: drives a host's driver through the engine-level
part of the black-box tests in HOST.md (T1-T17), then checks the store.

It follows conformance/DRIVER.md. It was written from the spec alone. It does
not know how any host works inside. Python 3.9, standard library only.

Usage:
  python3 thou_conform.py --host "<driver command>" [--second-host "<cmd>"]
                          [--repeat N] [--only T3,T6] [--json] [--keep]

Exit: 0 every test that ran passed; 1 a test failed; 2 usage or driver start error.
Pass means the host's code passed the engine-level tests. It is not a
conformance claim by itself.
"""

import argparse
import datetime
import json
import os
import queue
import re
import secrets
import shlex
import shutil
import signal
import stat
import subprocess
import sys
import tempfile
import threading
import time
import traceback
import unicodedata

HERE = os.path.dirname(os.path.abspath(__file__))
TOOLS = os.path.normpath(os.path.join(HERE, "..", "..", "tools"))
if TOOLS not in sys.path:
    sys.path.insert(0, TOOLS)
import thou_lint  # noqa: E402  (checks the stores that hosts write)

__version__ = "0.1"

LEVELS = ["reader", "proposer", "steward", "briefer"]
OP_LEVEL = {"host": 0, "mount": 0, "list": 0, "recall": 0, "pending": 1, "propose": 1,
            "decide": 2, "revise": 2, "edit": 2, "forget": 2, "policy": 2}
ERROR_CODES = {"absent", "memory_off", "unsupported_spec", "refused", "bad_target", "bad_path",
               "empty_body", "not_found", "invalid_proposal", "not_pending", "no_match",
               "ambiguous", "locked", "unsupported_op", "bad_request", "io_error"}
MEMORY_STATES = {"absent", "off", "on"}
MEMORY_OPS = {"mount", "list", "recall", "pending", "propose", "decide", "revise", "edit",
              "forget", "policy"}
JOURNAL_OPS = {"decide", "edit", "forget", "policy"}
DEFAULT_TIMEOUT = 10.0
MAX_LINE = 32 * 1024 * 1024
MAX_FILE_SEARCH = 10 * 1024 * 1024
XDG = {"XDG_CONFIG_HOME": "config", "XDG_DATA_HOME": "data", "XDG_STATE_HOME": "state",
       "XDG_CACHE_HOME": "cache"}
DRV = "DRIVER.md"

NOT_RUN = {
    "T4": "Needs a model: instruction-shaped text in the store must never make the agent call a tool (DRIVER.md, 'What a driver cannot show').",
    "T18": "Needs a model: a briefing is produced by an agent (DRIVER.md, 'What a driver cannot show').",
}
NOT_RUN_PARTS = {
    "T2": ["Last step: what the person says now wins over me.md (H2.3). Needs a model."],
    "T7": ["Whether the agent asks for watches.md only in a briefing or when asked about watches (H2.1, S4.3). Needs a model. The runner checks the engine's purpose rule only."],
    "T8": ["Whether the agent states a preference only by implication and then proposes (H2.1, H3.1). Needs a model. The runner checks the propose operation only."],
}


class DriverError(Exception):
    pass


# --------------------------------------------------------------------------
# small helpers

def utcnow():
    return datetime.datetime.now(datetime.timezone.utc)


def fmt_time(dt):
    return dt.strftime("%Y-%m-%dT%H:%M:%SZ")


def time_near_now(text, slack=300):
    try:
        when = datetime.datetime.strptime(text, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=datetime.timezone.utc)
    except (ValueError, TypeError):
        return False
    return abs((utcnow() - when).total_seconds()) <= slack


def slurp(path):
    with open(path, "r") as handle:
        return handle.read()


def b(text):
    return text if isinstance(text, bytes) else text.encode("utf-8")


def keep_ends(data):
    """Split bytes into lines that keep their LF (and CR before it)."""
    return [p for p in re.split(b"(?<=\n)", data) if p != b""]


def first_break_is_crlf(data):
    i = data.find(b"\n")
    return i > 0 and data[i - 1:i] == b"\r"


class Resp(dict):
    raw = ""


# --------------------------------------------------------------------------
# store snapshots

def snapshot(root):
    """Paths, bytes, symlink targets and modes under root. None if root is missing."""
    try:
        os.lstat(root)
    except OSError:
        return None
    snap = {}

    def visit(path, rel):
        st = os.lstat(path)
        mode = stat.S_IMODE(st.st_mode)
        if stat.S_ISLNK(st.st_mode):
            snap[rel] = ("link", os.readlink(path))
        elif stat.S_ISDIR(st.st_mode):
            snap[rel] = ("dir", mode)
            try:
                names = sorted(os.listdir(path))
            except OSError:
                snap[rel] = ("dir-unreadable", mode)
                return
            for name in names:
                visit(os.path.join(path, name), name if rel == "." else rel + "/" + name)
        elif stat.S_ISREG(st.st_mode):
            try:
                with open(path, "rb") as handle:
                    data = handle.read()
            except OSError:
                data = b"<unreadable>"
            snap[rel] = ("file", mode, data)
        else:
            snap[rel] = ("other", st.st_mode)

    visit(root, ".")
    return snap


def snap_diff(old, new):
    if old is None and new is None:
        return []
    if old is None:
        return ["created the store directory"]
    if new is None:
        return ["removed the store directory"]
    out = []
    for key in sorted(set(old) | set(new)):
        if key not in old:
            out.append("added " + key)
        elif key not in new:
            out.append("removed " + key)
        elif old[key] != new[key]:
            out.append("changed " + key)
    return out


# --------------------------------------------------------------------------
# driver process

def validate_response(req, resp, level_n):
    """Return a list of problems with a driver response (DRIVER.md)."""
    probs = []
    if not isinstance(resp, dict):
        return ["response is not a JSON object"]
    op = req["op"]
    if "id" not in resp:
        probs.append("response has no id")
    elif resp["id"] != req["id"] or type(resp["id"]) is not type(req["id"]):
        probs.append("response id %r does not match request id %r" % (resp["id"], req["id"]))
    ok = resp.get("ok")
    if not isinstance(ok, bool):
        probs.append("ok is missing or not a boolean")
        return probs
    if "notices" in resp and not (isinstance(resp["notices"], list)
                                  and all(isinstance(n, str) for n in resp["notices"])):
        probs.append("notices is not a list of strings")
    if "memory" in resp and resp["memory"] not in MEMORY_STATES:
        probs.append("memory is %r, not absent, off or on" % (resp["memory"],))
    if not ok:
        if resp.get("error") not in ERROR_CODES:
            probs.append("error code %r is not one DRIVER.md lists" % (resp.get("error"),))
        if not (isinstance(resp.get("message"), str) and resp["message"].strip()):
            probs.append("an error response has no message")
        return probs
    if op in MEMORY_OPS and "memory" not in resp:
        probs.append("%s answered without memory" % op)
    memory = resp.get("memory")
    if op == "host":
        for key in ("name", "version", "spec", "level", "enforcement"):
            if not isinstance(resp.get(key), str) or not resp.get(key):
                probs.append("host answer lacks a string %s" % key)
        if resp.get("level") not in LEVELS:
            probs.append("host level %r is not reader, proposer, steward or briefer" % (resp.get("level"),))
        if resp.get("enforcement") not in ("code", "instruction"):
            probs.append("host enforcement %r is not code or instruction" % (resp.get("enforcement"),))
    elif op == "mount":
        if not (isinstance(resp.get("store"), str) and os.path.isabs(resp["store"])):
            probs.append("mount: store is not an absolute path")
        files = resp.get("files")
        if not isinstance(files, list) or not all(
                isinstance(f, dict) and isinstance(f.get("path"), str) and isinstance(f.get("text"), str)
                for f in files):
            probs.append("mount: files is not a list of {path, text}")
        elif memory == "on" and [f["path"] for f in files] != ["me.md"]:
            probs.append("mount: files must hold only me.md when memory is on")
        elif memory != "on" and files:
            probs.append("mount: files must be empty unless memory is on")
    elif op == "list":
        for key in ("topics", "projects"):
            if not (isinstance(resp.get(key), list) and all(isinstance(n, str) for n in resp[key])):
                probs.append("list: %s is not a list of names" % key)
        if not isinstance(resp.get("watches"), bool):
            probs.append("list: watches is not a boolean")
    elif op == "recall":
        files, skipped = resp.get("files"), resp.get("skipped")
        if not (isinstance(files, list) and isinstance(skipped, list)):
            probs.append("recall: files and skipped must be lists")
        else:
            got = []
            for item in files + skipped:
                if not (isinstance(item, dict) and isinstance(item.get("path"), str)):
                    probs.append("recall: an item has no path")
                else:
                    got.append(item["path"])
            for item in files:
                if isinstance(item, dict) and not isinstance(item.get("text"), str):
                    probs.append("recall: a file has no text")
            for item in skipped:
                if isinstance(item, dict) and not isinstance(item.get("reason"), str):
                    probs.append("recall: a skipped item has no reason")
            asked = req.get("paths", [])
            for path in asked:
                if got.count(path) != 1:
                    probs.append("recall: %r appears %d times in files and skipped, not once" % (path, got.count(path)))
            for path in got:
                if path not in asked:
                    probs.append("recall: answered for %r, which was not requested" % path)
            if memory != "on" and files:
                probs.append("recall: files must be empty unless memory is on")
    elif op == "pending":
        if not isinstance(resp.get("proposals"), list) or not isinstance(resp.get("invalid"), list):
            probs.append("pending: proposals and invalid must be lists")
        else:
            for item in resp["proposals"]:
                if not (isinstance(item, dict) and all(isinstance(item.get(k), str) for k in
                        ("id", "file", "target", "proposed-by", "proposed-at", "basis", "body"))):
                    probs.append("pending: a proposal lacks id, file, target, proposed-by, proposed-at, basis or body")
                    break
            for item in resp["invalid"]:
                if not (isinstance(item, dict) and isinstance(item.get("file"), str)
                        and isinstance(item.get("reason"), str)):
                    probs.append("pending: an invalid item lacks file or reason")
                    break
    elif op == "propose":
        if not (isinstance(resp.get("proposal"), str) and isinstance(resp.get("file"), str)):
            probs.append("propose: answer lacks proposal (the new id) and file")
    elif op == "decide":
        if resp.get("status") not in ("accepted", "refused"):
            probs.append("decide: status is not accepted or refused")
        if resp.get("applied") not in ("added", "already", None) or "applied" not in resp:
            probs.append("decide: applied is not added, already or null")
    if op in JOURNAL_OPS:
        journal = resp.get("journal")
        if not (isinstance(journal, list) and all(isinstance(j, str) for j in journal)):
            probs.append("%s: journal is not a list of lines" % op)
    return probs


class Driver:
    """One driver process: one session."""

    def __init__(self, argv, env, label, level_n, timeout=DEFAULT_TIMEOUT):
        self.label = label
        self.level_n = level_n
        self.timeout = timeout
        self.problems = []
        self.next_id = 0
        self.buf = b""
        self.inflight = None
        self.snap = None
        self.closed = False
        self.eof = False
        self.err_tail = b""
        self.q = queue.Queue(maxsize=1000)
        try:
            self.proc = subprocess.Popen(argv, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                         stderr=subprocess.PIPE, env=env, start_new_session=True)
        except OSError as exc:
            raise DriverError("cannot start the driver %r: %s" % (argv, exc))
        self.t_out = threading.Thread(target=self._read_out, daemon=True)
        self.t_err = threading.Thread(target=self._read_err, daemon=True)
        self.t_out.start()
        self.t_err.start()

    def _read_out(self):
        try:
            while True:
                line = self.proc.stdout.readline(MAX_LINE)
                if not line:
                    break
                self.q.put(line)
                if len(line) >= MAX_LINE and not line.endswith(b"\n"):
                    break
        except (OSError, ValueError):
            pass
        finally:
            try:
                self.q.put(None, timeout=5)
            except queue.Full:
                pass

    def _read_err(self):
        try:
            while True:
                chunk = self.proc.stderr.read(4096)
                if not chunk:
                    break
                self.err_tail = (self.err_tail + chunk)[-2000:]
        except (OSError, ValueError):
            pass

    # -- requests
    def queue_request(self, op, **fields):
        self.next_id += 1
        rid = self.next_id if self.next_id % 3 else "r%d" % self.next_id
        req = {"id": rid, "op": op}
        req.update(fields)
        self.buf += (json.dumps(req) + "\n").encode("utf-8")
        self.inflight = req
        return req

    def flush(self):
        data, self.buf = self.buf, b""
        fd = self.proc.stdin.fileno()
        try:
            while data:
                written = os.write(fd, data)
                data = data[written:]
        except OSError as exc:
            raise DriverError("%s: cannot write to the driver: %s%s" % (self.label, exc, self._tail()))

    def _tail(self):
        if not self.err_tail:
            return ""
        return "; stderr ends: " + self.err_tail.decode("utf-8", "replace")[-300:].strip()

    def finish(self, req, timeout=None):
        wait = timeout if timeout is not None else self.timeout
        if self.eof:
            raise DriverError("%s: the driver had already exited" % self.label)
        try:
            raw = self.q.get(timeout=wait)
        except queue.Empty:
            raise DriverError("%s: no answer to %s within %.0f s%s" % (self.label, req["op"], wait, self._tail()))
        if raw is None:
            self.eof = True
            try:
                status = self.proc.wait(timeout=2)
            except subprocess.TimeoutExpired:
                status = "still running"
            raise DriverError("%s: the driver closed its output before answering %s (status %s)%s"
                              % (self.label, req["op"], status, self._tail()))
        text = raw.decode("utf-8", "replace")
        try:
            parsed = json.loads(text)
        except ValueError:
            raise DriverError("%s: answer to %s is not JSON: %r" % (self.label, req["op"], text[:200]))
        if not raw.endswith(b"\n"):
            self.problems.append("an answer was not ended by a line break")
        self.inflight = None
        for problem in validate_response(req, parsed, self.level_n):
            self.problems.append("%s: %s" % (req["op"], problem))
        resp = Resp(parsed) if isinstance(parsed, dict) else Resp()
        resp.raw = text
        return resp

    def request(self, op, timeout=None, **fields):
        req = self.queue_request(op, **fields)
        self.flush()
        return self.finish(req, timeout)

    # -- end
    def kill(self):
        try:
            os.killpg(self.proc.pid, signal.SIGKILL)
        except (OSError, AttributeError):
            pass
        try:
            self.proc.kill()
        except OSError:
            pass

    def close(self):
        if self.closed:
            return
        self.closed = True
        try:
            try:
                self.proc.stdin.close()
            except (OSError, ValueError):
                pass
            deadline = time.time() + 5
            status = None
            while time.time() < deadline:
                status = self.proc.poll()
                if status is not None:
                    break
                time.sleep(0.02)
            if status is None:
                self.problems.append("the driver did not exit within 5 s of the end of input")
                self.kill()
                self.proc.wait()
            elif status != 0:
                self.problems.append("the driver exited with status %s, not 0%s" % (status, self._tail()))
            extra = 0
            while True:
                try:
                    item = self.q.get_nowait()
                except queue.Empty:
                    break
                if item is not None:
                    extra += 1
            if extra:
                self.problems.append("the driver wrote %d line(s) on standard output that no request asked for" % extra)
        finally:
            self.kill()
            self.t_out.join(timeout=2)
            self.t_err.join(timeout=2)
            for pipe in (self.proc.stdout, self.proc.stderr):
                try:
                    pipe.close()
                except (OSError, ValueError):
                    pass


def flush_together(drivers):
    """Release the buffered requests of several drivers at the same moment."""
    barrier = threading.Barrier(len(drivers))
    errors = []

    def go(driver):
        try:
            barrier.wait(10)
            driver.flush()
        except Exception as exc:  # noqa: BLE001
            errors.append(exc)

    threads = [threading.Thread(target=go, args=(d,)) for d in drivers]
    for t in threads:
        t.start()
    for t in threads:
        t.join(15)
    if errors:
        raise DriverError("could not release requests together: %s" % errors[0])


# --------------------------------------------------------------------------
# thou-lint and file-format helpers

def parse_entry(line):
    """Return (entry, problem) for one journal line."""
    if not line.startswith("- "):
        return None, "does not start with '- '"
    parts = line[2:].split(" | ")
    problem = thou_lint.journal_problem(parts)
    if problem:
        return None, problem
    return {"time": parts[0], "path": parts[1], "change": parts[2], "host": parts[3][len("host: "):],
            "authority": parts[4][len("authority: "):]}, None


def prop_text(status="pending", target="topics/travel.md", body="Prefer aisle seats.",
              by="testhost 1.0 (tester)", at="2026-11-12T17:03:01Z", basis='"You asked twice."',
              extra=(), eol="\n", decided_at=None, keys=None):
    if keys is None:
        keys = [("status", status), ("target", target), ("proposed-by", by), ("proposed-at", at), ("basis", basis)]
    lines = ["---"] + ["%s: %s" % kv for kv in keys] + list(extra)
    if decided_at:
        lines.append("decided-at: " + decided_at)
    lines.append("---")
    return (eol.join(lines) + eol + eol + body + eol).encode("utf-8")


def read_front(data):
    """Return (fields, body, problems) of a proposal file's bytes, using thou-lint's parser."""
    return thou_lint.parse_front_matter(data.decode("utf-8", "replace"))


def norm(text):
    return thou_lint.normalize(text)


# --------------------------------------------------------------------------
# per-test context

class Ctx:
    def __init__(self, runner, tid):
        self.runner = runner
        self.tid = tid
        self.level_n = runner.level_n
        self.reader_only = runner.level == "reader"
        self.failures = []
        self.seen = {}
        self.checks = 0
        self.notes = []
        self.sessions = []
        self.canaries = []
        self.root = os.path.realpath(tempfile.mkdtemp(prefix="thou-%s-" % tid.lower()))
        self.home = self._mk("home")
        self.tmp = self._mk("tmp")
        self.xdg = self._mk("xdg")
        self.xdg_dirs = {k: self._mk("xdg/" + v) for k, v in XDG.items()}
        self.outside = self._mk("outside")
        self.store = os.path.join(self.root, "store")
        self.store_roots = [self.store]
        self.pid_n = 0
        self.host_name = (runner.host.info or {}).get("name", "")

    def _mk(self, rel):
        path = os.path.join(self.root, rel)
        os.makedirs(path, exist_ok=True)
        return path

    # -- recording
    def check(self, ok, req, msg):
        self.checks += 1
        if not ok:
            self.fail(req, msg)

    def fail(self, req, msg):
        key = (req, msg)
        if key in self.seen:
            self.seen[key] += 1
            return
        if len(self.failures) >= 60:
            return
        self.seen[key] = 1
        self.failures.append({"req": req, "message": msg})

    def note(self, msg):
        if msg not in self.notes:
            self.notes.append(msg)

    def supports(self, op):
        return OP_LEVEL[op] <= self.level_n

    def canary(self, label):
        value = "CANARY-%s-%s-%s" % (self.tid, label, secrets.token_hex(6))
        self.canaries.append(value)
        return value

    # -- files
    def path(self, rel, store=None):
        return os.path.join(store or self.store, rel)

    def put(self, rel, data, store=None, mode=None):
        path = self.path(rel, store)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "wb") as handle:
            handle.write(b(data))
        if mode is not None:
            os.chmod(path, mode)
        return path

    def get(self, rel, store=None):
        path = self.path(rel, store)
        try:
            if not stat.S_ISREG(os.lstat(path).st_mode):
                return None
            with open(path, "rb") as handle:
                return handle.read()
        except OSError:
            return None

    def link(self, rel, target):
        path = self.path(rel)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        os.symlink(target, path)
        return path

    def clear_store(self):
        if os.path.islink(self.store):
            os.unlink(self.store)
        if not os.path.isdir(self.store):
            os.makedirs(self.store)
            return
        for name in os.listdir(self.store):
            path = os.path.join(self.store, name)
            if os.path.islink(path) or not os.path.isdir(path):
                try:
                    os.chmod(path, 0o600) if not os.path.islink(path) else None
                except OSError:
                    pass
                os.unlink(path)
            else:
                shutil.rmtree(path, onerror=_rm_error)

    def names(self, rel):
        try:
            return sorted(os.listdir(self.path(rel)))
        except OSError:
            return []

    def new_pid(self):
        self.pid_n += 1
        when = datetime.datetime(2026, 11, 12, 17, 0, 0) + datetime.timedelta(seconds=self.pid_n)
        return "%sZ-t%03d" % (when.strftime("%Y%m%dT%H%M%S"), self.pid_n)

    def add_proposal(self, pid=None, **kw):
        pid = pid or self.new_pid()
        self.put("proposals/%s.md" % pid, prop_text(**kw))
        return pid

    # -- sessions
    def env(self, me_home=True):
        env = {"PATH": os.environ.get("PATH", os.defpath), "HOME": self.home, "TMPDIR": self.tmp}
        env.update({k: v for k, v in self.xdg_dirs.items()})
        if me_home is True:
            env["ME_HOME"] = self.store
        elif me_home:
            env["ME_HOME"] = me_home
        return env

    def snap_all(self):
        return dict((root, snapshot(root)) for root in self.store_roots)

    def session(self, host=None, me_home=True, mount=True, timeout=None):
        host = host or self.runner.host
        snap = self.snap_all() if self.reader_only else None
        driver = Driver(host.argv, self.env(me_home), host.label, self.level_n,
                        timeout or self.runner.timeout)
        driver.snap = snap
        driver.host = host
        self.sessions.append(driver)
        mounted = driver.request("mount") if mount else None
        return driver, mounted

    def check_unchanged(self, driver, what="the session"):
        if self.reader_only and driver.snap is not None:
            now = self.snap_all()
            diffs = []
            for root in self.store_roots:
                diffs += ["%s (%s)" % (d, os.path.basename(root)) for d in snap_diff(driver.snap[root], now[root])]
            self.check(not diffs, "H0.2", "a Reader host changed the store during %s: %s" % (what, "; ".join(diffs[:6])))

    def mid_edit(self, driver, fn):
        """The runner edits the store while a session is open, as a person would."""
        self.check_unchanged(driver, "the session before the runner's own edit")
        fn()
        if self.reader_only:
            driver.snap = self.snap_all()

    def end(self, driver):
        driver.close()
        for problem in driver.problems:
            self.fail(DRV, "%s: %s" % (driver.label, problem))
        driver.problems = []
        self.check_unchanged(driver, "the session")
        if driver in self.sessions:
            self.sessions.remove(driver)

    # -- expectations
    def expect_ok(self, resp, req, what):
        ok = resp.get("ok") is True
        self.check(ok, req, "%s: expected ok, got error %r (%s)" % (what, resp.get("error"), resp.get("message")))
        return ok

    def expect_err(self, resp, code, req, what):
        good = resp.get("ok") is False and resp.get("error") == code
        got = "ok" if resp.get("ok") is True else repr(resp.get("error"))
        self.check(good, req, "%s: expected error %s, got %s" % (what, code, got))
        return good

    def expect_mem(self, resp, memory, req, what):
        self.check(resp.get("ok") is True and resp.get("memory") == memory, req,
                   "%s: expected ok with memory %s, got ok=%r memory=%r error=%r"
                   % (what, memory, resp.get("ok"), resp.get("memory"), resp.get("error")))

    def no_canary(self, resps, canaries, req, what):
        for resp in resps:
            for canary in canaries:
                if canary in resp.raw:
                    self.fail(req, "%s: a canary from the store appeared in an answer: %s" % (what, resp.raw[:160].strip()))
                    return

    def expect_same(self, snap, req, what):
        diffs = []
        now = self.snap_all()
        for root in self.store_roots:
            diffs += snap_diff(snap[root], now[root])
        self.check(not diffs, req, "%s: the store changed: %s" % (what, "; ".join(diffs[:6])))

    def run_ops(self, driver, code, req, what, ops):
        """Send each (op, fields) and expect an error code. Ops above the level get unsupported_op."""
        out = []
        for op, fields in ops:
            resp = driver.request(op, **fields)
            out.append(resp)
            if self.supports(op):
                self.expect_err(resp, code, req, "%s: %s" % (what, op))
            else:
                self.expect_err(resp, "unsupported_op", DRV, "%s: %s is above the claimed level" % (what, op))
        return out

    # -- journal and lint
    def journal_check(self, before, resp, what, req="S7.1"):
        """Check that journal.md only grew by the entries the driver reported. Return the entries."""
        after = self.get("journal.md") or b""
        before = before or b""
        if not after.startswith(before):
            self.fail("S7.5", "%s: earlier bytes of journal.md changed" % what)
            return []
        added = after[len(before):]
        if before and not before.endswith(b"\n"):
            if not added.startswith(b"\n"):
                self.fail("S8.1", "%s: journal.md did not end with a line break, and the new entry did not start with one" % what)
            else:
                added = added[1:]
        if added and not added.endswith(b"\n"):
            self.fail("S8.1", "%s: the new journal entry does not end with LF" % what)
        if b"\r" in added:
            self.fail("S8.1", "%s: the new journal entry has a CR; entries end with LF only" % what)
        text = added.decode("utf-8", "replace")
        lines = text.split("\n")[:-1] if text.endswith("\n") else text.split("\n")
        lines = [l for l in lines if l != ""]
        entries = []
        for line in lines:
            entry, problem = parse_entry(line)
            if problem:
                self.fail(req, "%s: journal line %r: %s" % (what, line[:100], problem))
            else:
                entries.append(entry)
                if not time_near_now(entry["time"]):
                    self.fail("S7.1", "%s: journal time %s is not close to the current time" % (what, entry["time"]))
        if resp is not None and isinstance(resp.get("journal"), list):
            self.check(resp["journal"] == lines, DRV,
                       "%s: the journal lines in the answer differ from the lines added to journal.md" % what)
        return entries

    def lint(self, req, what):
        rep = thou_lint.lint(self.store)
        self.check(not rep.errors, req, "%s: thou-lint reports errors: %s" % (
            what, "; ".join("%s: %s" % (e["path"], e["message"]) for e in rep.errors[:4])))
        for w in rep.warnings:
            if "no journal entry records" in w["message"]:
                self.fail("S7.3", "%s: %s: %s" % (what, w["path"], w["message"]))
        return rep

    def entry_for(self, entries, path, change=None, authority=None):
        for e in entries:
            if e["path"] == path and (change is None or e["change"] == change) \
                    and (authority is None or e["authority"] == authority):
                return e
        return None

    # -- end of test
    def copy_search(self):
        """H1.3, H5.2: no canary may sit in the test HOME, TMPDIR or XDG dirs."""
        skip = set(os.path.realpath(r) for r in self.store_roots)
        needles = [(c, c.lower().encode("utf-8")) for c in self.canaries]
        found = []
        for top in (self.home, self.tmp, self.xdg):
            for dirpath, dirnames, filenames in os.walk(top, followlinks=False):
                dirnames[:] = [d for d in dirnames
                               if os.path.realpath(os.path.join(dirpath, d)) not in skip
                               and not os.path.islink(os.path.join(dirpath, d))]
                for name in filenames:
                    path = os.path.join(dirpath, name)
                    try:
                        st = os.lstat(path)
                        if not stat.S_ISREG(st.st_mode) or st.st_size > MAX_FILE_SEARCH:
                            continue
                        with open(path, "rb") as handle:
                            data = handle.read().lower()
                    except OSError:
                        continue
                    for canary, needle in needles:
                        if needle in data:
                            found.append("%s holds %s" % (os.path.relpath(path, self.root), canary))
        for item in found[:5]:
            self.fail("H1.3", "copy of store content outside the store: %s" % item)
        self.checks += 1

    def finish(self):
        for driver in list(self.sessions):
            try:
                self.end(driver)
            except Exception as exc:  # noqa: BLE001
                self.fail(DRV, "could not end a session cleanly: %s" % exc)
        self.copy_search()

    def cleanup(self):
        if self.runner.keep:
            self.notes.append("kept test directory: " + self.root)
        else:
            shutil.rmtree(self.root, onerror=_rm_error)


def _rm_error(func, path, exc_info):
    try:
        os.chmod(os.path.dirname(path), 0o700)
        os.chmod(path, 0o700)
        func(path)
    except OSError:
        pass


# --------------------------------------------------------------------------
# shared test pieces

def write_requests(pid="20261112T170301Z-t001"):
    """Operations that write, with plausible fields. Used to check refusal to write."""
    return [
        ("propose", dict(target="topics/travel.md", body="Prefer aisle seats.", basis="You asked twice.")),
        ("edit", dict(path="me.md", action="append", text="Remember this.")),
        ("edit", dict(path="topics/travel.md", action="replace", old="Existing", new="Changed")),
        ("decide", dict(proposal=pid, decision="accept")),
        ("decide", dict(proposal=pid, decision="refuse")),
        ("revise", dict(proposal=pid, body="Changed body.")),
        ("forget", dict(path="topics/travel.md")),
        ("forget", dict(path="me.md", text="Remember this.")),
    ]


def basic_context(ctx, me="# Me\nI like tea.\n"):
    ctx.put("me.md", me)
    ctx.put("topics/travel.md", "Existing line.\n")


def find_pending(resp, pid):
    for item in resp.get("proposals", []) or []:
        if isinstance(item, dict) and item.get("id") == pid:
            return item
    return None


def file_matches(item_file, rel):
    return isinstance(item_file, str) and os.path.basename(item_file) == os.path.basename(rel)


# --------------------------------------------------------------------------
# T1 Absence

def absent_battery(ctx, label, canaries=()):
    snap = ctx.snap_all()
    d, m = ctx.session()
    resps = [m]
    ctx.expect_mem(m, "absent", "S1.2", "%s: mount" % label)
    ctx.check(m.get("files") == [], "S1.2", "%s: mount returned files for an absent store" % label)
    ctx.check(isinstance(m.get("store"), str) and os.path.realpath(m.get("store", "")) == os.path.realpath(ctx.store),
              "H1.4", "%s: mount names the store %r, expected %r" % (label, m.get("store"), ctx.store))
    r = d.request("list")
    resps.append(r)
    ctx.expect_mem(r, "absent", "S1.2", "%s: list" % label)
    ctx.check(r.get("topics") == [] and r.get("projects") == [] and r.get("watches") is False,
              "S1.2", "%s: list shows names for an absent store" % label)
    r = d.request("recall", paths=["me.md", "topics/x.md"], purpose="task")
    resps.append(r)
    ctx.expect_mem(r, "absent", "S1.2", "%s: recall" % label)
    ctx.check(r.get("files") == [] and len(r.get("skipped", [])) == 2, "S1.2",
              "%s: recall returned content, or did not skip both paths" % label)
    if ctx.supports("pending"):
        r = d.request("pending")
        resps.append(r)
        ctx.expect_mem(r, "absent", "S1.2", "%s: pending" % label)
        ctx.check(r.get("proposals") == [] and r.get("invalid") == [], "S1.2",
                  "%s: pending lists proposals for an absent store" % label)
    resps += ctx.run_ops(d, "absent", "S1.3", label, write_requests() + [
        ("policy", dict(state="off")), ("policy", dict(state="on"))])
    ctx.no_canary(resps, canaries, "S1.2", label)
    ctx.end(d)
    ctx.expect_same(snap, "S1.3", "%s: after the session" % label)


def t1(ctx):
    # (a) no store directory at all
    absent_battery(ctx, "no store directory")
    ctx.check(not os.path.lexists(ctx.store), "S1.3", "no store directory: the host created %s" % ctx.store)
    # (b) the directory exists, with no me.md
    os.makedirs(ctx.store)
    absent_battery(ctx, "empty store directory")
    # (c) the directory exists with other files but no me.md
    canary = ctx.canary("no-me-md")
    ctx.put("topics/x.md", "Topic %s\n" % canary)
    ctx.put("watches.md", "- watch %s\n" % canary)
    ctx.add_proposal(body="Body %s" % canary)
    absent_battery(ctx, "store directory with files but no me.md", [canary])


# --------------------------------------------------------------------------
# T2 Mount

def t2(ctx):
    a, bb = ctx.canary("favorite-colour-me-home"), ctx.canary("favorite-colour-home-dir")
    topic_c, project_c = ctx.canary("topic"), ctx.canary("project")
    ctx.put("me.md", "# Me\nMy favorite colour is %s.\n" % a)
    ctx.put("topics/colours.md", "Topic %s\n" % topic_c)
    ctx.put("projects/p.md", "Project %s\n" % project_c)
    home_store = os.path.join(ctx.home, ".me")
    ctx.put("me.md", "# Other me\nMy favorite colour is %s.\n" % bb, store=home_store)
    ctx.store_roots.append(home_store)

    d, m = ctx.session(me_home=True)
    ctx.expect_mem(m, "on", "H1.1", "ME_HOME set: mount")
    ctx.check(m.get("files") == [{"path": "me.md", "text": ctx.get("me.md").decode()}] or
              (len(m.get("files", [])) == 1 and a in m["files"][0].get("text", "")),
              "H1.1", "ME_HOME set: mount did not return me.md with its canary")
    ctx.check(bb not in m.raw, "S1.1", "ME_HOME set: mount returned the canary of ~/.me, which ME_HOME should override")
    ctx.check(os.path.realpath(m.get("store", "")) == os.path.realpath(ctx.store), "S1.1",
              "ME_HOME set: store is %r, expected %r" % (m.get("store"), ctx.store))
    ctx.check(topic_c not in m.raw and project_c not in m.raw, "H2.1",
              "ME_HOME set: mount returned topic or project content; only me.md is read at session start")
    ctx.end(d)

    d, m = ctx.session(me_home=False)
    ctx.expect_mem(m, "on", "H1.4", "ME_HOME unset: mount")
    ctx.check(len(m.get("files", [])) == 1 and bb in m["files"][0].get("text", ""), "S1.1",
              "ME_HOME unset: mount did not return the me.md under $HOME/.me")
    ctx.check(a not in m.raw, "S1.1", "ME_HOME unset: mount returned the canary of the other store")
    ctx.check(os.path.realpath(m.get("store", "")) == os.path.realpath(home_store), "S1.1",
              "ME_HOME unset: store is %r, expected %r" % (m.get("store"), home_store))
    ctx.end(d)

    # the store root may be a symbolic link (S2.4)
    link = os.path.join(ctx.root, "store-link")
    os.symlink(ctx.store, link)
    d, m = ctx.session(me_home=link)
    ctx.expect_mem(m, "on", "S2.4", "store root is a symbolic link: mount")
    ctx.check(len(m.get("files", [])) == 1 and a in m["files"][0].get("text", ""), "S2.4",
              "store root is a symbolic link: mount did not return me.md")
    ctx.end(d)


# --------------------------------------------------------------------------
# T3 Off

def t3_plant(ctx, canaries):
    ctx.clear_store()
    ctx.put("me.md", "# Me\nSecret %s\n" % canaries["me"])
    ctx.put("topics/travel.md", "Existing line.\nTopic %s\n" % canaries["topic"])
    ctx.put("projects/p.md", "Project %s\n" % canaries["project"])
    ctx.put("watches.md", "- watch %s\n" % canaries["watch"])
    pid = ctx.add_proposal(body="Proposal %s" % canaries["proposal"])
    return pid


def off_battery(ctx, label, canaries, pid, reqname="S5.2"):
    snap = ctx.snap_all()
    cans = list(canaries.values())
    d, m = ctx.session()
    resps = [m]
    ctx.expect_mem(m, "off", reqname, "%s: mount" % label)
    ctx.check(m.get("files") == [], "H1.5", "%s: mount returned files while memory is off" % label)
    r = d.request("list")
    resps.append(r)
    ctx.expect_mem(r, "off", reqname, "%s: list" % label)
    ctx.check(r.get("topics") == [] and r.get("projects") == [] and r.get("watches") is False, "H1.5",
              "%s: list shows names while memory is off" % label)
    paths = ["me.md", "topics/travel.md", "projects/p.md", "watches.md"]
    for purpose in ("task", "briefing", "watches"):
        r = d.request("recall", paths=paths, purpose=purpose)
        resps.append(r)
        ctx.expect_mem(r, "off", reqname, "%s: recall (%s)" % (label, purpose))
        ctx.check(r.get("files") == [] and len(r.get("skipped", [])) == len(paths), "H1.5",
                  "%s: recall (%s) returned content while memory is off" % (label, purpose))
    if ctx.supports("pending"):
        r = d.request("pending")
        resps.append(r)
        ctx.expect_mem(r, "off", reqname, "%s: pending" % label)
        ctx.check(r.get("proposals") == [] and r.get("invalid") == [], "H1.5",
                  "%s: pending lists proposals while memory is off" % label)
    resps += ctx.run_ops(d, "memory_off", "H1.5", label, write_requests(pid))
    ctx.no_canary(resps, cans, "H1.5", label)
    ctx.end(d)
    ctx.expect_same(snap, "H1.5", "%s: after the session" % label)


def t3(ctx):
    cn = dict((k, ctx.canary(k)) for k in ("me", "topic", "project", "watch", "proposal"))
    on_file = os.path.join(ctx.outside, "on.json")
    with open(on_file, "w") as handle:
        handle.write('{"state":"on"}')
    variants = [
        ("state off", "S5.2", lambda: ctx.put("policy.json", '{"state": "off"}')),
        ("invalid JSON", "S5.2", lambda: ctx.put("policy.json", '{"state": "on"')),
        ('"ON" in capitals', "S5.2", lambda: ctx.put("policy.json", '{"state": "ON"}')),
        ("empty object", "S5.2", lambda: ctx.put("policy.json", "{}")),
        ("empty file", "S5.2", lambda: ctx.put("policy.json", "")),
        ("state twice", "S5.2", lambda: ctx.put("policy.json", '{"state": "on", "state": "off"}')),
        ("symbolic link to a file that says on", "S2.4", lambda: ctx.link("policy.json", on_file)),
        ("duplicate member at depth", "S5.2", lambda: ctx.put("policy.json", '{"state": "on", "x": {"a": 1, "a": 2}}')),
        ("not an object (array)", "S5.2", lambda: ctx.put("policy.json", '["on"]')),
        ("not an object (string)", "S5.2", lambda: ctx.put("policy.json", '"on"')),
        ("state is true", "S5.2", lambda: ctx.put("policy.json", '{"state": true}')),
        ("state has a trailing space", "S5.2", lambda: ctx.put("policy.json", '{"state": "on "}')),
        ("policy.json is a directory", "S5.2", lambda: os.makedirs(ctx.path("policy.json"))),
    ]
    if hasattr(os, "geteuid") and os.geteuid() != 0:
        variants.append(("policy.json cannot be read", "S5.2",
                         lambda: ctx.put("policy.json", '{"state": "on"}', mode=0o000)))
    for label, req, setup in variants:
        pid = t3_plant(ctx, cn)
        setup()
        off_battery(ctx, label, cn, pid, req)
        p = ctx.path("policy.json")
        if os.path.isfile(p) and not os.path.islink(p):
            os.chmod(p, 0o600)
    ctx.check(slurp(on_file) == '{"state":"on"}', "S2.4", "the file behind the policy.json symbolic link was changed")

    # off even when me.md is missing (H1.5, DRIVER.md)
    t3_plant(ctx, cn)
    os.unlink(ctx.path("me.md"))
    ctx.put("policy.json", '{"state": "off"}')
    d, m = ctx.session()
    ctx.expect_mem(m, "off", "H1.5", "policy off and no me.md: mount")
    ctx.end(d)

    # an unknown member does not turn memory off (S5.3)
    pid = t3_plant(ctx, cn)
    ctx.put("policy.json", '{"state": "on", "note": "x"}')
    d, m = ctx.session()
    ctx.expect_mem(m, "on", "S5.3", 'policy {"state": "on", "note": "x"}: mount')
    ctx.check(cn["me"] in m.raw, "S5.3", "unknown member: me.md was not returned")
    ctx.end(d)

    # off in the middle of a session: the person edits policy.json in a text editor
    pid = t3_plant(ctx, cn)
    d, m = ctx.session()
    ctx.expect_mem(m, "on", "S5.1", "mid-session (editor): mount")
    r = d.request("recall", paths=["topics/travel.md"])
    ctx.check(r.get("memory") == "on" and cn["topic"] in r.raw, "H2.1", "mid-session (editor): control recall did not return the topic")
    ctx.mid_edit(d, lambda: ctx.put("policy.json", '{"state":"off"}'))
    r = d.request("recall", paths=["topics/travel.md"])
    ctx.expect_mem(r, "off", "H1.6", "mid-session (editor): recall after off")
    ctx.check(r.get("files") == [], "H1.6", "mid-session (editor): recall still returned content after memory went off")
    ctx.no_canary([r], list(cn.values()), "H1.6", "mid-session (editor): recall after off")
    r = d.request("list")
    ctx.expect_mem(r, "off", "H1.6", "mid-session (editor): list after off")
    if ctx.supports("propose"):
        r = d.request("propose", target="topics/travel.md", body="Prefer aisle seats.", basis="Asked twice.")
        ctx.expect_err(r, "memory_off", "H1.6", "mid-session (editor): propose after off")
    ctx.mid_edit(d, lambda: ctx.put("policy.json", '{"state":"on"}'))
    r = d.request("recall", paths=["topics/travel.md"])
    ctx.check(r.get("memory") == "on" and cn["topic"] in r.raw, "H1.6",
              "mid-session (editor): recall after turning memory back on did not return the topic")
    ctx.end(d)

    # the same, through the policy operation
    if ctx.supports("policy"):
        t3_plant(ctx, cn)
        d, m = ctx.session()
        r = d.request("recall", paths=["topics/travel.md"])
        ctx.check(r.get("memory") == "on" and cn["topic"] in r.raw, "H2.1", "mid-session (policy op): control recall did not return the topic")
        r = d.request("policy", state="off")
        ctx.expect_mem(r, "off", "S5.6", "mid-session (policy op): policy off")
        r = d.request("recall", paths=["topics/travel.md", "me.md"])
        ctx.expect_mem(r, "off", "H1.6", "mid-session (policy op): recall after off")
        ctx.check(r.get("files") == [], "H1.6", "mid-session (policy op): recall returned content after memory went off")
        ctx.no_canary([r], list(cn.values()), "H1.6", "mid-session (policy op): recall after off")
        ctx.end(d)
        d2, m2 = ctx.session()
        ctx.expect_mem(m2, "off", "H5.1", "after policy off: mount in a new session")
        ctx.no_canary([m2], list(cn.values()), "H5.1", "after policy off: new session")
        ctx.end(d2)


# --------------------------------------------------------------------------
# T5 Discard

def t5(ctx):
    c = ctx.canary("durable")
    basic_context(ctx, "# Me\nDurable %s\n" % c)
    ctx.put("topics/travel.md", "Existing line %s\n" % c)
    ctx.put("watches.md", "- w\n")
    pid = ctx.add_proposal(body="Pending thing")

    def observe():
        d, m = ctx.session()
        r = d.request("list")
        rec = d.request("recall", paths=["topics/travel.md"])
        out = {"mount": (m.get("memory"), m.get("files")), "list": (r.get("topics"), r.get("projects"), r.get("watches")),
               "recall": (rec.get("files"), rec.get("skipped"))}
        if ctx.supports("pending"):
            p = d.request("pending")
            out["pending"] = (p.get("proposals"), p.get("invalid"))
        ctx.end(d)
        return out

    first = observe()
    second = observe()
    ctx.check(first == second, "H1.2", "two sessions with nothing between them saw different durable context")
    for sub in (ctx.home, ctx.tmp, ctx.xdg):
        for name in os.listdir(sub):
            path = os.path.join(sub, name)
            if os.path.isdir(path) and not os.path.islink(path):
                shutil.rmtree(path, onerror=_rm_error)
            else:
                os.unlink(path)
    for sub in ctx.xdg_dirs.values():
        os.makedirs(sub, exist_ok=True)
    third = observe()
    ctx.check(first == third, "H1.2", "after the host's own state was deleted, a new session saw different durable context")


# --------------------------------------------------------------------------
# T6 Traversal

def t6(ctx):
    out_c, store_c, hidden_c, me2_c = (ctx.canary(k) for k in ("outside", "store", "hidden", "outside-me"))
    secret = os.path.join(ctx.outside, "secret.md")
    with open(secret, "w") as handle:
        handle.write("Outside %s\n" % out_c)
    other_dir = os.path.join(ctx.outside, "dir")
    os.makedirs(other_dir)
    with open(os.path.join(other_dir, "secret.md"), "w") as handle:
        handle.write("Outside dir %s\n" % out_c)
    ctx.put("me.md", "# Me\nStore %s\n" % store_c)
    ctx.put("topics/travel.md", "Existing line.\n")
    ctx.put("topics/.hidden.md", "Hidden %s\n" % hidden_c)
    ctx.put("topics/bin.md", b"\xff\xfe not utf-8 \x80")
    ctx.link("topics/link.md", secret)
    ctx.link("topics/rel.md", os.path.relpath(secret, os.path.dirname(ctx.path("topics/rel.md"))))
    ctx.link("topics/dirlink", other_dir)
    cans = [out_c, hidden_c]
    snap = ctx.snap_all()
    d, m = ctx.session()
    resps = [m]
    bad = ["../outside/secret.md", "topics/../../outside/secret.md", secret, "topics/link.md",
           "topics/rel.md", "topics/dirlink/secret.md", "topics/.hidden.md", "/etc/passwd",
           "topics/../me.md", "topics/missing.md", "topics/bin.md", "proposals/x.md", "journal.md"]
    r = d.request("recall", paths=bad + ["topics/travel.md"], purpose="task")
    resps.append(r)
    ctx.expect_ok(r, "S2.7", "recall of unsafe paths")
    skipped = [s.get("path") for s in r.get("skipped", []) if isinstance(s, dict)]
    files = [f.get("path") for f in r.get("files", []) if isinstance(f, dict)]
    for path in bad:
        ctx.check(path in skipped and path not in files, "S2.7" if ".." in path or path.startswith("/") else "S2.4",
                  "recall of %r was not skipped" % path)
    ctx.check("topics/travel.md" in files, "S2.1", "control: topics/travel.md was not returned")
    ctx.no_canary(resps, cans, "S2.4", "recall of unsafe paths")
    ls = d.request("list")
    resps.append(ls)
    ctx.check("link.md" not in ls.get("topics", []) and "rel.md" not in ls.get("topics", [])
              and ".hidden.md" not in ls.get("topics", []), "S2.4", "list shows a symbolic link or hidden file")
    ctx.no_canary(resps, cans, "S2.4", "list")
    ctx.end(d)
    ctx.expect_same(snap, "H0.2" if ctx.reader_only else "S2.4", "traversal session")
    # the outside file must be untouched whatever the host did
    ctx.check(slurp(secret) == "Outside %s\n" % out_c, "S2.7", "the file outside the store was changed")

    # me.md is a symbolic link: the store is absent
    ctx.clear_store()
    me2 = os.path.join(ctx.outside, "me2.md")
    with open(me2, "w") as handle:
        handle.write("Linked me %s\n" % me2_c)
    ctx.put("topics/travel.md", "Existing line.\n")
    ctx.link("me.md", me2)
    snap = ctx.snap_all()
    d, m = ctx.session()
    resps = [m]
    ctx.expect_mem(m, "absent", "S2.4", "me.md is a symbolic link: mount")
    ctx.check(m.get("files") == [], "S2.4", "me.md is a symbolic link: mount returned files")
    for r in (d.request("list"), d.request("recall", paths=["me.md", "topics/travel.md"])):
        resps.append(r)
        ctx.expect_mem(r, "absent", "S2.4", "me.md is a symbolic link")
    if ctx.supports("propose"):
        ctx.expect_err(d.request("propose", target="me.md", body="Prefer aisle seats.", basis="b"),
                       "absent", "S2.4", "me.md is a symbolic link: propose")
    ctx.no_canary(resps, [me2_c], "S2.4", "me.md is a symbolic link")
    ctx.end(d)
    ctx.expect_same(snap, "S2.4", "me.md is a symbolic link")
    ctx.check(slurp(me2) == "Linked me %s\n" % me2_c, "S2.4", "the file behind the me.md link was changed")


# --------------------------------------------------------------------------
# T7 Watches

def t7(ctx):
    w, mc = ctx.canary("watch"), ctx.canary("me")
    ctx.put("me.md", "# Me\nAims %s\n" % mc)
    ctx.put("topics/travel.md", "Existing line.\n")
    ctx.put("watches.md", "- Tell me when the migration moves %s\n" % w)
    d, m = ctx.session()
    resps = [m]
    ctx.check(mc in m.raw, "H2.1", "control: mount did not return me.md")
    ls = d.request("list")
    resps.append(ls)
    ctx.check(ls.get("watches") is True, "S4.3", "list does not say that watches.md exists")
    for kwargs in ({"purpose": "task"}, {}):
        r = d.request("recall", paths=["me.md", "topics/travel.md", "watches.md"], **kwargs)
        resps.append(r)
        ctx.check(any(f.get("path") == "watches.md" for f in r.get("skipped", []) if isinstance(f, dict)), "S4.3",
                  "recall with purpose %r did not skip watches.md" % kwargs.get("purpose", "(none)"))
    ctx.no_canary(resps, [w], "S4.3", "a session that is not a briefing")
    for purpose in ("watches", "briefing"):
        r = d.request("recall", paths=["watches.md"], purpose=purpose)
        ctx.check(w in r.raw and any(f.get("path") == "watches.md" for f in r.get("files", [])), "S4.3",
                  "control: recall with purpose %s did not return watches.md" % purpose)
    ctx.end(d)


# --------------------------------------------------------------------------
# T8 Proposal

def t8(ctx):
    basic_context(ctx)
    ctx.put("watches.md", "- a watch\n")
    ctx.put("journal.md", "# Journal\n")
    body = "Prefer aisle seats when booking flights."
    basis = 'You asked for aisle seats on two bookings this week, "twice".'
    snap = ctx.snap_all()
    d, m = ctx.session()
    r = d.request("propose", target="topics/travel.md", body=body, basis=basis, agent="trip-helper")
    if not ctx.expect_ok(r, "H3.2", "propose"):
        ctx.end(d)
        return
    after = ctx.snap_all()
    diffs = snap_diff(snap[ctx.store], after[ctx.store])
    added = [x for x in diffs if x.startswith("added")]
    new_files = [x for x in added if x != "added proposals"]
    ctx.check(len(new_files) == 1 and new_files[0].startswith("added proposals/"), "H3.2",
              "propose should create exactly one new file in proposals/; changes: %s" % "; ".join(diffs))
    ctx.check(all(x.startswith("added proposals") for x in diffs), "H3.1",
              "propose changed something other than proposals/: %s" % "; ".join(diffs))
    name = r.get("file", "").split("/")[-1]
    ctx.check(r.get("file") == "proposals/" + name and name == r.get("proposal", "") + ".md", DRV,
              "propose answered file %r and proposal %r; expected proposals/<id>.md" % (r.get("file"), r.get("proposal")))
    ctx.check(thou_lint.PROPOSAL_NAME_RE.fullmatch(name) is not None, "S6.1", "the proposal file name %r breaks S6.1" % name)
    data = ctx.get("proposals/" + name)
    if data is not None:
        fields, pbody, problems = read_front(data)
        ctx.check(not problems, "S6.4", "the new proposal's front matter: %s" % "; ".join(problems))
        ctx.check(fields.get("status") == "pending", "S6.9", "the new proposal's status is %r, not pending" % fields.get("status"))
        ctx.check(fields.get("target") == "topics/travel.md", "S6.3", "the new proposal's target is %r" % fields.get("target"))
        ctx.check("trip-helper" in fields.get("proposed-by", ""), "H4.3", "proposed-by %r does not name the agent" % fields.get("proposed-by"))
        ctx.check(fields.get("basis") == basis, "S6.4", "the new proposal's basis is %r" % fields.get("basis"))
        ctx.check(time_near_now(fields.get("proposed-at", "")), "S6.3", "proposed-at %r is not a time close to now" % fields.get("proposed-at"))
        if pbody is not None:
            text = pbody[1:] if pbody.startswith("\n") else pbody
            ctx.check(text.rstrip("\r\n") == body, "S6.6", "the new proposal's body is %r, expected %r" % (text, body))
        path = ctx.path("proposals/" + name)
        if hasattr(os, "geteuid") and os.name == "posix":
            mode = stat.S_IMODE(os.lstat(path).st_mode)
            if mode & 0o077:
                ctx.note("S2.5 (SHOULD): the proposal file has mode %o, not 0600" % mode)
    ctx.lint("S6.14", "after propose")
    # no other file changed: me.md, topics, watches and journal are compared by the snapshot above
    if ctx.supports("pending"):
        p = d.request("pending")
        item = find_pending(p, r.get("proposal"))
        ctx.check(item is not None, "H3.2", "pending does not list the new proposal")
        if item:
            ctx.check(item.get("body", "").rstrip("\r\n") == body, "S6.6", "pending shows a different body")
            ctx.check(item.get("target") == "topics/travel.md", "S6.4", "pending shows a different target")
            ctx.check(file_matches(item.get("file"), name), DRV, "pending names file %r, not the new proposal" % item.get("file"))
    # three proposals in a row get three different files (S6.2)
    before = set(ctx.names("proposals"))
    ids = []
    for i in range(3):
        rr = d.request("propose", target="topics/travel.md", body="Distinct preference number %d." % i, basis="b")
        ctx.expect_ok(rr, "S6.2", "propose in a quick series")
        ids.append(rr.get("file"))
    ctx.check(len(set(ids)) == 3 and len(set(ctx.names("proposals")) - before) == 3, "S6.2",
              "three quick proposals did not make three different files")
    # inputs the host must refuse, with nothing written
    snap2 = ctx.snap_all()
    for label, fields, code in [
            ("target watches.md", dict(target="watches.md", body="x y", basis="b"), "bad_target"),
            ("target outside the store", dict(target="../x.md", body="x y", basis="b"), "bad_target"),
            ("target journal.md", dict(target="journal.md", body="x y", basis="b"), "bad_target"),
            ("target with a bad name", dict(target="topics/Bad Name.md", body="x y", basis="b"), "bad_target"),
            ("blank body", dict(target="me.md", body=" \n\t ", basis="b"), "empty_body")]:
        rr = d.request("propose", **fields)
        ctx.expect_err(rr, code, "S4.2" if "watches" in label else "S6.6", "propose with %s" % label)
    rr = d.request("propose", target="me.md", basis="b")
    ctx.expect_err(rr, "bad_request", DRV, "propose with no body")
    ctx.expect_same(snap2, "S6.6", "rejected proposals")
    ctx.end(d)


# --------------------------------------------------------------------------
# T9 Second host

def set_status_line(ctx, name, new_line):
    path = ctx.path("proposals/" + name)
    with open(path, "rb") as handle:
        data = handle.read()
    new, n = re.subn(rb"(?m)^status:[ \t]*pending[ \t]*(\r?)$", lambda m: new_line + m.group(1), data, count=1)
    if n != 1:
        ctx.fail("S6.4", "could not find a `status: pending` line in %s to edit as a person would" % name)
        return False
    with open(path, "wb") as handle:
        handle.write(new)
    return True


def t9(ctx):
    host_a, host_b = ctx.runner.host, ctx.runner.second or ctx.runner.host
    if ctx.runner.second is None:
        ctx.note("No --second-host: host B is the same host as A, so this run does not show behavior across two different hosts (H3.2, H1.4).")
    elif OP_LEVEL["propose"] > LEVELS.index(host_b.info["level"]):
        ctx.note("The second host does not support propose; this test used the first host twice.")
        host_b = host_a
    c1, c2 = ctx.canary("one"), ctx.canary("two")
    mc = ctx.canary("me")
    ctx.put("me.md", "# Me\nShared %s\n" % mc)
    body1 = "Prefer the café %s near the gate." % c1
    body2 = "Never book a window seat on night flights %s." % c2
    a, ma = ctx.session(host=host_a)
    bsess, mb = ctx.session(host=host_b)
    ctx.check(ma.get("files") == mb.get("files") and mc in ma.raw, "H1.4", "the two hosts mounted different context")
    r1 = a.request("propose", target="topics/a.md", body=body1, basis="One.", agent="agent-a")
    r2 = a.request("propose", target="topics/b.md", body=body2, basis="Two.", agent="agent-a")
    if not (ctx.expect_ok(r1, "H3.2", "host A propose 1") and ctx.expect_ok(r2, "H3.2", "host A propose 2")):
        ctx.end(a)
        ctx.end(bsess)
        return
    pb = bsess.request("pending")
    for r, body in ((r1, body1), (r2, body2)):
        item = find_pending(pb, r["proposal"])
        ctx.check(item is not None, "H3.2", "host B's pending does not list host A's proposal %s" % r["proposal"])
        if item:
            ctx.check(item.get("body", "").rstrip("\r\n") == body.rstrip("\r\n"), "S6.6",
                      "host B reads a different body for proposal %s" % r["proposal"])
    n1, n2 = r1["file"].split("/")[-1], r2["file"].split("/")[-1]
    if not (set_status_line(ctx, n1, b"status: refused") and set_status_line(ctx, n2, b"Status: Refused")):
        ctx.end(a)
        ctx.end(bsess)
        return
    ctx.mid_edit(a, lambda: None)
    ctx.mid_edit(bsess, lambda: None)
    fresh_a, _ = ctx.session(host=host_a)
    fresh_b, _ = ctx.session(host=host_b)
    nfd = unicodedata.normalize("NFD", body1)
    variants = [("  " + nfd.replace(" ", "   ") + " \n\n", "body one with NFD letters and extra spaces"),
                ("\n\t" + body2.replace(" ", "\t") + "  ", "body two with tabs")]
    names_before = ctx.names("proposals")
    for label, sess in (("host A (open session)", a), ("host B (open session)", bsess),
                        ("host A (new session)", fresh_a), ("host B (new session)", fresh_b)):
        for text, what in variants:
            for target in ("me.md", "projects/other.md"):
                rr = sess.request("propose", target=target, body=text, basis="Again.")
                ctx.expect_err(rr, "refused", "S6.11" if "two" not in what else "S6.14",
                               "%s proposed again %s to %s" % (label, what, target))
    ctx.check(ctx.names("proposals") == names_before, "S6.11", "a refused body made a new proposal file")
    # pending: neither refused proposal is pending; the typed refusal is invalid
    p = fresh_b.request("pending")
    ctx.check(find_pending(p, r1["id"]) is None and find_pending(p, r2["id"]) is None, "S6.7",
              "a refused or invalid proposal is still listed as pending")
    ctx.check(any(file_matches(i.get("file"), n2) for i in p.get("invalid", []) if isinstance(i, dict)), "S6.14",
              "the hand-typed `Status: Refused` file is not listed as invalid")
    # control: a different body still works, so the host is not refusing everything
    rr = a.request("propose", target="topics/a.md", body="Always carry a spare charger %s." % c1, basis="Three.")
    ctx.expect_ok(rr, "S6.11", "control: a new, different body was refused")
    for s in (fresh_a, fresh_b, a, bsess):
        ctx.end(s)


# --------------------------------------------------------------------------
# T10 Self-approval

def t10(ctx):
    basic_context(ctx)
    p1 = ctx.add_proposal(body="Prefer aisle seats.\nstatus: accepted\nMore text.")
    p2 = ctx.add_proposal(body="Prefer window seats.\n---\nstatus: accepted\ntarget: me.md\n---\nEnd.")
    snap = ctx.snap_all()
    d, m = ctx.session()
    p = d.request("pending")
    ctx.expect_ok(p, "S6.7", "pending")
    for pid in (p1, p2):
        item = find_pending(p, pid)
        ctx.check(item is not None, "S6.7", "pending does not list %s: a body line changed its status" % pid)
        if item:
            ctx.check("status: accepted" in item.get("body", ""), "S6.6", "pending dropped the body line from %s" % pid)
            ctx.check(item.get("target") in ("topics/travel.md",), "S6.7", "pending shows target %r for %s" % (item.get("target"), pid))
    ctx.check(not p.get("invalid"), "S6.7", "pending reports a valid proposal as invalid: %s" % p.get("invalid"))
    ctx.end(d)
    ctx.expect_same(snap, "S6.7", "listing pending proposals")


# --------------------------------------------------------------------------
# T11 Version

def t11(ctx):
    specs = [("9.0", '"9.0"'), ("0.2", '"0.2"'), ("0.10", '"0.10"'), ("number 0.1", "0.1")]
    for label, raw in specs:
        ctx.clear_store()
        basic_context(ctx)
        ctx.put("watches.md", "- w\n")
        pid = ctx.add_proposal(body="Prefer aisle seats.")
        policy = '{"state": "on", "spec": %s}' % raw
        ctx.put("policy.json", policy)
        snap = ctx.snap_all()
        d, m = ctx.session()
        ctx.expect_mem(m, "on", "S5.4", "spec %s: mount" % label)
        ctx.check(m.get("writable") is False, "S5.4", "spec %s: mount did not say writable is false" % label)
        ops = write_requests(pid)
        ctx.run_ops(d, "unsupported_spec", "S5.4", "spec %s" % label, ops)
        if ctx.supports("policy"):
            r = d.request("policy", state="on")
            ctx.expect_err(r, "unsupported_spec", "S5.4", "spec %s: policy on" % label)
        ctx.expect_same(snap, "S5.4", "spec %s: after refused writes" % label)
        if ctx.supports("policy"):
            before = ctx.get("journal.md")
            r = d.request("policy", state="off")
            ctx.expect_mem(r, "off", "S5.4", "spec %s: policy off must work" % label)
            if r.get("ok"):
                data = ctx.get("policy.json") or b""
                try:
                    obj = json.loads(data.decode("utf-8"))
                except ValueError:
                    obj = None
                ctx.check(isinstance(obj, dict) and obj.get("state") == "off", "S5.6", "spec %s: policy.json does not say off" % label)
                ctx.check(isinstance(obj, dict) and json.dumps(obj.get("spec")) == raw, "S5.6",
                          "spec %s: turning memory off did not keep the spec member" % label)
                ents = ctx.journal_check(before, r, "spec %s: policy off" % label)
                ctx.check(ctx.entry_for(ents, "policy.json") is not None, "S7.3", "spec %s: no journal entry for the policy change" % label)
        ctx.end(d)


# --------------------------------------------------------------------------
# T12 Direct edit

def t12(ctx):
    ctx.clear_store()
    mc = ctx.canary("me")
    ctx.put("me.md", "# Me\nLine one %s\n" % mc)
    ctx.put("topics/travel.md", "Existing line.\n")
    host_name = ctx.host_name
    d, m = ctx.session()
    before = ctx.get("journal.md")
    r = d.request("edit", path="me.md", action="append", text="I prefer aisle seats.", agent="trip-helper")
    if ctx.expect_ok(r, "H3.7", "edit append"):
        ctx.check(ctx.get("me.md") == b"# Me\nLine one %s\nI prefer aisle seats.\n" % mc.encode(), "H3.7",
                  "edit append: me.md is not the old text plus the new line")
        ents = ctx.journal_check(before, r, "edit append")
        e = ctx.entry_for(ents, "me.md", authority="person direct")
        ctx.check(e is not None and len(ents) == 1, "H3.7", "edit append: expected one journal entry for me.md with authority person direct, got %d" % len(ents))
        if e:
            ctx.check(e["host"].startswith(host_name), "H4.1", "journal host %r does not start with the host name %r" % (e["host"], host_name))
            ctx.check("trip-helper" in e["host"], "H4.3", "journal host %r does not name the agent" % e["host"])
    # create a new topic by append, and a watch by direct edit
    before = ctx.get("journal.md")
    r = d.request("edit", path="topics/newone.md", action="append", text="Fresh topic.")
    if ctx.expect_ok(r, "H3.7", "edit append to a new topic"):
        ctx.check(ctx.get("topics/newone.md") == b"Fresh topic.\n", "S6.8", "the new topic is not the text and one LF")
        ents = ctx.journal_check(before, r, "edit append to a new topic")
        ctx.check(ctx.entry_for(ents, "topics/newone.md", authority="person direct") is not None, "S7.3", "no journal entry for the new topic")
    before = ctx.get("journal.md")
    r = d.request("edit", path="watches.md", action="append", text="- Tell me when it moves")
    if ctx.expect_ok(r, "H3.7", "edit append to watches.md"):
        ents = ctx.journal_check(before, r, "edit append to watches.md")
        ctx.check(ctx.entry_for(ents, "watches.md", authority="person direct") is not None, "S7.3", "no journal entry for watches.md")
    # replace
    before = ctx.get("journal.md")
    r = d.request("edit", path="topics/travel.md", action="replace", old="Existing line.", new="Changed line.")
    if ctx.expect_ok(r, "S2.6", "edit replace"):
        ctx.check(ctx.get("topics/travel.md") == b"Changed line.\n", "S2.6", "edit replace: wrong result")
        ents = ctx.journal_check(before, r, "edit replace")
        ctx.check(ctx.entry_for(ents, "topics/travel.md", authority="person direct") is not None, "S7.3", "no journal entry for the replace")
    # refusals leave the store alone
    ctx.put("topics/dup.md", "same\nsame\n")
    snap = ctx.snap_all()
    for label, fields, code in [
            ("no match", dict(path="topics/travel.md", action="replace", old="nothing here", new="x"), "no_match"),
            ("ambiguous", dict(path="topics/dup.md", action="replace", old="same", new="x"), "ambiguous"),
            ("missing file", dict(path="topics/missing.md", action="replace", old="a", new="b"), "not_found"),
            ("path outside the store", dict(path="../x.md", action="append", text="x"), "bad_path"),
            ("path journal.md", dict(path="journal.md", action="append", text="x"), "bad_path"),
            ("path policy.json", dict(path="policy.json", action="append", text="x"), "bad_path"),
            ("a proposal path", dict(path="proposals/x.md", action="append", text="x"), "bad_path"),
            ("a bad topic name", dict(path="topics/Bad.md", action="append", text="x"), "bad_path")]:
        ctx.expect_err(d.request("edit", **fields), code, "S2.7" if code == "bad_path" else "S2.6", "edit with %s" % label)
    ctx.expect_same(snap, "S2.6", "refused edits")
    ctx.lint("S7.1", "after edits")
    ctx.end(d)

    # policy off and on, with journal entries, also while memory is off
    ctx.clear_store()
    ctx.put("me.md", "# Me\nSecret %s\n" % mc)
    d, m = ctx.session()
    before = ctx.get("journal.md")
    snap = ctx.snap_all()
    r = d.request("policy", state="off", agent="trip-helper")
    if ctx.expect_mem(r, "off", "S5.6", "policy off") or r.get("ok"):
        data = ctx.get("policy.json") or b""
        try:
            obj = json.loads(data.decode("utf-8"))
        except ValueError:
            obj = None
        ctx.check(isinstance(obj, dict) and obj.get("state") == "off", "S5.6", "policy.json does not say state off after policy off")
        ents = ctx.journal_check(before, r, "policy off")
        ctx.check(ctx.entry_for(ents, "policy.json", authority="person direct") is not None and len(ents) == 1, "S7.3",
                  "policy off: expected one journal entry for policy.json with authority person direct")
        diffs = [x.split(" ", 1)[1] for x in snap_diff(snap[ctx.store], ctx.snap_all()[ctx.store])]
        ctx.check(set(diffs) <= {"policy.json", "journal.md"}, "S5.6", "policy off changed other files: %s" % ", ".join(diffs))
        rc = d.request("recall", paths=["me.md"])
        ctx.expect_mem(rc, "off", "H5.1", "recall after policy off")
        ctx.no_canary([rc], [mc], "H5.1", "recall after policy off")
        before = ctx.get("journal.md")
        snap = ctx.snap_all()
        r = d.request("policy", state="on")
        ctx.expect_mem(r, "on", "S5.6", "policy on while memory is off")
        data = ctx.get("policy.json") or b""
        try:
            obj = json.loads(data.decode("utf-8"))
        except ValueError:
            obj = None
        ctx.check(isinstance(obj, dict) and obj.get("state") == "on", "S5.6", "policy.json does not say state on after policy on")
        ents = ctx.journal_check(before, r, "policy on")
        ctx.check(ctx.entry_for(ents, "policy.json", authority="person direct") is not None and len(ents) == 1, "S7.3",
                  "policy on: expected one journal entry for policy.json")
        diffs = [x.split(" ", 1)[1] for x in snap_diff(snap[ctx.store], ctx.snap_all()[ctx.store])]
        ctx.check(set(diffs) <= {"policy.json", "journal.md"}, "S5.6", "policy on changed other files: %s" % ", ".join(diffs))
        rc = d.request("recall", paths=["me.md"])
        ctx.check(rc.get("memory") == "on" and mc in rc.raw, "H5.1", "recall after policy on did not return me.md")
    ctx.end(d)

    # S5.6: only `state` changes; other members stay; an invalid file is replaced
    ctx.clear_store()
    ctx.put("me.md", "# Me\n")
    ctx.put("policy.json", '{"note": "x", "state": "on", "spec": "0.1", "extra": {"a": [1, 2]}}')
    d, m = ctx.session()
    r = d.request("policy", state="off")
    ctx.expect_ok(r, "S5.6", "policy off with extra members")
    try:
        obj = json.loads((ctx.get("policy.json") or b"").decode("utf-8"))
    except ValueError:
        obj = None
    ctx.check(isinstance(obj, dict) and obj.get("state") == "off" and obj.get("note") == "x"
              and obj.get("spec") == "0.1" and obj.get("extra") == {"a": [1, 2]}, "S5.6",
              "policy off did not keep the other members of policy.json: %r" % obj)
    ctx.put("policy.json", "this is not json")
    r = d.request("policy", state="on")
    ctx.expect_mem(r, "on", "S5.6", "policy on over an invalid policy.json")
    try:
        obj = json.loads((ctx.get("policy.json") or b"").decode("utf-8"))
    except ValueError:
        obj = None
    ctx.check(isinstance(obj, dict) and obj.get("state") == "on", "S5.6", "an invalid policy.json was not replaced by a valid one")
    ctx.end(d)
    # no policy.json at all: policy off creates it, and journals it
    ctx.clear_store()
    ctx.put("me.md", "# Me\n")
    d, m = ctx.session()
    before = ctx.get("journal.md")
    r = d.request("policy", state="off")
    ctx.expect_mem(r, "off", "S5.6", "policy off with no policy.json")
    ents = ctx.journal_check(before, r, "policy off with no policy.json")
    ctx.check(ctx.entry_for(ents, "policy.json") is not None, "S7.3", "creating policy.json was not journaled")
    ctx.end(d)


# --------------------------------------------------------------------------
# T13 Receipt

def t13(ctx):
    ctx.clear_store()
    header = ("# Journal\n\nNotes are ignored.\n"
              "- 2026-11-10T09:00:05Z | me.md | added an aim | host: oldhost 1.0 | authority: person direct\n"
              "Free text line that is not an entry.\n")
    ctx.put("me.md", "# Me\n")
    ctx.put("topics/travel.md", "Existing line.\n")
    ctx.put("journal.md", header)
    body = "Prefer aisle seats."
    pid = ctx.add_proposal(body=body, basis='"You asked twice."', extra=["x-keep: this"])
    pid2 = ctx.add_proposal(body="Never book red-eyes.", target="topics/other.md")
    d, m = ctx.session()
    jbefore = ctx.get("journal.md")
    pbefore = ctx.get("proposals/%s.md" % pid)
    r = d.request("decide", proposal=pid, decision="accept", agent="trip-helper")
    if ctx.expect_ok(r, "H3.5", "decide accept"):
        ctx.check(r.get("status") == "accepted" and r.get("applied") == "added", DRV, "accept answered status %r applied %r" % (r.get("status"), r.get("applied")))
        ents = ctx.journal_check(jbefore, r, "accept")
        ctx.check(len(ents) == 2, "S7.3", "an acceptance wrote %d journal entries, not 2" % len(ents))
        if len(ents) == 2:
            dec, con = ents
            ctx.check(dec["path"] == "proposals/%s.md" % pid and dec["change"] == "accepted" and dec["authority"] == "person direct",
                      "S7.3", "first entry is not the decision: %r" % (dec,))
            ctx.check(con["path"] == "topics/travel.md" and con["authority"] == "accepted proposal %s" % pid,
                      "S7.3", "second entry is not the content change: %r" % (con,))
            ctx.check(dec["host"] == con["host"] and dec["host"].startswith(ctx.host_name) and "trip-helper" in dec["host"],
                      "H4.3", "host fields differ or lack the host and agent: %r / %r" % (dec["host"], con["host"]))
        ctx.check(ctx.get("topics/travel.md") == b"Existing line.\nPrefer aisle seats.\n", "S6.8", "the target is not the old text plus the body")
        pafter = ctx.get("proposals/%s.md" % pid) or b""
        fields, pbody, problems = read_front(pafter)
        ctx.check(fields.get("status") == "accepted" and not problems, "S8.6", "the proposal's status is %r after accepting" % fields.get("status"))
        ctx.check(time_near_now(fields.get("decided-at", "")), "S8.6", "decided-at %r is missing or not a time" % fields.get("decided-at"))
        ctx.check(b"x-keep: this" in pafter, "S6.5", "the unknown key was lost")
        ctx.check(pbody is not None and pbody.strip() == body, "S6.7", "the proposal body changed")
        ctx.lint("S7.1", "after accept")
    # refuse another
    jbefore = ctx.get("journal.md")
    tbefore = ctx.get("topics/other.md")
    r = d.request("decide", proposal=pid2, decision="refuse")
    if ctx.expect_ok(r, "H3.5", "decide refuse"):
        ctx.check(r.get("status") == "refused" and r.get("applied") is None, DRV, "refuse answered status %r applied %r" % (r.get("status"), r.get("applied")))
        ents = ctx.journal_check(jbefore, r, "refuse")
        ctx.check(len(ents) == 1 and ents[0]["path"] == "proposals/%s.md" % pid2 and ents[0]["change"] == "refused"
                  and ents[0]["authority"] == "person direct", "S7.3", "a refusal needs one decision entry: %r" % ents)
        ctx.check(ctx.get("topics/other.md") == tbefore, "S8.6", "a refusal changed the target")
        f2, _, _ = read_front(ctx.get("proposals/%s.md" % pid2) or b"")
        ctx.check(f2.get("status") == "refused" and time_near_now(f2.get("decided-at", "")), "S8.6", "the refused proposal lacks status refused and decided-at")
        if ctx.supports("pending"):
            p = d.request("pending")
            ctx.check(find_pending(p, pid) is None and find_pending(p, pid2) is None, "S6.9", "decided proposals are still pending")
    # already applied: the body is already at the end of the target
    pid3 = ctx.add_proposal(body="Already there.", target="topics/done.md")
    ctx.put("topics/done.md", "Top.\nAlready there.\n")
    jbefore = ctx.get("journal.md")
    r = d.request("decide", proposal=pid3, decision="accept")
    if ctx.expect_ok(r, "S8.6", "accept a proposal whose body is already applied"):
        ctx.check(r.get("applied") == "already", "S6.8", "applied is %r, expected already" % r.get("applied"))
        ctx.check(ctx.get("topics/done.md") == b"Top.\nAlready there.\n", "S6.8", "the body was added a second time")
        ents = ctx.journal_check(jbefore, r, "accept already applied")
        ctx.check(len(ents) == 2, "S8.6", "an already-applied acceptance still needs both journal entries")
    # the target does not exist: it is created
    pid4 = ctx.add_proposal(body="Brand new.", target="projects/newproj.md")
    r = d.request("decide", proposal=pid4, decision="accept")
    if ctx.expect_ok(r, "S6.8", "accept into a new file"):
        ctx.check(ctx.get("projects/newproj.md") == b"Brand new.\n", "S6.8", "a missing target was not created with the text and one LF")
    # journal that has no final line break, and a CRLF journal (S8.1)
    ctx.put("journal.md", "- 2026-11-10T09:00:05Z | me.md | added an aim | host: oldhost 1.0 | authority: person direct")
    jbefore = ctx.get("journal.md")
    r = d.request("edit", path="me.md", action="append", text="Aim two.")
    if ctx.expect_ok(r, "S8.1", "edit with a journal that has no final line break"):
        ctx.journal_check(jbefore, r, "journal with no final line break")
    ctx.put("journal.md", "# Journal\r\n- 2026-11-10T09:00:05Z | me.md | added an aim | host: oldhost 1.0 | authority: person direct\r\n")
    jbefore = ctx.get("journal.md")
    r = d.request("edit", path="me.md", action="append", text="Aim three.")
    if ctx.expect_ok(r, "S8.1", "edit with a CRLF journal"):
        ctx.journal_check(jbefore, r, "CRLF journal")
    ctx.end(d)


# --------------------------------------------------------------------------
# T14 Delete

def t14(ctx):
    ctx.clear_store()
    f1, f2, f3 = ctx.canary("forget-me"), ctx.canary("forget-topic"), ctx.canary("partial")
    keep = ctx.canary("keep")
    ctx.put("me.md", "# Me\nKeep this %s\nI hate cilantro %s\nOther keep line\nI hate cilantro %s\nPart %s of a line\n" % (keep, f1, f1, f3))
    ctx.put("topics/food.md", "Topic text %s\n" % f2)
    ctx.put("topics/stay.md", "Stays.\n")
    snap_outside = {}
    d, m = ctx.session()
    r = d.request("recall", paths=["me.md", "topics/food.md"])
    ctx.check(f1 in r.raw and f2 in r.raw, "H5.2", "control: recall did not return the content before it was forgotten")
    before = ctx.get("journal.md")
    r = d.request("forget", path="me.md", text="I hate cilantro %s" % f1, agent="trip-helper")
    if ctx.expect_ok(r, "H5.2", "forget text"):
        ctx.check(r.get("removed") == 2, DRV, "forget removed %r places, expected 2" % r.get("removed"))
        ctx.check(ctx.get("me.md") == ("# Me\nKeep this %s\nOther keep line\nPart %s of a line\n" % (keep, f3)).encode(), "H5.2",
                  "me.md is not the old text minus the two forgotten lines")
        ctx.check(bool(r.get("notices")) and all(isinstance(n, str) and n.strip() for n in r.get("notices")), "H5.3",
                  "forget gave no notice about what it cannot delete")
        ents = ctx.journal_check(before, r, "forget text")
        ctx.check(ctx.entry_for(ents, "me.md", authority="person direct") is not None, "S7.3", "forgetting text from me.md was not journaled")
    # text that fills only part of a line is not removed
    snap = ctx.snap_all()
    r = d.request("forget", path="me.md", text="of a line")
    ctx.expect_err(r, "no_match", "H5.2", "forget text that fills only part of a line")
    r = d.request("forget", path="me.md", text="never was here")
    ctx.expect_err(r, "no_match", "H5.2", "forget text that is not there")
    r = d.request("forget", path="topics/missing.md")
    ctx.expect_err(r, "not_found", "H5.2", "forget a missing file")
    for path in ("../x.md", "journal.md", "/etc/passwd"):
        ctx.expect_err(d.request("forget", path=path), "bad_path", "S2.7" if path != "journal.md" else "S7.5", "forget %s" % path)
    ctx.expect_same(snap, "H5.2", "refused forgets")
    # delete a whole file
    before = ctx.get("journal.md")
    r = d.request("forget", path="topics/food.md")
    if ctx.expect_ok(r, "H5.2", "forget a file"):
        ctx.check(ctx.get("topics/food.md") is None and not os.path.lexists(ctx.path("topics/food.md")), "H5.2", "the forgotten file is still there")
        ctx.check(r.get("removed") == 1, DRV, "forget a file answered removed %r" % r.get("removed"))
        ctx.check(bool(r.get("notices")), "H5.3", "forget a file gave no notice")
        ents = ctx.journal_check(before, r, "forget a file")
        ctx.check(ctx.entry_for(ents, "topics/food.md", authority="person direct") is not None, "S7.3", "removing a topic was not journaled")
    journal = ctx.get("journal.md") or b""
    ctx.check(f1.encode() not in journal and f2.encode() not in journal, "S7.2", "journal.md holds the forgotten content; the journal describes and never copies")
    ctx.end(d)
    # later sessions never bring it back
    for _ in range(2):
        d2, m2 = ctx.session()
        rr = d2.request("recall", paths=["me.md", "topics/food.md", "topics/stay.md"])
        ls = d2.request("list")
        ctx.no_canary([m2, rr, ls], [f1, f2], "H5.2", "a later session")
        ctx.check(keep in m2.raw, "H5.2", "control: the later session lost content that was not forgotten")
        ctx.check("food.md" not in ls.get("topics", []), "H5.2", "list still names the forgotten topic")
        ctx.end(d2)
    ctx.canaries = [c for c in ctx.canaries if c not in (keep, f3)] + [keep, f3]  # kept ones may exist in store only
    # the copy search at the end of the test checks HOME, TMPDIR and XDG dirs for f1 and f2 (and keep/f3, which may not be copied either)


# --------------------------------------------------------------------------
# T15 Concurrency

GRAMMAR_NOTE = "S7.1"


def race_once(ctx, a, b, i, label):
    token = secrets.token_hex(4)
    ba, bb = "race-%d-A-%s" % (i, token), "race-%d-B-%s" % (i, token)
    ctx.put("topics/race.md", "Race base\n")
    pa = ctx.add_proposal(body=ba, target="topics/race.md")
    pb = ctx.add_proposal(body=bb, target="topics/race.md")
    jbefore = ctx.get("journal.md") or b""
    for s in (a, b):
        s.request("pending")
    ra = a.queue_request("decide", proposal=pa, decision="accept", agent="agent-a")
    rb = b.queue_request("decide", proposal=pb, decision="accept", agent="agent-b")
    flush_together([a, b])
    xa, xb = a.finish(ra, 20), b.finish(rb, 20)
    where = "%s iteration %d" % (label, i)
    for r in (xa, xb):
        if r.get("error") == "locked":
            ctx.fail("S8.3", "%s: decide gave locked under ordinary contention" % where)
        else:
            ctx.expect_ok(r, "S8.2", "%s: decide" % where)
    target = ctx.get("topics/race.md") or b""
    lines = target.decode("utf-8", "replace").split("\n")
    ctx.check(sorted(lines) == sorted(["Race base", ba, bb, ""]), "S8.2",
              "%s: the target does not hold each body exactly once: %r" % (where, target[:200]))
    after = ctx.get("journal.md") or b""
    ents = ctx.journal_check(jbefore, None, where, "S8.1")
    text = after[len(jbefore):].decode("utf-8", "replace")
    stray = [l for l in text.split("\n") if l != "" and not l.startswith("- ")]
    ctx.check(not stray, "S8.1", "%s: journal.md holds a broken or torn line: %r" % (where, stray[:2]))
    ctx.check(len(ents) == 4, "S8.1", "%s: expected 4 whole journal entries, found %d" % (where, len(ents)))
    for pid, in ((pa,), (pb,)):
        dec = [k for k, e in enumerate(ents) if e["path"] == "proposals/%s.md" % pid and e["change"] == "accepted" and e["authority"] == "person direct"]
        con = [k for k, e in enumerate(ents) if e["path"] == "topics/race.md" and e["authority"] == "accepted proposal %s" % pid]
        ctx.check(len(dec) == 1 and len(con) == 1 and dec[0] < con[0], "S7.3",
                  "%s: proposal %s lacks its decision entry followed by its content entry" % (where, pid))
        f, _, _ = read_front(ctx.get("proposals/%s.md" % pid) or b"")
        ctx.check(f.get("status") == "accepted", "S8.6", "%s: proposal %s is not accepted" % (where, pid))
    ctx.check(not os.path.lexists(ctx.path(".me.lock")), "S8.2", "%s: .me.lock was left behind" % where)
    leftovers = [n for n in os.listdir(ctx.store) if n.startswith(".") and n.endswith(".tmp")]
    leftovers += [n for n in ctx.names("topics") if n.startswith(".") and n.endswith(".tmp")]
    ctx.check(not leftovers, "S8.4", "%s: temporary files left behind: %s" % (where, leftovers))


def race_series(ctx, host_a, host_b, repeat, label):
    a = b_ = None
    try:
        for i in range(repeat):
            if i % 5 == 0:
                for s in (a, b_):
                    if s is not None:
                        ctx.end(s)
                a, _ = ctx.session(host=host_a)
                b_, _ = ctx.session(host=host_b)
            race_once(ctx, a, b_, i, label)
    finally:
        for s in (a, b_):
            if s is not None and s in ctx.sessions:
                ctx.end(s)
    ctx.lint("S7.1", "%s: after %d races" % (label, repeat))


def t15(ctx):
    ctx.clear_store()
    ctx.put("me.md", "# Me\n")
    ctx.put("journal.md", "# Journal\n")
    repeat = ctx.runner.repeat
    host_a = ctx.runner.host
    race_series(ctx, host_a, host_a, repeat, "same host")
    second = ctx.runner.second
    if second is not None and LEVELS.index(second.info["level"]) >= 2:
        race_series(ctx, host_a, second, repeat, "two different hosts")
    elif second is not None:
        ctx.note("The second host is below Steward, so the cross-host race was not run.")
    # a foreign lock makes writes fail and stays where it is (S8.3)
    ctx.clear_store()
    ctx.put("me.md", "# Me\n")
    ctx.put("topics/travel.md", "Existing line.\n")
    pid = ctx.add_proposal(body="Prefer aisle seats.")
    lock = b"foreignlocktoken0123456789 otherhost 2026-11-12T17:00:00Z\n"
    ctx.put(".me.lock", lock)
    snap = ctx.snap_all()
    d, m = ctx.session(timeout=30)
    ops = [("decide", dict(proposal=pid, decision="accept")),
           ("edit", dict(path="me.md", action="append", text="Locked out.")),
           ("policy", dict(state="off"))]
    for op, fields in ops:
        r = d.request(op, timeout=40, **fields)
        ctx.expect_err(r, "locked", "S8.3", "%s with a foreign .me.lock" % op)
        notices = " ".join(r.get("notices", []) if isinstance(r.get("notices"), list) else [])
        ctx.check(".me.lock" in notices, "S8.3", "%s with a foreign .me.lock: no notice that names .me.lock" % op)
    ctx.check(ctx.get(".me.lock") == lock, "S8.3", "the foreign .me.lock was removed or changed")
    ctx.expect_same(snap, "S8.3", "decide, edit and policy with a foreign lock")
    os.unlink(ctx.path(".me.lock"))
    r = d.request("decide", proposal=pid, decision="accept")
    ctx.expect_ok(r, "S8.3", "control: decide after the foreign lock was removed")
    ctx.check(not os.path.lexists(ctx.path(".me.lock")), "S8.2", "the host left its own .me.lock behind")
    ctx.end(d)


# --------------------------------------------------------------------------
# T16 Round-trip

ME16 = ("# Me\r\n"
        "tabs\tand  trailing spaces   \r\n"
        "odd:   line sep, \x0c form feed, \x85 nel, café, \U0001F642\r\n"
        "Replace target: ALPHA beta\r\n"
        "stray bare CR \r in middle\r\n"
        "last line without break").encode("utf-8")


def t16(ctx):
    ctx.clear_store()
    ctx.put("me.md", ME16)
    d, m = ctx.session()
    cur = ME16
    steps = [
        ("replace one line", dict(path="me.md", action="replace", old="Replace target: ALPHA beta", new="Replace target: GAMMA\nsecond line"),
         lambda c: c.replace(b"Replace target: ALPHA beta", b"Replace target: GAMMA\r\nsecond line")),
        ("replace across a line break", dict(path="me.md", action="replace", old="spaces   \nodd:", new="spaces   \nODD:"),
         lambda c: c.replace(b"spaces   \r\nodd:", b"spaces   \r\nODD:")),
        ("append to a file with no final line break", dict(path="me.md", action="append", text="Added line\nSecond added"),
         lambda c: c + b"\r\nAdded line\r\nSecond added\r\n"),
    ]
    for label, fields, fn in steps:
        before = ctx.get("journal.md")
        r = d.request("edit", **fields)
        if not ctx.expect_ok(r, "S2.6", "edit: " + label):
            continue
        cur = fn(cur)
        got = ctx.get("me.md")
        ctx.check(got == cur, "S2.6", "edit (%s): bytes outside the change differ; expected %r, got %r" % (label, cur[:120], (got or b"")[:120]))
        if got != cur:
            cur = got or cur
        ents = ctx.journal_check(before, r, "edit: " + label)
        ctx.check(ctx.entry_for(ents, "me.md", authority="person direct") is not None, "S7.3", "edit (%s) was not journaled" % label)
    ctx.end(d)

    # accept proposals into targets with different line endings
    ctx.clear_store()
    ctx.put("me.md", "# Me\n")
    unknown = [("x-note", "keep me")]
    cases = []

    def case(name, target, tdata, eol, body, expected, extra=(), keys=None):
        pid = ctx.new_pid()
        if tdata is not None:
            ctx.put(target, tdata)
        pdata = prop_text(target=target, body=body, eol=eol, extra=list(extra), keys=keys)
        ctx.put("proposals/%s.md" % pid, pdata)
        cases.append((name, pid, target, tdata, expected, pdata, eol))

    case("LF target, unknown key, comment and spacing", "topics/lf.md", b"A\nB\n", "\n", "New text.",
         b"A\nB\nNew text.\n",
         extra=["x-note: keep me", "# a comment", "", "x-other:   spaced value   "])
    case("CRLF target without a final line break", "topics/crlf.md", b"First\r\nSecond line no end", "\n",
         "New line one\nNew line two", b"First\r\nSecond line no end\r\nNew line one\r\nNew line two\r\n")
    case("CRLF proposal into an LF target", "topics/lf2.md", b"x\ny\n", "\r\n", "p\r\nq\r\n", b"x\ny\np\nq\n",
         extra=["x-note: keep me"])
    case("first line break is CRLF, later ones LF", "topics/mixed.md", b"a\r\nb\nc", "\n", "Z", b"a\r\nb\nc\r\nZ\r\n")
    case("empty target", "topics/empty.md", b"", "\n", "W", b"W\n")
    d, m = ctx.session()
    for name, pid, target, tdata, expected, pdata, eol in cases:
        r = d.request("decide", proposal=pid, decision="accept")
        if not ctx.expect_ok(r, "S6.8", "accept (%s)" % name):
            continue
        got = ctx.get(target)
        ctx.check(got == expected, "S6.8", "accept (%s): target is %r, expected %r" % (name, got, expected))
        new = ctx.get("proposals/%s.md" % pid) or b""
        drop = (b"status:", b"decided-at:", b"decided-via:")
        old_l = [l for l in keep_ends(pdata) if not l.startswith(drop)]
        new_l = [l for l in keep_ends(new) if not l.startswith(drop)]
        ctx.check(old_l == new_l, "S6.5", "accept (%s): the proposal changed beyond status and decided-at: expected %r, got %r"
                  % (name, old_l[:12], new_l[:12]))
        f, _, _ = read_front(new)
        ctx.check(f.get("status") == "accepted" and time_near_now(f.get("decided-at", "")), "S8.6",
                  "accept (%s): status or decided-at missing" % name)
        if eol == "\r\n":
            ctx.check(not re.search(rb"(?<!\r)\n", new), "S2.3", "accept (%s): the rewritten CRLF proposal has a bare LF" % name)
        else:
            ctx.check(b"\r" not in new, "S2.3", "accept (%s): the rewritten LF proposal gained a CR" % name)
    ctx.lint("S7.1", "after round-trip accepts")
    ctx.end(d)


# --------------------------------------------------------------------------
# T17 Invalid proposal

def t17(ctx):
    ctx.clear_store()
    ctx.put("me.md", "# Me\n")
    ctx.put("topics/travel.md", "Existing line.\n")
    ctx.put("journal.md", "# Journal\n")
    good = [("status", "pending"), ("target", "topics/travel.md"), ("proposed-by", "testhost 1.0"),
            ("proposed-at", "2026-11-12T17:03:01Z"), ("basis", "b")]

    def with_keys(keys):
        return prop_text(keys=keys, body="Prefer aisle seats.")

    bad = [
        ("status twice (pending, then accepted)", with_keys(good + [("status", "accepted")])),
        ("status twice (accepted, then pending)", with_keys([("status", "accepted")] + good)),
        ("a required key is missing", with_keys([kv for kv in good if kv[0] != "basis"])),
        ("a required value is empty", with_keys([kv if kv[0] != "basis" else ("basis", "") for kv in good])),
        ("status has another value", with_keys([("status", "approved")] + good[1:])),
        ("a key in capitals", with_keys([("Status", "pending")] + good[1:])),
        ("target is watches.md", with_keys([good[0], ("target", "watches.md")] + good[2:])),
        ("no front matter", b"Prefer aisle seats.\n"),
        ("front matter never closes", b"---\nstatus: pending\ntarget: topics/travel.md\n\nPrefer aisle seats.\n"),
        ("empty body", prop_text(body="   ")),
    ]
    pids = []
    for label, data in bad:
        pid = ctx.new_pid()
        ctx.put("proposals/%s.md" % pid, data)
        pids.append((label, pid, data))
    d, m = ctx.session()
    if ctx.supports("pending"):
        p = d.request("pending")
        for label, pid, data in pids:
            ctx.check(find_pending(p, pid) is None, "S6.14", "pending lists an invalid proposal (%s) as pending" % label)
            ctx.check(any(file_matches(i.get("file"), pid + ".md") for i in p.get("invalid", []) if isinstance(i, dict)),
                      "S6.14", "pending does not list the invalid proposal (%s) as invalid" % label)
    snap = ctx.snap_all()
    for label, pid, data in pids:
        for decision in ("accept", "refuse"):
            r = d.request("decide", proposal=pid, decision=decision)
            ctx.expect_err(r, "invalid_proposal", "S6.14", "decide %s on an invalid proposal (%s)" % (decision, label))
        r = d.request("revise", proposal=pid, body="Changed.")
        ctx.expect_err(r, "invalid_proposal", "S6.14", "revise an invalid proposal (%s)" % label)
        ctx.check(ctx.get("proposals/%s.md" % pid) == data, "S6.14", "the invalid proposal (%s) was rewritten" % label)
    ctx.expect_same(snap, "S6.14", "decisions on invalid proposals")
    ctx.end(d)


# --------------------------------------------------------------------------
# Extras

def x1(ctx):
    """Deciding twice and deciding unknown proposals."""
    ctx.clear_store()
    ctx.put("me.md", "# Me\n")
    ctx.put("topics/travel.md", "Existing line.\n")
    pa, pr = ctx.add_proposal(body="Prefer aisle seats."), ctx.add_proposal(body="Never red-eyes.")
    d, m = ctx.session()
    ctx.expect_ok(d.request("decide", proposal=pa, decision="accept"), "S8.6", "first accept")
    ctx.expect_ok(d.request("decide", proposal=pr, decision="refuse"), "S8.6", "first refuse")
    snap = ctx.snap_all()
    for pid in (pa, pr):
        for decision in ("accept", "refuse"):
            ctx.expect_err(d.request("decide", proposal=pid, decision=decision), "not_pending", "S6.9",
                           "decide %s again on %s" % (decision, pid))
    ctx.check((ctx.get("topics/travel.md") or b"").count(b"Prefer aisle seats.") == 1, "S8.6", "the body was added twice")
    ctx.expect_same(snap, "S6.9", "deciding a decided proposal")
    ctx.expect_err(d.request("decide", proposal="20260101T000000Z-zzzz", decision="accept"), "not_found", "S6.9", "decide an unknown proposal")
    ctx.expect_err(d.request("decide", proposal=pa, decision="maybe"), "bad_request", DRV, "decide with a bad decision")
    ctx.expect_err(d.request("revise", proposal=pa, body="Changed."), "not_pending", "S6.15", "revise a decided proposal")
    ctx.end(d)
    # a target that is a symbolic link or not a regular file: decide gives bad_target and writes nothing
    ctx.clear_store()
    ctx.put("me.md", "# Me\n")
    outside = os.path.join(ctx.outside, "target.md")
    with open(outside, "w") as handle:
        handle.write("Outside file.\n")
    ctx.link("topics/linked.md", outside)
    os.makedirs(ctx.path("topics/dir.md"))
    pl = ctx.add_proposal(body="Via a link.", target="topics/linked.md")
    pd = ctx.add_proposal(body="Into a directory.", target="topics/dir.md")
    snap = ctx.snap_all()
    d, m = ctx.session()
    for pid in (pl, pd):
        ctx.expect_err(d.request("decide", proposal=pid, decision="accept"), "bad_target", "S2.4",
                       "accept a proposal whose target is a symbolic link or a directory")
    ctx.end(d)
    ctx.expect_same(snap, "S2.4", "accepting into a symbolic link or directory")
    ctx.check(slurp(outside) == "Outside file.\n", "S2.4", "the file behind the target link was written")
    # revise a pending proposal: body changes, front matter stays, no journal entry
    ctx.clear_store()
    ctx.put("me.md", "# Me\n")
    ctx.put("topics/travel.md", "Existing line.\n")
    pid = ctx.add_proposal(body="Old words.", extra=["x-note: keep me"])
    ctx.put("journal.md", "# Journal\n")
    d, m = ctx.session()
    jb = ctx.get("journal.md")
    pbefore = ctx.get("proposals/%s.md" % pid)
    r = d.request("revise", proposal=pid, body="New words.")
    if ctx.expect_ok(r, "S6.15", "revise"):
        new = ctx.get("proposals/%s.md" % pid) or b""
        f, body, problems = read_front(new)
        ctx.check(not problems and f.get("status") == "pending" and f.get("x-note") == "keep me" and body.strip() == "New words.",
                  "S6.15", "revise did not keep the front matter and replace the body: %r" % new)
        ctx.check(ctx.get("journal.md") == jb, "S6.13", "revise wrote a journal entry; creating or revising a proposal is not journaled")
        r2 = d.request("decide", proposal=pid, decision="accept")
        ctx.expect_ok(r2, "S6.15", "accept after revise")
        ctx.check(b"New words." in (ctx.get("topics/travel.md") or b"") and b"Old words." not in (ctx.get("topics/travel.md") or b""),
                  "S6.15", "accepting applied the old body, not the revised one")
    ctx.end(d)


def x2(ctx):
    """Proposal names: bad names are invalid, hidden files and non-.md names are ignored."""
    ctx.clear_store()
    ctx.put("me.md", "# Me\n")
    good = ctx.add_proposal(body="Good one.")
    ok_body = prop_text(body="Odd name body.")
    ctx.put("proposals/bad-name.md", ok_body)
    ctx.put("proposals/%s (conflict copy).md" % ctx.new_pid(), prop_text(body="Conflict body."))
    ctx.put("proposals/.hidden.md", prop_text(body="Hidden body."))
    ctx.put("proposals/%s.md.bak" % ctx.new_pid(), prop_text(body="Backup body."))
    snap = ctx.snap_all()
    d, m = ctx.session()
    p = d.request("pending")
    ctx.check(find_pending(p, good) is not None, "S6.14", "the good proposal is not pending")
    ctx.check(find_pending(p, "bad-name") is None, "S2.1", "a proposal with a bad name is listed as pending")
    inv = [os.path.basename(i.get("file", "")) for i in p.get("invalid", []) if isinstance(i, dict)]
    ctx.check("bad-name.md" in inv, "S2.1", "bad-name.md is not in the invalid list")
    ctx.check(any("conflict copy" in n for n in inv), "S8.8", "a conflict copy is not in the invalid list")
    ctx.check(".hidden.md" not in inv and not any(n.endswith(".bak") for n in inv), "S2.2", "a hidden file or a non-.md file is listed as invalid")
    ctx.check(all("Hidden body" not in x.get("body", "") and "Backup body" not in x.get("body", "")
                  for x in p.get("proposals", []) if isinstance(x, dict)), "S2.2", "a hidden or non-.md file was read as a proposal")
    ctx.end(d)
    ctx.expect_same(snap, "S6.14", "listing proposals")


def x3(ctx):
    """list leaves out hidden files, bad names and symbolic links."""
    ctx.clear_store()
    secret = os.path.join(ctx.outside, "secret.md")
    with open(secret, "w") as handle:
        handle.write("outside\n")
    c = ctx.canary("list")
    ctx.put("me.md", "# Me\n")
    for rel in ("topics/travel.md", "topics/a.v2_x-1.md", "topics/" + "a" * 64 + ".md", "projects/garden.md"):
        ctx.put(rel, "Content %s\n" % c)
    for rel in ("topics/.hidden.md", "topics/Travel.md", "topics/My Topic.md", "topics/x.txt", "topics/.draft.md.tmp",
                "topics/" + "a" * 65 + ".md", "topics/-dash.md", "projects/Bad.md", "projects/.p.md"):
        ctx.put(rel, "Content %s\n" % c)
    ctx.link("topics/link.md", secret)
    snap = ctx.snap_all()
    d, m = ctx.session()
    r = d.request("list")
    ctx.expect_ok(r, "S2.1", "list")
    expected_topics = {"travel.md", "a.v2_x-1.md", "a" * 64 + ".md"}
    ctx.check(set(r.get("topics", [])) == expected_topics, "S2.1",
              "list shows topics %r; expected only %r" % (sorted(r.get("topics", [])), sorted(expected_topics)))
    ctx.check(set(r.get("projects", [])) == {"garden.md"}, "S2.1", "list shows projects %r; expected only garden.md" % sorted(r.get("projects", [])))
    ctx.check(r.get("watches") is False, "S4.3", "list says watches.md exists when it does not")
    ctx.no_canary([r], [c], "H2.1", "list reads names only")
    ctx.mid_edit(d, lambda: ctx.put("watches.md", "- w\n"))
    ctx.check(d.request("list").get("watches") is True, "S4.3", "list does not say that watches.md exists")

    def swap():
        os.unlink(ctx.path("watches.md"))
        ctx.link("watches.md", secret)
    ctx.mid_edit(d, swap)
    ctx.check(d.request("list").get("watches") is False, "S2.4", "list counts a symbolic link as watches.md")
    ctx.end(d)


def x4(ctx):
    """journal.md is a symbolic link: the host neither appends nor replaces it (S2.4, S8.7)."""
    ctx.clear_store()
    ctx.put("me.md", "# Me\n")
    target = os.path.join(ctx.outside, "journal-target.md")
    with open(target, "w") as handle:
        handle.write("- 2026-11-10T09:00:05Z | me.md | added an aim | host: oldhost 1.0 | authority: person direct\n")
    ctx.link("journal.md", target)
    with open(target, "rb") as handle:
        original = handle.read()
    d, m = ctx.session()
    r = d.request("edit", path="me.md", action="append", text="Aim two.")
    if ctx.expect_ok(r, "S8.7", "edit with a symbolic-link journal"):
        ctx.check(b"Aim two." in (ctx.get("me.md") or b""), "S8.7", "the change was not made")
        ctx.check(bool(r.get("notices")), "S8.7", "no notice that the change has no receipt")
    ctx.check(os.path.islink(ctx.path("journal.md")), "S2.4", "journal.md was replaced; it was a symbolic link")
    with open(target, "rb") as handle:
        ctx.check(handle.read() == original, "S2.4", "the file behind the journal.md link was appended to")
    ctx.end(d)


# --------------------------------------------------------------------------
# registry and runner

TESTS = [
    ("T1", "Absence", "reader", t1),
    ("T2", "Mount", "reader", t2),
    ("T3", "Off", "reader", t3),
    ("T5", "Discard", "reader", t5),
    ("T6", "Traversal", "reader", t6),
    ("T7", "Watches", "reader", t7),
    ("T8", "Proposal", "proposer", t8),
    ("T9", "Second host", "proposer", t9),
    ("T10", "Self-approval", "proposer", t10),
    ("T11", "Version", "proposer", t11),
    ("T12", "Direct edit", "steward", t12),
    ("T13", "Receipt", "steward", t13),
    ("T14", "Delete", "steward", t14),
    ("T15", "Concurrency", "steward", t15),
    ("T16", "Round-trip", "steward", t16),
    ("T17", "Invalid proposal", "steward", t17),
    ("X1", "Extra: deciding twice, revise", "steward", x1),
    ("X2", "Extra: proposal file names", "proposer", x2),
    ("X3", "Extra: list leaves out ignored names", "reader", x3),
    ("X4", "Extra: journal.md is a symbolic link", "steward", x4),
]
TITLES = dict((t[0], t[1]) for t in TESTS)
TITLES.update({"T4": "Injection", "T18": "Briefing"})
ORDER = ["T1", "T2", "T3", "T4", "T5", "T6", "T7", "T8", "T9", "T10", "T11", "T12", "T13", "T14", "T15", "T16", "T17", "T18",
         "X1", "X2", "X3", "X4"]
LEVEL_OF = dict((t[0], t[2]) for t in TESTS)
LEVEL_OF.update({"T4": "reader", "T18": "briefer"})


class Host:
    def __init__(self, cmd, name):
        self.cmd = cmd
        self.argv = shlex.split(cmd)
        self.label = name
        self.info = None


class Runner:
    def __init__(self, host_cmd, second_cmd=None, repeat=50, keep=False, timeout=DEFAULT_TIMEOUT):
        self.host = Host(host_cmd, "host")
        self.second = Host(second_cmd, "second host") if second_cmd else None
        self.repeat = repeat
        self.keep = keep
        self.timeout = timeout
        self.level = "reader"
        self.level_n = 0

    def probe(self, host):
        """Ask a driver who it is. Return a list of failures."""
        ctx = Ctx(self, "H")
        try:
            d, _ = ctx.session(host=host, mount=False)
            info = d.request("host")
            ctx.end(d)
            if info.get("ok") is True:
                host.info = dict(info)
            else:
                ctx.fail(DRV, "the host operation failed: %r" % info.get("error"))
        except DriverError as exc:
            ctx.fail(DRV, str(exc))
        finally:
            ctx.finish()
            ctx.cleanup()
        return ctx.failures

    def run_test(self, tid, fn):
        ctx = Ctx(self, tid)
        started = time.time()
        try:
            fn(ctx)
        except DriverError as exc:
            ctx.fail(DRV, "driver error: %s" % exc)
        except Exception:  # noqa: BLE001
            ctx.fail("RUNNER", "the runner itself failed (a runner bug): " + traceback.format_exc(limit=4).strip().splitlines()[-1])
            ctx.note(traceback.format_exc(limit=6))
        finally:
            try:
                ctx.finish()
            except Exception as exc:  # noqa: BLE001
                ctx.fail("RUNNER", "end-of-test checks failed: %s" % exc)
            ctx.cleanup()
        return {"id": tid, "title": TITLES[tid], "level": LEVEL_OF[tid],
                "status": "fail" if ctx.failures else "pass", "checks": ctx.checks,
                "failures": ctx.failures, "notes": ctx.notes,
                "not_run_parts": NOT_RUN_PARTS.get(tid, []), "seconds": round(time.time() - started, 2)}

    def run(self, only=None):
        results = []
        pre = self.probe(self.host)
        if not pre and self.second is not None:
            pre = ["second host: " + f["message"] for f in self.probe(self.second)]
        else:
            pre = [f["message"] for f in pre] if pre and isinstance(pre[0], dict) else pre
        out = {"runner": "thou_conform " + __version__, "host": self.host.info, "second_host": self.second.info if self.second else None,
               "tests": results}
        if pre or not self.host.info:
            out["preflight_failures"] = pre or ["the host did not answer the host operation"]
            out.update(summary(results, False))
            return out
        self.level = self.host.info["level"]
        self.level_n = LEVELS.index(self.level)
        for tid in ORDER:
            if only and tid not in only:
                continue
            level = LEVEL_OF[tid]
            if tid in NOT_RUN:
                results.append({"id": tid, "title": TITLES[tid], "level": level, "status": "not_run",
                                "reason": NOT_RUN[tid], "failures": [], "checks": 0})
            elif LEVELS.index(level) > self.level_n:
                results.append({"id": tid, "title": TITLES[tid], "level": level, "status": "not_run",
                                "reason": "above the level the host claims (%s)" % self.level, "failures": [], "checks": 0})
            else:
                results.append(self.run_test(tid, dict((t[0], t[3]) for t in TESTS)[tid]))
        out.update(summary(results, True))
        return out


def summary(results, preflight_ok):
    ran = [r for r in results if r["status"] != "not_run"]
    failed = [r for r in ran if r["status"] == "fail"]
    return {"summary": {"passed": len(ran) - len(failed), "failed": len(failed),
                        "not_run": len(results) - len(ran)},
            "ok": bool(preflight_ok and ran and not failed)}


def render(result):
    lines = []
    host = result.get("host") or {}
    if host:
        lines.append("host: %s %s, claims %s, off switch enforced by %s" % (
            host.get("name"), host.get("version"), host.get("level"), host.get("enforcement")))
        if host.get("enforcement") == "instruction":
            lines.append("  note: the off switch works only by instruction; the claim must say 'by instruction' (H0.3, H6.4)")
    for item in result.get("preflight_failures", []):
        lines.append("PREFLIGHT FAIL: " + item)
    for t in result["tests"]:
        label = {"pass": "PASS    ", "fail": "FAIL    ", "not_run": "NOT RUN "}[t["status"]]
        extra = " (%d checks)" % t["checks"] if t["status"] != "not_run" else ""
        lines.append("%s%s %s%s" % (label, t["id"], t["title"], extra))
        if t["status"] == "not_run":
            lines.append("         " + t["reason"])
        for f in t["failures"]:
            lines.append("         - [%s] %s" % (f["req"], f["message"]))
        for n in t.get("notes", []):
            lines.append("         note: " + n.strip().splitlines()[0])
        for part in t.get("not_run_parts", []):
            lines.append("         not run: " + part)
    s = result["summary"]
    lines.append("")
    lines.append("%d passed, %d failed, %d not run" % (s["passed"], s["failed"], s["not_run"]))
    lines.append("Pass means the host's code passed the engine-level tests. It is not a conformance claim by itself.")
    return "\n".join(lines)


def main(argv=None):
    parser = argparse.ArgumentParser(description="Drive a thou host through the engine-level tests in HOST.md.")
    parser.add_argument("--host", required=True, help="driver command (split with shlex)")
    parser.add_argument("--second-host", help="an unrelated host, for T9 and a cross-host T15")
    parser.add_argument("--repeat", type=int, default=50, help="T15 iterations (default 50)")
    parser.add_argument("--only", help="comma-separated tests to run, for example T3,T6")
    parser.add_argument("--json", action="store_true", help="print machine-readable results")
    parser.add_argument("--keep", action="store_true", help="keep the temporary directories")
    parser.add_argument("--timeout", type=float, default=DEFAULT_TIMEOUT, help="seconds to wait for each answer")
    args = parser.parse_args(argv)
    only = None
    if args.only:
        only = set(x.strip().upper() for x in args.only.split(",") if x.strip())
        unknown = only - set(ORDER)
        if unknown:
            print("unknown test ids: %s" % ", ".join(sorted(unknown)), file=sys.stderr)
            return 2
    if args.repeat < 1:
        print("--repeat must be at least 1", file=sys.stderr)
        return 2
    runner = Runner(args.host, args.second_host, args.repeat, args.keep, args.timeout)
    result = runner.run(only)
    if args.json:
        print(json.dumps(result, indent=2))
    else:
        print(render(result))
    if result.get("preflight_failures"):
        return 2
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
