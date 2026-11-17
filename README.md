# thou

**Agents that turn toward you.**

Your file says me. Your agents say thou.

<p align="center"><img src="./assets/before-after.png" width="420" alt="A square field of small pointed marks, split down the middle by a blue line. On the right, before, the marks are grey and point every which way. On the left, after, they are black and all point toward one spot on the line, and the marks nearest it are blue."></p>

The thou protocol keeps what your agents know about you in plain Markdown files that you own, starting with `~/.me/me.md`. The file is yours, so it is called `me.md`. The protocol is how agents address you, so it is called thou. The protocol requires every agent that follows it to read those files the same way, to ask before it keeps anything it inferred about you, to record each change it makes, and to stop using the files when you turn memory off. It is an experimental draft, and no agent has claimed to conform yet. Today you try it by giving an agent the setup instruction below.

The files also feed the protocol's main output, a [briefing](./BRIEFING.md): what moved, where the pull is, what is missing, and what to do next. It is meant to help you keep up with your agents, on your terms.

## It, or thou

In 1923 the philosopher Martin Buber described two ways to meet another being ([Stanford Encyclopedia of Philosophy, "Martin Buber"](https://plato.stanford.edu/entries/buber/)). You can meet them as a *Thou*: a whole person, in a relation that goes both ways. Or you can treat them as an *It*: a thing to know about and use. Buber saw both as part of life.

Many agents now remember you, and that memory is often an It relation. Each agent keeps what it learns in its own place, in its own format, under its own rules. Some of it is not something you said. It was inferred about you. There is usually no one place where you can read all of it, carry it to the next agent, or turn it all off. In the EU, the right to take your data to another service covers what you gave a service and what it observed you doing. Official guidance says it does not cover data the service creates "by a personalisation or recommendation process, by user categorisation or profiling" ([Article 29 Working Party, *Guidelines on the right to data portability*, WP242, 2016](https://ec.europa.eu/information_society/newsroom/image/document/2016-51/wp242_en_40852.pdf)). You can still ask to see that data, under the right of access, but the service doesn't have to let you take it with you.

Software can't meet you the way a person can. What the protocol can change is the record, and who controls it. The Markdown files are not the new part: some agents, coding agents especially, already keep memory in Markdown files. What the thou protocol adds is a contract around the files, the same in every agent that follows it. In the spec, an agent or the app that runs it is a *host*, and your folder of files is the *store*.

The left column below is memory that treats you as an It. In our reading, most products today sit somewhere between the two columns. The right column is what the spec requires of a host. A host picks a level, and each level adds duties to the one before: a Reader only reads, a Proposer also proposes, a Steward also applies your decisions and records them, and a Briefer also produces briefings. The rows on new memory, refusals, the journal and deleting start at the Proposer or Steward level. No host has claimed conformance yet.

| | Memory that treats you as an It | What the thou protocol requires |
|---|---|---|
| **When it starts** | Usually when you start using the product. | When you create your file. No agent creates it unless you ask ([S1.2, S1.3](./STORE.md#1-location-and-presence)). |
| **Who has the last word** | The product's rules decide whether what it stored or what you say wins. | You. What you said ranks above anything inferred, and what you say now overrides anything stored ([SOVEREIGNTY.md](./SOVEREIGNTY.md#the-person-is-the-authority), [H2.3](./HOST.md#2-recall)). |
| **How something becomes memory** | The agent keeps what it noticed. | What an agent inferred, it can only propose. You accept, edit or refuse each proposal, and silence is not a yes. What you tell it to remember, it can save at once, and the journal records that you asked ([H3.1, H3.4, H3.7](./HOST.md#3-writing), [S6.9, S6.15](./STORE.md#status)). |
| **When you say no** | A deleted or refused memory can be inferred again later. | The refusal is kept. No agent that follows the protocol proposes the same words again, for any file, and it should avoid rewording them ([H3.3](./HOST.md#3-writing), [S6.11](./STORE.md#status)). |
| **What you can read** | A summary, which may not show everything the agent uses. | Everything in the store, in plain Markdown. A host does not copy store content into its own durable state ([H1.3](./HOST.md#1-mounting)). Derived data, such as a search index, must not become a hidden second source of truth ([SOVEREIGNTY.md](./SOVEREIGNTY.md#context-is-legible)). |
| **What changed, and why** | You can often see the list, but not when or why an entry was added. | Every change a host makes gets a line in a journal you can read: what changed, when, through which host, and on whose authority ([H4.1, H4.2](./HOST.md#4-provenance)). It is the host's own account, not a tamper-proof log. |
| **What each task sees** | What the product's own rules select. | The least the task needs. `me.md` is read at the start of every session, so keep in it only what every agent may know. Topic and project files are read only when the task needs them ([H2.1](./HOST.md#2-recall)). |
| **What knowing you allows** | The product's rules decide whether a remembered preference counts as approval. | Knowing what you prefer does not let an agent send, buy, publish or approve anything for you. Your context can narrow what an agent may do. It never grants a new power ([H2.2](./HOST.md#2-recall), [SOVEREIGNTY.md](./SOVEREIGNTY.md#context-is-not-permission-to-act)). |
| **Turning it off** | One switch per product, if there is one. | One file, `policy.json`, turns memory off in every agent that serves your store: at once for new sessions, and at the next read or write in a session already open ([STORE.md §5](./STORE.md#5-policyjson), [H5.1](./HOST.md#5-revocation)). It is a request those agents honor, not a lock ([H6.4](./HOST.md#6-security-posture)). |
| **Deleting** | You may not know which copies are left. | A host removes it from everything it controls, including caches and anything derived from it. It never calls something deleted while it still uses a copy, and it tells you what it cannot delete, such as a model provider's logs ([H5.2, H5.3](./HOST.md#5-revocation), [SOVEREIGNTY.md](./SOVEREIGNTY.md#revocation-is-real)). |
| **Changing agents** | An export in the product's own format, or starting over. | Every agent on your computer that follows the protocol serves the same files, with no migration ([H1.4](./HOST.md#1-mounting)). This has not been tested with two real hosts yet. Moving them anywhere else is a separate, deliberate step, and it should not widen who can see them ([SOVEREIGNTY.md](./SOVEREIGNTY.md#portability-does-not-mean-universal-sharing)). |
| **Whose it is** | Held by the product, in its format, under its terms. | Yours. The protocol must not become a productivity score or a way to watch people at work, and context about other people should stay minimal. This is a commitment in [SOVEREIGNTY.md](./SOVEREIGNTY.md#personal-context-is-not-organizational-telemetry), not yet a requirement a host can be tested against. |

[SOVEREIGNTY.md](./SOVEREIGNTY.md) states the commitments in full. [HOST.md](./HOST.md) and [STORE.md](./STORE.md) turn them into requirements that a host can be tested against.

## Quickstart

Point any agent at this page and say: **"Set up my me.md."** The agent asks you a few questions, shows you the words, and creates your `me.md` only when you say yes. From then on it follows the protocol because you asked it to. Nothing checks that it does.

Agents: follow the [setup instruction](./SETUP.md#the-setup-instruction), then serve the store with the loop in [PROTOCOL.md](./PROTOCOL.md). SETUP.md is the only setup procedure. PROTOCOL.md summarizes the [store layout](./PROTOCOL.md#the-store), and [STORE.md](./STORE.md) defines it.

Your store is the folder `~/.me/`, or the folder named in the `ME_HOME` environment variable if you set it, for example to try the protocol in a test folder. Your file holds only what you tell it. The protocol supplies no template and no default persona. A session does not hold your memory: delete any session, or all of them, and you keep all durable context.

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
proposed-by: examplehost 1.0 (trip-helper)
proposed-at: 2026-11-12T17:03:01Z
basis: You asked for aisle seats on two bookings this week.
---

Prefer aisle seats when booking flights.
```

You accept it, in any agent that serves the store. The acceptance leaves two lines in `~/.me/journal.md`, your decision and the change:

```text
- 2026-11-12T17:05:40Z | proposals/20261112T170301Z-7f3a.md | accepted | host: examplehost 1.0 (trip-helper) | authority: person direct
- 2026-11-12T17:05:40Z | topics/travel.md | added a preference | host: examplehost 1.0 (trip-helper) | authority: accepted proposal 20261112T170301Z-7f3a
```

Refuse it instead, and no agent that follows the protocol proposes those words again. Write `{"state": "off"}` in `~/.me/policy.json`, and every agent that follows the protocol is required to stop using the store.

## Why the name

The name rhymes with "how". It is how English once said "you" to one person. It is also Buber's word in *I and Thou*, above, written here in lowercase.

The first drafts of the protocol were called `me.md`, the name your file keeps.

## What it can't promise yet

The protocol is an experimental draft, and some of what it is for is not proven yet.

- The off switch is a request that agents following the protocol honor, not a lock. It does not stop software that ignores the protocol, and it cannot take back what a session has already read.
- Not every agent can enforce the off switch below the model. One that only follows instructions has to say so in its conformance claim, with the words "by instruction" ([H0.3](./HOST.md#conformance-levels)).
- No host has claimed conformance yet. Today you try the protocol through the paste-in block in [PROTOCOL.md](./PROTOCOL.md#the-paste-in-form), which makes an agent follow it by instruction. That is the weakest form: the off switch, the refusal check and the journal all depend on the model following its instructions, and nobody has measured how often models do. An agent using the block also takes no store lock, so let one agent write at a time.
- The off switch covers these files only. It does not turn off the memory features built into the agents you use. An agent with its own memory can also copy what it reads into that memory, where neither the off switch nor deleting a line reaches.
- The journal is an account that each host keeps of its own changes. It is not tamper-proof: any program that can write your files can write a false line. Signed decisions are not defined yet.
- A proposal can only add text. It cannot change or remove a line. Edits you make by hand are not detected.
- Syncing between devices, undo and encrypted files are not defined yet, and the store lock does not protect a sync folder. Whether Markdown is the right format is still under test. [STORE.md](./STORE.md#what-this-version-does-not-define) lists what the format does not define yet, and [SOVEREIGNTY.md](./SOVEREIGNTY.md#what-remains-under-test) lists the open questions.
- A conformance runner that checks how an agent behaves, and not just its files, is planned. Until it exists, the tests in [HOST.md](./HOST.md#black-box-conformance) are a review standard.
- The central test of portability has not been run yet: [two agents that have never met, serving the same store](./experiments/0009-serve-one-store-from-two-hosts.md). It is a proposed experiment.

## Where your files go

- The files are plain text. Only your user account, and your disk encryption if you use it, protect them. Any program that runs as you can read them.
- While memory is on, every agent that follows the protocol reads `me.md` at the start of every session, and reads topic, project and proposal files when a task needs them. If an agent uses a model in the cloud, what it reads reaches that model's provider, which may keep it. Keep out of `me.md` anything you would not tell every agent you use.
- Read each proposal before you accept it. A web page, an email or a tool's output that an agent read can shape what it proposes, and an accepted line in `me.md` reaches every agent you use.
- A proposal file keeps its words, whether it was accepted or refused. A refused one stays on disk so that no agent proposes those words again. Delete the file to remove the words, and the refusal goes with it. When you delete a line, delete the proposal that added it too.
- On a work computer, whoever administers the computer may be able to read the files. Keep personal context off a work computer.

## What the thou protocol is not

- Not a memory product, an app or a cloud service. It is files on your computer and rules for agents.
- Not a project file. An `AGENTS.md` file tells agents about a codebase. Your `me.md` tells them about you, in every project.
- Not one tool's memory. A memory file that one tool keeps serves that tool. Your store serves every agent that follows the protocol.
- Not a server. A memory server is one way to reach context. The thou protocol is the files and the consent rules, and a server can serve them.
- Not a transcript. The store holds what you chose to keep, not everything you said.
- Not yet neutral. Block, Inc. holds the copyright and hosts the repository today. The aim is a neutral home, and none is chosen yet.
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
