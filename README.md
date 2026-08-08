# me.md

**Your memory should belong to you.**

`me.md` is an open memory protocol for AI agents. Everything an agent knows about you lives in plain files, in your words, on your machine:

```markdown
# Me

I'm training for my first marathon. Sundays are my long runs.

- Keep things short. I'm new to a lot of this.
- Ask me before you send anything to anyone.
```

That file is one person's, invented for illustration. Yours starts blank. The protocol ships no template, no default persona, no suggested topics — nothing that decides for you what your role is or what you care about.

Any agent you trust reads your file and knows you well enough to actually help. None of them own it. That is the entire technology: **the files are the interface.** No API, no server, no SDK, no account. The whole protocol is three moves:

```text
read     an agent recalls only what's relevant to the task at hand
propose  an agent that notices something worth keeping may only ask
decide   nothing becomes memory without your yes — and your no stays no
```

People call this memory, and we do too. The specification documents use **context** when precision matters — because part of the protocol's job is deciding what deserves to become memory at all. A proposal is not memory yet. A project fact is not personal memory. An agent's observation is not a fact about you.

## Quickstart

There is nothing to install. The protocol is a file you write.

1. **Create the file.** `mkdir -p ~/.me && touch ~/.me/me.md`
2. **Write something true, in your own words.** One line is enough.
3. **Point any agent you trust at it.** A conforming host discovers `~/.me/` on its own. For anything else, "read `~/.me/me.md` before we start" is a complete integration.

Your memory now outlives every tool that reads it. Add to the file when something proves worth keeping; delete anything, anytime, with a text editor.

## What memory does, in order

1. **Introduction** — an agent skips the stranger phase. No re-explaining yourself to every new tool.
2. **Working style** — answers arrive shaped the way you asked. The agent adapts to you.
3. **Boundary** — "always ask before sending as me" holds across every session and every host. Said once, stands guard permanently.
4. **Consent gate** — an agent that notices something worth keeping can only ask. Your yes is the only write path.
5. **Receipt** — every entry answers "why does it say this?": who wrote it, when, on whose authority.
6. **Advocate** — the file speaks for you when you're not watching: scopes recall to what's relevant, keeps family context out of work sessions, never lets stored preference become permission to act as you.
7. **Leverage** — the file is yours and the standard is open, so every tool competes to serve it and none can hold it hostage.

Steps 1–3 are why you write the file. Steps 4–7 are why you can afford to.

## Sovereignty first

Memory is a deeply personal thing. Most AI products treat it as theirs — collected silently, stored out of reach, and left behind when you leave. This protocol starts from the opposite commitment. A conforming implementation preserves these principles:

- **It is off until you turn it on.** Durable memory is opt-in, deliberate, and reversible.
- **You own the source of truth.** Not an agent, application, model provider, or employer.
- **You can see it.** Legible and inspectable, never a hidden inferred profile.
- **You choose what becomes durable.** An observation is not automatically a fact about you.
- **Context stays scoped.** Family context does not appear in an unrelated coding session.
- **What you say now wins.** Current instructions override stored defaults.
- **You can change your mind.** Correct, disable, forget, or delete — and deleted means deleted.
- **Action remains separate.** Knowing your preferences is not permission to act on your behalf.
- **Interfaces are replaceable.** Change agents or applications without surrendering continuity.

The full [sovereignty contract](./SOVEREIGNTY.md) separates these commitments from the technical choices still under test.

## A working shape

```text
~/.me/
  me.md         useful everywhere: how to work with you, defaults, boundaries
  topics/       focused context, recalled only when relevant
  projects/     work context — follows the project, not the person
  proposals/    agent suggestions awaiting your decision
  policy.json   on/off, audiences, scopes
```

The layout is the documentation, and it is not final. The deeper contracts:

- [CONTEXT.md](./CONTEXT.md) — the shared language: session, global, topic, project, proposed, and derived context
- [EXPRESSION.md](./EXPRESSION.md) — how memory is phrased in words the person recognizes as theirs, and how the system speaks about it
- [HOST.md](./HOST.md) — what any agent, harness, or CLI must do to serve a person's files; two hosts that have never heard of each other must serve the same person without coordinating
- [PROVENANCE.md](./PROVENANCE.md) — why any entry exists: what changed, who changed it, on whose authority
- [REVOCATION.md](./REVOCATION.md) — what disable, forget, delete, and purge must actually do
- [SYSTEM.md](./SYSTEM.md) — how person-owned context, policy, agents, and actions relate
- [EXTENSIONS.md](./EXTENSIONS.md) — what is core protocol, what is a candidate extension, and what stays application-specific
- [EXPERIMENTS.md](./EXPERIMENTS.md) — small, interface-neutral tests of one human question at a time

## What `me.md` is not

Not a transcript of everything you've said. Not a hidden psychological profile. Not a productivity score. Not manager or employer telemetry. Not permission for an agent to act without confirmation. Not memory owned by one application.

Sparse and true is better than comprehensive and speculative.

## Why open

A memory layer cannot meaningfully belong to the person if one product alone defines, stores, and interprets it. An open protocol lets independent implementations serve the same user-owned files, lets privacy and consent claims be examined in public, and lets the protocol outlive any one interface or company.

The protocol is the product. Interfaces are interchangeable.

## Status and contributing

`me.md` is an experimental protocol draft, not yet a stable standard. The work is paced: human contract first, then the core shape, then conformance tests, then evolution through independent implementations.

The most important question for any contribution is not how much an agent can remember. It is whether the system increases the person's agency.

Governance is described in [GOVERNANCE.md](./GOVERNANCE.md). Licensed under [Apache 2.0](./LICENSE).
