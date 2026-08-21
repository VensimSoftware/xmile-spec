# SPDX-License-Identifier: MIT
# Copyright (c) 2026 Ventana Systems, Inc. See LICENSE-Ventana.md.
"""Validate xmile-v1.x-proposal.xsd: it must accept everything the published
schema accepts, plus vendor extensions, and must still reject junk."""
import glob, os, sys
from lxml import etree

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(HERE))    # tools/v-generate/ -> repo root
OUT = os.path.join(REPO, 'proposals', 'schema')  # where generated schemas live
MODELS = os.path.join(REPO, 'models')            # the corpus to measure against
BASE = MODELS                                    # the corpus to measure against
XMILE = "http://docs.oasis-open.org/xmile/ns/XMILE/v1.0"

orig = etree.XMLSchema(etree.parse(os.path.join(HERE, "xmile-v1.0.xsd")))
print("published schema compiles: OK")
prop = etree.XMLSchema(etree.parse(os.path.join(OUT, "xmile-v1.x-proposal.xsd")))
print("proposal  schema compiles: OK\n")

# ---------------------------------------------------------------- regression
files = sorted(glob.glob(BASE + "/**/*.xmile", recursive=True) +
               glob.glob(BASE + "/**/*.stmx", recursive=True))
same = gained = lost = unparsable = 0
gained_names, lost_names = [], []
for f in files:
    try:
        doc = etree.parse(f)
    except Exception:
        unparsable += 1
        continue
    o, p = orig.validate(doc), prop.validate(doc)
    if o == p:
        same += 1
    elif p and not o:
        gained += 1
        gained_names.append(os.path.relpath(f, BASE))
    else:
        lost += 1
        lost_names.append(os.path.relpath(f, BASE))

print("corpus: %d files (%d unparsable XML, skipped)" % (len(files), unparsable))
print("  same verdict under both schemas : %d" % same)
print("  invalid before, VALID now       : %d" % gained)
print("  valid before, invalid now       : %d   <-- must be 0" % lost)
for n in lost_names:
    print("      REGRESSION:", n)
for n in gained_names[:12]:
    print("      newly valid:", n)
if len(gained_names) > 12:
    print("      ... and %d more" % (len(gained_names) - 12))

# ------------------------------------------------------------- targeted cases
HDR = ('<header><vendor>Ventana Systems</vendor><product version="1.0">Vensim</product>'
       '<name>t</name></header>')


def doc(body, extra_ns=""):
    return ('<?xml version="1.0"?>\n<xmile version="1.0" xmlns="%s" '
            'xmlns:vensim="http://www.vensim.com/XMILE" '
            'xmlns:isee="http://iseesystems.com/XMILE"%s>%s'
            '<model><variables>%s</variables></model></xmile>'
            % (XMILE, extra_ns, HDR, body))


CASES = [
    # (label, body, expect_valid_under_proposal)
    ("plain stock, no extensions",
     '<stock name="S"><eqn>0</eqn></stock>', True),
    ("vendor ELEMENT in a stock  <vensim:netflow>",
     '<stock name="S"><eqn>0</eqn><vensim:netflow>(a-S)/tau</vensim:netflow></stock>', True),
    ("vendor ATTRIBUTE           isee:varattrib",
     '<stock name="S" isee:varattrib="data"><eqn>0</eqn></stock>', True),
    ("FOUR vendor attributes, two namespaces, one tag",
     '<stock name="S" isee:varattrib="data" isee:units="X" '
     'vensim:supplementary="true" vensim:group="Core"><eqn>0</eqn></stock>', True),
    ("vendor element among many children (order-independent)",
     '<stock name="S"><vensim:netflow>x</vensim:netflow><eqn>0</eqn>'
     '<units>widgets</units><vensim:attach>y</vensim:attach><doc>d</doc></stock>', True),
    ("vendor element nested inside <element> (arrays)",
     '<stock name="S"><element subscript="a"><eqn>0</eqn>'
     '<vensim:netflow>z</vensim:netflow></element></stock>', True),
    ("REJECT: unprefixed unknown element (inherits XMILE ns)",
     '<stock name="S"><eqn>0</eqn><bonkerstag>x</bonkerstag></stock>', False),
    ("REJECT: unknown element forced to no namespace",
     '<stock name="S"><eqn>0</eqn><bonkerstag xmlns="">x</bonkerstag></stock>', False),
    ("REJECT: unprefixed unknown attribute",
     '<stock name="S" foreignattribute="nonsense"><eqn>0</eqn></stock>', False),
    ("REJECT: vendor element placed IN the XMILE namespace",
     '<stock name="S"><eqn>0</eqn><netflow>x</netflow></stock>', False),
]

print("\ntargeted cases (proposal schema):")
bad = 0
for label, body, expect in CASES:
    d = etree.fromstring(doc(body).encode())
    got = prop.validate(d)
    ok = (got == expect)
    bad += not ok
    print("  %-4s %-52s %s%s" % ("PASS" if ok else "FAIL", label,
                                 "valid" if got else "rejected",
                                 "" if ok else "   <-- expected %s" % expect))

# the same vendor cases must fail under the published schema, or the whole
# proposal is pointless
print("\nsame vendor cases under the PUBLISHED schema (all must be rejected):")
for label, body, expect in CASES[1:6]:
    d = etree.fromstring(doc(body).encode())
    got = orig.validate(d)
    print("  %-4s %-52s %s" % ("PASS" if not got else "FAIL", label,
                               "valid" if got else "rejected"))
    bad += bool(got)

# xs:all elements: attributes yes, elements no
print("\nxs:all elements (header): attribute wildcard applies, element wildcard cannot:")
for label, hdr, expect in [
    ("vendor attribute on <header>",
     '<header isee:draw_as="x"><vendor>V</vendor></header>', True),
    ("vendor element inside <header> (known limitation)",
     '<header><vendor>V</vendor><vensim:x>1</vensim:x></header>', False),
]:
    src = ('<?xml version="1.0"?>\n<xmile version="1.0" xmlns="%s" '
           'xmlns:vensim="http://www.vensim.com/XMILE" '
           'xmlns:isee="http://iseesystems.com/XMILE">%s<model><variables/></model></xmile>'
           % (XMILE, hdr))
    got = prop.validate(etree.fromstring(src.encode()))
    ok = got == expect
    bad += not ok
    print("  %-4s %-52s %s" % ("PASS" if ok else "FAIL", label,
                               "valid" if got else "rejected"))

print("\n%s" % ("ALL CHECKS PASSED" if not bad else "%d CHECK(S) FAILED" % bad))
sys.exit(1 if bad else 0)
