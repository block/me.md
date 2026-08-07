# Outcome and feedback events

**Status:** Optional extension hypothesis. Non-normative.

What happened is different from what is true about a person.

An agent may recommend a next move. The person may act, dismiss, defer, correct, or ignore it. They may say an answer was useful, noisy, too much, or “not me.” Those events can help an application stop repeating mistakes and understand whether work cleared.

They must not silently become identity, personality, performance, or preference claims.

## The human questions

A person should be able to understand:

- What event was recorded?
- What suggestion, task, artifact, or interpretation did it refer to?
- Did I explicitly record it, or did the system observe it?
- How will it affect future behavior?
- Is it temporary run history, local calibration, or portable state?
- Can it create a durable-context proposal?
- How long is it retained?
- Can I inspect, correct, or delete it?

## Event, context, and evidence are different

An outcome event describes an occurrence:

> The person dismissed recommendation `move_123`.

It does not automatically justify a personal claim:

> The person avoids difficult conversations.

A feedback event may describe an evaluation:

> The person marked this signal as noise.

It does not automatically justify:

> The person does not care about this project.

Applications should preserve the event at the narrowest useful level.

## Candidate event vocabulary

The exact vocabulary remains under test. Useful categories may include:

### Recommendation outcome

- **acted** — the person says they completed or intentionally followed the recommendation;
- **dismissed** — the person decided not to follow it;
- **deferred** — the person intends to revisit it later;
- **superseded** — another decision or event made it obsolete;
- **resolved externally** — the underlying issue cleared without the person acting;
- **unknown** — the application cannot determine what happened.

### Quality feedback

- **useful** — the output or signal helped;
- **noise** — it was not worth surfacing;
- **too much** — the volume, detail, urgency, or interruption was excessive;
- **not me** — the interpretation or expression did not fit the person;
- **closer** — a correction improved the fit but did not fully resolve it;
- **wrong** — a factual or interpretive claim was incorrect;
- **stale** — the information was no longer current;
- **duplicate** — the system repeated an already-known or already-cleared item.

### Correction

A correction should identify what is being corrected:

- source fact;
- interpretation;
- scope;
- urgency;
- recommendation;
- expression;
- context recall;
- audience;
- status.

Corrections should not automatically rewrite durable context. They may improve the current run or produce a later proposal.

## Event targets

An event should refer to a stable target where possible:

- recommendation;
- signal;
- artifact;
- source item;
- context proposal;
- context entry;
- run or session;
- watch trigger;
- draft or action receipt.

Events without a target can easily become vague claims about the person.

## Event origin

Useful origins include:

- **person-reported** — the person explicitly recorded the outcome or feedback;
- **externally verified** — an authorized source confirms a state change;
- **system-observed** — the application observed a bounded event;
- **agent-inferred** — the agent guessed an outcome or interpretation.

Agent-inferred outcomes should not be represented as ground truth. Where the distinction matters, the person should be able to confirm or correct them.

## Ground truth and uncertainty

Person-reported events are strong evidence of the person’s decision, but may still be informal.

External verification may confirm that a pull request merged or an event was canceled, but not why the person acted or how they felt.

The application should distinguish:

- event occurred;
- event is reported;
- event is inferred;
- event remains unknown.

A missing action event is not proof that the person ignored a recommendation.

## An illustrative event

```json
{
  "id": "event_01J...",
  "at": "2026-08-07T18:45:00Z",
  "kind": "recommendation-outcome",
  "value": "dismissed",
  "target": {
    "type": "recommendation",
    "id": "move_01J..."
  },
  "origin": "person-reported",
  "scope": "run:01J...",
  "note": "Already handled elsewhere",
  "portability": "local-private"
}
```

This is not a required schema.

## Effects on application behavior

Events may support bounded application changes such as:

- stop presenting a completed recommendation as unresolved;
- suppress an exact duplicate;
- lower the ranking of a repeatedly noisy detector;
- show that a deferred item is due for review;
- compare a recommendation with its actual outcome;
- explain why a later artifact changed;
- propose an ignore rule after repeated, consistent corrections.

The effect should be explainable and reversible.

An event should not silently:

- create a durable personal preference;
- infer motivation or character;
- change a sensitive identity claim;
- authorize an action;
- widen source access;
- become a productivity score;
- be shared with an employer or manager by default.

## From patterns to proposals

Multiple events may suggest a pattern.

The sovereign lifecycle is:

```text
events → derived pattern candidate → candidate expression → person decides
```

Examples:

- repeated “too much” feedback may justify proposing “Keep routine briefings shorter by default.”
- repeated dismissal of one detector may justify proposing an ignore rule for that detector.
- repeated corrections from “urgent” to “not urgent” may justify reviewing urgency logic.

The application should not jump directly from repeated events to a trait such as “the person is disengaged” or “the person dislikes detail.”

A pattern may indicate a flawed detector or interface rather than a durable preference.

## Run history and daily continuity

An application may retain run-level artifacts such as:

- top signal;
- tension;
- gap;
- recommended move;
- outcome status;
- source coverage;
- generated time.

This can support “what changed since last time?” without treating run history as personal memory.

Run history should be classified separately from canonical context. It is typically local-private or ephemeral, bounded by retention, and excluded from ordinary portable exports.

## Event retention

Events can accumulate into a detailed behavioral record.

An implementation should disclose:

- event categories retained;
- contents and notes retained;
- retention period;
- whether events are portable;
- whether they are synchronized;
- who can inspect them;
- whether they affect ranking or proposals;
- how they are deleted;
- whether aggregate patterns remain after raw events are removed.

A useful default is bounded local retention with no raw event export unless deliberately selected.

## Data minimization

Event records should avoid unnecessary personal or third-party content.

Prefer:

- stable target reference;
- event category;
- timestamp;
- origin;
- bounded note;
- scope;
- retention and portability class.

Avoid copying full messages, documents, recommendations, or conversation transcripts into every event.

## Feedback and voice

Feedback about tone or presentation should remain scoped to the relevant interface or artifact unless the person chooses a broader durable expression.

For example:

> “Too playful for this warning.”

may correct the current output or presentation rule. It should not automatically become:

> “The person dislikes playful language.”

Sovereignty includes tone, but tone preferences still need appropriate expression and scope.

## Event conflicts and corrections

The person may correct an event:

- change acted to deferred;
- mark an inferred event as wrong;
- remove a note;
- attach the event to a different target;
- delete the event.

Applications should preserve provenance for material event changes without turning event history into an undeletable behavioral dossier.

## Portability

Outcome and feedback events should be excluded from ordinary context exports by default.

A person may choose to export:

- a bounded event set;
- aggregate calibration settings;
- selected recommendation outcomes;
- no events at all.

A receiving implementation must not treat imported events as accepted personal context or use them to infer sensitive identity.

## Receipts and explanation

When events affect ranking or suppression, the person should be able to inspect a human reason:

- hidden because you dismissed this exact recommendation;
- no longer shown because the source item resolved;
- reduced because you marked this detector as noise three times;
- proposed as a preference because you explicitly corrected the same presentation pattern repeatedly.

Opaque engagement optimization is not an acceptable substitute.

## What this document does not standardize

This document does not define:

- an event schema;
- required event vocabulary;
- retention periods;
- ranking algorithms;
- pattern-detection thresholds;
- outcome verification mechanisms;
- user-interface controls;
- portability defaults;
- conformance requirements.

## Questions still under test

- Which event vocabulary is small enough to remain understandable?
- Which events should be person-reported versus externally verified?
- How long should raw events remain?
- When should repeated feedback produce a proposal?
- How can applications learn without building a behavioral profile?
- Which event effects should be visible by default?
- Should any event categories be portable?
- What deletion behavior should apply to derived patterns after raw events are removed?
