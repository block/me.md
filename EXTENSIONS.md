# Open-source boundary and candidate extensions

**Status:** Scope proposal. Non-normative.

The public project should preserve the smallest useful contract that keeps the person in control.

It should not turn every useful agent behavior into a mandatory part of `me.md`.

This document separates:

- the core human and context contract;
- candidate shared contracts that may belong in the protocol later;
- optional extensions that can remain independently implementable;
- reference workflows that demonstrate the ideas;
- application-specific details that should not become standards.

## What belongs in the public project

An idea is a strong candidate for open-source protocol work when it:

- applies across more than one agent, interface, or application;
- materially affects ownership, consent, scope, revocation, or portability;
- can be described without relying on one vendor's infrastructure;
- can be tested with synthetic fixtures and independent implementations;
- improves interoperability without forcing every implementation to reproduce one product;
- makes hidden behavior more inspectable or controllable by the person.

A useful feature is not automatically a protocol feature.

## Layer 1: the core protocol

The core should remain narrow.

The public project currently includes or is actively testing:

- the [sovereignty contract](./SOVEREIGNTY.md);
- shared [context scopes and lifecycle language](./CONTEXT.md);
- [expression and admission](./EXPRESSION.md);
- visible, user-governed canonical context;
- proposals that remain inactive until admitted;
- current instruction taking precedence over durable defaults;
- the separation of context from action authority;
- meaningful correction, disablement, forgetting, deletion, and projection;
- an [experiment discipline](./EXPERIMENTS.md) that keeps implementations from becoming standards by accident.

These are the constitutional and semantic center of the work.

## Layer 2: next candidate contracts

These ideas are broadly reusable and important to sovereignty, but need focused experiments before becoming normative.

### Provenance contract

A person should be able to understand:

- what changed;
- who or what changed it;
- why the change was allowed;
- when it happened;
- what proposal, import, or direct instruction it came from.

The protocol should define the human questions provenance must answer before choosing Git, JSONL, SQLite, an event log, or another mechanism.

### Capability and action contract

An implementation should expose what an agent may:

- read;
- propose;
- draft;
- modify locally;
- publish or send;
- delete or otherwise affect externally.

Context may restrict capabilities but must not grant new ones. Consequential authorization should be bound to a specific operation, destination, and payload.

A future machine-readable capability manifest is a strong candidate for shared work.

### Portability manifest

A person should be able to inspect which state is:

- portable and user-owned;
- private but local to one implementation;
- derived and rebuildable;
- local-only by design;
- excluded from export;
- projected into another surface.

A future portability manifest should describe state classes and boundaries without requiring a particular storage layout.

### Coverage and explanation receipts

When an agent uses context or external sources, the person should be able to understand material gaps:

- what context was available;
- what was actually recalled;
- which sources were checked;
- what was partial, stale, or unavailable;
- what was inferred rather than verified.

This should support trust without forcing the agent to narrate every ordinary preference it follows.

## Layer 3: optional public extensions

These can be valuable and interoperable without being required for every `me.md` implementation.

### Outcome and feedback events

A small event vocabulary could record ground truth such as:

- acted;
- dismissed;
- deferred;
- corrected;
- useful;
- noisy;
- too much;
- not me.

Events help applications evaluate recommendations and avoid repeated mistakes. They are not automatically facts about the person.

A public extension should define retention, scope, and whether event contents are portable or local-private.

### Intents and watches

A watch can be represented as an explicit monitoring intent:

- target or state to observe;
- authorized source;
- trigger condition;
- desired notification or draft behavior;
- expiration or stop condition.

This is user-owned intent, not inferred memory. It should be inspectable, editable, and removable.

### Reflection and pattern proposals

Applications may review events and run history for repeated patterns.

The sovereign boundary is:

```text
observed pattern → candidate expression → person decides
```

Reflection may propose an ignore rule, preference, or changed priority. It should not silently admit one.

### Orientation artifacts

An application may produce a brief, home view, meeting prep, or another orientation artifact from current evidence and context.

A generic artifact contract might eventually cover:

- source coverage;
- observations versus interpretations;
- urgency without false precision;
- one recommended next move;
- links back to evidence;
- outcome feedback.

The exact briefing format and ranking logic should remain reference behavior.

### Presentation and tone

Tone is part of the person's experience of agency.

Applications may offer expressive voices, moods, metaphors, or terse factual modes. The reusable principle is that tone should:

- never decorate uncertainty, coverage gaps, or serious warnings in a misleading way;
- remain grounded in true system state;
- be optional and replaceable;
- provide a plain mode;
- avoid using personality to soften consent or consequential-action moments.

A specific character or voice is not part of the protocol.

### Persona or avatar projection

A person may choose to generate a portable agent persona or style projection from accepted context.

This is a high-risk extension because a projection can appear to stand in for the person. It should be deliberate, inspectable, scoped, and revocable. It must not be produced automatically from inferred context.

The canonical context remains distinct from any avatar generated from it.

## Layer 4: reference workflows

The public project may eventually include synthetic reference workflows demonstrating the protocol. These are examples, not compatibility requirements.

Good candidates include:

- preparing for a meeting from authorized calendar, document, and project context;
- surfacing a time-sensitive obligation with an honest coverage line;
- suggesting an audience for a draft without notifying anyone automatically;
- identifying a decision that appears stalled or work that lacks an owner;
- helping someone notice their own work has gone unseen;
- showing why one recommendation outranked another;
- using explicit outcome feedback to stop repeating a cleared suggestion;
- promoting a repeated project pattern into a proposed personal default.

Each reference workflow should document:

- required capabilities and sources;
- what remains local or ephemeral;
- what the user must authorize;
- what is observation, interpretation, recommendation, or action;
- how the workflow fails safely under partial coverage.

## Layer 5: application-specific choices

These may be open-source implementation code, but they should not define the protocol:

- specific source providers and connector commands;
- named agent collections and personalities;
- exact onboarding scripts;
- numerical ranking formulas and thresholds;
- collaboration-graph weighting;
- exact urgency labels;
- product-specific settings screens;
- CLI command names;
- background schedules and daemons;
- exact file locations before experiments support them;
- organization-specific concepts, datasets, or fixtures.

Independent implementations should be free to make different choices while preserving the human contract.

## Mapping application ideas to the public cut

| Application idea | Public abstraction | Recommended disposition |
| --- | --- | --- |
| User-entered local memory | Canonical durable context and direct authorship | **Core**; exact command and JSONL path are reference details |
| Approved learned memory | Proposal, admission, recall policy, and provenance | **Core principles**; multi-key recall gates remain an experiment or reference policy |
| Outcome feedback such as acted, dismissed, or deferred | Outcome-event vocabulary | **Optional public extension** |
| “Useful,” “noise,” “too much,” or “not me” corrections | Feedback-event vocabulary | **Optional public extension** |
| Meeting preparation | Source-backed orientation workflow | **Reference workflow** |
| Human-readable urgency | Presentation and ranking guidance | **Reference behavior**, not a core protocol rule |
| Expressive briefing voice | User-controlled presentation layer | **Optional guidance**; specific voice stays implementation-specific |
| Drift, ownership, and visibility signals | Detector heuristics over external evidence | **Reference workflows** |
| Audience suggestions | Suggestion workflow plus action boundary | **Reference workflow**; never automatic notification authority |
| Central capability gate | Capability and action manifest | **Next protocol candidate** |
| Time-sensitive calendar leads | Time-aware orientation heuristic | **Reference workflow** |
| Persistent watches | Explicit intent and trigger model | **Optional public extension** |
| Recursive reflection | Pattern detection that produces proposals | **Optional public extension** |
| Onboarding priorities and things to ignore | Declared intent and preference context | **Optional extension**; ranking implementation remains local |
| Calibration mirror | Inspectable run-scoped interpretation | **Interface experiment**; sensitive inferred dimensions require strong restraint |
| Portability inspection | Machine-readable state-class manifest | **Next protocol candidate** |
| Daily run memory | Run artifact and outcome history | **Optional orientation extension**, not personal context by default |
| Recurring patterns | Derived candidates requiring admission | **Optional reflection extension** |
| Avatar or style projection | Deliberate non-canonical projection | **High-risk optional extension** |

## What is still missing from the public protocol

The current public work establishes the human contract, context language, expression, and experiment discipline. Important missing pieces include:

1. **Provenance:** a technology-neutral contract for explaining mutations.
2. **Capabilities:** a machine-readable separation between context access and action authority.
3. **Portability:** an inspectable manifest of portable, local-private, derived, projected, and excluded state.
4. **Coverage:** a way to communicate what context and evidence were actually available.
5. **Revocation tests:** active-session disablement, forgetting, deletion, and projection cleanup.
6. **Derived-state limits:** tests proving caches, indexes, and patterns cannot restore or outrank forgotten context.
7. **Event and intent boundaries:** shared language for feedback, outcomes, priorities, and watches without treating them as identity.
8. **Security model:** path safety, prompt injection, connector isolation, local permissions, and cross-interface trust.
9. **Conformance:** synthetic tests that verify the contract without requiring one application's architecture.

These should be developed in focused PRs and experiments rather than added as one large specification.

## Recommended sequence

A careful public sequence would be:

1. System map and open-source boundary.
2. Provenance contract and experiment.
3. Capability and action contract.
4. Portability manifest experiment.
5. Revocation and deletion experiment.
6. Outcome-event extension.
7. Intent and watch extension.
8. Coverage and explanation receipts.
9. Synthetic conformance tests.
10. Reference workflows and implementations.

The sequence keeps the sovereignty boundary ahead of application intelligence.

## What must never enter the public cut

Do not publish:

- real personal context or participant transcripts;
- private source data or production credentials;
- internal infrastructure, endpoints, or operational instructions;
- proprietary fixtures or organization-specific relationship graphs;
- hidden prompts that contain confidential information;
- claims that one product's implementation is the protocol;
- personal data collected merely because it is available.

Open source should make the architecture more inspectable without making people or organizations more exposed.
