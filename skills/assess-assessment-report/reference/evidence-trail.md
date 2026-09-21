---
topic: evidence-trail
family: assessment
skill: assess-assessment-report
verified_against:
  autosys: "12.0"
last_verified: 2026-09-17
confidence: cited
signals: []
---

# Evidence trail

How to answer "where did this number come from" in a customer review — every `G` table entry in
the report traces to a `manifest.<path>` field, and every ingested artifact traces to an
`evidence[].sha256`.

## Tracing a report number back to its manifest field

Every generated table in `assessment_report.md.j2` is rendered directly from a named
`manifest.<path>` (see `reference/report-structure.md`'s "Source manifest fields" column) — there
is no hand-typed number anywhere in a `G` section. To answer "where did X come from":

1. Find the section in `reference/report-structure.md`'s table.
2. Look up its "Source manifest fields" column.
3. `jq '.<path>' estate_manifest.json` (or the Python equivalent) to see the exact value.

## Tracing a manifest field back to an artifact

Every field in `estate_manifest.json` was produced by exactly one script from exactly one set of
input artifacts (`assess-estate-inventory/reference/manifest-schema.md`'s "Filled by" column for
`Estate`-level fields; `Instance`/`Job`/etc. core fields all trace to `build_estate_manifest.py`'s
`--instance`/`--autocal`/etc. inputs). Cross-reference `manifest.evidence[]` for the SHA-256 hash
of the specific file that produced a given instance's data.

## Tracing an AutoSys fact back to the PDF

Any `[AS p.N]` citation appearing anywhere in the report (including in reference files this
skill's output links to) is independently greppable: `grep -n "\[p.N\]" research/autosys-12.0/*.txt`
finds the exact source line. This is why every AutoSys-side reference file in this project cites
a page rather than paraphrasing from memory — it makes this exact check possible.

## What "reproducible" means here

Given the same input artifacts and the same registry version
(`manifest.generated_by.registry_version`), re-running the entire pipeline
(`build_estate_manifest.py` → `inventory_stats.py` → ... → `render_report.py`) produces a
byte-identical `estate_manifest.json` and report — every script in this project is deterministic
by design (plan §0). If a re-run produces a different number, either an input artifact changed
(check `evidence[].sha256`) or the registry was regenerated against an updated corpus/overlay
(check `generated_by.registry_version`) — never treat a discrepancy as random noise.
