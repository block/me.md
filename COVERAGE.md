# Coverage and explanation receipts

**Status:** Working protocol hypothesis. Non-normative.

A useful agent should not only produce an answer. It should be able to explain the material context and evidence boundaries behind that answer.

Coverage is not a list of everything connected to an application. It is an account of what was available, what was actually checked or recalled, what was partial or stale, and what the agent inferred rather than verified.

A receipt should increase trust without forcing the agent to narrate every ordinary preference it follows.

## The human questions

When context or external sources materially influence an outcome, a person should be able to answer:

- Which context scopes were available to this agent?
- Which entries or scopes were actually recalled?
- Which connected sources were authorized?
- Which sources were actually queried?
- What level of content was read?
- What was fresh, stale, partial, unavailable, or skipped?
- Which statements came from evidence?
- Which statements were interpretations or inferences?
- What uncertainty or gap might change the result?
- Was raw source content retained after the task?

## Authorization is not coverage

A source or context scope may be authorized without being used.

These states should remain distinct:

- **not authorized** — the agent cannot access it;
- **authorized** — access is permitted;
- **available** — the source or context can currently be reached;
- **attempted** — the implementation tried to access it;
- **read** — some defined content was successfully retrieved;
- **used** — the retrieved content materially influenced the output;
- **skipped** — access was possible but intentionally not attempted;
- **failed** — an access attempt did not succeed;
- **partial** — only part of the intended material was retrieved or processed;
- **stale** — the material may no longer represent current state;
- **disabled** — policy blocks use even if credentials or files still exist.

A connector shown as “connected” is not proof that the agent checked it for this task.

## Context availability and recall

A receipt should distinguish context made available to an agent from context actually selected for the task.

For example:

```text
Available:
- global communication defaults
- Project Phoenix context

Recalled:
- one global boundary
- Project Phoenix rollout constraints

Not exposed:
- unrelated personal topics
```

The receipt should avoid revealing a complete sensitive topic map merely to prove that unrelated context was not used.

Where possible, report narrow categories or counts rather than names of sensitive scopes.

## External-source coverage

External sources may include calendars, documents, code, messages, databases, or other changing systems.

A useful source receipt may identify:

- source type and account or workspace, where appropriate;
- purpose of access;
- query or selection boundary;
- time window;
- level of content read;
- freshness time;
- result status;
- whether content was retained;
- whether the source materially influenced the output.

“Read” should describe the real depth of access.

Examples:

- event titles and times only;
- message headers only;
- full document body;
- repository metadata but not file contents;
- first page of a paginated result;
- 18 of 25 matching records;
- cached snapshot from two hours ago.

A partial or headers-only read must not be presented as complete source understanding.

## Observations, interpretations, and recommendations

A trustworthy output should preserve the distinction between:

- **observation** — directly supported by recalled context or source evidence;
- **interpretation** — the agent’s synthesis or explanation;
- **recommendation** — a proposed next move;
- **uncertainty** — a material question that could not be resolved;
- **assumption** — a provisional premise used to proceed.

This distinction does not require every sentence to carry a label. It should be available where confusion would materially change the person’s decision.

An interpretation should not be phrased as if it were a stored fact about the person.

## Materiality

Not every use of context needs a visible disclosure.

Quietly honoring “lead with the answer” may be the right experience.

A receipt becomes especially valuable when:

- the output makes a consequential recommendation;
- a sensitive context scope influenced the result;
- source coverage is partial or stale;
- the agent chose among competing priorities;
- an inference could be mistaken for a fact;
- a source or context scope was unavailable;
- the person asks why the result was produced;
- an external action is being previewed;
- context from another project or topic might be suspected.

## Coverage should be truthful under failure

A polished answer can conceal poor coverage.

When access fails, the implementation should not silently substitute confidence.

It should distinguish:

- no results because nothing matched;
- no results because access failed;
- no results because the source was skipped;
- no results because only a limited time window was checked;
- no results because cached data was used;
- unknown outcome because the response could not be verified.

If a material source is missing, the output should state the limitation close enough to the conclusion to matter.

## Freshness and time

Coverage is time-bound.

A receipt should identify when material context or evidence was retrieved and whether the task depends on current state.

Useful concepts include:

- retrieved at;
- source-reported update time;
- cache age;
- relevant time window;
- expiration or freshness expectation;
- whether a later event could invalidate the result.

A source checked yesterday may be sufficient for a stable preference and inadequate for an imminent meeting or live incident.

## Explanation of selection

When an application ranks signals, chooses one recommendation, or recalls one scope, the person may need to understand why.

A useful explanation might say:

- this project context matched the active workspace;
- a global boundary applied to every authorized agent;
- a topic was recalled because the person explicitly named it;
- an item outranked another because of an imminent deadline;
- one source was excluded because access was disabled;
- a recommendation remained quiet because no time-sensitive trigger existed.

Explanations should use human reasons rather than opaque numeric scores alone.

Numbers may support implementation logic, but they should not create false precision or hide value judgments.

## Coverage receipts and privacy

A receipt can itself reveal sensitive information.

It may expose:

- topic names;
- source accounts;
- project names;
- document titles;
- relationship patterns;
- queries;
- timestamps;
- inferred interests.

Receipts should use the least detail needed for understanding. A person may inspect more locally, but portable or shared receipts should be conservative by default.

Coverage receipts are private state unless the person chooses to share them.

## Retention

An implementation should state whether receipts retain:

- identifiers only;
- bounded summaries;
- source references;
- raw queries;
- raw content;
- model prompts or outputs;
- context-entry identifiers;
- error details.

Receipts should not become a duplicate archive of every source read.

A useful default is metadata and references without raw personal or third-party content, with a bounded retention period suitable for explanation and debugging.

## Coverage and provenance

Coverage explains what informed a run or output.

Provenance explains how durable state changed.

They may reference one another, but they are different:

- recalling a context entry belongs in a coverage receipt;
- editing that entry belongs in provenance;
- authorizing an action belongs in a capability record;
- the action result belongs in an execution receipt.

One giant log should not blur these meanings.

## Coverage and derived state

Routing models, indexes, rankings, and summaries may influence what is selected.

A receipt should identify material derived selection without exposing proprietary model traces or pretending to provide hidden chain-of-thought.

Useful explanation can focus on observable factors:

- matched active project;
- explicit topic request;
- freshness threshold;
- deadline proximity;
- user-declared priority;
- unavailable source;
- scope restriction.

The person needs a reason they can evaluate, not private model reasoning.

## An illustrative receipt

```json
{
  "id": "receipt_01J...",
  "task": "prepare for a project review",
  "at": "2026-08-07T18:30:00Z",
  "context": {
    "available": ["scope:global", "project:phoenix"],
    "recalled": ["ctx_boundary_send", "ctx_phoenix_rollout"],
    "excluded_count": 3
  },
  "sources": [
    {
      "type": "calendar",
      "status": "read",
      "depth": "event metadata and attachments",
      "fresh_at": "2026-08-07T18:29:40Z",
      "retained": "references-only"
    },
    {
      "type": "project-docs",
      "status": "partial",
      "detail": "2 of 3 linked documents available"
    }
  ],
  "material_gaps": ["one linked project document unavailable"],
  "inferences": ["agenda likely focuses on rollout risk"]
}
```

This is not a required schema.

## Interface forms

Coverage may appear as:

- a concise line near an answer;
- an expandable “why this?” view;
- a run receipt;
- a source and context panel;
- inline evidence references;
- a machine-readable artifact;
- a warning when material coverage is missing.

The interface should optimize for the person’s decision, not for displaying every internal operation.

## What this document does not standardize

This document does not define:

- a receipt schema;
- source identifiers;
- citation syntax;
- retention periods;
- required user-interface placement;
- ranking explanations;
- freshness thresholds;
- model reasoning disclosure;
- conformance requirements.

## Questions still under test

- Which coverage states are understandable without being overly technical?
- When should a receipt be visible by default?
- How can a receipt prove least-context use without exposing sensitive topic names?
- What source-read depth should be standardized, if any?
- Which material gaps must appear next to a recommendation?
- How long should receipts be retained?
- Which receipt fields should be portable?
- What explanation is useful without exposing private model reasoning?
