---
topic: job-states-and-events
family: knowledge
skill: autosys-reference
verified_against:
  autosys: "12.0"
  autosys_doc_pages: [2299, 2914, 2915, 2916, 2917, 2919, 2920, 2923]
last_verified: 2026-09-17
confidence: cited
signals: []
---

# Job states and events

Generated data lives in `_lib/autosys_jil/registry/states.json` (18 entries) and `events.json`
(31 entries); this file is the prose companion. `airflow_equivalent` columns here are a
migration-relevant annotation, not part of the AutoSys source fact — see
`migrate-jil-to-airflow-translation/reference/job-states-to-task-states.md` for the full
translation treatment (deferrable-operator/HITL options, cutover implications).

## States [AS p.2912+ "AutoSys System States"]

| State | Terminal | Description [AS p.N] |
|---|---|---|
| `INACTIVE` | no | Job has never run or was reset; not eligible until conditions/schedule are met. [p.2914] |
| `ACTIVATED` | no | Containing box has started; job is waiting on its own starting conditions. [p.2916] |
| `STARTING` | no | Event processor initiated the start; the agent has not yet reported `RUNNING`. [p.2915] |
| `RUNNING` | no | The process is executing on the agent. [p.2914] |
| `SUCCESS` | **yes** | Exit code within the success range (0, or `<= max_exit_success`, or in `success_codes`). [p.2914] |
| `FAILURE` | **yes** | Exit code outside the success range. [p.2917] |
| `TERMINATED` | **yes** | Killed via `KILLJOB`, terminated by its box, or the agent was lost. [p.2917] |
| `RESTART` | no | Application-level failure; the scheduler will retry per `n_retrys`. [p.2923] |
| `QUE_WAIT` | no | Eligible to start but waiting for machine load / priority (see `reference/machines-load-and-resources.md`). [p.2914] |
| `WAIT_REPLY` | no | Waiting for a manual `REPLY_RESPONSE` — the only state with no automated equivalent. [p.2919] |
| `ON_HOLD` | no | Held by an operator; will **not** start; dependents wait. [p.2915] |
| `ON_ICE` | no | Iced by an operator; removed from the flow; **dependents treat it as `SUCCESS`**. [p.2915] |
| `ON_NOEXEC` | no | Runs through the flow without actually executing; marked `SUCCESS`. [p.2914] |
| `PEND_MACH` | no | Target machine offline/unreachable; waiting. [p.2916] |
| `SUSPENDED` | no | Suspended via `SUSPENDJOB`. [p.2920] |
| `RESWAIT` | no | Waiting for a virtual resource (`insert_resource`). [p.2915] |
| `REFRESH_DEPENDENCIES` | no | Transient: re-evaluating dependencies. |
| `REFRESH_FILEWATCHER` | no | Transient: file-watcher refresh. |

### `ON_HOLD` vs. `ON_ICE` vs. `ON_NOEXEC` — read this before designing a cutover primitive

These three look similar (all suppress normal execution) but have **different effects on
dependents**, which matters directly for `migrate-parallel-run-and-cutover`'s shadow/cut
mechanics:

| State | Job itself runs? | What dependents see |
|---|---|---|
| `ON_HOLD` | No | Dependents **wait** — the box/chain stalls until `JOB_OFF_HOLD`. |
| `ON_ICE` | No | Dependents proceed **as if it succeeded** — the job is skipped, not blocking. |
| `ON_NOEXEC` | No (marked `SUCCESS` without executing) | Same as a normal success — dependents proceed. |

`ON_ICE` is the natural AutoSys-side primitive for "freeze this job during migration without
blocking everything downstream of it," and `ON_HOLD` is the natural primitive for "stop
everything here." `migrate-parallel-run-and-cutover/reference/cutover-runbook.md` uses this
distinction explicitly when sequencing a cutover.

## Events [`sendevent -E` reference, `research/autosys-12.0/commands.txt`]

`_lib.autosys_jil.history.MANUAL_INTERVENTION_EVENTS` is the subset flagged
`hidden_control_flow: true` below — these are the events `history_stats.py`'s
`manual_intervention()` counts per job and per source user (plan §11.1: manual-intervention
frequency is a REDESIGN/HITL signal).

| Event | Category | Manual-intervention signal? |
|---|---|---|
| `STARTJOB` | control | yes |
| `FORCE_STARTJOB` | control | yes |
| `KILLJOB` | control | yes |
| `RESTARTJOB` | control | yes |
| `RESUMEJOB` | control | yes |
| `SUSPENDJOB` | control | yes |
| `SEND_SIGNAL` | control | yes |
| `DELETEJOB` | control | yes |
| `CHK_BOX_TERM` | control | yes |
| `JOB_ON_HOLD` / `JOB_OFF_HOLD` | hold-ice | yes |
| `JOB_ON_ICE` / `JOB_OFF_ICE` | hold-ice | yes |
| `JOB_ON_NOEXEC` / `JOB_OFF_NOEXEC` | hold-ice | yes |
| `CHANGE_STATUS` / `CHANGE_PRIORITY` | state | yes |
| `REPLY_RESPONSE` | state | yes |
| `RESEND_EXTERNAL_STATUS` / `REFRESH_EXTINST` | state | yes |
| `SET_GLOBAL` | global | yes |
| `MACH_OFFLINE` / `MACH_ONLINE` / `MACH_UNQUAL_OFFLINE` | machine-resource | no |
| `RELEASE_RESOURCE` | machine-resource | no |
| `COMMENT` / `ALARM` / `STOP_DEMON` / `AGGREGATE` / `REFRESH_BROKER` / `REFRESH_AUTH_HOST` | admin | no |

Full page citations for every event live in `_lib/autosys_jil/registry/events.json`; several
resolve to `[AS p.2299]`, the `sendevent -E` option's summary enumeration rather than each
event's own dedicated write-up — a legitimate but coarse citation (same limitation noted for
`attributes.md`'s handful of sub-parameter defaults; acceptable for v1).
