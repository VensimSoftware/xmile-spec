*Status against XMILE v1.1 (SDS Candidate Standard 02, 20 August 2024)
as reviewed 2026-07-30:* **Stands, and sharper.** 1.1 *added* `<doc>` to `<graph>` and `<table>`, but `<model>`, `<module>`, `<sim_specs>` and `<dimensions>` still cannot be documented. The item now also covers the missing save interval, an adjacent gap in the same element.

*Re-checked 2026-08-20 against the schema added to `xmile-spec` on 2026-08-18:*
**Stands, and now measurable.** Nothing was added. Running the new schema over our
corpus turns the gap into error counts: `<doc>` inside `<module>` is rejected, as are
`<format>` inside `<module>` (175 occurrences) and `url` on `<module>` (15). `<sim_specs>`
still has no `<doc>`.

---
# Documentation has nowhere to go in `<sim_specs>`

A model's control parameters are documented objects in Vensim — `INITIAL TIME`,
`FINAL TIME`, `TIME STEP` and `SAVEPER` are ordinary variables carrying units and
comments, and modellers do write on them ("timestep chosen for the delay in sector 3",
"horizon matches the policy study"). In XMILE they become bare values:

```xml
<sim_specs method="rk4" time_units="Month">
    <start>0</start><stop>75</stop><dt>0.25</dt>
</sim_specs>
```

There is no `<doc>` element anywhere in `<sim_specs>` — we checked the schema, the
content model is an `xs:all` of `stop`, `start` and `dt`, with `method`, `time_units`
and `pause` as attributes and nothing else. So any note attached to a control parameter
is dropped on the way through XMILE, silently. Our own round-trip test loses exactly
this: the source model's `INITIAL TIME` carries "Assumed with FINAL_TIME = LENGTH", and
after export and re-import it carries nothing.

This is part of a wider inconsistency. Taking the schema element by element, `<doc>` is
allowed on:

| Can be documented | Cannot be documented |
|---|---|
| `<stock>`, `<flow>`, `<aux>` | `<model>` |
| `<group>` (sector frames) | `<module>` |
| `<macro>` | `<sim_specs>` |
| | `<header>` (has `<caption>`, but no `<doc>`) |
| | `<dimensions>` |

So a modeller can annotate a variable, a sector and a macro, but not the model itself,
not a submodel, not a dimension, and not the run settings. The three that cannot are
exactly the ones that carry a model's *architecture* — the places where an explanation
is worth most, because the reader cannot infer the intent from an equation.

`<module>` is the sharpest of these: modules are how XMILE expresses hierarchy, and a
submodel is precisely the kind of thing whose purpose and interface need describing.

**Proposed change.** Allow `<doc>` as an optional child of `<sim_specs>`, `<model>`,
`<module>` and `<dimensions>`, and — for `<sim_specs>` — on `<start>`, `<stop>` and
`<dt>` individually, since the notes are usually specific to one of them. All optional
additions to `xs:all`/`xs:choice` content models, so every existing file stays valid.

**The same hole again, in `<macro>`: no units.** A `<macro>` may carry `<parm>`, `<eqn>`,
`<doc>`, `<format>`, `<sim_specs>`, `<variables>` and `<views>` — but no `<units>`, and
neither `<parm>` nor the macro's own result can state what they are measured in. In Vensim
a macro is written exactly like any other equation and has units on every line:

```
:MACRO: SMTH DECR(input,tau : RATE)
SMTH DECR = INTEG( RATE , input)
	~	input
	~	A SMOOTH that can only decrease
	|
RATE = MIN(0,(input-SMTH DECR)/tau)
	~	input/tau
	~		|
```

Note `input` and `input/tau` — units expressed in terms of the *parameters*, which is what
makes a macro dimensionally checkable at each call site. Dropping them loses the only thing
that would let a reader unit-check a macro.
The variables *inside* a `<macro>` are ordinary `<stock>`/`<flow>`/`<aux>` elements and may
already carry `<units>` — only the macro's own result cannot. We write XMILE's own
`<units>` element there too, accepting that it does not validate, for the same reason as
the `<doc>` above: the tag already exists and means exactly this, and inventing
`vensim:units` would be a second spelling of it. We would ask that `<units>` be permitted
on `<macro>` and on `<parm>`, which would close the gap without a new element.

**An adjacent gap in the same element: there is no save interval.** `<sim_specs>` holds
`start`, `stop`, `dt` and `run`, and nothing else. Vensim's `SAVEPER` — how often results
are stored, as distinct from the integration step — has nowhere to go, and neither does
Stella's equivalent. A model integrated at `dt = 1/128` and saved yearly is a different
artefact from one that stores every step: the output series differ in length by two orders
of magnitude, which is a practical matter of file size and of what a reader can plot. The
schema has no `savestep`, `save_interval` or similar under any spelling; we checked. We
now write `<vensim:saveper>` to avoid dropping it, and would rather the standard had a
place for it. We would suggest an OPTIONAL `<savestep>` alongside `<dt>`, defaulting to
`dt` — which is what every current file implies by being unable to say otherwise.

**What we ship in the meantime.** Vensim now writes the `<doc>` on `<start>`, `<stop>` and
`<dt>`, accepting that it does not validate, in the same spirit as `vensim:netflow` — the
alternative was to keep discarding the text. The value is written *first* and the `<doc>`
after it, so that a reader taking the element's text content still gets the number
(`.text` stops at the first child); only a validating reader notices anything. It is not
namespaced, unlike `vensim:netflow` and `vensim:attach`, because those name concepts XMILE
has no word for, whereas this is XMILE's own `<doc>` being asked to appear in one more
place. A `vensim:doc` would just be a second spelling of a tag that already exists.

**The general principle we would ask the TC to adopt:** an interchange format should not
silently discard human-authored text. Equations can be regenerated and diagrams
re-drawn, but a modeller's explanation of *why* is the least reproducible thing in the
file. Wherever the standard carries a value a person can annotate in a source tool, it
should carry the annotation too.
