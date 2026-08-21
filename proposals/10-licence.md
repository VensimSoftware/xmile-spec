*Status against XMILE v1.1 (SDS Candidate Standard 02, 20 August 2024)
as reviewed 2026-07-30:* **New in this draft.** `<header>` carries author, affiliation, client, copyright, contact and uuid, but no `<license>` and no citation/DOI. `<copyright>` is free text and unused in all 96 files we have; the one model that asserts rights does so in a diagram text box.

*Re-checked 2026-08-20 against the schema added to `xmile-spec` on 2026-08-18:*
**Stands, untouched.** No `<license>`, no citation or DOI in `<header>`.

---
# There is nowhere to put a licence

`<header>` already contains a deliberate provenance block: `<author>`, `<affiliation>`,
`<client>`, `<copyright>`, `<contact>`, `<uuid>`, `<created>`, `<modified>`. The omission
from that list is the one field that decides whether a published model may lawfully be
reused. There is no `<license>` element in the specification or the schema — the word
appears in v1.1 only in the IPR boilerplate concerning patent licensing of the
specification itself.

`<copyright>` is the nearest thing, and it is free text: it states ownership, not terms of
reuse, and no tool can act on it. Across our 96-file corpus it is used **zero times**.

Meanwhile a modeller who does care records rights by drawing them on the diagram.
From `Molecules.stmx`:

```xml
<text_box uid="77" x="48.58" y="775.99" width="244.17" height="25.5">Copyright (c) 2017, 2018, 2019 Jim Hines</text_box>
```

— repeated across several views so that it appears wherever a reader happens to be
looking. A rights statement painted onto the canvas cannot be read by a tool, cannot be
searched, cannot be aggregated across a library of models, and is lost if the view is
deleted. There is no conforming alternative: item 1's missing extension point means the
choice is free text in `<copyright>` or a vendor namespace that invalidates the file for
everybody else.

This matters more now than it did in 2015. Models are published as research artefacts —
deposited with DOIs, attached to journal articles, aggregated into teaching libraries and
model repositories. A machine-readable licence is what makes such a collection reusable
rather than merely readable, and it is precisely the field a repository needs to index.

**Proposal.** Add two OPTIONAL children of `<header>`:

1. `<license>` — RECOMMENDED to hold an SPDX short identifier (`CC-BY-4.0`, `MIT`,
   `GPL-3.0-or-later`) so it is machine-comparable, with an OPTIONAL `url` attribute for
   the full text and free text permitted for anything SPDX does not cover.
2. `<citation>` — a DOI or bibliographic reference for the model as a published artefact.
   `<uuid>` establishes identity but says nothing about how to cite the thing.

Neither affects simulation semantics, and both are inert for tools that ignore them. The
cost to an implementer is one optional element; the gain to a publisher is something no
amount of free text can provide.

---
