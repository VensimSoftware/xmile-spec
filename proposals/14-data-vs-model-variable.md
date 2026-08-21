*Status against XMILE v1.1 (SDS Candidate Standard 02, 20 August 2024)
as reviewed 2026-07-30:* **New in this draft.** XMILE `<data>` is import/export plumbing for a run; a Vensim data variable is a model variable with its own interpolation semantics (`:INTERPOLATE:`, `:RAW:`, `:HOLD BACKWARD:`, `:LOOK FORWARD:`). Neither is derivable from the other, and a data variable has nowhere to go.

*Re-checked 2026-08-20 against the schema added to `xmile-spec` on 2026-08-18:*
**Stands, untouched.**

---
# `<data>` describes a session, not a model

XMILE's `<data>` element holds `<export>` — write everything, or a named table, at an
interval — and `<import>` — a source, at an interval. It describes **what a run should read
and write**: session plumbing, settled once for the file.

Vensim's data is a property of a **variable**. A data variable is an ordinary member of the
model whose values come from a dataset rather than from an equation; it appears in other
equations exactly as any variable does, and it carries its own interpolation semantics —
`:INTERPOLATE:`, `:RAW:`, `:HOLD BACKWARD:`, `:LOOK FORWARD:` — because how you read
*between* two observations is a modelling decision, not a file-format one. Two data
variables in the same model routinely differ in it.

These are not the same concept at different levels of detail; they answer different
questions. "Which file do I read?" has no bearing on "what value does this variable take
between January and February?", and neither can be derived from the other. So a Vensim data
variable has nowhere to go: `<data>` is not a home for it, and the variable types
(`<stock>`, `<flow>`, `<aux>`) do not admit one either. Ours currently exports as
`<vensim:data>` in the variables section, for want of anywhere better.

We raise it as a second instance of the pattern in item 13's closing suggestion rather than
as a request for a `<data_variable>` element. The array chapter and this one have the same
shape: the standard has adopted one product's model of an area where products genuinely
differ, and has done so in the core rather than at the edge. Interpolation between
observations, in particular, is somewhere we would expect several defensible answers and no
common ground to legislate.

**What we would suggest.** Treat run-time I/O and data-valued variables as separate
questions; keep whichever has real agreement across products in the core; and let the rest
live in vendor namespaces until practice converges — which is the same profiling argument
made in item 13, and applies at least as well here.


---
