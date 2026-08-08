# Experiment 0009 — Serve one store from two hosts

**Status:** Proposed
**Contract under test:** [HOST.md](../HOST.md)
**Non-normative.** This experiment supplies evidence for the protocol; it does not define it.

## Human question

Can two unrelated agent surfaces serve the same person from the same context store — with no migration step, no shared vendor, and no coordination between them — while the person stays the authority in both?

## Setup

- One synthetic context store: a spine with two operating rules, one topic file, one pending proposal, and a provenance record for each entry.
- Two hosts that share no code and no runtime. Candidates: a GUI agent application and a plain CLI harness; or any conforming pair. At least one host must not be the reference implementation.
- No network coordination between hosts. The store is the only shared surface.

## Procedure

1. **Mount both.** Each host reads the same store. Verify both recall the spine rules and neither errors on the other's presence.
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
