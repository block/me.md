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
5. At the start of our future sessions, read ~/.me/me.md before we work.
```

That one message is the full setup. The agent creates the file, you speak, and only your approved words are saved.

## Use it with every other agent

Once the file exists, this single line makes any other agent know you:

```text
Read ~/.me/me.md before we start.
```

No import, no account, no sync. The file is the integration.

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
