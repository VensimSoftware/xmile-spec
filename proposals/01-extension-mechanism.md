*Status against XMILE v1.1 (SDS Candidate Standard 02, 20 August 2024)
as reviewed 2026-07-30:* **Stands.** §3.6 "Extending the Standard Language" covers only functions and macros. No XML extension point, no rule that a reader must ignore what it does not recognise, and nothing on when a writer should use an extension at all.

*Re-checked 2026-08-20 against the schema added to `xmile-spec` on 2026-08-18:*
**Half resolved by the schema; the text is unchanged.** The schema added on
2026-08-18 declares `xs:defaultOpenContent mode="interleave" appliesToEmpty="true"` with
`<xs:any namespace="##other" processContents="lax"/>`, plus a schema-level
`defaultAttributes="vendor_attributes"` whose wildcard is
`notNamespace="##targetNamespace ##local"`. That is the XSD 1.1 route this item described
as the better of the three, and the `##local` exclusion is the refinement 1a(ii) argued
for. Measured over our 122-file corpus, foreign-namespace errors fall from 9,150 to 74.
Our own XSD 1.0 demonstration schema reaches the same 74, so on real files the two are
equivalent; XSD 1.1 wins on the parts our corpus does not exercise, chiefly vendor
*elements* inside the `xs:all` groups, which XSD 1.0 cannot express at all.

What stands is the normative text. Section 2 still says only that "provision for vendor
specific additions are also detailed", and 3.6 "Extending the Standard Language" still
covers only functions and macros. There is no rule that a reader MUST ignore markup it
does not recognise, no statement of when a writer SHOULD reach for an extension, and no
mention anywhere in the prose of the mechanism the schema now implements. A schema alone
does not make an extension conforming; it makes it non-invalid.

Two holes in the mechanism as shipped, both worth a separate note:

* 34 elements are declared with a built-in simple type (`<eqn>`, `<doc>`, `<to>`,
  `<inflow>`, `<outflow>`, `<units>`, `<name>`, `<vendor>` among them). `defaultAttributes`
  applies to complex types only, so none of these can take a vendor attribute or a
  vendor child. 36 of the 74 residual errors are `vensim:attach` on `<connector><to>`.
* `<view>` and `<stacked_container>` set `defaultAttributesApply="false"` to avoid
  declaring two attribute wildcards on one type. Checked: the wildcard inherited from
  `view_content_type` does reach them, so `<view isee:page_cols="2">` validates. Worth
  a note in the schema because it is the kind of thing a later edit breaks silently.

---
# An extension mechanism

**The route is settled: XSD 1.1.** The schema adopted `xs:defaultOpenContent` and
schema-level `defaultAttributes` on 2026-08-18, which is form 1a(ii) below. The other two
forms, the XSD 1.0 wildcards with the 1a(i) container and the 1a(iii) NVDL dispatch, are
closed. They are kept because the comparison is what made the case, and because the same
machinery applies to the next proposal. What remains open in this item is the prose, which
still does not describe the mechanism, and the two holes recorded in the status block.

### The problem

XMILE v1.0 has **no way for a vendor to add anything to a file**:

- The schema contains **no `xs:any`** in 83 KB. We verified this by
  validating hand-built documents against the published XSD: an element in a vendor
  namespace is rejected with "this element is not expected", wherever it is placed.
- The specification contains **no rule requiring a conforming tool to ignore elements
  or attributes it does not recognise**. So even disregarding the schema, nothing
  obliges a reader to skip an unknown tag rather than fail on the file.

The practical result is that **every file any vendor has extended is invalid**,
including isee's own: `<smile>` and the `<isee:*>` elements are rejected by the
published schema exactly as our `<vensim:netflow>` is (item 2, which we had to ship this
way for want of the mechanism asked for here). The ecosystem tolerates this, which is luck
rather than design.

This is hard to square with section 3.2.2.3, which predefines *eleven* vendor
namespaces (`std`, `user`, `anylogic`, `forio`, `insightmaker`, `isee`, `powersim`,
`simanticssd`, `simile`, `sysdea`, `vensim`) for resolving **identifiers**. The
standard anticipates vendor divergence in the equation language and provides for it
carefully, while making vendor divergence in the XML illegal.

**And the schema cannot be extended from outside either.** A vendor wanting a stricter
file of its own — "XMILE, plus these few things" — would reach for `xs:redefine` (XSD 1.0)
or `xs:override` (1.1). Neither can help here, because both reach only *named* top-level
components — simple types, complex
types, groups, attribute groups — and element declarations cannot be redefined at all.
Counting the published XSD:

| | count |
|---|---|
| named complexTypes | **6** — `min_max_type`, `points_type`, `view_content_type`, `style_type`, `empty_type`, `boolean_or_empty_type` |
| anonymous inline complexTypes | **101** |

`stock`, `flow`, `aux`, `macro`, `sim_specs` and `header` are all top-level elements with
inline anonymous types. So there is no conforming way to express "XMILE's stock, plus one
more child" in a derived schema, and a vendor's only options are to fork the schema
wholesale or to give up validation. The content models are not merely closed; they are
unreachable.

This is a consequence of an authoring style rather than a decision, which is why we raise
it: naming the types would cost nothing in the instance documents and would make the
schema derivable even without change 1a below.

### Proposed change

Two parts, both small:

**1a — Schema.** Add two wildcards, one for elements and one for attributes:

```xml
<xs:any          namespace="##other" processContents="lax" minOccurs="0" maxOccurs="unbounded"/>
<xs:anyAttribute namespace="##other" processContents="lax"/>
```

`##other` confines both to foreign namespaces, so neither can be used to smuggle in
something that looks standard: XSD 1.0's *Wildcard allows Namespace Name* rule requires
the name be neither the target namespace nor absent. `<bonkerstag>` is rejected whether
it inherits the XMILE default namespace or carries none, and `foreignattribute="…"` is
rejected because attributes never inherit a default namespace. `lax` means a foreign
element is validated if the processor happens to know its schema, and passed over
otherwise. `##other` also enforces at the schema level the rule we ask for in
prose below — that a vendor MUST NOT place its extensions in the XMILE namespace, the
rule `<smile>` currently breaks.

**We attach a working schema, not a sketch.** `xmile-v1.x-proposal.xsd`
is the published `xmile-v1.0.xsd` with those wildcards inserted mechanically and nothing
else changed — 35 element wildcards and 108 attribute wildcards. Measured over the 101
XMILE files we hold, of which 94 (93%) use a foreign namespace somewhere:

| | published schema | with 1a |
|---|---|---|
| files rejected | 98 of 101 | 97 |
| total validation errors | 585 | **252** |

The wildcards remove **333 errors, 57% of everything the validator complains about**,
and no file that validated before fails afterwards. The remaining 252 are real findings
against the standard, and are the subject of items 5, 9 and 11.

**The one place XSD 1.0 cannot reach is `xs:all`.** Its content model is
`(annotation?, element*)` — no wildcard is permitted inside it, and *All Group Limited*
forbids wrapping it in a sequence to append one beside it. The published schema uses
`xs:all` 27 times, so those elements can take vendor *attributes* (the attribute wildcard
is a child of the complexType, outside the content model, and is therefore unaffected)
but not vendor *elements*:

| | vendor attributes | vendor elements |
|---|---|---|
| `stock`, `flow`, `aux`, `variables`, `model`, `xmile`, `macro`, `group`, `module`, and every array `<element>` | yes | **yes** |
| `header`, `sim_specs`, `options`, `gf`, `behavior`, `conveyor`, `entity`, `style`, and the view objects (`slider`, `knob`, `plot`, `switch`, `numeric_display`, `graphical_input`, view `stock`/`flow`/`aux`/`connector`/`alias`/`module`/`button`) | yes | no |

This costs us nothing for `<vensim:netflow>`, which belongs in a `<stock>`, nor for
`isee:varattrib="data"`, which is an attribute and so works everywhere. But it is not a
small gap, and the error counts above hide how large it is.

**How much is blocked, measured by content rather than error count.** Of the
13438 vendor elements in the corpus, 11643 (87%) are nested inside another vendor element
— vendors already build isolated subtrees, and no schema change affects those. Only 1795
are *attached* to a standard XMILE element, and it is those attachment points that a
change has to reach:

| attachment points (1795) | | reached by the wildcard |
|---|---|---|
| parent is `xs:choice` / `xs:sequence` | 824 (46%) | yes |
| parent is `xs:all` | 971 (54%) | **no** |

So the wildcard alone reaches under half of the places vendors actually extend. Most of
the remainder is isee hanging `loop_indicator`, `placeholder`, `annotation`, `spatial_map`
and the widget styles off `<style>`.

**Error counts are the wrong instrument here.** A validator stops descending once a
parent's content model fails, so one bad element near the top of a file masks every vendor
element below it. In
`Model_NightShiftWork_2NightShift5DaysOff.STMX` there are **355 vendor elements in
`xs:all` parents and the validator reports 1 error**. The 585 → 252 figures above are
sound as a measure of *how much of the complaint is vendor extensions*; they are useless
as a measure of *how much content a change admits*. The table above is the second
measure.

Three ways to close the remaining 54% follow. The first two change the schema and differ
in what they cost implementers; the third changes nothing and is what a vendor can do
today without the TC at all. We prefer the first.

### 1a(i) — a container element, staying in XSD 1.0

A wildcard is illegal inside `xs:all`, but a **named element** is not. So the wildcard can
move inside a container that is itself declared in the XMILE namespace:

```xml
<xs:element name="extensions">
  <xs:complexType>
    <xs:sequence>
      <xs:any namespace="##other" processContents="lax" maxOccurs="unbounded"/>
    </xs:sequence>
  </xs:complexType>
</xs:element>
```

declared once and referenced wherever a wildcard cannot go:

```xml
<xs:element ref="extensions" minOccurs="0"/>
```

We attach this as `xmile-v1.x-proposal-container.xsd`: the wildcard inline where the
compositor permits it, the container in the 27 `xs:all` content models where it does not.
That reaches all 1795 attachment points, in a file libxml2 still reads — the same coverage
as XSD 1.1 with none of its tooling cost. It is also the pattern ECMA-376 settled on for
the same problem, as `<extLst><ext uri="…">`.

Note `namespace="##other"` on the inner wildcard. `<xs:any>` defaults to `##any`, which
inside a container compiles perfectly well and quietly readmits `<bonkerstag>`; we have
checked that the version above rejects it inside the container as well as outside.

The container has a second advantage, unrelated to schema languages. It
gives an implementation **one element name to learn**: a reader that means to preserve
what it does not understand can copy one subtree verbatim, rather than having to be
namespace-aware at every position in the document. That is what makes 1b's *SHOULD
preserve* realistic to implement.

Its cost is the mirror image of the wildcard's. The wildcard legalises files that exist;
the container legalises a practice nobody follows yet, so the 971 vendor elements now
attached directly to `<header>`, `<style>`, `<view>` and the widgets would have to move
inside `<extensions>` before they validated. Most of that falls where it hurts least —
those are overwhelmingly view cosmetics that no importer round-trips faithfully today —
and the hybrid keeps the two elements that matter most for model semantics,
`<vensim:netflow>` in a `<stock>` and `isee:varattrib` on an `<aux>`, valid exactly as
they are written now.

**It is not free, and the cost is easiest to state from our own code.** A container changes
the bytes, so every reader that consumes vendor content
from an `xs:all` parent needs a change too. Ours does: `<vensim:saveper>` lives in
`<sim_specs>`, and our importer matches it among the direct children of that element. Move
it inside `<extensions>` and it stops being a direct child — our reader would ignore it
and silently lose the save interval from files we wrote ourselves. The fix is one level of
descent and perhaps ten lines, but it has to be made in every implementation that reads
any vendor element under `<header>`, `<sim_specs>`, `<gf>`, `<behavior>`, `<style>`,
`<view>` or the widgets, and it must accept both shapes for as long as old files exist.

That is an argument for adopting the container *with* the wildcard rather than instead of
it, which is what 1a(i) proposes: nothing that validates today stops validating, and the
migration is confined to the positions that were never expressible in the first place.

### 1a(ii) — XSD 1.1, for comparison

**We have built the XSD 1.1 version too**, as `xmile-v1.x-proposal-11.xsd`, so that the
choice can be made on measurements rather than on expectations. ("-11" is the version of
the schema language; it has nothing to do with XMILE v1.1.) It closes the `xs:all` gap
completely, because 1.1 relaxes `xs:all` to admit wildcards, and it says the whole thing
at the top of the file:

```xml
<xs:schema … defaultAttributes="vendor_attributes" vc:minVersion="1.1">
  <xs:defaultOpenContent mode="interleave" appliesToEmpty="true">
    <xs:any namespace="##other" processContents="lax"/>
  </xs:defaultOpenContent>
  <xs:attributeGroup name="vendor_attributes">
    <xs:anyAttribute namespace="##other" processContents="lax"/>
  </xs:attributeGroup>
```

`defaultOpenContent` governs elements only; `defaultAttributes` is the companion for the
attribute half and is easy to overlook — without it a 1.1 schema takes vendor elements
and rejects vendor attributes. Nothing in the existing 2000 lines needs rewriting: 1.1 is
a superset for everything this schema does, and UPA is retained, so no content model
changes meaning.

Two findings the TC should have before choosing.

**It is not quite the five lines it looks like.** `defaultAttributes` applies the group to
*every* complexType, derived ones included — but an attribute wildcard already propagates
from base to derived type, so a `complexContent` extension or restriction receives it
twice and the schema will not compile: *"default attribute is already declared in the
complex type"*. XSD 1.1 provides `defaultAttributesApply="false"` for exactly this; four
types in this schema need it — `empty_type` and `boolean_or_empty_type`, which restrict
`xs:anyType`, and `<view>` and `<stacked_container>`, which extend `view_content_type` —
and they still take vendor attributes by inheritance, so
nothing is lost. We had access to one 1.1 processor only and cannot say whether that
rejection is the specification or that implementation being strict.

**What it buys over the container, measured.** Nothing in coverage: both reach all 1795
attachment points. What 1.1 buys is that they are reached *in place* — files as vendors
write them today become valid, with no migration into containers:

| | schema cost | attachment points reached | files must change |
|---|---|---|---|
| 1a alone | 143 wildcard particles, +249 lines | 824 of 1795 | no |
| 1a(i) container | + 27 refs and one declaration, +302 lines | **1795** | yes, 971 elements move |
| 1a(ii) XSD 1.1 | 2 declarations + 4 exemptions, +11 lines | **1795** | no |

**They are not interchangeable.** A file
written for the container schema does *not* validate against the 1.1 one: `<extensions>`
is in the XMILE namespace, and a `defaultOpenContent` wildcard admits `##other` only. So a
container adopted now would have to be carried forward into any later move to 1.1, not
retired by it. We verified this.

**Against that, the tooling penalty is absolute.** A 1.0 processor does not *fail to
validate* against the 1.1 file — it cannot load it at all,
`xs:defaultOpenContent` being an element it does not recognise:

```
Element 'xs:schema': The content is not valid.
Expected is ((include | import | redefine | annotation)*, ...)
```

`vc:minVersion` does not rescue this: conditional inclusion is itself a 1.1 feature, so a
1.0 processor never gets far enough to honour it.

**How much that matters turns on who is behind the wall.** Of our 101 files, **three
validate against the published schema. All three are 25-element teacups with no vendor
element and no vendor attribute in them** — the smallest thing a script can emit. Every
model produced by a real tool, isee's own included, fails. So essentially nobody in this
ecosystem is validating XMILE today; if they were, they would have noticed. Everyone is
parsing without validating, which means everyone runs the same risks we do — ours,
for the record, being a hand-written dispatch that matches vendor tags on local name and
so cannot tell one vendor's `<members>` from another's.

So the tooling objection is not "N tools break". Nothing that is running breaks. It is
this:

> Nobody validates *because* validation is useless today — everything fails. Fix that, and
> validation becomes worth doing for the first time. The tooling cost is therefore not
> avoided by 1.1, it is deferred onto whoever builds the conformance harness the fix makes
> possible.

The practical question is which of this ecosystem's languages have a 1.1 processor. We
checked:

| | parsing (non-validating) | XSD 1.0 | XSD 1.1 |
|---|---|---|---|
| **Python** | every parser | lxml / libxml2 | **`xmlschema`**, free, pure Python, complete |
| **C / C++** | every parser | libxml2, Xerces-C++ | **none free.** Xerces-C++ is 1.0 only; XSD 1.1 went into Xerces-**J** at 2.12.0 and was never ported |
| **C#** | every parser | `XmlSchemaSet` | **none free.** `XmlSchemaSet` is documented 1.0-only; no Microsoft implementation exists |
| Java | every parser | JAXP default | Xerces-J 2.12+, if the v1.1 grammar is requested explicitly |

Two things follow. **Parsing is unaffected in every language**, because a non-validating
reader never reads the schema at all — no importer, ours or anyone's, changes by one line
for 1.1. And **the one language with a complete free 1.1 implementation is the one
conformance harnesses get written in.** Ours is Python; this document's figures
were produced with `xmlschema` at roughly twice libxml2's runtime over 101 files, which is
a nuisance, not an obstacle.

The residue is real but narrow: a C++ or C# implementation that wanted to validate would
have to buy a tool (Altova RaptorXML, Saxon-EE) or shell out to another language. That is
not nothing. It is much smaller than "most implementers could no longer validate XMILE",
which is what we would have written before counting.

### 1a(iii) — NVDL, which needs no change to anything

A vendor that wants its extended files validated today, without waiting for the TC, can
use **NVDL** (ISO/IEC 19757-4), which dispatches a compound document by namespace and
hands each section to a validator of its own. We attach `xmile-vendor.nvdl`; it is the
whole idea:

```xml
<rules xmlns="http://purl.oclc.org/dsdl/nvdl/ns/structure/1.0" startMode="xmile">
  <mode name="xmile">
    <namespace ns="http://docs.oasis-open.org/xmile/ns/XMILE/v1.0">
      <validate schema="xmile-v1.0.xsd" schemaType="application/xml-schema"/>
    </namespace>
    <anyNamespace match="elements attributes">
      <allow/>
    </anyNamespace>
  </mode>
</rules>
```

The XMILE schema sees the file with every vendor subtree already removed, so
`<vensim:netflow>` inside a `<stock>` passes — not because the schema tolerates it but
because the schema never sees it. **This is the only option here that changes nothing at
all**: the published XSD is used byte for byte. The properties 1a is careful about survive
for free, since an unprefixed element inherits the XMILE default namespace and so stays in
the XMILE section: `<bonkerstag>` is still rejected, an unqualified attribute is still
rejected, and `<smile>` is still rejected too — NVDL cannot rescue a vendor element that a
vendor placed in the standard's namespace, so item 11 is untouched either way.

A second file, `xmile-vensim.nvdl`, routes our own namespace to `vensim-ext.xsd` rather
than allowing it, which is the "XMILE, plus these few things" case. Note the design
consequence: NVDL hands each section to its validator as a document in its own right, so a
`<vensim:netflow>` subtree arrives with `vensim:netflow` as the *root*. Every extension
element must therefore be declared globally, the vendor schema is a flat list rather than
a structure, and it cannot see — or constrain — where in the XMILE document its element
appeared.

Two limits keep this from being an answer for the TC rather than for a vendor. It cannot
express any constraint that crosses a namespace boundary, "`vensim:netflow` only on a
`<stock>` with no `<inflow>`" being unsayable when the two are in different sections by
construction. And it needs an NVDL processor: Jing is the usual one and it needs a JVM,
which is a real cost for a toolchain that has none.

**A caveat.** Every other figure and claim in
this section was produced by running the schemas. These two files were not: the machine
they were written on has no JVM, so the dispatch itself is untested and they should be
read as drafts to try. What we could test is the half that needs no dispatcher —
validating each vendor subtree standalone, as NVDL would present it — and on that all 38
Vensim elements in the corpus pass.

**One case the two mechanisms handle differently: standard elements *inside* a vendor
element.** Two of ours do this —

```xml
<vensim:saveper>TIME_STEP<doc>The frequency with which output is stored.</doc></vensim:saveper>
<vensim:rc kind="constraint" name="cold_is_dormant"><eqn>…</eqn><units/><doc/></vensim:rc>
```

— and we would like to keep it that way. A `vensim:doc` would be a second spelling of a
tag that already exists, which is precisely what we ask elsewhere in this document not to
be forced into.

Under 1a, 1a(i) and 1a(ii) this needs no provision at all, and we checked:
`processContents="lax"` validates a foreign element only when the processor holds
a schema for its namespace, and skips the whole subtree otherwise — the `<doc>` with it.
All three proposal schemas accept both forms above, including deeply nested standard
markup such as a `<gf>` with `<ypts>`. When the processor *does* hold the vendor's schema,
it is that schema's business to say what standard elements it permits, which is a thing
XSD can express.

Under 1a(iii) it has to be said out loud, because NVDL dispatches by namespace at every
level and would otherwise hand each standard child back to the XMILE section as a document
rooted at `<doc>` or `<eqn>` — elements the published schema declares only as local
children of stock/flow/aux. NVDL provides for exactly this through `useMode`, and
`xmile-vensim.nvdl` uses it: inside a Vensim element, every descendant `<attach>`es to
that section instead of starting a new one, so the vendor schema sees
`<vensim:rc><eqn/><units/><doc/></vensim:rc>` entire. Untested, like the rest of the NVDL
route.

**A limit of `lax` worth stating plainly**, since it cuts against 1a rather than for it: a
misspelled vendor element is not caught even when the vendor's schema is available.
`<vensim:netfloww>` validates, because `lax` means "validate if a declaration is found",
and none is. We confirmed this by importing our extension schema into the proposal schema
and trying it. A vendor that wants its own extensions genuinely checked wants 1a(iii),
where the dispatch is by namespace rather than by declaration; 1a is an interoperability
mechanism, not a proofreading one.

The practical answer available today is an ISO standard for validating compound documents,
brought in because the schema admits no extension point, and it still leaves the standard's
own `<smile>` invalid. 1a would remove the need for it.

### What we suggest

*Superseded. The TC took the 1.1 route, and we think that is the right answer; the
paragraphs below record what we argued before the decision and why we held it loosely.*

**1a plus the 1a(i) container, normative, with the 1.1 file as an informative companion** —
though we hold this less firmly than we did before measuring, and would not argue against
a TC that preferred 1.1.

The case for the hybrid is that it reaches every attachment point using a schema language
every implementer already has a processor for, and that it can be adopted in two steps: 1a
first, legalising the files vendors write today, then the container, which is the only part
that asks anyone to change anything. The case against it is that it is 302 lines where 1.1
is 11, and that it imposes a migration — including on us — that 1.1 does not.

What we no longer believe is that 1.1 costs implementers their validators, because
essentially nobody in this ecosystem is validating: three of our 101 files pass, and all
three are teacups. Parsing is untouched by the choice in every language. The real 1.1 cost
is that a C++ or C# implementation wanting to validate would have to buy a tool, while
Python — where conformance harnesses actually live — is fully served for free. A TC that
judged that acceptable would get a materially cleaner schema and nothing left closed, and
we would not object.

NVDL is not an alternative to any of the three: it changes what you validate with rather
than what is valid, so it is what a vendor does meanwhile, not what the standard says.

If the TC prefers to move in one step rather than two, 1a alone is still worth having: it
legalises the files vendors write today, which is the immediate problem, and the container
can be added later without invalidating anything it accepted.

Every figure above was produced by running the schemas, not by reading them — the sole
exception being the NVDL dispatch, flagged where it appears. All three schemas are
generated mechanically from the published schema by one script, a second script performs
the comparison, and both are yours if you want them.

| | file | changes the published schema | needs |
|---|---|---|---|
| 1a | `xmile-v1.x-proposal.xsd` | yes, +249 lines | any XSD 1.0 validator |
| 1a(i) | `xmile-v1.x-proposal-container.xsd` | yes, +302 lines | any XSD 1.0 validator |
| 1a(ii) | `xmile-v1.x-proposal-11.xsd` | yes, +11 lines | an XSD 1.1 processor |
| 1a(iii) | `xmile-vendor.nvdl`, `xmile-vensim.nvdl` | **no** | an NVDL processor (JVM) |

**1b — Prose.** Two rules for readers. A conforming implementation **MUST ignore elements
and attributes in namespaces it does not recognise**, and **SHOULD preserve them** when it
rewrites a file it has read. The second half is what makes a vendor extension survive a
round trip through a third tool, which is the property that makes extensions worth
having at all.

And two for writers, because an extension point with no discipline for using it turns every
gap in the standard into a private dialect.

**Vendor extensions MUST NOT be placed in the XMILE namespace itself** — the rule `<smile>`
currently breaks — and a vendor namespace **MUST NOT be used to respell, with the same
meaning, something the standard already spells**. Our own practice is the example we can
speak for: we write XMILE's `<doc>` and `<units>` inside our own elements rather than
inventing `vensim:doc`, because a second spelling of an existing tag costs a reader the
value and gains nobody anything.

That rule presupposes the standard's scope is right, and where it is not, the fix belongs
in the standard rather than in the writer. `isee:show_pages` looks like the textbook
violation — 47 files prefixed against 5 bare, by item 9's count — but paging a diagram
across a grid of printed pages is one product's view model, not a general one, and item 9
finds four of the REQUIRED attributes around it written zero times by anybody. On that
reading the prefix is the vendor being more accurate than the specification, and the
remedy is to move the paging attributes out of the standard, not to make isee write them
bare. We would rather say that plainly than cite the case as a violation it may not be.

**A writer SHOULD prefer the standard's own construct wherever the standard offers a
neutral equivalent, and reach for a vendor extension only where it does not.** We would
rather see that in a form a harness can check than as a sentiment: **stripping every
foreign-namespace element and attribute from a conforming file SHOULD leave a valid model
that still runs**. Delete everything in a foreign namespace, validate, simulate, compare.
It also gives the MUST-ignore rule above something worth having — a reader that discards
what it does not understand should be left with a model rather than a wreck.

We are the first to be constrained by this. `<vensim:netflow>` (item 2) is precisely the
case where a standard-expressible workaround exists, and the rule says we should write the
synthesised flow with a vendor *attribute* recording what it was — which is what item 2's
workarounds subsection already finds dominates the alternatives. Vendor markup that
annotates standard structure is additive; vendor markup that replaces standard structure is
a fork.

**Why the rule is a SHOULD and not stronger.** It asks a writer to accept the standard's
coverage as neutral ground, and in similar cases that coverage places the implementation
burden on different parties. Non-negativity is in the schema on `<stock>`, on `<flow>` and
again in `<behavior>`, settable by inheritance at model and global scope — and §4.2 and
§4.3 are candid that the tag itself does not do the work:

> "Note that non-negative is not directly supported by XMILE. The option exists partly for
> documentation, partly to allow a vendor to invoke a macro to implement the
> functionality."

That is a workable arrangement and we have no quarrel with it: the exporter writes what its
model says, the tag documents the intent for a reader that cannot honour it, and the
implementation burden falls to the importer, which §3.6.2 and §4.8.4 equip with built-in
macros and option filters for the purpose. A net-flow stock is the same kind of feature — a
property of how a stock or a flow behaves, supported by a limited number of tools — and
gets the opposite treatment: nothing in the schema at all, so the exporter must reshape the
model before writing it, and the burden falls on the one party that still holds the
original. XMILE has a pattern for features not every tool implements. It is applied in one
case and not in the analogous one. Where a vendor extension exists because of that, it is a
legitimate extension rather than a lazy one, and the SHOULD binds in proportion to how
evenly the coverage falls.

**Two carve-outs, the first of which matters more than it looks.** The test is "runs", not
"loads". Where the only standard-expressible form is runnable but *wrong*, a writer SHOULD
NOT produce it. Item 13's reordered range is the case — flatten it to the standard's name
matching and the
file validates, loads, simulates, and computes different numbers, with no equation changed.
An extension a reader must ignore is a visible gap; a silently wrong model is not. So the
preference order is: the standard form where it is correct; the standard form plus a vendor
annotation where the standard is lossy but sound; a vendor element where it is neither; and
declining to export where even that would mislead.

**And the test cannot always be passed.** Some models are not expressible in XMILE at any
level of effort — Ventity, our own tool, has entity types, runtime entity creation and
per-entity attributes, none of which XMILE has a word for. Stripping the extensions from
such a file leaves no model rather than a lesser one, and a rule that condemned it would be
condemning a writer for the language's scope.

So the SHOULD binds a writer who had a standard option, and for the rest the useful
obligation is a different one: **where stripping the extensions does not leave a runnable
model, the file SHOULD say so.** A reader can then tell, before it simulates anything,
whether what it is about to ignore was holding the model up. This is the one capability
declaration we would keep, and the contrast with the ones item 11 proposes to drop is
exact: `uses_arrays` is derivable by inspecting the file, and this is not derivable at all.
Where 1a(i)'s container is used it is the natural carrier.

There is a second-order benefit for the TC, and it is why we would press for these rules
rather than leave extension to taste. If writers follow them, the vendor elements left in
the wild are a census of what the standard cannot say — a standing agenda for the next
revision, gathered from what implementers actually needed rather than from what anyone
thought to propose. That is how we found half the items in this document, and it would be
a good deal easier to read if the merely convenient extensions were not mixed in with the
necessary ones.

---
