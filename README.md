# me.md

**Keep up with agents, on your terms.**

Work is filling with agents. They act while you sleep, produce more than you can read, and move faster than you can watch. The person who tries to follow all of it drowns. The person who ignores it falls behind.

`me.md` gives you the other option: a **briefing**, shaped by you. It turns everything that moved into a person-shaped read — what moved, where the pull is, what is missing, and what to do next. Not a feed of all activity. A read built from what matters most to you.

For the briefing to be yours, the agents must know you — your aims, your boundaries, your "ask me first." That knowing is **memory**, and it must belong to you, or the briefing becomes one more thing a product does to you. So the protocol rests on memory you own: plain files, in your words, on your machine.

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

## The briefing

Memory is the substrate. The briefing is the chief value: the person-shaped read that lets you keep up with agents. A briefing looks like this:

```text
What moved      3 signals since your last read: 1 new, 2 unchanged.
                The migration decision you watch moved yesterday.

Where the pull  2 reviews wait on you. Your API change has waited
                15 days with no reviewer — consider a nudge.

What is missing Messages were scanned headers-only, so obligations
                there are this read's blind spot, not an absence.

Your move       Answer the review that blocks the release.

Coverage        git (34), calendar (12), mail (50, headers only).
```

Every part is composed against your aims and your watches — the same activity produces a different briefing for a different person. The full contract is [BRIEFING.md](./BRIEFING.md): five required parts, read-only composition, one suggested move, and an honest coverage receipt in every read.

## Quickstart

You do not install the protocol. Any agent you already use can set it up for you.

Give this instruction to any agent — a chat app, a CLI, an IDE, anything that can write a file:

> Set up my me.md memory. Create `~/.me/me.md` if it does not exist. Ask me a few short questions about how I like to work and what you must always ask before doing. Write only what I approve, in my own words. Then read that file at the start of every future session automatically, without my asking — record that rule in your persistent instructions now.

That one message is the full setup — the last setup effort you spend. A conforming host finds `~/.me/` and reads it at the start of every session on its own. You never ask an agent to remember you, and you never repeat the instruction. If a tool makes you re-invoke your own memory by hand each session, it is spending the attention this protocol exists to protect. (For an agent that does not yet conform, the one line "read `~/.me/me.md` before we start" is the temporary bridge.) [SETUP.md](./SETUP.md) has the full setup instruction, ready to copy.

If you prefer to do it yourself:

1. **Create the file.** `mkdir -p ~/.me && touch ~/.me/me.md`
2. **Write one true thing in your own words.** One line is sufficient.

Your memory now continues after each tool that reads it is gone. Add lines when they show their value. Remove any line, at any time, with a text editor — or tell any agent to do it for you.

## What the protocol does, in sequence

1. **Introduction** — an agent starts with knowledge of you. You do not introduce yourself to each new tool again.
2. **Working style** — answers come in the shape that you asked for. The agent adapts to you.
3. **Boundary** — a rule such as "ask me before you send anything as me" applies in each session and each host. You write the rule one time. The rule stays in effect.
4. **Consent gate** — an agent that finds something worth keeping can only ask. Only your agreement can add memory.
5. **Receipt** — each entry can show why it exists: who wrote it, when, and with what approval.
6. **Advocate** — the file speaks for you when you do not monitor it. It limits what agents read to the current task. It keeps family data out of work sessions. It does not let a stored preference become permission to act as you.
7. **Independence** — you own the file, and the standard is open. Each tool must compete to serve the file. No tool can lock the file in.
8. **Briefing** — the destination. Agents that know your aims turn everything that moved into your person-shaped read, and you keep up.

Points 1 through 3 are the reasons to write the file. Points 4 through 7 are the reasons the file is safe to write. Point 8 is the reason the protocol exists.

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

The briefing contract is drafted in [BRIEFING.md](./BRIEFING.md). The store shape that powers it — aims, workstreams, watches, and the people you work with — is planned, tracked as candidate contracts in [EXTENSIONS.md](./EXTENSIONS.md).

The layout is the documentation. The layout is not final. These documents give the full contracts:

- [CONTEXT.md](./CONTEXT.md) — the shared language: session, global, topic, project, proposed, and derived context
- [EXPRESSION.md](./EXPRESSION.md) — how memory is written in words that you know as yours, and how the system speaks about it
- [BRIEFING.md](./BRIEFING.md) — the protocol's main output: what a person-shaped briefing must contain, and the rules that keep it an advocate
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

A personal layer does not belong to the person if one product alone defines, stores, and interprets it. An open protocol lets independent implementations serve the same user-owned files. It lets the public examine the privacy and consent claims. It lets the protocol continue after each interface or company is gone.

The protocol is the product. Interfaces are interchangeable.

## Status and contributing

`me.md` is an experimental protocol draft. It is not a stable standard yet. The work has this sequence: the human contract first, then the core shape, then conformance tests, then evolution through independent implementations.

The most important question for a contribution is not how much an agent can remember. It is whether the system increases the person's agency.

[GOVERNANCE.md](./GOVERNANCE.md) describes the governance. The license is [Apache 2.0](./LICENSE).
