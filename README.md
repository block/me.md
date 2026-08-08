# me.md

**Your memory should belong to you.**

`me.md` is an open memory protocol for AI agents. All the data that an agent knows about you is in plain files. The files use your words. The files stay on your machine:

```markdown
# Me

I'm training for my first marathon. Sundays are my long runs.

- Keep things short. I'm new to a lot of this.
- Ask me before you send anything to anyone.
```

This file is an example only. Your file starts empty. The protocol supplies no template, no default persona, and no suggested topics. The protocol does not decide your role or your interests. You do.

An agent that you trust can read your file. Then the agent knows enough about you to give you real help. No agent owns the file. This is the full technology: **the files are the interface.** There is no API, no server, no SDK, and no account. The protocol has three operations:

```text
read     an agent reads only the content that applies to the current task
propose  an agent that finds something worth keeping can only ask you
decide   content becomes memory only when you agree — and your refusal stays in effect
```

People call this memory. We do too. The specification documents use the word **context** when precision is necessary. One task of the protocol is to decide which content can become memory. A proposal is not memory. A project fact is not personal memory. An observation from an agent is not a fact about you.

## Quickstart

You do not install the protocol. You write a file.

1. **Create the file.** `mkdir -p ~/.me && touch ~/.me/me.md`
2. **Write one true thing in your own words.** One line is sufficient.
3. **Tell an agent that you trust to read the file.** A conforming host finds `~/.me/` without help. For all other agents, the instruction "read `~/.me/me.md` before we start" is a complete integration.

Your memory now continues after each tool that reads it is gone. Add lines when they show their value. Remove any line, at any time, with a text editor.

## What memory does, in sequence

1. **Introduction** — an agent starts with knowledge of you. You do not introduce yourself to each new tool again.
2. **Working style** — answers come in the shape that you asked for. The agent adapts to you.
3. **Boundary** — a rule such as "ask me before you send anything as me" applies in each session and each host. You write the rule one time. The rule stays in effect.
4. **Consent gate** — an agent that finds something worth keeping can only ask. Only your agreement can add memory.
5. **Receipt** — each entry can show why it exists: who wrote it, when, and with what approval.
6. **Advocate** — the file speaks for you when you do not monitor it. It limits what agents read to the current task. It keeps family data out of work sessions. It does not let a stored preference become permission to act as you.
7. **Independence** — you own the file, and the standard is open. Each tool must compete to serve the file. No tool can lock the file in.

Points 1 through 3 are the reasons to write the file. Points 4 through 7 are the reasons the file is safe to write.

## Sovereignty first

Memory is personal. Most AI products keep your memory as their property. They collect it without your knowledge. They store it where you cannot see it. They keep it when you go. This protocol starts from the opposite rule. A conforming implementation obeys these principles:

- **Memory is off until you set it to on.** Durable memory is optional, deliberate, and reversible.
- **You own the source of truth.** No agent, application, model provider, or employer owns it.
- **You can see it.** All stored content is readable. There is no hidden profile.
- **You decide what becomes durable.** An observation is not automatically a fact about you.
- **Context stays in its scope.** Family data does not appear in an unrelated work session.
- **Your current instruction wins.** What you say now overrides stored defaults.
- **You can change your decision.** You can correct, disable, forget, or delete content. Deleted content stays deleted.
- **Action stays separate.** Knowledge of your preferences is not permission to act for you.
- **Interfaces are replaceable.** You can change agents or applications and keep your memory.

The [sovereignty contract](./SOVEREIGNTY.md) separates these commitments from the technical choices that are still under test.

## A working shape

```text
~/.me/
  me.md         applies everywhere: how to work with you, defaults, boundaries
  topics/       focused context, read only when it applies
  projects/     work context — stays with the project, not the person
  proposals/    agent suggestions that wait for your decision
  policy.json   on/off, audiences, scopes
```

The layout is the documentation. The layout is not final. These documents give the full contracts:

- [CONTEXT.md](./CONTEXT.md) — the shared language: session, global, topic, project, proposed, and derived context
- [EXPRESSION.md](./EXPRESSION.md) — how memory is written in words that you know as yours, and how the system speaks about it
- [HOST.md](./HOST.md) — the rules for each agent, harness, or CLI that serves your files; two hosts with no knowledge of each other must serve the same person without coordination
- [PROVENANCE.md](./PROVENANCE.md) — why an entry exists: what changed, who changed it, and with what approval
- [REVOCATION.md](./REVOCATION.md) — what disable, forget, delete, and purge must do
- [SYSTEM.md](./SYSTEM.md) — how person-owned context, policy, agents, and actions connect
- [EXTENSIONS.md](./EXTENSIONS.md) — what is core protocol, what is a candidate extension, and what stays application-specific
- [EXPERIMENTS.md](./EXPERIMENTS.md) — small, interface-neutral tests of one human question at a time

## What `me.md` is not

It is not a transcript of all that you said. It is not a hidden psychological profile. It is not a productivity score. It is not manager or employer telemetry. It is not permission for an agent to act without confirmation. It is not memory that one application owns.

A small and true file is better than a large and speculative one.

## Why open

A memory layer does not belong to the person if one product alone defines, stores, and interprets it. An open protocol lets independent implementations serve the same user-owned files. It lets the public examine the privacy and consent claims. It lets the protocol continue after each interface or company is gone.

The protocol is the product. Interfaces are interchangeable.

## Status and contributing

`me.md` is an experimental protocol draft. It is not a stable standard yet. The work has this sequence: the human contract first, then the core shape, then conformance tests, then evolution through independent implementations.

The most important question for a contribution is not how much an agent can remember. It is whether the system increases the person's agency.

[GOVERNANCE.md](./GOVERNANCE.md) describes the governance. The license is [Apache 2.0](./LICENSE).
