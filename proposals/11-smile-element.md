*Status against XMILE v1.1 (SDS Candidate Standard 02, 20 August 2024)
as reviewed 2026-07-30:* **New in this draft, and now half-answered.** The element appears in 88 of our 96 files, holding the namespace declaration and capability flags, and appears in neither the v1.0 prose, the v1.1 prose, nor the schema, while the documented `<options namespace=…>` is used 0 times. We understand from isee that `<smile>` is a legacy element equivalent to `<options>`; the item is now a transition plan, whose unfinished parts are what happens to the existing corpus and the one respect in which the two are not equivalent — `uses_arrays` levels have nowhere to port to.

*Re-checked 2026-08-20 against the schema added to `xmile-spec` on 2026-08-18:*
**Stands, untouched.** `<smile>` is still absent from the prose and from the schema; it
draws 71 errors in our corpus, in `<header>` where every file that has one puts it. The
transition plan this item proposes is unaffected by anything in 1.1.

---
# `<smile>`: the element every file has and no document describes

*Since drafting this item, we understand from isee that `<smile>` is a legacy element
equivalent to `<options>`. That settles the question the item was written to ask, and we
have rewritten the proposal below as a transition plan accordingly. The evidence is left as
gathered, because the size of the installed base determines how careful the transition has
to be — and because, on one point, the two are not quite equivalent.*

Items 5 and 9 concern requirements no implementation follows. This is the inverse, and it
is the more serious of the two: a practice every implementation follows that no document
describes at all.

Every Stella file opens its header like this:

```xml
<header>
    <smile version="1.0" namespace="std, isee"/>
```

`<smile>` appears in **88 of the 96 files** in our corpus. It is not in the v1.0 schema —
zero occurrences; `<header>` is an `xs:all` of `vendor`, `name`, `version`, `caption`,
`author`, `affiliation`, `client`, `copyright`, `created`, `modified`, `uuid`, `image`,
`options`, `product`, `contact`, `includes`. It is not in the v1.1 prose, and — we
checked — it is not in the v1.0 prose either: both documents mention SMILE exactly three
times, twice citing the SMILE PDF and once recounting how the name was chosen. **The
element has never been documented in any version of the specification.** Every file that
contains it is invalid on line 4, and 88 of 96 files contain it.

**What it carries is the part that matters.** Two things are riding on this undocumented
element:

*The namespace declaration.* Both artefacts place `namespace="…"` on `<options>`. Not one
file in our corpus does that — `<options namespace=…>` occurs **0 times**, while
`namespace="std, isee"` on `<smile>` occurs in 88. This bears directly on
[item 15](15-identifier-namespaces-question.md), which asks whether the
identifier-namespace mechanism of 3.2.2.3 is implemented by anyone. It is, universally — just not where the standard puts it. Any
reader honouring the documented location finds nothing, in every file it will ever be
given.

*The capability flags.* `<smile>` carries them as attributes, where the standard has them
as child elements of `<options>`:

```xml
<smile version="1.0" namespace="std, isee" uses_arrays="1" uses_conveyor="" uses_submodels=""/>
<smile version="1.0" namespace="std, isee" uses_arrays="3" uses_conveyor="" uses_submodels=""/>
```

Note `uses_arrays="1"`, `"2"`, `"3"` — a feature *level*, where `<uses_arrays>` in the
standard is a presence flag with a required attribute; and `uses_conveyor=""`, an empty
string standing in for "present". So `<smile>` is not a stray extra tag. It is a complete
parallel encoding of the `<options>` block, with different syntax and at least one
attribute carrying strictly more information than the standard's equivalent.

**And some of the flags are written by nobody at all, in either encoding.** `<uses_macros>`
is the clearest case. Three files in our corpus contain `<macro>` elements — two of them
produced by isee — and **not one of the three declares `<uses_macros>`**, on `<options>` or
on `<smile>`. The flag is required by the standard for exactly the situation these files
are in, and it is absent from all of them, including the files written by the vendor that
proposed it.

This is worth more than a tally: it suggests the capability block is the wrong mechanism,
not merely an ignored one. **Every fact these flags declare is
determinable from the file itself, more cheaply and more reliably than by trusting a
declaration**: a reader learns that a model uses macros by finding a `<macro>`, that it
uses conveyors by finding a `<conveyor>`, that it uses arrays by finding `<dimensions>`.
A redundant declaration has only two states — agreeing with the file, in which case it was
unnecessary, or disagreeing with it, in which case the reader must decide which to believe
and the standard does not say. The evidence is that writers do not maintain it, which is
what always happens to information that has to be kept in step by hand.

We therefore suggest a third option alongside the two below: **deprecate the capability
declarations outright**, in both encodings, and say that a reader determines a model's
requirements by inspecting it. That removes a class of drift rather than relocating it,
and it removes the awkward case where a file is unreadable *and* mis-declares why.

**Proposal.** We had drafted this item as a choice between documenting `<smile>` and
deprecating it, and isee's answer above settles that choice. We agree with the direction.
Three things need writing down.

1. **Say it in the specification.** `<smile>` is deprecated; writers SHOULD emit
   `<options>` instead. At present the standard is silent, so a vendor reading it has no
   way to learn that the near-universal practice is the deprecated one.

2. **Say what a reader does with a decade of existing files.** Deprecation does not make
   88 of 96 files valid, and those files will be read for years. Note that item 1's
   must-ignore-unknown rule does *not* rescue them: `<smile>` is in the XMILE namespace,
   so a `##other` wildcard rejects it by design, which is the point of `##other`. Making
   the legacy corpus validate needs `<smile>` declared in the schema as a deprecated
   optional child of `<header>` — the cost of which is one element declaration, against
   the alternative of the standard's own most common file shape remaining permanently
   invalid.

3. **Make sure `<options>` can actually receive what `<smile>` carries.** This is the part
   a bare "port it" instruction would leave undone, and the evidence above shows two gaps:

   - `namespace="std, isee"` ports cleanly — `<options namespace="…">` already exists in
     the standard and is exactly where the standard always wanted it. Nothing to add;
     writers simply move.
   - `uses_arrays="1" | "2" | "3"` does **not** port, and this is the one place the two
     encodings are not in fact equivalent: `<smile>` carries a feature *level*, where
     `<uses_arrays>` is a presence flag with a required `max_dimensions`. One of them has
     to give, and the TC should say which — either define the levels on `<options>`, or
     state the mapping and accept the loss.

   Unless, that is, the `uses_*` family goes away entirely, which is what we suggest
   above and what would make this third point moot. If the capability flags are dropped
   as derivable, the whole port reduces to moving `namespace` to the element the standard
   already specifies for it, and `<smile>` retires with nothing left to carry.

That is the outcome we would argue for: **drop the `uses_*` flags, move `namespace` to
`<options>`, declare `<smile>` deprecated but schema-legal so old files validate.**

None of this weakens the underlying point, which is why the item is worth raising even
now that the direction is agreed: for a decade the mechanism the standard defines for
declaring namespaces has been used by nobody, the mechanism everybody uses has been
described nowhere, and a validating reader has had to reject 92% of the corpus to be
conforming. That is also the strongest argument for item 1. Had there been a defined
extension point and a must-ignore-unknown rule, `<smile>` would have been a legal vendor
experiment that could be retired quietly, instead of a decade-old standing violation that
now needs a deprecation plan.

---
