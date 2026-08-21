# tools/v-generate - schema generators

Mechanical transforms of the published v1.0 schema, used to demonstrate a proposed change
and measure what it costs. Nothing here is hand-edited output: generating rather than
editing is what makes the difference between the baseline and the proposal provably only
the change being proposed.

```sh
py -3.12 tools/v-generate/make_proposal_xsd.py              # XSD 1.0 wildcards
py -3.12 tools/v-generate/make_proposal_xsd.py --xsd11      # XSD 1.1 open content
py -3.12 tools/v-generate/make_proposal_xsd.py --container  # a single <extensions> child
py -3.12 tools/v-generate/check_proposal_xsd.py             # self-check: accepts / still rejects
py -3.12 tools/v-generate/compare_proposals.py              # what each form costs
```

`make_proposal_xsd.py` and `check_proposal_xsd.py` need lxml. `compare_proposals.py` needs
`xmlschema` as well, because one of the three schemas it compares is XSD 1.1 and lxml
cannot read it.

## What is here

| File | |
|---|---|
| `xmile-v1.0.xsd` | Input. The published OASIS Standard schema, 14 December 2015, unmodified. Every generated schema is this file plus one change. |
| `make_proposal_xsd.py` | Generates the three vendor-extension schemas into `proposals/schema/`. |
| `check_proposal_xsd.py` | Asserts the generated XSD 1.0 schema accepts everything the published one accepts, plus vendor markup, and still rejects junk. |
| `compare_proposals.py` | Measures the three forms against each other and against `/models`: how much of the schema each touches, whether they agree on real files, and what running each one requires. |

## Why the v1.0 baseline is kept here

`spec/schema/xmile.xsd.xml` is the v1.1 schema. The generator needs the v1.0 one, which
is not in the working tree. It is in this repository's history, at the commit that added
it, but a generator that reaches into git history for its input is a generator nobody can
run, so the baseline is stored beside the script.

One difference worth recording: the copy here is the OASIS Standard of 14 December 2015,
while the one in this repository's history is Candidate OASIS Standard 01 of 29 July
2015, which is also what `spec/schema/xmile.xsd.xml` names as its source. The two were
diffed and are identical apart from whitespace and the provenance comment, so nothing
turns on the choice. The Standard is the authoritative artefact, so this uses it.

## The three forms

All three say the same thing: a vendor may add elements and attributes in its own
namespace, and nothing else. They differ in what it costs to say it.

| Form | Cost | Leaves closed |
|---|---|---|
| XSD 1.0 wildcards | 143 wildcard particles, +249 lines | 27 `xs:all` content models, which XSD 1.0 cannot open at all |
| `<extensions>` container | a single child element per type | vendor markup only in one place, not where it belongs |
| XSD 1.1 open content | 2 declarations plus 4 exemptions, +11 lines | nothing |

Against that stands the tooling penalty. libxml2, and so lxml, xmllint, nokogiri and PHP,
implements XSD 1.0 only, as do .NET's `XmlSchemaSet` and Java's default JAXP path. None
of them can load the 1.1 file. `compare_proposals.py` demonstrates that rather than
asserting it.

The specification took the XSD 1.1 route on 2026-08-18. The other two forms are closed,
not competing. The generator is kept because the comparison is what made the case, because
`00-corpus-validation.md` cites its output, and because the same machinery applies to the
next proposal.

On the file names: `-11` means XSD 1.1, the version of the schema language. It has
nothing to do with XMILE v1.1, the version of the standard. The two version numbers are
unrelated and both are in play here.

## Provenance

Copied from Ventana's XMILE test tree (`VensimTest/trunk/XMILE/minimal`). The only
changes repoint input, output and corpus at this repository's layout; regenerating
produces files byte-identical to the ones copied across.
