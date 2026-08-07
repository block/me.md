# Revocation and deletion contract

**Status:** Working protocol hypothesis. Non-normative.

A person’s control is not complete if context can be added but cannot be reliably stopped, forgotten, or removed.

Revocation is a family of operations. “Off,” “forget,” “delete,” and “purge” should not be treated as interchangeable labels for hiding something in the interface.

A trustworthy implementation should state what each operation affects, when it takes effect, which copies remain, and what is outside its control.

## The human questions

A person should be able to answer:

- What will stop being used immediately?
- What content will remain stored?
- Which agents, sessions, interfaces, or destinations lose access?
- Will proposals and background processes also stop?
- What history, provenance, indexes, caches, projections, exports, and backups remain?
- Can any retained state reconstruct or restore the removed context?
- How long will delayed deletion take?
- Which copies are outside this implementation’s control?
- How can the person verify the result?

## Revocation operations

### Revoke audience or capability

Remove an agent, interface, process, or destination’s authority to access or act on context.

Examples:

- remove one agent’s access to topic context;
- revoke an application’s permission to propose memories;
- disconnect an external source;
- invalidate an action capability;
- stop a projection from updating.

Revocation should affect the enforcement layer, including active sessions where practical. Changing a prompt while leaving a working tool or credential is not meaningful revocation.

### Disable

Stop use of a store, scope, capability, projection, or feature while retaining its underlying state.

Disablement is appropriate when the person wants a reversible pause.

A disabled context store should normally mean:

- recall fails;
- topic enumeration or routing fails where it would expose disabled state;
- proposals fail or remain unavailable;
- new projections are not generated;
- background reflection and monitoring that depend on the store stop;
- active sessions cannot continue using a retained access handle;
- stored canonical content remains untouched;
- the interface clearly says that disablement is not deletion.

Whether already-injected context can be withdrawn from a model’s current token window is an implementation limitation that must be explained honestly. The runtime should still block future access and actions.

### Forget

Remove one accepted context entry or scope from active durable context and future recall.

Forgetting should:

- remove the canonical active expression;
- prevent derived indexes or caches from restoring it;
- update or remove linked projections according to policy;
- prevent stale background jobs from re-admitting it;
- record only the minimum disclosed provenance needed for integrity or “do not re-propose” behavior;
- make any retained historical content and purge option visible.

A bounded tombstone may be useful to prevent a stale import, synchronization peer, or repeated agent proposal from silently restoring forgotten context. The tombstone must not itself become recallable context about the person.

### Delete

Remove specified state and the copies covered by the request.

A deletion request should name its target and coverage, for example:

- delete one context entry and its derived state;
- delete one topic and its history;
- delete pending proposals;
- delete an active projection;
- delete provenance content while retaining minimal integrity metadata;
- delete all state controlled by this implementation.

“Delete” must not mean merely removing an item from view while retaining an active or reconstructable copy elsewhere.

### Purge

Remove current state plus historical, derived, cached, projected, and other retained copies within the implementation’s control.

A purge may be narrower than “delete all” if it applies to one entry or scope. It is the operation that addresses residual copies, not merely the current canonical representation.

A purge should identify copies that cannot be removed immediately, such as encrypted backups scheduled to expire, and provide the expected deletion window.

### Reset

Return an implementation or scope to a known initial state.

Reset is an application convenience, not automatically a protocol operation. It should state whether it disables, forgets, deletes, or purges existing context. “Reset” must not obscure retention.

## Operation matrix

A human-readable operation matrix can prevent ambiguous controls:

| Operation | Active recall | Canonical content | History/provenance | Derived state | Projections | External exports |
| --- | --- | --- | --- | --- | --- | --- |
| Revoke audience | blocked for that audience | retained | retained per policy | inaccessible or invalidated for audience | destination-specific | unchanged |
| Disable store | blocked | retained | retained | disabled or invalidated | paused or removed per policy | unchanged |
| Forget entry | removed | removed from active state | minimal metadata or disclosed history may remain | removed or rebuilt | updated or removed | unchanged unless linked sync applies |
| Delete target | removed | removed | removed according to stated coverage | removed according to stated coverage | removed according to stated coverage | only controlled copies |
| Purge target | removed | removed | historical content removed within control | removed | removed within control | only controlled copies |

This table is illustrative. Each implementation must publish its actual semantics.

## Immediate, eventual, and best-effort effects

Not every copy can be removed at the same time.

An implementation should distinguish:

- **immediate** — enforced before the operation returns;
- **eventual** — scheduled with a documented deadline;
- **best effort** — attempted but not guaranteed;
- **outside control** — requires action in another system or by the person.

These states should not be collapsed into “done.”

For example:

- active recall may be blocked immediately;
- local indexes may be deleted immediately;
- synchronized peers may receive deletion eventually;
- encrypted backups may expire on a schedule;
- an offline export may be outside the source implementation’s control.

## Active sessions and loaded context

Revocation is hardest after context has already entered an active model session.

A runtime should:

- invalidate further recall and proposal operations immediately;
- stop background jobs and future turns from receiving disabled context;
- clear retrievable session caches where possible;
- avoid claiming it can erase text already present in a model’s context window when it cannot;
- offer a fresh session when continued isolation matters;
- explain which session artifacts or provider logs remain under separate retention policies.

A person should not need to restart the entire application merely to make access enforcement take effect, though a fresh model session may be necessary to remove already-injected context from conversational influence.

## Derived state must not resurrect context

Indexes, embeddings, summaries, rankings, pattern candidates, and caches must remain subordinate to canonical context.

After forgetting or deletion:

- retrieval should not return the removed content;
- a summary should not preserve its meaning as active context;
- reflection should not re-propose it solely from retained derived state;
- indexes should be rebuilt or invalidated;
- pattern models should not treat the removed entry as current truth;
- projections should not continue supplying it.

A test that deletes only the canonical file is insufficient.

## Proposals and dismissal records

Pending proposals are not accepted context, but they are still personal state.

A person should be able to:

- dismiss one proposal;
- clear pending proposals;
- remove proposal text and supporting excerpts;
- understand whether a minimal decision marker remains;
- remove or expire that marker where promised.

A “do not ask again” marker should be privacy-preserving, bounded, non-recallable, and included in deletion semantics.

## Provenance and history

Accountability and deletion can conflict.

An implementation should distinguish:

- provenance metadata that an operation occurred;
- full historical expressions;
- integrity hashes;
- proposal text;
- source excerpts;
- actor and session identifiers.

Forgetting may retain minimal provenance metadata if disclosed. Purging should remove historical content within the implementation’s control. If metadata must remain for security, legal, or integrity reasons, the reason, fields, access, and retention period should be explicit.

Provenance must not become a hidden mechanism for reconstructing deleted personal context.

## Projections and downstream copies

A projection is a copy supplied to another tool or instruction surface.

Revocation should identify:

- active projection destinations;
- whether the projection updates automatically;
- whether it can be removed remotely;
- whether the destination may have copied it further;
- whether the source operation removed, disabled, or merely stopped updating it.

Turning off the source store while leaving an active projection unchanged can violate the person’s expectation. Projection behavior should be explicit and independently controllable.

## Synchronization and stale copies

Synchronization peers and old exports can reintroduce removed context.

A sovereign design should use stable identity and deletion markers or another mechanism to prevent silent resurrection.

On import or sync, a stale copy of forgotten context should produce a conflict or remain inactive—not automatically become current because its timestamp is newer or its file still exists.

Deletion markers should contain the minimum information needed, expire according to disclosed policy, and remain removable where possible.

## External sources and credentials

Disconnecting an external source should revoke future access and invalidate credentials or tokens where possible.

It does not automatically delete:

- source data already copied into local caches;
- person-authored context derived from the source;
- run artifacts;
- drafts;
- provider-side logs;
- exports.

The interface should show those categories separately and offer cleanup where supported.

## Receipts

A revocation or deletion receipt should state:

- requested operation;
- target and scope;
- effective time;
- active sessions or agents affected;
- current canonical content removed or retained;
- proposals removed or retained;
- history and provenance behavior;
- derived state and caches removed or scheduled;
- projections affected;
- synchronized or backup copies pending;
- copies outside control;
- failures or uncertain outcomes;
- verification performed.

Receipts should avoid repeating deleted sensitive content.

## Verification

An implementation should verify outcomes rather than assume a delete call succeeded.

Useful checks include:

- recall returns no removed content;
- proposal tools cannot access a disabled store;
- indexes no longer reference removed entries;
- projections no longer contain the expression;
- active credentials are invalidated;
- the current manifest no longer lists deleted state;
- scheduled deletion jobs have a visible status;
- stale import attempts are blocked or reviewed.

Verification itself must not recreate or log the deleted content unnecessarily.

## Failure and partial completion

Deletion can fail or complete partially.

The interface should distinguish:

- succeeded;
- failed;
- partially completed;
- scheduled;
- unverifiable;
- outside control.

A partial deletion should identify residual copies and the next available action. The system must not present a reassuring success state when important copies remain active.

## Safe defaults

When semantics are unclear:

- disable access before attempting slower cleanup;
- prefer fresh sessions after sensitive revocation;
- prevent stale imports from activating automatically;
- retain less personal content in provenance and history;
- remove derived state rather than trying to preserve it;
- state limitations rather than implying universal deletion.

## What this document does not standardize

This document does not define:

- filesystem deletion methods;
- secure erasure guarantees;
- backup retention periods;
- tombstone schemas;
- synchronization protocols;
- projection APIs;
- provider log policies;
- legal retention rules;
- receipt schemas;
- user-interface labels;
- conformance requirements.

## Questions still under test

- Which operation words do people understand: disable, forget, delete, purge, reset, revoke?
- What should happen to active model sessions after memory is disabled?
- What minimal tombstone prevents resurrection without retaining meaning?
- Which provenance metadata should survive forgetting or deletion?
- When should projections be removed automatically?
- How should backup delays and outside-control copies be communicated?
- What verification is sufficient for a trustworthy deletion receipt?
- Which revocation behaviors should become mandatory for conformance?
