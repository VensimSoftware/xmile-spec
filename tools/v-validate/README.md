# tools/v-validate - corpus validator

Walks `/models`, validates every model against several schemas at once, and writes one
result file beside each model.

```sh
py -3.12 tools/v-validate/validate_xmile.py                 # walk models/, write results
py -3.12 tools/v-validate/validate_xmile.py --stdout        # print instead of writing
py -3.12 tools/v-validate/validate_xmile.py --schema x.xsd  # one schema only (repeatable)
py -3.12 tools/v-validate/validate_xmile.py models/pending  # a subfolder on its own
```

Needs lxml: `py -3.12 -m pip install lxml`.

## What a run reports

Results are grouped two ways.

By schema: one column per schema, all the way down the run, so the effect of a schema
change is a column comparison.

By subdirectory: one block per folder under `/models`, each with its own subtotal. A
folder there records which version of XMILE its models are expected to conform to, so
"which group did this change help?" has an answer.

The run ends with two summaries:

```
errors by folder and schema
                         xmile-v1.0.xsd  xmile-v1.x-proposal.xsd
  malformed/                          0                        0
  pending/                           58                       43
  v10-v11/                            0                        0
  all                                58                       43

verdicts by folder and schema
                schema                         valid    expected  UNEXPECTED         n/a
  pending/      xmile-v1.0.xsd                     0           5           2           0
  pending/      xmile-v1.x-proposal.xsd            0           5           2           0
  ...
```

Error counts and verdict counts say different things. A schema change that halves the
error count while leaving every file `UNEXPECTED` has moved no model closer to
conforming; one that turns two files from `UNEXPECTED` to `expected` has, whatever it did
to the total. `n/a` counts files that never reached a schema, either not well-formed or
of a type no schema covers; they are charged to every column so they cannot go missing
from a count.

Exit code is 0 when every model is valid or fails only in expected ways, 1 on an
unexpected error, 2 when a file is not well-formed.

## How this differs from tools/validate.py

Two validators, two jobs. Neither replaces the other.

| | `tools/validate.py` | `tools/v-validate/validate_xmile.py` |
|---|---|---|
| Engine | `xmlschema` (Python) | lxml / libxml2 |
| Schema versions | XSD 1.0 and 1.1 | XSD 1.0 only |
| Can read `spec/schema/xmile.xsd.xml` | yes | no |
| Documents | named on the command line | walks a tree |
| Output | to the console | a committed `.txt` beside each model |
| Question it answers | does this document conform? | what did this schema change do to the corpus? |

`tools/validate.py` is the one CI runs, and the one that validates against the schema the
specification ships. Use it for any ordinary "is this file valid?" question.

This script measures what a proposed schema change is worth, which means running two
schemas over the same models and diffing the verdicts. Hence the per-schema columns, the
`EXPECTED` table, and result files with no timestamps in them, so they can be committed
and diffed.

It cannot read the v1.1 schema. libxml2 implements XSD 1.0 only, so
`spec/schema/xmile.xsd.xml` will not load: not "fails to validate" but "cannot compile
the schema". The same limit stops xmllint, nokogiri, PHP and .NET's `XmlSchemaSet`. That
is the tooling cost of the XSD 1.1 decision, and this script is where you can see it.

By default it runs `xmile-v1.0.xsd` and `xmile-v1.x-proposal.xsd`, both XSD 1.0, both
found by name in the search path below.

## The EXPECTED table

Errors Vensim's exports produce deliberately are listed in `EXPECTED` near the top of the
script, each with its reason. A model whose errors are all expected reports `all
expected` and does not fail the run; anything else is `UNEXPECTED`.

Most entries name a proposal item: `view/@name` is item 9, `<doc>` on a control parameter
is item 4. When an item is resolved, delete its entry, and the models it covers should go
green on their own. If they do not, the resolution did not cover what we thought.

## Schema search path

A schema named without a directory is looked for in this order:

1. `tools/v-generate/`, the published v1.0 baseline
2. `proposals/schema/`, schemas a proposal generated
3. `spec/schema/`, what the specification ships
4. beside the script

A schema given with a path is taken as given.

## Provenance

Copied from Ventana's XMILE test tree (`VensimTest/trunk/XMILE/minimal`), where it walked
its own directory. The changes here repoint it at `/models`, add the search path above,
and group the run by folder.
