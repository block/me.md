# Experiment 0007: Understand context and source coverage

**Status:** Proposed  
**Protocol status:** Non-normative

## Question

Can a person understand what context and evidence informed an agent’s answer, notice material gaps, and distinguish observations from interpretations without being overwhelmed by implementation detail?

## Human outcome

A person should be able to tell:

- what context was available;
- what context was actually recalled;
- which sources were checked;
- how deeply they were read;
- what was stale, partial, unavailable, or skipped;
- what the agent inferred;
- whether a gap should change their decision.

## Hypothesis

A concise receipt with expandable detail will improve calibration when it emphasizes material gaps and observable selection reasons rather than narrating every tool call or exposing sensitive topic names.

## Smallest useful test

Use one synthetic decision-preparation task across three otherwise comparable runs:

1. **Complete coverage:** relevant global and project context available; all synthetic sources read.
2. **Partial coverage:** one linked document unavailable and one source read only at metadata level.
3. **Restricted coverage:** topic access disabled and one external source not authorized.

Each run produces the same style of answer plus a coverage receipt. The person explains what they believe the agent knew, what it did not know, and how much confidence they place in the recommendation.

## Human capabilities

- [x] Inspect
- [ ] Author
- [x] Recall
- [ ] Propose
- [ ] Decide
- [x] Explain
- [ ] Revoke
- [ ] Move

## Interface variants

The experiment may use:

- a one-line coverage summary with expandable details;
- inline evidence references;
- a run receipt;
- a context/source side panel;
- a command-line report;
- another interface preserving the same human capabilities.

## Context and source scope

- **Context:** synthetic global boundary, project context, and one unrelated hidden topic
- **Sources:** synthetic calendar, project documents, and message metadata
- **Retention:** references and bounded receipt metadata only
- **Sensitivity:** non-sensitive synthetic data

The unrelated topic name should remain hidden in every run.

## Steps

1. Show the person the synthetic task and the answer from the complete-coverage run.
2. Ask what they believe the agent used before revealing the receipt.
3. Show the concise receipt and let them expand details.
4. Repeat with the partial-coverage run.
5. Ask whether the missing document or metadata-only read changes their interpretation.
6. Repeat with the restricted-coverage run.
7. Ask whether “not authorized,” “not attempted,” and “failed” feel meaningfully different.
8. Show one observation, one interpretation, and one recommendation from each run.
9. Ask the person to classify them and identify any statement that sounds more certain than the receipt supports.
10. Verify that the receipt reveals no unrelated topic name or raw source content.
11. Show what receipt state is retained and how it can be removed.

## Evidence to collect

### Coverage comprehension

- Can the person distinguish authorized, available, attempted, read, used, skipped, failed, partial, stale, and disabled?
- Which distinctions matter to their decision?
- Can they tell the depth of a source read?
- Do they understand that connected does not mean checked?

### Calibration

- Does partial coverage reduce confidence appropriately?
- Does the person identify which gap could change the recommendation?
- Does the answer itself need a nearby warning, or is an expandable receipt enough?
- Does the receipt prevent a polished answer from feeling falsely complete?

### Context privacy

- Can the receipt prove narrow recall without naming unrelated topics?
- Do counts or scope categories provide enough assurance?
- Does the receipt expose project, source, query, or timing details unnecessarily?

### Explanation quality

- Can the person distinguish observation, interpretation, recommendation, assumption, and uncertainty?
- Are selection reasons understandable without numeric scores or hidden model reasoning?
- Does the agent over-narrate ordinary preference use?

## Success signals

- The person accurately identifies complete, partial, restricted, and failed coverage.
- Material gaps change confidence or next steps appropriately.
- The receipt distinguishes source depth and freshness.
- Unrelated topic metadata remains hidden.
- Observations and interpretations are not confused.
- The interface remains concise when coverage is ordinary and more visible when gaps are material.
- Receipts do not retain raw source content by default.

## Stop or revise signals

- The person assumes a connected source was checked when it was not.
- “No result” hides an access failure or skipped query.
- A metadata-only read is presented as full-content understanding.
- Sensitive topic names leak in the receipt.
- The receipt is so detailed that people ignore it.
- The receipt is so terse that material gaps remain invisible.
- Numeric scores imply more certainty than the evidence supports.
- Explanation drifts into private chain-of-thought rather than observable reasons.

## Sovereignty review

- **Legibility:** material context and evidence boundaries are inspectable.
- **Scope:** the receipt demonstrates least-context use without exposing unrelated context.
- **Privacy:** raw source content and sensitive topic names are minimized.
- **Authority:** interpretations remain distinguishable from facts about the person.
- **Implementation independence:** the experiment tests comprehension, not one receipt UI or source connector.

## Privacy and security

Use only synthetic context and sources. Public findings should contain aggregate comprehension and calibration patterns, not receipts, queries, source identifiers, or transcripts.

## What this experiment does not standardize

This experiment does not define:

- a receipt schema;
- source or context identifiers;
- citation syntax;
- freshness thresholds;
- required UI placement;
- retention periods;
- model reasoning disclosure;
- conformance requirements.

## Reversibility

Remove synthetic run receipts, source fixtures, context fixtures, caches, and experiment state. No real connected source should be involved.

## Findings

To be completed after one or more implementations run the experiment.

### Observations

Pending.

### Interpretation

Pending.

### Possible protocol implications

Pending.

### Open questions

- Which coverage states matter most to people?
- When should gaps be shown inline rather than behind an explanation view?
- How can least-context use be demonstrated without revealing sensitive metadata?
- What receipt data is useful enough to retain?
- Which coverage behaviors should become conformance requirements?
