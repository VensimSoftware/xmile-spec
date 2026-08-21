*Status against XMILE v1.1 (SDS Candidate Standard 02, 20 August 2024)
as reviewed 2026-07-30:* **New in this draft**, raised against 1.1's own text: 2.1 claims four categories while the document specifies at least seven kinds, one of them in 2.1's own closing paragraph.

*Re-checked 2026-08-20 against the schema added to `xmile-spec` on 2026-08-18:*
**Stands, and sharper than when written.** The section still claims four categories of
namespace. The schema has since introduced a working XML-tag-namespace mechanism, complete
with a `##other` wildcard and a deliberate `##local` exclusion, which is precisely the
category 2.1 mentions in one clause and does not count. The count still omits some,
like dimension namespaces.

---
# Section 2.1 undercounts the namespaces

2.1 opens:

> "There are four categories of namespaces in play in a XMILE whole-model — XML tag
> namespaces, Variable namespace, Function namespace and Unit namespaces."

At least three more are described elsewhere in the same specification, and one of them is
described in 2.1 itself.

**Element namespaces, one per dimension.** The closing paragraph of 2.1 says "Dimension
names, in turn, define their own Element namespace", and 3.2.2.3 calls the same thing "the
implicit array namespace". This is not merely a fifth item on the list: the other four are
*singletons* per whole-model, whereas Element namespaces are a family — one per dimension
name, arbitrarily many — which the "four categories" framing has no shape for. It also
obscures that a dimension straddles two namespaces at once: its *name* is "conceptually
part of the Variable namespace", while its *elements* form a namespace of their own,
resolved by context inside square brackets or by qualification (`Location.Boston`).

**Submodel namespaces.** 3.2.2.3 states that "identifiers within macros and submodels, by
definition, appear in their own local namespace", and later refers to "the implicit
namespaces of submodels". 2.1 mentions neither, and speaks instead of resolution "within
models", illustrated with `MyCompany.profit`. That understates the mechanism, because
4.7.1's `<connect>` addressing is a nested scope tree, not a flat set of models:

```xml
<connect to="Input"             from=".Root_Model_Output"/>
<connect to=".Root_Model_Input" from="Sub_Model.Output"/>
```

A leading `.` reaches the root, `Sub_Model.Output` reaches down into a child, and
connections "must be specified at the lowest common ancestor (LCA) of the submodel
hierarchy". A rule in 3.2.2.3 depends on treating these as namespaces: the
`namespace="std, isee"` fallback-resolution order explicitly **does not** apply to the
implicit namespaces of submodels, and identifiers accessed across models MUST be
qualified. A reader who took 2.1's four categories as complete would not know to
implement any of this.

**Macro-local namespaces.** Macros appear in 2.1 only as contributors of names *to* the
Function namespace, never as namespaces themselves — yet 3.2.2.3 groups them with
submodels as having their own local namespace, and 3.2.2.3's resolution rules elsewhere
refer to names resolved "in a macro definition, strictly inside the macro".

**Proposal.** Rewrite 2.1 to enumerate the namespace kinds actually specified, and to
distinguish the two structurally different sorts: those with exactly one instance per
whole-model (XML tag, Unit, Function, and the per-model Variable namespaces) and those
instantiated many times over (Element, submodel, macro). Since 2.1 is the section an
implementer reads first, it should also state which of them participate in the
`namespace="…"` fallback-resolution order and which do not, rather than leaving that to a
note in 3.2.2.3. This is an editorial change with no effect on file format, but namespace
resolution is exactly where independent implementations diverge silently.

**A related question on modules.** 4.7.1 requires a module's `name` to "match the `name`
attribute of the submodel" when no `resource` is given. If that is strict, two instances
of the same submodel inside one parent cannot be distinguished, which seems to work
against the same section's stated goal of supporting "arbitrary re-use of submodels". Is
the intent that re-use requires `resource`, or that the matching rule is looser than it
reads?

---
