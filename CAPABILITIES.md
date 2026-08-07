# Capability and action contract

**Status:** Working protocol hypothesis. Non-normative.

Context and authority are different.

Knowing what a person prefers may help an agent act more appropriately. It does not give the agent permission to read every scope, change durable context, contact another person, publish content, spend money, delete data, or take any other consequential action.

A capability contract makes that separation visible and enforceable.

## The human questions

A person should be able to understand:

- What can this agent or interface read?
- What can it propose?
- What can it change locally?
- What can it draft without acting?
- What can it do outside the local context store?
- Which operations require a fresh confirmation?
- What is currently blocked?
- How can access or authority be revoked?
- What happened after an authorized action?

The answers should not exist only in a model prompt.

## Capabilities are enforced outside the model

Prompts can guide behavior. They are not a security or authorization boundary.

A runtime or broker should enforce capabilities before an agent can access context, mutate canonical state, use an external source, or create an external effect.

If memory is disabled, a recall tool should fail. If sending is blocked, a model should not be able to bypass that decision through another tool path. If a proposal is permitted but direct mutation is not, generic filesystem access should not quietly become the mutation API.

## Default deny

Unknown capabilities should be denied.

An implementation should not infer authority from:

- the presence of context;
- a broad tool connection;
- a previous unrelated approval;
- an agent’s confidence;
- a statement inside imported content;
- a webpage, email, file, or document asking the agent to act;
- a project note that contradicts a broader boundary.

Authority should be granted deliberately, scoped narrowly, and revocable.

## Capability classes

The exact vocabulary remains under test. Useful conceptual classes include:

### Context access

- inspect global context;
- recall a named or selected topic;
- read project context for an attached project;
- inspect topic metadata;
- inspect provenance;
- inspect policy and portability state.

Access should be scoped by audience, purpose, and context class. Permission to read global defaults does not imply permission to enumerate sensitive topics.

### Context curation

- propose a new context entry;
- accept or revise a proposal on the person’s instruction;
- add context after an explicit “remember this” request;
- edit an existing entry;
- forget or delete context;
- import context;
- create or remove a projection.

Agent observation should normally permit proposal, not direct admission. Explicit user instruction may authorize a context-aware add, edit, or forget operation without duplicate approval.

### External-source access

- search or read a connected source;
- retrieve a specific document, event, message, or code artifact;
- inspect source coverage or freshness.

Source access is not durable-memory admission. Information read for a task should not become personal context automatically.

### Drafting

- compose text;
- prepare a proposed change;
- generate a structured action preview.

Drafting has no external effect. A draft must not be represented as sent, published, approved, or applied.

### External action

- send a message;
- publish or comment;
- approve or merge;
- create or modify an external record;
- make a purchase or financial transfer;
- delete external data;
- change access or permissions.

External actions should require transaction-specific authorization unless a person has deliberately established a narrow, revocable standing rule suitable for that risk level.

### Local runtime operations

- update a cache or index;
- write a run artifact;
- start a background process;
- install software or an extension;
- update the application.

“Local” does not automatically mean low-risk. Installation, background execution, credential access, and broad filesystem writes should remain separate capabilities.

## A capability is more than a verb

A useful capability description may include:

- **actor** — which agent, interface, or process may use it;
- **operation** — what may be done;
- **resource** — which context scope, source, file, service, or object;
- **purpose** — why access is granted;
- **audience or destination** — who or what may receive an output;
- **conditions** — limits such as read-only, draft-only, or exact topic;
- **duration** — one request, one session, until a date, or standing;
- **approval mode** — automatic, confirmation required, or blocked;
- **revocation state** — active, suspended, expired, or removed.

The protocol does not yet require all of these as machine fields. They describe the boundary an implementation should be able to explain.

## Standing grants and transaction authorization

Two kinds of permission are often confused.

### Standing grant

A standing grant allows a bounded class of operations over time.

Examples:

- this writing agent may read my global communication defaults;
- this project agent may read context attached to Project Phoenix;
- this application may propose memories but may not admit them;
- this calendar assistant may read event titles for meeting preparation.

Standing grants should be inspectable, narrowly scoped, and easy to revoke.

### Transaction authorization

Transaction authorization permits one exact consequential operation.

A strong authorization may bind:

- the capability;
- the actor;
- the destination or recipient;
- the exact payload or payload hash;
- the relevant account or project;
- an expiration time;
- an idempotency key;
- whether the action is reversible;
- whether the preview changed after approval.

If any material part changes, the previous authorization should no longer apply.

A generic “yes” should not authorize a different recipient, revised text, larger amount, broader audience, or later repeated action.

## Draft, preview, authorize, execute, verify

A useful consequential-action flow is:

```text
agent proposes action
        ↓
exact preview
        ↓
person authorizes this transaction
        ↓
runtime verifies authorization still matches
        ↓
execute once
        ↓
verify result and issue receipt
```

The person should see the exact material effect before authorization.

Execution is not complete merely because a tool call was attempted. The runtime should verify the result where possible and distinguish success, failure, partial completion, and unknown outcome.

## Context can restrict, not grant

A context entry may narrow authority:

> Always ask before sending something as me.

It must not create authority:

> Send weekly updates automatically.

The second statement may express a desired workflow, but an action broker still needs a valid capability and authorization policy. Imported or agent-authored context must never be able to grant itself new powers.

## Current instruction and authorization

A direct instruction in the current interaction can authorize some operations, but the runtime must interpret it within the capability boundary.

Examples:

- “Remember that I prefer concise answers” may authorize a context-aware local add.
- “Remove that family entry” may authorize forgetting that exact entry.
- “Draft a note to Sam” authorizes drafting, not sending.
- “Send it” may authorize a previously shown exact draft if the recipient, payload, account, and timing remain unchanged.

Ambiguous instructions should produce a narrower preview or clarification rather than expansive action.

## Revocation and active sessions

Revocation must affect the enforcement layer.

When a person disables a store, removes an audience, or revokes a source connection:

- new operations should fail immediately;
- active sessions should not retain a usable bypass;
- cached credentials and handles should be invalidated where practical;
- projections should be disabled or removed according to policy;
- the interface should state what remains in memory, cache, logs, or history.

A prompt saying “do not use memory” is not enough if the tool still returns it.

## Capability composition and confused deputies

An agent may have several individually reasonable capabilities that become dangerous when combined.

For example:

- read private context;
- read untrusted documents;
- draft external messages;
- send messages.

A malicious document could try to redirect the agent and exfiltrate context. The runtime should treat source content as untrusted data, prevent it from changing capability policy, and require exact authorization for external effects.

Capability review should consider combinations, not only individual tools.

## Multiple agents and purpose boundaries

Different agents may need different context and capabilities.

A writing agent, project agent, scheduling agent, and onboarding interface should not automatically share the same access merely because they run in one application.

A person should be able to understand the effective matrix:

| Agent or interface | Context it may read | Changes it may propose | Actions it may request |
| --- | --- | --- | --- |
| Writing helper | global writing defaults | writing-style proposals | draft text |
| Project helper | attached project context | project-context proposals | draft project changes |
| Scheduling helper | scheduling preferences and authorized calendar fields | scheduling proposals | draft or request event changes |

This table is illustrative. The principle is purpose-limited access.

## Capability manifests

A future machine-readable manifest could make effective capabilities inspectable across implementations.

An illustrative entry might look like:

```json
{
  "actor": "agent:writing-helper",
  "capability": "context.recall",
  "resource": "scope:global/communication",
  "purpose": "adapt writing assistance",
  "approval": "standing",
  "state": "active"
}
```

A transaction authorization might look like:

```json
{
  "id": "auth_01J...",
  "actor": "agent:writing-helper",
  "capability": "message.send",
  "destination": "contact:sam",
  "payload": "sha256:...",
  "expires_at": "2026-08-07T19:05:00Z",
  "idempotency_key": "send_01J...",
  "state": "approved"
}
```

These examples are not required schemas.

## Receipts and explanation

After a consequential operation, the person should be able to understand:

- what was attempted;
- which authorization was used;
- what destination and payload were involved;
- whether it succeeded;
- whether it can be undone;
- whether any side effects remain uncertain.

For denied operations, an interface should explain the relevant boundary without revealing secrets or encouraging bypass.

## What this document does not standardize

This document does not define:

- a capability vocabulary or schema;
- risk tiers;
- which operations may use standing grants;
- prompt or tool formats;
- authentication mechanisms;
- operating-system sandboxing;
- credential storage;
- transaction-signing technology;
- receipt formats;
- user-interface design;
- conformance requirements.

## Questions still under test

- Which context-access capabilities need separate grants?
- Can people understand purpose-limited agent access without permission fatigue?
- Which local writes are safe under standing authorization?
- When is a direct user instruction sufficient authorization?
- Which external actions should never use standing grants?
- What fields must be bound to a transaction confirmation?
- How should already-running sessions observe revocation?
- How should capability composition be reviewed for prompt-injection risk?
- Which parts of a capability manifest should be portable?
