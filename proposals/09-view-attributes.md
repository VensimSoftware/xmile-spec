*Status against XMILE v1.1 (SDS Candidate Standard 02, 20 August 2024)
as reviewed 2026-07-30:* **New in this draft**, raised against 1.1 §5.1.2: five REQUIRED view attributes appear in **none** of the 65 files with views among the 96 we have, the extent encoding implementations use (`isee:page_cols`/`isee:page_rows`) is in neither the text nor the schema, and standard attributes such as `show_pages` are more often written vendor-prefixed than bare.

*Re-checked 2026-08-20 against the schema added to `xmile-spec` on 2026-08-18:*
**Stands, untouched, and now confirmed against the schema.** `<view>` still has no `name`
attribute - 52 rejections in our corpus - and 5.1.2 still marks `width`, `height` and the
paging and navigation attributes REQUIRED. The new vendor wildcard does not rescue
`name`: it excludes `##local`, correctly, so an unprefixed attribute must still be one
the schema declares. Fixing this needs a change to the schema or the text.

---
# `<view>` requires attributes that nobody writes, and omits the one everybody does

v1.1 §5.1.2 states:

> "XMILE views are also REQUIRED to have a `width` and a `height` measured in pixels."

and then requires `page_width`, `page_height`, `page_sequence`, `page_orientation`,
`show_pages` ("In order for XMILE views to be printed each view is REQUIRED to specify its
paging"), plus `home_page` and `home_view` for navigation. We surveyed our test corpus of
96 XMILE/STMX files, 65 of which contain `<view>` tags, most written by Stella:

| attribute | status in 1.1 | files, bare | files, `isee:`-prefixed |
|---|---|---|---|
| `width`, `height` | REQUIRED | **0** | **0** |
| `page_sequence` | REQUIRED | **0** | **0** |
| `page_orientation` | REQUIRED | **0** | **0** |
| `order` | OPTIONAL (new in 1.1) | **0** | **0** |
| `home_page` | REQUIRED | 1 | 0 |
| `home_view` | REQUIRED | 28 | 0 |
| `show_pages` | REQUIRED | 5 | **47** |
| `page_width`, `page_height` | REQUIRED | 62 | 0 |
| `zoom` | OPTIONAL | 42 | 0 |
| `background` | OPTIONAL | 46 | 0 |
| `scroll_x`, `scroll_y` | OPTIONAL | 11, 11 | 22, 17 |
| `page_cols`, `page_rows` | **not in the specification** | 4, 0 | **36, 36** |
| `converter_size` | **not in the specification** | 11 | 12 |
| `name` | **not in the specification** | 15 | 4 |

Four REQUIRED attributes are entirely unwritten, in any form, and `home_page` appears once
in 65 files; a reader enforcing them would reject nearly every file we have, including
files produced by the tool whose authors wrote the section.

**Two things a view's extent is recorded as, neither of them `width`/`height`.** Stella
writes `isee:page_cols` and `isee:page_rows` in 36 files — columns and rows of printed pages, which
multiplied by `page_width`/`page_height` give the canvas size. This is arguably the better
encoding: it ties the canvas to the paging the same section already requires, and it
survives a change of paper size. It also shows that a view's extent is genuinely *not*
derivable from its contents — the canvas is a print layout, deliberately larger than the
diagram it holds — so `width`/`height` is not merely redundant with the member bounding
box. To isee's credit these are properly namespaced, which is the discipline item 1 asks
the standard to make available to everyone.

**The reverse problem is worse: standard attributes written in a vendor namespace.**
`show_pages` is a plain XMILE attribute, yet appears as `isee:show_pages` in 47 files and
bare in only 5; `scroll_x`/`scroll_y` are similarly split. A conforming reader looking for
`show_pages` finds nothing in 47 files where the value sits in plain sight one prefix
away. Over-namespacing loses interoperability exactly as under-namespacing does, and the
split counts on `scroll_x`, `converter_size` and `name` suggest the boundary between
standard and
vendor is not clear even to the vendor. `name` is the sharpest case: written bare 15 times
and prefixed 4 by the same tool — which is what happens when the standard offers no home
for a real piece of data (see item 5).

So one fact has three competing encodings — pixel `width`/`height`, `page_cols` ×
`page_rows`, and the bounding box of the member objects — with the standard requiring the
first, implementations writing the second, and no statement anywhere of which governs or
what a reader should do when they disagree. Is a view with `width="500"` containing an
object at `x="1000"` conforming? The specification does not say, and a reader must guess
whether to clip, grow, or ignore.

**Proposal.**

1. Make `width`/`height` OPTIONAL, with a defined fallback: the bounding box of the
   view's member objects, or an implementation default for an empty view (which has no
   bounding box — and empty views are real content, since modellers keep them so that the
   view name acts as a separator in a view menu).
2. Adopt `page_cols`/`page_rows` into the standard, or say explicitly that canvas extent is
   expressed in pixels and page counts are derived. Either resolves the ambiguity; leaving
   the encoding that implementations actually use undocumented does not.
3. Reduce the paging and navigation attributes to OPTIONAL-with-defaults. `home_page` is
   already given "default: 0" and `home_view` "default: false" in the very sentence that
   calls them REQUIRED, which suggests the intent was always that a reader could manage
   without them. Or take them out of the standard altogether, which we think is the better
   answer: paging a diagram across a grid of printed pages is one product's view model
   rather than a general one, the counts above are what a feature looks like when only its
   author implements it, and a vendor namespace is where most of it is already written.
4. State the rule for a *standard* attribute that appears in a vendor namespace — whether
   a reader should honour `isee:show_pages` as `show_pages`, or ignore it. Given the counts
   above, readers are already deciding this for themselves, differently. Item 1b proposes
   the writer-side half, that a vendor namespace MUST NOT respell a standard tag; the
   reader-side half is needed regardless, for the files that already exist. Note that if 3
   is taken the second way, `isee:show_pages` stops being a respelling at all and becomes a
   correctly namespaced vendor attribute — which is an argument for taking it that way.

The same section over-requires at object level too: "All display objects contained within
an XMILE file MUST have the following attributes: Position … Size `width`, `height`" —
while the paragraphs immediately below supply shape defaults (rectangle for a stock,
circle for an auxiliary) and make `width`/`height` optional line-wrapping *hints* on
`name_only` shapes that "may be ignored without consequence". The blanket MUST contradicts
the shape system beneath it.

By contrast §5.1.3 gets this right, requiring `uid` only on objects referred to elsewhere
and stating that UIDs are "NOT REQUIRED to be stable across successive reads and writes".
That is the discipline we are asking for on view attributes: require what a reader cannot
proceed without, and default the rest.

---
