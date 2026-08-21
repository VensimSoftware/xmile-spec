*Status against XMILE v1.1 (SDS Candidate Standard 02, 20 August 2024)
as reviewed 2026-07-30:* **New in this draft.** No way to declare an output beyond the one `<eqn>` names; `access="output"` marks the result, not extras (one per macro in all four real macros we have). Also flags an ambiguity in §4.8's `<eqn>`.

*Re-checked 2026-08-20 against the schema added to `xmile-spec` on 2026-08-18:*
**Stands, untouched.**

---
# A macro can only return one value

`<macro>` has no way to say that a macro produces anything besides its result. Vensim
declares extra outputs after an optional `:` in the argument list:

```
:MACRO: SMTH DECR(input,tau : RATE)
SMTH DECR = INTEG( RATE , input)
RATE = MIN(0,(input-SMTH DECR)/tau)
:END OF MACRO:
```

and a caller binds a name to each: `perceived temperature = SMTH DECR(teacup temperature,
perception time : rate of change)` makes `rate of change` an ordinary variable of the
model. The macro computes the smoothed value *and* the rate that produced it; without the
second output a modeller who wants both must compute the rate again outside the macro —
duplicating the logic that defines it — or give up the macro.

This is not a Vensim curiosity. Any macro that computes several quantities from one piece
of internal structure has the same shape: a delay that also reports its outflow, a
smoothing that also reports its gap, an allocation that reports both the amount allocated
and the shortfall. The single-return restriction pushes that structure back out into the
model, which is what a macro exists to avoid.

**What we could not use.** `access="output"` looked like the answer, and it is a standard
attribute on the variables inside a macro. But in all four real macros we have — two in
`COVID-19-Model-By-Age.stmx`, two in `FRIDA.stmx` — there is exactly **one**
`access="output"` per macro, and it always names the same variable as `<eqn>`. So the
attribute marks *the* result rather than an additional one, and with several so marked a
reader could not tell which value the macro returns.

**Proposal.** Allow a macro to export more than one variable, and say how a caller binds
them. Either:

1. Keep `<eqn>` as the single return value and add an explicit list of additional
   outputs — what we ship today as `<vensim:output>`; or
2. Declare `access="output"` on more than one variable legal, with `<eqn>` naming
   whichever is returned — which needs no new element, only a sentence saying that "is an
   output" and "is the result" are different questions.

We prefer (2), since it uses what is already there. Either way the *call* syntax needs a
form for binding the extras, and that is the part the standard cannot borrow from us.

**A smaller editorial point in the same section.** §4.8 says `<eqn>` holds a "valid XMILE
expression", and §4.8.1's own example is `LN(x)/LN(base)` — a full expression. Yet every
macro-with-variables we have seen writes `<eqn>` as a bare reference to one of its
variables (`<eqn>out</eqn>`, `<eqn>trend in input</eqn>`). Both readings are permitted by
the text and they produce visibly different files. We now follow the reference form
wherever a macro returns a stock, because it puts readable structure in `<variables>`
instead of an opaque expression — but we had to infer that from other vendors' files
rather than from the specification. A sentence saying `<eqn>` may be any expression, and
that naming a variable is the usual form when `<variables>` is present, would settle it.
