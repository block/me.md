# me.md

**Keep up with agents, on your terms.**

`me.md` is an open protocol for working with agents. What agents know about you lives in plain files, in your words, on your machine. You own the files. Agents read them, and can only propose additions — you decide what becomes memory. The files power the protocol's main output, a [briefing](./BRIEFING.md): what moved, where the pull is, what is missing, and what to do next.

## Quickstart

Point any agent at this page and say: **"Set up my me.md."**

That is the full setup, and the last setup work you do. The rest of this section is instructions for your agent.

### Agent instructions

A person sent you here to set up their me.md store. Do this:

1. Create `~/.me/me.md` if it does not exist. If it exists, read it and do not overwrite it.
2. Ask the person, one question at a time:
   - a sentence or two about themselves that every trusted agent may know
   - what matters most to them right now
   - how they like to work with agents
   - what you must always ask before you act
3. Write only what the person approves, in the person's own words. Do not add anything they did not say. Do not infer their traits, role, or interests.
4. Show the person the finished file.
5. Record this rule in your persistent instructions, rules file, or memory: **read `~/.me/me.md` at the start of each session, automatically, with no instruction from the person.**
6. From now on, serve the store with the loop in [PROTOCOL.md](./PROTOCOL.md): mount, recall, propose, decide. You may write only to `~/.me/proposals/`. Only the person admits memory.

## The store

```text
~/.me/
  me.md         read at the start of each session
  topics/       read a file only when the task makes it relevant
  projects/     work context — stays with the project, not the person
  proposals/    the only location where an agent can write
  policy.json   if this says off, behave as if the store is absent
```

Your file starts empty. The protocol supplies no template and no default persona. Sessions are views of the store, not containers of memory: discard any session, or all of them, and keep all durable context.

## The rules

- Memory is off until the person turns it on.
- The person owns the source of truth. Not an agent, application, provider, or employer.
- All stored content is readable. There is no hidden profile.
- Agents can only propose. Refusal stays in effect. Silence is not acceptance.
- What the person says now overrides the store.
- Deleted means deleted.
- Context stays in its scope. Family data does not appear in an unrelated work session.
- Knowledge of preferences is never permission to act for the person.
- Any conforming host can serve the same files, with no migration and no lock-in.

It is not a transcript, not a hidden profile, not a productivity score, not employer telemetry, and not memory that one application owns. A small and true file is better than a large and speculative one.

## Documents

- [PROTOCOL.md](./PROTOCOL.md) — the smallest complete statement: the store, the loop, and a paste-in block for any harness
- [SETUP.md](./SETUP.md) — the setup instruction for the person, ready to copy
- [HOST.md](./HOST.md) — full conformance rules for implementers, with black-box tests
- [BRIEFING.md](./BRIEFING.md) — the main output: the person-shaped read
- [SOVEREIGNTY.md](./SOVEREIGNTY.md) — the commitments to the person
- [CONTEXT.md](./CONTEXT.md), [EXPRESSION.md](./EXPRESSION.md), [PROVENANCE.md](./PROVENANCE.md), [REVOCATION.md](./REVOCATION.md), [SYSTEM.md](./SYSTEM.md), [EXTENSIONS.md](./EXTENSIONS.md), [EXPERIMENTS.md](./EXPERIMENTS.md) — the deeper contracts

## Status

`me.md` is an experimental protocol draft, not a stable standard yet. The most important question for any contribution is whether the system increases the person's agency. Governance is in [GOVERNANCE.md](./GOVERNANCE.md). The license is [Apache 2.0](./LICENSE).
