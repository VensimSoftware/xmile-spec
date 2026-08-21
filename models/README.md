# Test models

Small, hand-checkable XMILE files, so a change to the schema can be judged against real
documents instead of by reading a diff. `tools/v-validate/` walks this tree and writes
one result file beside each model, which turns the effect of a schema change into a diff
of a `.txt`.

```sh
py -3.12 tools/v-validate/validate_xmile.py           # walk models/, write results
py -3.12 tools/v-validate/validate_xmile.py --stdout  # print instead
```

Result files are committed. A `.txt` that changes means the verdict changed.

The console run is grouped by these subfolders and by schema, with a subtotal per folder
and two summary tables at the end, so a schema change can be read as what it did and to
which group, not as one number.

## Layout

Subfolders record which version of XMILE a model is expected to conform to.

| Folder | Meaning |
|---|---|
| `v10-v11/` | conforms to both v1.0 and v1.1 |
| `pending/` | does not conform today, and the reason is a proposal item rather than a mistake in the file |
| `malformed/` | deliberately broken; fixtures for the validator itself, not for the schema |

Two more folders are named by convention but do not exist yet, because nothing we have
belongs in them. Create one when something does.

* `v11/` conforms to v1.1 only: it uses something 1.1 added, such as a sub-range, or
  avoids something 1.1 withdrew. This is where a file in `pending/` moves when the item
  blocking it is resolved.
* `v10/` conforms to v1.0 but not v1.1, which means it uses a device 1.1 withdrew: a
  knob, a switch, a button. Real Stella files are full of them, but none of ours is a
  *deliberate* test of a withdrawn feature.

`pending/` should shrink. Every file in it names the proposal item that would let it move
up; when that item is resolved the file moves to `v11/` and the item is retired from
`proposals/`.

## Provenance

| File | Origin | Folder | Why it is where it is |
|---|---|---|---|
| `teacup.xmile` | James Houghton, "Hand Coded XMILE", via the PySD test suite | `v10-v11` | The one file here that validates clean against both schemas. |
| `teacup.stmx` | isee systems, STELLA 10.0.6 | `pending` | Root element is in `http://www.systemdynamics.org/XMILE`, the pre-OASIS namespace. Kept as the record that files in the wild still use it. |
| `Educational-Outcomes.stmx` | isee systems, Stella (development build) | `pending` | `<smile>` in `<header>`, proposal item 11: the element every file has and no document describes. |
| `teacup.mdl.xmile` | Vensim export of `teacup.mdl` | `pending` | `view/@name` (item 9) and `vensim:attach` (item 1, the simple-type hole). |
| `teacup+perc.mdl.xmile` | Vensim export of `teacup+perc.mdl` | `pending` | As above, plus `<doc>` on `<start>`/`<stop>`/`<dt>`, item 4. |
| `teacup+macro.mdl.xmile` | Vensim export of `teacup+macro.mdl` | `pending` | As above, plus `vensim:output` on a macro, item 12. |
| `data.xmile` | Vensim export of `data.mdl` | `pending` | `<doc>` on the control parameters and `vensim:saveper`, both halves of item 4. |
| `YEAST4.xmile` | Vensim export of `YEAST4.MDL`, a Vensim sample model | `pending` | The largest of the exports; the same four causes at scale. |
| `data.err.xmile` | `data.xmile`, deliberately broken | `malformed` | Not well-formed XML, so that "not well-formed" is a tested path in the validator and not a branch nobody runs. |

The Vensim exports write what we propose, not what validates. `<doc>` on a control
parameter is item 4 asking to be allowed, not an oversight. Each is the smallest file
that demonstrates one item, which is why they are worth keeping.

Vensim `.mdl` sources are not copied here. They can be added if round-trip fixtures turn
out to be useful.

## A note on the folder names

`v10-v11` rather than `v1v11`, because two unrelated version numbers are in play: XMILE
v1.0 / v1.1 is the version of the standard, XSD 1.0 / 1.1 the version of the schema
language. `proposals/schema/` holds files named `-11` for the second sense, one directory
away, so `v1v11` would read as the other thing.
