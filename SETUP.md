# Set up me.md with any agent

`me.md` is a new protocol for working with agents. It preserves human sovereignty: you own what agents know about you, you decide what they remember, and you can take it all with you. The purpose is not memory for its own sake. The purpose is to let you act on the things that matter most to you, with agents that know you well enough to help.

You do not install the protocol. You give one instruction to any agent that can write a file.

## The setup instruction

Copy this message and give it to any agent you trust — a chat app, a CLI, an IDE assistant:

```text
Set up my me.md memory. It is a protocol for working with agents that
preserves my ownership of what you know about me.

1. Create ~/.me/me.md if it does not exist. If it exists, read it and
   do not overwrite it.
2. Ask me, one question at a time:
   - a sentence or two about myself that I want every trusted agent
     to know
   - what matters most to me right now
   - how I like to work with agents
   - what you must always ask me before doing
3. Write only what I approve, in my own words. Do not add anything I
   did not say. Do not infer my traits, role, or interests.
4. Show me the finished file.
5. From now on, read ~/.me/me.md at the start of each session,
   automatically, with no instruction from me. If you have a
   persistent instruction, memory, or configuration mechanism,
   record this rule there now, so that the rule continues after
   this conversation.
```

That one message is the full setup. It is the last setup work that you do. The agent creates the file, you speak, and the agent saves only your approved words.

## After setup, the protocol operates without you

This rule is critical to the design: **the start of the protocol must not use the person's time or attention.** A conforming host finds `~/.me/` and reads it at the start of each session, with no instruction from the person. You do not ask an agent to remember you. You do not repeat an instruction. A tool that requires a manual start in each session uses the attention that this protocol exists to protect. That is a conformance failure, not an inconvenience.

Some agents do not conform yet and cannot keep a standing instruction. For those agents, this one line is a temporary bridge:

```text
Read ~/.me/me.md before we start.
```

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
