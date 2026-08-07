# The me.md sovereignty contract

`me.md` is experimental. Its storage layout, APIs, and implementation details will change as we learn.

These commitments are different. They are the conditions under which a personal context system remains meaningfully user-owned. An implementation should be able to explain how it preserves them before claiming compatibility with `me.md`.

## The person is the authority

Stored context may help an agent understand a person. It does not define the person.

The person must be able to inspect, correct, reject, override, disable, forget, and delete their context. An inferred profile must never outrank what the person explicitly says about themselves.

## Durability is chosen

Something an agent observes is not automatically memory.

Agent-inferred context must remain a proposal until the person accepts it. Context the person writes directly, or explicitly asks to record, may be saved without asking them to approve the same instruction twice.

Implementations should preserve the difference between user-authored, agent-proposed, imported, and derived context.

## Context is legible

A person should be able to understand what is stored about them without reverse-engineering an embedding, score, or behavioral model.

Derived representations may support search or routing, but they must not become a hidden competing source of truth. When it matters, the person should be able to understand what context was used and where it came from.

## Context is scoped

An implementation should use the least context needed for the current task.

Global, topic, and project context are different scopes. Information must not silently move from a narrower scope to a broader one. The existence and names of sensitive topics can themselves reveal personal information, so scoping applies to metadata as well as contents.

## What the person says now wins

Current instructions take precedence over durable defaults.

Stored context provides continuity. It is not authority over the present conversation.

## Context is not permission to act

Knowing a person's preferences does not authorize an agent to send, publish, purchase, approve, disclose, or otherwise act on their behalf.

Stored context may narrow what an agent is allowed to do—for example, by recording a boundary—but it must not grant new powers. Consequential actions require their own explicit authorization.

## Revocation is real

Turning context off must stop its use at the enforcement layer, not merely ask the agent to ignore it.

Forgetting must remove context from active recall. Deletion must have a clear meaning, including how history, indexes, caches, proposals, backups, and projections are handled. An implementation must not describe something as deleted while continuing to use a retained copy.

## Portability does not mean universal sharing

A person may carry context between trusted applications without sharing every part of it with every agent.

Exporting, synchronizing, or projecting context into another tool is a separate, deliberate operation. Portability should expand the person's choices, not expand the audience by default.

## Personal context is not organizational telemetry

The protocol must not become a hidden productivity score, performance profile, manager dashboard, employee-risk system, or mechanism for organizational surveillance.

Context about other people should be minimized and scoped to the person's legitimate use. Access to a conversation does not automatically justify retaining durable claims about everyone in it.

## Interfaces are replaceable

No agent or application should become the sole owner or interpreter of the person's context.

A person should be able to change interfaces without losing continuity or control. Implementation-specific indexes and caches must remain subordinate to the user-owned source of truth.

## What remains under test

The project is currently testing, rather than standardizing:

- whether `~/.me/` is the right default location;
- whether Markdown is the right primary representation;
- the exact relationship between global, topic, and project context;
- proposal, approval, correction, and dismissal experiences;
- provenance, history, and undo storage;
- local topic routing and indexing;
- protection of context at rest and in transit;
- synchronization between devices;
- export and interoperability formats;
- the minimum useful conformance surface.

## How we evaluate experiments

For each experiment, we should ask:

- Did this reduce the person's burden?
- Could the person predict what context would be used?
- Could they inspect and correct it?
- Did disabling, forgetting, and deletion work as expected?
- Did the system retrieve or expose more context than the task required?
- Did an implementation convenience silently widen scope, access, or authority?
- Could another implementation preserve the same human contract?
- What evidence would make us reverse the decision?

An implementation is evidence for the protocol. It is not automatically the protocol.
