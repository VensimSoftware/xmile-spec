*Status against XMILE v1.1 (SDS Candidate Standard 02, 20 August 2024)
as reviewed 2026-07-30:* **Stands.** 1.1 describes the per-variable tag as "its cousin at the top of each XMILE file".

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
