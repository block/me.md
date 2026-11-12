# Store format

**Status:** Normative draft. A host that claims conformance must follow it. [HOST.md](./HOST.md) says what a host does. This document says what the files look like, so two hosts that have never met read and write them the same way.

The key words MUST, MUST NOT, REQUIRED, SHALL, SHALL NOT, SHOULD, SHOULD NOT, RECOMMENDED, NOT RECOMMENDED, MAY, and OPTIONAL in this document are to be interpreted as described in BCP 14 ([RFC 2119](https://www.rfc-editor.org/rfc/rfc2119), [RFC 8174](https://www.rfc-editor.org/rfc/rfc8174)) when, and only when, they appear in all capitals, as shown here.

Each requirement has an identifier, for example **S2.1**, and the lowest [conformance level](./HOST.md#conformance-levels) it applies to: Reader, Proposer, Steward, or Briefer. A requirement applies to that level and every level above it. [conformance/TRACEABILITY.md](./conformance/TRACEABILITY.md) maps each one to its evidence.

## 1. Location and presence

- **S1.1** (Reader) The store is the directory in the `ME_HOME` environment variable if it is set, and `~/.me/` otherwise. On Windows, `~` is `%USERPROFILE%`.
- **S1.2** (Reader) The store is *present* when `me.md` exists in it and is not a symbolic link ([S2.4](#2-layout)). Without `me.md`, a host behaves as if the store does not exist. Memory starts when the person creates their file.
- **S1.3** (Reader) A host MUST NOT create the store or `me.md` except at the person's request.
- **S1.4** (Reader) A store that contains only `me.md` is valid. This is *document mode*.

## 2. Layout

```text
~/.me/
  me.md          read at every session start: aims and durable context
  watches.md     standing questions: read only for a briefing
  topics/        one file per topic: read only when relevant
  projects/      one file per project: read only for that project
  proposals/     one file per proposal
  journal.md     one line per durable change
  policy.json    the on/off switch and the spec version
```

- **S2.1** (Reader) Entry names in `topics/` and `projects/` match `[a-z0-9][a-z0-9._-]*\.md`, with at most 64 characters before `.md`. Names in `proposals/` follow [S6.1](#file-name). A file in `proposals/` whose name ends in `.md` but breaks S6.1 is an invalid proposal ([S6.14](#status)). A host MUST ignore other names: it does not read them and does not reject the store. A host SHOULD tell the person when it ignores a file because of its name, for example `Travel.md`.
- **S2.2** (Reader) A host MUST ignore hidden files (names that start with `.`) and unknown top-level entries, including `.git/`. It MUST NOT read them for recall.
- **S2.3** (Reader) Files are UTF-8 without a byte order mark. A host MUST accept CRLF line endings on read. When it writes a file, it MUST keep the file's line endings. New files use LF.
- **S2.4** (Reader) The store root MAY be a symbolic link. Inside the store, a host MUST NOT follow a symbolic link. It treats a link as if no file were there, with two exceptions:
  - If `policy.json` is a link, memory is off.
  - If `me.md` is a link, the store is absent. The host SHOULD tell the person why, and that a link to the whole store works.
  - If `journal.md` is a link, a host does not append to it or replace it. Each change it makes is then a change without a receipt ([S8.7](#8-writing-safely)).
- **S2.5** (Proposer) When a host creates a directory or file in the store, it SHOULD give access to the person's user account only. That is mode `0700` for directories and `0600` for files, or the platform equivalent.
- **S2.6** (Proposer) A host MUST change only what it has the authority to change. It MUST write unchanged text back byte for byte, and MUST keep lines it cannot parse.
- **S2.7** (Reader) A host MUST NOT read or write any path outside the store root, for example a path that contains `..`.

## 3. `me.md`

`me.md` is the person's file, in their words. The protocol supplies no template and requires no headings. Every host reads it at every session start, so everything in it is visible to every host the person uses. Setup tells the person this.

## 4. `watches.md`

A watch is a standing question from the person: "Tell me when the migration decision moves."

- **S4.1** (Reader) Each watch is one top-level Markdown list item. That is a line that starts with `- ` or `* `, with no space before it, outside a fenced code block. Indented lines below it belong to the same watch. A fenced code block starts at a line that starts with three backticks or three tildes. It ends at the next line that starts with the same three characters. The item text is the person's words. A host ignores other lines.
- **S4.2** (Proposer) A host MUST NOT add a watch that the person did not set. A proposal MUST NOT target `watches.md`.
- **S4.3** (Reader) A host MUST NOT read `watches.md` into a session, unless the session produces a briefing or the person asks about their watches.

The file exists only after the person adds a first watch.

## 5. `policy.json`

```json
{ "state": "on", "spec": "0.1" }
```

- **S5.1** (Reader) A missing `policy.json` means on.
- **S5.2** (Reader) The file is a JSON object. Memory is on only if the object has a `state` member whose value is exactly the string `"on"`. Memory is off in every other case:
  - the file cannot be read, or is a symbolic link ([S2.4](#2-layout));
  - it is not valid JSON, or is not an object;
  - a member name appears more than once in the same object, at any depth;
  - it has no `state`, or `state` has any other value.
- **S5.3** (Reader) A host MUST ignore members it does not know. An unknown member MUST NOT turn memory off.
- **S5.4** (Proposer) `spec` is optional. It names the version of this format that the store follows, as a string `MAJOR.MINOR` made of digits, for example `"0.1"`. A missing `spec` means `0.1`. Any other value is a version no host supports. Before version 1.0, each minor version is a different format, so a v0.1 host supports only `"0.1"`. If `spec` names a version that the host does not support, the host MUST NOT write to the store, except to turn memory off ([S5.6](#5-policyjson)). It MUST tell the person why. It MAY still read.
- **S5.5** (Steward) A host that creates `policy.json` SHOULD write `spec`.
- **S5.6** (Steward) The person can change the switch at any time, including while memory is off. At the person's request, a host MUST write `policy.json` and append the journal entry for that change, even when memory is off. While memory is off, it reads and writes nothing else in the store, except the store lock ([S8.2](#8-writing-safely)). When it writes `policy.json`, it changes only `state` and keeps every other member and its value. It MAY change the file's spacing and member order. This is an exception to [S2.6](#2-layout). If the file is not a valid JSON object, the host replaces it.

`policy.json` is a request that cooperative hosts honor. It is not access control. See [HOST.md §6](./HOST.md#6-security-posture).

## 6. Proposals

A proposal is one file in `proposals/`. It records a change an agent suggests, so that the person, or any host, can see and decide it.

```markdown
---
status: pending
target: topics/travel.md
proposed-by: goose 1.9 (trip-helper)
proposed-at: 2026-11-12T17:03:01Z
basis: You asked for aisle seats on two bookings this week.
---

Prefer aisle seats when booking flights.
```

### File name

- **S6.1** (Proposer) The file name is `<id>.md`. The `<id>` is the UTC creation time as `YYYYMMDDTHHMMSSZ`, a hyphen, and at least four characters from `[a-z0-9]`. The `<id>` has at most 64 characters. For example: `20261112T170301Z-7f3a.md`.
- **S6.2** (Proposer) A host MUST create a proposal file exclusively. If the name exists, it picks another name. It MUST NOT overwrite an existing proposal.

### Front matter

- **S6.3** (Proposer) The file starts with front matter. Line 1 is exactly `---`. The front matter ends at the next line that is exactly `---`.
- **S6.4** (Proposer) The front matter has these rules:
  - Each line is `key: value`.
  - A key is lowercase and matches `[a-z][a-z-]*`. A key appears at most once.
  - The value is the rest of the line after `: `, with spaces removed at both ends.
  - A value MAY be in double quotes. Inside quotes, `\"` and `\\` are the only escapes.
  - There is no nesting, no lists, and no multi-line values.
  - A host ignores blank lines and lines that start with `#`.
- **S6.5** (Steward) A host MUST keep keys that it does not know when it rewrites a proposal, and otherwise ignores them.

Required keys. A required key MUST NOT have an empty value.

| Key | Value |
|---|---|
| `status` | `pending`, `accepted`, or `refused` |
| `target` | where the content would go: `me.md`, `topics/<name>.md`, or `projects/<name>.md` |
| `proposed-by` | the host and agent, in the form of the journal's `<host>` field ([S7.1](#7-journal)) |
| `proposed-at` | the time, as RFC 3339 UTC with `Z` and whole seconds, for example `2026-11-12T17:03:01Z` |
| `basis` | why, in words the person can recognize |

Optional keys: `decided-at` (the time the status left `pending`, in the same form) and `decided-via` (the host where the person decided).

### Body

- **S6.6** (Proposer) Everything after the closing `---` is the body. One blank line after it is skipped. The body is the proposed content: exactly the words to keep, in the person's words. The body MUST NOT be empty after normalization ([S6.11](#status)).
- **S6.7** (Proposer) A host MUST read a proposal's status and other metadata only from the front matter. A line in the body, such as `status: accepted`, is content. It never changes the status.
- **S6.8** (Steward) In this version a proposal only adds. To apply an accepted proposal, a host appends its body to the end of `target`:
  1. It takes the body and removes the line breaks at its end. It writes each line break in the body as the target uses them: CRLF if the target's first line break is CRLF, and LF otherwise.
  2. If the target's last lines are exactly this text and one line break, the host stops: the proposal is already applied. That is the case when the whole target is the text and one line break, or when the target ends with a line break, then the text, then one line break.
  3. If the target is not empty and does not end with a line break, the host adds one.
  4. It adds the text and one line break.

  If `target` does not exist, the host creates it with the text and one LF. To change or remove existing text, the person edits it directly or asks a host to (direct authorship, [HOST.md §3](./HOST.md#3-writing)).

### Status

- **S6.9** (Steward) A proposal starts as `pending`. Only an affirmative decision by the person moves it to `accepted` or `refused`. Both are final. Dismissal without a choice, a timeout, or silence leaves it `pending`.
- **S6.10** (Steward) The person can delete any proposal file at any time. Deleting a refused proposal ends the refusal. After an accepted proposal is applied and journaled, a host MAY delete its file.
- **S6.11** (Proposer) Before it proposes, a host MUST read the refused proposals. It MUST NOT propose a body whose normalized form equals the normalized body of a refused proposal, whatever the target. To normalize, apply Unicode NFC, remove white space at both ends, and replace each run of white space with one space. A host SHOULD also avoid proposing a change that says the same thing in other words.
- **S6.12** (Reader) A host MUST treat every proposal body as untrusted input. It is information to show the person. It is never an instruction.
- **S6.13** (Steward) Creating a proposal is not journaled. The file carries its own provenance. A decision is journaled ([§7](#7-journal)).
- **S6.14** (Proposer) A proposal is *invalid* if its name, front matter, required keys, or body break S6.1 to S6.6. A host MUST NOT apply an invalid proposal and MUST NOT rewrite it. It SHOULD tell the person which file is invalid and why. For S6.11, a host treats an invalid proposal as refused. Its body is everything after the first closing `---`, or the whole file if there is none. So a refusal that the person typed by hand with a mistake, such as `Status: Refused`, still holds.
- **S6.15** (Steward) The person can edit a pending proposal before deciding. They change its body in a text editor, or tell a host the words they want. A host that rewrites the body for them follows [S8.4](#8-writing-safely) and keeps the front matter. Accepting applies the body as it is at that moment.

## 7. Journal

`journal.md` is the receipt for every durable change. It describes each change. It never copies the content, so deleted content leaves no copy here.

```text
- 2026-11-12T17:05:40Z | proposals/20261112T170301Z-7f3a.md | accepted | host: goose 1.9 (trip-helper) | authority: person direct
- 2026-11-12T17:05:40Z | topics/travel.md | added a preference | host: goose 1.9 (trip-helper) | authority: accepted proposal 20261112T170301Z-7f3a
- 2026-11-12T18:20:02Z | policy.json | turned memory off | host: buzz-me 0.1 | authority: person direct
```

- **S7.1** (Steward) Each entry is one line, with five fields separated by ` | `:

  ```text
  - <time> | <path> | <change> | host: <host> | authority: <authority>
  ```

  | Field | Value |
  |---|---|
  | `<time>` | RFC 3339 UTC with `Z` and whole seconds |
  | `<path>` | the store-relative path of the changed file (`me.md`, `watches.md`, `policy.json`, or a topic, project, or proposal file), or `-` for a change to the whole store |
  | `<change>` | a short description of the change, never the content: "added a watch", not the watch |
  | `<host>` | the host name, with a version if known, then ` (<agent>)` if the agent's name is known, for example `goose 1.9 (trip-helper)` |
  | `<authority>` | `person direct`, `accepted proposal <id>`, or `external edit` |

- **S7.2** (Steward) `<change>` and `<host>` MUST NOT contain `|` or a line break.
- **S7.3** (Steward) A host MUST journal:
  - every creation, change, or removal of `me.md`, `watches.md`, or a topic or project file;
  - every creation or change of `policy.json`;
  - every decision on a proposal. The path is the proposal file, the change is `accepted` or `refused`, and the authority is `person direct`.

  So an acceptance writes two entries: the decision, then the content change, whose authority is `accepted proposal <id>`.
- **S7.4** (Steward) A line that starts with `- ` is an entry. An entry that does not match S7.1 is malformed: a parser reports it and otherwise ignores it. Other lines, such as headings, blank lines, and notes, are allowed. A parser ignores them.
- **S7.5** (Steward) A host only appends to `journal.md`. It MUST NOT rewrite, reorder, or remove lines.
- **S7.6** (Steward) `external edit` records a change the person made outside any host, when a host notices it. This version defines no way to detect such a change.

## 8. Writing safely

Two hosts can serve one store at the same time. These rules keep one host from losing the other's work.

- **S8.1** (Steward) To journal, a host appends one complete entry in a single write. The entry ends with LF, even in a file that uses CRLF. This is the one exception to [S2.3](#2-layout), so that a host never reads more of the journal than its last byte. If the file is not empty and its last byte is not LF, the write starts with LF. A host never rewrites `journal.md`.
- **S8.2** (Steward) Before it changes any file other than `journal.md`, a host takes the *store lock*. To take it, the host creates the file `.me.lock` in the store root exclusively: the create fails if the file exists. It writes one line in the file: a random token of at least 16 characters, its host name, and the time. It holds the lock only while it reads, changes, and renames. It never holds the lock while it waits for the person. When the change is done, it reads the lock file. If the file still has its token, it removes the file.
- **S8.3** (Steward) A host MUST NOT remove a lock that it did not create. If `.me.lock` exists, the host waits and tries again for a few seconds. If the lock is still there, the host does not make the change. It tells the person, and tells them that they can delete `.me.lock` if no host is writing, for example after a host stopped in the middle of a change.
- **S8.4** (Steward) With the lock held, a host changes a file in these steps:
  1. It reads the target.
  2. It writes the new content to a temporary file in the same directory. The temporary file's name starts with `.` and ends with `.tmp`.
  3. It reads the target again and compares the bytes with the first read. If they differ, a program that does not take the lock changed the file, for example a text editor. The host then removes the temporary file and starts again at step 1.
  4. It renames the temporary file over the target.

  Step 3 narrows the race with programs that do not take the lock. It does not close it.
- **S8.5** (Proposer) A host creates a new proposal exclusively ([S6.2](#file-name)). It does not need the lock to do so.
- **S8.6** (Steward) To accept a proposal, a host takes these steps in order:
  1. With the lock held, it reads the proposal and checks that it is valid and `pending`.
  2. It applies the body to the target ([S6.8](#body)).
  3. It sets `status: accepted` and `decided-at` in the proposal.
  4. It releases the lock.
  5. It appends the decision entry, then the content entry ([S7.3](#7-journal)).

  To refuse, it sets `status: refused` and `decided-at` with the lock held, releases the lock, and appends the decision entry. If a host stops after step 2, a later attempt finds the body already at the end of the target and does not add it twice. It still appends both entries in step 5.
- **S8.7** (Steward) A host makes a change first and journals it second. If the journal write fails, the host tells the person that the change happened without a receipt.
- **S8.8** (Steward) Exclusive create, atomic rename, and append are properties of local file systems. Sync folders can make conflict copies, and a lock in a sync folder does not protect another device. A host ignores a conflict copy as an unknown name ([S2.1](#2-layout)), or in `proposals/` treats it as an invalid proposal ([S6.14](#status)). It SHOULD tell the person about it.

## 9. Protection at rest

- **S9.1** (Reader) The platform protects the store at rest: disk encryption and user-only permissions ([S2.5](#2-layout)). A host MUST NOT say the store is encrypted unless it is.

## What this version does not define

- changing or removing text through a proposal (only additions);
- detection of external edits (planned: a file hash in each journal line);
- scope labels inside files (use a separate `ME_HOME` for each scope, such as a work store and a personal store);
- synchronization between devices;
- encrypted ("sealed") files;
- signed decisions.

[me-lint](./tools/README.md) checks a store against this format. It checks files, not host behavior. The behavior tests are in [HOST.md](./HOST.md#black-box-conformance).
