"""Quoted consent: what the person typed, and whether a change rests on it (HOST.md H3.7, SOVEREIGNTY.md).

A client hook (Claude Code's UserPromptSubmit) records the person's latest message in a file outside the
store, one per client process, numbered within the session. The thou server reads it when an agent calls remember or
forget, and applies the change at once only when the person's own words ask for it:

- the quote is in the person's latest message, in words they wrote themselves: not a line they pasted after
  `>`, not a fenced block, not words in quotation marks that give an instruction, and not the rest of a
  sentence that reports what someone else said or wrote;
- that sentence asks for the operation: "forget", "delete" or "remove" for forget, and "remember", "note" or
  "save" for remember. A question doesn't ask, unless it is a request ("Can you…?"); nor does a verb with a
  negator up to four words before it ("please don't ever forget" asks to remember), nor one that describes
  someone ("I always forget");
- the words match what that sentence says. To remember, every word that carries meaning must be the
  person's, in their order. To forget, all but one at most, so "forget about Mochi" can take the line "I have a
  cat called Mochi." but "forget that my test is in March" can't take "I'm learning to drive and my test is in
  March." Or the person names a line by its subject, the words before its is/are/was/were: "forget my old
  address" takes "My old address is 4 Elm St.", when the value after the verb is one clause. A negator ("not",
  "no longer", "anymore", "used to") counts as a word that carries meaning, both ways. Only an ask with no words of its own ("forget that") takes them from the sentence before it.

Words from an email or a web page are not in what the person typed, so they can't pass. Everything that
doesn't pass changes nothing. Where the person named some of the words to forget, the agent may ask them, and
a bare yes in their next message confirms (thou_mcp.Said). Words the person only pasted or quoted have no yes:
the person says them in their own words, or nothing changes.

The file is the person's words, so only the client's hook writes it and only the server reads it. The
pre-tool-use hook keeps Claude Code's own tools out of its folder, as it does for the store. A forget takes
its words out of every kept message, and at session start the messages of clients that have gone, or that are
more than a day old, are deleted (H5.2).
"""

import hashlib
import json
import os
import re
import subprocess
import tempfile
import time
import unicodedata

FOLDER_ENV = "THOU_SAID_DIR"
MOST_PROMPT = 20000  # characters of the person's message kept, at most


def folder():
    """Where the latest messages are kept: outside the store, readable by the person's account only."""
    if os.environ.get(FOLDER_ENV):
        return os.path.abspath(os.path.expanduser(os.environ[FOLDER_ENV]))
    state = os.environ.get("XDG_STATE_HOME") or os.path.join(os.path.expanduser("~"), ".local", "state")
    return os.path.join(os.path.abspath(state), "thou", "said")


# --- which client --------------------------------------------------------------

# Programs that sit between a client and its hook or server: a hook runs through a shell, a server may start
# through env or uv. Node is not here: some clients are node programs.
_WRAPPERS = re.compile(r"^(?:-?(?:sh|bash|zsh|dash|ksh|fish|tcsh|csh)|env|uv|uvx|timeout|gtimeout|nice|nohup|"
                       r"python[\d.]*|python\.app|cmd(?:\.exe)?|powershell(?:\.exe)?|pwsh(?:\.exe)?)$", re.I)


def _proc(pid):
    """(parent pid, program name, start time) for a process, or None."""
    stat = "/proc/%d/stat" % pid
    if os.path.exists(stat):
        try:
            with open(stat) as handle:
                text = handle.read()
            name = text[text.index("(") + 1:text.rindex(")")]
            fields = text[text.rindex(")") + 2:].split()
            return int(fields[1]), name, fields[19]
        except (OSError, ValueError, IndexError):
            return None
    try:
        out = subprocess.run(["ps", "-o", "ppid=,lstart=,comm=", "-p", str(pid)], stdout=subprocess.PIPE,
                             stderr=subprocess.DEVNULL, universal_newlines=True, timeout=5).stdout.strip()
    except (OSError, subprocess.SubprocessError):
        return None
    found = re.match(r"(\d+)\s+(\w{3}\s+\w{3}\s+\d+\s+[\d:]+\s+\d{4})\s+(.+)", out)
    if not found:
        return None
    return int(found.group(1)), os.path.basename(found.group(3).strip()), found.group(2)


def client():
    """The client process this hook or server belongs to: the first ancestor that is not a shell or a
    launcher, as (pid, start time). Its hook and its server find the same one."""
    pid = os.getppid()
    for _ in range(8):
        info = _proc(pid)
        if info is None:
            return pid, None
        parent, name, started = info
        if not _WRAPPERS.match(name) or parent <= 1:
            return pid, started
        pid = parent
    return pid, None


def _path(who):
    return os.path.join(folder(), "client-%d.json" % who[0])


_RECORD = ("prompt", "at", "n", "session", "salt")


def _parked(data):
    """The other sessions' messages in this client's file, by the client's session id."""
    others = data.get("others") if data else None
    return {k: v for k, v in others.items() if isinstance(v, dict)} if isinstance(others, dict) else {}


def _switch(data, who, sid):
    """This client's file with session sid's message on top, where latest reads it, and the one that was on top
    parked under its own session id. One client process can run more than one session at a time (Codex runs its
    memory writer beside the person's session), and each keeps its own latest message."""
    data = data or {}
    others = _parked(data)
    if data.get("sid") != sid and any(k in data for k in _RECORD):
        others[data.get("sid") or ""] = {k: data[k] for k in _RECORD if k in data}
    mine = others.pop(sid or "", {})
    out = dict({k: mine[k] for k in _RECORD if k in mine} if data.get("sid") != sid else
               {k: data[k] for k in _RECORD if k in data}, client=list(who), sid=sid)
    if others:
        out["others"] = others
    return out


def record(prompt, who=None, sid=None):
    """The hook: keep the person's latest message for this client and session, replacing the one before."""
    who = who or client()
    before = _switch(_read(who), who, sid)
    number = before["n"] + 1 if isinstance(before.get("n"), int) else 1
    session = before.get("session") if isinstance(before.get("session"), str) else os.urandom(8).hex()
    before.update(prompt=prompt[:MOST_PROMPT], at=time.time(), n=number, session=session, salt=os.urandom(16).hex())
    _write(who, before)


def unreadable(sid=None, who=None):
    """The hook, for a message it can't read: this session's latest message is none, and no older one stands in."""
    who = who or client()
    data = {k: v for k, v in _switch(_read(who), who, sid).items() if k not in _RECORD}
    if "others" in data:
        _write(who, data)
    else:
        clear(who)


def mark(sid, who=None):
    """The pre-tool hook, as a session calls remember or forget: that session's message is the one the server
    reads. A session with no message kept leaves none on top, so nothing rests on another session's words."""
    who = who or client()
    data = _read(who)
    if data is None or data.get("sid") == sid:
        return
    _write(who, _switch(data, who, sid))


def _files():
    try:
        names = os.listdir(folder())
    except OSError:
        return []
    return [os.path.join(folder(), n) for n in sorted(names) if re.fullmatch(r"client-\d+\.json", n)]


def _load(path):
    try:
        with open(path) as handle:
            data = json.load(handle)
    except (OSError, ValueError):
        return None
    return data if isinstance(data, dict) else None


def scrub(text, who=None):
    """After a forget: take its words out of every kept message, this client's and any other's, so the layer
    keeps no copy of them (H5.2). Each word goes to a hash salted for that one message (_hide), so a second
    forget from the same sentence still finds the person's words, and the salt goes with the message. A message
    kept without a salt loses the sentences that hold the words instead, and so does a sentence where a word
    is still read after the hashing."""
    gone = words(text) - {NOT}
    if not gone:
        return
    def cut(record):
        prompt, salt = record.get("prompt"), record.get("salt")
        if not isinstance(prompt, str):
            return record
        if isinstance(salt, str) and salt:
            prompt = _hide(prompt, salt, lambda stems: not gone.isdisjoint(stems))
            if not (words(prompt) & gone):
                return dict(record, prompt=prompt)
        kept = [x for x in _SENTENCES.split(_apostrophes(prompt).replace("\r\n", "\n"))
                if x.strip() and not (words(x) & gone)]
        return dict(record, prompt="\n".join(kept))
    for path in _files():
        for _ in range(3):
            data = _load(path)
            if not data:
                break
            after = cut(data)
            if _parked(data):
                after["others"] = {k: cut(v) for k, v in _parked(data).items()}
            if after == data:
                break
            if _replace(path, after, data):
                break


MOST_AGE = 24 * 3600  # seconds a kept message may outlive a session that never ended


def _alive(who):
    try:
        pid, started = int(who[0]), who[1]
    except (TypeError, ValueError, IndexError):
        return False
    if pid <= 0:
        return False
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    except OSError:
        pass  # another user's process: it exists
    if started is None:
        return True
    info = _proc(pid)
    return info is None or info[2] == started  # a new process with the same number: the old one has gone


def sweep(now=None):
    """At session start: delete the kept messages of clients that have gone, and any more than a day old, so a
    session that ended without SessionEnd leaves nothing behind for long (H5.2)."""
    now = time.time() if now is None else now
    for path in _files():
        data = _load(path)
        try:
            old = now - os.stat(path).st_mtime > MOST_AGE
        except OSError:
            continue
        if data is None or old or not _alive(data.get("client")):
            try:
                os.unlink(path)
            except OSError:
                pass


def _write(who, record):
    _replace(_path(who), record)


def _replace(path, record, before=None):
    """Write the file whole, by rename. With before, only if the file still holds it; returns whether it wrote."""
    place = os.path.dirname(path)
    os.makedirs(place, mode=0o700, exist_ok=True)
    data = json.dumps(record)
    handle, temp = tempfile.mkstemp(dir=place, prefix=".said-")
    try:
        with os.fdopen(handle, "w") as out:
            out.write(data)
        os.chmod(temp, 0o600)
        if before is not None and _load(path) != before:
            os.unlink(temp)  # the hook wrote a newer message meanwhile
            return False
        os.replace(temp, path)
        return True
    except BaseException:
        try:
            os.unlink(temp)
        except OSError:
            pass
        raise


def clear(who=None, sid=None):
    """At session start: no message yet. At a session's end, with its id: that session's message goes, and the
    client's other sessions keep theirs."""
    who = who or client()
    data = _read(who) if sid is not None else None
    if data is not None:
        others = _parked(data)
        others.pop(sid, None)
        if data.get("sid") == sid:
            data = {k: v for k, v in data.items() if k not in _RECORD}
        data["others"] = others
        if not others and not any(k in data for k in _RECORD):
            data = None
        else:
            data = {k: v for k, v in data.items() if k != "others" or v}
    if data is not None:
        _write(who, data)
        return
    try:
        os.unlink(_path(who))
    except OSError:
        pass


def _read(who):
    try:
        with open(_path(who)) as handle:
            data = json.load(handle)
    except (OSError, ValueError):
        return None
    if not isinstance(data, dict) or list(data.get("client") or []) != list(who):
        return None  # another process that had the same number
    return data


def latest(who=None):
    """The person's latest message to this client, and where it stands: (session, number), the number counting
    1, 2, ... from the session's start. Or (None, None)."""
    return salted(who)[:2]


def salted(who=None):
    """latest, and the salt of the message's hashed words (_hide), or None: (prompt, place, salt)."""
    data = _read(who or client())
    prompt = data and data.get("prompt")
    number = data and data.get("n")
    session = data and data.get("session")
    if not isinstance(prompt, str) or not isinstance(number, int) or isinstance(number, bool) or \
            not isinstance(session, str):
        return None, None, None
    salt = data.get("salt")
    return prompt, (session, number), salt if isinstance(salt, str) and salt else None


# --- the person's own words ------------------------------------------------------

_FENCE = re.compile(r"(?ms)^[ \t]*(```|~~~).*?(?:^[ \t]*\1[^\n]*$|\Z)")
_PASTED = re.compile(r"(?m)^[ \t]*>.*$")
# A line that starts with a speaker's name and a colon, as in a pasted chat: "Sam: forget that…".
_SPEAKER = re.compile(r"(?m)^[ \t]*([A-Z][\w.'-]*(?:[ \t]+[\w.'-]+){0,2})[ \t]*:[ \t].*$")
_OWN_LEAD = re.compile(r"(?i)^(?:also|ps|p\.s\.|update|btw|fyi|edit|important|reminder|ok|okay|so|and|but|oh|"
                       r"please|thanks|hey|hi)$")
_QUOTED = re.compile(r"\"[^\"\n]*(?:\"|$)|\u201c[^\u201d\n]*(?:\u201d|$)|\u00ab[^\u00bb\n]*(?:\u00bb|$)|"
                     r"\u2018[^\u2019\n]*(?:\u2019|$)|(?:^|(?<=[\s(\[{]))'[^'\n]*'(?=$|[\s.,;:!?)\]}])", re.M)
# The rest of a sentence after a word that reports what someone else said, wrote or sent.
_REPORTED = re.compile(r"(?i)\b(?:says?|said|saying|wrote|writes?|writing|told|tells?|telling|asks?|asked|"
                       r"texted|texts?|messaged|emailed|replied|replies|sent|sends|posted|shared|forwarded|"
                       r"goes|went|according to)\b.*")
_THEIRS = re.compile(r"(?i)\byour (?:assistant|ai|agent|bot|chatbot)\b")
_SENTENCES = re.compile(r"(?<=[.!?])\s+|\n+")
GAP = "\n"


def _apostrophes(text):
    return unicodedata.normalize("NFKC", text).replace("\u02bc", "'")


def own_sentences(prompt):
    """The sentences of the message that the person wrote themselves.

    Left out: fenced blocks, lines pasted after >, lines that start with someone's name and a colon, words in
    quotation marks that themselves ask to remember or forget (an instruction someone else gave), the rest of
    a sentence after "said", "wrote", "sent" and the like, and a sentence that speaks of "your assistant".
    Quoted words that don't ask anything stay, without their marks: 'forget "I'm vegetarian"' names words."""
    if not isinstance(prompt, str):
        return []
    text = _apostrophes(prompt).replace("\r\n", "\n")
    text = _FENCE.sub(GAP, text)
    text = _PASTED.sub(GAP, text)
    text = _SPEAKER.sub(lambda m: m.group(0) if _OWN_LEAD.match(m.group(1)) or _asks_any(m.group(1)) else GAP,
                        text)
    text = _QUOTED.sub(lambda m: GAP if _asks_any(m.group(0)) else " " + m.group(0).strip("\"'\u201c\u201d\u00ab"
                                                                                       "\u00bb\u2018\u2019") + " ",
                       text)
    text = text.replace("\u2019", "'")
    out = []
    for sentence in _SENTENCES.split(text):
        sentence = re.sub(r"[ \t]+", " ", _REPORTED.sub("", sentence)).strip()
        if sentence and not _THEIRS.search(sentence):
            out.append(sentence)
    return out


def _plain(text):
    text = _apostrophes(text).replace("\u2019", "'").lower()
    text = re.sub(r"[\"\u201c\u201d\u00ab\u00bb\u2018]", "", text)
    return re.sub(r"\s+", " ", text).strip(" \t.,;:!?'")


# --- what the words mean ----------------------------------------------------------

STOP = frozenset("""
a an the and or but nor so yet of to in on at for with from by about as into onto over under than then
i im ive id ill me my mine myself you youre your yours we our ours us they their them he his him she her
it its itself is are was were be been being am do does did done have has had having will would can could
shall should may might must that this these those there here what which who whom whose when where why how
longer any more now just also very really still again too please thanks thank bit
part parts thing things stuff one two three four five six seven eight nine ten called named
forget forgets forgetting delete remove erase wipe scrub remember remembering note save keep mind write
down add memory memories store file line
""".split())

# Every negator reads as one word, NOT, and it carries meaning: "not vegetarian" is not "vegetarian".
NOT = "not"
_NEGATOR_PHRASES = re.compile(r"(?i)\b(?:no longer|used to|gave up|give up|given up)\b")
_NEGATORS = frozenset("""
not no never none nothing nobody neither cannot anymore stopped quit formerly
dont doesnt didnt isnt arent wasnt werent cant couldnt wont wouldnt shouldnt havent hasnt hadnt aint mustnt
neednt
""".split())

_SUFFIXES = ("ingly", "edly", "ings", "ing", "ies", "ied", "ers", "es", "ed", "er", "ly", "ic", "s", "y", "e")


def stem(word):
    """A crude stem, the same for "drive" and "driving", or "allergy" and "allergic"."""
    for _ in range(3):
        for suffix in _SUFFIXES:
            if word.endswith(suffix) and len(word) - len(suffix) >= 3:
                word = word[:-len(suffix)] + ("y" if suffix in ("ies", "ied") else "")
                break
        else:
            break
    return word


def _tokens(text):
    """The words that carry meaning, as stems, in order: no small words, no operation words, every negator as
    NOT."""
    text = unicodedata.normalize("NFKC", text).replace("\u2019", "'").lower()
    text = _NEGATOR_PHRASES.sub(" not ", text).replace("'", "")
    out = []
    for w in re.findall(r"[^\W_]+", text):
        if w in _NEGATORS:
            out.append(NOT)
        elif w not in STOP:
            out.append(stem(w))
    return out


def words(text):
    """The words that carry meaning, as a set of stems (_tokens)."""
    return set(_tokens(text))


_HIDDEN = re.compile(r"\bthouh[0-9a-f]{20}q\b")


def _hashed(stems, salt):
    """A forgotten word's stand-in in a kept message: one word, salted for that message only, and read by
    _tokens and stem as itself. stems are the word's own, as _tokens reads it."""
    key = "%s:%s" % (salt, " ".join(stems))
    return "thouh%sq" % hashlib.sha256(key.encode("utf-8")).hexdigest()[:20]


def _hide(text, salt, wanted):
    """text with each word that carries meaning, whose stems wanted(stems) picks, put as its salted hash. Small
    words, negators and the words of "no longer"-style phrases stay as they are, as _tokens reads them."""
    text = _apostrophes(text).replace("\u2019", "'")
    phrases = [m.span() for m in _NEGATOR_PHRASES.finditer(text)]
    def swap(m):
        word = m.group(0)
        if any(a <= m.start() < b for a, b in phrases) or _HIDDEN.fullmatch(word):
            return word
        stems = [x for x in _tokens(word) if x != NOT]  # one word can be two stems once lowercased: "İstanbul"
        return _hashed(stems, salt) if stems and wanted(stems) else word
    return re.sub(r"[^\W_]+(?:'[^\W_]+)*", swap, text)


# --- what the person asks ----------------------------------------------------------

_FORGET_VERB = r"forget|delete|remove|erase|wipe"
_REMEMBER_VERB = r"remember(?:ing)?|memori[sz]e|make a note|note|keep in mind|save|write (?:it |this |that )?down"
_VERB = re.compile(r"(?i)\b(?:%s|%s)\b" % (_FORGET_VERB, _REMEMBER_VERB))
_ADD = re.compile(r"(?i)\b(?:add|put)\b[^.!?\n]{0,60}?\b(?:to|in|into) (?:my |your |the )?"
                  r"(?:me\.md|memory|memories|thou|profile)\b")
# A negator up to four words before the verb, in the same clause: "please don't ever forget".
_NEG_BEFORE = re.compile(r"(?i)\b(?:don't|dont|do not|never|not|won't|wont|can't|cant|cannot|no longer|stop|"
                         r"didn't|didnt|doesn't|doesnt|shouldn't|shouldnt|mustn't|mustnt)(?:[ \t]+[\w']+){0,4}"
                         r"[ \t]+$")
# Words that make the verb describe someone, not ask: "I always forget", "people never remember".
_DESCRIBES = re.compile(r"(?i)\b(?:i|we|he|she|they|you|people|everyone|everybody|nobody|someone)"
                        r"(?:'ll|'d| will| would| can| could| might| may| should| must| did| do| does| tend to)?"
                        r"(?:[ \t]+(?:\w+ly|always|often|sometimes|never|still|just|also|ever|even|keep|kept))*"
                        r"[ \t]+$")
# The same, after a negator, for anyone but "you": "don't think I'd forget", but "don't you ever forget" asks.
_DESCRIBES_OTHER = re.compile(r"(?i)\b(?:i|we|he|she|they|people|everyone|everybody|nobody|someone)"
                              r"(?:'ll|'d|'m| will| would| can| could| might| may| should| must| did| do| does|"
                              r" tend to)?(?:[ \t]+(?:\w+ly|always|often|sometimes|never|still|just|also|ever|even|"
                              r"keep|kept|want you to|want to))*[ \t]+$")
_REQUEST_LEAD = re.compile(r"(?i)\b(?:can|could|would|will)[ \t]+you(?:[ \t]+(?:please|just|also|kindly))*[ \t]+$")
_CONDITIONAL = re.compile(r"(?i)\b(?:if|in case|unless|before|whether|lest|whenever)\b(?:[ \t]+[\w']+){0,3}"
                          r"[ \t]+$")
# A question asks for something only in the form of a request: "Can you forget my old address?"
_REQUEST = re.compile(r"(?i)^\W*(?:(?:and|also|so|oh|ok|okay|hey|then|now|please|actually)\W+)*"
                      r"(?:can|could|would|will)[ \t]+you\b")
_REMINISCES = re.compile(r"(?i)[ \t]+(?:when|how|the time|that time)\b")
_YES = re.compile(r"(?i)^(?:yes|yeah|yep|yup|y|sure|ok|okay|correct|right|confirm(?:ed)?|please do|do it|"
                  r"go ahead)(?:[ ,]+(?:please|thanks|thank you|do it|go ahead|that's right|forget it|"
                  r"remember it|save it|delete it|remove it))*$")


def _asks_any(text):
    return asks(text, "forget") or asks(text, "remember")


def _doubts(lead):
    """Whether the clause the verb is in already holds a negator, as in "I'm not sure I want you to forget". A
    bare "No" before the verb is an answer, not a doubt: "No forget it"."""
    clause = _CLAUSE.split(lead)[-1]
    return NOT in _tokens(clause) and not re.fullmatch(r"(?i)\W*(?:no|nope|nah)\W*", clause)


def ask_spans(sentence, op):
    """Where the sentence asks for op, as (start, end) spans of the words that ask, negator included: "don't
    forget" asks to remember, "stop remembering" to forget, when the negator stands up to four words before the
    verb in the same clause. Nothing asks in a question, unless it is a request ("Can you…?"), nor where the verb
    describes someone ("I always forget", "don't think I'd remember") or a condition ("in case you forget", "not
    sure whether to forget"), nor where a negator further back in the clause doubts it ("I'm not sure I want you
    to forget"), nor in "remember when"."""
    s = sentence.replace("\u2019", "'")
    if s.rstrip().endswith("?") and not _REQUEST.match(s):
        return []
    spans = []
    for m in _VERB.finditer(s):
        verb = re.sub(r"ing$", "", m.group(0).lower())
        kind = "forget" if re.fullmatch(_FORGET_VERB, verb) else "remember"
        negated = _NEG_BEFORE.search(s[:m.start()])
        if negated and _CLAUSE.search(negated.group(0)):  # "I'm not vegan anymore so forget that"
            negated = None
        if negated:  # only "forget" and "remember" turn into each other; "don't save" asks nothing
            meant = {"forget": "remember", "remember": "forget"}.get(verb)
            if meant is None or re.search(r"(?i)\bcan't|\bcant|\bcannot|\bdidn't|\bdidnt|\bdoesn't|\bdoesnt",
                                          negated.group(0)):
                continue
        else:
            meant = kind
        start = negated.start() if negated else m.start()
        lead = s[:start]
        if _DESCRIBES.search(lead) and not _REQUEST_LEAD.search(lead) or _CONDITIONAL.search(lead):
            continue
        if negated and (_CONDITIONAL.search(s[:m.start()]) or _DESCRIBES_OTHER.search(s[:m.start()])):
            continue  # "not sure whether to forget", "don't think I'd remember": the negator isn't on the verb
        if _doubts(lead):
            continue  # "I'm not sure I want you to forget": a negator earlier in the clause
        if verb == "remember" and not negated and _REMINISCES.match(s[m.end():]):
            continue
        if meant == op:
            spans.append((start, m.end()))
    if op == "remember":
        for m in _ADD.finditer(s):
            if not _NEG_BEFORE.search(s[:m.start()]) and not _DESCRIBES.search(s[:m.start()]):
                spans.append(m.span())
    return spans


def asks(sentence, op):
    return bool(ask_spans(sentence, op))


def _blanked(sentence, op):
    """The sentence without the words that ask, so "don't forget" leaves no negator behind."""
    out = sentence.replace("\u2019", "'")
    for start, end in sorted(ask_spans(sentence, op), reverse=True):
        out = out[:start] + " " + out[end:]
    return out


_UNDO = re.compile(r"(?i)^(?:please )?(?:undo(?: that| it| this)?|bring (?:it|that) back|put (?:it|that) back)"
                   r"(?:,? please)?$")


def is_undo(prompt):
    """A bare "undo", in the person's own words."""
    own = own_sentences(prompt)
    return len(own) == 1 and bool(_UNDO.match(_plain(own[0])))


def is_yes(prompt):
    """A bare yes, in the person's own words."""
    own = own_sentences(prompt)
    return len(own) == 1 and bool(_YES.match(_plain(own[0])))


def _counts(text, said):
    want = words(text)
    return len(want & words(said)), len(want)


def covered(op, text, said):
    """Whether the words of text are the person's: all of them to remember, all but one at most to forget."""
    hits, total = _counts(text, said)
    return hits > 0 and total - hits <= (0 if op == "remember" else 1)


def missing(text, said):
    """The words of text the person did not say, as text gives them."""
    have = words(said)
    seen = []
    for w in re.findall(r"[^\W_]+(?:'[^\W_]+)*", text.replace("\u2019", "'")):
        key = w.replace("'", "").lower()
        token = NOT if key in _NEGATORS else None if key in STOP or _HIDDEN.fullmatch(key) else stem(key)
        if token is not None and token not in have and w not in seen:
            seen.append(w)
    return seen


_CLAUSE = re.compile(r"(?i)[,;:()\u2013\u2014]+|\s-\s|\b(?:and|but|because|since|although|though|while|whereas|"
                     r"so|or)\b")


def _negation_differs(text, said):
    """Whether the person's clauses that hold these words say "not" ("no longer", "anymore", "used to"...)
    and the words don't, or the other way round."""
    want = words(text) - {NOT}
    theirs = any(NOT in words(c) for c in _CLAUSE.split(said) if words(c) & want)
    return theirs != (NOT in words(text))


def _in_order(text, said):
    """Whether the words of text come in the order the person said them."""
    seq, at = _tokens(said), 0
    for token in _tokens(text):
        try:
            at = seq.index(token, at) + 1
        except ValueError:
            return False
    return True


class Verdict:
    """ok: the change rests on the person's words. confirm: if not, the person may confirm it with a yes."""

    def __init__(self, ok, why="", confirm=False, unheard=False):
        self.ok, self.why, self.confirm, self.unheard = ok, why, confirm, unheard


NOT_TYPED = "These words aren't in what the person typed in their latest message."
PASTED_WHY = ("These words are only in text the person pasted or quoted, not in words they wrote themselves, so "
              "they aren't the person's ask.")
NEGATION_WHY = ("The person said this with a \"not\" (or \"no longer\", \"anymore\", \"used to\") that these "
                "words leave out, or the other way round.")


def _own_words(sentence, op):
    return words(_blanked(sentence, op)) - {NOT}


def _sources(own, at, op):
    """The person's words a change may rest on: each sentence that holds the quote and asks for op. An ask with no
    words of its own ("forget that") takes them from the sentence before it, and one that ends in a colon
    ("Remember these:") from the line after it. A forget that borrows from the sentence next to it needs a yes:
    "forget that" may only mean "never mind". (words, needs a yes)."""
    for i in at:
        if asks(own[i], op):
            if _own_words(own[i], op):
                yield _blanked(own[i], op), False
            else:
                if i > 0:
                    yield own[i - 1] + " " + _blanked(own[i], op), op == "forget"
                if own[i].rstrip().endswith(":") and i + 1 < len(own):
                    yield _blanked(own[i], op) + " " + own[i + 1], False
        if i + 1 < len(own) and asks(own[i + 1], op) and not _own_words(own[i + 1], op):
            yield own[i] + " " + _blanked(own[i + 1], op), op == "forget"
        if i > 0 and own[i - 1].rstrip().endswith(":") and asks(own[i - 1], op) and not _own_words(own[i - 1], op):
            yield _blanked(own[i - 1], op) + " " + own[i], False


_COPULA = frozenset(("is", "are", "was", "were"))
_LIST_MARK = re.compile(r"^\s*(?:[-*+]|\d+[.)])\s+")
# What starts a second clause in a line's value: another verb, a relative word, or a contraction that is one.
_SECOND_VERB = re.compile(r"(?i)\b(?:is|are|was|were|am|be|been|being|has|have|had|do|does|did|will|would|can|"
                          r"could|shall|should|may|might|must|who|whom|whose|which|that|where|when|because)\b|"
                          r"'(?:m|re|ve|ll|d)\b|n't\b|\b(?:it|he|she|that|there|what|who|where|here)'s\b")


def _subject_named(sentence, said):
    """Whether the person named a line by its subject: "forget my old address" names "My old address is 4 Elm
    St.", though not its value. The subject is the words before the line's first is/are/was/were, which stands
    within its first six words; it has a word that carries meaning, and the person named every one. The value
    after the verb is one clause: no "and", comma or semicolon, and no second verb, so "My test is in March and
    I'm learning to drive." can't go on "forget my test"."""
    parts = _LIST_MARK.sub("", sentence.replace("\u2019", "'")).split()
    at = next((i for i, w in enumerate(parts[:6]) if w.lower().strip(".,;:!?\"'") in _COPULA), None)
    if at is None:
        return False
    subject, value = " ".join(parts[:at]), " ".join(parts[at + 1:])
    named = words(subject)
    return bool(named) and named <= words(said) and not _CLAUSE.search(value) and not _SECOND_VERB.search(value)


def _forget_named(text, said):
    """A forget whose words the person didn't all name passes when the lines they named by subject
    (_subject_named) leave the rest of the text with one unnamed word at most, as any forget may have."""
    lines = _SENTENCES.split(text.replace("\r\n", "\n"))
    hits, total = _counts(" ".join(x for x in lines if not _subject_named(x, said)), said)
    return total - hits <= 1


def _judge(op, text, said, needs_yes):
    hits, total = _counts(text, said)
    if hits == 0:
        return Verdict(False, NOT_TYPED)
    if _negation_differs(text, said):
        return Verdict(False, NEGATION_WHY)
    gone = ", ".join(missing(text, said))
    if op == "remember":
        if hits < total:
            return Verdict(False, "To remember, use only the person's words. They didn't say: %s." % gone)
        if not _in_order(text, said):
            return Verdict(False, "To remember, use the person's words in the order they said them.")
        return Verdict(True)
    if total - hits > 1 and not _forget_named(text, said):
        return Verdict(False, "Forget only what the person named. They didn't name: %s. Or pass only the words "
                              "they named, where those make a whole clause of the line." % gone, hits * 3 >= total)
    if needs_yes:
        return Verdict(False, "The person didn't say which words to forget, and \"forget that\" or \"forget it\" "
                              "can just mean \"never mind\".", True)
    return Verdict(True)


def check(op, quote, text, prompt, salt=None):
    """Whether the person's latest message, in their own words, asks for this change.

    op is "forget" or "remember"; quote is the agent's copy of the person's words; text is the words to
    forget or keep. The words are checked against the sentence that asks, and only an ask with no words of its
    own borrows them from the sentence next to it. salt is the message's (salted): words of the quote that an
    earlier forget hashed in the message are hashed the same way to match, and so are the words to forget. The
    words to remember are not, so a forgotten word counts as not typed for a remember."""
    if prompt is None:
        return Verdict(False, "I don't have the person's latest message, so nothing they typed can stand for "
                              "their yes here.", unheard=True)
    if not isinstance(quote, str) or len(_plain(quote)) < 3:
        return Verdict(False, "quote is the person's own words that ask for this, copied from their latest "
                              "message.")
    hidden = set(_HIDDEN.findall(prompt)) if salt else set()
    if hidden:
        quote = _hide(quote, salt, lambda stems: _hashed(stems, salt) in hidden)
        if op == "forget":
            text = _hide(text, salt, lambda stems: _hashed(stems, salt) in hidden)
    own = own_sentences(prompt)
    # sentence by sentence, as the message is: a quote of two sentences keeps the full stop between them
    wanted = " ".join(p for p in (_plain(x) for x in _SENTENCES.split(_apostrophes(quote))) if p)
    plain = [_plain(x) for x in own]
    joined, spans, place = "", [], 0
    for x in plain:
        spans.append((place, place + len(x)))
        joined += x + " "
        place = len(joined)
    found = joined.find(wanted)
    at = [i for i, (a, b) in enumerate(spans) if found >= 0 and a < found + len(wanted) and found < b]
    tried = []
    for said, needs_yes in _sources(own, at, op):
        verdict = _judge(op, text, said, needs_yes)
        if verdict.ok:
            return verdict
        tried.append(verdict)
    if tried:
        return max(tried, key=lambda v: v.confirm)  # one the person can confirm, if there is one
    if at:
        return Verdict(False, "The person's words there don't ask to %s anything." % op)
    if covered(op, text, prompt) and not covered(op, text, " ".join(own)):
        return Verdict(False, PASTED_WHY)
    return Verdict(False, NOT_TYPED + " Words they pasted, quoted or reported from someone else don't count.")
