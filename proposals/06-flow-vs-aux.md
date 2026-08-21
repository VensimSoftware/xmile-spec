*Status against XMILE v1.1 (SDS Candidate Standard 02, 20 August 2024)
as reviewed 2026-07-30:* **Half answered.** `flow_concept` on an `<aux>` is now documented as the way to say "this auxiliary is conceptually a flow". There is still no rule about what `<inflow>`/`<outflow>` may reference.

*Re-checked 2026-08-20 against the schema added to `xmile-spec` on 2026-08-18:*
**Stands, half answered as before.** `flow_concept` on an `<aux>` remains the only part
that was addressed. Nothing in the 1.1 schema constrains what `<inflow>`/`<outflow>` may
reference.

---
# When must a rate be a `<flow>` rather than an `<aux>`?

The standard does not say, and the answer has consequences.

In Vensim there is no separate flow type: a rate is an auxiliary that a stock happens to
accumulate. Exporting to XMILE therefore forces a decision about which auxiliaries to
call flows, and we could find no rule to follow. The spec is silent on whether a variable
named in a stock's `<inflow>`/`<outflow>` must, or should, be declared as `<flow>` — and
it does not restrict what those elements may reference, so naming an `<aux>` is
apparently conforming.

Two consequences:

- **The same model can be written two ways, and a reader cannot tell rates from other
  variables by element type.** It has to parse every stock's flow lists and work back.
  That is a small burden, but it is the kind of thing a standard exists to remove.
- **The choice is not merely presentational.** Comparing the two content models in the
  schema, `<flow>` may carry `<non_negative>`, `<leak>`, `<leak_integers>`,
  `<overflow>` and `<multiplier>`, plus `leak_start`/`leak_end`; `<aux>` may carry none
  of them. A uniflow or a conveyor's leakage simply cannot be expressed on an `<aux>`.
  In the view layer the difference is larger still: a flow is a pipe with a valve and
  carries `<pts>`, an aux is a circle.

There is a hint that the ambiguity was noticed: the schema gives `<aux>` an attribute
**`flow_concept`** which appears nowhere in the specification text. Whatever it was
intended to mean — presumably "this auxiliary is conceptually a rate" — an attribute that
exists only in the schema cannot be relied on or implemented against.

**Proposed change.** State the rule. Our suggestion, which is what we have implemented:
a variable that any stock names in `<inflow>` or `<outflow>` SHOULD be declared as
`<flow>`; a reader encountering an `<aux>` there MUST treat it as a flow regardless.
And either document `flow_concept` or remove it.
