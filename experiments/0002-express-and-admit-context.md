# Experiment 0002: Express and admit proposed context

**Status:** Proposed  
**Protocol status:** Non-normative

## Question

Can an agent turn something said in conversation into a concise, bounded durable-context proposal that the person recognizes as accurate and theirs?

## Human outcome

A person should be able to see exactly how an agent would express a possible memory, understand where it would apply, revise the language, and decide whether it becomes durable context.

The resulting statement should help future agents without reducing the person to a trait, score, or profile written about them.

## Hypothesis

Agent-proposed context will feel more trustworthy when:

- the proposed sentence is shown exactly;
- it uses language the person recognizes;
- scope, strength, audience, and origin are visible;
- the person can edit the sentence before acceptance;
- no hidden interpretation becomes active alongside it.

Acceptance rate is not the primary measure. A clear dismissal may demonstrate control. The more important question is whether the person understands and owns the expression being proposed.

## Smallest useful test

During a real but non-sensitive task, the person expresses a reusable preference or boundary naturally.

For example:

> This review is too detailed. Start with the biggest risk and then add the rest.

After the preference has been relevant to the task, the agent may offer one proposal:

```text
Remember this?

“By default, when reviewing code, start with the largest risk.
Add detail after.”

Applies to: authorized agent sessions, when reviewing code
Strength: default
Origin: suggested from this conversation

[Edit]  [Remember]  [Not now]
```

The person accepts, edits, or dismisses the proposal. If accepted, the final visible source must contain exactly the person-approved expression.

This experiment ends at admission. It does not test whether the entry is later recalled correctly; that should be evaluated separately so expression quality is not confused with retrieval quality.

## Human capabilities

- [x] Inspect
- [x] Author
- [ ] Recall
- [x] Propose
- [x] Decide
- [x] Explain
- [x] Revoke
- [ ] Move

`Author` includes editing the candidate expression into the person's own words. `Revoke` is limited to removing an accepted test entry or ensuring a dismissed proposal did not become durable.

## Interface variants

The experiment may be implemented through:

- an in-conversation proposal card;
- a pending-proposals view;
- a command-line review flow;
- an editor showing suggested changes;
- another interface that preserves the same human capabilities.

Every interface must let the person:

1. read the exact candidate expression;
2. understand its scope or condition;
3. understand its strength;
4. see that it was proposed by an agent from the current interaction;
5. edit the wording before acceptance;
6. accept, defer, or dismiss it;
7. inspect the exact final expression if it becomes durable.

The interface should not require the person to inspect implementation metadata to discover a broader interpretation.

## Context scope

- **Scope:** one non-sensitive global preference, global boundary, or clearly conditioned preference
- **Sensitivity:** synthetic or non-sensitive
- **Audience:** only the authorized sessions described by the implementation
- **Origin:** agent-proposed from the current interaction
- **Retention:** no durable context before acceptance; exact person-approved expression after acceptance

Do not use health, identity, politics, religion, finances, relationships, employment performance, emotional state, or other sensitive claims in this first expression experiment.

Do not ask questions solely to manufacture something to remember. The proposal should arise from context the person already provided while completing a real task.

## Expression requirements

The candidate should follow the working principles in [`EXPRESSION.md`](../EXPRESSION.md):

- recognizable as the person's own;
- one meaningful claim;
- narrowest useful scope;
- appropriate strength;
- conditions and exceptions preserved;
- plain and concise;
- no inferred motive, trait, emotion, or identity;
- exact wording visible before admission.

The agent may propose operational language rather than a personality claim.

Prefer:

> By default, when reviewing code, start with the largest risk. Add detail after.

Avoid:

> The user is impatient and strongly prioritizes risk.

## Steps

1. The person begins a real, non-sensitive task with an agent.
2. During the task, they express a preference, correction, or boundary that could plausibly help in a future session.
3. The agent first uses that information to help with the current task; it does not interrupt merely to collect context.
4. At an appropriate moment, the agent proposes one exact durable expression.
5. The interface shows the expression, scope or condition, strength, audience, and origin.
6. Before the decision is finalized, the test checks whether the person can explain what would be saved and where it would apply.
7. The person accepts, edits, defers, or dismisses the proposal.
8. If edited, the interface shows the revised expression as the admission candidate.
9. If accepted, the person inspects the durable source and verifies that it matches the final expression exactly.
10. If dismissed, the person verifies that no durable context was created.
11. If accepted, the person removes the test entry and verifies that no active durable context remains.

## Evidence to collect

### Comprehension

- Could the person explain what exact statement would be kept?
- Could they explain when it would apply?
- Did they understand its strength as a preference, default, boundary, or temporary condition?
- Did they understand which agents or interfaces might receive it?

### Recognition and ownership

- Would the person say the sentence themselves?
- Did it feel like their language or like a system describing them?
- Did it preserve an important condition or exception?
- Did any word feel stronger, broader, or more certain than intended?

### Edits

Record only aggregate or redacted edit categories, such as:

- factual correction;
- scope narrowed or broadened;
- strength reduced or increased;
- condition or exception restored;
- wording made more natural;
- identity or trait language removed;
- proposal split into separate claims.

The edit itself may be more informative than whether the proposal was accepted.

### Admission integrity

- Did the accepted source match the final visible wording exactly?
- Did the implementation store additional active labels, rules, or interpretations the person could not inspect?
- Did a dismissed proposal remain inactive?
- Could the person remove an accepted test entry?

### Questions for the person

- What did you think the system was asking to remember?
- Where did you expect this to apply?
- Which word in the proposal carried the most meaning?
- Did anything sound more absolute than you intended?
- Did this feel like an instruction you own or a profile written about you?
- Would you prefer the statement in first person, as a direct instruction, or another form?
- Was the proposal useful at this moment, or did it interrupt the task?

## Success signals

- The person can accurately explain the candidate's meaning, scope, strength, and audience.
- The expression is recognized as accurate without inferred trait or identity language.
- Editing is easy and the person's revision becomes the exact canonical statement.
- Acceptance creates no hidden active interpretation beyond the visible expression and disclosed metadata.
- Dismissal creates no durable context.
- The proposal feels connected to the task rather than like a request for personal data.
- The person retains a clear way to remove the accepted test entry.

## Stop or revise signals

- The candidate describes the person from outside using traits, motives, emotions, or identity labels they did not choose.
- A task-specific statement is presented as global.
- “Prefer,” “usually,” or “by default” becomes “always” or “never.”
- Conditions or exceptions disappear during rewriting.
- Multiple unrelated claims are bundled together.
- The interface shows friendly wording while activating broader hidden rules or labels.
- The stored entry differs from the final person-approved expression.
- A dismissed proposal influences future behavior or becomes durable context.
- The agent asks unnecessary personal questions to generate a proposal.
- The proposal interrupts the task often enough to create burden or pressure.

## Sovereignty review

This experiment primarily exercises chosen durability, legibility, scope, authorship, and the distinction between context and action authority.

- **The person is the authority:** the person's edit replaces the agent's wording as the admission candidate.
- **Durability is chosen:** the proposal remains inactive before acceptance.
- **Context is legible:** the exact candidate and final expression are visible.
- **Context is scoped:** conditions and audience are shown before admission.
- **Current instruction wins:** the current conversation remains authoritative over any candidate statement.
- **Action remains separate:** no expression can grant an agent permission to take consequential action.
- **Revocation is possible:** an accepted test entry can be removed; a dismissed one does not become active.
- **Interfaces remain replaceable:** the experiment defines human capabilities rather than a required proposal card.

## Privacy and security

The public experiment design may include synthetic examples. Personal expressions, transcripts, proposal text, and edit histories are not public experiment data by default.

Implementations should minimize logging of candidate and accepted text. Any logging needed for local debugging should be disclosed, bounded, and included in cleanup.

Public findings should report aggregate or carefully redacted patterns. Do not publish raw context or infer sensitive traits from proposal edits or dismissals.

## What this experiment does not standardize

This experiment does not define:

- a context-entry or proposal schema;
- required labels for scope or strength;
- an API or tool name;
- a particular proposal card, settings page, editor, or CLI;
- a storage format or filesystem location;
- automatic proposal timing or frequency rules;
- model prompts;
- recall behavior;
- dismissal tombstones;
- provenance storage;
- conformance requirements.

## Reversibility

An implementation must be able to remove the experiment without leaving accepted test entries in an undiscoverable store.

The person should be able to keep an accepted expression in a legible form or remove it together with experiment-specific candidate text, caches, logs, and derived state covered by the implementation's cleanup promise.

## Findings

To be completed after one or more implementations run the experiment.

### Observations

Pending.

### Interpretation

Pending.

### Possible protocol implications

Pending.

### Open questions

- Is first-person language more recognizable than direct agent instructions?
- Which expression edits occur most often: scope, strength, wording, or exception?
- Does showing audience and origin improve understanding without overwhelming the person?
- How should an interface distinguish an agent proposal from an explicit “remember this” request?
- When does a concise rewrite become an unacceptable reinterpretation?
- Which expression properties should eventually be required for conformance?
