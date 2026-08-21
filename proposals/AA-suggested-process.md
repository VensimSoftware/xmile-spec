# A suggested process

The other files here are content items: things we think the specification should say
differently. This one is about how the work gets done, which is why it is filed apart
from them.

Sketched on the sd-tools list, <https://groups.google.com/g/sd-tools/c/KQIPH0QZ2uc>, as
four steps. Two of them have happened since.

1. **Get a repository up** with the text of the standard and the schema, in a format that
   is easy to edit. **Done:** this repository (parent), AsciiDoc, August 2026.

2. **Get the vendor-tag infrastructure working.** If it already works, produce an example;
   if it only works for functions, make the schema more extensible. **Done:**
   `xs:defaultOpenContent` and schema-level `defaultAttributes`, 18 August 2026.
   Item 1 records what remains: the prose does not describe the mechanism, and 34
   simple-typed elements are outside it.

3. **Simplify the core.** Find what is not common across implementations and make it
   optional, or move it into vendor-tag space.

4. **Then let vendors work asynchronously**, emitting core XMILE as far as they can with
   vendor extensions for the rest, and review the extensions periodically to see what has
   become common enough to promote into the spec.

## What step 3 needs

A decision rule, applied consistently. Item 7 sets out the union-versus-intersection
question and the matched pair that shows the rule is not being applied: `<non_negative>`
is in the standard as an option though three vendors lack it, while a net-flow stock is
excluded though Vensim has it. Item 2 argues the second case.

Macros are the model to copy. The core is simple; the features that are not universal are
in the optional section, with tiers of optionality inside it. Applying that shape to the
rest of the standard is most of step 3.

`00-corpus-validation.md` gives a way to pick candidates without arguing about them.
Anything the corpus shows every implementation writing belongs in the core; anything one
tool writes and the schema rejects is a candidate for vendor-tag space.

## What step 4 needs

A promotion rule, which nobody has written down. Step 4 is what makes the arrangement
self-correcting, but only if "common enough to promote" means something specific: how
many independent implementations, over what period, and who decides. Without that,
extensions accumulate and nothing is ever promoted, which is the failure mode this step
exists to prevent.

Step 4 also depends on step 2, so it has been impossible until this month. It is possible
now.
