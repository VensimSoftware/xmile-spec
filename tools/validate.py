"""Validate XMILE documents against the schema.

Why this is Python when the rest of the tooling is Node: the schema is an XSD
1.1 schema. It has to be. Section 2 says XMILE makes "provision for vendor
specific additions", and expressing that needs xs:defaultOpenContent and
schema-level defaultAttributes, neither of which exists in XSD 1.0 -- and the
<header> and <style> content models are xs:all groups, which in XSD 1.0 cannot
contain a wildcard at all. No Node implementation of XSD 1.1 exists; the
xmlschema package is the smallest dependency that does the job.

Consequences worth knowing before reaching for another validator: xmllint and
the .NET XmlSchemaSet implement XSD 1.0 only and will reject this schema rather
than skip it, even though vc:minVersion="1.1" asks them to skip. Xerces-J and
Saxon-EE will read it.

Run with no documents to compile the schema and stop, which is what CI does:
that alone catches a schema that has been broken by an edit.

Usage:
  python tools/validate.py                        compile the schema only
  python tools/validate.py model.stmx [more...]   also validate documents
  python tools/validate.py --schema other.xsd f   validate against another schema
  python tools/validate.py --max-errors 5 f       cap the report per document

--schema MAY be repeated. Every schema given is run over the whole document list
and the error totals are printed side by side at the end. That is how to answer
"what is a proposed schema change worth?" -- put the current schema and the
proposed one on the same command line and compare the totals over real models,
rather than reading a diff and guessing.
"""
import argparse
import glob
import sys
from pathlib import Path

DEFAULT_SCHEMA = Path('spec/schema/xmile.xsd.xml')


def fail(message, hint=None):
    print('validate FAILED: %s' % message, file=sys.stderr)
    if hint:
        print(hint, file=sys.stderr)
    return 2


def main(argv=None):
    parser = argparse.ArgumentParser(
        prog='validate.py',
        description='Validate XMILE documents against the XMILE schema (XSD 1.1).',
    )
    parser.add_argument('documents', nargs='*',
                        help='XMILE files to validate. Globs are expanded here, '
                             'so they work the same on every shell.')
    parser.add_argument('--schema', action='append', type=Path, metavar='XSD',
                        help='schema to validate against; may be repeated, in which '
                             'case the totals are compared (default: %s)' % DEFAULT_SCHEMA)
    parser.add_argument('--max-errors', type=int, default=25, metavar='N',
                        help='most errors to print per document, 0 for all (default: 25)')
    args = parser.parse_args(argv)

    try:
        import xmlschema
    except ImportError:
        return fail(
            'the xmlschema package is not installed.',
            'Install it with:  python -m pip install -r tools/requirements.txt',
        )

    schemas = args.schema or [DEFAULT_SCHEMA]

    compiled = []
    for path in schemas:
        if not path.exists():
            return fail('schema not found: %s' % path)
        try:
            schema = xmlschema.XMLSchema11(str(path))
        except Exception as exc:                              # noqa: BLE001
            return fail('%s did not compile as XSD 1.1.' % path,
                        '\n%s: %s' % (type(exc).__name__, exc))
        compiled.append((path, schema))
        print('schema OK: %s compiles as XSD 1.1 (%d global element(s), %d type(s)).'
              % (path, len(schema.elements), len(schema.types)))

    paths = []
    for pattern in args.documents:
        matches = sorted(glob.glob(pattern, recursive=True))
        if not matches:
            # A literal path that does not exist is an error, not an empty glob.
            if any(ch in pattern for ch in '*?['):
                print('note: %s matched no files' % pattern)
            else:
                return fail('document not found: %s' % pattern)
        paths.extend(matches)

    if not paths:
        return 0

    totals = []
    for n, (path, schema) in enumerate(compiled):
        # With one schema this prints exactly what it always printed. With more,
        # the comparison is the point, so each block is labelled.
        if len(compiled) > 1:
            print('%s=== %s ===' % ('\n' if n else '\n', path))
        total = sweep(paths, schema, args.max_errors)
        totals.append((path, total))

    if len(compiled) > 1:
        width = max(len(str(p)) for p, _ in totals)
        print('\ntotal errors over %d document(s):' % len(paths))
        for path, total in totals:
            print('    %-*s  %d' % (width, path, total))
        best = min(t for _, t in totals)
        if best < totals[0][1]:
            print('    (%s is %d fewer than %s)'
                  % (min(totals, key=lambda r: r[1])[0], totals[0][1] - best, totals[0][0]))

    if totals[0][1]:
        print('\nvalidate FAILED: %d error(s) across %d document(s).'
              % (totals[0][1], len(paths)), file=sys.stderr)
        return 1

    print('\nvalidate OK: %d document(s) valid.' % len(paths))
    return 0


def sweep(paths, schema, max_errors):
    """Validate every path against one schema; returns the error total."""
    total = 0
    for path in paths:
        try:
            errors = list(schema.iter_errors(path))
        except Exception as exc:                              # noqa: BLE001
            print('%s: not well-formed XML -- %s' % (path, exc))
            total += 1
            continue

        if not errors:
            print('%s: valid' % path)
            continue

        total += len(errors)
        print('%s: %d error(s)' % (path, len(errors)))
        shown = errors if max_errors == 0 else errors[:max_errors]
        for error in shown:
            where = getattr(error, 'path', None) or '(document)'
            reason = ' '.join(str(error.reason or '').split())
            print('  %s: %s' % (where, reason))
        if len(errors) > len(shown):
            print('  ... %d more; rerun with --max-errors 0 to see them all'
                  % (len(errors) - len(shown)))
    return total


if __name__ == '__main__':
    sys.exit(main())
