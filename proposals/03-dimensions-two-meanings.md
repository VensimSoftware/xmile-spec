*Status against XMILE v1.1 (SDS Candidate Standard 02, 20 August 2024)
as reviewed 2026-07-30:* **Stands.** 1.1 describes the per-variable tag as "its cousin at the top of each XMILE file".

*See also [item 16](16-element-name-collisions.md), the survey of element names that carry
more than one meaning. This is the worst of the four and the only one proposed for a fix.*

*Updated 2026-08-21 with what the collision costs the schema, and a naming fix.*

**The schema pays for this with a workaround it documents in a comment.** The whole-model
list is declared INLINE inside `<xmile>`, with the note *"need to inline dimensions element
below to avoid conflict with dimensions element in stock/flow/aux"* — present since the
v1.0 schema. XSD forbids two global elements with the same name, and the per-variable list
holds the global slot because `<stock>`, `<flow>` and `<aux>` reach it by `ref`. So the
whole-model one cannot be global, and a reader looking for it will not find it where every
other top-level element is declared.

**The collision was never forced by the content models, only by the naming.** The
whole-model type is a superset of the per-variable one — `<elem>` is `minOccurs="0"` and
`size` is optional — so one definition could have covered both levels. Checked against the
v1.1 schema:

| Content | whole-model type | per-variable type |
|---|---|---|
| `<dim name="R" size="2"><elem name="a"/></dim>` | accepted | **rejected** |
| `<dim name="R"/>` | accepted | accepted |

The split buys exactly one constraint: that a variable's dimension list contains
references and nothing else. Two different names would have bought it without the
workaround.

**The fix is the one units already uses.** `<model_units>` holds unit definitions,
`<unit>` is one definition, `<units>` is what a variable carries: three roles, three
names. So:

| role | units | dimensions now | dimensions proposed |
|---|---|---|---|
| container of definitions | `<model_units>` | `<dimensions>` | `<model_dimensions>` |
| one definition | `<unit>` | `<dim>` | `<dim>` |
| what a variable carries | `<units>` | `<dimensions>` | `<dimensions>` |

Renaming the whole-model one is also much the cheaper way round: 64 occurrences in the
corpus against 4,490 per-variable. The per-variable spelling, which is the one everybody
writes, does not change at all.

The 1.1.x schema proposal implements this, with the deprecated top-level `<dimensions>`
still accepted and sharing one definition with `<model_dimensions>` — the same treatment
`<smile>` gets, so the two cannot drift apart.

---

*Re-checked 2026-08-20 against the schema added to `xmile-spec` on 2026-08-18:*
**Stands, untouched.** The new schema still declares `dimensions` twice - once as the
whole-model dimension list and once as the per-variable subscript list - with no
annotation distinguishing them.

---
# `<dimensions>` means two different things

The same tag is used for two unrelated jobs, told apart only by where it appears:

- **At model scope it declares** the dimensions and their elements:
  `<dimensions><dim name="Region"><elem name="North"/><elem name="South"/></dim></dimensions>`
- **Inside a variable it applies** dimensions that were declared elsewhere:
  `<dimensions><dim name="Region"/></dimensions>`

These are different operations on different subjects — defining a set, versus saying
which sets a variable is arrayed over — and they share a tag name and a child name.

The clearest evidence that this is a wart is the schema itself: `xmile.xsd` has to
declare `<xs:element name="dimensions">` **twice**, with two different content models.
In the model-scope declaration `dim` carries `elem` children and its own attributes; in
the variable-scope one `dim` is a bare name and nothing else. The second is annotated
"Dimensions for a specific stock, flow, or aux in a model" — an annotation needed only
because the tag name does not distinguish the two.

The cost is small but real and falls on every implementer who supports arrays: readers
must branch on context to know what a `<dimensions>` block means, schema-driven tooling
gets two shapes under one name, and the document reads ambiguously to a human.

**Proposed change.** Give the per-variable use its own tag — `<apply-to>` or
`<dim-use>`, the TC's choice — and keep the existing spelling as a deprecated alias so
every current file stays valid. Purely additive; no existing document changes meaning.

*Related, from the same corner of the spec and worth raising if there is time:* a
dimension element and a model variable may share a name (Stella keeps them in separate
namespaces; most other tools cannot), and element names may be reused across independent
dimensions with the spec silent on whether the reuse denotes the same element. Both
force an importer to invent a disambiguation rule of its own.
