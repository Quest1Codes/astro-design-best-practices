---
topic: cutover-waves
family: migration
skill: migrate-topology-onprem-distributed
verified_against:
  airflow: "3.3.1"
  astro_runtime: "3.3-2"
  autosys: "12.0"
last_verified: 2026-09-17
confidence: mixed
signals: [multi_owner]
---

# Cutover waves

Moved. Full content is now split across two skills, by concern:

- **Which units go in which wave** (grouping principle, sequencing, pilot-wave criteria):
  `assess-migration-complexity-scoring/reference/wave-planning.md`
- **How a wave is actually cut over** (per-box mechanics, `ON_ICE`/`ON_HOLD`, what "clean"
  means): `migrate-parallel-run-and-cutover/reference/cutover-runbook.md`

This companion's own `reference/execution-topology-mapping.md` still covers the
Hosted/Hybrid/bridge classification that a wave's machine-group composition depends on.
