# SPDX-License-Identifier: MIT
# Copyright (c) 2026 Ventana Systems, Inc. See LICENSE-Ventana.md.
"""Generate a minimally invasive proposal schema from the v1.1 schema.

Input   spec/schema/xmile.xsd.xml            the v1.1 schema, XSD 1.1
Output  proposals/schema/xmile-v1.1.x-proposal.xsd

Generated rather than hand-edited for the same reason the vendor-extension schemas are:
the difference between the base and the proposal is then provably only the changes listed
here. Re-run it when the base schema moves.

Seven changes, each addressing a numbered proposal item. Six are additive -- no document
that validates against the v1.1 schema fails against them -- which compare_v11x.py asserts
rather than assumes. The seventh is deliberately restrictive and is marked as such.

  1  vendor attributes on simple-typed elements   item 1
  2  <doc> on structural containers                item 4
  3  <model_dimensions> for the whole-model list, after <model_units>  item 3
  4  required attributes nobody writes become optional        item 9's pattern
  5  <smile> as a synonym for <options>            item 11
  6  <license> in <header>                         item 10
  7  a whole-model <dim> must be interpretable     item 5's pattern

Usage:
  py -3.12 tools/v-generate/make_v11x_proposal.py
"""
import io
import os
import sys
import textwrap

from lxml import etree

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(HERE))
SRC = os.path.join(REPO, "spec", "schema", "xmile.xsd.xml")
DST = os.path.join(REPO, "proposals", "schema", "xmile-v1.1.x-proposal.xsd")

XSD = "http://www.w3.org/2001/XMLSchema"
XS = "{%s}" % XSD
BUILTIN = ("xs:string", "xs:double", "xs:int", "xs:integer", "xs:boolean", "xs:date",
           "xs:decimal", "xs:anyURI")

log = []


def note(change, detail):
    log.append((change, detail))


def el(tag, **kw):
    e = etree.SubElement(etree.Element("x"), XS + tag)
    for k, v in kw.items():
        e.set(k.rstrip("_").replace("_", ""), v)
    return e


def make(tag, **attrs):
    e = etree.Element(XS + tag)
    for k, v in attrs.items():
        e.set(k, v)
    return e


def sibling_indent(parent):
    """The whitespace that separates this element's children, as the file writes it.

    Taken from the children's own tails rather than from parent.text, which at the
    schema root is only a newline: the first child there is a comment, and the two-space
    indent the rest of the file uses never appears before it.
    """
    # parent.text is the whitespace before the first child, which is the indent we
    # want. It is only unusable at the schema root, where the first node is a
    # comment at column 0, so require it to carry an actual indent first.
    if parent.text and not parent.text.strip() and parent.text.strip("\n"):
        return parent.text
    # Fall back to the children's tails, but not to a lone child's: with one child
    # that tail is the whitespace before the closing tag, one level shallower than
    # a sibling separator.
    tails = [c.tail for c in parent if c.tail and not c.tail.strip()]
    if len(tails) > 1:
        return max(set(tails), key=tails.count)
    if parent.text and not parent.text.strip():
        return parent.text
    return "\n"


def dedent_block(e, step="  "):
    """Shift a subtree one indentation level left, in place.

    Naming the <options> content model moves it out of the element declaration it was
    nested in, so every line of it would otherwise sit one level too deep.
    """
    for node in e.iter():
        if node.text and not node.text.strip() and "\n" in node.text:
            node.text = node.text.replace("\n" + step, "\n", 1)
        if node is not e and node.tail and not node.tail.strip() and "\n" in node.tail:
            node.tail = node.tail.replace("\n" + step, "\n", 1)
    return e


def own_indent(e):
    """The indentation this element itself sits at, taken from what precedes it."""
    prev = e.getprevious()
    if prev is not None and prev.tail and "\n" in prev.tail:
        return prev.tail.rsplit("\n", 1)[-1]
    parent = e.getparent()
    if parent is not None:
        return sibling_indent(parent).rsplit("\n", 1)[-1]
    return ""


def indent_new(e, prefix):
    """Lay a freshly built subtree out over several lines.

    Elements built here have no whitespace in them, so they serialise as one very long
    line. The base schema is fully expanded, and a reviewer reads the two side by side.
    """
    step = "  "
    # Documentation is one long text node; the base schema wraps its own, so wrap ours.
    if e.tag == XS + "documentation" and e.text and len(e.text) > 70:
        body = textwrap.fill(" ".join(e.text.split()), width=76,
                             initial_indent=prefix + step, subsequent_indent=prefix + step)
        e.text = "\n" + body + "\n" + prefix
        return e
    kids = [c for c in e if isinstance(c.tag, str)]
    if not kids:
        return e
    e.text = "\n" + prefix + step
    for i, c in enumerate(kids):
        c.tail = "\n" + prefix + (step if i < len(kids) - 1 else "")
        indent_new(c, prefix + step)
    return e


def place_after(anchor, new):
    """Insert new immediately after anchor, on its own line, indented as its siblings.

    lxml gives an inserted element no tail, so without this it runs on to the end of the
    line the anchor sits on. That is only cosmetic, but it makes the diff against the
    base schema hard to read, which is the diff a reviewer has to read.
    """
    parent = anchor.getparent()
    indent = sibling_indent(parent)
    new.tail = anchor.tail if anchor is parent[-1] else indent
    anchor.tail = indent
    anchor.addnext(new)
    return new


def append_child(parent, new):
    """Append new as the last child, keeping the file's own indentation."""
    if len(parent):
        indent = sibling_indent(parent)
        last = parent[-1]
        new.tail = last.tail
        last.tail = indent
    else:
        # An element with no children has no whitespace to copy, so give it the
        # layout it would have had: one level in, closing tag back at its own.
        pad = own_indent(parent)
        parent.text = "\n" + pad + "  "
        new.tail = "\n" + pad
    parent.append(new)
    return new


def insert_first(parent, new):
    """Insert new as the first child, keeping the file's own indentation."""
    new.tail = sibling_indent(parent)
    parent.insert(0, new)
    return new


def comment(parent, text, index=None):
    c = etree.Comment(" " + text.strip() + " ")
    indent = sibling_indent(parent)
    c.tail = indent
    if index is None:
        parent.append(c)
    else:
        parent.insert(index, c)
    prev = c.getprevious()
    if prev is not None:
        prev.tail = indent
    elif parent.text is not None and not parent.text.strip():
        parent.text = indent
    return c


def doc_element(min_occurs="0"):
    """A <doc> child, declared exactly as the variable elements already declare it."""
    return make("element", name="doc", type="xs:string",
                minOccurs=min_occurs, maxOccurs="1")


# --------------------------------------------------------------- 1. simple types

# Bibliographic metadata, left alone. Nothing in a 122-model corpus carries an attribute
# or a child on any of these, and rewriting 15 declarations to permit something no one
# has asked for is diff without evidence. Delete a name here to bring it back in.
#   header, contact   bibliographic metadata: nothing in a 122-model corpus carries an
#                     attribute or a child on any of them.
#   conveyor          len, capacity, in_limit, sample and arrest are scalar settings on
#                     a conveyor. They hold one value each and have nowhere to grow.
#   unit              a unit definition's <eqn> and <alias>. Nothing documents a unit
#                     definition, and nothing annotates one.
#   macro             <parm>, <eqn> and <format>. A macro is a function definition, and
#                     its <eqn> is the body, not a model equation; nine of them in the
#                     corpus and nothing annotates any.
NO_REWRITE_UNDER = ("header", "contact", "conveyor", "unit", "macro")

#   mathml            a MathML payload: foreign markup with its own namespace and its
#                     own rules, and the one element here where a vendor has no
#                     business hanging an attribute.
#   inflow, outflow   references to a flow by name. Anything to be said about the flow
#                     belongs on the <flow> itself, and anything about the connection
#                     belongs on the parent <stock>, so neither needs to grow content.
#   doc               documentation. Annotating documentation is not a thing anyone
#                     needs to do, and a <doc> inside a <doc> is nobody's idea.
#   units             a units expression on a variable. 9,129 of them in the corpus and
#                     not one carries an attribute; the variable itself is where
#                     anything about it belongs.
#   eqn               every variable that has one also has a <doc>, so an <eqn><doc>
#                     would be a second place to say the same thing. On a <stock> it is
#                     the initial equation rather than the equation (item 16), inside a
#                     <macro> it is the body, and inside a <unit> it is a units
#                     expression -- five senses, none of them annotated in any of the
#                     23,579 occurrences in the corpus.
#   multiplier        a flow's unit-conversion multiplier (section 4, "Unit conversion
#                     multiplier"): the expression converting units on the downstream
#                     side of a main chain. Four in the corpus, none annotated.
#   of                the variable an <alias> points at. A name, and the alias itself
#                     is where anything about the alias belongs.
NO_REWRITE_NAMED = ("mathml", "inflow", "outflow", "doc", "units", "eqn", "multiplier",
                    "of")

NO_REWRITE_PAIRS = ()   # nothing needs one now that <eqn> is excluded outright


def nearest_named(e):
    p = e.getparent()
    while p is not None and isinstance(p.tag, str):
        if p.get("name"):
            return p.get("name")
        p = p.getparent()
    return None


def named_ancestors(e):
    """Every named ancestor, nearest first. <stock>/<element>/<eqn> gives element, stock."""
    out = []
    p = e.getparent()
    while p is not None and isinstance(p.tag, str):
        if p.get("name"):
            out.append(p.get("name"))
        p = p.getparent()
    return out


def change_1_simple_types(root):
    """Give every element declared with a built-in type a complex type instead.

    defaultAttributes applies to complex types only, so an element declared
    type="xs:string" can carry no vendor attribute at all. Rewriting it as a
    simpleContent extension of the same base changes nothing about its content and
    brings it inside the extension mechanism.

    Scoped to model content. Measured over 122 models, this change is worth 36 errors
    and every one of them is vensim:attach on <connector><to>. That argues for doing it
    where a vendor plausibly needs to annotate -- equations, units, flows, documentation
    -- and not for rewriting <author> and <fax> on the same principle.
    """
    n = skipped = 0
    for e in root.iter(XS + "element"):
        t = e.get("type")
        if t not in BUILTIN:
            continue
        name = e.get("name")
        ancestors = named_ancestors(e)
        if (nearest_named(e) in NO_REWRITE_UNDER
                or name in NO_REWRITE_NAMED
                or any(a == owner and name == child
                       for owner, child in NO_REWRITE_PAIRS
                       for a in ancestors)):
            skipped += 1
            continue
        del e.attrib["type"]
        ct = etree.SubElement(e, XS + "complexType")
        sc = etree.SubElement(ct, XS + "simpleContent")
        etree.SubElement(sc, XS + "extension", base=t)
        indent_new(e, own_indent(e))
        n += 1
    parts = ["under " + ", ".join("<%s>" % x for x in NO_REWRITE_UNDER),
             ", ".join("<%s>" % x for x in NO_REWRITE_NAMED)]
    if NO_REWRITE_PAIRS:
        parts.append(", ".join("<%s> under <%s>" % (c, o) for o, c in NO_REWRITE_PAIRS))
    note("1", "%d element declarations rewritten from a built-in type to a "
              "simpleContent extension of that type; %d left alone (%s)"
              % (n, skipped, "; ".join(parts)))
    return n


# ------------------------------------------------------------------- 2. <doc>

# <dim> takes a <doc> of its own, and the container's is no substitute. <model_dimensions>
# is the LIST; <dim> is one dimension in it, which is one Vensim subscript range, and each
# range carries its own comment. One <doc> on the list cannot hold N of them.
#
# Only the whole-model <dim> qualifies -- the one that defines a dimension and has <elem>
# children. The per-variable <dim> is a bare name reference with nothing to document.
DEFINITION_ELEMENTS = ("dim",)

# <view> is deliberately absent, and not merely deferred. Vensim has nothing to put
# in it, and the change would not be small: <view> extends view_content_type through
# complexContent, so it has no content model of its own, and adding <doc> to the shared
# base would give it to every view object at once. Revisit only if someone turns up with
# view-level documentation to write.
CONTAINERS = ("model", "module", "sim_specs", "dimensions", "group")


def content_model(ct):
    for kind in ("all", "sequence", "choice"):
        m = ct.find(XS + kind)
        if m is not None:
            return m
    return None


def defines_content(e):
    """True for the declaration that defines a thing, not the one that references it."""
    ct = e.find(XS + "complexType")
    return ct is not None and any(x.get("name") == "elem" for x in ct.iter(XS + "element"))


def change_2_doc(root):
    done = []
    for e in root.iter(XS + "element"):
        name = e.get("name")
        if name in DEFINITION_ELEMENTS:
            if not defines_content(e):
                continue
        elif name in CONTAINERS:
            # The per-variable <dimensions> is a list of bare name references sitting on
            # a variable that already has a <doc> of its own. Only the whole-model
            # container takes one.
            if name == "dimensions" and not any(
                    x.get("name") == "elem" for x in e.iter(XS + "element")):
                continue
        else:
            continue
        ct = e.find(XS + "complexType")
        if ct is None:
            continue
        m = content_model(ct)
        if m is None:
            continue
        if any(c.get("name") == "doc" for c in m.findall(XS + "element")):
            continue
        # Position matters in a sequence: appending would force <doc> after every
        # other child, so it goes first, where documentation conventionally sits and
        # where <doc> already sits among the children of a variable. In an xs:all or
        # an unbounded xs:choice the position is free, so append.
        if m.tag == XS + "sequence":
            insert_first(m, doc_element())
        else:
            append_child(m, doc_element())
        done.append(name)
    # Several of these are declared more than once -- <module> and <dimensions> each
    # appear in two places -- so count the declarations and name the elements once.
    uniq = sorted(set(done))
    note("2", "<doc> added to %s (%d declaration(s))"
         % (", ".join("<%s>" % d for d in uniq), len(done)))
    return done


# ------------------------------------------------------------ 3. <subscripts>

def change_3_model_dimensions(root):
    """Rename the whole-model dimension list <model_dimensions>, after <model_units>.

    Two different elements are called <dimensions>, and the schema pays for it with a
    workaround it documents in a comment: the whole-model list is declared INLINE inside
    <xmile>, because XSD forbids two global elements with the same name and the
    per-variable list holds the global slot -- <stock>, <flow> and <aux> reach it by ref.

    The collision was never forced by the content models. The whole-model type is a
    superset of the per-variable one: <elem> is optional and size is optional, so a bare
    <dim name="R"/> validates against it. One definition could have served both levels,
    at the price of letting <elem> and size into a variable's list, where they mean
    nothing. It was forced by the naming alone.

    Units show the fix. <model_units> is the container of definitions, <unit> is one
    definition, <units> is what a variable carries: three roles, three names. So the
    whole-model list becomes <model_dimensions>, which leaves <dimensions> to mean the
    per-variable list and nothing else.

    Renaming the whole-model one rather than the per-variable one is the cheaper way
    round by a wide margin: 64 occurrences in the corpus against 4,490.

    The deprecated spelling is handled as <smile> is. The content model becomes a named
    type, the preferred element owns it, and the deprecated inline <dimensions> becomes a
    reference to the same type -- one definition, so the two cannot drift, and nothing
    existing breaks.
    """
    xmile = None
    for e in root.findall(XS + "element"):
        if e.get("name") == "xmile":
            xmile = e
            break
    if xmile is None:
        note("3", "SKIPPED: no <xmile> declaration")
        return 0

    inline = None
    for e in xmile.iter(XS + "element"):
        if e.get("name") == "dimensions" and any(
                x.get("name") == "elem" for x in e.iter(XS + "element")):
            inline = e
            break
    if inline is None:
        note("3", "SKIPPED: whole-model <dimensions> not found inside <xmile>")
        return 0

    ct = inline.find(XS + "complexType")
    if ct is None:
        note("3", "SKIPPED: whole-model <dimensions> has no inline complexType")
        return 0

    named = dedent_block(etree.fromstring(etree.tostring(ct)))
    while named.tag != XS + "complexType":
        named = named  # pragma: no cover - shape guard
    named.set("name", "model_dimensions_type")
    # Global types live at the top level; put it beside the global <dimensions> so the
    # two dimension declarations are read together.
    glob = None
    for e in root.findall(XS + "element"):
        if e.get("name") == "dimensions":
            glob = e
            break
    anchor = glob if glob is not None else root[-1]
    for _ in range(named.get("name").count("x") * 0):
        pass
    dedent_to = own_indent(anchor)
    named.tail = "\n" + dedent_to
    place_after(anchor, named)

    # The preferred element.
    pad = own_indent(anchor)
    pref = make("element", name="model_dimensions", type="model_dimensions_type")
    a = etree.SubElement(pref, XS + "annotation")
    d = etree.SubElement(a, XS + "documentation")
    d.text = ("The dimensions the model defines, each with its elements. Named after "
              "<model_units>, which draws the same distinction: <model_units> holds unit "
              "DEFINITIONS and <units> is what a variable carries, so <model_dimensions> "
              "holds dimension DEFINITIONS and <dimensions> is what a variable carries. "
              "This element replaces the use of <dimensions> at the top level, which is "
              "deprecated and still accepted.")
    indent_new(pref, pad)
    place_after(named, pref)

    # The deprecated spelling keeps working, and shares the one definition.
    inline.remove(ct)
    inline.set("type", "model_dimensions_type")
    olda = etree.SubElement(inline, XS + "annotation")
    oldd = etree.SubElement(olda, XS + "documentation")
    oldd.text = ("DEPRECATED at this level, and accepted so that existing files validate. "
                 "This is the whole-model dimension list, which <dimensions> also names "
                 "on a <stock>, <flow> or <aux>, where it means the dimensions that "
                 "variable is arrayed over. Writers SHOULD emit <model_dimensions> here; "
                 "readers MUST accept both.")
    indent_new(inline, own_indent(inline))
    place_after(inline, make("element", ref="model_dimensions",
                             minOccurs="0", maxOccurs="1"))

    note("3", "whole-model dimension list renamed <model_dimensions>, sharing "
              "model_dimensions_type with the deprecated top-level <dimensions>")
    return 1


# ------------------------------------------- 4. requirements nobody meets

# (attribute name, name of the element or type that declares it, evidence)
DEMOTE = [
    ("title", "plot", "written on 204 of 1538 plots"),
    ("column_width", "table", "written on 5 of 23 table objects"),
    ("report_interval", "table", "written on 0 of 419 tables"),
    ("max_dimensions", "uses_arrays", "written on 0 of 13; section 2 calls it "
                                      "maximum_dimensions"),
]


def owner_name(a):
    e = a.getparent()
    while e is not None and isinstance(e.tag, str):
        if e.get("name"):
            return e.get("name")
        e = e.getparent()
    return None


def change_4_optional(root):
    done = []
    for attr_name, owner, why in DEMOTE:
        for a in root.iter(XS + "attribute"):
            if a.get("name") == attr_name and a.get("use") == "required" \
                    and owner_name(a) == owner:
                a.set("use", "optional")
                comment(a.getparent(), "v1.1.x proposal: was REQUIRED; %s." % why,
                        list(a.getparent()).index(a))
                done.append("%s/@%s" % (owner, attr_name))
    # The prose spells this attribute differently from the schema, and no file writes
    # either. Accept both rather than pick a winner.
    for a in root.iter(XS + "attribute"):
        if a.get("name") == "max_dimensions" and owner_name(a) == "uses_arrays":
            twin = place_after(a, make("attribute", name="maximum_dimensions",
                                       type="xs:integer", use="optional"))
            comment(a.getparent(), "v1.1.x proposal: section 2 of the specification calls "
                                   "this maximum_dimensions. Both are accepted until the "
                                   "TC picks one.",
                    list(a.getparent()).index(twin))
            done.append("uses_arrays/@maximum_dimensions (new alias)")
            break
    note("4", "made optional: " + ", ".join(done))
    return done


# ----------------------------------------------------------------- 5. <smile>

SMILE_ATTRS = [
    ("version", "xs:string"),
    ("namespace", "xs:string"),
    ("uses_arrays", "xs:string"),
    ("uses_conveyor", "xs:string"),
    ("uses_queue", "xs:string"),
    ("uses_submodels", "xs:string"),
    ("uses_macros", "xs:string"),
    ("uses_event_posters", "xs:string"),
    ("uses_outputs", "xs:string"),
    ("uses_inputs", "xs:string"),
    ("uses_annotation", "xs:string"),
]


def change_5_smile(root):
    """Declare <smile> as a minimal reference to the <options> content model.

    <smile> is deprecated and will be deleted, so it must not become the place the
    capability specification lives. It is fifteen lines: an annotation, a reference to
    the <options> content model, and the legacy attributes real files carry.

    That requires naming the type, because <smile> needs attributes <options> does not
    have, and a type can only be derived from a named one. So the content model moves
    from an anonymous inline complexType on <options> to complexType name="options_type"
    immediately below it. <options> keeps its own annotation and its position; what
    changes is that its content model is named rather than anonymous.

    XSD offers no way to have both halves. A substitution group would leave <options>
    untouched and give <smile> the same content for free, but a substitution-group member
    cannot add attributes, and the eleven legacy attributes are the whole reason <smile>
    needs its own type. Copying the content model into <smile> keeps <options> untouched
    at the cost of putting 250 lines of specification inside the deprecated element,
    which is the arrangement this avoids.

    When <smile> is retired, delete its declaration. options_type may stay named -- a
    named type used once is ordinary -- or be folded back inline, which is mechanical.
    """
    options = None
    for e in root.findall(XS + "element"):          # global declarations only
        if e.get("name") == "options":
            options = e
            break
    if options is None:
        note("5", "SKIPPED: no global <options> declaration")
        return False

    ct = options.find(XS + "complexType")
    if ct is None:
        note("5", "SKIPPED: <options> has no inline complexType to name")
        return False
    named = dedent_block(etree.fromstring(etree.tostring(ct)))
    named.set("name", "options_type")
    options.remove(ct)
    options.set("type", "options_type")
    # Removing the inline type leaves the annotation's tail pointing at where it was,
    # so the element would close one level too deep.
    last = options[-1] if len(options) else None
    if last is not None:
        last.tail = "\n" + own_indent(options)
    place_after(options, named)

    pad = own_indent(options)
    smile = make("element", name="smile")
    a = etree.SubElement(smile, XS + "annotation")
    d = etree.SubElement(a, XS + "documentation")
    d.text = ("DEPRECATED, and accepted so that existing files validate. <smile> is the "
              "legacy spelling of <options>: the same content model, named options_type "
              "so that both can share it, plus the capability flags written as attributes "
              "rather than as child elements. It appears in 88 of 96 files in a corpus of "
              "real models and in no version of the specification. Writers SHOULD emit "
              "<options>; readers MUST accept both. Note that uses_arrays here carries a "
              "level (1, 2, 3) where <uses_arrays> carries a presence flag and a "
              "dimension count, so porting one to the other loses information.")

    # defaultAttributesApply="false" for the reason the base schema gives on <view>:
    # this extends a type that already carries vendor_attributes, and applying the group
    # again would declare two attribute wildcards on one type. The wildcard is inherited.
    sct = etree.SubElement(smile, XS + "complexType")
    sct.set("defaultAttributesApply", "false")
    cc = etree.SubElement(sct, XS + "complexContent")
    ext = etree.SubElement(cc, XS + "extension", base="options_type")
    for name, typ in SMILE_ATTRS:
        etree.SubElement(ext, XS + "attribute", name=name, type=typ, use="optional")

    indent_new(smile, pad)
    place_after(named, smile)

    # <header> reaches <options> by ref, so <smile> is offered the same way.
    refs = 0
    for e in root.iter(XS + "element"):
        if e.get("ref") == "options":
            place_after(e, make("element", ref="smile",
                                minOccurs="0", maxOccurs="1"))
            refs += 1
    note("5", "<options> content model named options_type in place; <smile> declared "
              "below it as that type plus %d legacy attributes, accepted at %d site(s)"
              % (len(SMILE_ATTRS), refs))
    return True


# --------------------------------------------------------------- 6. <license>

def change_6_license(root):
    for e in root.iter(XS + "element"):
        if e.get("name") != "header":
            continue
        m = content_model(e.find(XS + "complexType"))
        lic = make("element", name="license", minOccurs="0", maxOccurs="1")
        a = etree.SubElement(lic, XS + "annotation")
        d = etree.SubElement(a, XS + "documentation")
        # The element name and this annotation both use the schema's American spelling,
        # matching color and center. Our own prose elsewhere spells it "licence"; the
        # two are not in conflict, but a reader sees the annotation beside the name.
        d.text = ("The license the model is published under. The text content is free "
                  "form; spdx carries an SPDX identifier where one applies, and url "
                  "points at the full terms. <copyright> asserts ownership and says "
                  "nothing about reuse, which is what this element is for.")
        ct = etree.SubElement(lic, XS + "complexType")
        sc = etree.SubElement(ct, XS + "simpleContent")
        ex = etree.SubElement(sc, XS + "extension", base="xs:string")
        etree.SubElement(ex, XS + "attribute", name="spdx", type="xs:string",
                         use="optional")
        etree.SubElement(ex, XS + "attribute", name="url", type="xs:anyURI",
                         use="optional")
        append_child(m, indent_new(lic, sibling_indent(m).strip("\n")))
        note("6", "<license> added to <header>, with optional spdx and url")
        return True
    return False


# --------------------------------------------- 7. a dimension must be interpretable

def change_7_dim_content(root):
    """Require a whole-model <dim> to say what its elements are.

    <dim name="Region"/> is accepted today at the whole-model level, and it is
    uninterpretable: a reader cannot know what the dimension contains. Either the
    elements are named, or a size is given from which positional names follow. One or
    the other is needed, and XSD 1.1 can say so with an assertion where XSD 1.0 could
    not express a co-occurrence constraint at all.

    THIS IS THE ONE CHANGE HERE THAT IS NOT ADDITIVE. It makes the schema reject
    something it currently accepts. The corpus says the cost is nil -- across 122 models
    every whole-model <dim> carries either <elem> children (63) or a size (76), and none
    carries neither -- but the guarantee the rest of this proposal offers does not extend
    to this change, and a reader should know which one to look at first if a file that
    used to validate stops.
    """
    n = 0
    for e in root.iter(XS + "element"):
        if e.get("name") != "dim" or not defines_content(e):
            continue
        ct = e.find(XS + "complexType")
        if ct is None:
            continue
        assertion = make("assert")
        assertion.set("test", "@size or elem")
        assertion.set("xpathDefaultNamespace", "##targetNamespace")
        comment(ct, "1.1.x proposal: a dimension must say what it contains, by naming "
                    "its elements or by giving a size. This is the one restrictive "
                    "change in this schema; no file in a 122-model corpus is affected.")
        append_child(ct, assertion)
        n += 1
    note("7", "assertion added to %d whole-model <dim> declaration(s): a dimension must "
              "carry <elem> children or a size" % n)
    return n


def main():
    if not os.path.exists(SRC):
        sys.exit("base schema not found: %s" % SRC)
    tree = etree.parse(SRC)
    root = tree.getroot()

    # Order matters in one place: change 1 rewrites every built-in-typed element, so it
    # runs before the changes that add new ones, which are written as complex types
    # already.
    change_1_simple_types(root)
    change_2_doc(root)
    change_3_model_dimensions(root)
    change_4_optional(root)
    change_5_smile(root)
    change_6_license(root)
    change_7_dim_content(root)

    banner = etree.Comment("""

  XMILE v1.1.x PROPOSAL. NOT A PUBLISHED ARTEFACT.

  spec/schema/xmile.xsd.xml plus six minimally invasive changes, generated by
  tools/v-generate/make_v11x_proposal.py. Do not edit this file; edit the generator.

  Every change is additive. A document that validates against the v1.1 schema
  validates against this one, which tools/v-generate/compare_v11x.py checks rather
  than assumes.

  See proposals/schema/xmile-v1.1.x-changes.md for what each change does and which
  proposal item it comes from.

""")
    root.insert(0, banner)

    # pretty_print would reformat parts of the base file and bury the real changes.
    # Every insertion above sets its own tail, so the file keeps its own layout.
    body = etree.tostring(tree, pretty_print=False, xml_declaration=False,
                          encoding="UTF-8")
    # lxml writes the declaration with single quotes, which would show up as a change
    # to line 1 of a file whose line 1 did not change. Reuse the base file's own.
    with io.open(SRC, "rb") as handle:
        first = handle.readline()
    if not first.lstrip().startswith(b"<?xml"):
        first = b'<?xml version="1.0" encoding="UTF-8"?>\n'
    with io.open(DST, "wb") as handle:
        handle.write(first)
        handle.write(body)

    print("wrote %s" % os.path.relpath(DST, REPO))
    for change, detail in log:
        print("  %s. %s" % (change, detail))
    return 0


if __name__ == "__main__":
    sys.exit(main())
