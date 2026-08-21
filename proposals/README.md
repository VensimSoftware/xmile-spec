# Proposals for XMILE - Ventana Systems

Working notes for the XMILE TC, one file per item, so an item can be revised, split or
retired on its own as the specification catches up with it. Prepared from implementing
both directions of the Vensim / XMILE bridge: import of around 40 .stmx models plus PySD
.xmile files, and export of Vensim models including World3, roughly 100 in all.

Numbered files are content items: things we think the specification should say
differently. `AA-suggested-process.md` is about how the work gets done, which is why
it is lettered rather than numbered.

Each file opens with two status lines: how the item stood against the v1.1 text when it
was written (2026-07-30), and how it stands against the schema added to this repository's parent
on 2026-08-18. `00-corpus-validation.md` holds the evidence for the second line, and the
numbers quoted in the items come from there.

The text and tables here are MIT, © 2026 Ventana Systems, Inc.; see
[LICENSE-Ventana.md](../LICENSE-Ventana.md), which also records what is not ours to
license — the generated schemas derive from the OASIS schema, and `models/` holds
third-party models.

`schema/` holds the schemas a proposal generated: three forms of the vendor-extension
change, the Vensim extension schema, and the NVDL alternatives. They are outputs of
`tools/v-generate/`, not hand-edited, and `tools/v-validate/` finds them by name.

## Items

| # | Item | Status 2026-08-20 |
|---|------|-------------------|
| [1](01-extension-mechanism.md) | An extension mechanism | Half resolved. The schema now has one; the prose does not describe it and sets no must-ignore rule. Two holes: 34 simple-typed elements take no vendor markup, and two types opt out of the attribute wildcard. |
| [2](02-netflow.md) | `<netflow>` for a net-rate stock | Less urgent now that item 1 makes a vendor-prefixed form valid. Raises 
questions about symmetry of treatment across features in the intersection or union of vendors. |
| [3](03-dimensions-two-meanings.md) | `<dimensions>` means two things | **Updated 2026-08-21.** The schema pays for the collision with an inline declaration and says so in a comment; the content models never required it. Fix: `<model_dimensions>`, after `<model_units>`. In the 1.1.x schema. |
| [4](04-doc-on-containers.md) | Documentation has nowhere to go | Unresolved. Now measurable: `<doc>`, `<format>` and `url` on `<module>` all rejected. |
| [5](05-schema-spec-drift.md) | Schema / specification drift | Partly resolved. 1.1 ships a new schema, and several named drifts are fixed. Expanding `<style>` moved the rest one level deeper: about 13,800 of 29,331 remaining errors are inside style blocks. Four new drifts found: `<connect2>`, `<default_format>`, `precision="full"`, and `uses_arrays/@max(imum)_dimensions`, which prose, schema and practice each spell differently. |
| [6](06-flow-vs-aux.md) | When must a rate be a `<flow>` | Unresolved. |
| [7](07-smile-and-vendor-neutrality.md) | Community needs over canonical form | Union or intersection? Intersection is the working rule but is not applied consistently: `<non_negative>` is in as an option, a net-flow stock is out. On built-ins, something had to be picked and the choice is fine; the ask is an identifier crosstab with conceptual rows and a column per vendor. |
| [7a](07a-crosstab-design.md) | Designing the function crosstab | Evidence for item 7's ask, from xmutil, Vensim and PySD. All three key on (name, arity); translation into XMILE is many-to-one; coverage runs 140 names against 57; some rows have no `std` column at all. |
| [7b](crosstab/README.md) | The crosstab, first cut | Working tables built from the spec, xmutil, Vensim, PySD and SDEverywhere: 165 concepts, 252 spellings, 226 support facts. Concepts are connected components of the asserted correspondences, not a curated list. |
| [S](schema/xmile-v1.1.x-changes.md) | A 1.1.x schema proposal | The v1.1 schema plus six additive changes addressing items 1, 3, 4, 9's pattern, 10 and 11. Corpus errors 29,407 to 28,000; no file worse. |
| [8](08-namespace-count.md) | Section 2.1 undercounts the namespaces | Unresolved. The schema now implements the category that 2.1 does not count. |
| [9](09-view-attributes.md) | `<view>` attributes nobody writes | Unresolved. `name` is still rejected, and the vendor wildcard correctly does not rescue it. |
| [10](10-licence.md) | Nowhere to put a licence | Unresolved. |
| [11](11-smile-element.md) | `<smile>` is in no document | Unresolved. 71 errors in the corpus. Transition item; may not require a schema change. |
| [12](12-macro-multiple-outputs.md) | A macro can only return one value | Unresolved. |
| [13](13-dimension-relations.md) | Dimensions cannot be related | Unresolved. |
| [14](14-data-vs-model-variable.md) | `<data>` describes a session | Unresolved. |
| [15](15-identifier-namespaces-question.md) | Identifier namespaces - a question rather than a proposal | - |
| [16](16-element-name-collisions.md) | Element names that mean more than one thing | **New 2026-08-21.** Four of them: `<dimensions>`, `<eqn>` (four meanings), `<units>`, and `<element>` vs `<elem>`. Item 3 fixes the first; the ask here is a naming rule for future additions, plus a decision on `<eqn>` on a stock. |
| [AA](AA-suggested-process.md) | A suggested process | Not a content item. Four steps sketched on sd-tools; steps 1 and 2 are done. Step 3 needs a decision rule, step 4 a promotion rule. |

## Reading order

Item 1 comes first because it is architectural: until there is an extension point *and* a
rule about unknown markup, no vendor can ship an experiment without writing invalid
files. The schema has now supplied the first half. Item 2 is the case in point, a small
semantic addition that item 1 would let us ship as an experiment instead of an invalid
file.

Items 5, 9 and 11 share a theme: the documents and
the files have drifted apart in both directions: normative requirements no implementation
follows (five `<view>` attributes written zero times), and universal practice no document
describes (`<smile>`, in 88 of 96 files, holding the namespace declaration the standard
assigns elsewhere). Every one of these came from running a validator over real models
rather than from reading, which is why `00-corpus-validation.md` exists.

Items 8, 13 and 15 overlap on namespace questions. Of particular interest is that, per 13, 
subranges create an internal inconsistency because they require matching names within dimension
namespaces, while elsewhere namespaces are required to be independent.

## Retiring an item

When the specification or the schema resolves an item, move the file to `resolved/` with
a closing line naming the commit or release that resolved it, and strike its row from the
table above. Partial resolution is recorded in the item's status block, not by moving it.
