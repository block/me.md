# The protocol shape

**Status:** Draft. This page is the smallest complete statement of the protocol.

`me.md` works with any AI harness or platform. If a tool can read and write files, it can serve a person's store. This page gives the full engagement in one shape. [HOST.md](./HOST.md) gives the full conformance rules.

## The store

```text
~/.me/
  me.md         read at the start of each session
  topics/       read a file only when the task makes it relevant
  projects/     read a file only for work on that project
  proposals/    the only location where an agent can write
  policy.json   if this says off, behave as if the store is absent
```

## The loop

The person's contract has three operations: read, propose, decide. A host adds one duty: mount. Together they make one loop:

```text
MOUNT    At the start of each session, find the store and read
         me.md. Do not ask the person. If the store is absent or
         policy is off, work normally without it.

RECALL   During the task, read the topic or project file that the
         task makes relevant. Do not read more.

PROPOSE  When you find something that the person may want to keep,
         write it to proposals/ in the person's words, and ask.
         Do not write to any other location in the store.

DECIDE   The person accepts, edits, or refuses. A refusal stays in
         effect. Silence is not acceptance.
```

An agent that follows the loop cannot write memory. Only the person can admit it.

## The paste-in form

Every harness has an instruction surface: a system prompt, a rules file, custom instructions, or an agent file. This block makes any of them serve the store:

```text
Serve my me.md store at ~/.me/ with this loop:

MOUNT — At the start of each session, read ~/.me/me.md if it exists
and ~/.me/policy.json does not say off. Do this automatically. Do
not ask me.

RECALL — Read a file in ~/.me/topics/ or ~/.me/projects/ only when
the current task makes it relevant.

PROPOSE — When you find something I may want to keep, write it as a
new file in ~/.me/proposals/ in my words, and ask me. Do not write
to any other location in ~/.me/.

DECIDE — I accept, edit, or refuse. My refusal stays in effect. My
silence is not acceptance.

What I say now always overrides the store. Stored preferences are
never permission to act for me.
```

This block is the complete integration for a harness that does not conform natively. A conforming host does all of this with no instructions — see [HOST.md](./HOST.md).

## Which document to use

- [SETUP.md](./SETUP.md) — for the person: create the store with one message.
- This page — for the harness: serve the store with one shape.
- [HOST.md](./HOST.md) — for the implementer: the full rules and the black-box tests.
- [BRIEFING.md](./BRIEFING.md) — the main output that the loop makes possible.
