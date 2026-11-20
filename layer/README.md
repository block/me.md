# The thou layer for Claude Code

Put it on once. From then on, every Claude Code session starts from your own words about yourself, and nothing new is kept about you unless you say yes.

**Status:** Experimental, like the protocol. The layer makes no conformance claim. [What it has passed](#what-it-has-passed) lists the tests it has run.

## What changes when you put it on

- **Every session starts from your words.** At the start of each session, the layer reads your `me.md` and gives it to Claude as information about you, not as instructions. What you say in the session wins over it. You don't have to ask.
- **One switch turns it off.** Write `{"state": "off"}` in `policy.json` in your store, or ask Claude to turn your memory off. From then on Claude gets nothing from your store. The only tools left show where your store is and turn memory back on.
- **Claude reaches your files through the layer.** Claude Code's own file and search tools, and shell commands that point into your store, are stopped at its edge. The layer checks the switch before every read and write, and keeps the journal. To make that edge a wall for the shell too, [turn on the sandbox](#make-the-fence-a-wall).
- **What Claude notices, it can only propose.** When Claude notices something you may want kept, it writes a proposal and tells you. Nothing changes until you accept it. If you refuse, no agent that follows the protocol proposes those words again.
- **Say "remember" or "forget", and it's done.** When you ask in your own words, such as "Remember that Mondays are soccer" or "Forget that my test is in March", the layer saves or removes the words at once and Claude tells you the receipt. The layer checks that your latest message asks for it, in words you typed. Words you pasted, quoted or forwarded from someone else, and words from a web page or an email Claude read, don't count: then nothing changes, and Claude asks you.
- **You approve every other change, with its words in front of you.** Before your store is started, a proposal is accepted or refused, words are changed, or memory is turned on or off, Claude Code asks you. The prompt shows the words, and for a proposal, the file they go to. It asks every time, even in auto mode or with permission prompts turned off, and it has no "don't ask again".
- **You see all of what you approve.** The layer refuses words with characters you can't see, such as zero-width spaces or hidden tag characters, and words too long to fit in one prompt.
- **Every change the layer makes leaves a receipt.** Each one gets a line in `journal.md`: what changed, when, and on whose say.

## Put it on

You need Claude Code v2.1.295 or later, and Python 3.9 or newer on macOS or Linux. In Claude Code, run:

```text
/plugin marketplace add block/thou
/plugin install thou@thou
```

Then start a new session.

Your store is the folder `~/.me/`, or the folder named in the `ME_HOME` environment variable. To try the layer without touching your own store, start Claude Code with a test folder:

```bash
ME_HOME=/tmp/thou-test claude
```

To try it from a copy of this repository without installing it, run `claude --plugin-dir layer`.

### If you don't have a me.md yet

Say "Set up my me.md." Claude asks what it should say and shows you the text. When you say yes, Claude Code asks you to approve it. The layer then creates your `me.md` with exactly those words. Only your user account can read the file, and if the layer creates the folder too, only your account can open it. There is no template. The file holds only what you say.

### Make the fence a wall

The layer's fence reads paths and commands, so a shell command that builds the path in some other way gets past it. Claude Code's sandbox closes that gap at the operating-system level. Add this to `~/.claude/settings.json`, with your `ME_HOME` folder in place of `~/.me` if you set one:

```json
{
  "sandbox": {
    "enabled": true,
    "allowUnsandboxedCommands": false,
    "filesystem": { "denyRead": ["~/.me"], "denyWrite": ["~/.me"] }
  },
  "permissions": { "deny": ["Read(~/.me/**)", "Edit(~/.me/**)"] }
}
```

The sandbox stops every shell command Claude runs from reading or writing the store, and the deny rules stop Claude Code's own file tools. The layer keeps working, because its hooks and tools don't run in the sandbox. The sandbox runs on macOS, Linux and WSL2; on Linux it needs `bubblewrap` and `socat`. See [Claude Code's sandboxing guide](https://code.claude.com/docs/en/sandboxing).

## Living with it

You don't need to do anything. These are things you can say:

- "What's waiting for me?" Claude lists the proposals that wait for your decision.
- "Accept it." "Refuse it." "Change it to …"
- "Remember that Mondays are soccer." The words are saved at once, and the journal records that you asked. Claude tells you: Saved: "Mondays are soccer". Every agent that uses your thou store will know it.
- "Forget that my test is in March." Claude removes those words, even from the middle of a line, and tells you what it can't delete. Name what to forget in the same message: "forget that" alone doesn't say what. If you asked about words you pasted or quoted, Claude asks you first, and a "yes" in your next message is enough.
- "Turn my memory off."

You can also open the files in any text editor. They are yours.

## Take it off

- **To pause it**, turn memory off. Your files stay as they are.
- **To remove it**, run `/plugin uninstall thou@thou`. Your files stay in your store, where you and any other agent that follows the protocol can read them. There is nothing to export.

## What it can't do

- **It covers Claude Code, and nothing else.** Another agent follows your `policy.json` only if it honors the protocol. The switch is a request those agents honor, not a lock.
- **Claude Code's own memory is separate.** Claude Code can keep its own notes about you, called auto memory, outside your store. The layer asks Claude to propose what it learns about you instead, but only by instruction. To keep what Claude remembers about you in one place, turn auto memory off: open `/memory` and use the auto memory toggle, or set `CLAUDE_CODE_DISABLE_AUTO_MEMORY=1`.
- **The model still decides some things.** It decides whether a topic or project is relevant, whether something is worth proposing, and whether it treats what it reads as information. The layer can't make those happen in code.
- **What Claude reads leaves your computer.** While memory is on, `me.md`, and anything Claude recalls, goes to the model provider with the rest of the session. Claude Code also saves session transcripts on your computer. Forgetting a line doesn't change those copies. Keep out of `me.md` anything you would not tell every agent you use.
- **Without the sandbox, the fence is not a wall.** It stops file tools that point into your store, searches that would walk into it, and shell commands that name it in the common ways: by its path, by a path relative to the working folder or to a `cd` or `-C` anywhere in the command, or by a pattern, through symbolic links too. It also stops commands that run the layer's own code, which would write as if you had asked. A command that builds the path some other way, such as in a variable or a script, gets through. With [the sandbox settings](#make-the-fence-a-wall), Claude Code's shell can't reach the store either. Any other program that runs as you can still read the files.
- **Approval needs a person.** In a run with no one to ask, such as `claude -p`, starting, deciding, editing and switching are refused. Remember and forget work there too, because they rest on your own words in the message, not on an approval. An app built on the Claude Agent SDK shows the approval in its own interface.
- **Your own words are checked, not their meaning.** The layer checks that your latest message asks to remember or forget, in words you typed, and that the change uses those words: all of them to remember, and all but one at most to forget, so "forget about Mochi" can take the line "I have a cat called Mochi." It can't tell whether you meant it. A message you type on someone else's behalf, without quotation marks or a "says", counts as yours.
- **Read what you approve.** A web page, an email or a tool's output that Claude read can shape what it proposes, and an accepted line in `me.md` reaches every agent you use. The layer makes sure you can see every character of what you approve, not that it is true. A long change can run past the top of a small window: scroll up, or make the window taller, before you answer.
- **Hooks and apps you install run as you.** In the checks, no allow rule or hook could answer the approval prompt for you. But a hook, a plugin or an app built on the Claude Agent SDK can change your files directly, like any program you run.
- **Other limits.** It is not tested on Windows. The store lock protects one computer, not a sync folder. A program that swaps a folder in your store for a symbolic link during a call could redirect one read or write. The layer doesn't write briefings.

## How it works

The layer is this folder: a Claude Code plugin in Python, with only the standard library. It has three parts, and all three run the same code in `thou_host/`, which follows [STORE.md](../STORE.md) v0.1 at the Steward level of [HOST.md](../HOST.md#conformance-levels).

- **A session-start hook** (`thou_hooks.py session-start`). It reads `policy.json` alone, then `me.md`, and adds `me.md` to the session as context. It adds nothing while memory is off or there is no store (H1.1, H1.5).
- **A prompt hook** (`thou_hooks.py user-prompt`). While memory is on, it keeps a copy of your latest message for `remember` and `forget` to check, in a file only your account can read: `~/.local/state/thou/said/`, or `$XDG_STATE_HOME/thou/said/`, or the folder in `THOU_SAID_DIR`. Each message replaces the one before. The copy goes at the end of the session, and a `forget` takes the sentences that held its words out of it. The hook never stops a message.
- **An MCP server** (`thou_mcp.py`), named `thou`. Its tools are `mount`, `where`, `list`, `recall`, `pending`, `propose`, `revise`, `decide`, `edit`, `remember`, `forget`, `policy` and `start`. In Claude Code they are named `mcp__plugin_thou_thou__<tool>`.
  - It reads `policy.json` before every call, keeps every path inside the store, takes the store lock, and writes the journal.
  - While memory is off, it offers only `where` and `policy`. While there is no store, it offers `where`, `policy` and `start`.
  - `remember` and `forget` act on your own words. Each call carries a `quote` of your latest message. The server makes the change only if the quote is in that message as words you wrote, not in a fenced block, a line after `>`, a line that starts with someone's name and a colon, quotation marks that hold an instruction, or the rest of a sentence after "said", "wrote", "sent" and the like. The sentence around it must ask to remember or forget, and the change must use your words. Otherwise nothing changes, and the answer tells Claude to ask you. For words you pasted or quoted, or a change that goes past the words you named, Claude may ask you, and a bare "yes" in your very next message confirms. A whole `me.md` can't be forgotten this way. The journal says `authority: person direct`, and Claude tells you the receipt.
  - `start`, `decide`, `edit` and `policy` act on your say-so too, and their journal entries say `authority: person direct`. Each carries `_meta["anthropic/requiresUserInteraction"]`, so Claude Code asks you before every call, in every permission mode, and shows the call's arguments. The server offers them only because the plugin tells it that Claude Code asks, by setting `THOU_CLIENT_ASKS=1` for it. Each of those calls carries the words it writes. `decide` carries the proposal's target and words, and the server decides nothing if they differ from the proposal on disk in any way the prompt would show.
  - No call writes words with characters a person can't see, or more than 2,000 characters or 30 lines in one change. A pending proposal with hidden characters can be refused or revised, never accepted. When a file already holds such characters, the server leaves them out of what Claude reads, and says so.
  - `start` creates `me.md` only when there is none, never from a template, and journals it as `created me.md` (S1.3, [SETUP.md](../SETUP.md)).
- **A pre-tool hook** (`thou_hooks.py pre-tool-use`). It stops Claude Code's file tools, searches that start above the store, and shell commands that point into it, from reaching the store or the copy of your latest message. If the hook fails, can't run or runs out of time, it stops the call.

The MCP server also works on its own, in any agent that speaks MCP: `python3 layer/thou_mcp.py`. There, it mounts only if the agent's model follows the server's instructions. And the server can't tell whether that agent asks you before a call, so it takes nothing on your say: it reads, proposes, and turns memory off when asked. It doesn't start, decide, edit or turn memory on. It remembers and forgets only if something runs `thou_hooks.py user-prompt` with each of your messages, as Claude Code's hook does; without that, it has no message to check, so it changes nothing and asks you. Turning memory off is journaled as your change, because the protocol records it that way, but there the journal can't tell whether you or the agent asked for it. If the agent asks you before every call to those tools and shows you the call, set `THOU_CLIENT_ASKS=1` in its settings for the server, and they're offered there too. The journal then says each of those changes was yours, so set it only for an agent that asks.

## What it has passed

- **Unit tests**, on temporary stores only: `python3 -m unittest discover -s layer/tests -p 'test_*.py'`. CI runs them on macOS and Linux.
- **Model-level checks**: `python3 layer/tests/claude_code_e2e.py`. It runs real Claude Code sessions with the layer on temporary stores, for the parts of tests T2, T3, T4, T7 and T8 in [HOST.md](../HOST.md#black-box-conformance) that need a model. It also checks that:
  - in bypass mode, with no one to approve, nothing is started, decided, edited or switched;
  - "remember" and "forget" in your own words land at once, and the same words pasted after `>`, or reported from someone else, change nothing;
  - an allow rule, and hooks that answer "allow", don't approve a change for you;
  - with the sandbox settings above and the layer's own fence taken out, the shell and the Read tool can't reach the store, and the thou tools still can.

  It calls a model, costs tokens, and varies from run to run, so CI doesn't run it.

Passing these is not a conformance claim. A claim needs every test for the level, including the review items in [TRACEABILITY.md](../conformance/TRACEABILITY.md).
