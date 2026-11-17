#!/usr/bin/env python3
"""TEST FIXTURE ONLY. Not a host. Do not use it for a person's store.

A minimal Steward driver that follows conformance/DRIVER.md closely enough to
pass the conformance runner. It exists so that the runner's own tests can show
that each check can fail: `--break NAME[,NAME]` switches on a deliberate bug.

  python3 fake_host.py [--level reader|proposer|steward] [--name N] [--break a,b]
"""

import json
import os
import random
import re
import secrets
import sys
import time
import unicodedata
from datetime import datetime, timezone

LEVELS = ["reader", "proposer", "steward"]
OP_LEVEL = {"host": 0, "mount": 0, "list": 0, "recall": 0, "pending": 1, "propose": 1,
            "decide": 2, "revise": 2, "edit": 2, "forget": 2, "policy": 2}
NAME = r"[a-z0-9][a-z0-9._-]{0,63}\.md"
NAME_RE = re.compile(NAME)
PID_RE = re.compile(r"[0-9]{8}T[0-9]{6}Z-[a-z0-9]{4,47}")
RECALLABLE = re.compile(r"me\.md|watches\.md|(?:topics|projects)/" + NAME)
TARGET_RE = re.compile(r"me\.md|(?:topics|projects)/" + NAME)
TIME_RE = re.compile(r"[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}Z")
REQUIRED = ("status", "target", "proposed-by", "proposed-at", "basis")
LOCK_WAIT = 3.0

OPTS = {"level": "steward", "name": "fakehost", "version": "0.0", "break": set()}


def bug(name):
    return name in OPTS["break"]


class Reply(Exception):
    def __init__(self, error, message, notices=None):
        Exception.__init__(self, message)
        self.error, self.message, self.notices = error, message, notices or []


# ---------------------------------------------------------------- store basics

def root():
    home = os.environ.get("ME_HOME")
    return home if home else os.path.join(os.path.expanduser("~"), ".me")


def p(rel):
    return os.path.join(root(), rel)


def now():
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def regular(path):
    return os.path.isfile(path) and not os.path.islink(path)


def read_bytes(rel):
    with open(p(rel), "rb") as handle:
        return handle.read()


def dup_hook(pairs):
    keys = [k for k, _ in pairs]
    if len(keys) != len(set(keys)):
        raise ValueError("duplicate member")
    return dict(pairs)


def read_policy():
    """Return (state, spec_ok, object_or_None)."""
    path = p("policy.json")
    if not os.path.lexists(path):
        return "on", True, None
    if os.path.islink(path):
        return "off", True, None
    try:
        with open(path, "rb") as handle:
            obj = json.loads(handle.read().decode("utf-8"), object_pairs_hook=dup_hook,
                             parse_constant=lambda c: (_ for _ in ()).throw(ValueError(c)))
    except (OSError, ValueError, UnicodeDecodeError):
        return "off", True, None
    if not isinstance(obj, dict):
        return "off", True, None
    state = obj.get("state")
    if bug("loose_policy") and isinstance(state, str):
        state = state.lower()
    if state != "on":
        return "off", True, obj
    spec = obj.get("spec", "0.1")
    return "on", (spec == "0.1" and isinstance(spec, str)) or bug("ignore_spec"), obj


CACHED = {}


def status():
    """Return (memory, writable). Policy first, before any other file (H1.5)."""
    if bug("policy_cache") and "policy" in CACHED:
        state, spec_ok = CACHED["policy"]
    else:
        state, spec_ok, _ = read_policy()
        CACHED["policy"] = (state, spec_ok)
    if state == "off":
        return "off", True
    if not regular(p("me.md")):
        return "absent", True
    return "on", spec_ok


def need_on(writable=False):
    memory, ok = status()
    if memory == "absent":
        raise Reply("absent", "There is no store (no me.md).")
    if memory == "off":
        raise Reply("memory_off", "Memory is off: policy.json does not say \"on\".")
    if writable and not ok:
        raise Reply("unsupported_spec", "policy.json names a spec this host does not support.")
    return memory


def host_field(agent=None):
    base = "%s %s" % (OPTS["name"], OPTS["version"])
    return "%s (%s)" % (base, agent) if agent else base


# ---------------------------------------------------------------- lock and writes

class Lock(object):
    def __enter__(self):
        if bug("no_lock"):
            return self
        self.token = secrets.token_hex(12)
        path = p(".me.lock")
        deadline = time.time() + LOCK_WAIT
        while True:
            try:
                fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
                os.write(fd, ("%s %s %s\n" % (self.token, OPTS["name"], now())).encode())
                os.close(fd)
                return self
            except FileExistsError:
                if time.time() > deadline:
                    if bug("lock_remove_foreign"):
                        os.unlink(path)
                        continue
                    raise Reply("locked", "Another host holds .me.lock. Delete it if no host is writing.",
                                ["The store lock .me.lock is held."])
                time.sleep(0.01)

    def __exit__(self, *exc):
        if bug("no_lock"):
            return
        try:
            with open(p(".me.lock"), "rb") as handle:
                if self.token.encode() in handle.read():
                    os.unlink(p(".me.lock"))
        except OSError:
            pass


def write_file(rel, make):
    """S8.4: read, make new bytes, write temp, re-read and compare, rename."""
    while True:
        old = read_bytes(rel) if os.path.lexists(p(rel)) else None
        new = make(old)
        time.sleep(random.uniform(0, 0.015))  # a window for races
        directory = os.path.dirname(p(rel))
        os.makedirs(directory, exist_ok=True)
        tmp = os.path.join(directory, "." + os.path.basename(rel) + ".tmp")
        with open(tmp, "wb") as handle:
            handle.write(new)
        os.chmod(tmp, 0o600)
        again = read_bytes(rel) if os.path.lexists(p(rel)) else None
        if again != old and not bug("no_lock"):
            os.unlink(tmp)
            continue
        os.replace(tmp, p(rel))
        return old


def journal(entries, notices):
    """Append whole entries, one write each (S8.1). Return the lines."""
    lines = []
    path = p("journal.md")
    for entry in entries:
        path_rel, change, authority, agent = entry[:4]
        if bug("journal_content") and len(entry) > 4:
            change = change + " " + entry[4].strip().replace("|", "/")[:120]
        line = "- %s | %s | %s | host: %s | authority: %s" % (now(), path_rel, change, host_field(agent), authority)
        lines.append(line)
    if os.path.islink(path):
        notices.append("journal.md is a symbolic link, so these changes have no receipt.")
        return []
    if bug("rewrite_journal") and os.path.exists(path):
        with open(path, "rb") as handle:
            kept = [l for l in handle.read().decode().split("\n") if l.startswith("- ")]
        with open(path, "wb") as handle:
            handle.write(("\n".join(kept + lines) + "\n").encode())
        return lines
    for line in lines:
        data = (line + "\n").encode()
        fd = os.open(path, os.O_WRONLY | os.O_APPEND | os.O_CREAT, 0o600)
        try:
            size = os.fstat(fd).st_size
            if size:
                with open(path, "rb") as handle:
                    handle.seek(size - 1)
                    if handle.read(1) != b"\n":
                        data = b"\n" + data
            if bug("torn_journal"):
                os.write(fd, data[:20])
                time.sleep(0.03)
                os.write(fd, data[20:])
            else:
                os.write(fd, data)
        finally:
            os.close(fd)
    return lines


# ---------------------------------------------------------------- text rules

def normalize(text):
    return re.sub(r"\s+", " ", unicodedata.normalize("NFC", text)).strip()


def convert_breaks(text, nl):
    return re.sub(r"\r\n|\n", nl, text)


def apply_body(old, body):
    """S6.8. Return (new bytes, applied)."""
    if old is None:
        return (body.rstrip("\r\n") + "\n").encode(), "added"
    crlf = first_break_crlf(old) and not bug("rewrite_crlf")
    nl = "\r\n" if crlf else "\n"
    text = convert_breaks(re.sub(r"(\r\n|\n)+\Z", "", body), nl).encode()
    if bug("overwrite_not_append"):
        return text + nl.encode(), "added"
    tail = text + nl.encode()
    if old == tail or old.endswith(nl.encode() + tail):
        return old, "already"
    if old and not old.endswith(b"\n"):
        old += nl.encode()
    return old + tail, "added"


# ---------------------------------------------------------------- proposals

def parse_proposal(data):
    """Return (fields, body, problem). problem is None for a valid proposal."""
    text = data.decode("utf-8", "replace")
    lines = text.split("\n")
    if lines[0].rstrip("\r") != "---":
        return {}, text, "no front matter"
    close = None
    for i in range(1, len(lines)):
        if lines[i].rstrip("\r") == "---":
            close = i
            break
    if close is None:
        return {}, text, "front matter is not closed"
    fields, problem = {}, None
    for line in lines[1:close]:
        line = line.rstrip("\r")
        if line.strip() == "" or line.startswith("#"):
            continue
        m = re.fullmatch(r"([a-z][a-z-]*): (.*)", line)
        if not m:
            problem = problem or "bad line %r" % line
            continue
        key, val = m.group(1), m.group(2).strip()
        if val.startswith('"'):
            q = re.fullmatch(r'"((?:[^"\\]|\\["\\])*)"', val)
            if not q:
                problem = problem or "bad quoting"
                continue
            val = re.sub(r'\\(["\\])', r"\1", q.group(1))
        if key in fields:
            problem = problem or "duplicate key %s" % key
        fields[key] = val
    body = "\n".join(lines[close + 1:])
    if bug("self_approve"):
        found = re.findall(r"(?m)^status:\s*(\w+)", text)
        if found:
            fields["status"] = found[-1]
    if bug("decide_invalid") and problem and problem.startswith("duplicate"):
        problem = None
    if problem is None:
        for key in REQUIRED:
            if not fields.get(key):
                problem = "missing or empty %s" % key
                break
    if problem is None and fields["status"] not in ("pending", "accepted", "refused"):
        problem = "bad status"
    if problem is None and not TARGET_RE.fullmatch(fields["target"]):
        problem = "bad target"
    if problem is None and not TIME_RE.fullmatch(fields["proposed-at"]):
        problem = "bad time"
    if problem is None and normalize(body) == "":
        problem = "empty body"
    return fields, body, problem


def body_text(body):
    return body[1:] if body.startswith("\n") else (body[2:] if body.startswith("\r\n") else body)


def load_proposals():
    """Return a list of dicts for every .md file in proposals/ that is not hidden."""
    out = []
    directory = p("proposals")
    if not os.path.isdir(directory):
        return out
    for name in sorted(os.listdir(directory)):
        if name.startswith(".") or not name.endswith(".md"):
            continue
        path = os.path.join(directory, name)
        if os.path.islink(path) or not os.path.isfile(path):
            continue
        with open(path, "rb") as handle:
            data = handle.read()
        fields, body, problem = parse_proposal(data)
        if not PID_RE.fullmatch(name[:-3]) and problem is None:
            problem = "bad file name"
        out.append({"name": name, "id": name[:-3], "data": data, "fields": fields, "body": body, "problem": problem})
    return out


def rewrite_proposal(data, updates, body=None):
    """Change given keys, keep every other line and the line endings."""
    text = data.decode("utf-8")
    eol = "\r\n" if "\r\n" in text else "\n"
    lines = text.split("\n")
    close = [i for i in range(1, len(lines)) if lines[i].rstrip("\r") == "---"][0]
    head, rest = lines[1:close], lines[close:]
    if bug("drop_unknown_keys"):
        head = [l for l in head if re.match(r"(status|target|proposed-by|proposed-at|basis|decided-at|decided-via):", l)]
    done = set()
    for i, line in enumerate(head):
        m = re.match(r"([a-z][a-z-]*): ", line.rstrip("\r"))
        if m and m.group(1) in updates and m.group(1) not in done:
            head[i] = "%s: %s%s" % (m.group(1), updates[m.group(1)], "\r" if line.endswith("\r") else "")
            done.add(m.group(1))
    for key, val in updates.items():
        if key not in done:
            head.append("%s: %s%s" % (key, val, "\r" if eol == "\r\n" else ""))
    if body is not None:
        cr = "\r" if eol == "\r\n" else ""
        tail = [cr, convert_breaks(body.rstrip("\r\n"), eol) + cr, ""]
        return "\n".join(["---" + cr] + head + ["---" + cr] + tail).encode()
    out = ["---" + ("\r" if eol == "\r\n" else "")] + head + rest
    if bug("rewrite_crlf"):
        return "\n".join(l.rstrip("\r") for l in out).encode()
    return "\n".join(out).encode()


# ---------------------------------------------------------------- operations

def op_host(req):
    return {"name": OPTS["name"], "version": OPTS["version"], "spec": "0.1", "level": OPTS["level"],
            "enforcement": "code"}


def op_mount(req):
    memory, ok = status()
    if bug("write_when_absent") and memory == "absent":
        os.makedirs(root(), exist_ok=True)
    if bug("touch_store"):
        try:
            open(p(".seen"), "w").close()
        except OSError:
            pass
    files = []
    if memory == "on" or (bug("read_when_off") and regular(p("me.md"))):
        text = read_bytes("me.md").decode("utf-8", "replace")
        files = [{"path": "me.md", "text": text}]
        if bug("copy_to_cache"):
            cache = os.path.join(os.path.expanduser("~"), ".cache")
            os.makedirs(cache, exist_ok=True)
            with open(os.path.join(cache, "me.md.copy"), "w") as handle:
                handle.write(text)
    out = {"memory": memory, "store": os.path.abspath(root()), "files": files}
    if memory == "on" and not ok:
        out["writable"] = False
    return out


def op_list(req):
    memory, _ = status()
    topics, projects, watches = [], [], False
    if memory == "on":
        for folder, bucket in (("topics", topics), ("projects", projects)):
            d = p(folder)
            if os.path.isdir(d) and not os.path.islink(d):
                for name in sorted(os.listdir(d)):
                    ok = NAME_RE.fullmatch(name) and regular(os.path.join(d, name))
                    if bug("list_hidden"):
                        ok = name.endswith(".md") and not os.path.islink(os.path.join(d, name))
                    if ok:
                        bucket.append(name)
        watches = regular(p("watches.md"))
    return {"memory": memory, "topics": topics, "projects": projects, "watches": watches}


def op_recall(req):
    paths, purpose = req.get("paths"), req.get("purpose", "task")
    if not isinstance(paths, list) or not all(isinstance(x, str) for x in paths) or purpose not in ("task", "briefing", "watches"):
        raise Reply("bad_request", "paths must be a list of strings.")
    memory, _ = status()
    files, skipped = [], []
    for rel in paths:
        if memory != "on":
            skipped.append({"path": rel, "reason": "memory is %s" % memory})
            continue
        if bug("follow_symlinks"):
            full = os.path.join(root(), rel)
            if os.path.isfile(full):
                files.append({"path": rel, "text": open(full, "rb").read().decode("utf-8", "replace")})
                continue
        if not RECALLABLE.fullmatch(rel):
            skipped.append({"path": rel, "reason": "not a path a host recalls"})
            continue
        if rel == "watches.md" and purpose == "task" and not bug("watches_leak"):
            skipped.append({"path": rel, "reason": "watches.md is read only for a briefing or when asked"})
            continue
        cache = os.path.join(os.environ.get("XDG_CACHE_HOME", ""), "fake", rel.replace("/", "_"))
        if bug("stale_cache") and rel.startswith("topics/") and os.path.exists(cache):
            files.append({"path": rel, "text": open(cache).read()})
            continue
        if not regular(p(rel)):
            skipped.append({"path": rel, "reason": "missing, or a symbolic link"})
            continue
        try:
            text = read_bytes(rel).decode("utf-8")
        except UnicodeDecodeError:
            skipped.append({"path": rel, "reason": "not valid UTF-8"})
            continue
        if bug("stale_cache"):
            os.makedirs(os.path.dirname(cache), exist_ok=True)
            with open(cache, "w") as handle:
                handle.write(text)
        files.append({"path": rel, "text": text})
    return {"memory": memory, "files": files, "skipped": skipped}


def op_pending(req):
    memory, _ = status()
    out = {"memory": memory, "proposals": [], "invalid": []}
    if memory != "on":
        return out
    for prop in load_proposals():
        if prop["problem"]:
            out["invalid"].append({"file": "proposals/" + prop["name"], "reason": prop["problem"]})
        elif prop["fields"]["status"] == "pending":
            f = prop["fields"]
            out["proposals"].append({"id": prop["id"], "file": "proposals/" + prop["name"], "target": f["target"],
                                     "proposed-by": f["proposed-by"], "proposed-at": f["proposed-at"],
                                     "basis": f["basis"], "body": body_text(prop["body"])})
    return out


def op_propose(req):
    target, body, basis = req.get("target"), req.get("body"), req.get("basis")
    if not all(isinstance(x, str) for x in (target, body, basis)):
        raise Reply("bad_request", "target, body and basis are required strings.")
    memory = need_on(True)
    if not TARGET_RE.fullmatch(target):
        raise Reply("bad_target", "The target must be me.md, topics/<name>.md or projects/<name>.md.")
    if normalize(body) == "":
        raise Reply("empty_body", "The body is empty.")
    if not bug("ignore_refusals"):
        for prop in load_proposals():
            refused = prop["problem"] is not None or prop["fields"].get("status") == "refused"
            if refused and normalize(prop["body"] if prop["problem"] else body_text(prop["body"])) == normalize(body):
                raise Reply("refused", "The person refused this before.")
    agent = req.get("agent")
    os.makedirs(p("proposals"), exist_ok=True, mode=0o700)
    while True:
        pid = "%s-%s" % (datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ"),
                         "".join(random.choice("abcdefghijklmnopqrstuvwxyz0123456789") for _ in range(4)))
        try:
            fd = os.open(p("proposals/%s.md" % pid), os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
            break
        except FileExistsError:
            continue
    quoted = '"%s"' % basis.replace("\\", "\\\\").replace('"', '\\"').replace("\n", " ")
    text = "---\nstatus: pending\ntarget: %s\nproposed-by: %s\nproposed-at: %s\nbasis: %s\n---\n\n%s\n" % (
        target, host_field(agent), now(), quoted, body.rstrip("\r\n"))
    os.write(fd, text.encode())
    os.close(fd)
    return {"memory": memory, "proposal": pid, "file": "proposals/%s.md" % pid}


def find_prop(pid):
    if not isinstance(pid, str) or not PID_RE.fullmatch(pid):
        raise Reply("not_found", "No such proposal.")
    for prop in load_proposals():
        if prop["id"] == pid:
            return prop
    raise Reply("not_found", "No such proposal.")


def op_decide(req):
    pid, decision = req.get("proposal"), req.get("decision")
    if decision not in ("accept", "refuse") or not isinstance(pid, str):
        raise Reply("bad_request", "proposal and decision (accept or refuse) are required.")
    memory = need_on(True)
    agent = req.get("agent")
    notices, entries, applied = [], [], None
    with Lock():
        prop = find_prop(pid)
        if prop["problem"]:
            raise Reply("invalid_proposal", "That proposal file is invalid: %s." % prop["problem"])
        if prop["fields"]["status"] != "pending" and not (bug("accept_twice") and decision == "accept"):
            raise Reply("not_pending", "That proposal was already decided.")
        rel = "proposals/" + prop["name"]
        if decision == "accept":
            target = prop["fields"]["target"]
            if os.path.lexists(p(target)) and not regular(p(target)):
                raise Reply("bad_target", "The target is a symbolic link or not a regular file.")
            holder = {}

            def make(old):
                new, holder["applied"] = apply_body(old, body_text(prop["body"]))
                return new
            write_file(target, make)
            applied = holder["applied"]
            write_file(rel, lambda old: rewrite_proposal(old, {"status": "accepted", "decided-at": now()}))
            entries = [(rel, "accepted", "person direct", agent, prop["body"]),
                       (target, "added text" if applied == "added" else "already applied", "accepted proposal " + pid, agent, prop["body"])]
        else:
            write_file(rel, lambda old: rewrite_proposal(old, {"status": "refused", "decided-at": now()}))
            entries = [(rel, "refused", "person direct", agent, prop["body"])]
    lines = journal(entries, notices)
    return {"memory": memory, "status": "accepted" if decision == "accept" else "refused", "applied": applied,
            "journal": lines, "notices": notices}


def op_revise(req):
    pid, body = req.get("proposal"), req.get("body")
    if not isinstance(pid, str) or not isinstance(body, str):
        raise Reply("bad_request", "proposal and body are required.")
    memory = need_on(True)
    if normalize(body) == "":
        raise Reply("empty_body", "The body is empty.")
    with Lock():
        prop = find_prop(pid)
        if prop["problem"]:
            raise Reply("invalid_proposal", "That proposal file is invalid.")
        if prop["fields"]["status"] != "pending":
            raise Reply("not_pending", "That proposal was already decided.")
        write_file("proposals/" + prop["name"], lambda old: rewrite_proposal(old, {}, body=body))
    return {"memory": memory}


def edit_path(path):
    if not isinstance(path, str) or not RECALLABLE.fullmatch(path):
        raise Reply("bad_path", "That path cannot be edited.")
    if os.path.islink(p(path)):
        raise Reply("bad_path", "That path is a symbolic link.")
    return path


def op_edit(req):
    path, action = req.get("path"), req.get("action")
    if action not in ("append", "replace"):
        raise Reply("bad_request", "action must be append or replace.")
    memory = need_on(True)
    path = edit_path(path)
    agent, notices = req.get("agent"), []
    with Lock():
        exists = os.path.lexists(p(path))
        if action == "append":
            if not isinstance(req.get("text"), str):
                raise Reply("bad_request", "text is required.")
            write_file(path, lambda old: apply_body(old, req["text"])[0])
            change = "added text" if exists else "created the file"
        else:
            if not isinstance(req.get("old"), str) or not isinstance(req.get("new"), str):
                raise Reply("bad_request", "old and new are required.")
            if not exists:
                raise Reply("not_found", "No such file.")
            data = read_bytes(path)
            crlf = first_break_crlf(data)
            nl = "\r\n" if crlf else "\n"
            old_b = convert_breaks(req["old"], nl).encode()
            new_b = convert_breaks(req["new"], nl).encode()
            count = data.count(old_b)
            if count == 0:
                raise Reply("no_match", "That text is not in the file.")
            if count > 1:
                raise Reply("ambiguous", "That text occurs more than once.")
            write_file(path, lambda old: old.replace(old_b, new_b, 1))
            change = "replaced text"
    lines = journal([(path, change, "person direct", agent)], notices)
    return {"memory": memory, "journal": lines, "notices": notices}


def first_break_crlf(data):
    i = data.find(b"\n")
    return i > 0 and data[i - 1:i] == b"\r"


def op_forget(req):
    path = req.get("path")
    memory = need_on(True)
    path = edit_path(path)
    text, agent = req.get("text"), req.get("agent")
    notices = [] if bug("no_notice_forget") else [
        "Copies the model provider kept, and anything you already exported, cannot be deleted by this host."]
    with Lock():
        if not regular(p(path)):
            raise Reply("not_found", "No such file.")
        if text is None:
            os.unlink(p(path))
            removed, change = 1, "removed the file"
        else:
            segments = [s for s in re.split(r"(?<=\n)", read_bytes(path).decode("utf-8")) if s != ""]
            want = re.split(r"\r?\n", text.rstrip("\r\n"))
            keep, removed, i = [], 0, 0
            while i < len(segments):
                window = [s.rstrip("\r\n") for s in segments[i:i + len(want)]]
                if window == want:
                    removed += 1
                    i += len(want)
                else:
                    keep.append(segments[i])
                    i += 1
            if not removed:
                raise Reply("no_match", "That text does not fill whole lines in the file.")
            write_file(path, lambda old: "".join(keep).encode())
            change = "removed text"
    lines = journal([(path, change, "person direct", agent, text or "")], notices)
    return {"memory": memory, "removed": removed, "journal": lines, "notices": notices}


def op_policy(req):
    state, agent = req.get("state"), req.get("agent")
    if state not in ("on", "off"):
        raise Reply("bad_request", "state must be on or off.")
    if not regular(p("me.md")):
        raise Reply("absent", "There is no store (no me.md).")
    cur_state, spec_ok, obj = read_policy()
    if state == "on" and not spec_ok:
        raise Reply("unsupported_spec", "policy.json names a spec this host does not support.")
    notices = []
    with Lock():
        new = dict(obj) if isinstance(obj, dict) else {"spec": "0.1"}
        new["state"] = state
        write_file("policy.json", lambda old: (json.dumps(new, indent=1) + "\n").encode())
    CACHED.pop("policy", None)
    lines = []
    if not bug("no_policy_journal"):
        lines = journal([("policy.json", "turned memory %s" % state, "person direct", agent)], notices)
    memory, _ = status()
    return {"memory": memory, "journal": lines, "notices": notices}


OPS = {"host": op_host, "mount": op_mount, "list": op_list, "recall": op_recall, "pending": op_pending,
       "propose": op_propose, "decide": op_decide, "revise": op_revise, "edit": op_edit,
       "forget": op_forget, "policy": op_policy}


def handle(line):
    try:
        req = json.loads(line)
    except ValueError:
        return {"id": None, "ok": False, "error": "bad_request", "message": "Not JSON."}
    if not isinstance(req, dict) or "id" not in req or not isinstance(req.get("op"), str):
        return {"id": req.get("id") if isinstance(req, dict) else None, "ok": False, "error": "bad_request",
                "message": "A request needs id and op."}
    rid, op = req["id"], req["op"]
    if op not in OPS or OP_LEVEL[op] > LEVELS.index(OPTS["level"]):
        return {"id": rid, "ok": False, "error": "unsupported_op", "message": "Not supported at this level."}
    try:
        out = OPS[op](req)
        resp = {"id": rid, "ok": True}
        resp.update(out)
        return resp
    except Reply as r:
        resp = {"id": rid, "ok": False, "error": r.error, "message": r.message}
        if r.notices:
            resp["notices"] = r.notices
        return resp


def main(argv):
    i = 0
    while i < len(argv):
        if argv[i] == "--level":
            OPTS["level"] = argv[i + 1]
        elif argv[i] == "--name":
            OPTS["name"] = argv[i + 1]
        elif argv[i] == "--break":
            OPTS["break"] = set(argv[i + 1].split(","))
        i += 2
    for line in sys.stdin:
        if not line.strip():
            continue
        sys.stdout.write(json.dumps(handle(line)) + "\n")
        sys.stdout.flush()
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
