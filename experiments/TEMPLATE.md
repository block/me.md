# Experiment template

**Number:** `0000`  
**Title:** A short description of the human question  
**Status:** Proposed | Running | Learned | Retired  
**Protocol status:** Non-normative

## Question

What is the smallest human question this experiment is trying to answer?

## Human outcome

What should become easier, safer, clearer, or more trustworthy for the person?

## Hypothesis

What do we currently believe, and why is it worth testing?

## Smallest useful test

Describe the minimum experience needed to test the hypothesis. Avoid combining adjacent capabilities unless they are necessary to answer the question.

## Human capabilities

Select the capabilities this experiment exercises:

- [ ] Inspect
- [ ] Author
- [ ] Recall
- [ ] Propose
- [ ] Decide
- [ ] Explain
- [ ] Revoke
- [ ] Move

## Interface variants

Which interfaces may implement the experiment? What must each interface make possible without prescribing its exact design?

## Context scope

What context may be used?

- Scope: global | topic | project | other
- Sensitivity: synthetic | non-sensitive | sensitive
- Audience: which agents, applications, or people may access it?
- Retention: what is kept, for how long, and where?

## Steps

1. Describe the participant's first action.
2. Describe what the agent or interface does.
3. Describe the fresh-session or changed-state check.
4. Describe how the participant corrects, removes, or exits the experiment.

## Evidence to collect

List the behavioral signals and questions that will help answer the hypothesis. Prefer observations about comprehension, predictability, burden, trust, and control over engagement metrics alone.

## Success signals

What outcomes would support continuing or expanding the experiment?

## Stop or revise signals

What outcomes would indicate harm, confusion, overreach, or a failed hypothesis?

## Sovereignty review

Which commitments in [`SOVEREIGNTY.md`](../SOVEREIGNTY.md) does this exercise or put at risk?

Answer explicitly:

- Can the person inspect and correct the context?
- Is the least necessary context used?
- Does current instruction override durable context?
- Can the experiment be disabled or reversed?
- Does stored context grant any new action authority?
- Could an implementation-specific store become a competing source of truth?

## Privacy and security

What personal context is read, written, derived, indexed, retained, projected, or deleted? How will public findings avoid exposing it?

## What this experiment does not standardize

List the storage formats, paths, APIs, interface details, models, or adjacent behaviors that remain open.

## Reversibility

How can the experiment be removed? Would any user-owned context require migration or cleanup?

## Findings

Complete after running the experiment.

### Observations

What happened?

### Interpretation

What might those observations mean?

### Possible protocol implications

What may deserve a later protocol proposal? What should remain implementation-specific?

### Open questions

What should be tested next?
