# Experiments

`me.md` is being developed through small, reversible experiments.

The goal is not to turn the first useful interface into a standard. It is to learn which human capabilities matter, which boundaries must hold, and which technical choices can remain replaceable.

Experiments are non-normative. They produce evidence for the protocol; they do not define the protocol by themselves.

## One human question at a time

Each experiment should test the smallest useful question it can.

A broad "memory experience" can combine inspection, editing, recall, proposals, approvals, provenance, revocation, and portability. If all of those arrive together, it becomes difficult to know which part created value, confusion, or discomfort.

Prefer a sequence such as:

1. Can a person inspect and edit context that an agent later follows?
2. Can an agent recall one relevant topic without seeing unrelated context?
3. When does an agent's suggestion to remember something feel useful rather than intrusive?
4. Does disabling or forgetting context reliably remove its influence?
5. Can a second trusted interface use the same source without widening access unexpectedly?

## Human capabilities

The project uses the following interface-neutral verbs to describe experiments:

| Capability | What the person can do |
| --- | --- |
| **Inspect** | See what durable context exists and where it applies |
| **Author** | Add or directly edit their own context |
| **Recall** | Let an agent retrieve context relevant to the current task |
| **Propose** | Receive a suggestion for new durable context without saving it automatically |
| **Decide** | Approve, revise, defer, or dismiss a proposal |
| **Explain** | Understand what context influenced an outcome and where it came from |
| **Revoke** | Disable, forget, or delete context and stop its use |
| **Move** | Export or use context through another trusted interface |

These are human capabilities, not API names or user-interface requirements.

## Interfaces are experimental

The same experiment may be implemented through a settings panel, a text editor, a command line, a chat interaction, or another interface.

An experiment should specify what the person must be able to accomplish while leaving the interface replaceable. Interface-specific findings are still useful, but they should be reported separately from claims about the protocol.

For example:

- "People could not find the edit control" is an interface finding.
- "People expected editing the visible source to change future agent behavior" may be a protocol finding.

## Experiment lifecycle

Experiments use four lightweight states:

- **Proposed** — the question and smallest test are documented.
- **Running** — one or more implementations are gathering evidence.
- **Learned** — observations and implications have been recorded.
- **Retired** — the experiment is no longer useful, safe, or relevant.

A learned experiment does not automatically become a protocol requirement. A separate protocol change should explain which evidence supports standardization.

## Evidence and reporting

Useful evidence may include:

- whether people can explain what is stored and who can use it;
- whether they can predict when context will be applied;
- whether the context reduces repeated explanation;
- whether editing or removing context changes subsequent behavior;
- where the experience feels helpful, surprising, intrusive, or unclear;
- implementation failures that weaken a sovereignty commitment.

Findings should distinguish:

1. **Observation** — what happened;
2. **Interpretation** — what we think it means;
3. **Protocol implication** — what, if anything, may deserve a shared rule.

## Privacy boundary

The experiment design can be public. A person's context is not experiment data by default.

Public findings should use synthetic examples, aggregate observations, or carefully redacted interaction patterns. Do not publish raw personal context, transcripts, topic names, prompts, or provenance records without explicit and informed permission.

Experiments should prefer non-sensitive test context when the human question does not require sensitive information.

## Sovereignty review

Every experiment must identify:

- what context is read, written, derived, retained, or exposed;
- who can access it;
- how the person can inspect and correct it;
- how the experiment is disabled or reversed;
- what would cause the experiment to stop;
- which commitments in [`SOVEREIGNTY.md`](./SOVEREIGNTY.md) are at risk.

## Current experiments

- [0001 — Inspect, edit, and reuse context](./experiments/0001-inspect-edit-reuse.md)

Use the [experiment template](./experiments/TEMPLATE.md) to propose another small test.
