# migrating-autosys-to-astronomer

A skill for migrating AutoSys Workload Automation (JIL job definitions, boxes, calendars) to Apache Airflow 3 on Astro. It contains a concept map of how every JIL construct translates to Airflow 3, reference docs for the parts that are genuinely hard to translate (condition strings, calendars), and a workflow that takes an estate from a read-only JIL scan to verified output parity and incremental, box-by-box cutover.

AutoSys is a distributed scheduler (Unix/Linux/Windows agents, an Application/Event Server, WCC) — not a mainframe scheduler. Where an estate's jobs touch mainframe-produced data or trigger JCL, that's a boundary-integration concern handled by a companion skill (see below), not a mainframe workload lift.

## How it works

The skill drives a migration through eight phases:

0. **Classify the estate**: mainframe-boundary jobs? a large distributed on-prem agent fleet? AutoSys already on Kubernetes? Load the matching companion skill(s) alongside this one — this skill always handles the job-semantics translation; the companions add the infrastructure-specific phases.
1. **Inventory**: [`scripts/jil_inventory.py`](scripts/jil_inventory.py) parses a JIL export read-only and lists every job and box, reconstructing box membership from each child job's `box_name` (JIL declares membership bottom-up, not top-down). The agent then classifies each record from the concept map ([`reference/mapping.md`](reference/mapping.md)): mechanical, needs judgment, redesign, or no equivalent with a documented alternative.
2. **Plan**: DAG boundaries (which boxes become TaskGroups vs. their own DAG), plus a decision for every `condition:` string — AutoSys's `s()/f()/n()/d()` boolean expressions don't map 1:1 onto Airflow trigger rules, which is what makes this the hardest part ([`reference/conditions-and-dependencies.md`](reference/conditions-and-dependencies.md) carries the decision tree).
3. **Trial** a few representative boxes end to end.
4. **Migrate piece by piece**, each job/box passing import, lint, execution, and output-parity checks against the still-running AutoSys job. Known failures and fixes live in [`reference/troubleshooting.md`](reference/troubleshooting.md); progress is tracked by [`scripts/status.py`](scripts/status.py), which refuses to call the migration done while anything is unaccounted for.
5. **Platform layer**: agents/machines, calendars, alerting, `autorep`/`sendevent`/WCC equivalents ([`reference/platform-and-cli-equivalents.md`](reference/platform-and-cli-equivalents.md)).
6. **Cut over gradually**: AutoSys stays the system of record until parity is measured; boxes flip one at a time (`ON_ICE` the AutoSys job, unpause the DAG); rollback is one step.
7. **Final report**: every job/box dispositioned, every condition string's equivalence documented, losses stated plainly.

## Companion skills

This skill covers job-semantics translation, which is common to every AutoSys estate. Infrastructure/architecture concerns differ enough by topology to live in separate skills:

- `migrating-autosys-mainframe-boundary-to-astro` — jobs that watch for or trigger mainframe-produced work (MFT/Connect:Direct drops, JCL submission via agent).
- `migrating-autosys-onprem-distributed-to-astro-cloud` — large fleets of on-prem Unix/Windows agents moving to Astro Cloud/Hybrid.
- `migrating-autosys-k8s-to-astronomer` — AutoSys already containerized/on Kubernetes, moving to Astronomer on Kubernetes.

Phase 0 of this skill tells you which of these to load based on what's in the JIL export and machine list.

## Using it

```bash
claude "Use the migrating-autosys-to-astronomer skill to migrate ~/autosys-export.jil to Airflow 3 on Astro"
```

Phase 1 is read-only; nothing touches the AutoSys instance or its schedules until the cutover phase at the end.

## What a translation looks like

```jil
/* AutoSys: a box with two command jobs, the second gated on the first */
insert_job: daily_load_box   job_type: b
box_terminator: 1
days_of_week: mo,tu,we,th,fr
start_times: "02:00"
run_calendar: business_days
alarm_if_fail: 1

insert_job: extract_orders   job_type: c
box_name: daily_load_box
command: /opt/etl/extract_orders.sh
machine: etl01

insert_job: load_orders   job_type: c
box_name: daily_load_box
command: /opt/etl/load_orders.sh
machine: etl01
condition: s(extract_orders)
```

```python
# Airflow 3: the box becomes a DAG scheduled on a Timetable derived from the
# business-days calendar; box_name membership becomes task membership;
# condition: s(extract_orders) becomes a plain dependency (default trigger_rule)
from airflow.sdk import dag, task

@dag(schedule=BusinessDaysTimetable(), catchup=False)
def daily_load_box():
    @task.bash
    def extract_orders():
        return "/opt/etl/extract_orders.sh"

    @task.bash
    def load_orders():
        return "/opt/etl/load_orders.sh"

    extract_orders() >> load_orders()
```

`reference/mapping.md` covers the full surface this way, including the JIL-to-Airflow-3 concept table for anyone newer to the Airflow side.

## Status

First draft, scaffolded from the same pattern as `migrating-dagster-to-airflow`. Not yet run against a real AutoSys estate — treat version-specific JIL attribute names (especially file-transfer job attributes) as needing verification against the customer's actual export or current Broadcom docs before relying on them, per the "do not invent JIL syntax" rule in `SKILL.md`.
