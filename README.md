# thou

**Agents that turn toward you.**

You say me. Your agents say thou.

Every agent you use is starting to remember you. Each one keeps what it learns in its own place, in its own format, under its own rules. There is no one place where you can read all of it, carry it to the next agent, or turn it all off. Some of it is not something you said. It was inferred about you, and it is kept on someone else's terms.

The thou protocol starts from the other side. It is an open protocol for personal context. What your agents know about you lives in plain files you own, starting with `~/.me/me.md`. Every agent that follows the protocol reads those files the same way. It asks before it keeps anything it inferred about you, it records each change it makes, and it stops using the files when you turn memory off.

The point is not memory for its own sake. It is to help you keep up with your agents, on your terms. The files power the protocol's main output, a [briefing](./BRIEFING.md): what moved, where the pull is, what is missing, and what to do next.

## Quickstart

Point any agent at this page and say: **"Set up my me.md."** The agent creates your `me.md` file and serves it under the thou protocol.

Agents: follow the [setup instruction](./SETUP.md#the-setup-instruction), then serve the store with the loop in [PROTOCOL.md](./PROTOCOL.md). SETUP.md is the only setup procedure. PROTOCOL.md summarizes the [store layout](./PROTOCOL.md#the-store), and [STORE.md](./STORE.md) defines it.

Your store is the folder `~/.me/`, or the folder named in the `ME_HOME` environment variable if you set it, for example to try the protocol in a test folder. Your file holds only what you tell it. The protocol supplies no template and no default persona. A session only reads the store. It does not hold your memory: delete any session, or all of them, and you keep all durable context.

## What it looks like

Your words, in `~/.me/me.md`:

```markdown
I lead the payments migration. Mornings are for deep work.
Always ask me before you message anyone outside my team.
```

An agent notices something and can only ask. It writes a proposal in `~/.me/proposals/`:

```markdown
---
status: pending
target: topics/travel.md
proposed-by: goose 1.9 (trip-helper)
proposed-at: 2026-11-12T17:03:01Z
basis: You asked for aisle seats on two bookings this week.
---

Prefer aisle seats when booking flights.
```

You accept it, in any agent that serves the store. The acceptance leaves two lines in `~/.me/journal.md`, your decision and the change:

```text
- 2026-11-12T17:05:40Z | proposals/20261112T170301Z-7f3a.md | accepted | host: goose 1.9 (trip-helper) | authority: person direct
- 2026-11-12T17:05:40Z | topics/travel.md | added a preference | host: goose 1.9 (trip-helper) | authority: accepted proposal 20261112T170301Z-7f3a
```

Refuse it instead, and no agent that follows the protocol proposes those words again. Write `{"state": "off"}` in `~/.me/policy.json`, and every one of them stops using the store.

## What we hold to

These are the commitments in short form. [SOVEREIGNTY.md](./SOVEREIGNTY.md) states them in full, and [HOST.md](./HOST.md) and [STORE.md](./STORE.md) turn them into requirements a host can be tested against.

- **You are the authority on you.** Stored context can help an agent understand you. It never defines you. What an agent inferred ranks below what you said yourself. You own the source of truth, not an agent, an application, a provider or an employer.
- **Memory starts with you, and it is chosen.** There is no memory until you create your file. Something an agent notices becomes a proposal: a short file that waits for you. You accept it, edit it or refuse it, or ask for an edit directly. A refusal stays in effect until you delete it. Silence is not a yes.
- **You can read all of it.** Your context is Markdown. No hidden profile, embedding or score competes with what you wrote. A host that changes your files records each change in a journal you can read: what changed, when, through which host, and on whose authority.
- **What you say now wins.** The store gives agents continuity. It has no authority over what you ask for in the present conversation.
- **Only what the task needs.** An agent recalls the least it needs for the work in front of it. Every agent reads `me.md` at the start of every session, so it holds only what every agent may know. Topic and project files are read only when the task needs them, so family context in its own topic file does not appear in an unrelated work session.
- **Knowing you is not permission.** Knowing what you prefer does not let an agent send, buy, publish or approve anything for you. Your context can narrow what an agent may do. It never grants a new power.
- **One switch turns it off, and deletion is honest.** `{"state": "off"}` in `policy.json` turns memory off in every agent that follows the protocol: at once for new sessions, and at the next read or write in a session already open. The switch is a request that those agents honor, not a lock. It does not stop software that ignores the protocol, and it cannot take back what a session has already read. A host that can keep that promise only by asking a model to obey must say so in its conformance claim, with the words "by instruction". A host never calls something deleted while it still uses a copy, and it tells you what it cannot delete, such as a model provider's logs.
- **It is yours, not your employer's.** The protocol is not a productivity score, a manager's dashboard or a way to watch people at work. Context about other people stays minimal, and scoped to your own legitimate use.
- **No one owns the interface.** Any conforming agent on the same computer serves the same files, with no migration and no lock-in. Syncing between devices is not defined yet.
- **Moving it is your choice.** Exporting or syncing your context into another tool is a separate step that you start. It never widens who can see it by default.

The store is not a transcript, and it is not memory that one application owns. A small and true file is better than a large and speculative one.

## Why the name

The name rhymes with "how". It is the old English word for "you", said to the person you are speaking to.

In 1923 Martin Buber wrote that we can meet another being as a *Thou*, a whole person. Or we can treat them as an *It*, a thing to know about and use ([Stanford Encyclopedia of Philosophy, "Martin Buber"](https://plato.stanford.edu/entries/buber/)). AI memory often treats you as an It: a profile inferred about you, kept by someone else, and shaped for their purposes. The thou protocol takes the other side. Software can't meet you the way a person can. It can ask before it keeps anything, and keep only what you agreed to, in words you can read, in files you own.

The file is yours, so it is called `me.md`. The protocol is the agent's side of the relationship, so it is called thou. The first drafts of the protocol were called `me.md` too. Your file keeps that name.

## What it can't promise yet

The protocol is an experimental draft, and some of what it is for is not proven yet.

- Not every agent can enforce the off switch below the model. One that only follows instructions has to say so.
- No host has claimed conformance yet. Today you try the protocol through the paste-in block in [PROTOCOL.md](./PROTOCOL.md#the-paste-in-form), which makes an agent follow it by instruction. That is the weakest form.
- The off switch covers these files only. It does not turn off the memory features built into the agents you use.
- The journal is an account that each host keeps of its own changes. It is not tamper-proof: any program that can write your files can write a false line. Signed decisions are not defined yet.
- Syncing between devices, undo and encrypted files are not defined yet. Whether Markdown is the right format is still under test. [STORE.md](./STORE.md#what-this-version-does-not-define) lists what the format does not define yet, and [SOVEREIGNTY.md](./SOVEREIGNTY.md#what-remains-under-test) lists the open questions.
- A conformance runner that checks how an agent behaves, and not just its files, is planned. Until it exists, the tests in [HOST.md](./HOST.md#black-box-conformance) are a review standard.
- The central test of portability has not been run yet: [two agents that have never met, serving the same store](./experiments/0009-serve-one-store-from-two-hosts.md). It is a proposed experiment.

## Where your files go

- The files are plain text. Only your user account, and your disk encryption if you use it, protect them. Any program that runs as you can read them.
- While memory is on, every agent that follows the protocol reads `me.md` at the start of every session. If an agent uses a model in the cloud, your words reach that model's provider. Keep out of `me.md` anything you would not tell every agent you use.
- A refused proposal stays on disk, with its words, so that no agent proposes them again. Delete the file to remove the words, and the refusal goes with it.
- On a work computer, whoever administers the computer may be able to read the files. Keep personal context off a work computer.

## What the thou protocol is not

- Not a memory product, an app or a cloud service. It is files on your computer and rules for agents.
- Not a project file. An `AGENTS.md` file tells agents about a codebase. Your `me.md` tells them about you, in every project.
- Not one tool's memory. A memory file that one tool keeps serves that tool. Your store serves every agent that follows the protocol.
- Not a transport. A memory server is a way to reach context. The thou protocol is the files and the consent rules, and a server can serve them.
- Not owned by Block. Block wrote the first draft, and the aim is a neutral home.
- Not employer telemetry. [SOVEREIGNTY.md](./SOVEREIGNTY.md#personal-context-is-not-organizational-telemetry) says so.

## Documents

Every protocol document listed below starts with a status line. There are three kinds.

**Normative drafts.** HOST.md defines host conformance, STORE.md defines the file formats, SOVEREIGNTY.md states the commitments to the person, and BRIEFING.md defines a conforming briefing. These drafts may change.

- [HOST.md](./HOST.md) — conformance rules and levels for implementers, with black-box tests
- [STORE.md](./STORE.md) — the file formats: layout, policy, proposals, journal, and safe writes
- [BRIEFING.md](./BRIEFING.md) — the main output, the person-shaped read, produced by hosts at the Briefer level
- [SOVEREIGNTY.md](./SOVEREIGNTY.md) — the commitments to the person

**Guides.** Setup and an overview of the rules.

- [PROTOCOL.md](./PROTOCOL.md) — the store, the loop, and a paste-in block for a harness
- [SETUP.md](./SETUP.md) — the setup instruction, ready to copy

**Non-normative.** Design notes, vocabulary, and open questions. They explain the rules. They do not add to them. Where they say "must", they explain; they do not bind a host.

- [CONTEXT.md](./CONTEXT.md) — shared vocabulary
- [PROVENANCE.md](./PROVENANCE.md) and [REVOCATION.md](./REVOCATION.md) — the reasons behind HOST.md §4 and §5
- [EXPRESSION.md](./EXPRESSION.md) — how context is put into words and admitted
- [SYSTEM.md](./SYSTEM.md) — the conceptual system map
- [EXTENSIONS.md](./EXTENSIONS.md) — the open-source boundary and candidate extensions
- [EXPERIMENTS.md](./EXPERIMENTS.md) — how the protocol is tested

**When documents disagree**, HOST.md and STORE.md win, then BRIEFING.md, then the guides, then the non-normative notes. SOVEREIGNTY.md says what the rules are for. A rule that breaks a commitment in it is a bug to fix.

## Tools

- The [thou-lint](./tools/README.md) tool checks that a store follows [STORE.md](./STORE.md). It checks files, not host behavior.

## Status, and how to help

The thou protocol is an experimental draft, not a stable standard yet. Releases are tagged `vX.Y.Z`, and a host that claims conformance names the release and the level it follows. Changes are in [CHANGELOG.md](./CHANGELOG.md).

If you build agents, read the spec and serve a store. If you use them, say **"Set up my me.md."** and tell us where it falls short. Every change gets the same test: does it give the person more say? Governance is in [GOVERNANCE.md](./GOVERNANCE.md). The license is [Apache 2.0](./LICENSE).
