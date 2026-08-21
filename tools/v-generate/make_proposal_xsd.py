# SPDX-License-Identifier: MIT
# Copyright (c) 2026 Ventana Systems, Inc. See LICENSE-Ventana.md.
"""Generate a vendor-extensible XMILE schema from xmile-v1.0.xsd.

    py -3.12 make_proposal_xsd.py            -> xmile-v1.x-proposal.xsd       (XSD 1.0)
    py -3.12 make_proposal_xsd.py --xsd11    -> xmile-v1.x-proposal-11.xsd    (XSD 1.1)

The two exist to be compared. They express the same intent -- let a vendor add elements
and attributes in its own namespace, and nothing else -- and the difference in what it
costs to say it is the point:

    XSD 1.0    143 wildcard particles across the schema (+249 lines), and 27 xs:all
               content models that cannot be opened at all
    XSD 1.1    two declarations at the top plus four derived-type exemptions
               (+11 lines), and nothing left closed

compare_proposals.py measures both and validates the corpus against each.

against which stands the tooling penalty: libxml2 (and so lxml, xmllint, nokogiri, PHP)
implements XSD 1.0 only, as does .NET's XmlSchemaSet, and Java's default JAXP path.
The 1.1 file is unreadable to all of them -- not "fails validation", but "cannot load the
schema". Validating it needs Xerces-J with the v1.1 grammar requested explicitly,
Saxon-EE, or the Python `xmlschema` package (py -3.12 -m pip install xmlschema);
check_proposal_xsd.py uses the last of those when it is installed.

The file names deliberately say "-11" rather than "v1.1": XMILE v1.1 is a version of the
standard, and this is a version of the schema language. They are unrelated.

--- XSD 1.0 (the default) ---------------------------------------------------

Adds the vendor-extension points described in section 1a of
XMILE_TC_proposal.md, and nothing else:

    <xs:any          namespace="##other" processContents="lax" .../>
    <xs:anyAttribute namespace="##other" processContents="lax"/>

Element wildcard placement, by compositor:

  choice maxOccurs="unbounded"   one bare <xs:any/> added as a further branch,
                                 so vendor elements may appear anywhere among
                                 the standard children.
  anything else (sequence, or a  the existing content model is wrapped in a new
  choice that occurs once)       xs:sequence and the wildcard appended after it,
                                 which preserves the original semantics exactly
                                 and places vendor elements last.
  all                            left alone.  XSD 1.0 forbids a wildcard inside
                                 xs:all - its content model is
                                 (annotation?, element*) - and All Group Limited
                                 forbids wrapping it.  Reported at the end.

The attribute wildcard is unaffected by any of this: xs:anyAttribute is a child
of the complexType (or of the extension/restriction under simple/complexContent),
not of the content model, so every complexType gets one.

--- XSD 1.1 (--xsd11) -------------------------------------------------------

Two schema-level mechanisms replace every one of those insertions:

  xs:defaultOpenContent   opens every complexType with complex content, including the
                          xs:all groups, which 1.1 relaxes to admit wildcards.
                          mode="interleave" lets vendor elements appear anywhere among
                          the standard children rather than only at the end;
                          appliesToEmpty="true" extends it to empty types such as
                          <queue> and <non_negative>.
  defaultAttributes       applies a named attributeGroup to every complexType in the
                          document. This is the half people forget: defaultOpenContent
                          governs ELEMENTS ONLY, and without defaultAttributes a 1.1
                          schema accepts vendor elements and rejects vendor attributes.

Both are additive. Nothing in the existing 2000 lines needs rewriting: 1.1 is a superset
for everything this schema does, and UPA is retained, so no content model changes meaning.
"""
import os
import sys
from lxml import etree

XS = "http://www.w3.org/2001/XMLSchema"
Q = lambda t: "{%s}%s" % (XS, t)

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(HERE))    # tools/v-generate/ -> repo root
OUT = os.path.join(REPO, 'proposals', 'schema')  # where generated schemas live
MODELS = os.path.join(REPO, 'models')            # the corpus to measure against


SRC_NAME = "xmile-v1.0.xsd"
DST_NAME = "xmile-v1.x-proposal.xsd"
DST_NAME_11 = "xmile-v1.x-proposal-11.xsd"
DST_NAME_CT = "xmile-v1.x-proposal-container.xsd"

VC = "http://www.w3.org/2007/XMLSchema-versioning"
ATTR_GROUP = "vendor_attributes"
CONTAINER = "extensions"


def locate(name):
    """A bare name is looked for beside this script, then in proposals/schema."""
    if os.path.isabs(name) or os.path.dirname(name):
        return name
    for d in (HERE, OUT):
        p = os.path.join(d, name)
        if os.path.exists(p):
            return p
    return os.path.join(HERE, name)


XSD11 = "--xsd11" in sys.argv
CONTAINERS = "--container" in sys.argv
if XSD11 and CONTAINERS:
    sys.exit("--xsd11 and --container are alternatives; pick one")
args = [a for a in sys.argv[1:] if not a.startswith("--")]

SRC = locate(args[0] if args else SRC_NAME)
if not os.path.exists(SRC):
    sys.exit("source schema not found: %s" % SRC)

# Generated schemas belong to the proposal, not to the specification, so they
# are written to proposals/schema rather than beside the baseline they came from.
DST = (args[1] if len(args) > 1
       else os.path.join(OUT,
                         DST_NAME_11 if XSD11 else
                         DST_NAME_CT if CONTAINERS else DST_NAME))

tree = etree.parse(SRC)
root = tree.getroot()

stats = dict(any_branch=0, any_wrapped=0, anyattr=0, skipped_all=0, skipped_content=0,
             containers=0)
closed = []


def path_of(el):
    """Slash-path of named ancestors, to tell view/stock from variables/stock."""
    names, p = [], el
    while p is not None:
        if p.tag in (Q("element"), Q("complexType")) and p.get("name"):
            names.append(p.get("name"))
        p = p.getparent()
    return "/".join(reversed(names)) or "(anonymous)"


def make(tag, **attrs):
    e = etree.Element(Q(tag))
    for k, v in attrs.items():
        e.set(k, v)
    return e


def append_child(parent, child):
    """Append as the last child, keeping the file's own indentation.

    The last child's tail is the whitespace that closes the parent, so it has to
    move to the new child; the new child inherits the indentation the parent uses
    for its children.
    """
    child_indent = parent.text if (parent.text and "\n" in parent.text) else "\n"
    if len(parent):
        child.tail = parent[-1].tail
        parent[-1].tail = child_indent
    else:
        child.tail = parent.text
        parent.text = child_indent
    parent.append(child)


def reindent(el, extra="  "):
    """Push a subtree one level deeper."""
    for n in el.iter():
        if n.text and "\n" in n.text:
            n.text = n.text.replace("\n", "\n" + extra)
        if n.tail and "\n" in n.tail:
            n.tail = n.tail.replace("\n", "\n" + extra)


CONTENT = (Q("sequence"), Q("choice"), Q("all"), Q("group"))
DERIVED = (Q("simpleContent"), Q("complexContent"))


def build_xsd11():
    """The whole XSD 1.1 transform: two schema-level declarations, no per-type edits."""
    indent = root.text if (root.text and "\n" in root.text) else "\n  "

    # xs:defaultOpenContent must precede the first top-level declaration -- the content
    # model of xs:schema is (include|import|redefine|override|annotation)*, then
    # defaultOpenContent, then the declarations. There are no imports here, so index 0.
    doc = make("defaultOpenContent", mode="interleave", appliesToEmpty="true")
    doc.text = indent + "  "
    doc.tail = indent
    wildcard = make("any", namespace="##other", processContents="lax")
    wildcard.tail = indent
    doc.append(wildcard)
    root.insert(0, doc)

    group = make("attributeGroup", name=ATTR_GROUP)
    group.text = indent + "  "
    group.tail = indent
    attr = make("anyAttribute", namespace="##other", processContents="lax")
    attr.tail = indent
    group.append(attr)
    root.insert(1, group)

    # defaultAttributes is the companion for attributes; defaultOpenContent covers
    # elements only. vc:minVersion marks the file for what it is -- a 1.0 processor still
    # cannot read it, because xs:defaultOpenContent is an element it does not know, but a
    # 1.1 processor is told plainly which grammar was intended.
    root.set("defaultAttributes", ATTR_GROUP)
    etree.register_namespace("vc", VC)
    root.set("{%s}minVersion" % VC, "1.1")

    # The one place the blanket rule does not fit, and the reason this is worth
    # generating rather than describing. defaultAttributes applies the group to EVERY
    # complexType, derived ones included -- but an attribute wildcard already propagates
    # from base to derived type, so a complexContent extension or restriction gets it
    # twice and is rejected: "default attribute is already declared in the complex type".
    # 1.1 provides defaultAttributesApply for exactly this. The exempted types still
    # accept vendor attributes, inherited from their base; nothing is given up.
    exempt = 0
    for ct in root.iter(Q("complexType")):
        if ct.find(Q("complexContent")) is not None:
            ct.set("defaultAttributesApply", "false")
            exempt += 1
    return exempt


EXEMPT_11 = build_xsd11() if XSD11 else 0

for ct in ([] if XSD11 else root.iter(Q("complexType"))):
    model = None
    for kid in ct:
        if kid.tag in CONTENT or kid.tag in DERIVED:
            model = kid
            break

    # ---- element wildcard -------------------------------------------------
    if model is None:
        pass                                  # attribute-only type; nothing to open
    elif model.tag == Q("choice") and model.get("maxOccurs") == "unbounded":
        append_child(model, make("any", namespace="##other", processContents="lax"))
        stats["any_branch"] += 1
    elif model.tag in (Q("choice"), Q("sequence"), Q("group")):
        idx = list(ct).index(model)
        outer_tail = model.tail
        inner_indent = (ct.text if (ct.text and "\n" in ct.text) else "\n") + "  "
        wrapper = make("sequence")
        wrapper.tail = outer_tail
        wrapper.text = inner_indent
        ct.remove(model)
        reindent(model)
        model.tail = inner_indent
        wrapper.append(model)
        append_child(wrapper, make("any", namespace="##other", processContents="lax",
                                   minOccurs="0", maxOccurs="unbounded"))
        wrapper[-1].tail = ct.text if (ct.text and "\n" in ct.text) else "\n"
        ct.insert(idx, wrapper)
        stats["any_wrapped"] += 1
    elif model.tag == Q("all"):
        if CONTAINERS:
            # A wildcard is illegal inside xs:all, but a named ELEMENT is not, so the
            # wildcard moves inside a container element that is itself declared in the
            # XMILE namespace. Same reach, no compositor change, still plain XSD 1.0.
            append_child(model, make("element", ref=CONTAINER, minOccurs="0"))
            stats["containers"] += 1
        else:
            stats["skipped_all"] += 1
            closed.append(path_of(ct))
    else:
        stats["skipped_content"] += 1         # simple/complexContent: no element children

    # ---- attribute wildcard ----------------------------------------------
    host = ct
    if model is not None and model.tag in DERIVED:
        for kid in model:
            if kid.tag in (Q("extension"), Q("restriction")):
                host = kid
                break
    if host.find(Q("anyAttribute")) is None:
        append_child(host, make("anyAttribute", namespace="##other", processContents="lax"))
        stats["anyattr"] += 1

if CONTAINERS:
    # Declared once, globally, and referenced -- so there is exactly one element name an
    # implementation has to learn to skip, and one place to change the rule. Added after
    # the main loop so it does not pick up the blanket anyAttribute: what a vendor puts
    # inside carries its own attributes, and the container itself needs none.
    indent = root.text if (root.text and "\n" in root.text) else "\n  "
    decl = make("element", name=CONTAINER)
    decl.text = indent + "  "
    decl.tail = indent
    ctype = make("complexType")
    ctype.text = indent + "    "
    ctype.tail = indent
    seq = make("sequence")
    seq.text = indent + "      "
    seq.tail = indent + "  "
    wild = make("any", namespace="##other", processContents="lax",
                maxOccurs="unbounded")
    wild.tail = indent + "    "
    seq.append(wild)
    ctype.append(seq)
    decl.append(ctype)
    root.append(decl)


BANNER_CT = """

  MODIFIED COPY - NOT A PUBLISHED ARTEFACT.

  xmile-v1.x-proposal-container.xsd = xmile-v1.0.xsd (OASIS Standard, 14 December
  2015) plus a HYBRID form of the vendor-extension proposal in section 1a of
  Ventana Systems' submission to the XMILE TC.  Generated mechanically.

  Two mechanisms, chosen per content model by what XSD 1.0 permits there:

    xs:choice / xs:sequence   an inline wildcard, exactly as in
                              xmile-v1.x-proposal.xsd, so files that vendors
                              already write - <vensim:netflow> inside a <stock> -
                              become valid with no change to them.

    xs:all                    a wildcard is illegal there (the content model is
                              (annotation?, element*)), so the wildcard moves
                              inside a container element:

                                <xs:element ref="extensions" minOccurs="0"/>

                              A named element IS legal inside xs:all, which is
                              what makes this work without changing compositors
                              and without XSD 1.1.  The container is declared
                              once at the foot of this file.

  This is the same reach as the XSD 1.1 version - nothing is left closed - in a
  file that libxml2 can still read.  The price is that vendor elements in
  <header>, <sim_specs>, <style>, <view> and the view widgets must move inside
  <extensions>; files written today do not become valid there, they become
  expressible there.

  Attributes are unaffected by all of this and use the blanket wildcard
  everywhere, container or not:

    <xs:anyAttribute namespace="##other" processContents="lax"/>

  ##other means the same throughout: any foreign namespace and nothing else, so
  <bonkerstag> and foreignattribute="..." are still rejected - inside the
  container as well as outside it, which a bare <xs:any/> would not do, its
  default being ##any.

"""

BANNER_11 = """

  MODIFIED COPY - NOT A PUBLISHED ARTEFACT.

  xmile-v1.x-proposal-11.xsd = xmile-v1.0.xsd (OASIS Standard, 14 December 2015)
  plus the XSD 1.1 form of the vendor-extension proposal in section 1a of Ventana
  Systems' submission to the XMILE TC.  Generated mechanically, not hand-edited.

  "-11" is the version of the SCHEMA LANGUAGE, not of XMILE.  XMILE v1.1 is a
  different thing entirely and this file has nothing to do with it.

  The whole change is the two declarations at the top of the file:

    <xs:defaultOpenContent mode="interleave" appliesToEmpty="true">
      <xs:any namespace="##other" processContents="lax"/>
    </xs:defaultOpenContent>

    <xs:attributeGroup name="vendor_attributes">
      <xs:anyAttribute namespace="##other" processContents="lax"/>
    </xs:attributeGroup>

  ... plus defaultAttributes="vendor_attributes" on <xs:schema>, which is what
  applies that group to every complexType.  defaultOpenContent governs ELEMENTS
  ONLY; without defaultAttributes a 1.1 schema would take vendor elements and
  reject vendor attributes.

  Compare xmile-v1.x-proposal.xsd, which says the same thing in XSD 1.0 and needs
  143 wildcard particles spread through the file to do it.  This version also has
  no gap: 1.1 relaxes xs:all to admit wildcards, so the 27 content models that
  the 1.0 version has to leave closed to vendor elements are open here.

  ##other means the same in both: any foreign namespace and nothing else, so
  <bonkerstag> and foreignattribute="..." are still rejected while
  <vensim:netflow> and isee:varattrib="data" pass.

  THE COST IS TOOLING, and it is not a graceful degradation.  libxml2 implements
  XSD 1.0 only - and so do lxml, xmllint, nokogiri and PHP - as do .NET's
  XmlSchemaSet and Java's default JAXP path.  None of them can LOAD this file;
  xs:defaultOpenContent is simply an element they do not know.  Validating it
  needs Xerces-J with the v1.1 grammar requested explicitly, Saxon-EE, or the
  Python xmlschema package.  vc:minVersion="1.1" marks the file for what it is,
  but cannot rescue a 1.0 processor: conditional inclusion is itself a 1.1
  feature.

"""

BANNER_10 = """

  MODIFIED COPY - NOT A PUBLISHED ARTEFACT.

  xmile-v1.x-proposal.xsd = xmile-v1.0.xsd (OASIS Standard, 14 December 2015)
  plus the vendor-extension points proposed in section 1a of Ventana Systems'
  submission to the XMILE TC.  Generated mechanically, not hand-edited: the only
  differences from the published schema are the added wildcard particles.

    <xs:any          namespace="##other" processContents="lax" .../>
    <xs:anyAttribute namespace="##other" processContents="lax"/>

  ##other admits any foreign namespace and nothing else.  An element or
  attribute in the XMILE namespace itself, or in no namespace at all, is still
  rejected - so <bonkerstag> and foreignattribute="..." fail exactly as they do
  today, while <vensim:netflow> and isee:varattrib="data" pass.  processContents
  "lax" validates a foreign element when the processor happens to hold a schema
  for its namespace and passes over it otherwise.

  This is plain XSD 1.0.  It compiles and validates under libxml2, which is what
  lxml, xmllint and a good deal of what implementers actually use are built on,
  and which supports no version beyond 1.0.

  ONE LIMITATION, and the reason this is a demonstration rather than a finished
  proposal: XSD 1.0 forbids a wildcard inside xs:all, whose content model is
  (annotation?, element*), and forbids wrapping an xs:all in anything else.  The
  elements listed at the foot of this file therefore accept vendor ATTRIBUTES
  but not vendor ELEMENTS.  Opening those too needs either a change of
  compositor - which costs xs:all its unordered and at-most-once guarantees - or
  XSD 1.1, where xs:all admits wildcards and where a single xs:defaultOpenContent
  plus one defaultAttributes group would replace every insertion made here.

"""

banner = etree.Comment(BANNER_11 if XSD11 else BANNER_CT if CONTAINERS else BANNER_10)
root.insert(0, banner)
banner.tail = "\n"

if not XSD11 and not CONTAINERS:
    footer = etree.Comment(
        "\n\n  Closed to vendor ELEMENTS (xs:all content models); vendor attributes\n"
        "  are accepted on all of them:\n\n"
        + "\n".join("    " + n for n in sorted(set(closed))) + "\n\n")
    root.append(footer)
    footer.tail = "\n"

tree.write(DST, encoding="UTF-8", xml_declaration=True)

if XSD11:
    print("xs:defaultOpenContent        : 1   (opens every complexType, xs:all included)")
    print("defaultAttributes group      : 1   (the attribute half; not covered by the above)")
    print("per-type edits               : %d   (defaultAttributesApply=false on derived types)" % EXEMPT_11)
    print("content models left closed   : 0")
else:
    print("xs:any as choice branch      : %d" % stats["any_branch"])
    print("xs:any after wrapped model   : %d" % stats["any_wrapped"])
    print("xs:anyAttribute              : %d" % stats["anyattr"])
    if CONTAINERS:
        print("<%s> refs into xs:all  : %d" % (CONTAINER, stats["containers"]))
        print("content models left closed   : 0")
    else:
        print("xs:all left closed           : %d particles, %d distinct paths"
              % (stats["skipped_all"], len(set(closed))))
    print("simple/complexContent        : %d (no element children possible)"
          % stats["skipped_content"])
print()
print("source : %s" % SRC)
print("written: %s" % DST)
if not XSD11 and not CONTAINERS:
    print()
    for n in sorted(set(closed)):
        print("   closed:", n)
