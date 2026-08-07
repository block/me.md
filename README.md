# me.md

**Your context should belong to you.**

Organizations are replacing coordination layers with intelligence systems. A world model can know the state of the organization, but it does not automatically know the state of the person. Without a personal layer, intelligence routes around the human instead of through them.

`me.md` gives the person a portable model of themselves — identity, aims, sources, workstreams, people, watches, memory policy, and operating rules — so that intelligence routes through them. It turns raw organizational activity into a person-shaped read: what moved, where the pull is, what is missing, and what to do next.

## Why this should exist

People already carry context from one relationship to another. We remember how someone likes to communicate, what they care about, and what boundaries matter.

Agents need some of that continuity too. But continuity becomes dangerous when context is inferred silently, stored opaquely, or shared more broadly than the person intended.

`me.md` is an attempt to hold both sides of that tension:

- enough continuity that every new agent does not feel like starting from zero;
- enough control that continuity does not become surveillance.

## Personal sovereignty

Sovereignty is the foundation of the protocol, not an optional privacy setting.

The full [sovereignty contract](./SOVEREIGNTY.md) separates the commitments this project intends to preserve from the technical choices still under test.

A conforming implementation should preserve these principles:

- **It is off until you turn it on.** Durable personal context is opt-in. A conforming implementation must work without it and must make enabling it a deliberate, reversible choice.
- **You own the source of truth.** Your context does not belong to an agent, application, model provider, or employer.
- **You can see it.** Stored context should be legible and inspectable, not hidden behind an inferred profile.
- **You choose what becomes durable.** An agent may suggest something worth remembering, but an observation is not automatically a fact about you.
- **Context stays scoped.** Family context should not appear in an unrelated coding session. Project facts should not quietly become personal identity.
- **What you say now wins.** Current instructions override stored defaults.
- **You can change your mind.** Context can be corrected, disabled, forgotten, or deleted.
- **Action remains separate.** Knowing your preferences is not permission to send, publish, purchase, or act on your behalf.
- **Interfaces are replaceable.** You should be able to change agents or applications without surrendering continuity.

The protocol is the stable center. Agents and applications are replaceable surfaces around it.

## A working shape

The exact structure is still being designed. An early shape looks like this:

```text
~/.me/
  me.md
  topics/
    family.md
    travel.md
    communication.md
  projects/
    <project-id>/
      project.md
  proposals/
  policy.json
```

Not every part of the personal model is specified yet. Aims, workstreams, people, and watches — the pieces that power the person-shaped read of what moved and where the pull is — are planned shape, tracked as candidate contracts in the [open-source boundary](./EXTENSIONS.md).

The [context model and shared language](./CONTEXT.md) explains the boundaries between session, global, topic, project, proposed, and derived context without treating this folder layout as final.

The [expression and admission guide](./EXPRESSION.md) explores how durable context can be phrased in language the person recognizes as theirs while keeping agent-specific projections subordinate to that source.

The [system map](./SYSTEM.md) shows how person-owned context, access policy, agents, actions, feedback, derived state, and projections relate without treating an entire application as the protocol.

The [open-source boundary](./EXTENSIONS.md) separates the core contract from candidate extensions, reference workflows, and application-specific choices.

The [host contract](./HOST.md) defines what any agent, harness, or CLI must do to serve a person's context — with no required tool protocol, runtime, or privileged application. The files are the interface; two hosts that have never heard of each other must be able to serve the same person on the same store.

### `me.md`

`me.md` holds a small amount of context that is useful across many situations: how agents should work with you, your defaults, and your boundaries.

```markdown
# Me

## How to work with me

- Lead with the answer.
- Use plain language before technical detail.

## Boundaries

- Always ask before sending something as me.
- Do not make purchases without confirmation.
```

### Topics

Topic files hold focused personal context that should be recalled only when it is relevant.

```markdown
# Family

- Monday evenings are usually reserved for soccer practice.
```

An agent helping with a family calendar may need that context. An unrelated coding agent probably does not.

### Projects

Project context describes a piece of work, not the person.

```markdown
# Phoenix migration

- The rollout must be reversible.
- The next decision is whether to support dual writes.
```

Personal context follows the person. Project context follows the project.

### Proposals

Agents may notice something that could be useful later. They can propose it, but a proposal is not memory until the person accepts it.

That distinction matters:

```text
observation → proposal → user decision → durable context
```

The person remains the authority at every step.

## How agents should use it

A trusted agent or application may:

1. read only the context relevant to the current task;
2. follow the person's stated defaults and boundaries;
3. propose new durable context when something appears genuinely reusable;
4. make it possible to understand what context was used;
5. let the person inspect, edit, disable, forget, or delete it.

Reading context is not permission to take action on someone's behalf.

## What `me.md` is not

`me.md` is not:

- a transcript of everything a person has said;
- a hidden psychological or behavioral profile;
- a productivity score;
- manager or employer telemetry;
- permission for an agent to act without confirmation;
- a requirement to share the same context with every agent;
- memory owned by one application.

Sparse and true is better than comprehensive and speculative.

## Why open

A personal context layer cannot meaningfully belong to the person if one product alone defines, stores, and interprets it.

An open protocol makes it possible for:

- different agents and applications to work from the same user-owned source;
- people to inspect and move their context;
- independent implementations to challenge and improve the design;
- privacy, consent, and security claims to be examined in public;
- the protocol to outlive any one interface or company.

The protocol is the product. Interfaces are interchangeable.

## Project status and pacing

`me.md` is currently an experimental protocol draft. It is not yet a stable compatibility standard.

We use [small, interface-neutral experiments](./EXPERIMENTS.md) to test one human question at a time. These experiments are non-normative: an implementation supplies evidence for the protocol, not an automatic standard.

We are intentionally pacing the work in stages:

### 1. Establish the human contract

Define the sovereignty principles, boundaries, and language clearly enough that technical decisions can be judged against them.

### 2. Draft the core shape

Specify global, topic, and project context; proposals and consent; provenance; correction; forgetting; and deletion. Portability, capabilities, coverage receipts, and outcome events are deliberately deferred candidate contracts — see the [open-source boundary](./EXTENSIONS.md).

### 3. Build conformance tests

Create synthetic examples and tests that independent implementations can use to verify the core contract.

### 4. Learn from real implementations

Evolve the protocol through use, security review, and implementations that are independent of any one application.

The goal is not to standardize every possible memory system. It is to establish the smallest useful contract that keeps the person in control.

## Contributing

The most important question is not how much an agent can remember.

It is whether the system increases the person's agency.

Contributions should make personal context more legible, portable, scoped, revocable, and useful—without turning it into surveillance or administration.

Project governance is described in [GOVERNANCE.md](./GOVERNANCE.md). This project is licensed under the [Apache License 2.0](./LICENSE).
