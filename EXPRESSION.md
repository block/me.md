# Expression and admission

**Status:** Working language principles and application-layer hypothesis. Non-normative.

Durable context begins as language.

The sentence a system keeps about a person is not a cosmetic detail. It can shape future interactions, travel across interfaces, and slowly become a description of who the system thinks the person is. Linguistic clarity is therefore part of sovereignty.

A durable context entry should be useful to an agent while remaining recognizable, bounded, and editable by the person it describes.

## The application responsibility: a context composer

Between conversation and durable context, an application may provide a **context composer**.

```text
conversation or observation
          ↓
    context composer
          ↓
     admission preview
          ↓
      person decides
          ↓
 canonical context entry
          ↓
 agent-specific projection
```

The context composer is a responsibility, not a required component or interface. It may appear as a chat card, settings panel, editor, command-line interaction, or another surface.

Its job is to help the person answer:

- What exactly would be kept?
- Is this a fact, preference, default, boundary, or temporary condition?
- Where does it apply?
- Which authorized agents or interfaces may use it?
- Did the system preserve the person's meaning?

A composer may clarify and shorten language. It must not quietly broaden, intensify, or reinterpret it.

## Canonical expression and projection

The **canonical expression** is the human-understandable statement governed by the person.

An implementation may render that statement differently for a particular agent. That rendering is a **projection**, not a new source of truth.

For example:

```text
Canonical expression:
For work emails, I prefer a direct, understated tone.

Agent projection:
For work emails, use a direct, understated tone.
```

A projection must preserve the canonical statement's meaning, scope, strength, and conditions. It must not turn a preference into a rule, a rule into permission, or a scoped statement into a global one.

The person should be able to inspect the canonical expression. When it matters, they should also be able to understand how an implementation projected it.

## Principles for sovereign expression

### Recognizable as the person's own

Use language the person would plausibly recognize and choose.

Prefer first-person phrasing or a direct instruction:

- “I prefer concise explanations.”
- “By default, lead with the answer.”
- “Always ask before sending something as me.”

Avoid writing a profile from the outside:

- “The user is impatient.”
- “The user has low tolerance for detail.”
- “The user is highly risk-averse.”

The goal is not to sound clinical or authoritative. It is to preserve meaning in language the person can own.

### One meaningful claim

A context entry should usually express one fact, preference, default, boundary, or condition.

Avoid bundling unrelated claims:

> I like concise answers, prefer morning meetings, use metric units, and dislike phone calls.

Separate entries are easier to inspect, scope, correct, forget, and project safely.

### The narrowest useful scope

State where a preference or rule applies.

Prefer:

- “For work emails, keep the tone direct and understated.”
- “When reviewing code, start with the largest risk.”
- “For Project Phoenix, include rollback detail in migration plans.”

Over:

- “Keep everything direct.”
- “Always focus on risk.”
- “I need detailed plans.”

A statement should not become global merely because global wording is shorter.

### The right strength

Words such as “prefer,” “usually,” “by default,” “always,” and “never” carry different authority.

Use the weakest wording that accurately preserves the person's intent:

- **Preference:** “I prefer…”
- **Default:** “By default…”
- **Usual pattern:** “Usually…”
- **Boundary:** “Always ask before…” or “Do not…”
- **Temporary condition:** “Until September 30…”

Do not introduce “always” or “never” unless the person explicitly chose that strength. A repeated behavior is not automatically a boundary.

### Conditions and exceptions stay visible

If a statement is true only under certain conditions, include them.

Prefer:

> Keep answers concise by default; expand when I ask for detail.

Over:

> Keep answers concise.

Exceptions are part of the meaning, not optional detail to remove during summarization.

### Useful behavior before presumed traits

When the goal is to help a future agent, describe the useful behavior or concrete fact rather than assigning a trait, motive, or emotional state.

| Avoid | Prefer as a candidate expression |
| --- | --- |
| “The user is impatient.” | “By default, lead with the answer. Expand when asked.” |
| “The user is risk-averse.” | “For migrations, include a rollback path before recommending execution.” |
| “The user dislikes enthusiasm.” | “For work messages, keep the tone direct and understated.” |
| “The user values family time.” | “Keep Monday evenings free when suggesting meeting times.” |
| “The user is disorganized.” | Do not create durable context from this judgment. |

The preferred wording is still only a candidate until the person authors or accepts it.

### Identity belongs to the person

Do not infer identity from behavior.

If a person explicitly says, “I am vegetarian,” that statement may be preserved in their own words. If an agent merely observes several meat-free choices, it should not convert that pattern into an identity claim.

A narrower proposal such as “For meal suggestions, avoid meat by default” may be more appropriate, but it still requires the person's decision before becoming durable.

The same restraint applies to health, emotion, politics, religion, relationships, ability, personality, and other sensitive or identity-bearing claims.

### Plain and concise

Prefer ordinary language over taxonomies, scores, or model terminology.

A context entry should usually fit in one clear sentence. Concision must not remove scope, conditions, uncertainty, or an exception that changes the meaning.

Structured metadata may accompany the sentence, but it must not replace the human-readable expression as the source the person governs.

### Origin and uncertainty remain visible

The statement and its origin are different things.

An admission interface should make clear whether the entry was:

- written directly by the person;
- explicitly requested by the person;
- proposed by an agent;
- imported from another source.

An agent-proposed sentence should not gain authority merely because it is written confidently. If the meaning is uncertain, the system should ask, propose narrower language, or leave it in the current session rather than manufacture certainty.

## Admission paths

Different origins require different application behavior.

### Direct authorship

When the person writes or edits the canonical expression themselves, their wording is authoritative.

An interface may offer clarity suggestions, but it must not silently replace the person's text.

### Explicit request to record

When the person explicitly asks to remember an exact statement, the application may record it and show the result without asking them to approve the same instruction twice.

For example:

> Remember this: Always ask before sending something as me.

The saved expression can be echoed with an edit or undo affordance.

An explicit request to remember does **not** authorize a material reinterpretation. If the application wants to paraphrase, broaden the audience, change the strength, infer a category, or alter the scope, it should show the proposed expression before admission.

### Agent proposal

When an agent notices something that may be useful later, it may propose one candidate expression.

The proposal must show the exact statement that would become durable, along with enough context for the person to understand its scope and origin. The proposal must not affect future sessions before acceptance.

The person may accept, edit, defer, or dismiss it.

### Import

Imported context should remain attributable to its source and should not silently acquire broader scope or stronger authority during import.

A person should be able to review what will be imported before it becomes active durable context.

## Admission preview

The exact interface is under test. A useful admission preview might show:

```text
Remember this?

“By default, when reviewing code, start with the largest risk.
Add detail after.”

Applies to: authorized agent sessions, when reviewing code
Strength: default
Origin: suggested from this conversation

[Edit]  [Remember]  [Not now]
```

The labels are illustrative, not a required schema.

The preview should make the following visible:

- the exact durable expression;
- its scope or condition;
- its strength;
- its intended audience;
- its origin;
- any expiration or review date.

A friendly summary must not hide a broader machine-readable interpretation.

## The person's edit wins

If the person revises a proposal, the revised expression becomes the candidate for admission.

The system must not retain the agent's original wording as a competing active statement. Future projections should be regenerated from the person-governed expression.

An application may retain provenance that an edit occurred, but provenance is not permission to keep using superseded meaning.

## Expression failure modes

Common failures include:

- **Profile language:** describing the person from outside rather than preserving their words or useful instructions.
- **Scope laundering:** turning a statement about one task, topic, or project into a global preference.
- **Absolutizing:** replacing “usually” or “prefer” with “always” or “never.”
- **Bundling:** combining unrelated claims into one entry.
- **Motive inference:** converting an action into a claim about values, intent, emotion, or character.
- **Identity inference:** converting repeated behavior into a sensitive or identity-bearing label.
- **Paraphrase drift:** changing meaning while presenting the result as a harmless rewrite.
- **Projection drift:** giving an agent a stronger or broader instruction than the canonical expression supports.
- **Hidden interpretation:** showing friendly prose while storing additional labels, scores, or rules the person cannot inspect.

## What this document does not standardize

This document does not define:

- a context-entry schema;
- required kinds or strength fields;
- a storage format or filesystem path;
- API or tool names;
- a particular admission card, settings view, editor, or CLI;
- a controlled vocabulary for identity or sensitive data;
- model prompts or projection syntax;
- conformance requirements.

These principles are a working application-layer hypothesis to test through experiments and independent implementations.

## Questions still under test

- Do people prefer first-person statements, direct instructions, or a mixture?
- Which labels for strength and scope are understandable without feeling bureaucratic?
- How much rewriting is helpful before it feels like reinterpretation?
- When should an application preserve exact wording even if it is longer or less polished?
- Does showing origin and audience increase trust or add noise?
- What explanation is needed when canonical expression and agent projection differ?
- Which expression rules should eventually become conformance requirements?
