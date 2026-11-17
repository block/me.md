#!/usr/bin/env python3
"""me-lint: a static validator for a me.md v0.1 store (STORE.md).

It checks that the files in a store follow the v0.1 format. It is not a host.
It never writes, never follows symlinks inside the store, and never reads
`.git/` or unknown top-level entries. Standard library only.

Usage: python3 me_lint.py <store-dir> [--json]
Exit:  0 no errors, 1 errors found, 2 usage error.
"""

import argparse
import datetime
import json
import os
import re
import stat
import sys
import unicodedata

# Digits are written [0-9], never \d: in Python, \d also matches non-ASCII digits.
NAME = r"[a-z0-9][a-z0-9._-]{0,63}\.md"
NAME_RE = re.compile(NAME)
NAME_RULE = "[a-z0-9][a-z0-9._-]*.md, at most 64 characters before .md"
PROPOSAL_RULE = "<id>.md, id = YYYYMMDDTHHMMSSZ-xxxx (4+ of [a-z0-9])"
ID = r"[0-9]{8}T[0-9]{6}Z-[a-z0-9]{4,47}"  # the id has capitals (T, Z), so proposals get their own name rule
PROPOSAL_NAME_RE = re.compile(ID + r"\.md")
ANY_MD_RE = re.compile(r".+\.md", re.DOTALL)  # S2.1: any .md name in proposals/ is a proposal, valid or not
TIME_RE = re.compile(r"[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}Z")
KEY_RE = re.compile(r"([a-z][a-z-]*): (.*)")
BARE_KEY_RE = re.compile(r"([a-z][a-z-]*):\s*")
QUOTED_RE = re.compile(r'"((?:[^"\\]|\\["\\])*)"')
TARGET_RE = re.compile(r"me\.md|(?:topics|projects)/" + NAME)
JOURNAL_PATH_RE = re.compile(r"-|me\.md|watches\.md|policy\.json|(?:topics|projects)/" + NAME
                             + "|proposals/" + ID + r"\.md")
AUTHORITY_RE = re.compile(r"person direct|external edit|accepted proposal " + ID)
SUPPORTED_SPECS = ("0.1",)  # before 1.0, each minor version is its own format (S5.4)
STATUSES = ("pending", "accepted", "refused")
REQUIRED = ("status", "target", "proposed-by", "proposed-at", "basis")
LOCK = ".me.lock"


class Report:
    def __init__(self):
        self.errors, self.warnings, self.notes = [], [], []
        self.present = False
        self.policy = None
        self.counts = {}

    def add(self, bucket, path, message):
        bucket.append({"path": path, "message": message})

    def error(self, path, message):
        self.add(self.errors, path, message)

    def warn(self, path, message):
        self.add(self.warnings, path, message)

    def note(self, path, message):
        self.add(self.notes, path, message)


class DuplicateMember(ValueError):
    pass


def valid_time(text, fmt, pattern=None):
    if pattern is not None and not pattern.fullmatch(text):
        return False
    try:
        datetime.datetime.strptime(text, fmt)
    except ValueError:
        return False
    return True


def rfc3339(text):
    return valid_time(text, "%Y-%m-%dT%H:%M:%SZ", TIME_RE)


def normalize(text):
    """S6.11: Unicode NFC, trim, and collapse each run of white space to one space."""
    return re.sub(r"\s+", " ", unicodedata.normalize("NFC", text)).strip()


def read_text(rep, root, rel):
    """Return the text of a regular file, or None after reporting why not.

    Uses lstat, so a symlink is reported and never followed."""
    path = os.path.join(root, rel)
    try:
        mode = os.lstat(path).st_mode
    except OSError as exc:
        rep.error(rel, "cannot stat: %s" % exc.strerror)
        return None
    if stat.S_ISLNK(mode):
        rep.error(rel, "symlink inside the store (hosts must not follow it)")
        return None
    if not stat.S_ISREG(mode):
        rep.error(rel, "not a regular file")
        return None
    try:
        with open(path, "rb") as handle:
            data = handle.read()
    except OSError as exc:
        rep.error(rel, "cannot read: %s" % exc.strerror)
        return None
    if data.startswith(b"\xef\xbb\xbf"):
        rep.error(rel, "starts with a UTF-8 BOM (must be UTF-8 without BOM)")
        return None
    try:
        return data.decode("utf-8")
    except UnicodeDecodeError:
        rep.error(rel, "not valid UTF-8")
        return None


def strict_object(pairs):
    seen = set()
    for key, _ in pairs:
        if key in seen:
            raise DuplicateMember(key)
        seen.add(key)
    return dict(pairs)


def reject_constant(name):
    raise ValueError("%s is not JSON" % name)


def check_policy(rep, root):
    """Fill rep.policy, following STORE.md §5."""
    rel = "policy.json"
    policy = {"state": "on", "reason": "no policy.json (default on)", "spec": None, "writable": True}
    rep.policy = policy
    path = os.path.join(root, rel)
    if not os.path.lexists(path):
        return

    def off(why):
        policy["state"] = "off"
        policy["reason"] = why
        rep.warn(rel, "%s; hosts treat memory as off" % why)

    if os.path.islink(path):
        return off("policy.json is a symbolic link")
    text = read_text(rep, root, rel)
    if text is None:
        policy["state"], policy["reason"] = "off", "policy.json cannot be read"
        return
    try:
        data = json.loads(text, object_pairs_hook=strict_object, parse_constant=reject_constant)
    except DuplicateMember as exc:
        return off("policy.json has the member %s more than once" % json.dumps(exc.args[0]))
    except (ValueError, RecursionError):
        return off("policy.json is not valid JSON")
    if not isinstance(data, dict):
        return off("policy.json is not a JSON object")
    if "state" not in data:
        return off("policy.json has no state")
    if data["state"] == "off":
        policy["state"], policy["reason"] = "off", 'state is "off"'
        rep.note(rel, "memory is off by the person's choice")
    elif data["state"] == "on":
        policy["reason"] = 'state is "on"'
    else:
        return off('state must be exactly "on" or "off"')

    if "spec" not in data:
        rep.note(rel, 'no spec: hosts read the store as version 0.1 '
                      '(a host that creates policy.json should write "spec": "0.1")')
        return
    spec = data["spec"]
    policy["spec"] = spec
    if spec not in SUPPORTED_SPECS:
        policy["writable"] = False
        shown = spec if isinstance(spec, str) else json.dumps(spec)
        rep.warn(rel, "spec %s is not a version v0.1 hosts support; hosts must not write to "
                      "this store, except to turn memory off" % shown)


def list_entries(rep, root, folder, name_re, name_rule):
    """Return the valid-named regular entries of a folder. Reports the rest."""
    path = os.path.join(root, folder)
    try:
        mode = os.lstat(path).st_mode
    except OSError:
        return []
    if stat.S_ISLNK(mode):
        rep.error(folder, "symlink inside the store (hosts must not follow it)")
        return []
    if not stat.S_ISDIR(mode):
        rep.error(folder, "expected a directory")
        return []
    found = []
    for name in sorted(os.listdir(path)):
        rel = folder + "/" + name
        if name.startswith("."):
            continue
        mode = os.lstat(os.path.join(path, name)).st_mode
        if stat.S_ISLNK(mode):
            rep.error(rel, "symlink inside the store (hosts must not follow it)")
        elif not name_re.fullmatch(name):
            rep.warn(rel, "ignored by hosts: name must match " + name_rule)
        elif not stat.S_ISREG(mode):
            rep.warn(rel, "ignored by hosts: not a regular file")
        else:
            found.append(name)
    return found


def parse_front_matter(text):
    """Return (fields, body, problems), following STORE.md S6.3 to S6.6.

    body is None when there is no closed front matter."""
    lines = text.split("\n")
    fields, problems = {}, []
    if lines[0].rstrip("\r") != "---":
        return fields, None, ["front matter must start with --- on line 1"]
    close = None
    for index in range(1, len(lines)):
        if lines[index].rstrip("\r") == "---":
            close = index
            break
    if close is None:
        return fields, None, ["front matter is not closed by a line that is exactly ---"]
    for number in range(1, close):
        line = lines[number].rstrip("\r")
        if line.strip() == "" or line.startswith("#"):
            continue
        match = KEY_RE.fullmatch(line)
        if not match:
            bare = BARE_KEY_RE.fullmatch(line)
            if bare:
                problems.append("line %d: %s has no value" % (number + 1, bare.group(1)))
            else:
                problems.append("line %d: expected `key: value` with a lowercase key" % (number + 1))
            continue
        key, raw = match.group(1), match.group(2).strip()
        if raw.startswith('"'):
            quoted = QUOTED_RE.fullmatch(raw)
            if not quoted:
                problems.append("line %d: bad quoted value for %s (only \\\" and \\\\ escapes)" % (number + 1, key))
                continue
            raw = re.sub(r'\\(["\\])', r"\1", quoted.group(1))
        if key in fields:
            problems.append("line %d: duplicate key %s" % (number + 1, key))
        fields[key] = raw
    return fields, "\n".join(lines[close + 1:]), problems


def check_proposal(rep, root, name):
    """Check one proposal. Return a record for the cross-file checks."""
    rel = "proposals/" + name
    pid = name[:-3]
    record = {"name": name, "id": pid, "valid": False, "fields": {}, "body": None}
    before = len(rep.errors)
    if not PROPOSAL_NAME_RE.fullmatch(name):
        rep.error(rel, "name must be %s; hosts treat this file as an invalid proposal (S6.14)" % PROPOSAL_RULE)
    elif not valid_time(pid[:16], "%Y%m%dT%H%M%SZ"):
        rep.error(rel, "filename id does not start with a valid UTC time")
    text = read_text(rep, root, rel)
    if text is None:
        return record
    fields, body, problems = parse_front_matter(text)
    record["fields"] = fields
    record["body"] = text if body is None else body  # S6.14: the whole file when there is no front matter
    for problem in problems:
        rep.error(rel, "front matter: " + problem)
    if not problems:
        check_fields(rep, rel, fields)
        if normalize(body) == "":
            rep.error(rel, "body is empty (the body is the proposed content)")
        if re.search(r"^status:", body, re.MULTILINE):
            rep.note(rel, "body contains a status-like line; only front matter counts")
    record["valid"] = len(rep.errors) == before
    if record["valid"]:
        key = "proposals_" + fields["status"]
        rep.counts[key] = rep.counts.get(key, 0) + 1
    else:
        rep.counts["proposals_invalid"] += 1
    return record


def check_fields(rep, rel, fields):
    for key in REQUIRED:
        if key not in fields:
            rep.error(rel, "missing required key: " + key)
        elif fields[key] == "":
            rep.error(rel, "required key is empty: " + key)
    status = fields.get("status")
    if status and status not in STATUSES:
        rep.error(rel, "status must be one of pending, accepted, refused")
    target = fields.get("target")
    if target == "watches.md":
        rep.error(rel, "target must not be watches.md (hosts never add watches)")
    elif target and not TARGET_RE.fullmatch(target):
        rep.error(rel, "target must be me.md, topics/<name>.md or projects/<name>.md")
    for key in ("proposed-at", "decided-at"):
        if fields.get(key) and not rfc3339(fields[key]):
            rep.error(rel, "%s must be RFC 3339 UTC like 2026-11-12T17:03:01Z" % key)


def check_refusals(rep, records):
    """S6.11 and S6.14: a pending body must not equal a refused or invalid one, for any target."""
    refused = [r for r in records if r["body"] is not None
               and (not r["valid"] or r["fields"]["status"] == "refused")]
    for record in records:
        if not record["valid"] or record["fields"]["status"] != "pending":
            continue
        rel = "proposals/" + record["name"]
        body = normalize(record["body"])
        for other in refused:
            if other is record or normalize(other["body"]) != body:
                continue
            if not other["valid"]:
                rep.warn(rel, "same body as invalid proposal %s, which hosts treat as refused (S6.14)"
                         % other["name"])
                continue
            refused_at = other["fields"].get("decided-at") or other["fields"]["proposed-at"]
            if record["fields"]["proposed-at"] > refused_at:
                rep.error(rel, "proposes again the body of refused proposal %s (S6.11)" % other["name"])
            else:
                rep.warn(rel, "same body as refused proposal %s, proposed before that refusal"
                         % other["name"])


def check_decisions(rep, records, entries):
    """S7.3: every decision, and the content change of every acceptance, has a journal entry."""
    for record in records:
        status = record["fields"].get("status") if record["valid"] else None
        if status not in ("accepted", "refused"):
            continue
        rel = "proposals/" + record["name"]
        if not any(e["path"] == rel and e["change"] == status and e["authority"] == "person direct"
                   for e in entries):
            rep.warn(rel, "no journal entry records this decision (S7.3); "
                          "expected only if the person edited the file by hand")
        if status == "accepted" and not any(e["authority"] == "accepted proposal " + record["id"]
                                            for e in entries):
            rep.warn(rel, "no journal entry records the change this proposal made (S7.3)")


def check_journal(rep, root):
    """Return the well-formed entries. S7.4: every line that starts with '- ' is an entry."""
    entries = []
    text = read_text(rep, root, "journal.md")
    if text is None:
        return entries
    for number, line in enumerate(text.split("\n"), 1):
        line = line.rstrip("\r")
        if not line.startswith("- "):
            continue
        rep.counts["journal_entries"] += 1
        parts = line[2:].split(" | ")
        problem = journal_problem(parts)
        if problem:
            rep.error("journal.md", "line %d: %s" % (number, problem))
        else:
            entries.append({"path": parts[1], "change": parts[2], "authority": parts[4][len("authority: "):]})
    if text and not text.endswith("\n"):
        rep.note("journal.md", "does not end with a line break; the next entry must start with one (S8.1)")
    return entries


def journal_problem(parts):
    if len(parts) != 5:
        return "expected 5 fields separated by ' | ', found %d" % len(parts)
    when, path, change, host, authority = parts
    if any("|" in part for part in parts):
        return "a field contains '|'"
    if not rfc3339(when):
        return "time must be RFC 3339 UTC with Z, like 2026-11-12T17:03:01Z"
    if not JOURNAL_PATH_RE.fullmatch(path):
        return "path must be '-' or a store-relative file path"
    if change.strip() == "":
        return "change is empty"
    if not host.startswith("host: ") or host[6:].strip() == "":
        return "host field must be 'host: <name>'"
    if not authority.startswith("authority: ") or not AUTHORITY_RE.fullmatch(authority[11:]):
        return "authority must be person direct, external edit, or accepted proposal <id>"
    return None


def count_watches(text):
    """S4.1: top-level list items outside fenced code blocks."""
    count, fence = 0, None
    for line in text.split("\n"):
        line = line.rstrip("\r")
        if line.startswith(("```", "~~~")):
            if fence is None:
                fence = line[:3]
            elif line.startswith(fence):
                fence = None
            continue
        if fence is None and line.startswith(("- ", "* ")):
            count += 1
    return count


def lint(root):
    rep = Report()
    rep.counts = {"topics": 0, "projects": 0, "proposals": 0, "proposals_pending": 0,
                  "proposals_accepted": 0, "proposals_refused": 0, "proposals_invalid": 0,
                  "watches": 0, "journal_entries": 0}
    me_path = os.path.join(root, "me.md")
    if not os.path.lexists(me_path):
        rep.note(".", "store absent: no me.md (a normal state; hosts behave as if no store exists)")
        return rep
    if os.path.islink(me_path):
        rep.warn("me.md", "me.md is a symbolic link, so hosts treat the store as absent "
                          "(link the whole store instead)")
        return rep
    rep.present = True
    check_policy(rep, root)
    read_text(rep, root, "me.md")
    if os.path.lexists(os.path.join(root, LOCK)):
        rep.note(LOCK, "the store lock exists: a host is writing, or one stopped without removing it. "
                       "If no host is writing, the person can delete it (S8.3)")
    for folder in ("topics", "projects"):
        names = list_entries(rep, root, folder, NAME_RE, NAME_RULE)
        rep.counts[folder] = len(names)
        for name in names:
            read_text(rep, root, folder + "/" + name)
    names = list_entries(rep, root, "proposals", ANY_MD_RE, "<name>.md")
    rep.counts["proposals"] = len(names)
    records = [check_proposal(rep, root, name) for name in names]
    if os.path.lexists(os.path.join(root, "watches.md")):
        text = read_text(rep, root, "watches.md")
        if text is not None:
            rep.counts["watches"] = count_watches(text)
    entries = []
    if os.path.lexists(os.path.join(root, "journal.md")):
        entries = check_journal(rep, root)
    check_refusals(rep, records)
    check_decisions(rep, records, entries)
    return rep


def render(rep):
    lines = []
    for label, bucket in (("ERROR", rep.errors), ("WARN", rep.warnings), ("NOTE", rep.notes)):
        lines.extend("%s %s: %s" % (label, f["path"], f["message"]) for f in bucket)
    if rep.present:
        lines.append("me-lint: policy %s, %d error(s), %d warning(s)"
                     % (rep.policy["state"], len(rep.errors), len(rep.warnings)))
    return lines


def main(argv=None):
    parser = argparse.ArgumentParser(description="Validate a me.md v0.1 store (static; not a host).")
    parser.add_argument("store", help="path to the store directory (the ME_HOME or ~/.me directory)")
    parser.add_argument("--json", action="store_true", help="print a JSON report")
    args = parser.parse_args(argv)
    if not os.path.isdir(args.store):
        print("me-lint: not a directory: %s" % args.store, file=sys.stderr)
        return 2
    rep = lint(args.store)
    if args.json:
        print(json.dumps({"present": rep.present, "policy": rep.policy, "errors": rep.errors,
                          "warnings": rep.warnings, "notes": rep.notes, "counts": rep.counts},
                         indent=2, sort_keys=True))
    else:
        print("\n".join(render(rep)))
    return 1 if rep.errors else 0


if __name__ == "__main__":
    sys.exit(main())
