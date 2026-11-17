# nodehost

A second, independent host for the thou protocol. It is written in plain Node.js (ESM, Node 22 or newer, no dependencies, nothing to install). It was written from [STORE.md](../../STORE.md), [HOST.md](../../HOST.md) and [conformance/DRIVER.md](../../conformance/DRIVER.md) alone. [SPEC_NOTES.md](./SPEC_NOTES.md) lists every place where that text was unclear, and what this host chose.

- Name and version: `nodehost 0.1.0`
- Level: Steward (everything up to `policy`; no briefings)
- Off switch: enforced in code (`enforcement: "code"`), below any model

## Status

**It claims no conformance.** It passes its own tests, agrees with the example stores in `conformance/fixtures/`, and passes every test the [conformance runner](../../conformance/runner/README.md) can run, alone and paired with thou-py ([experiment 0009](../../experiments/0009-serve-one-store-from-two-hosts.md)). A claim needs more: the model-level tests (T2 last step, T4, the choice of what to recall, T18) run through an agent, and the review items in [TRACEABILITY.md](../../conformance/TRACEABILITY.md). It has no agent interface yet, only the driver. Briefer level (H7, T18) is not built.

## Layout

```text
hosts/node/
  thou-driver.mjs     the driver CLI (JSON Lines on stdin and stdout)
  lib/host.mjs        the host: every driver operation
  lib/policy.mjs      policy.json: the off cases, spec check, state rewrite
  lib/json.mjs        strict JSON parser that sees duplicate member names
  lib/proposal.mjs    proposal names, front matter, validity, rewriting
  lib/append.mjs      the S6.8 append rule, on bytes
  lib/journal.mjs     the journal grammar
  lib/fsx.mjs         no-follow reads, store lock, safe writes, journal append
  lib/text.mjs        normalization and line handling
  test/               node --test
```

## Run the driver

```sh
ME_HOME=/path/to/a/test/store node hosts/node/thou-driver.mjs
```

One process is one session. Send one JSON object per line. Each answer is one line.

```sh
printf '%s\n' '{"id":1,"op":"mount"}' '{"id":2,"op":"pending"}' \
  | ME_HOME=/tmp/test-store HOME=/tmp/test-home node hosts/node/thou-driver.mjs
```

Never point it at a real store while testing. `ME_HOME` unset means `$HOME/.me`.

`THOU_LOCK_WAIT_MS` (default 3000) sets how long a write waits for `.me.lock`. It exists for tests.

## Run the tests

From the repository root:

```sh
node --test hosts/node/test/
```

Every test uses a temporary directory for the store, and a second one for `HOME`. Nothing reads or writes `~/.me`. The suite takes about ten seconds. It includes the concurrency test: two driver processes accept proposals into one target, 40 rounds.

## What it does not do

- No briefings (Briefer level).
- It does not delete accepted proposals when you forget text (a MAY in DRIVER.md). It says so in a notice. See SPEC_NOTES.md.
- It does not detect external edits (S7.6).
- It does not clean up a stale `.me.lock`. It never removes a lock it did not create.
- Windows is untested. The code avoids POSIX-only calls where it can, but `O_NOFOLLOW` and hard links are used when present.
- A race remains between the symlink checks on directories and the file operations that follow. Files are opened without following a link. Directory components are checked, not pinned.
