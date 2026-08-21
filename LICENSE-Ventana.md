# MIT License

Copyright (c) 2026 Ventana Systems, Inc.

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.

---

## What this covers

The material Ventana Systems contributed to this repository:

- `tools/v-validate/` and `tools/v-generate/` — the scripts, and the schemas they
  generate that are wholly ours.
- `proposals/` — the proposal text, `00-corpus-validation.md`, `AA-suggested-process.md`,
  and the crosstab tables under `proposals/crosstab/` to the extent they are our work.
- `spec/schema/README.md`, and the changes to `tools/validate.py` and
  `.github/workflows/build.yml`.

## What it does not cover

Licensing our own work says nothing about anyone else's, and several things here are
someone else's:

- **`spec/` and `archive/`** are the specification. Version 1.0 is © OASIS Open 2015,
  version 1.1 © System Dynamics Society 2024, each under its own terms. Note that the
  OASIS notice permits derivative works that comment on or explain the document but
  forbids modifying the document itself outside an OASIS Technical Committee.
- **`proposals/schema/xmile-v1.x-proposal*.xsd`** are the published OASIS schema plus a
  mechanical change. They are derivative works of that schema and carry its notice; only
  the change is ours, and the generator that makes it is the part we license here.
- **`models/`** holds third-party models — isee systems, James Houghton via the PySD test
  suite, WorldTrans FRIDA — each with its provenance recorded in `models/README.md`. They
  are included as test fixtures under their own terms and are not ours to license.
- **The crosstab's third-party facts.** `proposals/crosstab/` merges data extracted from
  xmutil (MIT, © 2018 bobeberlein), PySD (MIT, © 2013-2022 PySD contributors) and
  SDEverywhere (MIT, © 2016-2024 Todd Fincannon and Climate Interactive / New Venture
  Fund). Those remain under their own licences and are cited in
  `proposals/crosstab/README.md`. What we license here is the Vensim column, the
  generator, and the derived structure.
