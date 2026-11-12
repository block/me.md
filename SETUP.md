# Set up me.md with any agent

**Status:** Guide for the person. It adds no rules. The rules are in [HOST.md](./HOST.md), [STORE.md](./STORE.md), and [SOVEREIGNTY.md](./SOVEREIGNTY.md).

`me.md` is a new protocol for working with agents. It preserves human sovereignty: you own what agents know about you, you decide what they remember, and any agent on your computer that follows the protocol can use it. The purpose is not memory for its own sake. The purpose is to let you act on the things that matter most to you, with agents that know you well enough to help.

You do not install the protocol. You give one instruction to any agent that can read and write files on your computer: a CLI agent, a desktop agent, or an IDE assistant. A chat app in a web browser usually cannot reach your files, so it cannot set up or serve the store.

## The setup instruction

Copy this message and give it to any agent you trust that can work with your files:

```text
Set up my me.md. It is an open protocol for working with agents: I
own what you know about me, I decide what you remember, and any
other agent on this computer that follows the protocol can use it.

My store is the folder named in the ME_HOME environment variable if
it is set, and ~/.me/ otherwise. Below, "the store" means that
folder.

1. Create me.md in the store if it does not exist. If it exists,
   read it and do not overwrite it.
2. Tell me that every agent I use will read this file at the start
   of each session. Then ask me, one question at a time:
   - a sentence or two about myself that every trusted agent may know
   - what matters most to me right now
   - how I like to work with agents
   - what you must always ask me before you act
3. Write only what I approve, in my own words. Do not add anything I
   did not say. Do not infer my traits, role, or interests.
4. Show me the finished file. Then add this line at the end of
   journal.md in the store, with the current UTC time and your name
   and version:
   - <time> | me.md | created me.md | host: <you> | authority: person direct
   If me.md already existed and you changed it, write "changed me.md"
   instead. If you changed nothing, add no line.
5. Copy the paste-in block from
   https://github.com/block/me.md/blob/main/PROTOCOL.md#the-paste-in-form
   into your persistent instructions, rules file, or memory, so that
   it continues after this conversation. If you cannot fetch it,
   record at least this rule: at the start of each session, find the store (ME_HOME if it is set, otherwise
   ~/.me/), read only policy.json in it, and decide before you open
   any other file there. Memory is on if the file is missing, or if
   it is a JSON object whose "state" is exactly "on". Otherwise,
   including when it is not valid JSON, memory is off: open no other
   file in the store and write nothing there. If memory is on, read
   me.md in the store if it exists. Do this automatically, with no
   instruction from me.
6. After setup, follow the read, propose, and decide loop in
   https://github.com/block/me.md/blob/main/PROTOCOL.md, and use the
   file formats in
   https://github.com/block/me.md/blob/main/STORE.md.
   Inferred changes go in proposals/ in the store. Before you
   propose, read the refused proposals, and never propose their
   words again. I accept, edit, or refuse each proposal. You may
   apply an edit I explicitly request or a proposal I accept. Record
   each change in journal.md, in the form STORE.md gives. Accepting a
   proposal records two lines: my decision and the change. A refused
   proposal stays in proposals/, marked refused.
   My refusal stays in effect. My silence is not acceptance.
```

That one message is the full setup. After you send it, you have no more setup to do. The agent creates the file, you answer its questions, and the agent saves only the words you approve. After setup, the agent serves the store with the full loop in [PROTOCOL.md](./PROTOCOL.md).

## Check that it works

Close the conversation. Start a new session with the same agent, or with a different agent that serves the store, and ask: "What do you know about me from my me.md?" It answers from your file, without you pointing it there. If it does not, the standing rule from step 5 did not stick. Use the bridge line below, or the paste-in block in [PROTOCOL.md](./PROTOCOL.md).

To check the rest of the loop, mention a preference twice without asking the agent to remember it. The agent should ask you about a new file in `proposals/` and change nothing else.

## After setup, the protocol operates without you

This rule is critical to the design: **the start of the protocol must not use the person's time or attention.** A conforming host finds the store and reads it at the start of each session, with no instruction from the person. You do not ask an agent to remember you. You do not repeat an instruction. A tool that needs a manual start in each session takes your attention, and the protocol exists to protect that attention. That is a conformance failure, not an inconvenience.

Some agents do not conform yet and cannot keep a standing instruction. For those agents, this one line is a temporary bridge:

```text
Check ~/.me/policy.json. If memory is on, read ~/.me/me.md before we start.
```

If you set `ME_HOME`, use that folder instead of `~/.me/`.

There is no import, no account, and no synchronization. The file is the integration. The bridge line is a temporary aid, not the design.

For a harness with an instruction surface — a system prompt, a rules file, custom instructions — [PROTOCOL.md](./PROTOCOL.md) has a paste-in block that serves the full loop, not only the read.

## The rules the agent must follow

Any agent that serves your file must obey the protocol:

- Your file starts empty. The agent supplies no template and no default persona.
- The agent writes only what you approve, in your words.
- The agent that finds something new worth keeping can only ask. Your refusal stays in effect.
- You can read, change, or delete any line, at any time, with a text editor — or tell any agent to do it for you.
- Deleted content stays deleted.

The full rules for hosts are in [HOST.md](./HOST.md). The full commitments to the person are in [SOVEREIGNTY.md](./SOVEREIGNTY.md).

## Why this exists

Agents become genuinely useful when they know you. Most products keep that knowledge as their property. This protocol keeps it as yours — so the more agents help you, the more capable you become, and the freer you stay to change tools, change direction, and spend your attention on what matters most to you.
