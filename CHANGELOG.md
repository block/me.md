# Changelog

Each release is a tag of the form `vX.Y.Z`. A host that claims conformance names the release it follows, for example "conforms to me.md v0.1.0". Until version 1.0, any release can change the normative drafts.

Each release lists changes for the person and for hosts. The release page includes one file that contains all normative drafts at that tag.

## 0.1.0 — Unreleased

The first tagged draft. It records the protocol as it is now, so that hosts and experiments have a version to name.

### For the person

- One setup instruction ([SETUP.md](./SETUP.md)). Give it to any agent that can write a file. After setup, the agent reads `~/.me/me.md` at the start of each session with no instruction from you.
- Your store is plain files in `~/.me/`: `me.md`, `topics/`, `projects/`, `proposals/`, and `policy.json`. It starts empty.
- Agents can only propose. You accept, edit, or refuse. A refusal stays in effect. Silence is not acceptance.
- The commitments to you are in [SOVEREIGNTY.md](./SOVEREIGNTY.md).

### For hosts

- [PROTOCOL.md](./PROTOCOL.md): the store layout, the loop (mount, recall, propose, decide), and a paste-in block for a harness that does not conform natively.
- [HOST.md](./HOST.md): the conformance rules for mounting, recall, writing, provenance, revocation, and security, with eight black-box tests.
- [BRIEFING.md](./BRIEFING.md): what a conforming briefing contains.

### Not decided in this release

These are under test, not standardized. See [SOVEREIGNTY.md](./SOVEREIGNTY.md#what-remains-under-test).

- the exact `policy.json` schema
- whether `~/.me/` is the right default location, and whether Markdown is the right primary format
- provenance, history, and undo storage
- protection of context at rest and in transit, and synchronization between devices
- the minimum useful conformance surface
