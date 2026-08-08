# Briefing contract

**Status:** Draft protocol contract. This is the protocol's main output.

The reason `me.md` exists is to help a person keep up with agents. The briefing is how. It turns everything that moved into a person-shaped read: **what moved, where the pull is, what is missing, and what to do next.**

Memory makes the briefing possible. The briefing is what memory is for.

## Definitions

- **Briefing** — a read of activity since the person's last read, composed against their aims, watches, and workstreams. Produced on request or on a schedule the person set.
- **Aim** — a durable statement of what matters to the person now. Person-authored or person-approved, like all durable context.
- **Watch** — a standing question the person wants answered when the answer changes. "Tell me when the migration decision moves." A watch is not memory of the person; it is an instruction from the person.
- **Workstream** — a body of work the person is part of. Follows the project scoping rule: it stays with the work, not the person.
- **Signal** — one observed movement relevant to an aim, watch, or workstream.
- **Coverage** — the honest statement of what was actually read to produce the briefing, and at what depth.

## What a conforming briefing contains

### 1. What moved

Signals since the last briefing, each tied to a source the person could check themselves. New is distinguished from unchanged. A signal names its subject plainly: a commit, a meeting note, a review, a message.

### 2. Where the pull is

What is waiting on the person, and what of the person's work is waiting on others. Both directions. Work going unseen is a pull too — the briefing may suggest who could be looped in, drawn from the people the person actually works with.

### 3. What is missing

Dropped threads, unanswered obligations, and — most importantly — the read's own blind spots. If a source was scanned shallowly, the briefing says so and names what kind of thing could hide there. Absence of evidence is reported as absence of evidence, never as evidence of absence.

### 4. What to do next

One move, not a list of twenty. The briefing may rank; the person decides. A briefing that ends in a task list has become a manager. A briefing that ends in a suggested move has remained an advocate.

### 5. Coverage receipt

Every briefing ends with what was read, what was unavailable, and a confidence statement. A briefing without a coverage receipt is an assertion, not a read.

## Rules

- **Composed against the person's aims, not the org's.** Two people watching the same activity receive different briefings, because their aims differ. The org-shaped view already exists everywhere else.
- **Read-only by default.** Producing a briefing requires no writes. Nothing observed while composing becomes durable memory — an observation surfaced in a briefing is still only a candidate, subject to the proposal path.
- **Watches are instructions, not inferences.** A host must not create watches from observed behavior. The person sets them, sees them, and can delete them like any other line in their files.
- **The briefing states its own limits.** Shallow scans, skipped sources, and low-confidence readings are named in the read itself, not hidden in a log.
- **Honest tone, no theater.** The briefing does not celebrate, guilt, or nag. It reports, suggests one move, and stops. The [system's voice principles](./EXPRESSION.md#the-systems-voice) apply in full.
- **The person's response is theirs to give.** A host may let the person record what they did with a briefing, so future reads improve. Recording is optional, person-initiated, and inspectable like everything else. Silence is a valid response and must not degrade future briefings.

## What this contract does not specify

- Sources, connectors, or scan mechanics — application-specific.
- Schedule, delivery surface, or format — a briefing may be text in a terminal, a card in an app, or a spoken summary.
- Personality — a host may give the briefing a voice, but personality decorates true facts only; it never supplies them.
- Ranking algorithms — how a host decides "the one move" is an implementation choice, judged by whether the person recognizes the move as theirs.

## Failure modes

- **The feed:** reporting everything that happened instead of what matters to this person. Volume is the problem the briefing exists to solve.
- **The manager:** converting the read into assignments, scores, or completion tracking.
- **The inference engine:** deriving aims and watches from behavior instead of taking them from the person.
- **The confident blank:** presenting a shallow scan as a complete read. The coverage receipt exists to make this impossible.
- **Silent memory:** letting briefing observations leak into durable context without the proposal path.
