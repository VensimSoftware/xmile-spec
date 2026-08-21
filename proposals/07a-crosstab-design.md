# Designing the function crosstab

Item 7 asks the TC for a crosstab of function constructs rather than a canonical list.
This is the evidence for that ask and a proposed shape for the table. Surveyed 2026-08-21
across four implementations that read or write both Vensim and XMILE.

## What was surveyed

**xmutil** (`github.com/bobeberlein/xmutil`, MIT), C++, converts Vensim `.mdl` and Dynamo
`.dyn` to XMILE and back. Its Vensim-to-XMILE mapping is 58 entries carried as macro
arguments in `src/Function/Function.h`:

```cpp
DFSubclass(FunctionSmooth, "SMOOTH", 2, "SMTH1")
```

34 of the 58 are renames, 22 pass the name through, and 2 have no XMILE form at all
(`GAME`, `TABBED ARRAY`). The reverse direction is separate data in
`src/Xmile/XmileFunctions.cpp`: `kFuncMap`, 20 rows, plus `kArityMap`, 16 rows over 8
names, plus an uppercase-and-underscore fallback.

**Vensim**, whose XMILE layer registers 140 XMILE function names in
`src/vensim/XMILEFunctions.cpp`, each with a rename, an arity-keyed rename, or a
conversion function for the cases a rename cannot express.

**PySD** (`github.com/SDXorg/pysd`), Python, whose Abstract Model Representation defines
25 semantic node types in `translators/structures/abstract_expressions.py`. Its Vensim
parser maps 31 names onto them and its XMILE parser 25. Anything without a node passes
through `CallStructure(function, arguments)` with the name as a string.

**SDEverywhere** (`github.com/climateinteractive/SDEverywhere`, Climate Interactive)
compiles Vensim to C and JavaScript and reads XMILE. It uses each dialect's own names
rather than a mapping of its own, but publishes two "Supported Functions" wiki pages
recording which functions each of its targets implements -- a kind of fact none of the
other three records.

## Five findings

**All three key on (name, arity), not on name.** None of them coordinated, and each
arrived at the same discriminator. PySD's `structures` dictionary holds arity-keyed
sub-dictionaries for `delay`, `smth1` and `safediv`. xmutil has `kArityMap`. Vensim has
`std::map<size_t, wxString>{{1, "ZIDZ"}, {2, "XIDZ"}}`. A table whose rows are names
cannot express what any of the three needed to express.

**Translation into XMILE is many-to-one, so the reverse needs the arity to recover.**
xmutil maps `SMOOTH` and `SMOOTHI` both to `smth1`, `SMOOTH3` and `SMOOTH3I` both to
`smth3`, `DELAY1` and `DELAY1I` both to `delay1`, `ZIDZ` and `XIDZ` both to `safediv`,
`INITIAL` and `REINITIAL` both to `INIT`. The information that distinguishes them
survives only in the argument count, which is why `kArityMap` exists.

**Two directions held as separate data will drift.** xmutil's forward table is 58 macro
invocations in a header; its reverse table is 36 rows in a source file. Nothing checks
that one is the inverse of the other. A single crosstab read in both directions cannot
develop that class of bug.

**Coverage differs by more than a factor of two, so a column is not a checkbox.** Vensim's
XMILE layer knows 140 names; xmutil maps 57. The 100 Vensim knows and xmutil does not are
mostly Stella's own: the conveyor and queue family (`CTFLOW`, `CTMEAN`, `CYCLETIME`,
`THROUGHPUT`), the attribute functions (`ATTRMEAN`, `ATTRCOUNT`), the statistical
distributions (`BETA`, `WEIBULL`, `NEGBINOMIAL`, `TRIANGULAR`), the financial functions
(`PMT`, `FV`, `PV`), and `PREVIOUS`, `SELF` and `HISTORY`. A cell therefore needs three
states, not two: this tool spells it *X*, this tool has no equivalent, and nobody has
checked.

**Some rows will have no `std` column at all.** `SAFEDIV` appears nowhere in the v1.1
text, yet Vensim writes `SAFEDIV`, xmutil writes `safediv`, and PySD parses `safediv`.
`WITH_LOOKUP`, `GET_DIRECT_DATA`, `VECTOR SELECT`, `TIME_BASE`, `DELAY_CONVEYOR` and
`GET_DATA_AT_TIME` are in the same position. A canonical list has nowhere to put a
function the field uses and the standard has not defined. A table has a row with one
column empty, which is both accurate and a standing proposal.

## Proposed shape

Rows are a concept plus a signature. Columns are one per implementation, `std` among
them. One notes column for what the mapping does not preserve.

| concept | args | std | vensim | pysd node | notes |
|---|---|---|---|---|---|
| first-order smooth | 2 | `SMTH1` | `SMOOTH` | `SmoothStructure(order=1)` | initialises to the input |
| first-order smooth | 3 | `SMTH1` | `SMOOTHI` | `SmoothStructure(order=1)` | third argument is the initial value |
| safe division | 2 | | `ZIDZ` | `CallStructure("zidz")` | not in the specification; universal in practice |
| safe division | 3 | | `XIDZ` | `CallStructure("xidz")` | third argument is the value when the denominator is zero |
| array minimum | 1 | `MIN` | `VMIN` | | XMILE spells the reducer and the pairwise form alike |
| pairwise minimum | 2 | `MIN` | `MIN` | | |
| previous value | 1 | `PREVIOUS` | | | no Vensim equivalent |

`SMTH1` occupies two rows because two Vensim functions map onto it, which is the fact a
one-row-per-name table cannot hold. `MIN` occupies two rows for the opposite reason: one
XMILE spelling covers two distinct operations, split in Vensim.

PySD's 25 node types are a good starting vocabulary for the concept column. They are
already the union of what two independent parsers needed, which is a stronger basis than
a list drawn up from one dialect.

## Seeding it

Every column can be filled mechanically from something that exists:

- `std` from §3.5 of the specification, 40 functions.
- `vensim` from the 140 registrations in `XMILEFunctions.cpp`, and cross-checked against
  xmutil's 58 forward mappings, which were written independently. Disagreements between
  the two are worth reading before either is trusted.
- `pysd node` from `translators/structures/abstract_expressions.py` and the two
  `*_structures.py` dictionaries.
- Arity from all three, which record it already.

The notes column is the part that needs a person. It is also the part worth the most,
since it holds the differences that make a translation wrong rather than merely verbose:
`SMTH1` against `SMOOTH` in initial-value handling, `FORCST` against `FORECAST` in
argument order, `INT` against `INTEGER` in truncation against rounding, `LOG10` fixing a
base where Vensim's `LOG` takes one.

## A first cut exists

[crosstab/](crosstab/) holds a working table built to this design from five sources: the
specification, xmutil, Vensim, PySD and SDEverywhere. `crosstab/README.md` reports what it
found. The short version is that the design's three predictions hold -- arity is
load-bearing on 9 concepts, one dialect carries several spellings for one concept on
another 3, and the drift check found a real round-trip loss in xmutil, where `REINITIAL`
returns as `INITIAL`.

## What it will not do

A crosstab records correspondence. It does not make two functions agree. Where a note
says the initial-value convention differs, a translator still has to decide what to emit,
and two translators may reasonably decide differently. What the table removes is the
situation today, in which each of them decides privately and no one can compare the
decisions.
