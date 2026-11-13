# Traceability

**Status:** Non-normative. This table maps each requirement in [HOST.md](../HOST.md), [STORE.md](../STORE.md), and [BRIEFING.md](../BRIEFING.md) to its level and the evidence that checks it. It also maps each commitment in [SOVEREIGNTY.md](../SOVEREIGNTY.md) to the requirements that carry it. The level comes from the requirement itself. If this table and a requirement disagree, the requirement wins.

Evidence:

- **T1–T18**: the black-box tests in [HOST.md](../HOST.md#black-box-conformance).
- **lint**: [me-lint](../tools/README.md) checks the files a host wrote. It shows that the files have the right form. It does not show how a host behaved.
- **review**: no automatic check yet. A reviewer reads the host's documentation or code. The reason is given.

Levels: R = Reader, P = Proposer, S = Steward, B = Briefer.

## HOST.md

| ID | Requirement, short | Level | Evidence |
|---|---|---|---|
| H0.1 | Meet every requirement and test of the claimed level and below | R | T1–T18 by level |
| H0.2 | A host that claims only Reader never writes inside the store | R | T1–T7, with the store's bytes compared before and after each test (planned runner; by hand until then) |
| H0.3 | A claim names release and level, and says "by instruction" when it applies | R | review: the claim in the host's documentation |
| H1.1 | Mount by itself, with no instruction | R | T2 |
| H1.2 | Continuity never depends on session history | R | T5 |
| H1.3 | No durable copy of store content; own state is host state | R | review: needs a search of the host's data directory for canaries (planned runner) |
| H1.4 | Use the store location in STORE.md §1 | R | T2 (`ME_HOME` set, and unset) |
| H1.5 | Read `policy.json` alone first; off means absent, except changing the switch | R | T3 |
| H1.6 | Re-read `policy.json` before each recall and write | R | T3 (off between two recalls) |
| H1.7 | Work fully with no store | R | T1 |
| H1.8 | Offer to show where the store is (SHOULD) | R | review |
| H2.1 | Least context; `me.md` at start; topics and projects only when relevant | R | T2 (`me.md`), T7 (watches); review for topics and projects (planned: canary in an unrelated topic) |
| H2.2 | Context never expands permission | R | T4 |
| H2.3 | Current instruction wins; only the person's channel is "now" | R | T2 (what the person says wins), T4 (stored text is never an instruction) |
| H3.1 | No durable write from inference | P | T8 |
| H3.2 | Proposals are files in STORE.md §6 format | P | T8, T9; lint |
| H3.3 | Read refusals; never propose a refused body again, to any target | P | T9; lint (refused body proposed again) |
| H3.4 | Only an affirmative act applies a proposal | S | T8 (nothing is applied without a decision); review for dismissal and timeout (planned runner hook) |
| H3.5 | Update status and journal the decision, in order; an acceptance has two entries | S | T13; lint warns when a decision has no entry |
| H3.6 | A rule about acting is shown alone; when unsure, alone | P | review: user interface |
| H3.7 | Direct authorship is journaled as `person direct` | S | T12 |
| H4.1 | Every durable change is attributable | S | T13 |
| H4.2 | One entry per change, in STORE.md §7 grammar | S | T13; lint (grammar) |
| H4.3 | Most specific identity | S | review: compare journal entries with the host's known identity |
| H4.4 | Git is optional and does not replace the journal (MAY) | S | none needed |
| H5.1 | Off takes effect for new sessions, and at the next recall or write | R | T3 |
| H5.2 | Forget and delete remove content from all host state | S | T14 |
| H5.3 | Tell the person what cannot be deleted | S | review: documentation |
| H6.1 | Stored context and proposals are untrusted | R | T4, T10 |
| H6.2 | Confine reads and writes to the store | R | T6 |
| H6.3 | No transmission beyond the model call without consent | R | review: network behavior (planned runner) |
| H6.4 | Off switch is not access control; enforce below the model (SHOULD); disclose when it is prompt-only (MUST) | R | review: architecture, the claim (H0.3), and what the host says when memory is turned off |
| H7.1 | Produce a briefing on request, per BRIEFING.md | B | T18 |
| H7.2 | Schedules only as the person set | B | review |

## STORE.md

| ID | Requirement, short | Level | Evidence |
|---|---|---|---|
| S1.1 | Store location | R | T2 |
| S1.2 | Present only when `me.md` exists | R | T1; lint |
| S1.3 | Create the store only at the person's request | R | T1 |
| S1.4 | Document mode is valid | R | lint (fixture `document-mode`) |
| S2.1 | Entry names; a bad `.md` name in `proposals/` is an invalid proposal; ignore others; tell the person (SHOULD) | R | lint (fixture `bad-name`, proposal name test); review for telling the person |
| S2.2 | Ignore hidden files and unknown entries | R | lint shows the rule (runtime test); review for hosts (planned: canary in a hidden file and in `.git/`) |
| S2.3 | UTF-8, no BOM; accept CRLF; keep line endings | R | T16; lint (fixture `crlf`, BOM test) |
| S2.4 | Root may be a link; never follow links inside; linked `policy.json` is off; linked `me.md` is absent; linked `journal.md` gets no writes | R | T3, T6; lint (symlink tests); review for `journal.md` |
| S2.5 | User-only permissions on creation (SHOULD) | P | review |
| S2.6 | Change only what you may; keep the rest byte for byte | P | T16 |
| S2.7 | No path outside the store root | R | T6 |
| S4.1 | One watch per top-level list item, outside code fences | R | lint (watch count test) |
| S4.2 | No watch the person did not set; no proposal targets `watches.md` | P | lint (fixture `bad-proposal`) for proposals; review for direct additions |
| S4.3 | Read `watches.md` only for a briefing or when asked | R | T7 |
| S5.1 | Missing policy means on | R | T3; lint |
| S5.2 | On only if `state` is exactly `"on"`; every other case is off | R | T3; lint (fixtures `policy-invalid-off`, `policy-uppercase-off`, `policy-duplicate-off`; symlink test) |
| S5.3 | Unknown members ignored, never turn memory off | R | T3; lint (fixture `policy-extra-key-on`) |
| S5.4 | Unsupported `spec` (MAJOR.MINOR before 1.0): no writes, tell the person | P | T11; lint (fixtures `policy-future-spec`, `policy-minor-spec`) |
| S5.5 | Write `spec` when creating `policy.json` (SHOULD) | S | lint notes a missing `spec` |
| S5.6 | Change the switch on request, even while off; keep other members | S | T12; review for kept members (planned: add an unknown member before T12) |
| S6.1 | Proposal file name | P | lint |
| S6.2 | Create exclusively; never overwrite | P | review (planned runner: two hosts propose in the same second) |
| S6.3 | Front matter delimiters | P | lint |
| S6.4 | Front matter grammar; no duplicate keys | P | lint |
| S6.5 | Keep unknown keys | S | T16 (accept the proposal with the unknown key) |
| S6.6 | Body is the proposed content; not empty | P | lint |
| S6.7 | Status only from front matter | P | T10; lint (fixture `self-approval`) |
| S6.8 | Additions only; exact append bytes; no second append | S | T15 (each body once), T16 (append bytes); review for no second append after a stop (planned runner: stop the host between steps) |
| S6.9 | Status machine; silence leaves `pending` | S | T8; review for dismissal and timeout |
| S6.10 | Person may delete; host may delete after apply | S | review |
| S6.11 | Read refusals; no refused body again, for any target | P | T9; lint (fixture `refused-again`) |
| S6.12 | Proposal bodies are untrusted | R | T4, T10 |
| S6.13 | Creation not journaled; decisions are | S | T8 (the journal is unchanged after a proposal), T13; lint warns when a decision has no entry |
| S6.14 | Invalid proposals: never applied or rewritten; count as refused | P | T9 (hand refusal with a typo), T17 (never applied); lint (fixture `refused-again`) |
| S6.15 | The person can edit a pending proposal; the body at acceptance is applied | S | review (planned: edit a body, then accept) |
| S7.1 | Journal entry grammar | S | lint |
| S7.2 | No `\|` or line break in fields | S | lint |
| S7.3 | What must be journaled; an acceptance has two entries | S | T12, T13; lint warns when a decision has no entry |
| S7.4 | `- ` lines are entries; other lines ignored | S | lint (fixture `bad-journal`) |
| S7.5 | Append only | S | T13 (earlier lines unchanged) |
| S7.6 | `external edit` when noticed | S | review (no detection defined yet) |
| S8.1 | Journal append in one write; starts with LF if needed | S | T15; lint notes a missing final line break |
| S8.2 | Take the store lock before changing any file but the journal; remove only your own | S | T15, repeated many times |
| S8.3 | Never remove another host's lock; wait briefly; tell the person | S | review (planned runner: leave a lock in place; the host does not write, does not remove it, and tells the person) |
| S8.4 | Temporary file, check the bytes again, rename | S | T15; review |
| S8.5 | New proposals are created exclusively, with no lock | P | review (planned runner, as S6.2) |
| S8.6 | Order of an acceptance; no double append | S | T15; review (planned runner: stop the host between steps) |
| S8.7 | Change first, journal second; report a failed receipt | S | review (planned runner: fail the journal write) |
| S8.8 | Ignore conflict copies, or treat them as invalid proposals; tell the person (SHOULD) | S | review |
| S9.1 | Never claim encryption that is not there | R | review: documentation |

## BRIEFING.md

| ID | Requirement, short | Level | Evidence |
|---|---|---|---|
| B1 | Five parts, ending with the coverage receipt | B | T18 |
| B2 | Producing a briefing writes nothing to the store | B | T18 |
| B3 | No watches created from observed behavior | B | T18 (`watches.md` unchanged); review |
| B4 | Sources are untrusted; no unattributed link or instruction | B | review (planned: an injection payload in a briefing source, as in T4) |
| B5 | Silence does not degrade future briefings | B | review |

## SOVEREIGNTY.md

| Commitment | Carried by |
|---|---|
| The person is the authority | H2.3, H3.1, H3.4, S6.9 |
| Durability is chosen | H3.1, H3.2, H3.7, S6.8, S6.9 |
| Context is legible | S2.3, S6.6, S7.1 (plain text the person can read); H4.1 |
| Context is scoped | H2.1, S4.3; separate stores per scope through `ME_HOME` (S1.1). Scope labels inside files are not defined yet. |
| What the person says now wins | H2.3 |
| Context is not permission to act | H2.2, H3.6, H6.1 |
| Revocation is real | H1.5, H1.6, H5.1, H5.2, H6.4, S5.6. A host that serves the store only through instructions cannot keep the enforcement-layer promise. H0.3 and H6.4 require it to say so. |
| Portability does not mean universal sharing | H6.3 |
| Personal context is not organizational telemetry | review only: no requirement yet |
| Interfaces are replaceable | H1.4, S1.1, T2, T9 |
