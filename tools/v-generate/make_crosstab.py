# SPDX-License-Identifier: MIT
# Copyright (c) 2026 Ventana Systems, Inc. See LICENSE-Ventana.md.
"""Build the function crosstab from every source we have.

Proposal item 7 asks the TC for a crosstab of function constructs instead of a canonical
list, and 07a-crosstab-design.md works out the shape. This produces a first cut of it.

The concepts are not curated. Each source contributes EDGES between (dialect, spelling)
pairs -- "xmutil translates Vensim SMOOTH to XMILE smth1", "Vensim's reader maps XMILE
SAFEDIV to ZIDZ at two arguments" -- and a concept is a connected component of that
graph. That is what makes this the union of what is known rather than one dialect's list
with annotations: a row exists because some implementation asserted a correspondence, and
a row with one member exists because nobody did.

Sources, in the order they are merged. Full citation, with licences, is in
proposals/crosstab/README.md.

  spec        XMILE v1.1, SDS Candidate Standard 02, section 3.5
  xmutil      https://github.com/bobeberlein/xmutil            MIT
  vensim      https://vensim.com                               proprietary, our own tree
  pysd        https://github.com/SDXorg/pysd                   MIT
  sde         https://github.com/climateinteractive/SDEverywhere   MIT

What is read from each:

  spec       spec/schema/../03-model-equation-structure.adoc, section 3.5.
             Contributes std names with no edges -- what the standard defines.
  xmutil     Function.h (Vensim -> XMILE, 58 macro invocations) and
             XmileFunctions.cpp (XMILE -> Vensim, kFuncMap + kArityMap).
             Two directions held as separate data, so they are merged as separate
             edges and any disagreement survives into the output.
  vensim     XMILEFunctions.cpp, 140 registrations, each carrying two flags this
             table wants anyway: whether the mapping was checked against Vensim's
             own result, and whether the XMILE implementation differs.
  pysd       a small hand-entered seed, since PySD's tables are Python dicts in a
             repository we do not vendor. Marked provenance=manual.
  sde        SDEverywhere's two "Supported ... Functions" wiki pages, transcribed.
             Contributes no spellings of its own -- it uses each dialect's names --
             but confirms which names exist and records whether its C and JavaScript
             targets implement each one. That lands in support.tsv.

Usage:
  py -3.12 tools/v-generate/make_crosstab.py
      --vensim-src D:/vensim/vensim/src/vensim
      --xmutil-src D:/vensim/xmutil

Writes proposals/crosstab/{concepts,spellings,edges,crosstab}.tsv. With a source
missing, its rows are simply absent and the run says so.
"""
import argparse
import io
import os
import re
import sys
from collections import defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(HERE))
OUT = os.path.join(REPO, "proposals", "crosstab")

ANY = ""  # arity not specified by the source


# --------------------------------------------------------------------------- sources

def read(path):
    with io.open(path, encoding="utf-8", errors="replace") as handle:
        return handle.read()


SPEC_NAMES = set()


def from_spec(edges, names, notes):
    """Section 3.5 of the specification: the names std defines."""
    path = os.path.join(REPO, "spec", "03-model-equation-structure.adoc")
    if not os.path.exists(path):
        return 0
    text = read(path)
    start = text.find("=== Built-in Functions")
    end = text.find("=== Extending the Standard Language", start)
    if start < 0:
        return 0
    body = text[start:end if end > 0 else len(text)]
    # Each built-in is written as a definition line, "{empty}ABS:  absolute value...",
    # followed a couple of lines later by "Parameters: 1: ...". The {empty} is an
    # AsciiDoc escape and is not always present.
    lines = body.split("\n")
    found = {}
    pending = None
    for line in lines:
        s = line.strip()
        m = re.match(r"^(?:\{empty\})?([A-Z][A-Z0-9_]{1,20})\s*:\s+\S", s)
        if m and not s.startswith("Parameters") and not s.startswith("Range"):
            pending = m.group(1)
            found.setdefault(pending, ANY)
            continue
        if pending and s.startswith("Parameters:"):
            n = re.search(r"Parameters:\s*(\d+)", s)
            if n:
                found[pending] = n.group(1)
            pending = None
    for name, arity in found.items():
        names.add(("std", name, ANY))
        SPEC_NAMES.add(name)
        if arity:
            notes[("std", name, ANY)].append("spec 3.5: %s parameter(s)" % arity)
    return len(found)


def from_xmutil(root, edges, names, notes):
    """xmutil: Vensim -> XMILE macros, and the XMILE -> Vensim tables."""
    fh = os.path.join(root, "src", "Function", "Function.h")
    xf = os.path.join(root, "src", "Xmile", "XmileFunctions.cpp")
    if not os.path.exists(fh):
        return 0
    n = 0
    text = read(fh)
    pat = re.compile(r'\bD?FSubclass(?:Start)?\(\s*\w+\s*,\s*"([^"]*)"\s*,\s*(-?\d+)\s*,\s*"([^"]*)"')
    for m in pat.finditer(text):
        vensim, narg, xmile = m.group(1), int(m.group(2)), m.group(3).strip()
        names.add(("vensim", vensim, ANY))
        if not xmile:
            notes[("vensim", vensim, ANY)].append("xmutil: no XMILE form emitted")
            continue
        xmile = xmile.split("(")[0]           # RANDOM 0 1 -> "UNIFORM(0,1)"
        arity = str(narg) if narg >= 0 else ANY
        names.add(("std", xmile, ANY))
        edges.append(("vensim", vensim, "std", xmile, arity, "xmutil/Function.h"))
        n += 1

    if os.path.exists(xf):
        text = read(xf)
        for x, a, v in re.findall(r'\{"([a-z_0-9]+)"\s*,\s*(\d+)\s*,\s*"([^"]+)"\}', text):
            names.add(("std", x.upper(), ANY))
            names.add(("vensim", v, ANY))
            edges.append(("std", x.upper(), "vensim", v, a, "xmutil/kArityMap"))
            n += 1
        for x, v in re.findall(r'\{"([a-z_0-9]+)"\s*,\s*"([^"]+)"\}', text):
            names.add(("std", x.upper(), ANY))
            names.add(("vensim", v, ANY))
            edges.append(("std", x.upper(), "vensim", v, ANY, "xmutil/kFuncMap"))
            n += 1
    return n


def from_vensim(root, edges, names, notes, flags):
    """Vensim's XMILE reader: 140 registrations, with its two verification flags."""
    hdr = os.path.join(root, "XMILEFunctions.h")
    src = os.path.join(root, "XMILEFunctions.cpp")
    if not os.path.exists(src):
        return 0
    defines = dict(re.findall(r'#define\s+(STR_XMILE_FUNCTION_\w+)\s+"([^"]+)"', read(hdr)))
    text = read(src)
    n = 0
    for line in text.split("\n"):
        s = line.strip()
        if s.startswith("//") or "global_vec_XMILEFunctions.push_back" not in s:
            continue
        m = re.search(r"XMILEFunction\(\s*(STR_XMILE_FUNCTION_\w+)\s*,\s*(true|false)\s*,\s*(true|false)\s*(.*)$", s)
        if not m:
            continue
        xmile = defines.get(m.group(1))
        if not xmile:
            continue
        checked, differs, tail = m.group(2) == "true", m.group(3) == "true", m.group(4)
        names.add(("std", xmile, ANY))
        flags[("std", xmile)] = (checked, differs)
        n += 1

        # The fourth constructor argument decides the form. Read it positionally: a
        # regex that just hunts for the first quoted string mistakes the trailing
        # default argument for a rename when the rename is wxEmptyString, which is
        # exactly what TREND does.
        rest = tail.lstrip()
        if rest.startswith(","):
            rest = rest[1:].lstrip()

        arity = re.findall(r"\{\s*(\d+)\s*,\s*\"([^\"]+)\"\s*\}", rest)
        if rest.startswith("std::map") and arity:
            for commas, vensim in arity:
                names.add(("vensim", vensim, ANY))
                # the map is keyed on comma count; arguments = commas + 1
                edges.append(("std", xmile, "vensim", vensim, str(int(commas) + 1),
                              "vensim/XMILEFunctions.cpp"))
            continue

        conv = re.match(r"(ConvertFunction_\w+)", rest)
        if conv:
            notes[("std", xmile, ANY)].append(
                "vensim: conversion is code (%s), not a rename" % conv.group(1))
            continue

        if rest.startswith("NULL"):
            continue                      # recognised, no conversion asserted

        m4 = re.match(r'(?:wxEmptyString|"([^"]*)")\s*(?:,\s*"([^"]*)")?', rest)
        if m4:
            vensim, default = m4.group(1), m4.group(2)
            if vensim:
                names.add(("vensim", vensim, ANY))
                edges.append(("std", xmile, "vensim", vensim, ANY,
                              "vensim/XMILEFunctions.cpp"))
            if default is not None:
                notes[("std", xmile, ANY)].append(
                    "vensim: appends %s as a trailing argument" % default)
    return n


# PySD's structures live in Python dictionaries in a repository we do not vendor, so this
# is entered by hand from translators/structures/abstract_expressions.py and the two
# *_structures.py files, surveyed 2026-08-21. Marked manual so it is never mistaken for
# something a build step verified.
PYSD_SEED = [
    # (std spelling, arity or ANY, pysd node)
    ("SMTH1", "2", "SmoothStructure(order=1)"),
    ("SMTH1", "3", "SmoothStructure(order=1)"),
    ("SMTH3", ANY, "SmoothStructure(order=3)"),
    ("SMTHN", ANY, "SmoothNStructure"),
    ("DELAY1", ANY, "DelayStructure(order=1)"),
    ("DELAY3", ANY, "DelayStructure(order=3)"),
    ("DELAYN", ANY, "DelayNStructure"),
    ("DELAY", ANY, "DelayFixedStructure"),
    ("FORCST", ANY, "ForecastStructure"),
    ("TREND", ANY, "TrendStructure"),
    ("INIT", "1", "InitialStructure"),
    ("SAFEDIV", "2", "CallStructure(zidz)"),
    ("SAFEDIV", "3", "CallStructure(xidz)"),
    ("INTEG", ANY, "IntegStructure"),
    ("ALLOCATE", ANY, "AllocateByPriorityStructure"),
]


def from_pysd(edges, names, notes):
    for xmile, arity, node in PYSD_SEED:
        names.add(("std", xmile, ANY))
        names.add(("pysd", node, ANY))
        edges.append(("std", xmile, "pysd", node, arity, "pysd/manual"))
    return len(PYSD_SEED)


# SDEverywhere (github.com/climateinteractive/SDEverywhere, Climate Interactive) compiles
# Vensim to C and JavaScript and reads XMILE. It publishes two wiki pages, "Supported
# Vensim Functions" and "Supported XMILE and Stella Functions", which are transcribed
# here as of 2026-08-21 and marked sde/manual.
#
# What it contributes is not spellings -- it uses each dialect's own names -- but two
# things nothing else here has: independent confirmation that a name exists in a dialect,
# and whether an implementation actually implements it, per target. "partial" is the
# page's warning marker.
#
# The XMILE page ends with a catch-all row for everything unsupported, so absence from
# this list is not evidence; only the rows below are.
SDE_XMILE = [
    ("ABS", "yes", "yes", ""), ("ARCCOS", "yes", "yes", ""), ("ARCSIN", "yes", "yes", ""),
    ("ARCTAN", "yes", "yes", ""), ("COS", "yes", "yes", ""), ("EXP", "yes", "yes", ""),
    ("INF", "no", "no", ""), ("INT", "yes", "yes", ""), ("LN", "yes", "yes", ""),
    ("LOG10", "no", "no", ""), ("MAX", "yes", "yes", ""), ("MIN", "yes", "yes", ""),
    ("PI", "no", "no", ""), ("SIN", "yes", "yes", ""), ("SQRT", "yes", "yes", ""),
    ("TAN", "yes", "yes", ""), ("EXPRND", "no", "no", ""), ("LOGNORMAL", "no", "no", ""),
    ("NORMAL", "no", "no", ""), ("POISSON", "no", "no", ""), ("RANDOM", "no", "no", ""),
    ("DELAY", "yes", "yes", ""), ("DELAY1", "yes", "yes", ""), ("DELAY3", "yes", "yes", ""),
    ("DELAYN", "no", "no", ""), ("FORCST", "no", "no", ""), ("SMTH1", "yes", "yes", ""),
    ("SMTH3", "yes", "yes", ""), ("SMTHN", "no", "no", ""), ("TREND", "yes", "yes", ""),
    ("PULSE", "no", "no", ""), ("RAMP", "yes", "yes", ""), ("STEP", "yes", "yes", ""),
    ("DT", "yes", "yes", ""), ("STARTTIME", "yes", "yes", ""), ("STOPTIME", "yes", "yes", ""),
    ("TIME", "yes", "yes", ""), ("INIT", "yes", "yes", ""),
    ("PREVIOUS", "no", "no", ""), ("SELF", "no", "no", ""),
    ("MEAN", "no", "no", "array form"), ("RANK", "no", "no", "array form"),
    ("SIZE", "yes", "yes", "array form"), ("STDDEV", "no", "no", "array form"),
    ("SUM", "yes", "yes", "array form"),
    ("LOOKUP", "yes", "yes", ""), ("LOOKUPINV", "yes", "yes", ""), ("NPV", "yes", "yes", ""),
]

SDE_VENSIM = [
    ("ABS", "yes", "yes", ""), ("ACTIVE INITIAL", "yes", "yes", ""),
    ("ALLOCATE AVAILABLE", "yes", "no", "see the page's caveats"),
    ("ALLOCATE BY PRIORITY", "yes", "no", ""),
    ("ARCCOS", "yes", "yes", ""), ("ARCSIN", "yes", "yes", ""), ("ARCTAN", "yes", "yes", ""),
    ("COS", "yes", "yes", ""), ("DELAY1", "yes", "yes", ""), ("DELAY1I", "yes", "yes", ""),
    ("DELAY3", "yes", "yes", ""), ("DELAY3I", "yes", "yes", ""),
    ("DELAY FIXED", "yes", "no", ""), ("DEMAND AT PRICE", "yes", "no", ""),
    ("DEPRECIATE STRAIGHTLINE", "partial", "no", "the fisc argument is not supported"),
    ("ELMCOUNT", "yes", "yes", ""), ("EXP", "yes", "yes", ""),
    ("FIND MARKET PRICE", "yes", "no", ""), ("GAME", "yes", "yes", ""),
    ("GAMMA LN", "yes", "no", ""), ("GET DATA BETWEEN TIMES", "yes", "yes", ""),
    ("GET DIRECT CONSTANTS", "yes", "yes", ""), ("GET DIRECT DATA", "yes", "yes", ""),
    ("GET DIRECT LOOKUPS", "yes", "yes", ""),
    ("GET DIRECT SUBSCRIPT", "partial", "partial", "csv only, no xlsx"),
    ("GET XLS CONSTANTS", "yes", "yes", "synonym for GET DIRECT CONSTANTS"),
    ("GET XLS DATA", "yes", "yes", "synonym for GET DIRECT DATA"),
    ("GET XLS LOOKUPS", "yes", "yes", "synonym for GET DIRECT LOOKUPS"),
    ("IF THEN ELSE", "yes", "yes", ""), ("INITIAL", "yes", "yes", ""),
    ("INTEG", "yes", "yes", ""), ("INTEGER", "yes", "yes", ""),
    ("INVERT MATRIX", "yes", "yes", ""), ("LN", "yes", "yes", ""),
    ("LOOKUP BACKWARD", "yes", "yes", ""), ("LOOKUP FORWARD", "yes", "yes", ""),
    ("LOOKUP INVERT", "yes", "yes", ""), ("MAX", "yes", "yes", ""), ("MIN", "yes", "yes", ""),
    ("MODULO", "yes", "yes", ""), ("NPV", "yes", "yes", ""), ("POWER", "yes", "yes", ""),
    ("PULSE", "yes", "yes", ""), ("PULSE TRAIN", "yes", "yes", ""),
    ("QUANTUM", "yes", "yes", ""), ("RAMP", "yes", "yes", ""),
    ("SAMPLE IF TRUE", "yes", "yes", ""), ("SIN", "yes", "yes", ""),
    ("SMOOTH", "yes", "yes", ""), ("SMOOTHI", "yes", "yes", ""),
    ("SMOOTH3", "yes", "yes", ""), ("SMOOTH3I", "yes", "yes", ""),
    ("SQRT", "yes", "yes", ""), ("STEP", "yes", "yes", ""),
    ("SUPPLY AT PRICE", "yes", "no", ""), ("TAN", "yes", "yes", ""),
    ("TREND", "yes", "yes", ""), ("VECTOR ELM MAP", "yes", "yes", ""),
    ("VECTOR SELECT", "partial", "partial", "only numerical_action 0 (sum) and 3 (max)"),
    ("VECTOR SORT ORDER", "yes", "yes", ""), ("VMAX", "yes", "yes", ""),
    ("VMIN", "yes", "yes", ""), ("WITH LOOKUP", "yes", "yes", ""),
    ("XIDZ", "yes", "yes", ""), ("ZIDZ", "yes", "yes", ""),
]


def from_sde(edges, names, notes, support):
    n = 0
    for dialect, table in (("std", SDE_XMILE), ("vensim", SDE_VENSIM)):
        for spelling, c, js, note in table:
            names.add((dialect, spelling, ANY))
            support.append((dialect, spelling, "sde/c", c, note))
            support.append((dialect, spelling, "sde/js", js, note))
            n += 1
    return n


# Correspondences we know but no tool implements yet. Every other source here is
# extracted from something that runs; these are asserted by a person, so they are marked
# ventana/manual and are the one place in the build where knowledge enters by hand.
#
# The "XMILE side only" section of SUMMARY.md is the worklist these come from: a concept
# with a Stella spelling and no Vensim one is either a real gap in every translator or a
# function with no Vensim equivalent, and only a person can say which.
KNOWN = [
    # (std spelling, vensim spelling, arity, note)
    ("BETA", "RANDOM BETA", ANY, "gap in Vensim's XMILE reader as of 2026-08-21"),
]


def from_known(edges, names, notes):
    for xmile, vensim, arity, note in KNOWN:
        names.add(("std", xmile, ANY))
        names.add(("vensim", vensim, ANY))
        edges.append(("std", xmile, "vensim", vensim, arity, "ventana/manual"))
        if note:
            notes[("std", xmile, ANY)].append(note)
    return len(KNOWN)


# ------------------------------------------------------------------- concept building

def components(names, edges):
    """Union-find over (dialect, spelling); a component is a concept."""
    parent = {}

    def find(x):
        parent.setdefault(x, x)
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    def union(a, b):
        ra, rb = find(a), find(b)
        if ra != rb:
            parent[ra] = rb

    for d, s, _ in names:
        find((d, s))
    for d1, s1, d2, s2, _a, _src in edges:
        union((d1, s1), (d2, s2))

    groups = defaultdict(list)
    for node in list(parent):
        groups[find(node)].append(node)
    return groups


def label(members):
    """Name a concept: prefer the std spelling, else Vensim's, else anything."""
    for dialect in ("std", "vensim", "pysd"):
        cand = sorted(s for d, s in members if d == dialect)
        if cand:
            return cand[0].lower().replace(" ", "_")
    return "unknown"


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--vensim-src", default=r"D:/vensim/vensim/src/vensim")
    ap.add_argument("--xmutil-src", default=r"D:/vensim/xmutil")
    args = ap.parse_args(argv)

    edges, names, notes, flags, support = [], set(), defaultdict(list), {}, []

    counts = [
        ("spec", from_spec(edges, names, notes)),
        ("xmutil", from_xmutil(args.xmutil_src, edges, names, notes)),
        ("vensim", from_vensim(args.vensim_src, edges, names, notes, flags)),
        ("pysd", from_pysd(edges, names, notes)),
        ("sde", from_sde(edges, names, notes, support)),
        ("known", from_known(edges, names, notes)),
    ]
    for name, n in counts:
        print("  %-8s %s" % (name, ("%d fact(s)" % n) if n else "nothing extracted"))

    groups = components(names, edges)
    concepts = {}
    for root, members in groups.items():
        cid = label(members)
        while cid in concepts and concepts[cid] != members:
            cid += "_x"
        concepts[cid] = members

    if not os.path.isdir(OUT):
        os.makedirs(OUT)

    def write(name, header, rows):
        path = os.path.join(OUT, name)
        with io.open(path, "w", encoding="utf-8", newline="\n") as handle:
            handle.write("\t".join(header) + "\n")
            for row in rows:
                handle.write("\t".join(str(c) for c in row) + "\n")
        print("  wrote %-16s %d row(s)" % (name, len(rows)))

    member_of = {}
    for cid, members in concepts.items():
        for node in members:
            member_of[node] = cid

    # concepts.tsv -- one row per equivalence class.
    #
    # reach says whether any source asserted a correspondence ACROSS dialects, and when
    # none did, which single dialect the concept sits in. "linked" is not a claim about
    # any particular pair -- read the dialects column for that.
    crows = []
    for cid in sorted(concepts):
        members = concepts[cid]
        dialects = sorted(set(d for d, _ in members))
        reach = "linked" if len(dialects) > 1 else "%s-only" % dialects[0]
        crows.append((cid, len(members), ",".join(dialects), reach))
    write("concepts.tsv", ("concept", "n_spellings", "dialects", "reach"), crows)

    # spellings.tsv -- one row per (concept, dialect, spelling)
    srows = []
    for (d, s, _a) in sorted(names):
        cid = member_of.get((d, s), "?")
        checked, differs = flags.get((d, s), ("", ""))
        note = "; ".join(notes.get((d, s, ANY), []))
        srows.append((cid, d, s,
                      "yes" if checked is True else ("no" if checked is False else ""),
                      "yes" if differs is True else ("no" if differs is False else ""),
                      note))
    write("spellings.tsv",
          ("concept", "dialect", "spelling", "checked_vs_vensim", "differs", "notes"), srows)

    # edges.tsv -- the asserted correspondences, with who asserted each
    erows = []
    for d1, s1, d2, s2, arity, src in sorted(edges):
        erows.append((member_of.get((d1, s1), "?"), d1, s1, d2, s2, arity, src))
    write("edges.tsv",
          ("concept", "from_dialect", "from", "to_dialect", "to", "args", "source"), erows)

    # support.tsv -- who implements what. A name existing in a dialect and an
    # implementation supporting it are different facts, so they are different tables.
    if support:
        srows2 = []
        for dialect, spelling, impl, status, note in sorted(support):
            srows2.append((member_of.get((dialect, spelling), "?"), dialect, spelling,
                           impl, status, note))
        write("support.tsv",
              ("concept", "dialect", "spelling", "implementation", "status", "notes"), srows2)

    # crosstab.tsv -- the human-readable pivot
    dialects = ("std", "vensim", "pysd")
    prows = []
    for cid in sorted(concepts):
        cells = []
        for d in dialects:
            sp = sorted(s for dd, s in concepts[cid] if dd == d)
            cells.append(" | ".join(sp))
        arities = sorted(set(a for d1, s1, d2, s2, a, _ in edges
                             if member_of.get((d1, s1)) == cid and a), key=lambda v: int(v))
        note = "; ".join(sorted(set(
            n for node, ns in notes.items() if member_of.get(node[:2]) == cid for n in ns)))
        prows.append([cid] + cells + [",".join(arities), note])
    write("crosstab.tsv", ("concept",) + dialects + ("args_seen", "notes"), prows)

    # summary.tsv / SUMMARY.md -- one screen for a reader who will not open the others.
    #
    # Two column groups, because they answer different questions. std / stella / vensim
    # are LANGUAGES: how each writes the concept. pysd / sde / xmutil are TOOLS: what
    # each covers. A language cell is a spelling; a tool cell is coverage.
    #
    # The split between std and stella is by the specification: a name section 3.5
    # defines is std, and any other XMILE-namespace name is Stella's own -- unless the
    # only source naming it is xmutil, in which case it is xmutil's coinage and is
    # reported in the xmutil column instead of being credited to a language.
    xmile_by_source = defaultdict(set)
    for d1, s1, d2, s2, arity, src in edges:
        for d, s in ((d1, s1), (d2, s2)):
            if d == "std":
                xmile_by_source[s].add(src.split("/")[0])
    for (d, s, _a) in names:
        if d == "std" and s in SPEC_NAMES:
            xmile_by_source[s].add("spec")
        elif d == "std" and (d, s) in flags:
            xmile_by_source[s].add("vensim")

    def sde_cell(cid):
        got = [r for r in support if member_of.get((r[0], r[1])) == cid]
        if not got:
            return ""
        st = set(r[3] for r in got)
        if "partial" in st:
            return "partial"
        c = set(r[3] for r in got if r[2] == "sde/c")
        j = set(r[3] for r in got if r[2] == "sde/js")
        if c == {"yes"} and j == {"yes"}:
            return "C+JS"
        if c == {"yes"}:
            return "C only"
        if "yes" in c or "yes" in j:
            return "some"
        return "no"

    def xmutil_cell(cid, coined):
        srcs = set(src for d1, s1, d2, s2, a, src in edges
                   if member_of.get((d1, s1)) == cid and src.startswith("xmutil"))
        if not srcs:
            return ""
        fwd = any("Function.h" in s for s in srcs)
        rev = any("Func" not in s or "kFuncMap" in s or "kArityMap" in s for s in srcs)
        rev = any(("kFuncMap" in s or "kArityMap" in s) for s in srcs)
        cell = "both ways" if (fwd and rev) else ("to XMILE" if fwd else "to Vensim")
        return cell + (" (coins %s)" % ", ".join(sorted(coined)) if coined else "")

    srows3, mdrows = [], []
    for cid in sorted(concepts):
        members = concepts[cid]
        xmile = sorted(s for d, s in members if d == "std")
        std = [s for s in xmile if s in SPEC_NAMES]
        coined = [s for s in xmile
                  if s not in SPEC_NAMES and xmile_by_source.get(s, set()) <= {"xmutil"}]
        stella = [s for s in xmile if s not in SPEC_NAMES and s not in coined]
        vensim = sorted(s for d, s in members if d == "vensim")
        pysd = sorted(s for d, s in members if d == "pysd")
        row = (cid, " | ".join(std), " | ".join(stella), " | ".join(vensim),
               " | ".join(pysd), sde_cell(cid), xmutil_cell(cid, coined))
        srows3.append(row)
        mdrows.append(row)
    write("summary.tsv",
          ("concept", "xmile std", "stella", "vensim", "pysd", "sde", "xmutil"), srows3)

    def cell(value, code):
        # A pipe inside a Markdown cell ends the cell, so alternatives are comma-listed.
        if not value:
            return ""
        parts = [v.strip() for v in value.split("|")]
        return ", ".join("`%s`" % v for v in parts) if code else ", ".join(parts)

    def table(rows):
        out = ["| concept | xmile std | stella | vensim | pysd | sde | xmutil |",
               "|---|---|---|---|---|---|---|"]
        for r in rows:
            out.append("| %s | %s | %s | %s | %s | %s | %s |"
                       % (r[0], cell(r[1], True), cell(r[2], True), cell(r[3], True),
                          cell(r[4], False), r[5], r[6]))
        return out

    both = [r for r in mdrows if r[3] and (r[1] or r[2])]
    xonly = [r for r in mdrows if not r[3]]
    vonly = [r for r in mdrows if r[3] and not (r[1] or r[2])]

    md = [
        "# Function crosstab, summary",
        "",
        "Generated by `tools/v-generate/make_crosstab.py`. The full relational tables are",
        "beside this file; `README.md` documents every column and where each fact came from.",
        "",
        "Two column groups, answering different questions.",
        "",
        "- **Languages** -- `xmile std`, `stella`, `vensim` -- how each writes the concept.",
        "  `xmile std` is a name section 3.5 of the specification defines; `stella` is an",
        "  XMILE-namespace name it does not.",
        "- **Tools** -- `pysd`, `sde`, `xmutil` -- what each one covers. `pysd` names the AST",
        "  node, `sde` gives SDEverywhere's support across its C and JavaScript targets, and",
        "  `xmutil` says which directions it translates.",
        "",
        "An empty language cell means that language has no spelling for the concept. An empty",
        "tool cell means that tool does not cover it.",
        "",
        "## Translated between languages (%d)" % len(both),
        "",
        "Some implementation asserts a correspondence here.",
        "",
    ]
    md += table(both)
    md += [
        "",
        "## XMILE side only (%d)" % len(xonly),
        "",
        "No source maps these to a Vensim function. Most are Stella's own; each is either a",
        "genuine gap in every translator, or a function with no Vensim equivalent.",
        "",
    ]
    md += table(xonly)
    md += [
        "",
        "## Vensim side only (%d)" % len(vonly),
        "",
        "Named by a source on the Vensim side with no XMILE spelling recorded.",
        "",
    ]
    md += table(vonly)
    md.append("")
    with io.open(os.path.join(OUT, "SUMMARY.md"), "w", encoding="utf-8", newline="\n") as h:
        h.write("\n".join(md))
    print("  wrote %-16s %d + %d + %d row(s)"
          % ("SUMMARY.md", len(both), len(xonly), len(vonly)))

    linked = sum(1 for c in crows if c[3] == "linked")
    print("\n  %d concepts, %d linked across dialects, %d in one dialect only"
          % (len(crows), linked, len(crows) - linked))

    # Two sources asserting different Vensim spellings for one std name at one arity is
    # the drift the design predicts when each direction is held as separate data. Report
    # it rather than silently picking a winner.
    claim = defaultdict(set)
    for d1, s1, d2, s2, arity, src in edges:
        if d1 == "std" and d2 == "vensim":
            claim[(s1, arity)].add((s2, src))
        elif d1 == "vensim" and d2 == "std":
            claim[(s2, arity)].add((s1, src))
    clashes = {k: v for k, v in claim.items() if len(set(s for s, _ in v)) > 1}
    if clashes:
        print("\n  %d (std name, arity) pair(s) where sources disagree:" % len(clashes))
        for (name, arity), v in sorted(clashes.items()):
            print("    %s%s" % (name, ("/%s args" % arity) if arity else ""))
            for spelling, src in sorted(v):
                print("        %-22s %s" % (spelling, src))
    else:
        print("\n  no source disagreements")
    return 0


if __name__ == "__main__":
    sys.exit(main())
