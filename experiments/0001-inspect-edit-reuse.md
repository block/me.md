# Experiment 0001: Inspect, edit, and reuse context

**Status:** Proposed  
**Protocol status:** Non-normative

## Question

Does visible, user-editable context make continuity between agent sessions feel useful and trustworthy?

## Human outcome

A person should be able to state one durable preference or boundary once, see exactly what was kept, and observe it being honored in a later session without losing the ability to correct or remove it.

## Hypothesis

Continuity will feel meaningfully user-owned when the durable source is visible and editable, the audience is understandable, and changes to the source reliably change later agent behavior.

The experiment may fail even if the agent follows the context correctly. A system can be behaviorally accurate while still feeling opaque, overreaching, or difficult to control.

## Smallest useful test

Use one or two non-sensitive, cross-context statements such as:

- "Lead with the answer."
- "Always ask before sending something as me."

The person authors or edits the statements through an interface, starts a fresh agent session, and gives the agent a task where the context is relevant. The person then changes or removes a statement and repeats the task in another fresh session.

This experiment does not include agent-inferred memory, topic recall, project context, synchronization, or cross-tool projection.

## Human capabilities

- [x] Inspect
- [x] Author
- [x] Recall
- [ ] Propose
- [ ] Decide
- [x] Explain
- [x] Revoke
- [ ] Move

`Recall` here means that a fresh agent session can use the small global context supplied by the implementation. `Revoke` is limited to changing or removing the test statements; full store disablement and deletion semantics should be tested separately.

## Interface variants

The experiment may be implemented through:

- a settings or context panel;
- a plain-text or Markdown editor;
- a command-line interface;
- an explicit chat command;
- another interface that preserves the same human capabilities.

Every interface must let the person:

1. find the durable source;
2. read the exact statements an agent may receive;
3. add, edit, and remove a statement;
4. understand the statement's scope and intended audience;
5. verify that a fresh session is using the current source rather than a stale or hidden copy.

The experiment does not require the agent to repeatedly announce that it is following stored context. Quietly honoring a preference may be the better experience. The person should still have a way to inspect what was available to the session when needed.

## Context scope

- **Scope:** global agent-working preferences and boundaries only
- **Sensitivity:** synthetic or non-sensitive
- **Audience:** only the agent sessions explicitly included in the experiment
- **Retention:** the visible source and only the implementation state required to deliver it

Do not use family, health, financial, relationship, identity, employer, or similarly sensitive context for this first experiment.

## Steps

1. The person is shown where the durable context lives and which sessions can use it.
2. They add one preference and, optionally, one boundary in their own words.
3. They inspect the resulting source and confirm that no additional statement was inferred or stored.
4. They start a fresh agent session and give it a task where the preference or boundary is relevant.
5. They note whether the agent follows the context accurately and without unnecessary narration.
6. They edit the preference or remove the boundary from the visible source.
7. They start another fresh session and repeat a comparable task.
8. They verify that the changed or removed statement no longer influences the new session.
9. They are shown how to leave the experiment and remove the test context.

## Evidence to collect

Behavioral observations:

- Could the person find and understand the durable source?
- Could they explain which sessions or agents would receive it?
- Did the fresh session follow the current statement?
- Did an edit take effect in the next fresh session?
- Did a removed statement stop influencing later sessions?
- Did any hidden, cached, or derived copy compete with the visible source?
- Did the person need to repeat themselves less?

Questions for the person:

- What did you expect the next agent to know?
- Was anything used that you did not expect?
- Did this feel like your context or like a profile the product kept about you?
- When did it feel like the agent knew you, and when did it feel like a system had stored something about you?
- After editing or removing the statement, what did you expect to happen?
- Would you put anything else here? What would you avoid putting here?

## Success signals

- The person can explain where the source of truth lives and who can use it.
- The preference reduces repeated instruction in a later session.
- Agent behavior reflects the current visible source rather than a stale copy.
- Editing and removal produce predictable changes in subsequent sessions.
- The context is applied only when relevant.
- The person describes the experience as useful continuity rather than hidden profiling.

## Stop or revise signals

- The person cannot predict which sessions receive the context.
- The agent applies the context in unrelated or inappropriate situations.
- The interface stores or derives additional context without making it visible.
- Editing the visible source does not reliably change later behavior.
- Removed context continues to influence a fresh session.
- The experiment depends on a hidden store that can override the user-owned source.
- Participants feel pressured to provide personal details in order to test the feature.

## Sovereignty review

This experiment primarily exercises authority, legibility, present-instruction precedence, revocation, and interface replaceability.

- **Inspection and correction:** the exact durable statements must be visible and editable.
- **Least necessary context:** only one or two non-sensitive global statements are used.
- **Present instruction:** what the person says in the current session must override the durable statement.
- **Reversal:** the statements and experiment-specific delivery state must be removable.
- **Action authority:** stored context cannot authorize consequential actions.
- **Source of truth:** no hidden profile, cache, or derived index may outrank the visible source.

## Privacy and security

The experiment should collect no raw personal context for public reporting. Use synthetic examples where possible.

Implementation logs should avoid recording the contents of the statements unless required for local debugging and explicitly disclosed. Public findings should contain aggregate observations or redacted patterns, never participant files or transcripts by default.

## What this experiment does not standardize

This experiment does not standardize:

- the filesystem location of context;
- Markdown or any other storage format;
- an API or tool name;
- a particular settings, chat, editor, or CLI design;
- how prompts are assembled;
- the model or agent runtime;
- topic and project scoping;
- proposal and approval flows;
- full disablement, forgetting, purge, or backup semantics;
- synchronization or cross-interface portability.

## Reversibility

An implementation must be able to remove the experiment without stranding the person's context in an unreadable format.

At the end of the experiment, the person should be able to keep the visible statements, export them in a legible form, or remove them together with experiment-specific caches and delivery state.

## Findings

To be completed after one or more implementations run the experiment.

### Observations

Pending.

### Interpretation

Pending.

### Possible protocol implications

Pending.

### Open questions

- Is a global preference-and-boundary scope understandable without introducing topic context?
- How much explanation is needed when an agent silently follows durable context?
- What proof does a person need that editing or removal reached a fresh session?
- Which parts of the experience are interface-specific, and which suggest a shared protocol rule?
