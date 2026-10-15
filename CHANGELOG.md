# Changelog

Each release is a tag of the form `vX.Y.Z`. A host that claims conformance names the release it follows, for example "conforms to me.md v0.1.0". Until version 1.0, any release can change the normative drafts.

Each release lists changes for the person and for hosts. Read a release against the documents at its tag, not the changing main branch.

To publish: merge the reviewed changes and dated changelog entry into main, then use GitHub’s Releases page to create a tag at that commit and write the release notes. Mark experimental releases as pre-releases. Share the specific release URL or the Releases list; pre-releases do not appear at `releases/latest`.

## 0.1.0 — Unreleased

The first tagged draft. It records the protocol as it is now, so that hosts and experiments have a version to name.

### For the person

- One setup instruction ([SETUP.md](./SETUP.md)). Give it to any agent that can write a file. After setup, the agent reads `~/.me/me.md` at the start of each session with no instruction from you.
- Your store is plain files in `~/.me/`: `me.md`, `topics/`, `projects/`, `proposals/`, and `policy.json`. It starts empty.
- Agent-inferred changes require a proposal. You may authorize an edit directly or approve a proposal. A refusal stays in effect. Silence is not acceptance.
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
