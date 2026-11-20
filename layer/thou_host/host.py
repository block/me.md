"""The host: every operation a thou v0.1 host does, at the Steward level (HOST.md, STORE.md).

Each public method returns a dict for a successful answer, or raises HostError.
The driver, the MCP server and the Claude Code hooks all call these methods,
so the rules live in one place.
"""

import json
import os
import re
import secrets
import time

from . import formats
from .formats import Proposal, as_shown, normalize
from .storefs import Changing, Locked, Missing, StoreFS, location

NAME = "thou-layer"
VERSION = "0.1.0"
LEVEL = "steward"

_RECALL_PURPOSES = ("task", "briefing", "watches")
_ID_CHARS = "abcdefghijklmnopqrstuvwxyz0123456789"

PROVIDER_NOTICE = ("I removed it from the store and from this host's memory. I can't delete copies outside "
                   "the store: saved agent sessions and the model provider may keep what earlier sessions "
                   "read, and backups, sync folders or exported copies keep their own.")
OFF_NOTICE = ("Memory is off. This host enforces that in its own code, for its own tools. Another agent on "
              "this machine follows it only if it honors policy.json.")
# S5.1: a journal entry for policy.json, whatever its change says. Hosts journal every write of policy.json and
# never delete it, so with such an entry a missing policy.json was set once and has since gone.
_POLICY_ENTRY = re.compile(rb"(?m)^- [^|\r\n]*\| policy\.json \|")
MOST_PENDING = 50  # proposals waiting for the person, at most: past that, propose asks them to decide first
# One change holds at most this much, so that it fits in an approval prompt in an ordinary window. Claude Code
# shows a change's words in full, so longer words run off the top of the window.
MOST, MOST_LINES = 2000, 30


def _too_long(text):
    """Why text is too long for one approval prompt, or None."""
    lines = len(formats.body_lines(text))
    if len(text) > MOST or lines > MOST_LINES:
        return ("has %d characters on %d lines. One change holds at most %d characters and %d lines, so that the "
                "person can read all of it when they approve it." % (len(text), lines, MOST, MOST_LINES))
    return None


class HostError(Exception):
    def __init__(self, code, message, notices=()):
        Exception.__init__(self, message)
        self.code, self.message, self.notices = code, message, list(notices)


class _Again(Exception):
    """The proposal changed between reading it and applying it."""


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
        """Read policy.json alone and decide, then check for me.md. Opens no other file, except journal.md when
        policy.json is missing (S5.1)."""
        kind = self.fs.kind("policy.json")
        obj = None
        if kind == "missing" and self._switch_gone():
            return self._off("policy.json is missing, but journal.md shows the switch was set before, so the "
                             "person's last choice is unknown. Only the person can turn memory on again: in an agent "
                             "that asks them first, or by writing {\"spec\": \"0.1\", \"state\": \"on\"} to %s "
                             "(S5.1)" % os.path.join(self.root, "policy.json"))
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

    def _switch_gone(self):
        """S5.1: whether journal.md records a change to policy.json. A journal that can't be read can't show that
        the switch was never set, so it counts as yes; a link counts as no file (S2.4)."""
        kind = self.fs.kind("journal.md")
        if kind in ("missing", "link"):
            return False
        try:
            return bool(_POLICY_ENTRY.search(self.fs.read("journal.md")))
        except (Missing, OSError):
            return True

    def _off(self, reason):
        return {"memory": "off", "notices": ["Memory is off: %s." % reason], "obj": None}

    def _spec_message(self, obj):
        return ("policy.json says this store follows spec %s. This host supports only %s, so it will not "
                "write to the store, except to turn memory off (S5.4)."
                % (formats.quoted(obj.get("spec")), formats.SPEC))

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
        text = data.decode("utf-8")
        found = formats.hidden(text)
        if found:  # the agent reads what the person would see, as for words the host writes
            notices.append("%s holds characters a person can't see (%s). I left them out of what I read here."
                           % (rel, formats.code_points(found)))
            text = formats.visible(text)
        return text

    def _visible(self, text, what, check_hidden=True):
        """Words that will be written must be words the person can see in full when they approve them."""
        found = formats.hidden(text) if check_hidden else []
        if found:
            raise HostError("hidden_characters", "%s holds characters a person can't see (%s), so I wrote nothing. "
                                                 "Use only words the person can read." % (what, formats.code_points(found)))
        too_long = _too_long(text)
        if too_long:
            raise HostError("too_long", "%s %s I wrote nothing; split it into smaller changes." % (what, too_long))

    def _not_refused(self, body):
        """H3.3, S6.11: refused words, and the words of an invalid proposal, are never proposed again."""
        wanted = normalize(body)
        found, _ = self._proposals()
        for p in found:
            if (not p.valid or p.status == "refused") and normalize(p.body or "") == wanted:
                why = "refused" if p.valid else "invalid, which counts as refused (S6.14)"
                raise HostError("refused", "You refused these words before (proposals/%s is %s), so I will not "
                                           "propose them again (S6.11)." % (formats.shown_name(p.name), why))

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
                                       "., _ and -, ending in .md (S2.1)." % (folder, formats.shown_name(name)))
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
            if not name.endswith(".md") or not formats.is_utf8(name):
                why = "its name is not UTF-8" if name.endswith(".md") else "it does not end in .md"
                notices.append("I ignore proposals/%s because %s (S2.1)." % (formats.shown_name(name), why))
                continue
            try:
                self.fs.check("proposals/" + name)
            except ValueError:
                notices.append("I ignore proposals/%s because its name has characters a store file's name can't "
                               "(S2.1)." % formats.shown_name(name))
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
                    item = p.summary()
                    found = formats.hidden(p.body)
                    if found:
                        item["hidden"] = ("These words hold characters a person can't see (%s). They can be refused "
                                          "or revised, not accepted." % formats.code_points(found))
                    too_long = _too_long(p.body)
                    if too_long:
                        item["too_long"] = "These words %s They can be refused or revised, not accepted." % too_long
                    proposals.append(item)
        return self._answer(s, proposals=proposals, invalid=invalid, notices=notices)

    def propose(self, target, body, basis, agent=None):
        self._writable()
        if not isinstance(target, str) or not formats.TARGET_RE.fullmatch(target):
            raise HostError("bad_target", "A proposal targets me.md, topics/<name>.md or projects/<name>.md "
                                          "(S6.4). It never targets watches.md (S4.2).")
        if not isinstance(body, str):
            raise HostError("bad_request", "A proposal needs a body: the words to keep.")
        if normalize(body) == "":
            raise HostError("empty_body", "The proposal has no words to keep (S6.6).")
        if not isinstance(basis, str) or formats.one_line(basis) == "":
            raise HostError("bad_request", "A proposal needs a basis: why, in words the person will recognize.")
        self._visible(body, "The proposal")
        self._visible(basis, "The basis")
        self._not_refused(body)  # H3.3: read the refusals first
        waiting = sum(1 for p in self._proposals()[0] if p.valid and p.status == "pending")
        if waiting >= MOST_PENDING:
            raise HostError("too_many", "%d proposals already wait for the person, so I proposed nothing. Ask them "
                                        "to decide some first." % waiting)
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
        if not isinstance(pid, str):
            raise HostError("bad_request", "proposal is the proposal's id.")
        if not formats.ID_RE.fullmatch(pid):
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

    def decide(self, proposal, decision, agent=None, words=None, target=None):
        """S8.6, in order: lock, check, apply, set status, unlock, journal.

        words and target, when given, are what the person was shown: the proposal's words and the file they
        go to. If the proposal says anything else when it is decided, nothing is decided. Words compare as a
        prompt shows them (formats.as_shown), so only differences the person could not see are ignored.
        A body with characters a person can't see is never accepted.
        """
        if decision not in ("accept", "refuse"):
            raise HostError("bad_request", "decision is accept or refuse.")
        if words is not None and not isinstance(words, str):
            raise HostError("bad_request", "words are the proposal's words, as the person saw them.")
        if target is not None and not isinstance(target, str):
            raise HostError("bad_request", "target is the file the proposal adds to, as the person saw it.")
        seen_target = target
        self._writable()
        rel = self._proposal_path(proposal)
        who = self.who(agent)
        notices, applied, unmarked = [], None, None
        status = "accepted" if decision == "accept" else "refused"
        token = self._lock(agent)
        try:
            for _ in range(5):
                data, p = self._read_pending(rel)
                shown = as_shown(formats.visible(p.body))
                if words is not None and as_shown(formats.visible(words)) != shown:
                    raise HostError("words_differ", "Those are not the words of %s, so I decided nothing. It "
                                                    "says:\n%s" % (rel, shown))
                if seen_target is not None and seen_target != p.fields["target"]:
                    raise HostError("target_differs", "%s adds to %s, not %s, so I decided nothing."
                                    % (rel, p.fields["target"], seen_target))
                target = p.fields["target"]
                if status == "refused":
                    break
                found = formats.hidden(p.body)
                if found:
                    raise HostError("hidden_characters", "%s holds characters a person can't see (%s), so I will "
                                                         "not add it. Refuse it, or revise it to words the person "
                                                         "can read." % (rel, formats.code_points(found)))
                too_long = _too_long(p.body)
                if too_long:
                    raise HostError("too_long", "%s %s So I will not add it. Refuse it, or revise it shorter."
                                    % (rel, too_long))

                def add(old):
                    # S6.15: apply the body as it is at acceptance. If the file changed since it was read,
                    # start again rather than apply words the person did not see.
                    if self.fs.read_or_none(rel) != data:
                        raise _Again()
                    return formats.appended(old, p.body)
                try:
                    _, new = self.fs.replace(target, add)
                except _Again:
                    continue
                except Missing as exc:
                    raise HostError("bad_target", "I will not write %s: %s." % (target, exc.why))
                applied = "added" if new is not None else "already"
                break
            else:
                raise Changing("%s kept changing while I tried to accept it, so I made no change" % rel)

            def mark(old):
                if old != data:
                    notices.append("%s changed while I was deciding it, so I left its status alone. %s"
                                   % (rel, "Its words as they were are in %s." % target if applied else ""))
                    return None
                return Proposal(p.name, old).decided(status, formats.now(), who)
            try:
                self.fs.replace(rel, mark)
            except (OSError, Missing) as exc:
                unmarked = getattr(exc, "why", None) or str(exc)
        finally:
            self.fs.unlock(token)
        if unmarked is not None:
            if applied != "added":
                raise HostError("io_error", "I could not mark %s %s: %s. Nothing changed." % (rel, status, unmarked))
            # The words are in the file, so the journal says so (S8.7), though the proposal still says pending.
            self._journal([formats.journal_entry(target, "added the text of an accepted proposal", who,
                                                 "accepted proposal " + p.id)], notices)
            raise HostError("io_error", "I added the words of %s to %s, but could not mark it accepted: %s. It "
                                        "still says pending; the journal records the addition."
                            % (rel, target, unmarked))
        when = formats.now()
        entries = [formats.journal_entry(rel, status, who, "person direct", when)]
        if status == "accepted":
            entries.append(formats.journal_entry(target, "added the text of an accepted proposal", who,
                                                 "accepted proposal " + p.id, when))
        journal = self._journal(entries, notices)
        return self._answer(self.state(), status=status, applied=applied, journal=journal, notices=notices)

    def revise(self, proposal, body, agent=None):
        """S6.15: the person changes a pending body. Not journaled (S6.13).

        Only a proposal this host wrote: one the person wrote by hand, or another host proposed, keeps its
        words, and its proposed-by would no longer say who wrote them."""
        self._writable()
        if not isinstance(body, str):
            raise HostError("bad_request", "revise needs a body: the new words.")
        if normalize(body) == "":
            raise HostError("empty_body", "The new body has no words (S6.6).")
        rel = self._proposal_path(proposal)
        self._visible(body, "The new body")
        self._not_refused(body)
        token = self._lock(agent)
        try:
            data, p = self._read_pending(rel)
            by = formats.one_line(p.fields["proposed-by"])
            if not by.startswith(NAME + " "):
                raise HostError("not_ours", "%s was proposed by %s, not by this host, so I will not change its "
                                            "words. Propose the new words instead, and the person can refuse "
                                            "the old ones." % (rel, formats.quoted(by, 60)))
            self.fs.replace(rel, lambda old: Proposal(p.name, old).revised(body) if old == data else None)
        finally:
            self.fs.unlock(token)
        return self._answer(self.state())

    def _editable(self, path):
        if not isinstance(path, str):
            raise HostError("bad_request", "path is the store-relative file to change.")
        if not (path == "watches.md" or formats.TARGET_RE.fullmatch(path)):
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
            self._visible(text, "The text")
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
            self._visible(new, "The new words")
            self._visible(old, "The words to change", check_hidden=False)
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
                    at = data.find(a)
                    if at < 0:
                        raise HostError("no_match", "Those words are not in %s." % path)
                    if data.find(a, at + 1) >= 0:  # counts overlapping places too
                        raise HostError("ambiguous", "Those words appear more than once in %s." % path)
                    return data[:at] + b + data[at + len(a):]
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

    def forget(self, path, text=None, agent=None, kept=None):
        """H5.2, H5.3: remove the content, its applied proposals, and any cached copy. Say what can't be deleted."""
        self._writable()
        path = self._editable(path)
        if text is not None and (not isinstance(text, str) or normalize(text) == ""):
            raise HostError("bad_request", "text is the words to forget.")
        who = self.who(agent)
        notices, entries, removed, done = [], [], 0, False
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
                    if kept is not None:
                        del kept[:]
                    out, count = formats.without_text(data or b"", text, kept)
                    if count == 0 and formats.inside_a_clause(data or b"", text):
                        raise HostError("inside_a_clause", "Those words are inside a clause in %s, so taking them "
                                                           "out would leave a broken sentence. Nothing changed. "
                                                           "Forget the whole line, or a whole clause of it." % path)
                    if count == 0:
                        raise HostError("no_match", "Those words are not in %s as whole words." % path)
                    counted.append(count)
                    return out
                self.fs.replace(path, cut)
                removed = counted[-1]
                entries.append(formats.journal_entry(path, "removed text", who, "person direct"))
            wanted = normalize(text) if text is not None else None
            try:
                self._forget_proposals(path, wanted, who, entries, notices)
            except (OSError, Missing) as exc:
                # The words are gone already, so the answer says so, with what was left undone.
                notices.append("I could not finish with the proposals for %s (%s), so some may still hold %s."
                               % (path, getattr(exc, "why", None) or exc, "these words" if wanted else "its words"))
            done = True
        finally:
            self.fs.unlock(token)
            if not done:
                self.session.clear()
                self._journal(entries, [])  # whatever went wrong, a change that happened has its receipt (S8.7)
        self.session.clear()
        notices.append(PROVIDER_NOTICE)
        if os.path.lexists(os.path.join(self.root, ".git")):
            notices.append("The store is a git repository, so its history still holds the words until you "
                           "rewrite it.")
        journal = self._journal(entries, notices)
        return self._answer(self.state(), removed=removed, journal=journal, notices=notices)

    def _forget_proposals(self, path, wanted, who, entries, notices):
        found, more = self._proposals()
        notices += more  # a proposal it ignores may hold the words too
        for p in found:
            body = normalize(p.body or "")
            same_file = p.valid and p.fields["target"] == path
            if same_file and p.status == "accepted" and (wanted is None or body == wanted):
                rel = "proposals/" + p.name
                self.fs.remove(rel)  # S6.10: an applied, journaled proposal may be deleted
                entries.append(formats.journal_entry(rel, "deleted an applied proposal", who, "person direct"))
            elif (wanted and wanted in body) or (wanted is None and same_file):
                state = p.status if p.valid else "invalid"
                notices.append("proposals/%s still holds %s. It is %s; delete it yourself if you want it "
                               "gone%s." % (formats.shown_name(p.name),
                                            "these words" if wanted else "words for %s" % path, state,
                                            ", which ends the refusal" if state in ("refused", "invalid") else ""))

    def start(self, text, agent=None):
        """Create the store's me.md with the person's own words, at their request (S1.3, SETUP.md).

        Never overwrites: if me.md exists, nothing changes. The folder, if this creates it, is the
        person's alone (S2.5). It does not create missing folders above the store.
        """
        if not isinstance(text, str) or normalize(text) == "":
            raise HostError("empty_body", "me.md starts with the person's own words, and these have none. "
                                          "There is no template.")
        self._visible(text, "The text")
        s = self.state()
        if s["memory"] == "off":
            raise HostError("memory_off", s["notices"][0] + " I wrote nothing.")
        if s["memory"] == "on":
            raise HostError("exists", "There is already a me.md at %s, so I changed nothing. To add to it, "
                                      "use edit." % self.root)
        if self.fs.kind("me.md") != "missing":
            raise HostError("bad_path", "me.md at %s is a symbolic link or not a regular file, so I will not "
                                        "create it (S2.4)." % self.root)
        if s["obj"] is not None and not formats.spec_supported(s["obj"]):
            raise HostError("unsupported_spec", self._spec_message(s["obj"]))
        try:
            os.mkdir(self.root, 0o700)  # S2.5
        except FileExistsError:
            if not os.path.isdir(self.root):
                raise HostError("bad_path", "%s is not a folder, so I can't start a store there." % self.root)
        except FileNotFoundError:
            raise HostError("bad_path", "The folder that should hold %s does not exist, so I created "
                                        "nothing." % self.root)
        who = self.who(agent)
        notices = []
        token = self._lock(agent)
        try:
            self.fs.create("me.md", formats.appended(None, text))
        except FileExistsError:
            raise HostError("exists", "Another program created me.md at %s just now, so I changed nothing."
                            % self.root)
        finally:
            self.fs.unlock(token)
        journal = self._journal([formats.journal_entry("me.md", "created me.md", who, "person direct")], notices)
        return self._answer(self.state(), store=self.root, journal=journal, notices=notices)

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
        gone = kind == "missing" and self._switch_gone()
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
                    if state == "on" and kind == "missing" and not gone:
                        return None  # a missing policy.json already means on, unless the switch was set (S5.1)
                    return formats.policy_bytes({"state": state, "spec": formats.SPEC})
                _, _, obj = formats.parse_policy(data)
                if obj is None:
                    return formats.policy_bytes({"state": state, "spec": formats.SPEC})
                if obj.get("state") == state:
                    return None
                obj["state"] = state
                return formats.policy_bytes(obj)
            try:
                _, after = self.fs.replace("policy.json", flip)
            except RecursionError:
                raise HostError("io_error", "policy.json is nested too deeply for me to rewrite, so I changed nothing.")
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
