# SPDX-License-Identifier: MIT
# Copyright (c) 2026 Ventana Systems, Inc. See LICENSE-Ventana.md.
"""Check the 1.1.x proposal against the v1.1 schema it is derived from.

Two questions, and the first matters more than the second:

  1. Is it additive? Six of the seven changes are: no document that validates against
     v1.1 may fail against them, and no file may gain an error. Change 7 is
     deliberately restrictive -- it requires a whole-model <dim> to say what it
     contains -- so for that one the corpus check is what shows the cost, which is
     nil: no file gains an error from it either.
  2. What does it buy? Error counts over a corpus, and a set of hand-written cases that
     exercise each change directly.

Usage:
  py -3.12 tools/v-generate/compare_v11x.py [--corpus DIR]
"""
import argparse
import io
import os
import sys
import glob
import tempfile

import xmlschema

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(HERE))
BASE = os.path.join(REPO, "spec", "schema", "xmile.xsd.xml")
PROP = os.path.join(REPO, "proposals", "schema", "xmile-v1.1.x-proposal.xsd")

HDR = ('<?xml version="1.0" encoding="utf-8"?>\n'
       '<xmile version="1.1" xmlns="http://docs.oasis-open.org/xmile/ns/XMILE/v1.0"'
       ' xmlns:isee="http://iseesystems.com/XMILE"'
       ' xmlns:vensim="http://www.vensim.com/XMILE">\n'
       '%s'
       '</xmile>\n')

MINIMAL_HEADER = ("  <header><vendor>V</vendor><product version=\"1\">P</product>"
                  "</header>\n")
SIM = "  <sim_specs><start>0</start><stop>10</stop></sim_specs>\n"
MODEL = ("  <model><variables><aux name=\"a\"><eqn>1</eqn></aux></variables></model>\n")

# A label starting with REJECT marks a case the proposal must reject: change 7 is
# the one restrictive change here, and a check that only ever asks "is this
# accepted now?" cannot test it.
REJECT = "REJECT "

# (label, which change it exercises, document body)
CASES = [
    ("vendor:attach on <connector><to>", 1,
     MINIMAL_HEADER + SIM +
     '  <model><variables><aux name="a"><eqn>1</eqn></aux>'
     '<aux name="b"><eqn>a</eqn></aux></variables>'
     '<views><view><connector uid="1"><from>a</from>'
     '<to vensim:attach="1">b</to></connector></view></views></model>\n'),
    ("<doc> in <sim_specs>", 2,
     MINIMAL_HEADER +
     "  <sim_specs><start>0</start><stop>10</stop><doc>why these bounds</doc>"
     "</sim_specs>\n" + MODEL),
    ("<doc> in <model>", 2,
     MINIMAL_HEADER + SIM +
     '  <model><doc>what this model is for</doc><variables>'
     '<aux name="a"><eqn>1</eqn></aux></variables></model>\n'),
    ("<doc> on each <dim>, where a subscript comment lands", 2,
     MINIMAL_HEADER + SIM +
     '  <model_dimensions>'
     '<dim name="Region" size="2"><doc>The regions.</doc>'
     '<elem name="North"/><elem name="South"/></dim>'
     '<dim name="Product" size="3"><doc>Product lines.</doc></dim>'
     '</model_dimensions>\n'
     + MODEL),
    ("vensim:doc on the control parameters", 1,
     MINIMAL_HEADER +
     '  <sim_specs><start vensim:doc="The initial time.">0</start>'
     '<stop vensim:doc="The final time.">10</stop>'
     '<dt vensim:doc="The time step.">0.25</dt></sim_specs>\n'
     + MODEL),
    ("<model_dimensions> at the top level", 3,
     MINIMAL_HEADER + SIM +
     '  <model_dimensions><dim name="Region" size="2">'
     '<elem name="North"/><elem name="South"/></dim></model_dimensions>\n'
     '  <model><variables><aux name="a">'
     '<dimensions><dim name="Region"/></dimensions>'
     '<eqn>1</eqn></aux></variables></model>\n'),
    ("the deprecated top-level <dimensions> still works", 3,
     MINIMAL_HEADER + SIM +
     '  <dimensions><dim name="Region" size="2">'
     '<elem name="North"/></dim></dimensions>\n'
     + MODEL),
    ("<plot> with no title", 4,
     MINIMAL_HEADER + SIM +
     '  <model><variables><aux name="a"><eqn>1</eqn></aux></variables>'
     '<views><view><stacked_container uid="1"><graph><plot index="0">'
     '<entity name="a"/></plot></graph></stacked_container></view></views></model>\n'),
    ("<uses_arrays> with no dimension count", 4,
     '  <header><vendor>V</vendor><product version="1">P</product>'
     '<options><uses_arrays/></options></header>\n' + SIM + MODEL),
    ("<uses_arrays maximum_dimensions>, the prose spelling", 4,
     '  <header><vendor>V</vendor><product version="1">P</product>'
     '<options><uses_arrays maximum_dimensions="2"/></options></header>\n' + SIM + MODEL),
    ("<smile> with attribute-style flags", 5,
     '  <header><smile version="1.0" namespace="std, isee" uses_arrays="2"'
     ' uses_conveyor=""/><vendor>V</vendor><product version="1">P</product></header>\n'
     + SIM + MODEL),
    ("<smile> with child-element flags", 5,
     '  <header><smile version="1.0" namespace="std, isee"><uses_conveyor/></smile>'
     '<vendor>V</vendor><product version="1">P</product></header>\n' + SIM + MODEL),
    ("a dimension with a size and no elements", 7,
     MINIMAL_HEADER + SIM +
     '  <model_dimensions><dim name="Region" size="2"/></model_dimensions>\n'
     + MODEL),
    (REJECT + "a dimension with neither elements nor a size", 7,
     MINIMAL_HEADER + SIM +
     '  <model_dimensions><dim name="Region"/></model_dimensions>\n'
     + MODEL),
    (REJECT + "the same, under the deprecated <dimensions>", 7,
     MINIMAL_HEADER + SIM +
     '  <dimensions><dim name="Region"/></dimensions>\n'
     + MODEL),
    ("<license>", 6,
     '  <header><vendor>V</vendor><product version="1">P</product>'
     '<license spdx="CC-BY-4.0" url="https://example.org/terms">Creative Commons</license>'
     '</header>\n' + SIM + MODEL),
]


def errors(schema, path):
    try:
        return [" ".join(str(e.reason or "").split()) for e in schema.iter_errors(path)]
    except Exception as exc:                                  # noqa: BLE001
        return ["NOT WELL-FORMED: %s" % exc]


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--corpus", default=r"D:/vensim/VensimTest/trunk/XMILE")
    args = ap.parse_args(argv)

    for path in (BASE, PROP):
        if not os.path.exists(path):
            sys.exit("not found: %s" % path)
    base = xmlschema.XMLSchema11(BASE)
    prop = xmlschema.XMLSchema11(PROP)
    print("both schemas compile as XSD 1.1\n")

    print("=== the changes, one case each ===")
    tmp = tempfile.mkdtemp()
    worst = 0
    for label, change, body in CASES:
        p = os.path.join(tmp, "case.xmile")
        io.open(p, "w", encoding="utf-8").write(HDR % body)
        before, after = errors(base, p), errors(prop, p)
        if label.startswith(REJECT):
            verdict = "rejected" if after else "WRONGLY ACCEPTED"
            if not after:
                worst = 1
        else:
            verdict = "fixed" if before and not after else (
                "already valid" if not before and not after else "STILL FAILS")
            if verdict == "STILL FAILS":
                worst = 1
        print("  %d  %-44s %-14s (%d -> %d)"
              % (change, label.replace(REJECT, ""), verdict, len(before), len(after)))
        if after and not label.startswith(REJECT):
            for a in after[:2]:
                print("         %s" % a[:96])

    paths = sorted(sum((glob.glob(os.path.join(args.corpus, "**", "*." + e),
                                  recursive=True)
                        for e in ("xmile", "stmx", "itmx")), []))
    if not paths:
        print("\nno corpus at %s; skipping the regression check" % args.corpus)
        return worst

    print("\n=== regression check over %d documents ===" % len(paths))
    tot_before = tot_after = 0
    regressed, improved, revealed = [], [], []
    for p in paths:
        before, after = errors(base, p), errors(prop, p)
        tot_before += len(before)
        tot_after += len(after)
        # A message present after but not before is not by itself a regression. The
        # validator stops descending at an error, so fixing one error exposes whatever
        # sat behind it. Only a rising count means the schema rejects more than it did.
        new = set(after) - set(before)
        if len(after) > len(before):
            regressed.append((p, sorted(new)[:3]))
        else:
            if len(after) < len(before):
                improved.append((p, len(before) - len(after)))
            if new:
                revealed.append((p, sorted(new)[:2]))

    print("  errors: %d -> %d  (%+d)" % (tot_before, tot_after, tot_after - tot_before))
    print("  files improved: %d" % len(improved))
    for p, n in sorted(improved, key=lambda r: -r[1])[:8]:
        print("      %-52s %d fewer" % (os.path.basename(p)[:52], n))

    if revealed:
        print("\n  errors revealed behind ones now fixed, in %d file(s):" % len(revealed))
        seen = set()
        for p, msgs in revealed:
            for m in msgs:
                if m[:60] not in seen:
                    seen.add(m[:60])
                    print("      %s" % m[:104])
        print("      (these were always wrong; the validator could not reach them)")

    if regressed:
        worst = 1
        print("\n  REGRESSIONS in %d file(s) -- the proposal is not additive:"
              % len(regressed))
        for p, msgs in regressed[:10]:
            print("      %s" % os.path.basename(p))
            for m in msgs:
                print("          %s" % m[:100])
    else:
        print("\n  no file gained an error. Six changes are additive by construction;")
        print("  change 7 is restrictive and this is what shows it costs nothing here.")
    return worst


if __name__ == "__main__":
    sys.exit(main())
