# Platform and CLI equivalents

## Command-line tools

| AutoSys | Purpose | Airflow/Astro equivalent |
|---|---|---|
| `autorep -j <job> -q` | Report a job's current status | `airflow tasks state <dag_id> <task_id> <execution_date>` / `astro deployment dag-runs` / Airflow REST API `GET /dags/{dag_id}/dagRuns` |
| `autorep -j ALL -q` | Full estate status dump | Airflow REST API bulk DAG/DagRun listing; this is also the source export for `scripts/jil_inventory.py` if a live instance is available for cross-checking the static JIL export |
| `sendevent -E STARTJOB -J <job>` | Force-start a job | `airflow dags trigger <dag_id>` / `astro deployment dag trigger` |
| `sendevent -E JOB_ON_ICE -J <job>` | Freeze a job (won't run until thawed) | `airflow dags pause <dag_id>` (DAG-level) — note AutoSys `ON_ICE` is job-granular while Airflow's native pause is DAG-granular; a frozen single task within an otherwise-active box needs a task-level guard (e.g. a `Variable`-gated short-circuit) rather than a direct equivalent |
| `sendevent -E JOB_OFF_ICE -J <job>` | Thaw a frozen job | `airflow dags unpause <dag_id>`, or clear the task-level guard above |
| `sendevent -E CHANGE_STATUS -s SUCCESS -J <job>` | Manually mark a job's status (operational override) | `airflow tasks clear` + manual state set via REST API/UI, or `airflow dags backfill` for a specific logical date — used sparingly, same as in AutoSys |
| `jil < file.jil` | Load/update job definitions | The DAG file itself, deployed via `astro deploy` / CI-CD — JIL's "definition as text" maps naturally onto "DAG as code," which is a genuine improvement (version control, code review) worth calling out in the report |
| WCC (Workload Control Center) | Web UI for defining, monitoring, and operating jobs | Airflow UI (monitoring/operating) + DAG code and CI/CD (defining) + Astro UI (Deployment-level operations). WCC's "define a job through a form" workflow has no direct equivalent — defining is now code, not a form. Flag this as a workflow change for job authors, not just an infrastructure swap |

## Agents and machines

`machine:` assignments and the underlying agent fleet are an infrastructure concern, not a job-semantics one — this skill records the *intent* ("this job needs to run somewhere with access to X") in the manifest, but the actual executor/queue/pool mapping is handled by whichever companion skill matches the estate's topology (see `SKILL.md` Phase 0):

- Mainframe-adjacent boundary jobs → `migrating-autosys-mainframe-boundary-to-astro`
- Large on-prem distributed agent fleets → `migrating-autosys-onprem-distributed-to-astro-cloud`
- AutoSys already containerized/on Kubernetes → `migrating-autosys-k8s-to-astronomer`

Do not attempt to resolve `machine:` → executor/pool mappings without loading the applicable companion skill; the right answer depends entirely on the target topology.
