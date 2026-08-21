# The function crosstab, first cut

A working table of the kind item 7 asks the TC for, built from five sources. Generated
2026-08-21 by `tools/v-generate/make_crosstab.py`; do not edit the `.tsv` files by hand.

| Source | Licence | Read from |
|---|---|---|
| **XMILE v1.1**, SDS Candidate Standard 02 — section 3.5, Built-in Functions | — | `spec/03-model-equation-structure.adoc` in this repository. Version 1.0 is at <https://docs.oasis-open.org/xmile/xmile/v1.0/os/xmile-v1.0-os.html> |
| **xmutil**, Robert Eberlein — <https://github.com/bobeberlein/xmutil> | MIT, © 2018 bobeberlein | `src/Function/Function.h`, `src/Xmile/XmileFunctions.cpp` |
| **Vensim**, Ventana Systems — <https://vensim.com> | source proprietary; the facts extracted here are MIT, © 2026 Ventana Systems, Inc. | `src/vensim/XMILEFunctions.{h,cpp}` |
| **PySD**, PySD contributors — <https://github.com/SDXorg/pysd> | MIT, © 2013-2022 PySD contributors | `pysd/translators/structures/abstract_expressions.py`, `translators/{vensim,xmile}/*_structures.py` |
| **SDEverywhere**, Climate Interactive — <https://github.com/climateinteractive/SDEverywhere> | MIT, © 2016-2024 Todd Fincannon and Climate Interactive / New Venture Fund | wiki: [Supported Vensim Functions](https://github.com/climateinteractive/SDEverywhere/wiki/Supported-Vensim-Functions), [Supported XMILE and Stella Functions](https://github.com/climateinteractive/SDEverywhere/wiki/Supported-XMILE-and-Stella-Functions) |

All four implementations' contributions are MIT here. Three are MIT at source. The
Vensim column comes from our own tree, which is not public, so only the extracted names
and flags appear in these tables — and those, the generator, and the derived structure are
released under MIT, © 2026 Ventana Systems, Inc. See [LICENSE-Ventana.md](../../LICENSE-Ventana.md),
which also says what it does not cover.

The point of building it now is that the design in `07a-crosstab-design.md` predicts
things — that implementations key on arity, that a forward-only mapping loses
information, that two directions held separately drift — and a table either shows those
or it does not.

## Start here

[SUMMARY.md](SUMMARY.md) is the one-screen view, and the one to hand to somebody who will
not open a TSV. It splits the columns into two groups that answer different questions:
`xmile std`, `stella` and `vensim` are **languages**, giving each one's spelling of the
concept; `pysd`, `sde` and `xmutil` are **tools**, giving what each covers. It is
sectioned by whether a correspondence exists at all — 42 concepts translated between
languages, 86 on the XMILE side only, 37 on the Vensim side only.

The XMILE-only section is a worklist. A concept with a Stella spelling and no Vensim one
is either a real gap in every translator or a function with no Vensim equivalent, and
only a person can tell those apart. `BETA` was the first found that way: it is Vensim's
`RANDOM BETA`, which no tool maps. That correspondence is now in the tables, marked
`ventana/manual`, since it is asserted rather than extracted.

## The five tables

Relational rather than one wide sheet, so it can be read in either direction. The wide
pivot is generated from the others for human reading.

| File | Rows | Grain |
|---|---:|---|
| `SUMMARY.md` | 165 | the readable view, sectioned; languages and tools kept apart |
| `summary.tsv` | 165 | the same, as data |
| `concepts.tsv` | 165 | one per concept, with how many dialects reach it |
| `spellings.tsv` | 252 | one per (concept, dialect, spelling), with verification flags |
| `edges.tsv` | 119 | one per asserted correspondence, with the source that asserted it |
| `support.tsv` | 226 | one per (spelling, implementation), with support status |
| `crosstab.tsv` | 165 | the pivot: concept against dialect, with arities and notes |

A name existing in a dialect and an implementation supporting it are different facts, so
they are different tables. `support.tsv` is where the second kind lives.

Bidirectionality falls out of `edges.tsv`. A row records that some implementation claims
Vensim `SMOOTH` at two arguments is XMILE `SMTH1`; querying by either column is the same
query.

## Columns

`concepts.tsv`

| Column | |
|---|---|
| `concept` | identifier for the equivalence class, taken from its `std` spelling where there is one and a Vensim spelling otherwise |
| `n_spellings` | how many `(dialect, spelling)` pairs are in the class |
| `dialects` | which dialects those spellings are in |
| `reach` | `linked` when the class spans more than one dialect, meaning some source asserted a correspondence; otherwise `std-only`, `vensim-only` or `pysd-only`, naming the single dialect it sits in. Not a claim about any particular pair of dialects — read `dialects` for that. |

Today: 54 linked, 86 `std-only`, 25 `vensim-only`. Every one-dialect concept has exactly
one spelling, so `reach` there also means "no source has mapped this to anything".

`spellings.tsv`

| Column | |
|---|---|
| `concept` | which class this spelling belongs to |
| `dialect` | `std`, `vensim` or `pysd` |
| `spelling` | the name as that dialect writes it, or the node type for `pysd` |
| `checked_vs_vensim` | `yes` where Vensim's registry records the mapping as manually verified to produce Vensim's result, `no` where it records the opposite, empty where the source has no such flag |
| `differs` | `yes` where Vensim's registry marks the XMILE implementation as not equivalent |
| `notes` | anything the source said in passing, such as an appended default argument |

`edges.tsv` — the asserted correspondences, one row each.

| Column | |
|---|---|
| `concept`, `from_dialect`, `from`, `to_dialect`, `to` | the correspondence |
| `args` | argument count where the source keyed on one, empty where it did not |
| `source` | which file asserted it, so any row can be checked against its origin |

Direction is recorded as the source stated it, not normalised. `xmutil/Function.h` rows
run Vensim to std because that is the direction that table translates; `kArityMap` rows
run the other way. Reading the table in one direction means ignoring `from`/`to` and
treating each row as an undirected pair, which is what the concept grouping does.

`support.tsv` — which implementation implements what.

| Column | |
|---|---|
| `concept`, `dialect`, `spelling` | what is being implemented |
| `implementation` | `sde/c` or `sde/js` today; any tool can add rows |
| `status` | `yes`, `no` or `partial` |
| `notes` | what `partial` means for that row |

`crosstab.tsv` — the pivot, generated from the others. One column per dialect holding
that dialect's spellings joined by ` | `, plus `args_seen` and `notes`.

## Concepts are derived, not curated

No one sat down and wrote a list of concepts. Each source contributes edges between
`(dialect, spelling)` pairs, and a concept is a connected component of that graph. A
concept with one member exists because no implementation asserted a correspondence for
it, which is a fact worth recording rather than a gap to fill in.

That is what makes this the union of what is known. 54 of the 165 concepts are linked
across more than one dialect; 111 sit in one dialect alone — 86 XMILE functions Vensim
recognises but has never needed to translate, and 25 Vensim functions SDEverywhere names
that no XMILE translation covers.

## What each source contributes

| Source | Facts | Contribution |
|---|---:|---|
| spec §3.5 | 40 | the names `std` defines, with parameter counts; also what separates `xmile std` from `stella` in the summary |
| xmutil | 92 | 56 Vensim→XMILE edges from `Function.h`, 20 from `kFuncMap`, 16 arity-keyed from `kArityMap` |
| Vensim | 121 | 140 registrations, of which 12 assert an edge; the rest are recognised without a translation |
| PySD | 15 | hand-entered from the AST node set, marked `pysd/manual` |
| SDEverywhere | 113 | both wiki pages, transcribed; support status rather than spellings |
| Ventana | 1 | correspondences we know that no tool implements, marked `ventana/manual` |

Vensim's registry carries two flags this table wanted anyway, so they are extracted
rather than invented: `checked_vs_vensim` records whether a mapping was manually verified
to produce Vensim's result, and `differs` marks a function whose XMILE implementation is
not equivalent. Across 252 spellings: 9 checked, 112 explicitly not checked, 131 unknown
because their source records no such flag. The three-state cell the design argued for is
already needed on the first cut.

## What SDEverywhere adds

It contributes no spellings of its own, using each dialect's own names, but it is the
only source that says whether anything is **implemented**. Its C and JavaScript targets
disagree on 8 Vensim functions, all of them supported in C and absent from JavaScript:
`ALLOCATE AVAILABLE`, `ALLOCATE BY PRIORITY`, `DELAY FIXED`, `DEMAND AT PRICE`,
`DEPRECIATE STRAIGHTLINE`, `FIND MARKET PRICE`, `GAMMA LN` and `SUPPLY AT PRICE`. Three
functions are supported only in part: `DEPRECIATE STRAIGHTLINE` ignores the fiscal-period
argument, `GET DIRECT SUBSCRIPT` reads csv but not xlsx, and `VECTOR SELECT` implements
two of its numerical actions.

None of that fits a spelling table, which is why `support.tsv` exists. It generalises:
any implementation can add rows without touching the spellings.

It also raised the Vensim spelling count from 66 to 90, naming functions no XMILE
translation covers at all — `QUANTUM`, `PULSE TRAIN`, `SAMPLE IF TRUE`, `GAMMA LN`,
`DEMAND AT PRICE`, `SUPPLY AT PRICE`, `FIND MARKET PRICE`, `DEPRECIATE STRAIGHTLINE`.

One caution about provenance: both pages were read through a web fetch and transcribed
into the generator by hand, and the XMILE page ends with a catch-all row covering
everything unsupported. Absence from the transcription is therefore not evidence of
anything. The rows present are marked `sde/manual` for the same reason the PySD rows are.

## What the first cut shows

**Arity is load-bearing.** 9 concepts carry more than one arity, and in every case the
arity is what distinguishes two different functions:

```
safediv   std=SAFEDIV    vensim=XIDZ | ZIDZ                       args=2,3
smth1     std=SMTH1      vensim=SMOOTH | SMOOTHI                  args=2,3
init      std=INIT       vensim=ACTIVE INITIAL | INITIAL | REINITIAL   args=1,2
arraymax  std=ARRAYMAX | MAX   vensim=MAX | VMAX                  args=1,2
```

**One concept can carry several spellings in one dialect.** `endtime` collects `ENDTIME`,
`FINAL_TIME` and `STOPTIME` on the XMILE side against a single Vensim `FINAL TIME`;
`initial_time` collects `INITIAL_TIME` and `STARTTIME`; `dt` collects `DT` and
`TIME_STEP`. A one-row-per-name table cannot hold that in either direction.

**A blank cell is information.** `previous` has a `std` spelling, a spec entry, and no
Vensim column, because there is no Vensim equivalent. 86 concepts are `std-only` and 25
are `vensim-only`.

**The spec's parameter counts disagree with practice.** §3.5 gives `SMTH1` two
parameters; implementations use two or three. It gives `TREND` two; Vensim's reader
appends a default to make three.

**The drift check found a real one.** Exactly one `(std name, arity)` pair has sources
claiming different Vensim spellings:

```
INIT/1 args
    INITIAL      xmutil/Function.h
    INITIAL      xmutil/kArityMap
    REINITIAL    xmutil/Function.h
```

xmutil translates both Vensim `INITIAL` and `REINITIAL` to XMILE `INIT`, and its reverse
table maps `INIT` at one argument back to `INITIAL`. A model using `REINITIAL` round-trips
as `INITIAL`, silently. The forward and reverse tables are separately maintained, so
nothing in xmutil can notice; the crosstab noticed on the first run.

## Limits of this cut

The PySD column is 15 rows entered by hand from a survey, not extracted, and is marked
`pysd/manual` for that reason. Only the interesting concepts have it.

Concept labels come from the `std` spelling where one exists and a Vensim spelling
otherwise. They are identifiers, not names a committee agreed to, and the labels are the
part most obviously wanting human attention.

Nothing here verifies semantics. An edge means an implementation asserted a
correspondence, which is not the same as the two functions computing the same number. The
`checked_vs_vensim` column is the only semantic claim in the table, it comes from one
implementation, and it says no far more often than yes.

## Rebuilding

```sh
py -3.12 tools/v-generate/make_crosstab.py \
    --vensim-src D:/vensim/vensim/src/vensim \
    --xmutil-src D:/vensim/xmutil
```

The Vensim and xmutil sources are outside this repository. A source that cannot be found
is skipped and the run says so, so the table degrades to whatever is available rather
than failing.
