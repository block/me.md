# Experiment 0003: Understand why context changed

**Status:** Proposed  
**Protocol status:** Non-normative

## Question

Can a person understand who changed a piece of durable context, why the change was allowed, and what remains after correction or removal—without being exposed to implementation internals or a surveillance-like activity log?

## Human outcome

A person should be able to inspect one context entry and answer:

- Where did this come from?
- Did I write it, ask for it, accept a proposal, import it, or receive it through a migration?
- Has anyone or anything changed it since?
- Why was that change permitted?
- Is an older version still retained anywhere?
- What can I undo or purge?

## Hypothesis

Provenance will increase trust when it is attached to meaningful mutations, uses honest actor and authorization language, and minimizes copies of personal content.

A raw Git history or verbose event stream may be technically complete while remaining confusing, overly detailed, or privacy-invasive. The experiment should test comprehension, not the amount of metadata shown.

## Smallest useful test

Use one non-sensitive context entry and exercise three mutation paths:

1. the person authors the entry directly;
2. an agent proposes an edit and the person revises or accepts it;
3. the person removes or forgets the entry.

The interface then offers a human-readable provenance view for the entry and explains what historical content, if any, remains after removal.

An optional variant may include an edit made through a second trusted interface or text editor to test honest “external edit” attribution.

## Human capabilities

- [x] Inspect
- [x] Author
- [ ] Recall
- [x] Propose
- [x] Decide
- [x] Explain
- [x] Revoke
- [ ] Move

## Interface variants

The experiment may be implemented as:

- an entry-level “history” or “why is this here?” view;
- a timeline in a settings interface;
- a command-line inspection flow;
- a plain provenance document;
- another interface that preserves the same human capabilities.

The interface should not require the person to understand commits, hashes, event sourcing, or database records.

## Context scope

- **Scope:** one synthetic or non-sensitive global context entry
- **Audience:** only the test interfaces and agents
- **Retention:** current expression plus the minimum provenance and optional history required by the implementation
- **External sources:** none required

## Steps

1. The person authors a simple entry, such as “By default, lead with the answer.”
2. They inspect the entry and its origin.
3. In a later interaction, an agent proposes a scoped edit, such as adding “Expand when I ask for detail.”
4. The person revises or accepts the proposal.
5. They inspect the provenance view and explain who changed what, why it was allowed, and whether the agent wording was revised.
6. The person corrects the entry directly.
7. Optionally, the entry is edited through another trusted interface or text editor.
8. The person inspects how the system attributes that edit.
9. The person forgets or removes the entry.
10. The interface explains what active context, provenance metadata, historical content, caches, and projections remain.
11. Where supported, the person purges retained historical content and verifies the result.

## Evidence to collect

### Comprehension

- Can the person identify the current canonical expression?
- Can they identify who or what last changed it?
- Can they explain the authorization basis?
- Can they distinguish direct authorship from an accepted agent proposal?
- Can they tell whether a proposal was revised before admission?
- Can they explain what remains after forgetting or deletion?

### Trust and burden

- Does the provenance view increase confidence or create anxiety?
- Is the amount of information appropriate?
- Which details are useful: actor, time, operation, authorization, source, old wording, or integrity status?
- Does the interface feel like personal control or like an activity-monitoring system?

### Integrity

- Does every tested mutation produce honest provenance?
- Does a failed provenance write create a visible accountability gap?
- Are unknown external edits labeled honestly rather than attributed to the person or agent?
- Does the current source match the last applied mutation?
- Can superseded or forgotten content still influence an agent?

### Data minimization

- Does provenance duplicate the full context text unnecessarily?
- Can the person understand the event using identifiers, concise summaries, or hashes?
- What historical content is retained for undo?
- Is retained history included in deletion and export behavior?

## Success signals

- The person can explain the entry’s origin and last meaningful change without technical assistance.
- Agent-mediated changes show the exact authorization path.
- Revised proposals are distinguishable from proposals accepted as written.
- Unknown or external edits are attributed honestly.
- Forgetting removes the entry from active context.
- The interface clearly explains whether metadata or historical content remains.
- Provenance does not expose unrelated conversation content or become a broad activity log.

## Stop or revise signals

- The system attributes an unknown change to the person or an agent without evidence.
- A prompt-level instruction is presented as proof of authorization.
- Provenance silently fails while agent-mediated writes continue as if fully accounted for.
- The person cannot distinguish current context from retained history.
- Forgotten or superseded wording continues to influence agents.
- The interface requires Git or database expertise.
- Provenance collects substantially more personal content than needed.
- The feature feels primarily useful to administrators rather than to the person.

## Sovereignty review

This experiment exercises authority, legibility, chosen durability, revocation, and implementation independence.

- **Authority:** provenance must show why a change was legitimate without turning the record into a new authority over the person.
- **Legibility:** the person can understand meaningful changes in ordinary language.
- **Chosen durability:** agent proposals remain inactive until accepted.
- **Revocation:** provenance and history behavior after forgetting or deletion is explicit.
- **Implementation independence:** the experiment tests human questions, not Git, JSONL, SQLite, or another mechanism.
- **Anti-surveillance:** provenance is scoped to context integrity and is not a general behavioral log.

## Privacy and security

Use synthetic or non-sensitive context.

Public findings should report only aggregate observations, redacted interface patterns, and categories of confusion or value. Do not publish raw context, proposal text, timelines, actor identifiers, or interaction transcripts by default.

Implementations should disclose whether full historical expressions are retained, encrypted, synchronized, backed up, or exported.

## What this experiment does not standardize

This experiment does not define:

- a provenance event schema;
- stable identifier syntax;
- Git, JSONL, a database, or an append-only ledger;
- cryptographic hashes or signatures;
- retention periods;
- fail-open or fail-closed behavior;
- history and undo user interface;
- synchronization conflict handling;
- conformance requirements.

## Reversibility

The experiment must be removable without leaving an undisclosed history store behind.

The person should be able to remove the test entry, experiment-specific caches, retained historical content, and provenance state covered by the implementation’s cleanup promise.

## Findings

To be completed after one or more implementations run the experiment.

### Observations

Pending.

### Interpretation

Pending.

### Possible protocol implications

Pending.

### Open questions

- What is the minimum provenance that people actually understand and use?
- Is old wording necessary for trust, or mostly useful for undo?
- Which mutation paths need fail-closed provenance?
- How should external edits be reconciled across interfaces?
- What metadata should survive forgetting or deletion?
- Can provenance remain useful without becoming telemetry?
