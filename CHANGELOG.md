# Changelog

Each release is a tag of the form `vX.Y.Z`. A host that claims conformance names the release it follows, for example "conforms to me.md v0.1.0". Until version 1.0, any release can change the normative drafts.

Each release lists changes for the person and for hosts. Read a release against the documents at its tag, not the changing main branch.

To publish: merge the reviewed changes and dated changelog entry into main, then use GitHub’s Releases page to create a tag at that commit and write the release notes. Mark experimental releases as pre-releases. Share the specific release URL or the Releases list; pre-releases do not appear at `releases/latest`.

## 0.1.0 — Unreleased

The first tagged draft. It gives hosts and experiments a version to name. It also fixes the file formats, so that two hosts that have never met read and write the same store the same way. Some formats change from the drafts on main before this release: see [Upgrading a store from earlier drafts](#upgrading-a-store-from-earlier-drafts).

### For the person

- One setup instruction ([SETUP.md](./SETUP.md)). Give it to any agent that can read and write files on your computer. After setup, the agent reads `~/.me/me.md` at the start of each session with no instruction from you. SETUP.md includes a way to check that it works.
- Your store is plain files in `~/.me/` (or `$ME_HOME`): `me.md`, `watches.md`, `topics/`, `projects/`, `proposals/`, `journal.md`, and `policy.json`. It starts empty. Memory starts when `me.md` exists.
- Every agent you use reads `me.md` in every session. Setup tells you this.
- `{"state": "off"}` in `policy.json` turns memory off in every conforming host. A policy file that is unreadable, is not valid JSON, or names a field twice also means off. Extra fields in the file do not turn memory off. You can ask any host at the Steward level to turn memory off or on, even while memory is off, and the change is journaled. You can also edit the file yourself.
- A refusal is kept as a proposal whose status is `refused`, so no conforming host proposes the same words again, for any file. Delete the file to end the refusal.
- Every change leaves an entry in `journal.md`, readable by any host and by you. Accepting a proposal leaves two: your decision and the change.
- Any agent on the same computer can serve the store. Syncing between devices is not defined yet.
- Agent-inferred changes require a proposal. You accept, edit, or refuse each proposal, or ask for an edit directly. A refusal stays in effect. Silence is not acceptance. A proposal that would add a rule about how agents act is shown to you on its own.
- Your aims live in `me.md`. Your watches live in `watches.md`, one per list item, in your words. Only you add them. Hosts read them only for a briefing.
- The commitments to you are in [SOVEREIGNTY.md](./SOVEREIGNTY.md).

### For hosts

- [STORE.md](./STORE.md) (new): the file formats. Store presence; layout and names; `policy.json` with an optional `spec` version; proposal files with front matter, read only from the front matter; the exact bytes of an append; one journal grammar; and rules for writing safely when two hosts share a store, with a store lock and a fixed order for accepting a proposal.
- [HOST.md](./HOST.md): the conformance rules for mounting, recall, writing, provenance, revocation, security, and briefings. Each requirement has an identifier. Four conformance levels: Reader, Proposer, Steward, and Briefer, named on every requirement. Eighteen black-box tests, each assigned to a level. A claim names the release and the level, and says "by instruction" when the off switch depends on the model obeying.
- [BRIEFING.md](./BRIEFING.md): what a conforming briefing contains, and where its inputs live in the store. A host at the Briefer level produces one when the person asks. Scheduled briefings are optional and run only on a schedule the person set. Briefing sources are untrusted input.
- [PROTOCOL.md](./PROTOCOL.md): the store layout, the loop (mount, recall, propose, decide), and a paste-in block that matches STORE.md. A harness that uses only the paste-in block is an *instructed host*.
- [me-lint](./tools/README.md) (new): checks that a store follows STORE.md, with synthetic fixture stores. It checks files, not host behavior.
- HOST.md, STORE.md, and BRIEFING.md use the BCP 14 key words. README.md says which document wins when two disagree.

### Upgrading a store from earlier drafts

A store made with the drafts on main before this release can need these changes. Make them by hand, or ask a host to make them as direct edits.

- **Watches.** Move the lines under a `## Watches` heading in `me.md` to `watches.md`, one list item per watch. A v0.1 host reads watches only from `watches.md`.
- **Proposals.** Replace a `Status:` line with front matter that starts on line 1 ([STORE.md §6](./STORE.md#6-proposals)). A v0.1 host treats a proposal without valid front matter as invalid. It never applies it, and treats it as refused, so it never proposes those words again.
- **Journal.** Old lines stay as they are. The journal is append-only. New entries use the grammar in [STORE.md §7](./STORE.md#7-journal). me-lint reports old lines that start with `- ` and do not match.
- **Policy.** No change is needed. `{"state": "on"}` still means on. A `policy.json` with extra fields now means on, where the earlier drafts meant off.

### Not decided in this release

These are under test, not standardized. See [SOVEREIGNTY.md](./SOVEREIGNTY.md#what-remains-under-test).

- whether Markdown is the right primary format
- changing or removing text through a proposal (this release defines additions only)
- detecting edits made outside any host
- undo, and how long the journal and refused proposals are kept
- scope labels inside files (use a separate `ME_HOME` for each scope)
- protection of context in transit, encrypted files, and synchronization between devices
- whether the four conformance levels are the right cut
- where "since the last read" is tracked, so that two hosts give the same briefing window
