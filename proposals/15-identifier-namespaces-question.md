# Identifier namespaces - a question rather than a proposal

Is the identifier-namespace mechanism of 3.2.2.3 **implemented by anyone**? If a file
declares `<options namespace="vensim, std"/>`, do other tools actually resolve
unrecognised identifiers against the `vensim` namespace, or is the mechanism currently
a dead letter?

This matters to us directly. We would rather not translate Vensim's function names into
the isee spellings on export — `SMOOTH3` is a more readable name than `SMTH3`, and
`IF THEN ELSE(a,b,c)` is no less precise than `IF a THEN b ELSE c` — and the namespace
mechanism appears to be the standard's own answer to exactly that. But it is only an
answer if readers implement it. If they do not, the TC may want to consider accepting
common vendor spellings as aliases in `std`, which would cost implementers little and
would remove the main reason for exporters to mangle their own models on the way out.
