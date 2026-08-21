*Status against XMILE v1.1 (SDS Candidate Standard 02, 20 August 2024)
as reviewed 2026-07-30:* **Stands.** "netflow" appears nowhere; a stock still changes only through named flows.
A vendor <vensim:netflow> element would be newly valid.

*Re-checked 2026-08-20 against the schema added to `xmile-spec` on 2026-08-18:*
**Stands, untouched.** "netflow" appears nowhere in the 1.1 text or in the new schema.
The vendor-extension mechanism (item 1) does now let us ship `vensim:netflow` in a valid
file, which removes the urgency but not the case: a stock whose derivative is an
expression is still inexpressible in standard XMILE, so the information is lost on any
round trip through another tool.

---
# `<netflow>`: stocks whose derivative is an expression

### The problem

XMILE section 3.1.1 states that "the value of a stock is increased by its inflows and
decreased by its outflows", and a stock's own `<eqn>` gives only its initial value.
There is consequently no way to express a stock whose derivative is simply an
expression:

```
Smoothed Signal = INTEG( (input - Smoothed Signal) / tau, 0 )
```

This form is ordinary in Vensim and was ordinary in DYNAMO. It is not expressible in
XMILE at all.

An exporter has three options today, and all three are bad:

1. **Invent a flow.** Synthesise a `<flow>` carrying the expression and reference it as
   the stock's only `<inflow>`. This requires inventing a *name* the modeller never
   wrote. That name then appears in the receiving tool's variable list, in its
   diagrams, in any sensitivity or loop analysis run on the model, and in any file
   subsequently exported from it. The round trip never recovers the original form.
2. **Emit the stock with no flows.** Valid against the schema, and silently wrong: the
   stock simply never changes. (Our own exporter did this by accident until recently —
   11 of World3's 15 stocks exported as inert. Nothing in the schema or the spec
   flagged it.)
3. **Refuse to export the model.**

### Why this belongs in the standard

The mathematics of a stock is `dx/dt = f(...)`. Named inflows and outflows are a
*presentation* of `f` — a good one, and the right default for teaching and for
diagrams — but they are a presentation, not the semantics. Requiring the decomposition
in the interchange format has three consequences we think the TC did not intend:

- **It embeds one vendor's modelling convention in a vendor-neutral standard.** Stella
  requires the decomposition; DYNAMO did not, and Vensim does not.
- **It is inconsistent within XMILE itself.** An `<aux>` may hold an arbitrary
  expression, and a `<macro>` body is unconstrained. Stocks alone are required to route
  their arithmetic through named intermediates.
- **It puts a diagram concern in the wrong layer.** XMILE already has a view layer,
  which is exactly where "this model draws its rates as valves on pipes" belongs. The
  variables section should be free to carry the mathematics.

### Proposed change

Add an optional `<netflow>` element to the stock content model, as an alternative to
`<inflow>`/`<outflow>`:

```xml
<stock name="Smoothed_Signal">
    <eqn>0</eqn>
    <netflow>(input - Smoothed_Signal) / tau</netflow>
</stock>
```

Semantics: the stock's derivative is the value of the `<netflow>` expression, i.e.
`stock(t) = stock(t-dt) + dt · netflow(t-dt)`, which is the existing stock semantics
with `netflow` in place of `inflows − outflows`.

Constraints we suggest:

- `<netflow>` and `<inflow>`/`<outflow>` are **mutually exclusive** on a given stock.
  (Allowing both raises a needless question about whether they sum.)
- At most one `<netflow>` per stock.
- Conveyors, queues and ovens keep their existing rules; `<netflow>` applies to plain
  stocks only.

Schema change, in the `stock` content model:

```xml
<xs:element name="netflow" type="xs:string" minOccurs="0" maxOccurs="1" />
```

**This asks for no new mechanism, only the one the standard already uses for a feature of
this kind.** §4.2 and §4.3 say of `<non_negative>` that it "is not directly supported by
XMILE" and exists "partly for documentation, partly to allow a vendor to invoke a macro to
implement the functionality", with §3.6.2 and §4.8.4 supplying the built-in macros and
option filters that do the work. `<netflow>` fits that shape exactly: a reader that
implements it integrates the expression, and a reader that does not wraps it in a macro —
the same macro the workarounds subsection below arrives at independently. The parallel is
imperfect in one respect, and it bears on how the fallback has to be worded. Ignoring
either tag changes the numbers, and neither failure announces itself: a model that has lost
its non-negativity constraint runs on and violates the bound, and a model that has lost its
`<netflow>` runs on with a constant stock. The second is the more dangerous, because the
dynamics are gone rather than merely unbounded — and we have measured that on ourselves,
in the 11 of World3's 15 stocks our own exporter shipped as inert with nothing in the
schema or the spec flagging it. So for `<netflow>` the fallback has to be implemented
rather than merely permitted.

### Backward compatibility

Total. No existing file contains `<netflow>`, so no existing file changes meaning, and
any file not using it validates exactly as before. A reader that does not implement it
has two choices — decompose it into a synthetic flow on read (the same
workaround as today, but now *its* choice rather than something forced on every
exporter), or report that the model uses a feature it does not support. Both are
visible failures. The status quo produces a silent one.

### Workarounds considered

Before asking for a new element we looked for a way to say this in XMILE as it stands.
There is one that works. Its limits make the case for `<netflow>`.

**A macro.** Define `NETFLOW INTEG(expression, initval)` whose body is
`INTEG(expression, initval)`, and write the stock as an ordinary variable holding a call
to it. This is legal XMILE — `<macro>` bodies carry their own `<variables>`, stocks
included, and Stella writes such macros itself: two of the real isee-produced files in our
corpus contain them.

It survives the obvious objection. The motivating expression references the stock it
belongs to, as do 4 of the 9 `<vensim:netflow>` expressions in our own exports, so a macro
argument looks circular. It is not: the macro expands to a stock, and the stock breaks the
loop exactly as `INTEG` does. We built the case —
`minimal/netflow.mdl`, three formulations of one first-order smooth — and the compiled
model shows it directly:

```c
/* #netflow macro smooth>NETFLOW INTEG# */
VGV->RATE[1] = ((VGV->LEVEL[8]-VGV->LEVEL[6])/VGV->LEVEL[10]);   /* (signal - smooth)/tau */
...
VGV->LEVEL[6] = VGV->LEVEL[1];                                   /* the variable aliases the stock */
```

`LEVEL[1]` is the macro's stock; `LEVEL[6]` is the model-level variable; the rate reads
the latter, whose value is known at the start of the step. `SMOOTH fn` compiles to the
same shape. The macro form, the plain `INTEG` form and the built-in `SMOOTH` agree to six
decimals at all 101 saved points.

It is also better than inventing a flow, on the axis this item cares about: the
model keeps **one** variable with the modeller's own name, and no invented name enters the
receiving tool's variable list, diagrams or analyses. The internal stock is the macro's
business.

Two costs remain, and they are why we still ask for `<netflow>`:

- **The variable is no longer a stock.** It presents to the receiving tool as an ordinary
  variable holding a function call. It will not be drawn as a level, will not be treated
  as one by any structural analysis, and will not export as one. For a stock-and-flow tool
  that is a real loss, and it is precisely the loss `<netflow>` avoids.
- **Macros are not universally supported.** PySD — the third major implementation in this
  ecosystem — does not implement them, so a file using this workaround would not run
  there, where the same model written with a synthesised flow would.

**A marker attribute.** If the goal is narrowed to round-tripping rather than fidelity,
the cheapest mechanism is a synthesised flow carrying a vendor attribute:

```xml
<flow name="Smoothed_Signal_net" vensim:synthetic="netflow">
  <eqn>(input - Smoothed_Signal) / tau</eqn>
</flow>
```

Every tool runs it, PySD included, because the structure is plain XMILE; the writer can
collapse it back to `INTEG` on re-import; and a tool that strips the attribute loses only
the round trip, not the model. It does not solve the problem — the invented name is still
there, which is the harm — but as a *workaround* it dominates both the bare synthetic flow
and the macro.

None of the three works, and the least-bad one requires turning a stock into something
that is not a stock. A format that can express `dx/dt = f(...)` only by concealing the
stock inside a macro is missing an element, not a convention.

### What we have shipped in the meantime

Vensim writes this as `<vensim:netflow>` in our own namespace, which makes the file
schema-invalid — see item 1, which is the reason we had no better option. We would
retire the prefixed form immediately if `<netflow>` is standardised.

---
