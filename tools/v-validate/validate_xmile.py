# SPDX-License-Identifier: MIT
# Copyright (c) 2026 Ventana Systems, Inc. See LICENSE-Ventana.md.
r"""Validate every model under /models against the XMILE schemas.

Small, hand-checkable files used to pin down what the schema does and does not accept.
It takes no arguments in the normal case -- it walks /models, including subfolders,
validates every .stmx / .xmile / .mdlx file it finds, and writes one result file beside
each model:

    models/v10-v11/teacup.xmile   ->   models/v10-v11/teacup.xmile.txt

Result files are named after the full source filename, not its stem, because a round-trip
corpus routinely holds teacup.xmile and teacup.stmx side by side.

The console run is grouped by subdirectory, because in /models a subdirectory means
something: it records which version of XMILE the models in it are expected to conform
to. Each group carries its own subtotal, and the run ends with two summaries -- errors
by folder and schema, and verdict counts by folder and schema -- so "did this schema
change help, and where?" is answered without counting lines.

    py -3.12 tools/v-validate/validate_xmile.py                 walk /models, write results
    py -3.12 tools/v-validate/validate_xmile.py --stdout        print instead of writing
    py -3.12 tools/v-validate/validate_xmile.py --schema x.xsd  one schema only (repeatable)
    py -3.12 tools/v-validate/validate_xmile.py models/pending  walk a different directory

Every model is validated against each schema in SCHEMAS below that can be found, and the
result file carries one section per schema, so the effect of a schema change is visible
as a diff of the .txt rather than as a number someone has to remember. --schema overrides
the list; --stdout prints instead of writing.

Output is deterministic -- no timestamps -- so the result files can be committed and
diffed: a change in a .txt means the schema verdict really changed.

Exit code is 0 when every model is valid or fails only in expected ways under every
schema, 1 when there is an unexpected error, 2 when a file is not well-formed XML.

Errors Vensim's own exports produce from vendor tags are expected under the v1 schema
and listed in EXPECTED below. Most of them disappear under xmile-v1.x-proposal.xsd,
which is the point of that file: it is xmile-v1.0.xsd plus the vendor-extension
wildcards of section 1a of the TC proposal, and comparing the two sections of a result
file is the evidence for that item.

Schemas are searched for in tools/generate, then proposals/schema, then spec/schema,
then beside this script. Requires lxml (py -3.12 -m pip install lxml).

IMPORTANT: lxml is built on libxml2, which implements XSD 1.0 only, so this script
CANNOT read spec/schema/xmile.xsd.xml -- the v1.1 schema is an XSD 1.1 schema. Use
tools/validate.py for that one. The division is deliberate rather than a limitation to
work around: this script exists to compare XSD 1.0 schemas against each other, which is
what the vendor-extension proposal needed, and tools/validate.py exists to validate
against the schema the specification ships.
"""
import os
import re
import sys
import glob

try:
    from lxml import etree
except ImportError:
    sys.exit('lxml required: py -3.12 -m pip install lxml')

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(HERE))          # tools/v-validate/ -> repo root
MODEL_ROOT = os.path.join(REPO, 'models')
SOURCE_EXTENSIONS = ('*.stmx', '*.xmile', '*.mdlx')

# Where to look for a schema named without a directory, in order.
SCHEMA_DIRS = (
    os.path.join(REPO, 'tools', 'v-generate'),           # the published v1.0 baseline
    os.path.join(REPO, 'proposals', 'schema'),         # schemas a proposal generated
    os.path.join(REPO, 'spec', 'schema'),              # what the specification ships
    HERE,
)

# Schemas to validate against, in report order. Any that cannot be found is skipped
# silently, so a checkout without the proposal schema still works unchanged.
#   xmile-v1.0.xsd           the published OASIS schema -- the verdict that counts
#   xmile-v1.x-proposal.xsd  the same schema plus the section 1a vendor-extension
#                            wildcards; the difference between the two sections of a
#                            result file is what that proposal buys
SCHEMAS = ('xmile-v1.0.xsd', 'xmile-v1.x-proposal.xsd')

COLUMN = 42                     # width of one schema's column in the console summary

# Verdict classes, in report order. A file gets one per schema, except the ones that
# never reach a schema -- unparsable, or of a type no schema covers.
VALID, EXPECTED_ONLY, UNEXPECTED, NO_VERDICT = 'valid', 'expected', 'UNEXPECTED', 'n/a'
STATUSES = (VALID, EXPECTED_ONLY, UNEXPECTED, NO_VERDICT)

# Errors we produce deliberately and do not intend to fix. Each entry is
# (fragment of the lxml message, why it is expected).
EXPECTED = (
    ('vensim.com/XMILE}netflow',
     'vensim:netflow -- a stock whose rate is an expression; XMILE cannot say it'),
    ('vensim.com/XMILE}attach',
     'vensim:attach -- which of a flow\'s two sketch objects an arrow ended on'),
    ("}view', attribute 'name'",
     'view name -- every tool writes it; neither schema nor prose allows it'),
    # <doc> on a control parameter. start/stop are xs:double and dt is a complexType with
    # simpleContent, so libxml2 words the two cases differently -- hence three entries
    # rather than one. Proposal item 4 asks the TC to allow this; we ship what we propose.
    ("}start': Element content is not allowed",
     'doc on <start> -- proposal item 4: control parameters carry comments in Vensim'),
    ("}stop': Element content is not allowed",
     'doc on <stop> -- proposal item 4: control parameters carry comments in Vensim'),
    ("}dt': Element content is not allowed",
     'doc on <dt> -- proposal item 4: control parameters carry comments in Vensim'),
    ('vensim.com/XMILE}saveper',
     'vensim:saveper -- the save interval; <sim_specs> has start/stop/dt/run and no '
     'equivalent, so both the value and any comment on it are otherwise dropped'),
    ('vensim.com/XMILE}output',
     'vensim:output -- a macro output beyond the value it returns, written after the '
     '":" in a Vensim argument list; an XMILE macro returns exactly one value'),
    # Only <macro>'s OWN units are invalid -- the stocks/flows/auxes inside a macro are
    # ordinary variables and may carry <units> already. The fragment cannot see the parent
    # element, so a stray <units> elsewhere would also be excused; the report still prints
    # the path, so check it when this one appears somewhere unexpected.
    ("}units': This element is not expected",
     'units on <macro> -- proposal item 4: a Vensim macro carries units, often expressed '
     'in terms of its parameters, and <macro> has nowhere to put them'),
    # Subscript structure -- proposal item 13. XMILE dimensions are flat and mutually
    # independent; these say what a range IS and what it maps to, and the nesting says
    # what it belongs to.
    ('vensim.com/XMILE}kind',
     'vensim:kind -- on a <dim>, family/subrange/equivalent/copy, since XMILE cannot say '
     'a dimension is related to another at all; on an <aux>, data or string, which are '
     'variables XMILE has no element for but which stay <aux> so that references to them '
     'still resolve'),
    ('vensim.com/XMILE}rc',
     'vensim:rc -- a Reality Check constraint or test input. Not model arithmetic, so it '
     'does not pretend to be a variable; XMILE has no counterpart'),
    ('vensim.com/XMILE}except',
     'vensim:except -- ":EXCEPT: [Boston,Seattle]"; XMILE cannot exclude part of an array '
     'from an equation, and without it the equation and its exceptions collide'),
    ('vensim.com/XMILE}members',
     'vensim:members -- a range declaration as written (a family composed of subranges, a '
     'sequence, a reordering); XMILE has no hierarchical composition of ranges'),
    ('vensim.com/XMILE}map',
     'vensim:map -- an element of one family paired with one of another; XMILE has no '
     'mapping between dimensions'),
    ("}dim': This element is not expected",
     'nested <dim> -- a subrange declared inside its family, so that copying the family '
     'carries everything derived from it'),
)

# Extensions with no schema to validate against.
NO_SCHEMA = {'.mdlx': 'no schema exists for .mdlx yet; checked for well-formedness only'}

VARIABLE_TAGS = ('stock', 'flow', 'aux', 'gf', 'module', 'group', 'macro')

# lxml reports fully-qualified names, which makes a message three times longer than the
# fact it conveys. Abbreviate the namespaces we know for readability. Classification
# happens on the raw message first, so this never affects which errors are expected.
NS_ABBREV = (
    ('{http://docs.oasis-open.org/xmile/ns/XMILE/v1.0}', '{xmile}'),
    ('{http://www.systemdynamics.org/XMILE}', '{sdorg}'),
    ('{http://iseesystems.com/XMILE}', '{isee}'),
    ('{http://www.vensim.com/XMILE}', '{vensim}'),
)


def abbreviate(message):
    for uri, short in NS_ABBREV:
        message = message.replace(uri, short)
    return message


def localname(tag):
    return tag.rsplit('}', 1)[-1] if isinstance(tag, str) else str(tag)


def display_name(tag):
    """Local name, prefixed when the element is not in the XMILE namespace -- so that
    'isee:prefs' is not silently reported as plain 'prefs'."""
    if not isinstance(tag, str) or not tag.startswith('{'):
        return localname(tag)
    uri = tag[:tag.index('}') + 1]
    if uri == NS_ABBREV[0][0]:                       # the XMILE default namespace
        return localname(tag)
    for known, short in NS_ABBREV[1:]:
        if uri == known:
            return '%s:%s' % (short.strip('{}'), localname(tag))
    return '{%s}%s' % (uri.strip('{}'), localname(tag))


def element_path(element):
    """Ancestor chain of an element, e.g. 'xmile > header > smile'."""
    parts = []
    while element is not None:
        if isinstance(element.tag, str):
            parts.append(display_name(element.tag))
        element = element.getparent()
    return ' > '.join(reversed(parts))


def index_by_line(doc):
    """Map source line number -> elements starting on it."""
    index = {}
    for element in doc.iter():
        if isinstance(element.tag, str) and element.sourceline:
            index.setdefault(element.sourceline, []).append(element)
    return index


def blamed_element(message, candidates):
    """Pick which element on a line the message is about.

    lxml names the offending element in the message, so prefer the candidate whose local
    name matches. Several elements can start on one line (Stella writes long lines), and
    without this the parent path would often describe the wrong one.
    """
    named = re.search(r"Element '([^']+)'", message)
    if named:
        want = localname(named.group(1))
        for element in candidates:
            if localname(element.tag) == want:
                return element
    return candidates[0] if candidates else None


def start_tag(element, limit=220):
    """Reconstruct an element's start tag from the parsed tree.

    Deliberately rebuilt rather than quoted from the file: libxml2's line numbers run
    behind the real line whenever the file contains lone CR bytes (XML 1.0 s2.11 folds
    them into the content), so indexing the source text by the reported line can quote a
    completely unrelated tag. The parsed element cannot drift.
    """
    parts = [display_name(element.tag)]
    for name, value in element.attrib.items():
        parts.append('%s="%s"' % (display_name(name), value))
    empty = len(element) == 0 and not (element.text or '').strip()
    text = '<%s%s>' % (' '.join(parts), '/' if empty else '')
    if len(text) > limit:
        text = text[:limit - 5] + ' ...>'
    return text


def format_error(line, message, index):
    """Render one validation error with the offending element and its ancestry."""
    out = []
    element = blamed_element(message, index.get(line, []))

    where = 'line %s' % line
    if element is not None:
        where += '  in  %s' % element_path(element)
    out.append('    %s' % where)

    if element is not None:
        out.append('        %s' % start_tag(element))
        parent = element.getparent()
        if parent is not None:
            out.append('        parent: %s' % start_tag(parent, limit=140))

    out.append('        %s' % abbreviate(message))
    return out


def find_schema(name):
    """Locate one schema by name in SCHEMA_DIRS, or take a path as given."""
    if os.path.isabs(name) or os.path.dirname(name):
        return name if os.path.exists(name) else None
    for directory in SCHEMA_DIRS:
        path = os.path.join(directory, name)
        if os.path.exists(path):
            return path
    return None


def load_schemas(names, required):
    """Compile the schemas that can be found. Returns [(path, XMLSchema), ...].

    A name given on the command line must exist -- a typo there is a mistake, not a
    checkout without the file -- while a missing entry in SCHEMAS is simply skipped.
    """
    loaded = []
    for name in names:
        path = find_schema(name)
        if path is None:
            if required:
                sys.exit('schema not found: %s' % name)
            continue
        try:
            loaded.append((path, etree.XMLSchema(etree.parse(path))))
        except etree.XMLSchemaParseError as exc:
            sys.exit('schema will not compile: %s\n    %s' % (path, exc))
    if not loaded:
        sys.exit('none of %s found beside this script or in its parent directory'
                 % ', '.join(names))
    return loaded


def count_lone_cr(path):
    """Lone CR bytes, which make libxml2's line numbers run behind the real file."""
    try:
        with open(path, 'rb') as handle:
            data = handle.read()
    except OSError:
        return 0
    return len(re.findall(b'\r(?!\n)', data))


def classify(message):
    """Return the reason this error is expected, or None if it is not."""
    for fragment, reason in EXPECTED:
        if fragment in message:
            return reason
    return None


def describe_contents(doc):
    """One line per model, saying what the file actually contains.

    Counts are labelled with the bare tag name, unpluralised -- these are element names,
    not English nouns, and "5 auxs" reads worse than "5 aux".
    """
    counts = []
    for tag in VARIABLE_TAGS + ('view',):
        n = len(doc.findall('.//{*}' + tag))
        if n:
            counts.append('%d %s' % (n, tag))
    return ', '.join(counts) or '(nothing recognised)'


def verdict_section(doc, path, schema, schema_path, with_note):
    """One schema's verdict on an already-parsed document.

    Returns (lines, exit code, summary, error count, status). `with_note` carries the
    lone-CR
    warning, which is a property of the file rather than of the schema and so is printed
    only once however many schemas are in play.
    """
    lines = ['schema:   %s' % os.path.basename(schema_path)]

    if schema.validate(doc):
        lines.append('result:   VALID')
        return lines, 0, 'VALID', 0, VALID

    errors = [(e.line, e.message, classify(e.message)) for e in schema.error_log]
    unexpected = [e for e in errors if e[2] is None]
    expected = [e for e in errors if e[2] is not None]

    summary = '%d error(s)' % len(errors)
    if expected:
        summary += ', %d expected' % len(expected)
    if unexpected:
        summary += ', %d UNEXPECTED' % len(unexpected)
    elif expected:
        summary += ' -- all expected'
    lines.append('result:   %s' % summary)

    index = index_by_line(doc)

    lone_cr = count_lone_cr(path) if with_note else 0
    if lone_cr:
        lines.append('note:     %d lone CR byte(s) in this file; libxml2 counts them as '
                     'content, so the line numbers below run up to %d lines behind an '
                     'editor. The quoted tags are rebuilt from the parse tree and are '
                     'correct regardless.' % (lone_cr, lone_cr))

    if unexpected:
        lines.append('')
        lines.append('unexpected:')
        for line, message, _ in unexpected:
            lines += format_error(line, message, index)
    if expected:
        lines.append('')
        lines.append('expected (deliberate Vensim extensions):')
        seen = set()
        for line, message, reason in expected:
            if reason not in seen:
                lines.append('    -- %s' % reason)
                seen.add(reason)
            lines += format_error(line, message, index)

    return (lines, 1 if unexpected else 0, summary, len(errors),
            UNEXPECTED if unexpected else EXPECTED_ONLY)


def report(path, schemas):
    """Validate one file against every schema.

    Returns (report lines, worst exit code,
    [(schema name, summary, error count, status), ...]).
    With a single schema the output is identical to what this script produced before it
    learned about more than one, so committed result files do not churn.
    """
    name = os.path.basename(path)
    extension = os.path.splitext(name)[1].lower()
    lines = ['source:   %s' % name]

    try:
        doc = etree.parse(path)
    except etree.XMLSyntaxError as exc:
        lines += ['result:   NOT WELL-FORMED', '', '    %s' % exc]
        return lines, 2, [('--', 'NOT WELL-FORMED', 0, NO_VERDICT)]
    except OSError as exc:
        lines += ['result:   UNREADABLE', '', '    %s' % exc]
        return lines, 2, [('--', 'UNREADABLE', 0, NO_VERDICT)]

    root = doc.getroot()
    lines.append('root:     %s' % root.tag)
    lines.append('contents: %s' % describe_contents(doc))

    skip = NO_SCHEMA.get(extension)
    if skip:
        lines += ['schema:   -- none --', 'result:   WELL-FORMED (%s)' % skip]
        return lines, 0, [('--', 'WELL-FORMED', 0, NO_VERDICT)]

    worst, verdicts = 0, []
    for n, (schema_path, schema) in enumerate(schemas):
        if n:
            lines.append('')
        section, code, summary, count, status = verdict_section(
            doc, path, schema, schema_path, with_note=(n == 0))
        lines += section
        worst = max(worst, code)
        verdicts.append((os.path.basename(schema_path), summary, count, status))

    return lines, worst, verdicts


def group_by_folder(paths, root):
    """[(folder, [path, ...]), ...] in folder order, files sorted within a folder.

    The folder is the path relative to the walk root, which in /models is the whole
    point: it records which version of XMILE the models in it are expected to conform
    to. A model sitting directly in the root is reported under "./".
    """
    groups = {}
    for path in paths:
        folder = os.path.dirname(os.path.relpath(path, root)).replace(os.sep, '/')
        groups.setdefault(folder + '/' if folder else './', []).append(path)
    return [(folder, sorted(groups[folder], key=lambda p: os.path.basename(p).lower()))
            for folder in sorted(groups)]


def main(argv):
    to_stdout = '--stdout' in argv

    wanted = [argv[i + 1] for i, a in enumerate(argv)
              if a == '--schema' and i + 1 < len(argv)]
    consumed = set(wanted)

    # An optional directory argument, so a subfolder can be validated on its own.
    given = [a for a in argv if not a.startswith('--') and a not in consumed]
    root = given[0] if given else MODEL_ROOT
    if not os.path.isdir(root):
        sys.exit('not a directory: %s' % root)

    # Subfolders are the point of /models -- they record which version of XMILE a
    # model is expected to validate under -- so the walk is recursive.
    paths = []
    for pattern in SOURCE_EXTENSIONS:
        paths.extend(glob.glob(os.path.join(root, '**', pattern), recursive=True))
    paths.sort(key=lambda p: os.path.relpath(p, root).lower())

    if not paths:
        sys.exit('no .stmx / .xmile / .mdlx files under %s' % root)

    schemas = load_schemas(wanted or SCHEMAS, required=bool(wanted))

    schema_names = [os.path.basename(sp) for sp, _ in schemas]

    errors_by = {}          # folder -> schema -> error count
    status_by = {}          # folder -> schema -> {status: n}

    worst = 0
    for folder, group in group_by_folder(paths, root):
        print()
        print('%s  (%d file(s))' % (folder, len(group)))
        errors_by[folder] = dict.fromkeys(schema_names, 0)
        status_by[folder] = {n: dict.fromkeys(STATUSES, 0) for n in schema_names}

        for path in group:
            lines, code, verdicts = report(path, schemas)
            worst = max(worst, code)

            text = '\n'.join(lines) + '\n'
            if to_stdout:
                print(text)
            else:
                with open(path + '.txt', 'w', encoding='utf-8', newline='\n') as handle:
                    handle.write(text)

            # One line per model, one column per schema, padded so the columns line up
            # down the whole run rather than only within a group.
            print(('  %-38s %s'
                   % (os.path.basename(path),
                      ' | '.join(s.ljust(COLUMN) for _, s, _, _ in verdicts))).rstrip())

            for schema_name, _, count, status in verdicts:
                if schema_name == '--':
                    # Never reached a schema -- unparsable, or a type no schema covers.
                    # Charge it to every column so it is not silently absent.
                    for name in schema_names:
                        status_by[folder][name][status] += 1
                    continue
                errors_by[folder][schema_name] += count
                status_by[folder][schema_name][status] += 1

        print(('  %-38s %s'
               % ('-- subtotal',
                  ' | '.join(('%d error(s)' % errors_by[folder][n]).ljust(COLUMN)
                             for n in schema_names))).rstrip())

    folders = list(errors_by)
    width = max([len(f) for f in folders] + [12])
    column = max([len(n) for n in schema_names] + [10])

    print()
    print('errors by folder and schema')
    print('  %-*s  %s' % (width, '', '  '.join(n.rjust(column) for n in schema_names)))
    for folder in folders:
        print('  %-*s  %s' % (width, folder,
                              '  '.join(('%d' % errors_by[folder][n]).rjust(column)
                                        for n in schema_names)))
    print('  %-*s  %s' % (width, 'all',
                          '  '.join(('%d' % sum(errors_by[f][n] for f in folders)).rjust(column)
                                    for n in schema_names)))

    print()
    print('verdicts by folder and schema')
    print('  %-*s  %-*s  %s' % (width, '', column, 'schema',
                                ' '.join(s.rjust(11) for s in STATUSES)))
    for folder in folders:
        for name in schema_names:
            counts = status_by[folder][name]
            print('  %-*s  %-*s  %s'
                  % (width, folder, column, name,
                     ' '.join(('%d' % counts[s]).rjust(11) for s in STATUSES)))

    return worst


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
