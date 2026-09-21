---
topic: report-structure
family: assessment
skill: assess-assessment-report
verified_against:
  autosys: "12.0"
last_verified: 2026-09-17
confidence: cited
signals: []
---

# Report structure

14 sections + 3 appendices (plan §7, extended per §11.13's "Operational profile" and "Command
payload analysis" additions). `G` = generated from `estate_manifest.json` by
`render_report.py`/`assessment_report.md.j2`; `H` = human-authored prose, and
`render_report.py --final` refuses to render if a `HUMAN:` placeholder remains empty, or any `G`
table is empty without an explicit `waived_reason`.

## H sections are analysis, not documentation

The reader of this report already has (or can be pointed to) `astro-design-best-practices`,
`autosys-reference`, and `autosys-to-astronomer` — the knowledge skills that explain what a
Deployment is, what an OR-condition means, what dag-factory does, and so on. An `H` section that
restates one of those concepts is not adding anything this specific engagement needed; it's
padding. Every sentence in an `H` section should be something that would be **false or meaningless
for a different AutoSys estate** — a number, a named job/box/instance, a specific decision,
override, or risk, drawn from *this* estate's own `G`-section data above it. If a sentence would
read identically in every assessment this skill ever produces, cut it or replace it with the
specific finding it was standing in for.

`render_report.py --final` enforces a mechanical floor for this: every `H` section must contain at
least one number or named token traceable to this report's own `G`-section data (a section with
none reads as generic explanation and is refused), and any sentence that near-verbatim matches
text from the knowledge skills is refused outright. Moderate similarity is only a warning — citing
a concept by its correct name isn't wrong, substituting the concept's explanation for the finding
is. Run `render_report.py --out report.md --lint` at any point during Phase 2 to see the same
checks applied to a still-in-progress draft, non-blocking.

| # | Section | G/H | Source manifest fields | Length guidance |
|---|---|---|---|---|
| 1 | Executive summary | H | — | Go / go-with-conditions / stay; top 5 risks; effort range; recommended tooling. Half a page. |
| 2 | Scope & method | G+H | `evidence[]`, instance list | What was assessed, what wasn't, how (this skill family, version). One page. |
| 3 | Estate profile | G | `stats.*_histogram`, `stats.box_depth_distribution` | Instance/job/box/machine/resource/calendar/xinst counts, owner/application/group breakdown. |
| 4 | Operational profile | G | `history.*` | Concurrency curve, dead-job candidates, manual-intervention table, SLA breaches. Explicitly note if history wasn't collected (optional artifact) rather than omitting the section silently. |
| 5 | Job-type coverage | G | `stats.job_type_histogram`, `unknowns.job_types` | Histogram; per family: count, default target, disposition distribution; unknowns list. |
| 6 | Attribute usage | G | `stats.attribute_family_histogram` | SLA/load/retry/notification/credential attribute usage with translation implication per family. |
| 7 | Dependency topology | G+H | `graph.*` | Graph metrics, cross-box/cross-instance edge counts, cycles, longest chain, OR/look-back/exitcode/VALUE condition counts (from per-job `condition_summary`); H: interpretation. |
| 8 | Command payload analysis | G+H | `command_summary.*` | Interpreter/OS-hint histograms, hidden-control-flow edges, credential-hit counts (never values), template clusters; H: interpretation. |
| 9 | Calendars and scheduling | G | `schedules.*` | Cron-expressible %, DST-sensitive job list, timezone spread. |
| 10 | Complexity scoring | G+H | `scores.*` | Per-disposition counts, effort points, effort-days range, tooling hint; H: notable REDESIGN/NONE items named plainly. |
| 11 | Target architecture | G+H | `architecture.decisions`, `architecture.sizing`, `architecture.cost_estimate` | Decision-table outputs with KB links; sizing numbers with `basis` (observed/floor) and formula; H: any overrides with reasons. |
| 12 | Translation tooling strategy | H | `scores.estate.tooling_hint` (seed only) | Otto / Orbiter / hand / hybrid, per wave. |
| 13 | Waves and effort | G+H | `waves[]` | Generated proposal; H: final, human-reviewed assignment. |
| 14 | Risks, losses, stay-signals | H | seeded from `scores.estate.by_flag`, `history.sla_breaches`, `history.dead_job_detection_trusted` | Stated plainly — a REDESIGN item or a low-confidence dead-job finding is not softened into ambiguous language. |
| A | Evidence appendix | G | `evidence[]` | Artifact list with SHA-256 hashes and receipt dates; registry version (`generated_by.registry_version`); every `[AS p.N]` citation used anywhere in the report is traceable back to `research/autosys-12.0/*.txt`. |
| B | Unknowns and escalations | G | `unknowns.*` across all instances | Every unresolved job type/attribute/condition/reference, per `assess-estate-inventory/reference/unknowns-and-escalation.md`'s resolution. |
| C | Glossary | G | — | Reused from `autosys-to-astronomer/SKILL.md`'s glossary table. |

## Example `H` paragraph (executive summary, illustrative only)

> This assessment covers the ACE instance's 297 jobs across 50 boxes. 97.6% of jobs score MECH
> or JUDG; two REDESIGN-flagged boxes involve OR-combined conditions spanning cross-instance
> dependencies and should be scoped as a dedicated design spike before wave planning. Estimated
> effort: 106-197 person-days. Recommendation: **Migrate with conditions** — proceed, with the
> REDESIGN items named explicitly rather than absorbed into the general estimate.

## Waived `G` sections

A `G` table that's genuinely empty (e.g. no `history.*` data because run-history artifacts
weren't collected) is rendered with an explicit `waived_reason` string, never silently blank —
`render_report.py --final` enforces this structurally.
