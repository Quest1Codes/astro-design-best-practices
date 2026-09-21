---
topic: coexistence-modes
family: migration
skill: migrate-parallel-run-and-cutover
verified_against:
  airflow: "3.3.1"
  astro_runtime: "3.3-2"
  autosys: "12.0"
last_verified: 2026-09-17
confidence: mixed
signals: []
---

# Coexistence modes

Thin wrapper over the general coexistence patterns
(`astro-design-best-practices/reference/migration-execution-and-coexistence/` — Phase 2
of this refactor adds `signals:` front-matter to that cluster so `kb-routing.md` can route into
it directly; until then, read the cluster's index in its own `SKILL.md`), with manifest-driven
mode selection for this skill specifically.

## Mode selection

| Mode | When | AutoSys state | Airflow state |
|---|---|---|---|
| **Paused shadow** | Default for most units | Fully live, authoritative | DAG deployed, `is_paused_upon_creation=True`, manually triggered per parity cycle |
| **Live shadow** | Units where a manual trigger cadence can't reproduce the real trigger conditions (event-driven `FW`/`FT` jobs, `condition:`-gated units) | Fully live, authoritative | DAG unpaused but writes routed to a non-production sink (a shadow table/path), never the real output location, until `go` |
| **Dry-run only** | Units with irreversible side effects that can't be safely shadowed at all (an FTP delivery to an external counterparty, an irrevocable financial transaction) | Fully live, authoritative | DAG validated through Gate 1-3 only (import/lint/execution against a test target); no live-target shadow run at all — parity is established by code review + a single supervised cutover, not repeated cycles |

`manifest.scores.jobs[key].flags` (e.g. `hidden_flow`, `sla`) and the job type
(`reference/job-types/*.md`'s disposition table) are the inputs to this choice — a box containing
any REDESIGN-flagged or `hidden_flow`-flagged unit should default to **live shadow** at minimum,
since a paused shadow can't exercise the actual trigger path that made those units complex in the
first place.

## Coexistence duration

Match the observation window to the job's own schedule (a monthly close job needs a longer
parity window than a daily feed) — see `reference/parity-cycles.md`'s cycle-count table.
