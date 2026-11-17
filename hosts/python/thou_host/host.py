"""The host: every operation a thou v0.1 host does, at the Steward level (HOST.md, STORE.md).

Each public method returns a dict for a successful answer, or raises HostError.
The driver, the MCP server and the Claude Code hooks all call these methods,
so the rules live in one place.
"""

import json
import os
import secrets
import time

from . import formats
from .formats import Proposal, normalize
from .storefs import Locked, Missing, StoreFS, location

NAME = "thou-py"
VERSION = "0.1.0"
LEVEL = "steward"

_RECALL_PURPOSES = ("task", "briefing", "watches")
_ID_CHARS = "abcdefghijklmnopqrstuvwxyz0123456789"

PROVIDER_NOTICE = ("I removed it from the store and from this host's memory. I can't delete copies outside "
                   "the store: saved agent sessions and the model provider may keep what earlier sessions "
                   "read, and backups, sync folders or exported copies keep their own.")
OFF_NOTICE = ("Memory is off. This host enforces that in its own code. Another agent on this machine "
              "follows it only if it honors policy.json.")


class HostError(Exception):
    def __init__(self, code, message, notices=()):
        Exception.__init__(self, message)
        self.code, self.message, self.notices = code, message, list(notices)


class Host:
    def __init__(self, root=None, agent=None):
        self.root = root or location()
        self.fs = StoreFS(self.root)
        self.agent = agent
        self.session = {}  # session cache only (H1.3); cleared by forget (H5.2)

    # --- who and where ---

    def who(self, agent=None):
        """The journal's <host> field: name, version, and the agent if known (S7.1, H4.3)."""
        agent = formats.one_line(agent or self.agent or "").replace("(", "").replace(")", "")
        return "%s %s" % (NAME, VERSION) + (" (%s)" % agent if agent else "")

    def host(self):
        return {"name": NAME, "version": VERSION, "spec": formats.SPEC, "level": LEVEL, "enforcement": "code"}

    # --- on, off, absent (H1.5, S1.2, S5) ---

    def state(self):
        """Read policy.json alone and decide, then check for me.md. Never opens another file."""
        kind = self.fs.kind("policy.json")
        obj = None
        if kind == "link":
            return self._off("policy.json is a symbolic link")
        if kind == "other":
            return self._off("policy.json cannot be read")
        if kind == "file":
            try:
                data = self.fs.read("policy.json")
            except Missing:
                return self._off("policy.json cannot be read")
            state, reason, obj = formats.parse_policy(data)
            if state == "off":
                return self._off(reason)
        me = self.fs.kind("me.md")
        if me != "file":
            notices = []
            if me == "link":
                notices.append("me.md is a symbolic link, so the store counts as absent (S2.4). "
                               "A link to the whole store folder works instead.")
            return {"memory": "absent", "notices": notices, "obj": obj}
        writable = formats.spec_supported(obj)
        notices = []
        if not writable:
            notices.append(self._spec_message(obj))
        return {"memory": "on", "writable": writable, "notices": notices, "obj": obj}

    def _off(self, reason):
        return {"memory": "off", "notices": ["Memory is off: %s." % reason], "obj": None}

    def _spec_message(self, obj):
        return ("policy.json says this store follows spec %s. This host supports only %s, so it will not "
                "write to the store, except to turn memory off (S5.4)." % (json.dumps(obj.get("spec")), formats.SPEC))

    def _answer(self, s, **fields):
        out = {"memory": s["memory"]}
        if s["memory"] == "on" and not s["writable"]:
            out["writable"] = False
        out.update(fields)
        if s["notices"]:
            out["notices"] = list(s["notices"]) + list(out.get("notices", []))
        return out

    def _writable(self):
        s = self.state()
        if s["memory"] == "absent":
            raise HostError("absent", "There is no store at %s, so I wrote nothing." % self.root, s["notices"])
        if s["memory"] == "off":
            raise HostError("memory_off", s["notices"][0] + " I wrote nothing.")
        if not s["writable"]:
            raise HostError("unsupported_spec", s["notices"][0])
        return s

    def _lock(self, agent):
        try:
            return self.fs.lock(self.who(agent))
        except Locked as exc:
            raise HostError("locked", str(exc), [str(exc)])

    def _journal(self, entries, notices):
        written = []
        for entry in entries:
            if self.fs.journal(entry):
                written.append(entry)
            else:
                notices.append("The change happened, but I could not write its journal entry, so it has "
                               "no receipt (S8.7).")
        return written

    def _decode(self, rel, data, notices):
        if data.startswith(b"\xef\xbb\xbf"):
            notices.append("%s starts with a byte order mark. thou files are UTF-8 without one (S2.3)." % rel)
            data = data[3:]
        return data.decode("utf-8")

    # --- Reader ---

    def mount(self):
        s = self.state()
        files, notices = [], []
        if s["memory"] == "on":
            try:
                text = self._decode("me.md", self.fs.read("me.md"), notices)
                files.append({"path": "me.md", "text": text})
                self.session["me.md"] = text
            except (Missing, UnicodeDecodeError) as exc:
                notices.append("I could not read me.md: %s." % getattr(exc, "why", "it is not valid UTF-8"))
        return self._answer(s, store=self.root, files=files, notices=notices)

    def where(self):
        s = self.state()
        return self._answer(s, store=self.root)

    def list(self):
        s = self.state()
        out = {"topics": [], "projects": [], "watches": False}
        notices = []
        if s["memory"] == "on":
            for folder in ("topics", "projects"):
                names, more = self.fs.listdir(folder)
                notices += more
                for name in names:
                    if formats.NAME_RE.fullmatch(name):
                        out[folder].append(name)
                    else:
                        notices.append("I ignore %s/%s because of its name. Names are lowercase letters, digits, "
                                       "., _ and -, ending in .md (S2.1)." % (folder, name))
            out["watches"] = self.fs.kind("watches.md") == "file"
        return self._answer(s, notices=notices, **out)

    def recall(self, paths, purpose="task"):
        if purpose not in _RECALL_PURPOSES:
            raise HostError("bad_request", "purpose is task, briefing or watches.")
        if not isinstance(paths, list):
            raise HostError("bad_request", "paths is a list of store paths.")
        s = self.state()  # H1.6: policy.json again before each recall
        files, skipped, notices = [], [], []
        for path in paths:
            reason = None
            if s["memory"] != "on":
                reason = "memory is %s" % s["memory"]
            elif not isinstance(path, str) or not (path == "watches.md" or formats.TARGET_RE.fullmatch(path)):
                reason = "not a file a host recalls: me.md, watches.md, topics/<name>.md or projects/<name>.md"
            elif path == "watches.md" and purpose == "task":
                reason = "watches.md is read only for a briefing or when you ask about your watches (S4.3)"
            if reason is None:
                try:
                    text = self._decode(path, self.fs.read(path), notices)
                    files.append({"path": path, "text": text})
                    continue
                except Missing as exc:
                    reason = exc.why
                except UnicodeDecodeError:
                    reason = "it is not valid UTF-8"
            skipped.append({"path": path, "reason": reason})
        return self._answer(s, files=files, skipped=skipped, notices=notices)

    # --- Proposer ---

    def _proposals(self):
        """[(name, Proposal or None)] for every .md entry in proposals/, and notices."""
        names, notices = self.fs.listdir("proposals")
        out = []
        for name in names:
            if not name.endswith(".md"):
                notices.append("I ignore proposals/%s because it does not end in .md (S2.1)." % name)
                continue
            try:
                out.append(Proposal(name, self.fs.read("proposals/" + name)))
            except Missing:
                continue
        return out, notices

    def pending(self):
        s = self.state()
        proposals, invalid, notices = [], [], []
        if s["memory"] == "on":
            found, notices = self._proposals()
            for p in found:
                if not p.valid:
                    invalid.append({"file": "proposals/" + p.name, "reason": "; ".join(p.problems)})
                elif p.status == "pending":
                    proposals.append(p.summary())
        return self._answer(s, proposals=proposals, invalid=invalid, notices=notices)

    def propose(self, target, body, basis, agent=None):
        self._writable()
        if not isinstance(target, str) or not formats.TARGET_RE.fullmatch(target):
            raise HostError("bad_target", "A proposal targets me.md, topics/<name>.md or projects/<name>.md "
                                          "(S6.4). It never targets watches.md (S4.2).")
        if not isinstance(body, str) or normalize(body) == "":
            raise HostError("empty_body", "The proposal has no words to keep (S6.6).")
        if not isinstance(basis, str) or formats.one_line(basis) == "":
            raise HostError("bad_request", "A proposal needs a basis: why, in words the person will recognize.")
        wanted = normalize(body)
        found, _ = self._proposals()  # H3.3: read the refusals first
        for p in found:
            if (not p.valid or p.status == "refused") and normalize(p.body or "") == wanted:
                why = "refused" if p.valid else "invalid, which counts as refused (S6.14)"
                raise HostError("refused", "You refused these words before (proposals/%s is %s), so I will not "
                                           "propose them again (S6.11)." % (p.name, why))
        for _ in range(20):
            stamp = time.gmtime()
            pid = time.strftime("%Y%m%dT%H%M%SZ", stamp) + "-" + "".join(
                secrets.choice(_ID_CHARS) for _ in range(6))
            data = formats.new_proposal(target, body, basis, self.who(agent),
                                        time.strftime("%Y-%m-%dT%H:%M:%SZ", stamp))
            try:
                self.fs.create("proposals/%s.md" % pid, data)  # S6.2, S8.5: exclusive, no lock
            except FileExistsError:
                continue
            except Missing as exc:
                raise HostError("bad_request", "I could not create the proposal: %s." % exc.why)
            s = self.state()
            return self._answer(s, proposal=pid, file="proposals/%s.md" % pid)
        raise HostError("bad_request", "I could not find a free proposal name.")

    # --- Steward ---

    def _proposal_path(self, pid):
        if not isinstance(pid, str) or not formats.ID_RE.fullmatch(pid):
            raise HostError("not_found", "There is no proposal %r." % (pid,))
        return "proposals/%s.md" % pid

    def _read_pending(self, rel):
        try:
            data = self.fs.read(rel)
        except Missing as exc:
            raise HostError("not_found", "I could not read %s: %s." % (rel, exc.why))
        p = Proposal(rel.split("/", 1)[1], data)
        if not p.valid:
            message = "%s is invalid, so I will not apply or change it: %s." % (rel, "; ".join(p.problems))
            raise HostError("invalid_proposal", message, [message])
        if p.status != "pending":
            raise HostError("not_pending", "%s was already %s." % (rel, p.status))
        return data, p

    def decide(self, proposal, decision, agent=None):
        """S8.6, in order: lock, check, apply, set status, unlock, journal."""
        if decision not in ("accept", "refuse"):
            raise HostError("bad_request", "decision is accept or refuse.")
        self._writable()
        rel = self._proposal_path(proposal)
        who = self.who(agent)
        notices, applied = [], None
        token = self._lock(agent)
        try:
            data, p = self._read_pending(rel)
            target = p.fields["target"]
            status = "accepted" if decision == "accept" else "refused"
            if status == "accepted":
                try:
                    _, new = self.fs.replace(target, lambda old: formats.appended(old, p.body))
                except Missing as exc:
                    raise HostError("bad_target", "I will not write %s: %s." % (target, exc.why))
                applied = "added" if new is not None else "already"

            def mark(old):
                q = Proposal(p.name, old) if old is not None else None
                if q is None or not q.valid or q.status != "pending":
                    notices.append("%s changed while I was deciding it, so I left its status alone." % rel)
                    return None
                return q.decided(status, formats.now(), who)
            self.fs.replace(rel, mark)
        finally:
            self.fs.unlock(token)
        when = formats.now()
        entries = [formats.journal_entry(rel, status, who, "person direct", when)]
        if status == "accepted":
            entries.append(formats.journal_entry(target, "added the text of an accepted proposal", who,
                                                 "accepted proposal " + p.id, when))
        journal = self._journal(entries, notices)
        return self._answer(self.state(), status=status, applied=applied, journal=journal, notices=notices)

    def revise(self, proposal, body, agent=None):
        """S6.15: the person changes a pending body. Not journaled (S6.13)."""
        self._writable()
        if not isinstance(body, str) or normalize(body) == "":
            raise HostError("empty_body", "The new body has no words (S6.6).")
        rel = self._proposal_path(proposal)
        token = self._lock(agent)
        try:
            data, p = self._read_pending(rel)
            self.fs.replace(rel, lambda old: Proposal(p.name, old).revised(body) if old == data else None)
        finally:
            self.fs.unlock(token)
        return self._answer(self.state())

    def _editable(self, path):
        if not isinstance(path, str) or not (path == "watches.md" or formats.TARGET_RE.fullmatch(path)):
            raise HostError("bad_path", "I change only me.md, watches.md, topics/<name>.md and projects/<name>.md.")
        return path

    def edit(self, path, action, text=None, old=None, new=None, agent=None):
        """H3.7: an edit the person asked for, journaled as person direct."""
        self._writable()
        path = self._editable(path)
        who = self.who(agent)
        notices = []
        if action == "append":
            if not isinstance(text, str) or normalize(text) == "":
                raise HostError("bad_request", "append needs text.")
            token = self._lock(agent)
            try:
                before, after = self.fs.replace(path, lambda data: formats.appended(data, text))
            except Missing as exc:
                raise HostError("bad_path", "I will not write %s: %s." % (path, exc.why))
            finally:
                self.fs.unlock(token)
            if after is None:
                notices.append("Those words are already at the end of %s, so I changed nothing." % path)
                return self._answer(self.state(), journal=[], notices=notices)
            change = "created the file" if before is None else "added text"
        elif action == "replace":
            if not isinstance(old, str) or old == "" or not isinstance(new, str):
                raise HostError("bad_request", "replace needs old and new.")
            token = self._lock(agent)
            try:
                if self.fs.kind(path) == "missing":
                    raise HostError("not_found", "%s does not exist." % path)

                def swap(data):
                    if data is None:
                        raise HostError("not_found", "%s does not exist." % path)
                    eol = formats.line_break_of(data)
                    a = old.replace("\r\n", "\n").encode("utf-8").replace(b"\n", eol)
                    b = new.replace("\r\n", "\n").encode("utf-8").replace(b"\n", eol)
                    count = data.count(a)
                    if count == 0:
                        raise HostError("no_match", "Those words are not in %s." % path)
                    if count > 1:
                        raise HostError("ambiguous", "Those words appear %d times in %s." % (count, path))
                    return data.replace(a, b)
                _, after = self.fs.replace(path, swap)
            except Missing as exc:
                raise HostError("bad_path", "I will not write %s: %s." % (path, exc.why))
            finally:
                self.fs.unlock(token)
            if after is None:
                return self._answer(self.state(), journal=[], notices=["Nothing changed."])
            change = "changed text"
        else:
            raise HostError("bad_request", "action is append or replace.")
        self.session.pop(path, None)
        journal = self._journal([formats.journal_entry(path, change, who, "person direct")], notices)
        return self._answer(self.state(), journal=journal, notices=notices)

    def forget(self, path, text=None, agent=None):
        """H5.2, H5.3: remove the content, its applied proposals, and any cached copy. Say what can't be deleted."""
        self._writable()
        path = self._editable(path)
        if text is not None and (not isinstance(text, str) or normalize(text) == ""):
            raise HostError("bad_request", "text is the words to forget.")
        who = self.who(agent)
        notices, entries, removed = [], [], 0
        token = self._lock(agent)
        try:
            kind = self.fs.kind(path)
            if kind == "missing":
                raise HostError("not_found", "%s does not exist." % path)
            if kind != "file":
                raise HostError("bad_path", "%s is a symbolic link or not a regular file." % path)
            if text is None:
                self.fs.remove(path)
                removed = 1
                entries.append(formats.journal_entry(path, "deleted the file", who, "person direct"))
            else:
                counted = []

                def cut(data):
                    out, count = formats.without_lines(data or b"", text)
                    if count == 0:
                        raise HostError("no_match", "Those words do not fill whole lines in %s." % path)
                    counted.append(count)
                    return out
                self.fs.replace(path, cut)
                removed = counted[-1]
                entries.append(formats.journal_entry(path, "removed text", who, "person direct"))
            wanted = normalize(text) if text is not None else None
            found, _ = self._proposals()
            for p in found:
                body = normalize(p.body or "")
                if p.valid and p.status == "accepted" and (
                        body == wanted or (wanted is None and p.fields["target"] == path)):
                    rel = "proposals/" + p.name
                    self.fs.remove(rel)  # S6.10: an applied, journaled proposal may be deleted
                    entries.append(formats.journal_entry(rel, "deleted an applied proposal", who, "person direct"))
                elif wanted and wanted in body:
                    state = p.status or "invalid"
                    notices.append("proposals/%s still holds these words. It is %s; delete it yourself if you "
                                   "want it gone%s." % (p.name, state, ", which ends the refusal"
                                                        if state in ("refused", "invalid") else ""))
        finally:
            self.fs.unlock(token)
        self.session.clear()
        notices.append(PROVIDER_NOTICE)
        if os.path.lexists(os.path.join(self.root, ".git")):
            notices.append("The store is a git repository, so its history still holds the words until you "
                           "rewrite it.")
        journal = self._journal(entries, notices)
        return self._answer(self.state(), removed=removed, journal=journal, notices=notices)

    def policy(self, state, agent=None):
        """S5.6: the person changes the switch, even while memory is off. Only state changes."""
        if state not in ("on", "off"):
            raise HostError("bad_request", 'state is "on" or "off".')
        if self.fs.kind("me.md") != "file":
            raise HostError("absent", "There is no store at %s. I don't create one unless you ask (S1.3)." % self.root)
        kind = self.fs.kind("policy.json")
        if state == "on" and kind == "file":
            try:
                _, _, obj = formats.parse_policy(self.fs.read("policy.json"))
            except Missing:
                obj = None
            if obj is not None and not formats.spec_supported(obj):
                raise HostError("unsupported_spec", self._spec_message(obj))
        who = self.who(agent)
        notices = []
        token = self._lock(agent)
        try:
            if kind == "link":
                os.unlink(self.fs.abs("policy.json"))  # a link is not a valid JSON object: replace it
            if kind not in ("missing", "file", "link"):
                raise HostError("bad_path", "policy.json is not a regular file, so I can't change it.")

            def flip(data):
                if data is None:
                    if state == "on" and kind == "missing":
                        return None  # a missing policy.json already means on (S5.1)
                    return formats.policy_bytes({"state": state, "spec": formats.SPEC})
                _, _, obj = formats.parse_policy(data)
                if obj is None:
                    return formats.policy_bytes({"state": state, "spec": formats.SPEC})
                if obj.get("state") == state:
                    return None
                obj["state"] = state
                return formats.policy_bytes(obj)
            _, after = self.fs.replace("policy.json", flip)
        finally:
            self.fs.unlock(token)
        journal = []
        if after is not None or kind == "link":
            change = "turned memory %s" % state
            journal = self._journal([formats.journal_entry("policy.json", change, who, "person direct")], notices)
        else:
            notices.append("Memory was already %s." % state)
        if state == "off":
            self.session.clear()
            notices.append(OFF_NOTICE)
        s = self.state()
        out = self._answer(s, journal=journal)
        # The answer's own notices come after the state's.
        out["notices"] = out.get("notices", []) + notices
        return out
