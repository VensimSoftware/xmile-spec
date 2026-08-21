# The XMILE schema

New `xmile.xsd.xml` is the XML Schema for XMILE documents, XSD 1.1. `tools/validate.py`
validates against it; `npm run validate` with no arguments compiles it and stops, which is
what CI runs.

This file records what changed from the v1.0 schema and how the result compares with an
independently generated schema of the same intent. Measured 2026-08-20 with `xmlschema`
4.3.2 under Python 3.12.

## The v1.0 baseline

The header names Candidate OASIS Standard 01 of 29 July 2015 as its source. The final
OASIS Standard of 14 December 2015 also exists, and is what
`tools/v-generate/xmile-v1.0.xsd` holds. The two were diffed: they are identical apart
from whitespace and the provenance comment, so nothing turns on which was used. The
Standard is the authoritative artefact and the header would be more accurate naming it.

## What changed from v1.0

Global declarations went from 46 elements and 31 named types to 38 and 32.

**The vendor-extension mechanism**, which v1.0 had no form of at all — 83 KB containing no
wildcard of any kind:

- `xs:defaultOpenContent mode="interleave" appliesToEmpty="true"` with
  `<xs:any namespace="##other" processContents="lax"/>`, applying an element wildcard to
  every complex type. `interleave` admits an extension anywhere among the standard
  children rather than only at the end; `appliesToEmpty` extends it to types that would
  otherwise permit no children.
- `defaultAttributes="vendor_attributes"` on `xs:schema`, whose wildcard is
  `notNamespace="##targetNamespace ##local"`, applying an attribute wildcard to every
  complex type. XSD 1.0 has no equivalent, and could not have carried one inside this
  schema's `xs:all` groups in any case.
- `defaultAttributesApply="false"` on the `<view>` and `<stacked_container>` types, which
  extend `view_content_type` and inherit its wildcard; applying the group again would
  declare two attribute wildcards on one type. The inherited wildcard does reach them —
  `<view isee:page_cols="2">` validates.

**Features v1.1 withdrew.** Eight global elements are gone: `button`, `knob`,
`list_input`, `switch`, `graphical_input`, `graphics_frame`, `popup`, `switch_action`, and
the global `entity` declaration, whose only two references were from the option group and
from `switch_action`. `menu_action_choices` went with `button`. `numeric_display` is not
an input and survives, moved to the output objects. `uses_inputs` became `empty_type`,
having no remaining attributes; `uses_outputs` lost `lamp` and `gauge`.

**Defects fixed**, each of which had made a conforming document invalid:

- `<unit>` accepts `<eqn>` followed by `<alias>` elements. It was an `xs:choice`, so the
  specification's own example in Section 2 could not validate against its own schema.
- `connector/@polarity` exists. Section 6 documents it as `+ | - | none`, and it was
  absent from the schema entirely.
- `empty_type` and `boolean_or_empty_type` are declared directly instead of as
  unconstrained restrictions of `xs:anyType`. The old spelling collides with a
  schema-wide `defaultAttributes` group, because a restriction of `anyType` cannot also
  take one.
- `<style>` admits the seven object types it was missing: `alias`, `stacked_container`,
  `slider`, `numeric_display`, `graph`, `table`, `text_box`. `style_type` gained an
  optional `<shape>`, and `graph_style_type` and `table_style_type` are new.
- `version` accepts `1.1`, and still accepts `1.0`, since the namespace did not change.

## Comparison with an independently generated schema

`proposals/schema/xmile-v1.x-proposal-11.xsd` is the v1.0 schema plus the same mechanism,
generated mechanically by `tools/v-generate/make_proposal_xsd.py --xsd11` before this
schema was published. The two were arrived at separately, so the agreement is worth
recording.

The element wildcard is character-for-character the same in both. The attribute wildcard
differs in spelling only: `namespace="##other"` there against
`notNamespace="##targetNamespace ##local"` here. XSD 1.1 defines the first as the second,
and the two were checked against each other:

| Case | this schema | generated schema |
|---|---|---|
| vendor attribute, `isee:foo="1"` | accept | accept |
| vendor element, `<isee:note>` | accept | accept |
| unprefixed unknown attribute | reject | reject |
| unprefixed unknown element | reject | reject |
| unknown element in the XMILE namespace | reject | reject |

Rejecting the unprefixed cases is the point of the exclusion: a vendor attribute that
forgot its prefix, or a withdrawn one such as `lamp="true"`, must not validate silently.

The two schemas differ in scope rather than mechanism. The generated one is v1.0 content
plus the extension points, so it lacks every content change above. This one is v1.1
content plus the same extension points. Over a 122-file corpus both cut
foreign-namespace errors from 9,150 to the same 74;
`proposals/00-corpus-validation.md` reports that and what the residue consists of.

## A known gap

34 element declarations use a built-in simple type — `<eqn>`, `<doc>`, `<to>`,
`<inflow>`, `<outflow>`, `<units>`, `<name>`, `<vendor>` and `<copyright>` among them.
`defaultAttributes` reaches complex types only, so none of these can take a vendor
attribute or a vendor child. It is not hypothetical: 36 of the 74 residual errors in the
corpus are `vensim:attach` on `<connector><to>`.
