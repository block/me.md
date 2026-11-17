"""The thou v0.1 file formats (STORE.md): names, policy.json, proposals, journal entries.

Pure functions only. Nothing here touches the file system.
"""

import datetime
import json
import re
import unicodedata

SPEC = "0.1"

# Digits are written [0-9], never \d: in Python, \d also matches non-ASCII digits.
NAME_RE = re.compile(r"[a-z0-9][a-z0-9._-]{0,63}\.md")  # S2.1
ID_RE = re.compile(r"[0-9]{8}T[0-9]{6}Z-[a-z0-9]{4,47}")  # S6.1: at most 64 characters
TARGET_RE = re.compile(r"me\.md|(?:topics|projects)/[a-z0-9][a-z0-9._-]{0,63}\.md")
TIME_RE = re.compile(r"[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}Z")
KEY_RE = re.compile(r"([a-z][a-z-]*): (.*)", re.DOTALL)
BARE_KEY_RE = re.compile(r"([a-z][a-z-]*):\s*")
QUOTED_RE = re.compile(r'"((?:[^"\\]|\\["\\])*)"')
REQUIRED = ("status", "target", "proposed-by", "proposed-at", "basis")
STATUSES = ("pending", "accepted", "refused")


def now():
    """RFC 3339 UTC with Z and whole seconds (S7.1)."""
    return datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


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


def one_line(text):
    """Make a value safe for one front-matter line or one journal field."""
    return re.sub(r"\s+", " ", text.replace("|", "/")).strip()


# --- policy.json (S5) -------------------------------------------------------

class _Duplicate(ValueError):
    pass


def _strict(pairs):
    seen = set()
    for key, _ in pairs:
        if key in seen:
            raise _Duplicate(key)
        seen.add(key)
    return dict(pairs)


def _no_constant(name):
    raise ValueError(name + " is not JSON")


def parse_policy(data):
    """Decide on or off from the bytes of policy.json (S5.2-S5.4).

    Returns (state, reason, obj). obj is the parsed object when it is a valid
    JSON object with no repeated member, else None."""
    try:
        text = data.decode("utf-8")
        obj = json.loads(text, object_pairs_hook=_strict, parse_constant=_no_constant)
    except _Duplicate as exc:
        return "off", 'policy.json repeats the member "%s"' % exc, None
    except (UnicodeDecodeError, ValueError):
        return "off", "policy.json is not valid JSON", None
    if not isinstance(obj, dict):
        return "off", "policy.json is not a JSON object", None
    if obj.get("state") == "on":
        return "on", 'policy.json says "on"', obj
    if "state" not in obj:
        return "off", 'policy.json has no "state"', obj
    return "off", 'policy.json says "state": %s, and only "on" means on' % json.dumps(obj["state"]), obj


def spec_supported(obj):
    """S5.4: a missing spec means 0.1. Any other value is unsupported."""
    return obj is None or "spec" not in obj or obj["spec"] == SPEC


def policy_bytes(obj):
    return (json.dumps(obj, ensure_ascii=False, indent=2) + "\n").encode("utf-8")


# --- proposals (S6) ---------------------------------------------------------

class Proposal:
    """A parsed proposal file. Keeps the raw lines so a rewrite changes only what it must."""

    def __init__(self, name, data):
        self.name = name
        self.id = name[:-3] if name.endswith(".md") else name
        self.data = data
        self.fields = {}
        self.field_lines = {}  # key -> line index
        self.lines = []  # each line with its line break
        self.close = None  # index of the closing --- line
        self.body = None
        self.problems = []
        self._parse()

    @property
    def valid(self):
        return not self.problems

    @property
    def status(self):
        return self.fields.get("status") if self.valid else None

    def _parse(self):
        if not (self.name.endswith(".md") and ID_RE.fullmatch(self.name[:-3])):
            self.problems.append("the file name is not <YYYYMMDDTHHMMSSZ>-<4+ of a-z0-9>.md (S6.1)")
        elif not valid_time(self.id[:16], "%Y%m%dT%H%M%SZ"):
            self.problems.append("the file name does not start with a valid UTC time (S6.1)")
        try:
            text = self.data.decode("utf-8")
        except UnicodeDecodeError:
            self.problems.append("the file is not valid UTF-8 (S2.3)")
            self.body = self.data.decode("utf-8", "replace")
            return
        self.lines = split_lines(text) or [""]
        bare = [line.rstrip("\n").rstrip("\r") for line in self.lines]
        if bare[0] != "---":
            self.problems.append("line 1 is not exactly --- (S6.3)")
            self.body = text  # S6.14: the whole file
            return
        for index in range(1, len(bare)):
            if bare[index] == "---":
                self.close = index
                break
        if self.close is None:
            self.problems.append("the front matter has no closing --- line (S6.3)")
            self.body = text
            return
        for index in range(1, self.close):
            line = bare[index]
            if line.strip() == "" or line.startswith("#"):
                continue
            match = KEY_RE.fullmatch(line)
            if not match:
                if BARE_KEY_RE.fullmatch(line):
                    self.problems.append("line %d has a key with no value (S6.4)" % (index + 1))
                else:
                    self.problems.append("line %d is not `key: value` with a lowercase key (S6.4)" % (index + 1))
                continue
            key, raw = match.group(1), match.group(2).strip()
            if raw.startswith('"'):
                quoted = QUOTED_RE.fullmatch(raw)
                if not quoted:
                    self.problems.append("line %d has a bad quoted value (S6.4)" % (index + 1))
                    continue
                raw = re.sub(r'\\(["\\])', r"\1", quoted.group(1))
            if key in self.fields:
                self.problems.append("the key %s appears more than once (S6.4)" % key)
            self.fields[key] = raw
            self.field_lines[key] = index
        rest = self.lines[self.close + 1:]
        if rest and rest[0].strip("\r\n") == "":
            rest = rest[1:]  # S6.6: one blank line is skipped
        self.body = "".join(rest)
        if self.problems:
            return
        for key in REQUIRED:
            if self.fields.get(key, "") == "":
                self.problems.append("the required key %s is missing or empty (S6.4)" % key)
        if self.fields.get("status") and self.fields["status"] not in STATUSES:
            self.problems.append("status is not pending, accepted or refused (S6.4)")
        target = self.fields.get("target")
        if target and not TARGET_RE.fullmatch(target):
            self.problems.append("target is not me.md, topics/<name>.md or projects/<name>.md (S6.4, S4.2)")
        for key in ("proposed-at", "decided-at"):
            if self.fields.get(key) and not rfc3339(self.fields[key]):
                self.problems.append("%s is not a UTC time like 2026-11-12T17:03:01Z (S6.4)" % key)
        if normalize(self.body) == "":
            self.problems.append("the body is empty (S6.6)")

    def summary(self):
        return {
            "id": self.id,
            "file": "proposals/" + self.name,
            "target": self.fields["target"],
            "proposed-by": self.fields["proposed-by"],
            "proposed-at": self.fields["proposed-at"],
            "basis": self.fields["basis"],
            "body": self.body,
        }

    def decided(self, status, when, via):
        """The file with status set and decided-at, decided-via after it. Other lines stay byte for byte (S6.5)."""
        lines = list(self.lines)
        index = self.field_lines["status"]
        eol = _eol_of(lines[index]) or _eol_of(lines[0]) or "\n"
        lines[index] = "status: " + status + eol
        extra = []
        for key, value in (("decided-at", when), ("decided-via", via)):
            if key in self.field_lines:
                at = self.field_lines[key]
                lines[at] = key + ": " + value + (_eol_of(lines[at]) or eol)
            else:
                extra.append(key + ": " + value + eol)
        lines[index + 1:index + 1] = extra
        return "".join(lines).encode("utf-8")

    def revised(self, body):
        """The file with a new body. The front matter and the blank line after it stay byte for byte."""
        head = self.lines[:self.close + 1]
        rest = self.lines[self.close + 1:]
        eol = _eol_of(head[-1]) or "\n"
        if rest and rest[0].strip("\r\n") == "":
            head.append(rest[0])
        elif not _eol_of(head[-1]):
            head[-1] += eol
        text = eol.join(body_lines(body))
        return ("".join(head) + text + eol).encode("utf-8")


def split_lines(text):
    """Split on LF only, keeping each line break. str.splitlines also splits on other characters."""
    return re.findall(r"[^\n]*\n|[^\n]+\Z", text)


def _eol_of(line):
    if line.endswith("\r\n"):
        return "\r\n"
    if line.endswith("\n"):
        return "\n"
    return ""


def body_lines(text):
    """The lines of a body, with its final line breaks removed (S6.8 step 1)."""
    return re.sub(r"(\r?\n)+\Z", "", text).replace("\r\n", "\n").split("\n")


def new_proposal(target, body, basis, proposed_by, when):
    def value(text):
        text = one_line(text)
        if text.startswith('"') or text != text.strip():
            text = '"' + text.replace("\\", "\\\\").replace('"', '\\"') + '"'
        return text
    head = ["---", "status: pending", "target: " + target, "proposed-by: " + value(proposed_by),
            "proposed-at: " + when, "basis: " + value(basis), "---", ""]
    return ("\n".join(head + body_lines(body)) + "\n").encode("utf-8")


# --- appending text (S6.8) --------------------------------------------------

def line_break_of(data):
    """The target's line break: CRLF if its first line break is CRLF, LF otherwise."""
    at = data.find(b"\n")
    return b"\r\n" if at > 0 and data[at - 1:at] == b"\r" else b"\n"


def as_target_text(text, data):
    """Text with its final line breaks removed and its line breaks written the way data uses them."""
    eol = line_break_of(data or b"")
    return eol.join(line.encode("utf-8") for line in body_lines(text)), eol


def appended(data, text):
    """S6.8: the target's new bytes, or None when the text is already at its end."""
    if data is None:
        return b"\n".join(line.encode("utf-8") for line in body_lines(text)) + b"\n"
    chunk, eol = as_target_text(text, data)
    whole = chunk + eol
    if data == whole or (data.endswith(whole) and data[:-len(whole)].endswith(b"\n")):
        return None
    if data and not data.endswith(b"\n"):
        data += eol
    return data + whole


def without_lines(data, text):
    """Remove each place where text fills whole lines, with its line break. Returns (bytes, count)."""
    chunk, _ = as_target_text(text, data)
    if not chunk:
        return data, 0
    out, count, start = bytearray(), 0, 0
    at = data.find(chunk)
    while at != -1:
        end = at + len(chunk)
        starts_line = at == 0 or data[at - 1:at] == b"\n"
        if data[end:end + 2] == b"\r\n":
            stop = end + 2
        elif data[end:end + 1] == b"\n" or end == len(data):
            stop = end + (1 if end < len(data) else 0)
        else:
            stop = None
        if starts_line and stop is not None:
            out += data[start:at]
            start = stop
            count += 1
            at = data.find(chunk, stop)
        else:
            at = data.find(chunk, at + 1)
    out += data[start:]
    return bytes(out), count


# --- journal (S7) -----------------------------------------------------------

def journal_entry(path, change, host, authority, when=None):
    return "- %s | %s | %s | host: %s | authority: %s" % (when or now(), path, one_line(change),
                                                        one_line(host), authority)
