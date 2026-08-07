# Experiment 0005: Inspect and move a selected context subset

**Status:** Proposed  
**Protocol status:** Non-normative

## Question

Can a person understand what state is portable, select a narrow subset, move it to a second trusted interface, and verify that nothing broader moved or became active unexpectedly?

## Human outcome

A person should be able to move useful continuity without exporting their entire context store, hidden derived state, raw source data, or sensitive topic map.

They should understand what was included, what stayed local, what the destination will do with it, and which copies remain after the move.

## Hypothesis

Portability will feel sovereign when it is selective, inspectable, and receipt-based rather than a single “export everything” operation.

A legible inventory of state classes should help people distinguish canonical context from history, projections, derived state, and local-only implementation data.

## Smallest useful test

Create a synthetic context store containing:

- two global entries;
- one non-sensitive topic with one entry;
- one project entry;
- one pending proposal;
- one dismissed proposal marker;
- one historical version;
- one derived index;
- one active projection;
- one synthetic external-source cache;
- one fake credential placeholder that must never export.

The person chooses to export only one global entry and the project context to a second mock interface.

The destination previews the import, leaves it inactive until confirmed, and reports unsupported or transformed fields. The person verifies that the topic, proposals, history, derived state, source cache, and credential did not move.

## Human capabilities

- [x] Inspect
- [ ] Author
- [ ] Recall
- [ ] Propose
- [x] Decide
- [x] Explain
- [x] Revoke
- [x] Move

## Interface variants

The experiment may use:

- an export/import wizard;
- a command-line manifest and package preview;
- a settings-based portability view;
- a plain inspectable archive with a separate import confirmation;
- another interface preserving the same human capabilities.

The interface must distinguish current canonical context from other state classes before export.

## Context scope

- **Context:** entirely synthetic and non-sensitive
- **Source:** one test implementation
- **Destination:** one mock trusted interface
- **Export subset:** one global entry and one project scope
- **External effects:** local package creation and simulated import only

## Steps

1. Show the person an inventory of all synthetic state by class.
2. Ask them which items they expect an ordinary context export to include.
3. Let them select one global entry and one project scope.
4. Show a pre-export summary of included and excluded state.
5. Create an inspectable package and export receipt.
6. Open the package in a second mock interface.
7. Show what the destination can preserve, transform, or cannot support.
8. Ask the person to predict what will become active after import.
9. Require a separate import confirmation before activation.
10. Verify that only the selected context becomes active.
11. Verify that the topic name and contents, proposals, history, derived index, source cache, and fake credential did not move.
12. Edit or forget one source entry and explain whether the exported copy changes automatically.
13. Remove imported context from the destination and show which source, package, projection, and provenance copies remain.

## Evidence to collect

### Inventory comprehension

- Can the person distinguish canonical context from derived, historical, projected, ephemeral, and local-only state?
- Which state classes are confusing or feel overly technical?
- Do they expect accepted context to export by default?
- Do they expect topic names to remain private when topic contents are excluded?

### Selection and preview

- Can the person predict exactly what the package contains?
- Do they notice history, third-party data, and sensitive-scope warnings?
- Do default selections feel conservative enough?
- Does the package remain human-inspectable?

### Import integrity

- Does the destination preserve wording, scope, strength, origin, and stable identity where supported?
- Does it report unsupported semantics rather than silently dropping or broadening them?
- Does imported context remain inactive until confirmed?
- Can the destination avoid creating undisclosed projections or derived profiles?

### Copy and deletion understanding

- Does the person understand that an offline export will not update automatically?
- Can they identify the source copy, export package, destination copy, and active projection?
- Do they understand which copies are affected by deletion in each interface?

## Success signals

- The person selects a narrow subset and accurately predicts the result.
- Sensitive and unrelated state remains excluded.
- Topic metadata does not leak when the topic is not selected.
- Pending and dismissed proposals do not become accepted context.
- Derived state and source caches remain excluded by default.
- The destination previews conflicts and unsupported semantics.
- Imported context does not activate without confirmation.
- Receipts explain included, excluded, and remaining copies.

## Stop or revise signals

- “Export context” silently includes the entire store.
- Topic names or descriptions leak despite excluding the topic.
- Credentials, raw source data, history, or derived state are included without explicit selection.
- Import broadens scope, strengthens wording, or admits proposals automatically.
- A stale package silently resurrects forgotten context.
- The person believes source deletion removed an offline export or destination copy when it did not.
- The destination creates a hidden competing source of truth.

## Sovereignty review

- **Selective portability:** only the person-selected subset moves.
- **Legibility:** inventory, preview, package, and receipts are inspectable.
- **Scope:** global and project context remain distinct.
- **Chosen durability:** proposals remain proposals; import requires separate admission.
- **Privacy:** sensitive, third-party, credential, and derived state are excluded by default.
- **Revocation:** copy boundaries and deletion limits are explicit.
- **Interface replaceability:** the destination may differ technically while preserving meaning.

## Privacy and security

Use only synthetic state and a mock destination. The fake credential placeholder must be represented only as an exclusion test and must not contain a real secret.

Public findings should report aggregate comprehension, selection, and conflict patterns—not packages, manifests, or participant data.

## What this experiment does not standardize

This experiment does not define:

- a package or archive format;
- a manifest schema;
- encryption;
- transport or synchronization;
- merge algorithms;
- stable identifier syntax;
- sensitive-data taxonomies;
- import interface design;
- conformance requirements.

## Reversibility

Delete the synthetic package, mock destination data, receipts, projections, caches, and test state. No real external service or personal context should be involved.

## Findings

To be completed after one or more implementations run the experiment.

### Observations

Pending.

### Interpretation

Pending.

### Possible protocol implications

Pending.

### Open questions

- Which state classes make sense to people?
- What should ordinary export select by default?
- How should stale exports interact with later forgetting or deletion?
- Which semantics must a destination preserve before activating imported context?
- How should active projections appear in portability receipts?
