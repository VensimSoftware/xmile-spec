*Status against XMILE v1.1 (SDS Candidate Standard 02, 20 August 2024)
as reviewed 2026-07-30:* **New in this draft.** No subset, equivalence or mapping between dimensions; §3.7.1.1 relates sub-ranges by a name match §2.1 says is meaningless; `@` positions exist only because dimensions cannot be named apart; name matching cannot express a permutation of the same element set at all; and §3.7.1.3 lets two conforming tools compute different numbers.

*Re-checked 2026-08-20 against the schema added to `xmile-spec` on 2026-08-18:*
**Stands, untouched.** Sub-range support was added before this review and is already
accounted for in the item.

---
# Dimensions cannot be related to one another, and the workarounds contradict each other

This is the largest remaining gap, and it is one gap rather than several. XMILE's
dimensions are flat and mutually independent: there is no way to declare that one is a
subset of another, that two are the same range used twice, or that elements of one
correspond to elements of another. Every array feature that looks like it supplies such a
relationship turns out to be a workaround for its absence, and two of them contradict the
specification elsewhere.

### The evidence

**1. Sub-ranges rest on a rule §2.1 says is meaningless.** §3.7.1.1 relates a sub-range to
its superset by name:

> "element matching is done by the simulation engine to pair together identical elements
> from a sub-range and its superset."

But §2.1 states the opposite about element names:

> "Dimension names, in turn, define their own Element namespace. Thus, even though Array
> Dimension names must be unique, they can have overlapping Element names… (as in
> `Location.Boston`, where Location is a Dimension name with element Boston)."

If §2.1 holds, `Location.Boston` and `LocationTotal.Boston` are two *distinct* elements
that share a spelling, exactly as two locals in different scopes may. §3.7.1.1 then pairs
them *because* the spellings match. And since nothing declares that `LocationTotal` is a
superset of `Location`, the collision is the only signal available — the one signal §2.1
says carries no meaning. The feature is also optional ("if an implementor… wishes to
support sub-range functionality"), so a model using it computes different results in two
conforming tools.

**2. The `@` operator exists because dimensions cannot be named apart.** §3.7.1.2 is
explicit: *"Dimension positions: **when dimension names are not unique** and the desired
order is not an exact reversal…"*. It is needed only because XMILE permits `DimM × DimN ×
DimN`, an array with the same dimension twice and no way to say which is which. Vensim
never needs it: a range used twice in one variable is declared as two *equivalent* ranges
with distinct names — `FromCity <-> City`, `ToCity <-> City` — so `Inbound Trips[FromCity,
ToCity]` names both axes unambiguously and transposition is expressed by naming, not by
counting. A declaration mechanism removes the need for the positional escape hatch.

**3. Aggregation is positional where the concept is set-based.** `*` means "this entire
axis", so with sub-ranges in play it cannot distinguish summing over a family from summing
over one of its subsets. In our test model `SUM(trips[City!])` and `SUM(trips[East
City!])` aggregate the same variable over the same axis and differ only in *which set*;
`*` can express only the first. The other slice form does not help: `A[1:3]` is ordinal —
"the first three elements even if that dimension has named indices" — while §3.7.1.1
itself says sub-range elements "do not have to be specified in the same order they appear
in their superset". The standard offers positional slicing for a concept it defines as
order-independent.

**4. Mappings have no expression at all.** `Region: East, West -> (City: East City, West
City)` states that each city belongs to a region, so `City Weather[City] = Region
Weather[Region]` reads a regional value at city granularity. Nothing in XMILE relates two
dimensions this way. The workaround is to build an explicit 0/1 membership array and sum
against it — which is what a format without mappings forces a modeller to write by hand,
and it is O(cities × regions) where the declaration is O(1).

**5. Name matching cannot express a permutation — by construction.** This is the sharpest
form of the objection. It is an impossibility, not a missing feature.

A range may be declared as the same elements in a different order, and mapped onto the
original:

```
City:        East City, West City        (Boston, New York, Seattle, San Jose)
Sister City: West City, East City -> City
```

`Sister City` contains exactly City's elements, reordered. The mapping onto `City` is
therefore positional and pairs each city with its opposite number — Seattle with Boston,
San Jose with New York — so that `Sister City Inbound Trips[Sister City] = City Inbound
Trips[City]` gives every city its partner's traffic. The reordering *is* the content.

XMILE relates two dimensions by matching identical element names (§3.7.1.1). Applied here
it pairs Boston with Boston and Seattle with Seattle: the identity. And no amount of
extra declaration can rescue it, because the two ranges hold **the same names** — the
mechanism has nothing left to distinguish the intended pairing from the trivial one. A
correspondence that is *not* name-equality cannot be written in a language whose only
correspondence *is* name-equality.

We hit this in our own exporter before noticing it in the standard: classifying such a
range as "a copy of City" and omitting its element list turned the permutation into the
identity, and **no equation changed** — every formula still read the same, while the model
computed something else. That is the failure mode this item is about, and a diff of the
equations cannot detect it.


### A separate and more serious problem in the same chapter

§3.7.1.3 says that when a slice does not match the array:

> "they will be truncated or extended (potentially with zeroes) as necessary. **Extension
> is non-standard with the implementation free to handle it by either filling with zeroes
> or additional elements from the same array.** A warning SHOULD be generated whenever a
> range is truncated or extended."

Two conforming implementations may therefore produce **different numbers from the same
model**, with only a SHOULD-level warning. For an interchange format that is the most
serious kind of defect there is: not a file that fails to load, but one that loads
everywhere and simulates differently.

It is also hard to square with §3.7.1.1, which makes the analogous case mandatory:

> "In the case where an array element is encountered on the right-hand side which is not
> present in the dimension for the variable it is used with a 0 MUST be returned, NaN is
> not allowed."

One section requires 0 for a missing element; the other leaves the implementation free to
substitute zeroes *or* other elements of the array. And the §3.7.1.1 wording is itself
ambiguous — "a 0 MUST be returned" could be read as a zero index or a zero value, and only
the "NaN is not allowed" clause settles it toward a value, by inference rather than
statement.

### What we would ask for

1. **Declare relationships instead of inferring them.** A dimension should be able to
   state that it is a subset of another, an equivalent of another, or mapped element-wise
   onto another. This removes the dependence on name collision, resolves the conflict with
   §2.1, and makes `@` positions unnecessary.
2. **Allow a set where a slice is expected.** With subsets declared, `SUM(trips[East_City])`
   says exactly what Vensim's `SUM(trips[East City!])` says, with no new expression syntax
   — a dimension name simply becomes legal in a slice position.
3. **Replace the truncate/extend licence with an error.** A mismatched range should be a
   diagnostic, not an implementation-defined result. If silent behaviour must be retained
   for compatibility, make the 0-fill mandatory so that at least all conforming tools agree.
4. **Say plainly whether §3.7.1.1's "0" is an index or a value.**

### What we ship, and why it is shaped this way

We have implemented the export side of this in Vensim, as a demonstration rather than a
proposal of syntax. It is offered because it is easier to argue about something concrete,
and because it shows the cost of the four asks above is small.

```xml
<dim name="City" vensim:kind="family">
  <elem name="Boston"/><elem name="New_York"/><elem name="Seattle"/><elem name="San_Jose"/>
  <dim name="East_City" vensim:kind="subrange">
    <elem name="Boston"/><elem name="New_York"/>
  </dim>
  <dim name="West_City" vensim:kind="subrange">
    <elem name="Seattle"/><elem name="San_Jose"/>
  </dim>
  <dim name="FromCity" vensim:kind="equivalent"/>
  <dim name="ToCity" vensim:kind="equivalent"/>
</dim>

<dim name="Region" vensim:kind="family">
  <elem name="East"/><elem name="West"/>
  <vensim:map from="East" to="East_City"/>
  <vensim:map from="West" to="West_City"/>
</dim>
```

Three decisions in that, each of which the TC would face too:

**Relationships are declared, never inferred.** `vensim:kind` says what a range is —
`family`, `subrange`, `equivalent` or `copy` — and our reader takes the relationship from
that alone. It never matches element names across dimensions, because §2.1 says a name
match carries no information. This is the whole of ask 1, and it is one attribute.

**Nesting states parentage**, so no parent attribute is needed and an orphan cannot be
written. It also gives encapsulation: copying a `<dim>` carries the family, its subranges,
its equivalents and its mappings as one unit, which is the property a person or an editor
wants. Nesting is a declaration site and *not* a scope — dimension names stay global, as
§2.1 requires, so no equation resolves differently because of where a declaration sits.

**A member list is heterogeneous, and `<dim>` cannot be.** A range is declared from a
mixture of elements, subranges and sequences —

```
City:    East City, West City                      two subranges
aFamily: anElement, (numeric1-numeric3), aSubRange an element, a sequence, a subrange
```

— whereas `<dim>` admits `<elem>` and nothing else. So the flat element list is not a
lossy rendering of the declaration, it is a different kind of thing: it can say *which
elements a range contains* but never *how the range was built*. We keep the declaration in
`<vensim:members>` and write it ahead of the `<elem>` list it supersedes. Three things go
otherwise, and the third changes results: which subranges compose a family; that a run of
elements was written as a sequence; and the element ORDER, where a range is deliberately a
reordering of another.

**Mappings are explicit pairs.** Vensim declares them positionally — `Region: East, West
-> (City: East City, West City)` — and we expand that to one `<vensim:map>` per pair, so
the file does not depend on order. An element may map to a subrange (the common case) or
to a single element.

The cost of all this, measured against the published schema, is that a `<dim>` may not
carry a foreign attribute, may not contain a nested `<dim>`, and may not contain a foreign
element. Three content-model relaxations, or one `xs:any` and one `anyAttribute` if item 1
were adopted first.

**What we could not demonstrate**, because it needs a change in the equation language
rather than the declarations: aggregation over a declared subset. Vensim writes
`SUM(trips[East City!])`; the XMILE equivalent would be `SUM(trips[East_City])`, a
dimension name in a slice position, which is ask 2. Until that exists we can express the
structure but not the operation that motivates most of it.


### And a suggestion about scope

We think the array chapter is where the standard has moved furthest from describing
common ground. There is little agreement between products on ordinal slicing, transposition,
mismatched-range behaviour or sub-range semantics, and the sections above show the text
does not fully agree with itself either. Our own model's constructs — subranges, equivalent
ranges, mappings, `:EXCEPT:` — are not exotic, and none of them can be said at all.

We would rather see the chapter **profiled** than enlarged: a small core that every tool
implements and that carries most real models — named dimensions, apply-to-all equations,
per-element equations, and whole-array aggregation — with the contested remainder moved
to an optional layer or left to vendor namespaces until practice converges. That is close
to what happened with `flow_concept` in 1.1: a documented way to say something rather than
a mandated semantics.

We say this as the vendor whose constructs are the ones missing, and are aware how that
reads. But the alternative to profiling is not neutrality — it is a standard that mandates
one product's array model in detail, which item 7 takes up, not a separate one.
