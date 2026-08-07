# Experiment 0006: Verify disablement, forgetting, and deletion

**Status:** Proposed  
**Protocol status:** Non-normative

## Question

Can a person predict and verify the difference between disabling a context store, forgetting one entry, deleting a scope, and purging all controlled copies?

## Human outcome

A person should be able to stop context use immediately, remove selected context, understand what remains, and receive an honest receipt when some copies are delayed or outside the implementation’s control.

## Hypothesis

Revocation will feel trustworthy when operations have distinct names and visible coverage, access is blocked before cleanup completes, derived state cannot restore removed context, and receipts distinguish immediate, eventual, failed, and outside-control effects.

## Smallest useful test

Create a synthetic store with:

- one global entry;
- one topic entry;
- one pending proposal;
- one dismissed-proposal marker;
- one historical version;
- one derived index and summary;
- one active projection into a mock agent file;
- one active agent session with recall access;
- one mock synchronized peer;
- one offline export package.

The person performs four operations in sequence:

1. disable the store;
2. re-enable it and forget the topic entry;
3. delete the global scope and selected history;
4. purge all remaining state controlled by the implementation.

The experiment then attempts active-session recall, projection use, derived-state retrieval, stale synchronization, and import from the offline export.

## Human capabilities

- [x] Inspect
- [ ] Author
- [x] Recall
- [x] Propose
- [x] Decide
- [x] Explain
- [x] Revoke
- [x] Move

## Interface variants

The experiment may use:

- a settings and deletion flow;
- a command-line inspection and cleanup flow;
- a context dashboard;
- another interface preserving the same human capabilities.

The interface must state what each operation affects before execution and issue a receipt afterward.

## Context scope

- **Context:** entirely synthetic and non-sensitive
- **Agents:** one active mock session and one fresh session
- **Projection:** one mock local instruction file
- **Synchronization:** one mock peer
- **Export:** one offline synthetic package
- **External services:** none

## Steps

### Part A: Disable

1. Show all current state and copies.
2. Disable the context store while an agent session remains active.
3. Attempt recall, topic enumeration, proposal creation, projection refresh, and background reflection.
4. Verify that access-layer operations fail immediately while canonical files remain stored.
5. Ask the person what they believe still exists.
6. Start a fresh session and verify no context is supplied.

### Part B: Forget

7. Re-enable the store.
8. Forget the topic entry.
9. Attempt recall by entry, topic, summary, and derived index.
10. Verify the active projection no longer contains the entry according to the disclosed projection policy.
11. Show any minimal tombstone, provenance metadata, or retained history and explain why it remains.
12. Attempt to synchronize a stale peer containing the forgotten entry; require review or keep it inactive.

### Part C: Delete

13. Delete the global scope and request removal of its historical content.
14. Verify current context, selected history, derived state, and controlled projections are removed.
15. Show any delayed backup or synchronization cleanup separately.
16. Verify provenance cannot reconstruct the deleted expression.

### Part D: Purge

17. Purge all remaining experiment state controlled by the implementation, including proposals, dismissal markers, caches, histories, manifests, projections, and mock synchronization data.
18. Verify the store and derived state are absent.
19. Attempt to import the old offline package.
20. Require a warning that it contains stale deleted context and prevent silent activation.
21. Show that the offline package remains outside the source implementation’s control until the person deletes it separately.
22. Issue a final receipt listing completed, delayed, failed, and outside-control effects.

## Evidence to collect

### Comprehension

- Can the person explain the difference between disable, forget, delete, and purge?
- Do they understand that disabling retains content?
- Do they understand which historical and provenance state remains after forgetting?
- Can they identify copies outside the implementation’s control?
- Which terms feel clear or misleading?

### Enforcement

- Do active-session recall and proposal operations fail after disablement?
- Does a fresh session receive no disabled context?
- Can generic tools or cached handles bypass the access layer?
- Do background tasks stop?
- Do projections follow the disclosed policy?

### Non-resurrection

- Can indexes, summaries, patterns, caches, or history return forgotten content?
- Does stale synchronization restore the entry automatically?
- Does an old export activate deleted context without review?
- Does provenance retain enough content to reconstruct the expression?

### Receipts and limitations

- Can the person tell what completed immediately?
- Are delayed and failed copies clearly identified?
- Are outside-control exports or provider logs described honestly?
- Does verification support the receipt without recreating sensitive content?

## Success signals

- The person accurately predicts each operation’s effect.
- Disablement immediately blocks access and proposals in active and fresh sessions.
- Forgetting removes active context and invalidates derived retrieval.
- Deletion removes the stated canonical, historical, derived, and projected copies.
- Purge clears all experiment state within control.
- Stale synchronization and import do not silently resurrect removed context.
- Receipts distinguish completed, delayed, failed, and outside-control effects.
- No operation is described as more complete than the implementation can verify.

## Stop or revise signals

- “Off” changes only a prompt while tools still return context.
- The person believes disabled data was deleted.
- Forgotten content remains available through summaries, indexes, history, or projections.
- A stale peer or export restores context automatically.
- Delete-all leaves undisclosed proposal, cache, projection, or history state.
- Provenance records preserve reconstructable deleted content without disclosure.
- The interface reports success despite material residual copies.
- Operation names create more confusion than clarity.

## Sovereignty review

- **Revocation is real:** enforcement precedes or accompanies cleanup.
- **Legibility:** each operation declares target, coverage, timing, and residual copies.
- **Derived state is subordinate:** caches and patterns cannot restore removed meaning.
- **Portability is selective:** offline exports and synchronized copies are tracked separately.
- **Interfaces are replaceable:** behavior is tested independently of one deletion UI.
- **Honesty:** limitations and outside-control copies remain visible.

## Privacy and security

Use only synthetic state, mock peers, and offline test packages.

Public findings should contain aggregate comprehension and failure categories, not deletion receipts, paths, identifiers, or package contents.

## What this experiment does not standardize

This experiment does not define:

- secure erasure technology;
- backup retention periods;
- tombstone or receipt schemas;
- synchronization protocols;
- provider-side deletion;
- exact operation labels;
- user-interface design;
- conformance requirements.

## Reversibility

The experiment itself ends only after all controlled synthetic state is purged. The offline package must be deleted separately, demonstrating an outside-control copy before final cleanup.

## Findings

To be completed after one or more implementations run the experiment.

### Observations

Pending.

### Interpretation

Pending.

### Possible protocol implications

Pending.

### Open questions

- Which operation terms are most understandable?
- What must be immediate when disabling context?
- How should already-injected model context be handled?
- What minimal deletion marker prevents resurrection?
- Which residual copies should a receipt always list?
- What revocation tests should become conformance requirements?
