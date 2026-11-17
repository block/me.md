# Conformance driver

**Status:** Draft, for v0.2.0. This page is a test interface, not part of the protocol. A host does not need a driver to conform. [HOST.md](../HOST.md) and [STORE.md](../STORE.md) define conformance. This page defines how the [conformance runner](./runner/README.md) talks to a host, so that one runner can test any host.

A *driver* is a small program that a host ships for testing. It runs the host's own code, the same code that serves a person, and exposes it as a few operations. The runner starts the driver, sends it requests, and then checks two things: what the driver answered, and what is in the store.

The driver stands in for two parties:

- The **agent** asks to mount, recall, list, and propose.
- The **person** decides, edits, forgets, and turns memory on or off. A person operation in a request means the person made an affirmative act ([H3.4](../HOST.md#3-writing)). The driver does not ask again.

A driver shows what the host's code does with the store. It cannot show what a model does with what it recalls. Tests that need a model, such as injection (T4), are run through an agent instead. See [What a driver cannot show](#what-a-driver-cannot-show).

## Running a driver

- The runner starts the driver as a command, for example `python3 hosts/python/thou_driver.py`.
- The runner sets the environment. It sets `HOME`, `TMPDIR`, `XDG_CONFIG_HOME`, `XDG_DATA_HOME`, `XDG_STATE_HOME` and `XDG_CACHE_HOME` to test directories. It sets `ME_HOME` to a test store, or unsets it so that the store is `$HOME/.me` ([S1.1](../STORE.md#1-location-and-presence)). A host keeps its own state only under these directories, so the runner can search them for copies of store content ([H1.3](../HOST.md#1-mounting)).
- One process is one session. A host MAY keep state in memory during the session, as it would in real use.
- The runner writes one request per line on standard input, as a JSON object. The driver writes one response per line on standard output, in the same order, and flushes after each one. It writes nothing else on standard output. It MAY write anything on standard error.
- At the end of input, the driver exits with status 0.
- The first request in each session is `mount`.
- The runner MAY run two drivers at once on one store, for example for test 15.

## Requests and responses

A request is a JSON object with `id` and `op`, and the fields of that operation:

```json
{"id": 3, "op": "propose", "target": "topics/travel.md", "body": "Prefer aisle seats.", "basis": "You asked for aisle seats twice."}
```

`id` is any JSON value. The response carries it back unchanged.

A response always has `id` and `ok`. When `ok` is `true`, the response has the fields of that operation. When `ok` is `false`, it has `error`, one of the codes below, and `message`, a sentence for the person:

```json
{"id": 3, "ok": false, "error": "memory_off", "message": "Memory is off: policy.json does not say \"on\"."}
```

Any response MAY have `notices`: a list of sentences the host would show the person. Examples: why memory is off, why the host will not write, that it ignored `Travel.md` because of its name, or that `.me.lock` is held. The runner checks that some tests produce a notice. It never checks the wording.

Every operation that reads the store answers with `memory`:

| `memory` | Meaning |
|---|---|
| `"absent"` | The store has no `me.md`, or `me.md` is a symbolic link ([S1.2](../STORE.md#1-location-and-presence)). |
| `"off"` | `policy.json` turns memory off ([S5.2](../STORE.md#5-policyjson)). The host decides this before it opens any other file ([H1.5](../HOST.md#1-mounting)), so it answers `"off"` even when `me.md` is missing. |
| `"on"` | Memory is on and `me.md` exists. |

When `memory` is `"on"` and `policy.json` names a `spec` the host does not support ([S5.4](../STORE.md#5-policyjson)), the response also has `"writable": false`. Otherwise `writable` is `true` or left out.

Text fields carry a file's contents decoded as UTF-8, with its line breaks as they are, CRLF included.

## Operations

Each operation has the lowest [level](../HOST.md#conformance-levels) a host needs to support it. A host answers an operation above its level with `unsupported_op`.

### `host` (Reader)

Who the host is and what it claims. It does not touch the store.

```json
{"id": 1, "ok": true, "name": "examplehost", "version": "1.0", "spec": "0.1", "level": "steward", "enforcement": "code"}
```

- `level` is `"reader"`, `"proposer"`, `"steward"` or `"briefer"`. The runner runs the tests for that level and the levels before it.
- `enforcement` is `"code"` when the host's own code enforces the off switch, and `"instruction"` when only instructions to a model do ([H6.4](../HOST.md#6-security-posture)).

### `mount` (Reader)

Starts the session: find the store, decide on or off, and read `me.md` ([H1.1](../HOST.md#1-mounting), [H1.5](../HOST.md#1-mounting)).

Answer: `memory`, `store` (the absolute path of the store), and `files`. When `memory` is `"on"`, `files` has one item, `{"path": "me.md", "text": "…"}`. Otherwise `files` is empty.

### `list` (Reader)

The names the agent could recall. It reads directory names only, never file contents.

Answer: `memory`, `topics` and `projects` (lists of file names such as `"travel.md"`), and `watches` (`true` if `watches.md` exists). All three are empty or `false` unless `memory` is `"on"`. Names that break [S2.1](../STORE.md#2-layout), hidden files, and symbolic links are left out. A host SHOULD add a notice for a name it ignores.

### `recall` (Reader)

Reads files the task makes relevant. The host re-reads `policy.json` first ([H1.6](../HOST.md#1-mounting)).

Request: `paths`, a list of store-relative paths, and `purpose`, one of `"task"` (the default), `"briefing"` or `"watches"`.

Answer: `memory`, `files` (a list of `{"path", "text"}`), and `skipped` (a list of `{"path", "reason"}`). Every requested path appears in exactly one of the two lists. When `memory` is not `"on"`, every path is skipped.

A host recalls only `me.md`, `topics/<name>.md`, `projects/<name>.md`, and `watches.md`. It recalls `watches.md` only when `purpose` is `"briefing"` or `"watches"` ([S4.3](../STORE.md#4-watchesmd)). It skips any other path, including a path with `..`, an absolute path, a hidden file, a symbolic link, a missing file, and a file that is not valid UTF-8 ([S2.2–S2.7](../STORE.md#2-layout)).

### `pending` (Proposer)

The proposals waiting for a decision.

Answer: `memory`, `proposals`, and `invalid`.

- `proposals` lists each valid proposal whose `status` is `pending`: `{"id", "file", "target", "proposed-by", "proposed-at", "basis", "body"}`. The status comes only from the front matter ([S6.7](../STORE.md#body)).
- `invalid` lists each invalid file in `proposals/` ([S6.14](../STORE.md#status)): `{"file", "reason"}`.

### `propose` (Proposer)

The agent suggests a change ([H3.1–H3.3](../HOST.md#3-writing)).

Request: `target`, `body`, `basis`, and optionally `agent`, the agent's name for the `proposed-by` field.

Answer: `memory`, `proposal` (the new proposal's id), and `file`, the store-relative path of the new proposal. The field is `proposal`, not `id`, because `id` is the request's.

Errors: `absent`, `memory_off`, `unsupported_spec`, `refused` (the normalized body equals a refused or invalid proposal's body, [S6.11](../STORE.md#status)), `bad_target`, `empty_body`.

### `decide` (Steward)

The person accepts or refuses a pending proposal ([S8.6](../STORE.md#8-writing-safely)).

Request: `proposal` (the id), `decision` (`"accept"` or `"refuse"`), and optionally `agent`.

Answer: `memory`, `status` (`"accepted"` or `"refused"`), `applied` (`"added"`, `"already"` when the body was already at the end of the target, or `null` for a refusal), and `journal`, the lines the host appended to `journal.md`, without their final line break.

Errors: `absent`, `memory_off`, `unsupported_spec`, `not_found`, `invalid_proposal`, `not_pending`, `bad_target` (the target is a symbolic link or not a regular file, so the host will not write it), `locked`.

### `revise` (Steward)

The person changes the body of a pending proposal before deciding ([S6.15](../STORE.md#status)).

Request: `proposal`, `body`.

Answer: `memory`. Creating or revising a proposal is not journaled ([S6.13](../STORE.md#status)).

Errors: `absent`, `memory_off`, `unsupported_spec`, `not_found`, `invalid_proposal`, `not_pending`, `empty_body`, `locked`.

### `edit` (Steward)

The person asks for a change in their own words: direct authorship ([H3.7](../HOST.md#3-writing)).

Request: `path` (`me.md`, `watches.md`, or a topic or project file), `action`, and optionally `agent`.

- `"action": "append"` with `text`. The host adds the text at the end of the file the way [S6.8](../STORE.md#body) adds a proposal body, and creates the file if it is missing (but never `me.md`, [S1.3](../STORE.md#1-location-and-presence)).
- `"action": "replace"` with `old` and `new`. The host writes the line breaks in `old` and `new` the way the file uses them, then replaces the one place where `old` occurs. Every other byte stays the same ([S2.6](../STORE.md#2-layout)).

Answer: `memory` and `journal`.

Errors: `absent`, `memory_off`, `unsupported_spec`, `bad_path`, `not_found` (the file is missing, for `replace`), `no_match`, `ambiguous` (`old` occurs more than once), `locked`.

### `forget` (Steward)

The person deletes something ([H5.2](../HOST.md#5-revocation)).

Request: `path`, and optionally `text` and `agent`. With `text`, the host removes each place where `text` fills whole lines, with their line breaks. Without `text`, it deletes the file.

Answer: `memory`, `removed` (how many places, or 1 for a file), and `journal`. The host MUST add a notice that names what it cannot delete, such as copies the model provider kept ([H5.3](../HOST.md#5-revocation)). It MAY also delete accepted proposals that carry the same text ([S6.10](../STORE.md#status)), and journal each one.

Errors: `absent`, `memory_off`, `unsupported_spec`, `bad_path`, `not_found`, `no_match`, `locked`.

### `policy` (Steward)

The person turns memory on or off ([S5.6](../STORE.md#5-policyjson)). This works while memory is off.

Request: `state` (`"on"` or `"off"`), and optionally `agent`.

Answer: `memory` (after the change) and `journal`.

Errors: `absent` (the host does not create a store, [S1.3](../STORE.md#1-location-and-presence)), `unsupported_spec` (only for `"on"`: a host that does not support the store's `spec` may only turn memory off, [S5.4](../STORE.md#5-policyjson)), `locked`.

## Error codes

| Code | Meaning |
|---|---|
| `absent` | No store. The host wrote nothing. |
| `memory_off` | Memory is off. The host wrote nothing. |
| `unsupported_spec` | `policy.json` names a `spec` the host does not support. The host wrote nothing. |
| `refused` | The person refused this body before. |
| `bad_target` | The target is not `me.md`, `topics/<name>.md` or `projects/<name>.md`, or, for `decide`, it is a symbolic link or not a regular file. |
| `bad_path` | The path is not one this operation may change. |
| `empty_body` | The body is empty after normalization. |
| `not_found` | No such proposal or file. |
| `invalid_proposal` | The proposal file breaks S6.1–S6.6. The host did not apply or rewrite it. |
| `not_pending` | The proposal was already decided. |
| `no_match` | The text to replace or forget is not in the file. |
| `ambiguous` | The text to replace occurs more than once. |
| `locked` | Another host holds `.me.lock`. The host made no change, left the lock in place, and added a notice that names `.me.lock`. |
| `unsupported_op` | The host does not support this operation at its level. |
| `bad_request` | The request is not a JSON object, or a field is missing or has the wrong type. |

When a change succeeds but the journal write fails, the answer is `ok: true` with a notice that the change has no receipt ([S8.7](../STORE.md#8-writing-safely)).

## What a driver cannot show

A driver runs the host's code without a model. These parts of the tests need an agent with a model in front of the host:

- **T2**, the last step: what the person says now wins over `me.md`.
- **T4**: instruction-shaped text in the store never makes the agent call a tool.
- Choosing what to recall: the agent reads a topic only when the task makes it relevant (H2.1), and states a preference by implication only as a proposal (T8).
- **T18**: briefings.

The runner reports these as not run. A host that claims a level still has to pass them. The runner's [README](./runner/README.md) describes the agent adapter for running them.
