"""forgotten.json: what keeps forgotten words from coming back in a proposal, without the words (STORE.md S10).

The method thou-stems-1. After a forget, the host adds an item: for each forgotten sentence, the salted hashes
of its words that carry meaning (said.words), as one sorted list. A sentence with a negator ("not", "no
longer", "used to"...) also holds the hash of the negator.

Before it writes a proposal, the host leaves out each line of the body that holds at least two thirds of a
forgotten sentence's word hashes, not counting the negator's. So a restatement with a "not" still matches: "not
vegetarian anymore, don't re-add it" holds "vegetarian". An item goes when the person says the same words again
in their own words, with the same negation (S10.5).

The file holds no words, no file names and no other text. Anyone who can read it and guess a word can test the
guess, so it is not a secret from someone who guesses. The salt, random for each store, keeps a list of hashes
made for one store from working on another.
"""

import hashlib
import json
import re
import secrets

from . import said

FILE = "forgotten.json"
METHOD = "thou-stems-1"
MOST_ITEMS = 500  # S10.5: when a host adds one more, the oldest goes
MOST_SENTENCES = 200  # in one item
_HASH = re.compile(r"[0-9a-f]{16,64}")
_SALT = re.compile(r"[0-9a-f]{32,64}")
_SENTENCE = re.compile(r"(?<=[.!?;])\s+|\n+")


class Unreadable(ValueError):
    """forgotten.json is there, but it isn't a file this host can read and rewrite safely."""


def new_salt():
    return secrets.token_hex(16)


def _hash(salt, stem):
    return hashlib.sha256(bytes.fromhex(salt) + stem.encode("utf-8")).hexdigest()[:16]


def sentence_hashes(salt, text):
    """One sorted list of hashes for each sentence of text that has words carrying meaning."""
    out = []
    for sentence in _SENTENCE.split(text or ""):
        stems = said.words(sentence)
        if stems - {said.NOT}:
            out.append(sorted(_hash(salt, s) for s in stems))
    return out[:MOST_SENTENCES]


def parse(data):
    """The file's object, checked: {"salt": hex, "items": [{"id", "at", "method", "lines": [[hex, ...], ...]}]}.
    None for no file."""
    if data is None:
        return None
    try:
        obj = json.loads(data.decode("utf-8"))
    except (UnicodeDecodeError, ValueError):
        raise Unreadable("it is not JSON")
    if not isinstance(obj, dict) or set(obj) != {"salt", "items"}:
        raise Unreadable("it is not an object with only salt and items")
    if not isinstance(obj["salt"], str) or not _SALT.fullmatch(obj["salt"]):
        raise Unreadable("its salt is not 32 to 64 lowercase hex characters")
    if not isinstance(obj["items"], list):
        raise Unreadable("its items are not a list")
    for item in obj["items"]:
        if not isinstance(item, dict) or set(item) != {"id", "at", "method", "lines"} or \
                not all(isinstance(item[k], str) for k in ("id", "at", "method")) or \
                not isinstance(item["lines"], list):
            raise Unreadable("an item is not {id, at, method, lines}")
        for line in item["lines"]:
            if not isinstance(line, list) or not line or \
                    not all(isinstance(h, str) and _HASH.fullmatch(h) for h in line):
                raise Unreadable("an item's lines are not lists of hashes")
    return obj


def dump(obj):
    return (json.dumps(obj, indent=1) + "\n").encode("utf-8")


def added(data, item_id, when, text):
    """The file's new bytes with one more item for text, or None when text has no words to keep out. The oldest
    items go past MOST_ITEMS."""
    obj = parse(data) or {"salt": new_salt(), "items": []}
    lines = sentence_hashes(obj["salt"], text)
    if not lines:
        return None
    obj["items"] = (obj["items"] + [{"id": item_id, "at": when, "method": METHOD, "lines": lines}])[-MOST_ITEMS:]
    return dump(obj)


def _holds(have, line, negator):
    """Whether hashes have hold at least two thirds of a forgotten sentence's word hashes."""
    want = set(line) - {negator}
    hits = len(set(have) & want)
    return hits > 0 and hits * 3 >= len(want) * 2


def _ours(obj):
    return [i for i in obj["items"] if i["method"] == METHOD] if obj else []


def matching(obj, text):
    """The items one of whose forgotten sentences text holds, with or without a negator."""
    if not obj:
        return []
    negator = _hash(obj["salt"], said.NOT)
    have = {h for sentence in sentence_hashes(obj["salt"], text) for h in sentence}
    return [i for i in _ours(obj) if any(_holds(have, line, negator) for line in i["lines"])]


def kept_lines(obj, body):
    """The lines of a proposal body that hold no forgotten sentence, and how many were left out (S10.4)."""
    if not obj:
        return body, 0
    out, left_out = [], 0
    for line in body.splitlines(True):
        if line.strip() and matching(obj, line):
            left_out += 1
        else:
            out.append(line)
    return "".join(out), left_out


def covered_items(obj, text):
    """The items text says again: each forgotten sentence held by a sentence of text with the same negation."""
    if not obj:
        return []
    negator = _hash(obj["salt"], said.NOT)
    mine = sentence_hashes(obj["salt"], text)

    def said_again(line):
        return any(_holds(s, line, negator) and (negator in s) == (negator in line) for s in mine)
    return [i for i in _ours(obj) if all(said_again(line) for line in i["lines"])]


def same_words(obj, item_id, text):
    """Whether text has exactly the words of the item item_id: the same sentences, the same hashes."""
    for item in _ours(obj):
        if item["id"] == item_id:
            return sorted(map(tuple, sentence_hashes(obj["salt"], text))) == sorted(map(tuple, item["lines"]))
    return False


def without(data, ids):
    """The file's new bytes without the items ids, or None when none of them is there."""
    obj = parse(data)
    if not obj:
        return None
    kept = [i for i in obj["items"] if i["id"] not in ids]
    if len(kept) == len(obj["items"]):
        return None
    obj["items"] = kept
    return dump(obj)
