*Status against XMILE v1.1 (SDS Candidate Standard 02, 20 August 2024)
as reviewed 2026-07-30:* **Partly resolved; the finding has changed** — see the item itself. `flow_concept` is documented at last; the view `name` gap remains; and v1.1 ships no schema of its own, citing instead the *superseded* `v1.0/cos01` revision, which turns the question into "which artefact is normative?".

*Re-checked 2026-08-20 against the schema added to `xmile-spec` on 2026-08-18:*
**Partly resolved; the "which artefact is normative" question is answered.** Version 1.1
now ships a schema of its own (`spec/schema/xmile.xsd.xml`, 2026-08-18), so the item's
sharpest complaint - that 1.1 cited the superseded `v1.0/cos01` revision - is gone. The
new schema also fixes several specific drifts this item listed: `<unit>` accepts `<eqn>`
followed by `<alias>` elements (was `xs:choice`, which its own example violated),
`connector/@polarity` exists at last, `empty_type` and `boolean_or_empty_type` are
declared directly rather than as restrictions of `xs:anyType`, and `<style>` admits the
seven object types it was missing.

The drift persists, and expanding `<style>` moved it one level deeper instead of
closing it. Over 122 real models the new schema reports 29,331 standard-side errors, of
which about 13,800 are inside a `<style>` block and 4,500 more under
`stacked_container/graph`. `graph_style_type` and `table_style_type` were derived from the
`<graph>` and `<table>` element declarations, and those declarations are themselves short
of what every tool writes: `axis_color`, `grid_color`, `legend_position`, `interval`, the
whole `axis_title_*`, `axis_label_*` and `header_*` families. `<slider>` in a style block
is missing `num_ticks`, `vertical`, `wrap_title`, `input_width`, `input_expands`.

Four more drifts in our corpus that this item did not list:

* `<connect2>` inside `<module>` - 3,576 occurrences across FRIDA and the isee exchange
  models, in neither text nor schema.
* `<default_format>` as a child of `<xmile>` - 57 occurrences, likewise undocumented.
* `format/@precision="full" | "max" | "auto"` and `scale_by="auto"` - 138 occurrences,
  rejected because the schema types both as numeric.
* `<uses_arrays>` - Section 2 calls `maximum_dimensions` REQUIRED, the schema declares
  it as `max_dimensions` and required, Section 2's own example writes `<uses_arrays/>`
  bare, and of the 41 files in our corpus that use the tag, none writes either spelling.
  This one is three-way: prose against itself, prose against schema, and both against
  every implementation. It also breaks a sample file in this repository.

A caution for anyone reading these totals: the error counts are inflated by cascade. When
a withdrawn 1.0 device such as `<button>` or `<switch>` appears, every sibling after it in
the same content model is also reported as unexpected. The vendor mechanism itself is
sound - a minimal file with vendor elements and attributes in a `<view>`, a `<style>` and
an `<aux>` validates with zero errors.

---
# The schema and the specification have drifted apart

The fallback mechanism in 3.4.1 is a good piece of design and we are using it —

> "In these cases, a supported fallback method SHOULD also be provided, for example,
> 'gear, rk4'. This means that Gear should be used if the product supports it.
> Otherwise, use rk4."

— which lets a tool name a scheme the standard does not define without stranding
anybody. Vensim's Difference setting is numerically Euler (it differs only in how a run
is stored), so we now write `method="difference,euler"`: our own reader restores the
setting exactly, and every other reader gets the numerically identical Euler. We would
not ask for a `difference` value in the enumeration; the fallback idiom already covers
it. There are two problems with the idea, though.

**The schema cannot express it.** `method_type` is a union of the enumeration with
`xs:string`:

```xml
<xs:simpleType name="method_type">
  <xs:union memberTypes="standard_method_type xs:string" />
</xs:simpleType>
```

The `xs:string` arm is presumably there to admit fallback lists, but a union with
`xs:string` cannot reject anything: `method="rk-4"` and `method="banana"` validate
exactly as well as `method="gear,rk4"`, and a reader matching enumerated values falls
back to its default without anyone being told. (We found this by shipping
`method="RK4"` ourselves and having it validate.) A pattern — a comma-separated list of
name tokens — would admit every legitimate fallback list while still catching a typo.

**v1.1 ships no schema of its own, and points backwards at a superseded one.** Its
"Additional artifacts" list names the schema component as
`http://docs.oasis-open.org/xmile/xmile/v1.0/cos01/schemas/` — the *Candidate* OASIS
Standard revision of 29 July 2015, not the final OASIS Standard revision of 14 December
2015 at `v1.0/os/schemas/`. The two files differ only in their header comment, so nothing
changes technically, but a specification should not cite a superseded artefact as its own
component. v1.1 also still declares the v1.0 XML namespace
(`http://docs.oasis-open.org/xmile/ns/XMILE/v1.0`), and no `v1.1/` directory exists on
the OASIS docs server. So the v1.0 XSD remains the only machine-readable artefact anyone
has, while the prose around it has moved. If
implementers are expected to keep using it, the two need reconciling; if they are not, it
should be withdrawn, because today it is the only thing that says `rk2_auto`, `rk4_auto`
or a `<view>` without a name are or are not allowed. One consequence for us: we write
`method="rk4_auto,rk4"` — the adaptive form for readers that follow the schema, with the
fixed form as the fallback the prose does define.

**A view has nowhere to keep its name** — still true in v1.1, whose own list of view
attributes runs `order`, `width`, `height`, `zoom`, `scroll_x`, `scroll_y`, `background`,
`page_width`, `page_height`, `page_sequence`, `page_orientation`, `show_pages`,
`home_page`, `home_view`, and no `name`. 1.1 added `order` for presenting views in
sequence, which makes the omission harder to read as an oversight: views are now
explicitly things a user navigates between, and a thing you navigate between needs a
label. In the v1.0 schema, `<view>` accepts `background`, `zoom`,
`scroll_x`, `scroll_y`, `home_page`, `home_view`, `page_width`, `page_height`,
`show_pages`, `page_orientation`, `page_sequence`, `type`, `x`, `y` and `content` — and
**not `name`**. Yet `<view name="…">` is what isee writes (37 times in the one Stella
model we use as a test case), it is what every importer must therefore read, and a view's
name is real model content: modellers name views after sectors, and some keep an
otherwise empty view purely so that its name acts as a separator in the view menu. There
appears to be no conforming way to name a view at all. Either the attribute belongs in
the schema or the specification should say where a view name lives.

**The schema and the text enumerate different methods.** They do not overlap cleanly:

| | euler | rk2 | rk2_auto | rk4 | rk4_auto | rk45 | gear |
|---|---|---|---|---|---|---|---|
| schema `standard_method_type` | yes | yes | yes | yes | yes | — | — |
| specification 3.4.1 | yes | yes | — | yes | — | yes | yes |

So `rk2_auto` and `rk4_auto` are valid against the schema but absent from the text,
while `rk45` and `gear` — the text's own example of a fallback — are described in the
text and invalid against the enumeration (they pass only through the `xs:string` arm).
An implementer cannot tell which list is normative. Reconciling the two, and saying
plainly what a reader should do with a method it does not recognise **when no fallback
is given**, would remove the guesswork.

---
