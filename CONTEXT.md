# Context model and shared language

**Status:** Working vocabulary and protocol hypothesis. Non-normative.

This document gives the project a shared way to talk about personal context while the storage format, APIs, and interfaces remain under test.

The words matter. When every kind of state is called “memory,” it becomes easy to blur the difference between what a person said, what an agent inferred, what belongs to a project, and what an implementation cached for convenience.

## Core terms

### Person

The human authority over their context.

An agent may use context to be more helpful. It does not get to define the person or become the final authority on what is true about them.

### Agent

A system that interprets context while helping with a task.

An agent is a consumer of the protocol, not the owner of it.

### Interface

The surface through which a person inspects, authors, corrects, or uses context. It may be a settings panel, text editor, command line, chat interaction, or something else.

Interfaces are replaceable. The protocol should not depend on one interface remaining available.

### Context

Information intentionally made available to help an agent understand the current task, the surrounding situation, or how to work with the person.

Context is the broad term. It includes current instructions and durable context, but not every observation, transcript, cache, or model inference.

### Current context

Information supplied for the present session or task.

Current context is temporary unless the person authors it into durable context or accepts a proposal to keep it. What the person says now takes precedence over durable defaults.

### Durable context

Context intentionally retained for use beyond the current session.

Durable context must have a legible source of truth and a clear scope. It may be authored directly by the person, explicitly recorded at their request, imported with their knowledge, or admitted after they accept a proposal.

### Memory

A common user-facing word for durable context intended for future reuse.

Protocol discussions prefer **durable context** because “memory” can imply hidden, automatic, or agent-owned state. An interface may use the word memory, but the underlying context should remain inspectable, scoped, and governed by the person.

### Context entry

A human-understandable unit of durable context that can be inspected and corrected.

An entry might be a sentence, bullet, field, or paragraph. This term does not require a particular schema or storage format.

### Source of truth

The canonical, user-governed representation of durable context.

An implementation may create indexes, embeddings, summaries, or caches, but those derived forms must remain subordinate to the source of truth and must not silently preserve a competing profile.

### Derived state

Implementation-generated state used for routing, search, performance, or presentation.

Examples include indexes, embeddings, caches, summaries, and topic classifiers. Derived state is not automatically durable context. It should be rebuildable, inspectable at the level needed to understand its effect, and included in revocation and deletion semantics.

## Context scopes

Scope answers three questions:

1. **When is this context relevant?**
2. **Which agents or interfaces may use it?**
3. **For what purpose may it be used?**

Scope is not just a folder name. It is a boundary around use and audience.

### Session context

Context for the current conversation or task only.

Example:

> “For this answer, walk me through the reasoning instead of leading with the conclusion.”

Session context should not become durable merely because an agent observed it.

### Global context

A small set of cross-context preferences, defaults, and boundaries that may help across many authorized sessions.

Examples:

- Lead with the answer.
- Use plain language before specialized terminology.
- Always ask before sending something as me.

Global does **not** mean public or available to every agent. It means broadly relevant within the audience the person has authorized.

Global context should stay sparse. Personal facts that are relevant only in one area of life should usually have a narrower scope.

### Topic context

Focused personal context for one area of life or recurring concern.

Examples might include family logistics, travel preferences, communication style, or accessibility needs.

Topic context should be recalled only when relevant. Topic names and descriptions can themselves reveal sensitive information, so an implementation should avoid exposing the complete topic index when a narrower routing method will work.

### Project context

Context about a piece of work, not a claim about the person.

Examples:

- The rollout must be reversible.
- The project uses PostgreSQL.
- The next decision concerns dual writes.

Project context should follow the project. It must not silently become personal context because the same person worked on it.

A repeated pattern across projects may justify a proposal to create personal context. Repetition alone does not admit it.

## Origin and provenance

A context system should preserve how durable context came to exist.

Useful origin categories include:

- **User-authored** — the person wrote or edited it directly.
- **Explicitly recorded** — the person directly asked an agent or interface to keep it.
- **Agent-proposed** — an agent suggested it and the person accepted or revised it.
- **Imported** — the person knowingly brought it from another source.
- **Derived** — the implementation generated it for routing, search, or presentation; it is not the canonical statement about the person.

Provenance should make it possible to answer:

- What changed?
- Who or what changed it?
- Why was the change allowed?
- When did it happen?
- What source or proposal did it come from?

The protocol does not yet require Git, a ledger, a database, or any other provenance storage mechanism.

## Proposals and decisions

An observation is not durable context.

When an agent notices something that might be useful later, the safe lifecycle is:

```text
observation → proposal → person’s decision → durable context
```

A proposal should be visible as a proposal. It must not influence future sessions before acceptance.

The person may:

- **Accept** it as written.
- **Revise** the wording, scope, or audience before accepting it.
- **Defer** the decision.
- **Dismiss** it without creating durable context.

A person who directly authors context or explicitly says “remember this” should not be asked to approve the same instruction a second time. That is different from an agent inferring something and proposing it.

## Recall, routing, and explanation

### Recall

Selecting durable context for use in the current task.

Recall should use the least context needed. It is not permission to bulk-load every topic or expose the person’s full context map to every agent.

### Routing

Choosing which scope or entries may be relevant before recall.

Routing may use filenames, metadata, rules, local models, or indexes. Those are implementation choices. Whatever the mechanism, it must not become a hidden authority or reveal more personal context than the task requires.

### Explanation

Making it possible for the person to understand what durable context influenced an outcome and where it came from.

Explanation does not require an agent to narrate every preference it follows. Quietly honoring context may be the better experience. The person should still have a way to inspect what was available and used when that matters.

## Precedence and conflicts

Durable context provides defaults. It does not control the present conversation.

A useful working order is:

1. Current explicit instruction from the person.
2. Relevant durable context from the narrowest applicable scope.
3. Broader durable defaults.
4. Derived suggestions or agent inference.

Platform safety and capability constraints remain separate from this context order.

More specific context may refine a broader preference:

- Global: “Keep explanations concise.”
- Project: “Migration plans must include rollback detail.”

The project context can require more detail for that project.

More specific context must not silently weaken a broader boundary or grant action authority:

- Global boundary: “Ask before sending something as me.”
- Project note: “Send weekly updates automatically.”

The project note cannot create permission to send. Action authorization remains separate.

When context conflicts and the correct interpretation is not clear, the implementation should ask or choose the safer, less expansive behavior rather than guessing.

## Revocation language

These actions are related but not interchangeable.

### Disable

Stop using a context store or scope while retaining it.

Disablement should be enforced by the context-access layer, not only by a prompt asking an agent to ignore the data.

### Forget

Remove context from active durable state and future recall.

An implementation may retain a minimal decision record to avoid repeating a dismissed proposal, but any retained state and its lifetime must be disclosed.

### Delete

Remove specified context and the copies covered by the deletion request.

Deletion semantics should explicitly address derived indexes, caches, history, backups, proposals, and projections. “Delete all” should not mean “hide the current file while retaining usable copies elsewhere.”

### Revoke

The broader human capability to withdraw access or influence through disablement, forgetting, deletion, or removal of an authorized audience.

## Projection, export, and synchronization

These operations all move or reproduce context, but they create different risks.

### Projection

A rendered or copied subset of context placed into another tool or instruction surface.

A projection is not the source of truth. Creating one should be deliberate, limited in scope, and reversible.

### Export

A portable copy a person can inspect and move elsewhere.

An export should not silently include derived state, dismissed proposals, sensitive scopes, or historical copies that the person did not expect.

### Synchronization

Keeping context aligned across devices or stores.

Synchronization expands the number of copies and systems involved. It therefore needs clear conflict, revocation, deletion, and trust semantics.

Portability should expand the person’s choices, not the audience by default.

## Examples

| Statement or state | Scope or type | Durable? |
| --- | --- | --- |
| “Lead with the answer.” | Global context | Yes, when authored or accepted |
| “My child has soccer on Mondays.” | Family topic context | Yes, when authored or accepted |
| “This rollout must be reversible.” | Project context | Yes, within that project |
| “Explain this one step by step today.” | Session context | No, unless explicitly kept |
| An agent notices repeated requests for tables | Observation or proposal | Not until accepted |
| A vector index of topic files | Derived state | No; subordinate to the source of truth |
| A copy rendered into another agent’s instruction file | Projection | No; non-canonical copy |

## What this document does not standardize

This document does not yet define:

- a filesystem location;
- Markdown or another canonical representation;
- a schema for entries, scopes, or proposals;
- API or tool names;
- topic identifiers or routing algorithms;
- provenance storage;
- encryption, synchronization, or backup mechanisms;
- user-interface language;
- conformance requirements.

Those choices should be informed by experiments and independent implementations.

## Questions still under test

- Are global, topic, project, and session scopes sufficient?
- How should an implementation route context without revealing a sensitive topic index?
- What is the smallest useful unit of provenance?
- When should a repeated project pattern become a personal-context proposal?
- What should forgetting retain, if anything, to respect “do not ask again”?
- How should deletion interact with history and backups?
- What explanation is useful without making agents narrate every use of context?
- Which parts of this model need shared conformance rules, and which should remain implementation-specific?
