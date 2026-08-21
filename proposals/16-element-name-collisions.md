*New 2026-08-21.* Written while building the 1.1.x schema proposal, which addresses one of
these and leaves the rest alone. Counts are from the 122-model corpus described in
`00-corpus-validation.md`.

---
# Element names that mean more than one thing

Four element names in XMILE carry more than one meaning. Item 3 covers the worst of them,
`<dimensions>`, and proposes a fix. This item is the survey, because taken together they
look less like four accidents than like a missing rule.

| Name | Meanings | Where the trouble is |
|---|---|---|
| `<dimensions>` | the whole-model list of dimension definitions; the per-variable list of dimension references | the specification |
| `<eqn>` | the equation; the *initial* equation; the initial equation for one array element; a units expression; a macro body | the specification |
| `<units>` | a variable's units expression; and, in 42 files, a unit definition | one vendor's older exports |
| `<element>` vs `<elem>` | a per-element equation; a member of a dimension | the specification |

## `<dimensions>`, two meanings

The whole-model element holds definitions — `<dim name="Region">` with `<elem>` children.
The per-variable element holds references — `<dim name="Region"/>`, name only. 4,554
occurrences in the corpus, 64 of them the whole-model kind and the rest per-variable.

The schema knows. The whole-model declaration is inlined inside `<xmile>` with the comment
*"need to inline dimensions element below to avoid conflict with dimensions element in
stock/flow/aux"* — a workaround for a collision the schema could not otherwise express.
Item 3 proposes `<model_dimensions>` for the whole-model list, following the pattern
`<model_units>` already sets, and records what the workaround costs. Renaming the
whole-model one moves 64 elements where renaming the per-variable one would move 4,490.

## `<eqn>`, five meanings

23,579 occurrences, and the meaning depends entirely on the parent:

| Parent | Occurrences | Meaning |
|---|---:|---|
| `<aux>`, `<flow>` | 9,607 | the equation |
| `<element>` | 11,632 | the equation for one array element |
| `<stock>` | 1,085 | the **initial** equation, not the equation |
| `<unit>` | 1,187 | a units expression, not a model equation |
| `<macro>` | 9 | the macro body, in terms of formal parameters |

Two of these are worth separating from the rest.

The **stock** case misleads. A reader who knows `<eqn>` on an `<aux>` is the equation will
read `<eqn>` on a `<stock>` the same way and be wrong: a stock's behaviour comes from its
flows, and its `<eqn>` sets only where it starts. `<initial>` would have said so.

The **macro** case is the only one that is ambiguous *within* its own context, and so the
only one a reader cannot resolve by looking at the parent. Everywhere else, knowing you
are inside a `<stock>` or a `<unit>` tells you what `<eqn>` means. Inside a `<macro>` it
does not: as item 12 sets out, §4.8 says `<eqn>` holds a "valid XMILE expression", and
every macro-with-variables we have seen instead writes a bare reference naming which
internal variable is the result — `<eqn>out</eqn>`. Both readings are permitted by the
text. That one wants a sentence in the specification whatever happens to the name.

The `<unit>` case is a different language entirely: a units expression, not a model
equation. Its identifiers resolve in the unit namespace, and a reader who evaluates it as
arithmetic gets nonsense.

## `<units>`, overloaded in practice rather than in the schema

Here the specification is clean, and it is the model to copy. Three roles, three names:
`<model_units>` is the container, `<unit>` is one definition, `<units>` is what a variable
carries. That discipline is exactly what `<dimensions>` lacks.

The trouble is in the files. 42 elements write `<units name="…"><eqn>…</eqn></units>`
inside `<model_units>`, where the schema says `<unit>` — the plural name doing the
singular's job — against 1,191 correct `<unit>` elements. All 42 come from one vendor's
older exports and the newest files from that vendor get it right, so this reads as a fixed
bug. It should not be legalised: it would buy 42 errors at the price of a permanent second
spelling.

## `<element>` and `<elem>`

Two names four characters apart, in the same subject area, meaning different things.
`<element>` (11,632) is a per-element equation on a variable; `<elem>` (311) is a member of
a dimension. Both appear in array-related markup, often in the same file, and neither name
suggests which is which.

Nothing to fix — renaming either would break every file — but it belongs in the list,
because it shows the same absence of a naming rule that produced the other three.

## What we would ask for

**A naming rule for anything added from here on**, and one sentence would do it: an
element name means one thing, and where two things are related, the pattern is
`<model_units>` / `<unit>` / `<units>` — a distinct name for the container, the
definition, and the reference. XMILE already has the right answer in it; it is just not
written down, so it was not followed.

**An alternative name for `<eqn>` on a stock, with `<eqn>` deprecated there.** This is
the one collision that actively misleads a reader, and the remedy has the same shape as
item 3's:

```xml
<stock name="population">
  <initial>1000</initial>     <!-- preferred -->
  <inflow>births</inflow>
</stock>
```

`<initial>` is accepted on `<stock>` and on `<stock><element>`; `<eqn>` remains valid
there and is annotated as deprecated. Writers SHOULD emit `<initial>`; readers MUST accept
both. Nothing existing breaks, and the misleading spelling stops being the only option.

Deliberately **not** in the 1.1.x schema proposal. That proposal repairs what the schema
wrongly rejects; this changes what writers should emit, which is a decision about the
language rather than a defect in its expression. It belongs in the text.

**A sentence on `<eqn>` in a macro**, which item 12 asks for on its own account. Of the
five senses it is the only one the parent element does not disambiguate, so it is the only
one where a reader has to guess.

The other three want nothing done. `<dimensions>` is handled by item 3, `<units>` is
someone else's fixed bug, and `<element>`/`<elem>` is a wart to live with.

---
