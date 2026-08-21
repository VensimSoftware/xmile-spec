*Status against XMILE v1.1 (SDS Candidate Standard 02, 20 August 2024)
as reviewed 2026-07-30:* **Stands, essentially untouched.** The move to the SD Society changes who owns the document, not what it says: §3.5's built-ins and the whole array chapter are still one vendor's language.

*Rewritten 2026-08-20.* The earlier draft read the Stella function set as capture and
asked for the standard to be made vendor-neutral. That was the wrong request. The choice
of function set was reasonable. What would serve the community is a translation table,
not a more neutral canonical list. Reframed below, following the sd-tools thread at
<https://groups.google.com/g/sd-tools/c/KQIPH0QZ2uc>.

---
# Serving community needs is more useful than canonical form

isee has carried this effort for a long time, and the community has benefited from that
work. Nothing here is a complaint about it, and none of it asks for immediate change; it
probes a conceptual frame, which is where a discussion of this kind should start.

Our interest is narrow. We are not looking to use XMILE as an `.mdl` replacement. We
round-trip models through it to assess the fidelity of our translation work, and that
turns out to be a good way to find what can and cannot be represented cleanly. Most of
what follows came out of that.

## Union or intersection?

Behind the questions of restrictiveness and ambiguity is one question: should the
standard be the union of the features its constituent tools provide, or the intersection?

Intersection — the features common to most or all vendors — is the practical and
agreeable set, and it is most of what the standard already contains. "Stocks integrate
flow variables only" is the intersection view.

The rule is not applied consistently. A matched pair shows it:

- `<non_negative>` is in, as an option. It is native to Stella/iThink and InsightMaker,
  and absent from Vensim, Dynamo and Powersim.
- A net-flow stock is out entirely. It is native to Vensim and absent from Stella.

Both are features some vendors have and others do not; one was admitted as an option and
the other excluded. That is not a platform-neutral decision rule. Under the intersection
view either `<netflow>` should be an option too, or `<non_negative>` should be a vendor
tag. Item 2 argues the first. Here I only note that the two were decided in opposite
directions.

The `<non_negative>` text makes it worse. §4.2 lists it among the stock's OPTIONS, then
says:

> Note that non-negative is not directly supported by XMILE. The option exists partly for
> documentation, partly to allow a vendor to invoke a macro to implement the
> functionality.

What does "not directly supported" mean for something the standard directly names? If the
tag exists so a vendor can implement it with a macro, then on the intersection reading it
is a vendor tag, and saying so would cost nothing.

Macros show how this can work. The core is simple, and the features that are not
universal — local `sim_specs`, variable arguments, default values — are in the optional
section, with tiers of optionality inside it (`<macro>` options, `<recursive>`, and so
on). The core could probably grow by at least `<variables>` without challenging anyone.

Unfortunately, macro support is optional, and one of the key vendors (PySD) does not support them.

## The built-ins

§3.5 lists forty required built-in functions, all in the Stella spelling. Something had
to be picked, and the choice is fine. The objection is not to which dialect won; it is
that "canonical" is not the most useful goal available.

§3.5 is canonical and §3.6 puts function extensions in vendor namespaces, which until the
schema gained a wildcard in August 2026 may have been the only vendor namespace that
could be validated against the schema.

The result is silly in both directions. It is silly for Vensim to emit `vensim.SMOOTH`
when `SMTH1` means the same thing. It is also silly to require translation of something
that was already clear, at the cost of making the language unfamiliar to a large
population of readers.

§3.2.2.3 compounds this by asking every language to reserve the `std` names for collision
avoidance. That is clutter for many languages, and a problem macros cannot solve on their
own. Vensim, or Vensim users, must therefore reserve both SMTH and SMOOTH.

## An identifier crosstab

Publish a list of supported function constructs with a crosstab of how each is spelled in
each implementation. Rows are conceptual — "first order smooth" — and every vendor,
including `std`, is a column.

A conceptual row is what makes this a translation table instead of an annotated canonical
list, and it is what lets a new entrant add a column, after which everyone has their
Rosetta stone.

PySD is the working precedent. Its Abstract Syntax Tree, or Abstract Model
Representation, splits translation into parsers (Vensim `.mdl`, XMILE → AMR) and builders
(AMR → Python), with the AMR as a set of data classes. Its nodes are semantic, not
syntactic, so a smooth is a smooth, not a call to a function spelled `SMOOTH`. Both
parsers produce the same node, and the builder never sees either vendor's spelling.

Five reasons a crosstab beats a canonical list:

- It answers the question implementers have. Nobody needs to be told `SMTH1` exists; they
  need to know what corresponds to it, and what breaks.
- It can carry the caveats. Several pairs are not simple renames: `SMTH1`/`SMOOTH` differ
  in initial-value handling, `FORCST`/`FORECAST` in argument order and meaning,
  `INT`/`INTEGER` in truncation versus rounding, and `LOG10` fixes a base where Vensim's
  `LOG` takes one. A list has nowhere to put that sentence; a table cell does.
- It can record absences. `PREVIOUS` and `SELF` have no Vensim equivalent. A blank cell
  with a note is information; silence in a canonical list is not.
- It is additive. A new implementation is a new column, changing no semantics, needing no
  version bump, and invalidating no existing file. It can be maintained at the speed of
  the field instead of the speed of a standards revision.
- It is testable. A table is data, so a conformance suite can round-trip each row and
  report which mappings hold. Prose cannot be tested.

Combined with a revamp of namespace handling this would be cleaner than what §3.2.2.3
asks for today. A first step is a `functions.tsv` in this repository: a concept column, a
`std` column from §3.5, a Vensim column, open to anyone who wants to add theirs. It does
not need TC approval to be useful, only to be authoritative.

## The array chapter

§4.5 is built on "Apply-to-All" and "Non-Apply-to-All" arrays with an "array owner".
That is isee's vocabulary for a product feature rather than a term of art in the field,
and it arrived the same way and for the same good reason as the function names.

The remedy is cheaper here. §4.5 already glosses these parenthetically as "one equation
for the whole array" and "one equation per element". Lead with the gloss and keep
"Apply-to-All" as the alias. No semantics change, and the reader no longer needs one
product's feature names to get through the chapter.

## Two loose ends

The normative reference to *SMILE: A Common Language for System Dynamics* cites
`http://www.iseesystems.com/community/support/SMILEv4.pdf`, which returns "Page Not
Found". A normative reference should not disappear because a member reorganised their
website. Re-home it under the Society with a stable URL, or retire the citation as
historical; its content is in section 3 of XMILE now, so retiring it costs nothing.

`<smile version="…" namespace="…"/>` appears in the header of essentially every file one
vendor produces, and in neither the prose nor the schema. It looks as though the
`namespace` attribute, which the spec puts on `<options>`, was given a container of its
own at some point. It accounts for 71 errors in our corpus. Item 11 is the transition
plan; the point here is narrower — an unprefixed element in the standard's own namespace
is the one case the extension mechanism cannot help with, by design.

## Process

The four-step process sketched in the same thread is filed separately, in
[AA-suggested-process.md](AA-suggested-process.md). Step 3 there, simplifying the core,
is where the union-versus-intersection question above has to be settled.
