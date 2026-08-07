# Experiment 0004: Understand and revoke agent authority

**Status:** Proposed  
**Protocol status:** Non-normative

## Question

Can a person understand what one agent may read, propose, draft, and execute—and can they revoke that authority predictably, including in an active session?

## Human outcome

A person should be able to distinguish:

- context access from context mutation;
- proposal from admission;
- draft from external action;
- standing access from one-time transaction authorization;
- disabled from deleted.

They should be able to revoke access and observe enforcement rather than relying on the agent to behave voluntarily.

## Hypothesis

A small, purpose-limited capability view will increase control without creating permission fatigue when it uses human terms, shows only material distinctions, and binds consequential authorization to an exact preview.

## Smallest useful test

Use one synthetic agent with:

- standing access to one non-sensitive global context entry;
- permission to propose context but not admit it;
- permission to draft a message but not send it automatically;
- a simulated send capability requiring exact transaction authorization.

During the experiment, the person revokes context access while the session is active and verifies that recall and proposal operations fail. They then approve one simulated message preview and verify that changing the recipient or payload invalidates the authorization.

No real message is sent.

## Human capabilities

- [x] Inspect
- [ ] Author
- [x] Recall
- [x] Propose
- [x] Decide
- [x] Explain
- [x] Revoke
- [ ] Move

## Interface variants

The experiment may use:

- a capability panel;
- a settings view;
- a command-line manifest;
- an in-context authorization preview;
- another interface preserving the same human capabilities.

The person must be able to see the effective capability, not only a list of installed tools.

## Context and action scope

- **Context:** one synthetic or non-sensitive global entry
- **Agent:** one test agent with a clear purpose
- **External action:** simulated message send only
- **Recipient and payload:** synthetic
- **Retention:** capability decisions, simulated receipts, and minimal experiment state

## Steps

1. Show the person what the test agent may read, propose, draft, and execute.
2. Ask them to predict whether the agent can directly edit context or send a message.
3. Let the agent recall the authorized context entry.
4. Let the agent make a proposal; verify that the proposal remains inactive.
5. While the session remains active, the person revokes context access.
6. Attempt recall and proposal again; both should fail at the access layer.
7. The agent drafts a synthetic message to a synthetic recipient.
8. Show the exact recipient and payload and ask the person to authorize that simulated transaction.
9. Change the recipient or payload before execution; verify the prior authorization no longer matches.
10. Restore the exact preview, authorize it, and execute only the simulation.
11. Show a receipt distinguishing attempted, authorized, and simulated-success states.
12. Remove the standing grant and verify the effective capability view changes.

## Evidence to collect

- Can the person explain what the agent may read?
- Can they distinguish proposal from direct mutation?
- Can they distinguish draft from send?
- Do they understand what persists after access is disabled?
- Does revocation affect an active session?
- Which fields do they expect an action confirmation to bind?
- Do they assume one approval can be reused?
- Does the capability view feel clear or bureaucratic?
- Does a denial explain the boundary without suggesting a bypass?

## Success signals

- The person predicts the agent’s effective authority accurately.
- Context access and action authority remain visibly separate.
- Active-session recall fails after revocation.
- Proposals cannot admit themselves.
- Drafting creates no external effect.
- A changed recipient or payload invalidates prior authorization.
- The simulated action produces a clear receipt.
- Unknown or unlisted capabilities are denied.

## Stop or revise signals

- The person equates tool presence with authorization.
- Revocation changes a prompt but leaves a working access path.
- Generic filesystem or shell access bypasses the context mutation boundary.
- A project note or imported document grants capability.
- One approval authorizes materially different or repeated actions.
- The interface hides the effective actor, resource, purpose, or duration.
- The capability model creates so much friction that people approve without reading.

## Sovereignty review

- **Authority:** the person grants and revokes bounded capabilities.
- **Scope:** one agent receives only the context needed for its stated purpose.
- **Action separation:** context and drafting do not grant execution authority.
- **Revocation:** enforcement occurs outside the model and affects active sessions.
- **Legibility:** the effective capability is shown in human terms.
- **Security:** untrusted content cannot alter the grant or transaction authorization.

## Privacy and security

Use only synthetic context, recipient, and message content. No external action should occur.

Public findings should contain aggregate comprehension and friction patterns, not raw capability records, actor identifiers, or interaction transcripts.

## What this experiment does not standardize

This experiment does not define:

- a capability schema or vocabulary;
- a permission UI;
- risk tiers;
- authentication or credential storage;
- transaction-signing technology;
- external action APIs;
- operating-system sandboxing;
- conformance requirements.

## Reversibility

Remove the test agent grants, authorization records, receipts, caches, and simulated action state. The experiment must not leave a real external effect or standing authority behind.

## Findings

To be completed after one or more implementations run the experiment.

### Observations

Pending.

### Interpretation

Pending.

### Possible protocol implications

Pending.

### Open questions

- Which capability distinctions are meaningful to people?
- How should active sessions receive revocation?
- When is standing authorization appropriate?
- What transaction fields must be immutable after approval?
- How do we avoid permission fatigue without broad grants?
