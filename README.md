# me.md

**Keep up with agents, on your terms.**

`me.md` is an open protocol for working with agents. What agents know about you lives in plain files, in your words, on your machine. You own the files. Agents read them and propose additions. They may apply changes you explicitly request or approve — you decide what becomes memory. The files power the protocol's required main output, a [briefing](./BRIEFING.md): what moved, where the pull is, what is missing, and what to do next.

## Quickstart

Point any agent at this page and say: **"Set up my me.md."**

Agents: follow the [setup instruction](./SETUP.md#the-setup-instruction), then serve the store with the loop in [PROTOCOL.md](./PROTOCOL.md). SETUP.md is the only setup procedure; PROTOCOL.md defines the [store layout](./PROTOCOL.md#the-store).

Your file starts empty. The protocol supplies no template and no default persona. Sessions are views of the store, not containers of memory: discard any session, or all of them, and keep all durable context.

## The rules

- Memory is off until the person creates their file.
- The person owns the source of truth. Not an agent, application, provider, or employer.
- All stored content is readable. There is no hidden profile.
- Agent-inferred changes require a proposal. You accept, edit, or refuse each proposal, or ask for an edit directly. Refusal stays in effect. Silence is not acceptance.
- What the person says now overrides the store.
- Deleted means deleted.
- Context stays in its scope. Family data does not appear in an unrelated work session.
- Knowledge of preferences is never permission to act for the person.
- Any conforming host on the same computer serves the same files, with no migration and no lock-in. Syncing between devices is not defined yet.

It is not a transcript, not a hidden profile, not a productivity score, not employer telemetry, and not memory that one application owns. A small and true file is better than a large and speculative one.

## Documents

Every protocol document listed below starts with a status line. There are three kinds.

**Normative drafts.** HOST.md defines host conformance, SOVEREIGNTY.md states the commitments to the person, and BRIEFING.md defines a conforming briefing. These drafts may change.

- [HOST.md](./HOST.md) — full conformance rules for implementers, with black-box tests
- [BRIEFING.md](./BRIEFING.md) — the required main output: the person-shaped read
- [SOVEREIGNTY.md](./SOVEREIGNTY.md) — the commitments to the person

**Guides.** Setup and an overview of the rules.

- [PROTOCOL.md](./PROTOCOL.md) — the store, the loop, and a paste-in block for a harness
- [SETUP.md](./SETUP.md) — the setup instruction, ready to copy

**Non-normative.** Design notes, vocabulary, and open questions. They explain the rules. They do not add to them.

- [CONTEXT.md](./CONTEXT.md) — shared vocabulary
- [PROVENANCE.md](./PROVENANCE.md) and [REVOCATION.md](./REVOCATION.md) — the reasons behind HOST.md §4 and §5
- [EXPRESSION.md](./EXPRESSION.md) — how context is put into words and admitted
- [SYSTEM.md](./SYSTEM.md) — the conceptual system map
- [EXTENSIONS.md](./EXTENSIONS.md) — the open-source boundary and candidate extensions
- [EXPERIMENTS.md](./EXPERIMENTS.md) — how the protocol is tested

## Status

`me.md` is an experimental protocol draft, not a stable standard yet. Releases are tagged `vX.Y.Z`, and a host that claims conformance names the release it follows. Changes are in [CHANGELOG.md](./CHANGELOG.md). The most important question for any contribution is whether the system increases the person's agency. Governance is in [GOVERNANCE.md](./GOVERNANCE.md). The license is [Apache 2.0](./LICENSE).
