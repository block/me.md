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
5. From now on, read ~/.me/me.md at the start of every session,
   automatically, without my asking. If you have a persistent
   instruction, memory, or configuration mechanism, record this rule
   there now so it survives this conversation.
```

That one message is the full setup — and the last setup effort you spend. The agent creates the file, you speak, and only your approved words are saved.

## After setup, the protocol runs without you

This is critical to the design: **the start of the protocol must not cost the person time or attention.** A conforming host finds `~/.me/` and reads it at the start of every session on its own. You never ask to be remembered. You never repeat an instruction. If a tool makes you re-invoke your own memory by hand each session, it is spending the attention this protocol exists to protect — that is a conformance failure, not an inconvenience.

For an agent that does not yet conform and has no way to keep a standing instruction, this single line is the temporary bridge:

```text
Read ~/.me/me.md before we start.
```

No import, no account, no sync. The file is the integration — and the bridge line is a stopgap, not the design.

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
