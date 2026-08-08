# Experiment 0010 — Produce a person-shaped briefing

**Status:** Proposed
**Contract under test:** [BRIEFING.md](../BRIEFING.md)
**Non-normative.** This experiment supplies evidence for the protocol; it does not define it.

## Human question

Can a briefing composed from a person's own aims and watches help them keep up with agent-speed activity — without becoming a feed, a manager, or a surveillance report?

## Setup

- One synthetic context store with: two aims, two watches, and one workstream, all person-authored.
- A body of synthetic activity larger than a person would read directly: commits, messages, meeting notes, review requests — some relevant to the aims and watches, most not.
- One host that composes a briefing from the store and the activity. The store is read-only for the entire run.

## Procedure

1. **Compose.** Produce a briefing. Verify it contains the five parts: what moved, where the pull is, what is missing, what to do next (one move), and a coverage receipt.
2. **Person-shaped check.** Change one aim in the store. Recompose against identical activity. The briefing must change in the direction of the new aim.
3. **Blind-spot check.** Remove a source from the host's reach. The briefing must name the gap in its own text, not silently narrow.
4. **Read-only check.** Diff the store before and after every composition. Zero writes. Anything the host wants to keep must arrive as a proposal.
5. **Watch check.** Delete a watch from the store with a text editor. The next briefing must not report on it, and must not recreate it.
6. **One-move check.** The "what to do next" section contains one suggested move. The person's decision to ignore it must not appear in any future briefing as a reminder, escalation, or score.

## What would falsify the contract

- Two people with different aims receive materially the same briefing from the same activity.
- The briefing reports a shallow scan as a complete read.
- Composition writes anything durable without the proposal path.
- Watches appear that the person did not set.
- Ignored suggestions return as nags.

## What this deliberately does not test

Source connectors, scheduling, delivery surfaces, ranking quality, or personality. Those are application choices judged against the contract, not parts of it.
