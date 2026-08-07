# Portability contract

**Status:** Working protocol hypothesis. Non-normative.

Portability should expand a person’s choices without expanding the audience for their context by default.

User-owned does not mean universally shareable. Local does not mean portable. Open format does not mean safe to export in full.

A portability contract should help a person understand what can move, what stays local, what is derived, what has already been projected elsewhere, and what must be excluded unless they deliberately choose otherwise.

## The human questions

A person should be able to answer:

- What state exists?
- Which parts are canonical context?
- Which parts are derived, historical, projected, or ephemeral?
- Which parts can be exported?
- Which parts are intentionally local-only?
- Will an export include sensitive scopes, third-party information, history, or dismissed proposals?
- Where has context already been copied or projected?
- What happens to updates, forgetting, and deletion after something moves?
- Can another implementation import the context without silently changing its meaning or scope?

## Portability is selective

A person may want to move:

- global working preferences;
- one topic;
- one project’s context;
- accepted context only;
- provenance metadata without historical text;
- an explicit agent projection;
- a complete archive for private backup.

These are different operations.

An implementation should not treat “export my context” as permission to include every topic, raw source artifact, cache, log, embedding, proposal, history snapshot, or credential it can find.

The person should be able to preview and select the intended subset.

## State classes

The exact labels remain under test. A useful portability inventory may distinguish:

### Portable private

User-governed state intended to move between trusted implementations.

Examples:

- accepted global context;
- selected topic context;
- selected project context;
- disclosed policy settings;
- stable entry identifiers where needed for continuity.

Portable private state remains private. “Portable” describes the person’s ability to move it, not permission to publish it.

### Local private

Private implementation state that may be useful locally but is not part of the portable source of truth.

Examples:

- run artifacts;
- local outcome events;
- debugging state;
- source-coverage snapshots;
- private indexes whose transfer would reveal more than the person expects.

An implementation should explain whether this state is rebuildable and whether it is included in deletion.

### Local only

State deliberately excluded from ordinary export.

Examples may include:

- sensitive inferred candidates;
- cryptographic keys;
- credentials;
- device-specific authorization records;
- local safety decisions;
- state whose license or third-party rights prohibit transfer.

Local-only status should be visible and justified. It should not become a convenient label for vendor lock-in.

### Derived and rebuildable

Indexes, embeddings, caches, rankings, summaries, and classifiers generated from canonical or external sources.

Derived state should normally be excluded from portable exports. A receiving implementation can rebuild its own representation from the person-governed source.

If derived state is exported, the person should know why, what it contains, and whether it can reveal forgotten or sensitive context.

### Projection

A non-canonical rendering or copy delivered to another agent, tool, or instruction surface.

A portability view should identify active projections and their destinations. Exporting the source does not automatically update or remove those copies.

### Historical

Superseded expressions, snapshots, provenance content, and migration backups.

History may support undo or accountability, but it can retain text the person no longer wants active. Ordinary export should exclude historical content unless the person deliberately requests an archive that includes it.

### Ephemeral

Session context, temporary routing state, transient source results, and short-lived action previews.

Ephemeral state should not become durable merely because an export process can access it.

### Excluded third-party or source data

Messages, documents, calendar records, code, and other material obtained from external sources may contain other people’s information or separate rights.

Access for a task does not automatically make source material part of the person’s portable context. Exports should contain references or person-authored summaries where appropriate rather than copying raw source data by default.

## A portability manifest

A future machine-readable manifest could inventory state without requiring one filesystem layout.

A useful manifest may describe:

- stable state identifier;
- human-readable name;
- state class;
- canonical or derived status;
- scope;
- sensitivity;
- origin;
- storage location or resolver;
- default export behavior;
- whether history is included;
- whether third-party data is present;
- active projections;
- encryption or protection expectations;
- version and migration information;
- deletion and synchronization behavior.

An illustrative entry might look like:

```json
{
  "id": "scope:global",
  "name": "Global agent preferences and boundaries",
  "class": "portable-private",
  "canonical": true,
  "scope": "global",
  "default_export": "selected",
  "contains_third_party_data": false,
  "history_included": false,
  "projections": ["tool:local-writing-agent"],
  "format_version": "draft-0"
}
```

This example is not a required schema.

## Export

Export creates a portable copy.

A trustworthy export flow should:

1. show the categories and scopes available;
2. state what is selected by default;
3. exclude credentials, secrets, raw connected-source data, and undisclosed derived state;
4. identify sensitive or third-party content;
5. distinguish current context from history;
6. show active projections that will not be affected by the export;
7. produce an inspectable package;
8. include format and compatibility information;
9. issue a receipt describing what was included and excluded.

An export should not silently activate context in the destination. Import and admission remain separate decisions.

## Import

Import brings context into another implementation.

A trustworthy import flow should preserve:

- the person-governed expression;
- scope;
- strength and conditions;
- origin and provenance references;
- stable identity where useful;
- exclusions and local-only boundaries;
- version information.

Before imported context becomes active, the person should be able to inspect:

- what will be added;
- which scopes and audiences will receive it;
- conflicts with existing context;
- unsupported fields or semantics;
- whether the destination will create projections or derived state;
- what will remain only in the import package.

An implementation must not silently broaden scope, strengthen a preference, flatten a project into personal context, or convert a proposal into accepted context during import.

## Conflict handling

Two implementations may contain different versions of the same entry.

Conflict handling should distinguish:

- same stable entry, different revision;
- semantically similar entries with different identities;
- narrower and broader scopes;
- current context and historical copies;
- accepted context and pending proposals;
- forgotten or deleted entries reappearing from an older export.

When safe reconciliation is unclear, the person should review the conflict rather than having the system guess.

A newer timestamp alone is not always enough. A stale export must not resurrect context that the person later forgot or deleted without a clear warning and decision.

## Synchronization is not export

Synchronization keeps state aligned over time.

It introduces additional questions:

- Which device or implementation is authoritative?
- How are concurrent edits merged?
- How quickly does revocation propagate?
- Can an offline copy recall disabled context?
- How are deletions and tombstones represented?
- What happens when one implementation cannot express another’s scope or policy?
- Which projections and derived caches are synchronized?

The protocol should not assume synchronization merely because an export format exists.

## Projection is not portability

Projection renders a subset of context for a particular agent or tool.

A projection may be useful without being portable canonical state. It should identify:

- the source subset;
- destination;
- generation time;
- whether it updates automatically;
- whether it can be removed;
- whether the destination may copy or retain it further.

A person who exports canonical context should not assume every projection moved, updated, or disappeared.

## Portability and deletion

Moving context creates more copies.

A portability contract should make deletion limits explicit:

- Can the source implementation remove only its own copy?
- Does a synchronized destination receive deletion?
- Are offline exports outside the source’s control?
- Do active projections require separate cleanup?
- Does provenance retain identifiers after content deletion?
- Can a stale import restore forgotten context?

The person should not be promised universal deletion where the implementation cannot enforce it. Receipts and manifests should identify destinations and copies that require separate action.

## Portability and sensitive context

Some context requires stronger care:

- health;
- finances;
- identity;
- politics or religion;
- relationships;
- accessibility;
- employment or performance;
- information about children or other third parties.

A default export should not include sensitive scopes merely because they are canonical. The person should make an informed, scope-specific choice.

Encryption can protect a package in transit or at rest, but it does not solve audience, scope, import, or deletion questions.

## Portability and inferred context

Agent-proposed or inferred context should not become portable merely because it is stored locally.

At minimum, an export should distinguish:

- accepted person-governed context;
- pending proposals;
- dismissed proposals or decision markers;
- derived pattern candidates;
- identity-bearing inferences;
- local-only safety or personalization state.

Pending and dismissed proposals should be excluded from ordinary portable context. Identity-bearing inferred state should remain local-only unless the person explicitly authors or admits a portable expression.

## Compatibility and evolution

Portable packages should declare a format or protocol version.

A receiving implementation should:

- preserve unknown fields where practical;
- report unsupported semantics;
- avoid treating missing fields as broader permission;
- never reinterpret an older entry as stronger, wider, or more portable;
- make migrations inspectable and reversible where practical;
- retain provenance for material migration changes.

Compatibility is not merely successful parsing. It is preservation of human meaning and sovereignty boundaries.

## Receipts

After export or import, the person should receive a clear account of:

- selected and excluded scopes;
- state classes included;
- history and provenance behavior;
- sensitive and third-party content warnings;
- destination or package location;
- format version;
- unsupported or transformed content;
- active projections not affected;
- deletion and synchronization limitations.

## What this document does not standardize

This document does not define:

- archive or package format;
- encryption mechanism;
- manifest schema;
- transport protocol;
- synchronization service;
- merge algorithm;
- stable identifier syntax;
- default sensitive-data taxonomy;
- import user interface;
- conformance requirements.

## Questions still under test

- Which state classes are understandable and sufficient?
- What should an ordinary export include by default?
- Should provenance metadata be portable separately from historical content?
- How should a receiving implementation preserve unsupported scope or policy?
- What prevents stale exports from resurrecting forgotten context?
- Which sensitive scopes require explicit per-export confirmation?
- How should projections and synchronized copies be represented?
- Which portability fields should eventually become normative?
