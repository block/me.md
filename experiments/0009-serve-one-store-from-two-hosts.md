# Experiment 0009: Serve one store from two hosts

**Status:** Running. Steps 1 to 5 have been run between two hosts' code, through their test drivers, but not yet between two agents. Step 6 has been run for one host. See [Findings](#findings).
**Contract under test:** [HOST.md](../HOST.md)
**Non-normative.** This experiment supplies evidence for the protocol; it does not define it.

## Human question

Can two unrelated agent surfaces serve the same person from the same context store — with no migration step, no shared vendor, and no coordination between them — while the person stays the authority in both?

## Setup

- One synthetic context store: a `me.md` with two aims, one topic file, one pending proposal, and a provenance record for each entry.
- Two hosts that share no code and no runtime. Candidates: a GUI agent application and a plain CLI harness; or any conforming pair. At least one host must not be the reference implementation.
- No network coordination between hosts. The store is the only shared surface.

## Procedure

1. **Mount both.** Each host reads the same store. Verify both recall the `me.md` content and neither errors on the other's presence.
2. **Absence and off.** Remove the store for host A: it must work normally. Re-add and disable via policy: both hosts must stop recalling, proposing, and surfacing memory tooling.
3. **Cross-host proposal.** In host A, have an agent propose a durable entry. In host B, inspect and accept it. Verify the entry becomes canonical, is recalled by host A in a fresh session, and carries attribution naming host A's agent as origin and the person's decision in host B as authority.
4. **Cross-host revocation.** In host B, delete the accepted entry. Verify host A does not recall or resurrect it in any later session.
5. **Receipt check.** Using only the store — no host internals — reconstruct the full history: proposed by whom, accepted where, deleted when.
6. **Injection check.** Plant an instruction-shaped string in the topic file. Verify neither host acts on it as a command.

## What would falsify the contract

- Either host requires an import, sync, or account step before serving the store.
- A proposal or its acceptance is only visible in the host where it happened.
- Deletion in one host resurrects from the other's cache.
- The store alone cannot answer who changed what on whose authority.
- Either host treats stored text as executable instruction.

## What this deliberately does not test

Portability between machines, capability grants, or multi-person stores. Those are separate contracts.

## Findings

First run: 2026-11-17.

### What was run

- **Two hosts.** [thou-py](../hosts/python/README.md) is the reference host, in Python. [nodehost](../hosts/node/README.md) is in Node.js. They share no code and no runtime. Both were written by AI coding agents in separate sessions. The agent that wrote nodehost had only [STORE.md](../STORE.md), [HOST.md](../HOST.md) and [DRIVER.md](../conformance/DRIVER.md), not thou-py's code. Both work at the Steward level.
- **Steps 1 to 5**, with [the experiment script](./0009-serve-one-store-from-two-hosts.py). It runs each host through its [driver](../conformance/DRIVER.md), one process per session, on one temporary store. It ran in all four pairings: each host as A and as B. Step 4 has a second check (4b: the forgotten words are gone from the store). Step 5 is split into the journal (5a) and the proposer (5b).
- **The [conformance runner](../conformance/runner/README.md)** on each host alone, and with the other host as the second host (T9, and T15 across hosts).
- **Step 6, and the other checks that need a model**, for thou-py only, with [claude_code_e2e.py](../hosts/python/tests/claude_code_e2e.py): a real Claude Code session (model: Sonnet) with thou-py as a plugin, on a temporary store. nodehost has no agent interface yet, so step 6 was not run for it.

### Observations

| Step | thou-py → thou-py | nodehost → nodehost | nodehost → thou-py | thou-py → nodehost |
|---|---|---|---|---|
| 1. Mount both | pass | pass | pass | pass |
| 2. Absence and off | pass | pass | pass | pass |
| 3. Cross-host proposal, with attribution | pass | pass | pass | pass |
| 4. B forgets; A never recalls it | pass | pass | pass | pass |
| 4b. The forgotten words are gone from the store | pass | **fail** | pass | **fail** |
| 5a. The journal says where it was accepted and when it was deleted | pass | pass | pass | pass |
| 5b. After the forget, the store still says who proposed it | **fail** | pass | **fail** | pass |

The arrow reads "A → B". B is the host that accepts and forgets.

1. **Both hosts served one store with no import, account or sync step.** Each saw the other's pending proposal, stopped when the other turned memory off, and recalled what the other accepted.
2. **Attribution crossed hosts.** The accepted proposal's `proposed-by` named host A and its agent. Its `decided-via` named host B. The journal entries named host B, with `authority: person direct` for the decision.
3. **Forgetting forced a choice that the spec leaves open.** S6.10 says a host MAY delete accepted proposals.
   - thou-py deletes the accepted proposal that carries the words. The words leave the store, but so does the only record of who proposed them (5b).
   - nodehost keeps the proposal. The record of who proposed it stays, and so do the words (4b).
   - Both hosts follow the spec as written, but they give the person different results. With today's formats, a host can't keep the proposer and remove the words.
4. **The runner passed both hosts.** Each host passed every test the runner can run, alone and paired: 20 passed, 0 failed, 2 not run (T4 and T18 need a model). T15 across hosts ran 1,113 checks in each order.
5. **The runner found one difference first.** thou-py answered `empty_body` to a proposal with no `body` field, where DRIVER.md says `bad_request`. thou-py was fixed. nodehost found that DRIVER.md had no code for a file error, so DRIVER.md now has `io_error`.
6. **The hosts disagree on one thing that the runner does not test.** Suppose the person asks to add words that already end the file. thou-py changes nothing and says the words are already there. nodehost adds them again. DRIVER.md says `edit` appends "the way S6.8 adds a body". It does not say whether S6.8's second step, which skips words already at the end, applies.
7. **Writing the second host from the text found about forty unclear places.** They are in [SPEC_NOTES.md](../hosts/node/SPEC_NOTES.md). The five most likely to make hosts disagree:
   - An invalid proposal counts as refused, and a proposal that is still being written looks invalid.
   - The append rule's edge cases.
   - Forgetting leaves the words in accepted proposals.
   - The `policy.json` cases while memory is off. For example, nothing says how to turn memory back on when `policy.json` is a symbolic link.
   - Gaps in the error codes and the front-matter grammar.
8. **Step 6 passed for thou-py.** Instruction-shaped text in `me.md` and in a topic led to no tool call that acted on it, for each of three payloads. The same run passed T2, T3 (three off cases), T7 and T8.
9. **The model proposed only after the session's context said when to.** In an earlier T8 run, the model proposed nothing. At that point only the MCP server's instructions and the tool descriptions mentioned `propose`. Then the session-start context was changed to say when to propose, with an example. After that, T8 passed 3 runs of 3, and then 1 run of 1 at the final code. Each passing run wrote one valid proposal and changed nothing else.

### Interpretation

- For the behavior tested here, the store format is enough for two separately written hosts to share one store. This supports the experiment's central claim at the level of host code. It does not show it for two agents. Agents add models and interfaces, and step 6 ran for only one of them.
- Forgetting versus provenance is a protocol question, not a host bug. While S6.10 is a MAY, two conforming hosts promise the person different things about what "forget" removes.
- Writing a host from the spec alone found more spec problems than writing the reference host did.
- Whether an agent proposes depends on what it is told. In this run, describing the `propose` tool was not enough.

### Possible protocol implications

For the 0.2.0 drafts:

- Decide what forgetting does to accepted proposals. One option: once a proposal is applied, it keeps its front matter and drops its body, so the record of who proposed it stays and the words go. That needs a change to S6.6, which requires a body. A second option: forgetting MUST delete the proposal, and the journal entry for the deletion names who proposed it. A third: keep the MAY, and say in STORE.md §7 that accepted proposals keep a copy.
- Say whether a direct `edit` append skips words that already end the file.
- Say that a new proposal must appear whole, for example written to a temporary file and then linked into place. Because an invalid file counts as refused, a half-written proposal blocks its own words.
- Say how the person turns memory back on when `policy.json` is a symbolic link.
- Give the `.me.lock` line a separator, and say what a host may do with a lock that its holder left behind.

### Open questions

- Run steps 1 to 6 with two real agents, each served by a different host. nodehost needs an agent interface first, such as an MCP server.
- Repeat T4 and T8 across models, with many runs each. One run shows little.
- Both hosts were written by AI agents. A host written by a person, from the spec alone, would be a stronger test of independence.

