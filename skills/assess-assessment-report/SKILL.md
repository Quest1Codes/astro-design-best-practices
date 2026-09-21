---
name: assess-assessment-report
description: Final phase of an AutoSys estate assessment — renders the 14-section assessment report from the fully-scored, architected estate manifest. Use once assess-astro-target-architecture has populated manifest.architecture. Every generated (G) table traces to a manifest field; every human (H) section is a placeholder render_report.py --final refuses to accept unfilled, empty, generic, or near-verbatim-copied-from-a-knowledge-skill.
---

# Assessment report

Render the deliverable. Every generated table comes straight from `estate_manifest.json`
(`assess-estate-inventory`/`assess-migration-complexity-scoring`/`assess-astro-target-architecture`'s
combined output); every human section is an explicit `HUMAN:` placeholder in the draft, and the
`--final` gate refuses to pass while one remains — there is no code path that lets an unauthored
section reach a customer silently.

`--final` also refuses a *filled-but-generic* section: one with no number or named finding
traceable to this estate's own data, or one whose prose near-verbatim matches this KB's own
knowledge skills (astro-design-best-practices/autosys-reference/autosys-to-astronomer). The
deliverable is this estate's analysis, not those skills rephrased — see "H sections are analysis,
not documentation" in `reference/report-structure.md`.

## Requirements

- `estate_manifest.json` with `stats{}`, `graph{}`, `scores{}`, `waves[]`, `architecture{}` all
  populated (every prior assessment phase run).
- `jinja2` (already a `_lib` dependency). `pandoc` optional, for DOCX output.

## Workflow

### Phase 1: Draft

```
python3 scripts/render_report.py --manifest estate_manifest.json --out report.md --draft
```

Renders `templates/assessment_report.md.j2` fresh. Every `G` section is filled with real data;
every `H` section contains a `HUMAN: <prompt>` placeholder to author directly in `report.md`.
**Re-running `--draft` overwrites the file, including any human edits already made** — use it
only to create the first draft, or to intentionally discard edits and start over.

### Phase 2: Author every HUMAN: section

Per `reference/report-structure.md`, write each `H` section directly into `report.md`, replacing
its `HUMAN:` placeholder with **this estate's findings**, not a restatement of what the underlying
concept is — every sentence should reference a number, a named job/box/instance, or a specific
decision from the manifest data rendered above it. An empty `G` table found genuinely empty (e.g.
no history data collected) already carries a `<!-- WAIVED: reason -->` comment in the draft for
the expected cases — replace that comment's reason if the actual situation differs, don't just
leave it.

Optionally, run the gate early and often while authoring:

```
python3 scripts/render_report.py --out report.md --lint
```

Advisory only (always exits 0) — flags sections with no estate-specific signal yet, or prose that
resembles the knowledge skills' reference text, before you get to the blocking `--final` gate.

### Phase 3: Finalize

```
python3 scripts/render_report.py --out report.md --final
```

Validates (does **not** re-render) the existing `report.md`: fails if any `HUMAN:` marker remains,
any `<!-- G:empty:... -->` marker lacks an adjacent `<!-- WAIVED: reason -->` comment, any `H`
section has no number or named finding traceable to this report's own `G`-section data, or any `H`
sentence near-verbatim matches (≥0.92 similarity) text from the knowledge skills. Moderately
similar phrasing (0.75–0.92) is printed as a non-blocking warning to review, not a hard failure.
Add `--docx report.docx` (either phase) to also produce a DOCX via `pandoc`, when present —
Markdown only otherwise.

### Phase 4: Evidence appendix check

Confirm Appendix A actually lists every artifact `assess-estate-discovery` validated, with real
SHA-256 hashes (not placeholders) — per `reference/evidence-trail.md`.

### Gate

`python3 -m autosys_jil.status --manifest estate_manifest.json summary --workflow assessment`
should read `reported` once `--final` has passed. This is the terminal state of the assessment
workflow.

## Reference routing

| Question | Read |
|---|---|
| The 14 sections + 3 appendices, G/H, source fields | `reference/report-structure.md` |
| How to trace a report number back to a manifest field or a PDF page | `reference/evidence-trail.md` |

## Scripts

| Script | Purpose |
|---|---|
| `scripts/render_report.py` | `--draft` renders fresh from the manifest; `--lint` runs advisory (non-blocking) specificity/echo checks against the in-progress file; `--final` validates the existing file (blocking) without overwriting it |

## Templates

| Template | Purpose |
|---|---|
| `templates/assessment_report.md.j2` | The report structure; `table()` is a Jinja global for rendering any histogram/dict as a Markdown table |
