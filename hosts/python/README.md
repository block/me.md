# thou-py: a reference host

**Status:** Experimental, like the protocol. thou-py makes no conformance claim yet. [What it has passed](#what-it-has-passed) says exactly which tests it has run.

thou-py serves a person's store under the thou protocol: the v0.1 store format ([STORE.md](../../STORE.md)) at the Steward level ([HOST.md](../../HOST.md#conformance-levels)). It enforces the rules in its own code, not through instructions to a model. It is one folder of Python 3.9 or newer, with only the standard library.

It is a reference: code you can read next to the spec to see one way to meet it. Where this code and the spec differ, the spec wins.

## Three ways to run it

All three run the same code in `thou_host/`.

### In Claude Code, as a plugin

This folder is a Claude Code plugin. To try it for one session:

```
claude --plugin-dir hosts/python
```

The plugin has three parts:

- **A session-start hook** (`thou_hooks.py session-start`). At the start of every session, it reads `policy.json` alone, then `me.md`, and adds `me.md` to the session as context. It says nothing when memory is off or there is no store. You don't have to ask (H1.1).
- **An MCP server** (`thou_mcp.py`), named `thou`. Its tools are `mount`, `where`, `list`, `recall`, `pending`, `propose`, `decide`, `revise`, `edit`, `forget` and `policy`. The server reads `policy.json` before every call. While memory is off, it offers only `where` and `policy` (H1.5).
- **A pre-tool hook** (`thou_hooks.py pre-tool-use`). It stops Claude Code's own file tools, and shell commands that name the store, from reaching the store. The model can then reach the store only through the thou tools, which keep the rules (H6.4).

Claude Code asks before it runs an MCP tool you haven't allowed. Allow the tools that only read or propose: `mount`, `where`, `list`, `recall`, `pending` and `propose`. Leave `decide`, `revise`, `edit`, `forget` and `policy` to ask every time. Your yes to that prompt is the affirmative act that HOST.md H3.4 requires. The prompt shows the tool's arguments, and for `decide` that is only the proposal's id. So read the proposal first: ask the agent to show it, or look at the file in `proposals/`. In Claude Code these tools are named `mcp__plugin_thou_thou__<tool>`.

### In any agent that speaks MCP

Run `python3 hosts/python/thou_mcp.py` as a stdio MCP server. For example, in goose, add a command-line extension with that command. The server's instructions tell the agent to call `mount` at the start of a session. When memory is off or there is no store, the server gives no instructions. That is mounting by instruction: the agent mounts only if the model follows the instruction. In Claude Code, the session-start hook mounts in code instead.

Set your client to ask before `decide`, `revise`, `edit`, `forget` and `policy`, if it can.

### As a conformance driver

`python3 hosts/python/thou_driver.py` speaks the [driver interface](../../conformance/DRIVER.md), so the [conformance runner](../../conformance/runner/README.md) can test it.

The store is `$ME_HOME` if it is set, and `~/.me` otherwise. To try thou-py without touching your own store, set `ME_HOME` to a test folder.

## What it enforces in code

- **The off switch.** It reads `policy.json` alone before it opens any other file, and again before every recall and write (H1.5, H1.6). Every off case in S5.2 counts: a missing `state`, `"ON"`, invalid JSON, a repeated member at any depth, a symbolic link.
- **The store's edges.** It touches only the paths in STORE.md §2, checked by pattern (S2.7). It checks every part of a path for a symbolic link, and opens files without following one (S2.4). See [Limits](#limits) for the gap that remains. It ignores hidden files and other names, and says so (S2.1, S2.2).
- **Least context for watches.** It reads `watches.md` only for a briefing or when you ask about your watches (S4.3).
- **Proposals.** It writes proposals in the S6 format, creates each file exclusively, and refuses to propose words you refused, for any target, after normalizing them. An invalid proposal counts as refused (S6.11, S6.14).
- **Decisions.** It accepts in the S8.6 order: lock, check, apply, set status, unlock, journal. It never applies or rewrites an invalid proposal. It keeps unknown front-matter lines byte for byte.
- **Writes.** It takes the store lock, never removes a lock it didn't create, and writes through a temp file that it compares before it renames (S8.2–S8.4). It keeps each file's line endings and every byte it didn't change (S2.3, S2.6, S6.8).
- **The journal.** It appends one entry per change, in one write each, and never rewrites the journal (S7, S8.1). It records `thou-py 0.1.0`, plus the agent's name when it knows it, for example `thou-py 0.1.0 (claude-code)` (H4.3).
- **Versions.** If `policy.json` names a `spec` other than `"0.1"`, it writes nothing except to turn memory off, and says why (S5.4).
- **Forgetting.** It removes the words and clears its session cache. It deletes an accepted proposal when the proposal's whole body is the words you forgot, or when you forget its whole target file. Other proposals that still hold the words are named in a notice. It tells you what it can't delete (H5.2, H5.3).

## What the model still decides

thou-py can't make these happen in code. They rest on the model, guided by the tool descriptions and the session-start context:

- recalling a topic or project only when the task makes it relevant (H2.1);
- noticing something worth proposing, and proposing it (T8);
- calling `decide`, `edit`, `forget` or `policy` only when you asked. thou-py journals these as your direct act (`authority: person direct`), but its code can't tell whether you asked or the model decided to call. Your client's permission prompt is the check;
- treating what it reads as information, not instructions (H6.1). thou-py marks recalled text as data, and the pre-tool hook keeps the store's files out of the file tools, but the model reads the text.

## Limits

- **Bypass permissions.** If Claude Code runs with permission prompts off, nothing asks you before `decide`, `edit`, `forget` or `policy`. H3.4 then rests on the model.
- **The pre-tool hook is a fence, not a wall.** It catches file tools that point into the store, and shell commands that name the store's path, `~/.me` or `$ME_HOME`. When the session works inside the store, it stops every file tool and shell command. A shell command that builds the path some other way gets through. If the hook itself fails, it stops the call.
- **A symbolic link swapped in mid-call.** thou-py checks each folder in a path, then opens the file without following a link. A program that replaces `topics/` with a link between the check and the open could redirect one read or write. Closing that gap needs `openat`-style calls on each folder. The Node host has the same gap.
- **Saved sessions.** Claude Code saves session transcripts, and they include what was recalled. Forgetting a line doesn't change old transcripts. The forget notice says so.
- **Showing proposals.** `pending` returns every pending proposal. Showing each one to you, alone when it tells agents how to act (H3.6), is up to the agent's interface.
- **Platforms.** Tested on macOS and Linux. Windows is not supported yet: the code uses `O_NOFOLLOW` and `pread`.
- **Sync folders.** The lock and the rename protect one machine's file system, not a folder synced between devices (S8.8).
- **Briefings.** thou-py does not produce briefings, so it does not aim at the Briefer level.

## What it has passed

- **Unit tests:** `python3 -m unittest discover -s hosts/python/tests -p 'test_*.py'`. They use temporary stores only.
- **Model-level checks with Claude Code:** `python3 hosts/python/tests/claude_code_e2e.py`. This file is opt-in. It calls a model, so CI doesn't run it. It runs a real Claude Code session with this plugin on a temporary store, for the parts of tests T2, T3, T4, T7 and T8 that need a model. The results are in [experiment 0009](../../experiments/0009-serve-one-store-from-two-hosts.md).
- **The conformance runner:** see [experiment 0009](../../experiments/0009-serve-one-store-from-two-hosts.md).

Passing these does not make a conformance claim. A claim needs every test for the level, including the review items in [TRACEABILITY.md](../../conformance/TRACEABILITY.md).
