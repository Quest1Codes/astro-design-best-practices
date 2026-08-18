# AutoSys Client Surface Inventory → Astro API/CLI/UI Parity Mapping

Every AutoSys operation that operators perform today goes through one of several "client surfaces" — tools and interfaces that communicate with the Application Server. Before decommissioning AutoSys, every team that uses any of these surfaces needs a mapped Astro/Airflow equivalent. Missing even one surface means a team will lose a capability they rely on.

## Client Surface Inventory

{syn: AutoSys `jil` → Airflow DAG Python code; AutoSys `autorep` → Airflow REST API; AutoSys `sendevent` → Airflow REST API `POST /dagRuns`}

| AutoSys Client Surface | What It Does | Astro/Airflow Equivalent |
|---|---|---|
| **`jil` CLI** | Define/update/delete job definitions from the command line | Python DAG code in Git (deployed via Astro CLI `astro deploy`) [B2] |
| **`autorep` CLI** | Read-only reporting: job status, run history, machine/calendar/variable listings | Airflow REST API (`GET /api/v1/...`); `astro` CLI for Deployment queries [B2] |
| **`sendevent` CLI** | Manually trigger, hold, kill, or change status of jobs | Airflow REST API (`POST /api/v1/dags/{id}/dagRuns`, `PATCH` for state changes) [B2] |
| **WCC Web UI (Workload Control Center)** | Browser-based GUI for job monitoring, manual intervention, and reporting | Airflow UI (per-Deployment) + Astro Observe for cross-Deployment view [B2] |
| **AEWS REST API** | Programmatic control-plane access (CI/CD, external triggers) | Airflow REST API + Astro API [B2] |
| **JIL/SDK** | Programmatic job definition in client applications | Python DAG SDK (Airflow DAG objects, `@dag`, `@task` decorators) [B2] |
| **WCC Enterprise Command Line (ECLI)** | Run CLI commands (jil, autorep) inside the WCC browser tab | Astro CLI and Airflow REST API (no browser-embedded CLI equivalent) |

## Capability Gaps Requiring Process Change

| AutoSys Capability | Gap in Astro |
|---|---|
| `sendevent CHANGE_PRIORITY` (immediate priority change for queued job) | No exact equivalent; use `priority_weight` at design time, not runtime |
| WCC ECLI (browser-embedded CLI for ops teams) | No browser-embedded CLI in Airflow UI; teams must use Airflow REST API or Astro CLI |
| `autorep -c` (calendar definitions) | Calendars are code in Airflow (custom timetables); no CLI query for calendar definitions |

## Migration Readiness Checklist per Team

Before migrating a team's jobs, verify:
- [ ] Are they using `jil` for job definitions? → Confirm Git/DAG deployment workflow is understood.
- [ ] Are they using `autorep` for monitoring? → Confirm they have Airflow REST API or UI access.
- [ ] Are they using `sendevent` for manual intervention? → Confirm they have Airflow UI access and know DAG Trigger / Mark Success / Clear task flows.
- [ ] Are they using WCC for cross-team visibility? → Confirm they have Astro Organization access and Astro Observe.
- [ ] Are they scripting via AEWS? → Confirm their scripts are updated to call Airflow REST API endpoints.

## Sources

[B1] Broadcom AutoSys Documentation — `jil`, `autorep`, `sendevent`, WCC, ECLI, AEWS REST API, SDK — client surfaces and the Application Server as the central broker (accessed 2026-08-18)
[B2] Astronomer Docs & Apache Airflow Docs — Astro CLI `astro deploy`, Airflow REST API endpoints, Astro Observe, Airflow UI DAG Trigger and task management (accessed 2026-08-18)
