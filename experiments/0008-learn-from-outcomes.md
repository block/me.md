# Experiment 0008: Learn from outcomes without profiling the person

**Status:** Proposed  
**Protocol status:** Non-normative

## Question

Can an application use explicit outcome and quality feedback to stop repeating mistakes and track whether recommendations cleared—without turning events into hidden personal traits or productivity telemetry?

## Human outcome

A person should be able to record what happened and see a bounded, understandable effect:

- “acted” clears the recommendation;
- “dismissed” stops the exact item from nagging;
- “deferred” preserves a chosen review point;
- “noise” reduces or suppresses the relevant detector;
- “not me” corrects an interpretation without creating a durable identity claim.

## Hypothesis

A small event vocabulary with stable targets, visible origin, bounded retention, and explainable effects will help agents improve while preserving the difference between behavior history and personal context.

## Smallest useful test

Use a synthetic orientation workflow that produces several recommendations and signals over multiple runs.

The person records:

- one recommendation as acted;
- one as dismissed with a bounded note;
- one as deferred until a chosen date;
- one detector output as noise three times;
- one interpretation as “not me.”

The application updates later runs, shows the event-driven reasons, and—after repeated noise feedback—may create one proposed ignore rule. The proposal remains inactive until accepted.

## Human capabilities

- [x] Inspect
- [ ] Author
- [ ] Recall
- [x] Propose
- [x] Decide
- [x] Explain
- [x] Revoke
- [ ] Move

## Interface variants

The experiment may use:

- inline feedback controls;
- a run-history view;
- a command-line event recorder;
- an outcome review panel;
- another interface preserving the same human capabilities.

## Context and event scope

- **Recommendations and signals:** synthetic
- **Events:** local-private by default
- **Retention:** bounded to the experiment window
- **Agent proposals:** at most one synthetic ignore-rule proposal
- **Sensitive context:** none

## Steps

1. Present a synthetic recommendation and let the person mark it acted.
2. Run the workflow again and verify the recommendation is shown as cleared rather than unresolved.
3. Present another recommendation and let the person dismiss it with “already handled elsewhere.”
4. Verify the exact recommendation does not reappear as active.
5. Let the person defer a third item to a chosen date and verify it remains quiet until that date.
6. Surface one synthetic detector output across three runs and let the person mark it noise each time.
7. Show how the detector’s influence changes and why.
8. Optionally propose one bounded ignore rule based on the repeated explicit feedback.
9. Verify the proposal remains inactive until accepted.
10. Present an interpretation and let the person mark it “not me.”
11. Verify the current interpretation is corrected without creating a trait or identity memory.
12. Show the event history, origin, retention, and effects.
13. Delete selected raw events and verify derived patterns are removed or recomputed according to the disclosed policy.

## Evidence to collect

### Vocabulary comprehension

- Can the person distinguish acted, dismissed, deferred, resolved, useful, noise, too much, not me, and wrong?
- Which categories overlap or feel judgmental?
- Do people want free-text notes, fixed labels, or both?

### Effect predictability

- Does acted clear the correct target?
- Does dismissed suppress only the intended recommendation?
- Does deferred return at the expected time?
- Is detector weighting or suppression understandable?
- Does “not me” correct the interpretation without broadening into identity?

### Profile boundary

- Can the person distinguish event history from durable context?
- Does repeated feedback create a proposal rather than an automatic preference?
- Does the application blame the person when a detector is poor?
- Are events used for product engagement or employee scoring beyond the disclosed purpose?

### Retention and deletion

- Can the person inspect and delete events?
- What happens to aggregate patterns after raw events are deleted?
- Are full recommendations or transcripts duplicated into events?
- Do imported or exported events become context accidentally?

## Success signals

- The person understands the event vocabulary and expected effects.
- Recommendation outcomes attach to stable targets.
- Cleared items stop appearing as unresolved.
- Dismissal and deferral remain narrow and reversible.
- Repeated feedback may create a proposal but never an automatic personal rule.
- “Not me” corrects the current interpretation without creating identity memory.
- Event-driven ranking changes have human-readable explanations.
- Raw event deletion updates or removes derived patterns as disclosed.

## Stop or revise signals

- Missing events are interpreted as inaction or disengagement.
- Dismissal becomes a broad claim that the person does not care.
- Feedback is used as productivity or performance telemetry.
- Events silently create durable context or sensitive traits.
- A detector repeatedly blames the person instead of being corrected.
- Event notes duplicate large amounts of source or conversation content.
- Deleting raw events leaves undisclosed behavioral patterns active.
- The vocabulary feels moralizing or manipulative.

## Sovereignty review

- **Events are not identity:** occurrences remain separate from personal context.
- **Chosen durability:** patterns produce proposals, not automatic memories.
- **Legibility:** event effects on ranking or suppression are explainable.
- **Scope:** feedback applies to the target or detector it names.
- **Revocation:** events and derived patterns can be removed.
- **Anti-surveillance:** events are not employer or engagement telemetry by default.

## Privacy and security

Use only synthetic recommendations, signals, and event notes. Public findings should contain aggregate comprehension and effect patterns, not event streams or participant transcripts.

## What this experiment does not standardize

This experiment does not define:

- an event schema or vocabulary;
- ranking formulas;
- detector thresholds;
- retention periods;
- event portability;
- user-interface controls;
- conformance requirements.

## Reversibility

Remove all synthetic recommendations, raw events, derived patterns, proposed rules, run artifacts, and experiment state.

## Findings

To be completed after one or more implementations run the experiment.

### Observations

Pending.

### Interpretation

Pending.

### Possible protocol implications

Pending.

### Open questions

- Which event labels are clearest and least judgmental?
- When does repeated feedback justify a proposal?
- How should derived patterns respond to raw-event deletion?
- Which event effects should be visible by default?
- Can applications learn enough without retaining detailed event history?
