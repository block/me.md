# Spec notes from the second host

These are the places where STORE.md, HOST.md or DRIVER.md was unclear, silent, or seemed to contradict itself, while writing `nodehost` from the spec text alone. Each item says what the host chose. Requirement IDs are in bold. "Chose" means a guess that another host may not share. Those are the items most likely to make two hosts disagree.

## The five that matter most

1. **Invalid counts as refused (S6.11, S6.14) is too wide, and it can fire on a file that is still being written.**
   Every invalid file in `proposals/` blocks its body forever. That includes a conflict copy (S8.8), an editor backup that ends in `.md`, and a proposal with a typo in `basis`. Only deleting the file ends it. Worse, S6.2 and S8.5 say "create exclusively" and say nothing about content. A host that does `open(O_EXCL)` then `write` shows other hosts an empty or half-written file. That file is invalid, so it counts as refused, and `pending` reports it. Chose: write a hidden temp file, then hard-link it to the final name (atomic and exclusive), with a plain exclusive create as the fallback. The spec should say proposals appear whole, or say that an invalid file only blocks a body when it is older than a few seconds.

2. **The S6.8 append rule: three open points.**
   (a) Step 2 says the target ends with "the text and one line break". If the target uses mixed line breaks, which break? Chose: LF or CRLF both match, so a retry is never doubled.
   (b) Step 2 is a crash-recovery rule. It also fires when the person's file legitimately ends with the same line, and it does nothing if another proposal landed after the first crash. It reports `applied: "already"` and journals "added" either way, which is a false receipt. Chose: for `already`, the journal's change text says the text was found already at the end.
   (c) DRIVER `edit` append says "the way S6.8 adds a body". Does that include step 2? Chose: no. A person who says "remember X" twice gets two lines. With step 2, the second request would silently do nothing, and there would be nothing to journal.
   Also: "removes the line breaks at its end" is plural. Chose all trailing CR/LF breaks, not trailing spaces, and not leading blank lines. A lone CR is not a line break anywhere in this host.

3. **Forgetting leaves copies in accepted proposals (H5.2, S6.10, S7 intro).**
   STORE.md section 7 says "deleted content leaves no copy here" about the journal. But every accepted proposal in `proposals/` keeps the full body forever. S6.10 makes deleting it a MAY, and DRIVER `forget` repeats the MAY. A host that follows the spec exactly forgets a line in `topics/` while the same line sits in `proposals/<id>.md`. H5.2 says "all state the host controls". Chose: do not delete proposals (the person can, S6.10), and put a notice in the `forget` answer that says so. I think this should be a MUST, or accepted proposals should drop the body when applied.

4. **`policy.json` while off: three gaps (S5.2, S5.6, S2.4, DRIVER `policy`).**
   (a) S2.4 turns memory off for a symbolic `policy.json` and never says how to turn it on again. Chose: the `policy` op replaces the link with a regular file (rename replaces the link and does not follow it). The link's target is untouched.
   (b) S5.2 makes duplicate member names an off case. S5.6 says keep every other member, and replace the file only if it is "not a valid JSON object". Is `{"a":1,"a":2}` valid? It parses. Chose: a file with duplicate names is not usable, so it is replaced with `{"state": ..., "spec": "0.1"}`. Keeping members is impossible when "keep the value of `a`" has two answers.
   (c) The `policy` op needs "store is absent" (me.md missing) to be checked while memory is off, but S5.6 says read nothing else. And DRIVER says other ops answer `off` even when me.md is missing, while `policy` lists `absent`. Chose: `policy` does an `lstat` of me.md only (no read). No me.md means `absent`, even if policy says off.
   Also: S5.6 rewrites keep other members' exact text (including big numbers). `JSON.parse` then `JSON.stringify` would change `12345678901234567890`. The spec allows changing spacing and order but not values.

5. **Error codes and the front-matter grammar leave gaps that every host will fill differently.**
   - No code for an OS error (full disk, permission denied). Chose: an extra code `io_error`. It is not in DRIVER.md.
   - A symlinked or non-directory `topics/`, `projects/` or `proposals/` has no code in `propose`, `edit` or `forget`. Chose: `bad_path` (listed for `edit` and `forget`, not for `propose`). For `decide`, the coordinator's update gave `bad_target`, which this host uses.
   - Empty `basis` in a `propose` request: S6.4 forbids it, DRIVER lists no code. Chose: `bad_request`.
   - Grammar (S6.4): is `key:` with nothing after it a line? Chose: yes, with an empty value (so an unknown key may be empty, a required key may not). Are "spaces" only U+0020? Chose: yes, so a tab-padded value is kept as is. Is a whitespace-only line "blank"? Chose: yes (spaces and tabs). A quoted value that is not closed, or has an escape other than `\"` and `\\`: chose invalid. S6.4 never says.

## STORE.md

- **S1.1** An empty `ME_HOME` counts as unset (an empty path would mean the current directory). A relative `ME_HOME` is resolved against the current directory. `~` in `ME_HOME` is not expanded. If both `ME_HOME` and `HOME` are unset the host falls back to the OS home directory. The spec does not say.
- **S1.2** `me.md` that is a directory, a FIFO, or unreadable: chose absent (not a regular file). `mount` with an `me.md` that is not valid UTF-8: DRIVER says `files` has one item when memory is on, and recall says to skip invalid UTF-8. Chose: skip it, answer `on` with `files: []` and a notice.
- **S2.1** Case-insensitive file systems (macOS default) make `Travel.md` and `travel.md` the same file, and `Topics/` the same directory as `topics/`. The name rules assume a case-sensitive file system. Chose: validate names as text, exactly, before touching the disk. A person on macOS can still hit a case collision. The spec should say so.
- **S2.1** "A host SHOULD tell the person when it ignores a file because of its name." Hidden files are ignored silently (S2.2). Chose: a notice for every non-hidden entry in `topics/` or `projects/` that is not a plain file with a valid name (including directories and links).
- **S2.1, S6.1** Proposal ids are checked as a format (`\d{8}T\d{6}Z-[a-z0-9]{4,}`, at most 64), not as a calendar date. Times in front matter (`proposed-at`, `decided-at`) are checked as real dates, with seconds up to 60 (RFC 3339 leap second). The spec says "RFC 3339" in one place and "as YYYYMMDDTHHMMSSZ" in the other.
- **S2.3** Mixed line endings: "the file's line endings" means the first line break only. A file that mixes CRLF and LF is kept as is, and new text uses the first one. The journal is the one place a host writes LF into a CRLF file (S8.1). The proposal header lines the host adds use the proposal's first line break.
- **S2.4** Links: a link is "as if no file were there". For writes that cannot mean "create the file", because the name is taken and creating would replace the link. Chose: refuse (`bad_path`, or `bad_target` for `decide`). Same for a link to a directory.
- **S2.4** A symlink in `proposals/` named `x.md`: ignored, not invalid. A subdirectory in `proposals/`: ignored.
- **S5.2** "at any depth": needs a JSON parser that reports duplicates. Chose: compare decoded names (so `"state"` duplicates `"state"`). A UTF-8 byte order mark makes the file not valid JSON (off). Invalid UTF-8 is off. The host refuses to read a `policy.json` over 1 MiB (off) and stops at 256 levels of nesting (off). Neither limit is in the spec. Both fail toward off.
- **S5.4** "`spec` is a string MAJOR.MINOR made of digits" and "any other value is unsupported". Chose: supported only if the member is missing, or is exactly the string `"0.1"`. So `"0.01"`, `0.1` (number), `null` and `""` are all unsupported. The spec's own definition of "digits" would let `"00.1"` through as a valid version string that no host supports, which is the same outcome.
- **S5.6** A `policy` request that changes nothing (on when already on) still writes the file and journals "turned memory on". The spec says "at the person's request, MUST write". Chose to follow it literally.
- **S6.3, S6.14** "The first closing `---`": if line 1 is not exactly `---`, there is no opening, so no closing. Chose: the body for refusal matching is then the whole file. If the person typed `--- ` (trailing space) on line 1, a later `---` is not treated as the closing line. A host that reads it the other way blocks different bodies.
- **S6.4** A required key with a quoted empty value `""` is empty (invalid). `decided-at` that is present but malformed makes the proposal invalid. S6.4 only says what the form is. `proposed-by` containing `|` is invalid (S7.2 says a host field must not). The form of `proposed-by` beyond that is not checked, because the spec gives no grammar for a host field.
- **S6.6** "One blank line after it is skipped." Chose: a blank line is spaces and tabs only. If the proposal has no blank line, there is none to skip.
- **S6.6, DRIVER `pending`** Does `body` include its final line break? The body is "everything after the closing `---`", so it does. Chose: `pending.body` has the trailing line breaks removed, the way S6.8 step 1 does. Internal breaks, CRLF included, are as in the file. A runner that compares to the raw file text will see a difference.
- **S6.11** The normalizer uses the Unicode White_Space set (it includes U+0085 and excludes U+FEFF). JavaScript's `\s` differs on both, so the host spells the set out. The spec says only "white space".
- **S6.14** An invalid proposal's body is decoded lossily when the file is not UTF-8, so a refusal still holds.
- **S6.15** `revise` keeps the front matter byte for byte, then writes one blank line, the body, and one line break, in the proposal's own line-break style. If the original had no blank line after the closing `---`, one appears.
- **S7.1** `<change>` is free text, and "never the content". The host uses fixed phrases ("added text", "replaced text", "removed text", "removed the file", "added proposed text", "created the file with proposed text", "found the proposed text already at the end", "turned memory on").
- **S7.3** Does not require journaling `revise` (a durable change to a proposal file) or deleting a proposal. Chose: journal neither. Removing `me.md` through `forget` is journaled, because it is a removal of `me.md`.
- **S8.1, S8.6** The two entries of an acceptance are written as two single writes, not one write of two lines. With two hosts writing, other entries can fall between the decision and the content entry. S8.6 step 5 and S7.3 say "the decision, then the content change" and do not say adjacent. T13 should say whether a reader may rely on that.
- **S8.2** The lock line is "a random token, its host name, and the time" with no separator. A host name with a version has a space ("examplehost 1.0"). Chose: space separated, host name without version, token first (32 hex characters). A reader that wants to parse it cannot, in general. The spec should pick a separator.
- **S8.2, S8.3** "A few seconds" of waiting: chose 3 s, 10 to 40 ms between tries. A stale lock is never removed automatically, so a crashed host blocks every Steward until the person deletes `.me.lock`. That is the spec's choice, but it means one crash stops all writes with no age or pid to check.
- **S8.4** Step 3 compares bytes to the first read. It does not say what to do when the target does not exist (a new topic). Chose: treat "missing" as a snapshot, and create the file with a hard link so it can never replace a file that appeared in between. Step 2's temp name `.<name>.tmp` is fixed, which is safe only under the lock. Proposal creation has no lock (S8.5), so it uses a random temp name.
- **S8.6** The status write (step 3) happens after the content write (step 2) with the lock held. If the proposal file changed between the first check and step 3 (an editor), the host re-parses and fails with `invalid_proposal` or `not_pending`, after the content is already applied. The spec's crash rule (retry sees the body at the end) covers the retry, but not "the person edited the proposal into something else in between".
- **S8.6** `decided-via`: optional in S6.4. Chose to write it (`nodehost 0.1.0`, no agent) after `decided-at`. If the proposal already has `decided-at` or `decided-via`, they are replaced in place, because a second key would make the file invalid.
- **H1.6** "Read `policy.json` again before each write". Chose also to read it again after taking the lock, so a switch flipped during the wait still wins.
- **H5.2** The host has no caches and keeps nothing between requests, so this requirement cannot be exercised on it. A conformance runner should not read "no copy found" as evidence for a host that never had one.

## DRIVER.md

- Unknown `op`, and ops above the level (`briefing`): `unsupported_op`. A request that is not a JSON object, or has no string `op`: `bad_request` with `id` null if there is no `id`. Blank input lines are skipped with no response. The doc says "one response per line", and a blank line is not a request.
- `propose` used `id` for the new proposal in the first draft, which collides with the request `id`. The coordinator fixed it to `proposal`. This host answers `proposal` and `file`.
- Error answers carry `memory` where the host knows it. `writable: false` appears on any answer when memory is on and the spec is unsupported.
- `store` is the absolute `ME_HOME` as given (resolved, not `realpath`). On macOS a temp dir under `/var` is `/private/var` after `realpath`. A runner that compares paths needs to know which.
- `pending.proposals[].file` and `invalid[].file` are store-relative paths (`proposals/<id>.md`), as in `propose`. The doc says "file" for invalid and does not say.
- `list` names are sorted by UTF-16 code unit. The doc gives no order.
- `decide` looks up `proposals/<proposal>.md`. An id that has a path separator, starts with `.`, or ends in `.md` is `not_found`. A file with a bad name (invalid by S6.1) can still be looked up by its stem, and answers `invalid_proposal`.
- `decide` error order: `absent`, `memory_off`, `unsupported_spec`, then the lock (`locked`), then `not_found`, `invalid_proposal`, `not_pending`, `bad_target`. The lock is taken before the proposal is read (S8.6 step 1), so `locked` can hide `not_found`.
- `propose` error order: `absent`, `memory_off`, `unsupported_spec`, `bad_target`, `empty_body`, `bad_request` (empty basis), `refused`.
- `propose` flattens line breaks in `basis` and `agent` to spaces, and replaces `|` in `agent` (S7.2), because front-matter values are one line. It converts CRLF in `body` to LF, because new files are LF (S2.3). "Exactly the words to keep" is not quite exact for a CRLF body.
- `edit` `replace`: `old` and `new` are converted to the file's line break. A file with mixed breaks may not match a multi-line `old`. Matching is bytewise and counts overlapping hits for `ambiguous`. An empty `old` is `bad_request`.
- `forget` with `text`: "fills whole lines" is read as: split the text into lines (trailing breaks dropped), then remove each run of file lines equal to them, left to right, without overlap. Case-sensitive, exact. An empty `text` is `bad_request`. The path set is the same as for `edit`; a proposal, `journal.md` or `policy.json` is `bad_path`, so the person cannot delete a proposal through the driver (S6.10 says they can, with an editor).
- `forget` without `text` on `me.md` deletes it and the store becomes absent. The spec does not say whether that is allowed. The answer's `memory` is the state after the change, as for `policy`.
- `forget` always adds a notice naming what it cannot delete (H5.3), including the accepted-proposal copies from item 3.
- `locked`: the host waits `THOU_LOCK_WAIT_MS` (default 3000). A runner with a shorter timeout will read this as a hang.
- `recall`: a path that appears twice is answered twice. `watches.md` with `purpose: "task"` is skipped. Reasons are free text.

## HOST.md

- **H1.5 and T3** "Off means no recall, no injection, no proposals, no tooling that implies memory." A driver cannot show "no tooling". It can only show that every op answers `off` and writes nothing.
- **T9** The test says to refuse by editing `status: refused` in an editor, which leaves `decided-at` out. That is valid (decided-at is optional). The invalid typo case is the second step. Both are in this host's tests.
- **T16** "The new text starts on a new line and uses CRLF" is consistent with S6.8. "A line the host cannot parse" has no meaning for `me.md`, which has no grammar (S3). The test is really about bytes.
- **H3.6** Showing a proposal alone when its body "tells agents when to act" has no driver op. Nothing here detects it.

## What I think the spec gets wrong

- Invalid-as-refused (S6.14) trades a real safety property (a mistyped refusal still holds) for a way to lose proposals by accident. It should apply only to files whose front matter shows a refusal (any key that reads `refused`, case-insensitive), not to every invalid file.
- The accepted proposal as a permanent copy of memory (S6.10, H5.2, S7 intro). See item 3.
- S8.2 has no way to tell a live lock from a dead one. A token, host and time are written but nothing says what to do with the time.
- The `policy.json` symlink case is an off switch the person cannot flip back through any documented path (S2.4 versus S5.6).
- DRIVER's `forget` MAY delete accepted proposals "that carry the same text". "The same text" is not defined (equal normalized body? contains?).
- S6.1 gives proposal ids no clock rule. Two hosts on two machines with a skewed clock can write ids that sort in the wrong order. Nothing in the spec sorts by id, but `pending` order in the driver is by file name, and a runner might expect creation order.
