---
topic: os-monitors-om
family: migration
skill: migrate-jil-to-airflow-translation
verified_against:
  airflow: "3.3.1"
  astro_runtime: "3.3-2"
  autosys: "12.0"
  autosys_doc_pages: [2551]
last_verified: 2026-09-17
confidence: mixed
signals: []
---

# OS monitors: OMCPU, OMD, OMEL, OMIP, OMP, OMS, OMTF

| Code | What it monitors | Default target | Disposition |
|---|---|---|---|
| `OMCPU` | CPU usage | Prometheus/Datadog (or the customer's existing infra-monitoring stack) | **NONE** |
| `OMD` | Disk usage | Same | **NONE** |
| `OMEL` | Windows Event Log | Same | **NONE** |
| `OMIP` | IP/network reachability | Same | **NONE** |
| `OMP` | Process presence | Same | **NONE** |
| `OMS` | Windows service status | Same | **NONE** |
| `OMTF` | Text file reading/monitoring (log grep) | **NONE** by default, unless the result is load-bearing for a downstream job — see below | NONE / JUDG |

Infrastructure monitoring belongs in a dedicated monitoring stack, not the orchestrator — this is
the single largest source of `NONE`-dispositioned jobs in a typical estate (`> 20% OM* job types`
is `assess-estate-inventory/reference/reading-the-inventory.md`'s "monitoring culture" signal).
`scoring_rules.yaml`'s `jt.om*: 1pt NONE flag:monitoring` scores this family cheaply and
deliberately — don't second-guess the NONE disposition without a specific reason.

## The `OMTF` exception

If an `OMTF` job's text-file-monitoring result actually gates a downstream job (a real
`condition:` dependency exists on it, not just an informational alert), it's load-bearing and
needs a real translation: `@task.bash` running the equivalent grep/search, or a `FileSensor`
variant checking file content rather than just existence. Check
`manifest.graph`'s condition edges for the `OMTF` job before defaulting to NONE — a job with
outbound condition edges from other jobs is not purely monitoring.

## Documented alternative

State plainly in the report which monitoring stack replaces these (Prometheus/Datadog/existing
tooling) — a NONE disposition is not "delete and forget," it's "this moves to infra monitoring,"
and the report should name where.

## What the scaffolder emits vs. leaves as TODO

Refuses to scaffold anything for a NONE-dispositioned unit (per the hard rule) — lists them
instead, grouped by monitored resource type, as input to the infra-monitoring migration
conversation (out of this skill's scope).
