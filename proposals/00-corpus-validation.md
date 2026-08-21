# Corpus validation: v1.0, our XSD 1.0 demonstration, and the 2026-08-18 v1.1 schema

Evidence for the status lines in the items beside this file. Run 2026-08-20.

## Method

122 documents: `.xmile`, `.stmx` and `.itmx` files under our XMILE test corpus. 36 come
from the isee exchange library, 29 from PySD/venpy, 17 from WorldTrans FRIDA, the rest
from the Hayward loop-analysis supplements in ISDC and SDR, our own Vensim exports, and
hand-written minimal cases. Two are not well-formed XML and are excluded from the totals.

All three schemas were compiled and run by the same engine, `xmlschema` 4.3.2 under
Python 3.12, so the numbers are comparable. That engine is what `tools/validate.py` uses.
It is not what `tools/v-validate/validate_xmile.py` uses; that one is built on lxml, which
implements XSD 1.0 only and cannot compile the new schema at all. See "On the two
validators" below.

| Schema | Foreign-namespace errors | Standard-side errors | Files with no errors |
|---|---|---|---|
| `xmile-v1.0.xsd` (OASIS Standard, 14 Dec 2015) | 9,150 | 21,864 | 3 |
| our `xmile-v1.x-proposal.xsd` (XSD 1.0 wildcards) | 74 | 22,875 | 4 |
| `spec/schema/xmile.xsd.xml` (2026-08-18, XSD 1.1) | 74 | 29,331 | 4 |

Forty of the 122 files validate clean if vendor-namespace markup is ignored, under all
three. That number is a property of the corpus, not of any schema.

Our XSD 1.0 schema is in the table as evidence, not as a live proposal. The route is
settled: the specification took XSD 1.1 on 2026-08-18. What the middle row shows is that
the two forms were equivalent on real files, which is worth knowing when weighing the
next such choice.

## What the numbers mean

**The vendor-extension problem is solved, and both routes solve it identically:** 9,150
errors down to 74 either way. The two schemas reach the same residue by different means.
Ours inserts `xs:any namespace="##other"` and `xs:anyAttribute` particles throughout; the
new one declares `xs:defaultOpenContent` and schema-level `defaultAttributes` once. On
this corpus they are indistinguishable. The XSD 1.1 form is better where the corpus
happens to be silent, chiefly vendor elements inside the `xs:all` groups, which XSD 1.0
cannot express at all, and it is far less to maintain.

The 74 that remain:

| Count | What | Why |
|---|---|---|
| 36 | root element in `http://www.systemdynamics.org/XMILE` | pre-OASIS namespace; correctly not this schema's business |
| 36 | `vensim:attach` on `<connector><to>` | `<to>` is declared `type="xs:string"`, a simple type, and `defaultAttributes` reaches complex types only |
| 2 | `uuid` pattern | genuinely malformed in the file |

The second row is a real hole. 34 element declarations in the schema use a built-in
simple type, among them `<eqn>`, `<doc>`, `<to>`, `<inflow>`, `<outflow>`, `<units>`,
`<name>`, `<vendor>` and `<copyright>`. None can take a vendor attribute or a vendor
child, and several are exactly where a vendor would want to annotate.

**The standard-side count rose, and that is a deeper check rather than a regression.** The
v1.0 schema rejected an entire `<style><graph>` block in one error, because `<graph>` was
not a permitted child of `<style>` at all. The new schema admits it, so the validator
descends into the block and reports each unrecognised attribute individually. About
13,800 of the 29,331 errors are inside a `<style>` block, and 4,500 more under
`stacked_container/graph`.

**Error totals are inflated by cascade.** When a withdrawn 1.0 device appears, whether
`<button>`, `<knob>`, `<switch>` or `<graphics_frame>`, every sibling after it in the
same content model is also reported as unexpected, well-formed vendor elements included.
A minimal file exercising vendor elements and attributes in a `<view>`, a `<style>` and
an `<aux>` validates with zero errors, which is the right check on the mechanism.

## Where the remaining errors are

| Errors | Path | Nature |
|---|---|---|
| 5,975 | `views/view/style/graph` | `graph_style_type` omits `axis_*`, `legend_position`, `interval`, `grid_color`, `axis_color` |
| 4,485 | `views/view/stacked_container/graph` | the same attributes, on `<graph>` itself |
| 3,767 | `variables/module` | 3,576 of them `<connect2>`, undocumented and unschema'd |
| 3,690 | `views/style/graph` | as above |
| 2,920 | `stacked_container/graph/plot` | plot attributes |
| 2,169 | `style/table`, both paths | the `header_*` family absent from `table_style_type` |
| 710 | `views/style/slider` | `num_ticks`, `vertical`, `wrap_title`, `input_width`, `input_expands` |
| 558 | `views/view` | 339 `<button>` and other withdrawn devices; 52 the `name` attribute |
| 266 | `variables/*/format` | `precision` of `full`, `max` or `auto`, and `scale_by="auto"`, all typed as numeric |
| 168 | `xmile` | 57 `<default_format>`, 36 old-namespace roots |
| 71 | `header` | `<smile>` |

## The repository's own sample files

`spec/schema/` gained three sample documents alongside the schema. None validated against
it, and CI did not notice: `npm run validate` with no arguments compiles the schema and
stops.

Two failures were transcription artifacts in `WithArrays.xmile`, both fixed on this
branch: an unterminated `<options namespace="std, isee"?` on line 4, which left the file
not well-formed, and a stray `+` in front of the `<view>` tag, a leftover diff marker
parsed as a text node inside `<views>`.

Two real disagreements remain.

`<ai_information>` and `ai_state="..."` are a proposed addition to the standard that the
schema does not yet declare: 11 direct rejections, and 12 more from the cascade, since
everything after `<ai_information>` in `<xmile>` is then reported as unexpected too, four
legal `isee:` elements among them. The schema's comment on `##local` cites `ai_state` as
an example of a vendor attribute that "forgot its prefix". That is worth correcting, as
it is a proposed standard attribute and the comment as written argues against admitting
it. Nothing is wrong with the samples; the schema is behind the proposal.

`<uses_arrays/>` is written bare, and the required attribute has two names. Section 2
says the tag "has one REQUIRED attribute", `maximum_dimensions`, while its own first
example three paragraphs earlier writes `<uses_arrays/>` with no attribute at all. The
schema declares the attribute as `max_dimensions`, required. Across the 122-file corpus,
41 files use `<uses_arrays>` and none writes either spelling. The prose contradicts
itself, the prose contradicts the schema, and no implementation follows either: the item
9 pattern, on a different tag.

CI on this branch now runs `npm run validate -- "spec/schema/*.xmile"`. It is red until
the AI proposal is in the schema and the `uses_arrays` name is settled, which makes it a
serviceable tracker for both.

## On the two validators

`tools/validate.py` and `tools/v-validate/validate_xmile.py` do different jobs, and both
are worth keeping.

`tools/validate.py` is the right shape for a specification repository. It compiles the
schema with no documents, which is the check CI needs; it reports a document path per
error; it expands globs itself, so behaviour does not depend on the shell; and
`validate.mjs` locates an interpreter, so `npm run validate` works alongside
`npm run lint`.

`validate_xmile.py` answers a different question: what is a proposed schema change worth?
It walks a tree, runs several schemas over it, groups the run by folder and by schema,
and writes a deterministic result file beside each model so a verdict change shows up as
a diff. It also keeps an `EXPECTED` table of the errors Vensim's exports produce
deliberately, each mapped to the proposal item that would resolve it, so an unexpected
error is visible without reading past the known ones.

Both have since gained the other's better idea. `tools/validate.py` now takes a
repeatable `--schema` and prints a totals comparison, which is what made the table at the
top of this file reproducible inside the repository. `validate_xmile.py` cannot go the
other way: lxml is XSD 1.0 only, so it cannot load `spec/schema/xmile.xsd.xml` at all.
Either it grows an `xmlschema` backend, or it stays the XSD 1.0 comparison tool and
`tools/validate.py` remains the one that validates against the shipped schema.
