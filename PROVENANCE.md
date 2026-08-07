# Provenance contract

**Status:** Working protocol hypothesis. Non-normative.

Provenance explains how durable context came to exist and why a change was allowed.

It is not the same as version history, a debugging log, or surveillance. A person should not need to understand Git, database internals, or model traces to answer a few basic questions about their context:

- What changed?
- Who or what changed it?
- Why was the change allowed?
- When did it happen?
- What source, proposal, or instruction did it come from?
- Is the change still active?

The protocol should preserve those answers without requiring one storage technology.

## Provenance belongs to the mutation boundary

Every path that can change canonical context should produce an honest account of the change.

Common mutation paths include:

- the person authors or edits context directly;
- the person explicitly asks an agent to record something;
- the person accepts or revises an agent proposal;
- the person imports context from another source;
- an implementation migrates a format;
- another trusted interface edits the source of truth;
- the person forgets or deletes context;
- a projection or export is created, updated, or removed.

Recording provenance after a generic filesystem write is weaker than enforcing the mutation through a context-aware operation. An implementation should prefer a mutation boundary that knows the actor, authorization, target, and intended operation before applying the change.

## Human questions before machine fields

A provenance implementation should first support human understanding.

### What changed?

The person should be able to identify the affected entry, scope, projection, policy, or other state.

A change may be described as:

- created;
- edited;
- moved to another scope;
- accepted from a proposal;
- imported;
- forgotten;
- deleted;
- projected;
- restored;
- migrated.

The vocabulary may evolve, but it should not collapse materially different events into a generic “updated.”

### Who or what changed it?

The actor should be represented honestly.

Useful actor categories include:

- the person;
- a named agent;
- a named interface or application;
- an importer;
- a migration process;
- an unknown or external editor.

An implementation should not attribute a change to the person merely because it cannot identify the actual actor.

### Why was it allowed?

The provenance record should state the authorization basis, not merely that a write succeeded.

Examples include:

- direct authorship;
- explicit request in the current interaction;
- proposal accepted as written;
- proposal accepted after revision;
- import reviewed and confirmed;
- format migration under a disclosed compatibility rule;
- external edit detected in the user-owned source.

A prompt instruction such as “only edit with permission” is not itself a durable authorization record.

### When did it happen?

The person should be able to place a change in time and distinguish the change from later observation or synchronization.

Timestamps should be machine-readable and should not imply greater precision than the implementation actually has.

### What did it come from?

Where applicable, the record should reference the source that explains the change:

- a proposal identifier;
- a session or interaction identifier;
- an import source;
- a previous context-entry identifier;
- a migration version;
- a projection destination.

References should avoid duplicating raw sensitive content when an identifier, hash, or bounded summary is enough.

## Canonical content and provenance are different

The canonical expression is the current person-governed statement.

Provenance explains how it changed. It must not become a competing active profile.

A superseded expression may be retained for undo or history, but the implementation must disclose:

- whether old content remains;
- where it remains;
- how long it is retained;
- whether agents can recall it;
- whether it is exported or synchronized;
- how the person can purge it.

Old content retained for history must not continue influencing agents after it is superseded, forgotten, or deleted.

## Provenance without data duplication

A provenance system should minimize copies of personal context.

Often the useful record is:

- stable event identifier;
- timestamp;
- actor;
- operation;
- target identifier and scope;
- authorization basis;
- source reference;
- before and after integrity references;
- result status.

The record does not always need the full before-and-after text.

An illustrative event might look like:

```json
{
  "id": "evt_01J...",
  "at": "2026-08-07T18:00:00Z",
  "actor": {
    "type": "agent",
    "id": "writing-helper"
  },
  "operation": "edit",
  "target": {
    "type": "context-entry",
    "id": "ctx_01J...",
    "scope": "global"
  },
  "authorization": {
    "basis": "proposal-approved-after-revision",
    "proposal_id": "prop_01J..."
  },
  "before": "sha256:...",
  "after": "sha256:...",
  "result": "applied"
}
```

This example is not a required schema. It illustrates the questions a future machine-readable contract may need to answer.

## Stable identity matters

Timestamps and text are not reliable identifiers.

Two sessions may propose the same sentence at the same time. A person may edit a proposal before accepting it. A later correction may reuse similar wording.

Entries, proposals, decisions, events, and projections should have stable identities where an implementation needs to distinguish them.

Approval should bind to the exact candidate expression, scope, audience, and relevant conditions the person reviewed—not merely to matching text.

## Results and failures

Provenance should distinguish:

- applied;
- rejected;
- failed;
- partially applied;
- superseded;
- reversed.

A failed history write must not be represented as successful provenance. Likewise, a successful context mutation with a failed provenance record creates an accountability gap that should be surfaced rather than silently ignored forever.

Implementations may choose fail-closed or fail-open behavior for different operations, but they should document the choice. High-risk agent-mediated writes should generally prefer stronger guarantees than low-risk local user edits.

## Concurrent and external edits

User-owned context may be edited by more than one trusted interface.

A provenance implementation should account for:

- concurrent edits;
- stale writes;
- conflicting revisions;
- edits made outside the primary application;
- synchronization arriving later than the original change.

When attribution is unknown, say so. “Edited outside this application” is more honest than inventing an actor.

A detected external edit should not automatically be treated as agent-authorized or user-authored. It is an observed mutation with an unknown or externally supplied origin until more is known.

## Forgetting, deletion, and provenance

Provenance creates a tension: accountability can preserve information the person asked to remove.

The implementation must distinguish at least:

- **active context** — available for recall;
- **provenance metadata** — evidence that an operation occurred;
- **historical content** — old expressions or snapshots;
- **derived state** — indexes, caches, summaries, and projections.

Forgetting active context may retain a minimal event showing that an entry was forgotten, without retaining the forgotten expression itself.

Deletion should state whether provenance metadata remains and whether that metadata can identify or reconstruct the deleted content. “Delete all” must address historical content, derived state, projections, and synchronized copies—not just the current canonical file.

The person should have a way to purge historical content and, where the implementation permits, provenance metadata. Legal or security retention requirements must be disclosed rather than hidden behind the protocol.

## Provenance is not telemetry

A provenance record exists to support the person’s control and the integrity of their context.

It should not quietly become:

- employee monitoring;
- productivity analytics;
- behavioral scoring;
- engagement measurement;
- a relationship graph;
- a training dataset;
- a record of every conversation turn.

Access to provenance should be no broader than necessary. Exporting or sharing it is a separate choice.

## Integrity and tamper evidence

Implementations may use append-only logs, hashes, signatures, database constraints, Git objects, or other mechanisms to detect accidental or malicious alteration.

The protocol does not yet require a particular mechanism.

A stronger integrity mechanism is useful only if it remains understandable and does not prevent the person from deleting their own context. Tamper evidence should protect the person’s authority, not override it.

## Minimum application behavior

A trustworthy interface should let the person:

- inspect the current expression;
- see its origin and last meaningful change;
- distinguish person-authored, agent-proposed, imported, migrated, and unknown changes;
- understand why an agent-mediated change was allowed;
- see whether a proposal was revised before admission;
- undo or correct a change where supported;
- understand what history remains after forgetting or deletion;
- purge retained historical content when promised.

The interface does not need to expose implementation internals by default. It should reveal enough to answer the human questions without requiring forensic work.

## What this document does not standardize

This document does not define:

- Git, JSONL, SQLite, or another storage mechanism;
- a required event schema;
- cryptographic signatures or hash algorithms;
- history retention periods;
- undo behavior;
- synchronization conflict resolution;
- whether every direct user edit must block on provenance persistence;
- user-interface layout;
- conformance requirements.

These choices should be informed by experiments, security review, and multiple implementations.

## Questions still under test

- What is the smallest provenance record that still supports meaningful accountability?
- When is a content hash sufficient, and when does useful undo require retaining old text?
- Should high-risk agent writes fail closed if provenance cannot be recorded?
- How should direct file edits and concurrent interfaces be reconciled?
- What provenance should survive forgetting or deletion?
- How long should proposal and dismissal records remain?
- Which provenance fields should eventually become portable?
- How much provenance should an ordinary person see before it becomes noise?
