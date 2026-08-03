---
name: migrating-autosys-to-astronomer
description: Guide for migrating AutoSys Workload Automation (JIL job definitions) to Apache Airflow 3 on Astro. Use when the user mentions migrating, converting, or porting AutoSys (CA WA AE) jobs, boxes, or JIL to Airflow or Astro, wants to plan or assess such a migration, or asks what a JIL construct maps to in Airflow. Covers job types (command, box, file watcher, file transfer), condition syntax (s/f/n/d), calendars, global variables, alerting/SLAs, and autorep/sendevent/WCC equivalents. Always load this skill first for any AutoSys-to-Airflow request; it classifies the estate and routes to companion skills for mainframe-boundary, distributed on-prem, or AutoSys-on-k8s topologies.
hooks:
  PostToolUse:
    - matcher: "Edit"
      hooks:
        - type: command
          command: "echo 'DAG edited: consider re-running python3 scripts/status.py summary to confirm no manifest records were silently left pending'"
---

# AutoSys → Airflow 3 (Astro) migration

Migrate an AutoSys Workload Automation estate (JIL job definitions, boxes, calendars, agents) to Airflow 3 on Astro Runtime, honestly. The migration is inventory-first (every job, box, and condition string gets an explicit disposition before anything is translated), incremental (domain by domain, AutoSys stays authoritative until parity is proven), and estate-aware (this skill handles the job-semantics translation that is common to every AutoSys shop; topology-specific concerns route to a companion skill — see Phase 0).

First time driving this? Read `reference/quickstart.md`: hour-one commands, the JIL glossary, and what can and cannot break.

## A note on scope

AutoSys/CA WA AE is a **distributed** scheduler (Unix/Linux/Windows agents + Application Server + Event Server + WCC). It does not run natively on z/OS — mainframe scheduling is a separate Broadcom product line (CA Workload Automation for z/OS, formerly CA-7). If the estate has jobs that trigger or watch for mainframe-produced work, that is a **boundary integration**, not a mainframe lift; route it to the mainframe-boundary companion skill (Phase 0) rather than assuming this skill moves mainframe compute.

## Migration at a glance

1. Baseline the target Astro project's tests (if one exists), then inventory the AutoSys estate read-only (`scripts/jil_inventory.py` → manifest).
2. Classify the estate's topology (Phase 0) and load whichever companion skill(s) apply. Classify every job/box/calendar (MECH/JUDG/REDESIGN/NONE per `reference/mapping.md`); make the go/no-go call; plan DAG boundaries and condition-string translations into the manifest.
3. Trial-migrate 2-3 representative boxes end-to-end through validation.
4. Migrate domain by domain (by box, then by machine/team ownership), tracking per-unit state (`scripts/status.py`); fix failure classes via `reference/troubleshooting.md`, never stub.
5. Map the platform layer (agents/machines, calendars, alerting, WCC, autorep/sendevent) per `reference/platform-and-cli-equivalents.md`.
6. Run side by side (AutoSys stays authoritative), then cut over box by box or machine-group by machine-group, keeping rollback one step away.
7. Deliver the migration report: every job/box dispositioned, an equivalence row per condition string, losses stated plainly.

## Requirements

- Target **Astro Runtime 3.3+** (Airflow 3.3+); Dataset-driven scheduling and Timetables need this range for a clean calendar mapping.
- A JIL export of the estate (`autorep -j ALL -q` output or a `jil` dump). A running AutoSys instance is helpful but not required for the inventory phase.
- `astro` CLI for the target project.

## Hard rules

1. **Never stub.** A translated job/box either works through validation or is deferred with a written reason. Fake-success bodies and workaround code with long justifying comments are failures.
2. **No silent omissions.** Every record in the manifest ends `complete` or `deferred (reason)`. `scripts/status.py summary` exits nonzero otherwise; run it before claiming done.
3. **Equivalence rows for every condition string.** Each `condition:` attribute gets a report row: source expression, target implementation (trigger_rule / Dataset / custom sensor), delta in one sentence. AutoSys's `n()` (not running) and OR-combined conditions have no single stock Airflow equivalent — the sin is not the delta, it is the undocumented delta.
4. **Fix classes, not instances.** When a translation pattern fails validation, fix the pattern (and record it in `reference/troubleshooting.md`), then re-apply; do not hand-patch one job.
5. **Do not invent JIL syntax.** JIL attribute names and job types drift across AutoSys/WA AE versions (notably file-transfer job attributes and any container/agent-related job types). The references contain the stable, well-documented core (`c`, `b`, `f` job types; `condition`, `box_name`, `days_of_week`, `start_times`, `run_calendar`/`exclude_calendar`, `alarm_if_fail`, `term_run_time`). Anything not covered there gets verified against the customer's actual JIL export or current Broadcom docs before use — never assumed from a version you haven't checked.

## Phase 0: Preflight and estate classification

Confirm target Runtime version and `astro` CLI presence. Then classify the source estate from the JIL export and agent/machine list — this determines which companion skill(s) to load alongside this one:

| Signal in the estate | Load companion skill |
|---|---|
| File-watcher or FT jobs whose paths/hosts reference z/OS datasets, MFT gateways, or Connect:Direct/NDM; jobs that submit JCL via agent | `migrating-autosys-mainframe-boundary-to-astro` |
| Many `machine:` values spanning on-prem Unix/Windows hosts (dozens to thousands of agents), no containerization | `migrating-autosys-onprem-distributed-to-astro-cloud` |
| AutoSys Application Server / agents already running as containers or on Kubernetes | `migrating-autosys-k8s-to-astronomer` |

An estate can match more than one row (e.g., a distributed on-prem fleet with a mainframe boundary at its edges) — load every companion that matches. This skill's own phases (1-7 below) still run in all cases; the companion skills add platform/infrastructure phases, not a replacement workflow.

## Phase 1: Inventory (read-only)

```
python3 scripts/jil_inventory.py <jil_export.jil> --out manifest.json
```

The manifest lists every job/box with its attributes (job_type, command, machine, condition, box_name, calendar refs, alerting), reconstructs box membership (child jobs declare `box_name`, not the reverse — the scanner builds the tree), and flags condition strings that reference multiple jobs with AND/OR combinations for later classification. Every record starts `classification: "pending"`. Classifying is YOUR judgment task: assign each record MECH / JUDG / REDESIGN / NONE from `reference/mapping.md`.

## Phase 1.5: Go/no-go

Before translating anything, assess what this estate gives up:

| If load-bearing | The Airflow-world answer | Stay-signal only if |
|---|---|---|
| `n()` (not-running) gating used as a manual mutual-exclusion lock | `max_active_runs=1` + task-level concurrency pools | Cross-DAG mutual exclusion across teams with no shared pool namespace |
| Deep AND/OR condition trees spanning boxes | Decompose into Dataset-driven schedules where possible (see `reference/conditions-and-dependencies.md`); residue becomes a small evaluator task | A single condition string ANDs/ORs across more jobs than is practical to decompose by hand |
| WCC ad hoc operational actions (on ice/off ice, force-start, priority bump during an incident) | `astro`/`airflow` CLI + REST API, Airflow UI | Incident responders require the exact WCC click-path with no retraining window |
| Global-variable-driven runtime job cloning (template jobs instantiated by `sendevent`) | Dynamic task mapping | The cloning logic itself is undocumented/tribal and can't be reconstructed from JIL alone |

Outcome is three-valued: **Migrate**, **Migrate with conditions** (the common case — name the losses, proceed), or **Stay on AutoSys, today** (reserved for multiple unmitigated stay-signals at once).

## Phase 2: Plan

- **DAG boundaries**: each top-level box is a candidate DAG; nested boxes are candidate TaskGroups. A box that spans machine/team ownership or has a materially different schedule than its parent is a candidate for its own DAG linked via Dataset or `TriggerDagRunOperator` instead of a TaskGroup — decide per `reference/mapping.md`.
- **Condition-string decisions** via `reference/conditions-and-dependencies.md` (trigger_rule / Dataset / custom evaluator).
- **Calendar decisions** via `reference/calendars-and-scheduling.md` (Timetable vs cron vs Dataset-driven).
- **Order**: leaf boxes first, dependency order after; the platform layer (Phase 5) last.
- Fill each planned unit's target expectations into the manifest: `dag_id`, `task_count`, `trigger_rule`/`edges`, `schedule`. An unenriched manifest means downstream validation checks nothing — treat missing fields as a planning gap, not a shortcut.
- Scaffold the target: `astro dev init`, shared helpers under `include/`.

## Phase 3: Trial

Migrate 2-3 representative boxes end-to-end before fanning out: one MECH command-job box, one box with a nontrivial condition string, and one calendar-driven box (or the nearest available mix). What the trial teaches goes into `reference/troubleshooting.md` before scaling.

## Phase 4: Migrate, domain by domain

Per unit, the state machine (tracked in the manifest):

```
pending → translate → fix-import → fix-lint → fix-tests → verify-parity → complete
                                    ↘ deferred (reason required)
```

- Translate using the reference file for the construct (routing table below).
- Validate: `astro dev parse` / `astro dev pytest` for import and lint gates, then execution and output parity against the still-running AutoSys job (compare exit codes, output files, row counts) per `reference/validation.md`.
- On failure, retry with the latest validator output in context (cap ~10 attempts, then defer with the failure class).
- Advance state only on gate pass: `python3 scripts/status.py advance <unit-id> ...`. A wrong disposition is corrected with `status.py reopen <unit-id> --reason ...`.
- Commit per unit, atomically.

## Phase 5: Platform layer

`reference/platform-and-cli-equivalents.md`: agent/machine → executor or worker-queue mapping (or defer to the relevant companion skill for the full infrastructure plan), `autorep`/`sendevent`/`jil` → `airflow`/`astro` CLI and REST API, WCC → Airflow UI + Astro UI, alerting → `reference/alerting-and-sla.md`.

## Phase 6: Side-by-side and cutover

AutoSys remains authoritative. Run migrated DAGs paused/shadowed; compare outputs over the same logical window. Cut over box by box (or machine-group by machine-group, per the companion skill's wave plan): put the AutoSys job/box `ON_ICE`, unpause the Airflow DAG; rollback is the reverse (`OFF_ICE` + pause DAG).

## Phase 7: Final report

`scripts/status.py summary` must pass. The report contains: the go/no-go assessment and rationale, disposition table for every job/box, all condition-string equivalence rows, the NONE/REDESIGN losses stated plainly, the calendar map, and the deferred list with reasons.

## Reference routing

| Construct encountered | Read |
|---|---|
| First hour, JIL glossary, what can break | `reference/quickstart.md` |
| Any job/box (first stop: one row per construct) | `reference/mapping.md` |
| `condition:` strings, `s()`/`f()`/`n()`/`d()`, box dependency chains | `reference/conditions-and-dependencies.md` |
| `run_calendar`/`exclude_calendar`, `days_of_week`, `start_times`, `run_window` | `reference/calendars-and-scheduling.md` |
| `%%variable%%` substitution, global variables | `reference/global-variables-and-templating.md` |
| `alarm_if_fail`, `term_run_time`, notifications | `reference/alerting-and-sla.md` |
| `autorep`, `sendevent`, `jil`, WCC, agents/machines | `reference/platform-and-cli-equivalents.md` |
| Parity testing, validation gates | `reference/validation.md` |
| Failure classes seen before | `reference/troubleshooting.md` |
| Estate is mainframe-boundary / distributed on-prem / AutoSys-on-k8s | see Phase 0 table above for the companion skill |

## Scripts

| Script | Purpose |
|---|---|
| `scripts/jil_inventory.py` | Parse a JIL export → JSON manifest (jobs, boxes, conditions, calendars) |
| `scripts/status.py` | Per-unit state machine + completeness gate |
