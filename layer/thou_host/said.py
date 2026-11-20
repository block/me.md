"""Quoted consent: what the person typed, and whether a change rests on it (HOST.md H3.7, SOVEREIGNTY.md).

A client hook (Claude Code's UserPromptSubmit) records the person's latest message in a file outside the
store, one per client process, numbered within the session. The thou server reads it when an agent calls remember or
forget, and applies the change at once only when the person's own words ask for it:

- the quote is in the person's latest message, in words they wrote themselves: not a line they pasted after
  `>`, not a fenced block, not words in quotation marks, and not the rest of a sentence that reports what
  someone else said or wrote;
- the sentence around the quote asks for that operation: "forget", "delete" or "remove" for forget, and
  "remember", "note" or "save" for remember, without a "don't" or "never" in front;
- the words match what the person said. To remember, every word that carries meaning must be the person's.
  To forget, all but one at most, so "forget about Mochi" can take the line "I have a cat called Mochi."
  but "forget that my test is in March" can't take "I'm learning to drive and my test is in March."

Words from an email or a web page are not in what the person typed, so they can't pass. Everything that
doesn't pass changes nothing. Where the person pasted or quoted the words, or named at least half of them,
the agent may ask them, and a bare yes in their next message confirms (thou_mcp.Said).

The file is the person's words, so only the client's hook writes it and only the server reads it. The
pre-tool-use hook keeps Claude Code's own tools out of its folder, as it does for the store.
"""

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


def record(prompt, who=None):
    """The hook: keep the person's latest message for this client, replacing the one before."""
    who = who or client()
    before = _read(who)
    number = before["n"] + 1 if before and isinstance(before.get("n"), int) else 1
    session = before.get("session") if before and isinstance(before.get("session"), str) else os.urandom(8).hex()
    _write(who, {"prompt": prompt[:MOST_PROMPT], "at": time.time(), "n": number, "session": session,
                 "client": list(who)})


def scrub(text, who=None):
    """After a forget: take the sentences that hold its words out of the kept message, so the layer keeps no
    copy of them (H5.2). The other sentences stay, for a remember in the same message."""
    who = who or client()
    data = _read(who)
    if not data or not isinstance(data.get("prompt"), str):
        return
    gone = words(text)
    kept = [s for s in _SENTENCES.split(_apostrophes(data["prompt"]).replace("\r\n", "\n"))
            if s.strip() and not (words(s) & gone)]
    _write(who, dict(data, prompt="\n".join(kept)))


def _write(who, record):
    place = folder()
    os.makedirs(place, mode=0o700, exist_ok=True)
    data = json.dumps(record)
    handle, temp = tempfile.mkstemp(dir=place, prefix=".said-")
    try:
        with os.fdopen(handle, "w") as out:
            out.write(data)
        os.chmod(temp, 0o600)
        os.replace(temp, _path(who))
    except BaseException:
        try:
            os.unlink(temp)
        except OSError:
            pass
        raise


def clear(who=None):
    """At session start: no message yet."""
    try:
        os.unlink(_path(who or client()))
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
    data = _read(who or client())
    prompt = data and data.get("prompt")
    number = data and data.get("n")
    session = data and data.get("session")
    if not isinstance(prompt, str) or not isinstance(number, int) or isinstance(number, bool) or \
            not isinstance(session, str):
        return None, None
    return prompt, (session, number)


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
not no never longer anymore any more now just also very really still again too please thanks thank bit
part parts thing things stuff one two three four five six seven eight nine ten called named
forget forgets forgetting delete remove erase wipe scrub remember remembering note save keep mind write
down add memory memories store file line
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


def words(text):
    """The words that carry meaning, as stems: no small words, no "not", no operation words."""
    text = unicodedata.normalize("NFKC", text).replace("’", "'").replace("'", "").lower()
    return {stem(w) for w in re.findall(r"[^\W_]+", text) if w not in STOP}


_NEGATED = r"(?<!\bdon't )(?<!\bdont )(?<!\bdo not )(?<!\bnever )(?<!\bnot )(?<!\bwon't )(?<!\bcan't )"
_FORGET = re.compile(r"(?i)" + _NEGATED + r"\b(?:forget|delete|remove|erase|wipe)\b|"
                     r"\b(?:stop|don't|dont|do not|no longer) remember(?:ing)?\b")
_REMEMBER = re.compile(r"(?i)\b(?:don't|dont|do not|never) forget\b|" + _NEGATED.replace("never", "stop") +
                       r"(?<!\bno longer )\b(?:remember|memori[sz]e|make a note|note|keep in mind|save|"
                       r"write (?:it |this |that )?down)\b|" + _NEGATED.replace("never", "stop") +
                       r"\b(?:add|put)\b[^.!?\n]{0,60}?\b(?:to|in|into) (?:my |your |the )?"
                       r"(?:me\.md|memory|memories|thou|profile)\b")
_YES = re.compile(r"(?i)^(?:yes|yeah|yep|yup|y|sure|ok|okay|correct|right|confirm(?:ed)?|please do|do it|"
                  r"go ahead)(?:[ ,]+(?:please|thanks|thank you|do it|go ahead|that's right|forget it|"
                  r"remember it|save it|delete it|remove it))*$")


def _asks_any(text):
    return asks(text, "forget") or asks(text, "remember")


def asks(sentence, op):
    sentence = sentence.replace("’", "'")
    return bool((_FORGET if op == "forget" else _REMEMBER).search(sentence))


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
        if key not in STOP and stem(key) not in have and w not in seen:
            seen.append(w)
    return seen


class Verdict:
    """ok: the change rests on the person's words. confirm: if not, the person may confirm it with a yes."""

    def __init__(self, ok, why="", confirm=False, unheard=False):
        self.ok, self.why, self.confirm, self.unheard = ok, why, confirm, unheard


def check(op, quote, text, prompt):
    """Whether the person's latest message, in their own words, asks for this change.

    op is "forget" or "remember"; quote is the agent's copy of the person's words; text is the words to
    forget or keep."""
    if prompt is None:
        return Verdict(False, "I don't have the person's latest message, so nothing they typed can stand for "
                              "their yes here.", unheard=True)
    pasted = covered(op, text, prompt)
    if not isinstance(quote, str) or len(_plain(quote)) < 3:
        return Verdict(False, "quote is the person's own words that ask for this, copied from their latest "
                              "message.", pasted)
    own = own_sentences(prompt)
    wanted = _plain(quote)
    plain = [_plain(x) for x in own]
    joined, spans, place = "", [], 0
    for x in plain:
        spans.append((place, place + len(x)))
        joined += x + " "
        place = len(joined)
    found = joined.find(wanted)
    at = [i for i, (a, b) in enumerate(spans) if found >= 0 and a < found + len(wanted) and found < b]
    if not at:
        return Verdict(False, "Those words are not in the person's latest message as their own words. Words "
                              "they pasted, quoted or reported from someone else don't count.", pasted)
    for i in at:
        window = " ".join(own[max(0, i - 1):i + 2])
        if not any(asks(s, op) for s in own[max(0, i - 1):i + 2]):
            continue
        if covered(op, text, window):
            return Verdict(True)
        hits, total = _counts(text, window)
        near = pasted or hits * 2 >= total
        gone = ", ".join(missing(text, window))
        if op == "remember":
            return Verdict(False, "To remember, use only the person's words. They didn't say: %s." % gone, near)
        return Verdict(False, "Forget only what the person named. They didn't name: %s. Pass fewer words, such as "
                              "the part of the line they named." % gone, near)
    return Verdict(False, "The person's words there don't ask to %s anything." % op, pasted)
