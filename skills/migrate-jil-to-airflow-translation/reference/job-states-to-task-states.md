---
topic: job-states-to-task-states
family: migration
skill: migrate-jil-to-airflow-translation
verified_against:
  airflow: "3.3.1"
  astro_runtime: "3.3-2"
  autosys: "12.0"
  autosys_doc_pages: [2914, 2915, 2916, 2917, 2919, 2920, 2923]
last_verified: 2026-09-17
confidence: mixed
signals: []
---

# AutoSys state → Airflow TaskInstance state

NEW. Full AutoSys-side state facts (terminal flags, `ON_HOLD`/`ON_ICE`/`ON_NOEXEC` semantics) are
already cited in `autosys-reference/reference/job-states-and-events.md` — this file adds the
translation prose only; read that file first for the source facts.

| AutoSys state | Airflow TaskInstance state | Translation note |
|---|---|---|
| `INACTIVE` | no TI / `none` | Not yet eligible; no Airflow equivalent needed beyond "not scheduled yet" |
| `ACTIVATED` | `scheduled` | Box started, job waiting on its own conditions |
| `STARTING` | `queued` | |
| `RUNNING` | `running` | |
| `SUCCESS` | `success` | Subject to `max_exit_success`/`success_codes` — see `reference/alerting-and-sla.md` |
| `FAILURE` | `failed` | |
| `TERMINATED` | `failed` (killed) / a custom `shutdown`-style marker if the distinction matters operationally | See `reference/alerting-and-sla.md`'s `alarm_if_terminated` row — Airflow doesn't distinguish killed-from-failed the same way by default |
| `RESTART` | `up_for_retry` | `n_retrys` → `retries`; see the job-type family files for per-type retry translation |
| `QUE_WAIT` | `queued` (pool/`max_load` wait) | See `autosys-reference/reference/machines-load-and-resources.md`; `assess-astro-target-architecture/scripts/size_target.py`'s `pool_slots()` sizes the Airflow-side equivalent |
| `WAIT_REPLY` | **no equivalent** | Manual-reply jobs need a HITL (human-in-the-loop) operator or a REDESIGN — see `astro-design-best-practices/reference/scheduler-and-dag/human-in-the-loop-operators-for-wait-reply.md` (new KB topic, Phase 2) |
| `ON_HOLD` | DAG paused / task cleared-to-`none` | **Cutover primitive** — dependents wait. See `migrate-parallel-run-and-cutover/reference/cutover-runbook.md` |
| `ON_ICE` | DAG paused **and** downstream treats as success | **Cutover primitive**, semantics differ from `ON_HOLD` — dependents proceed. Same cutover-runbook reference |
| `ON_NOEXEC` | `skipped` while marking success for dependents | |
| `PEND_MACH` | `queued` (no worker available) | |
| `SUSPENDED` | **no equivalent** | Document as an operational gap if the estate relies on `SUSPENDJOB` semantics beyond a simple pause |
| `RESWAIT` | `queued` waiting on a pool slot | Virtual-resource wait; see `autosys-reference/reference/machines-load-and-resources.md`'s resource types |
| `REFRESH_DEPENDENCIES` / `REFRESH_FILEWATCHER` | n/a (transient) | No translation needed |

## `WAIT_REPLY` and human-in-the-loop jobs

A job whose condition or workflow expects a manual `REPLY_RESPONSE` (`sendevent`,
[AS p.2919]) — or a mainframe `ZOSM` (z/OS Manual) job, or a `PAREQ` (Process Automation Start
Request Form) — is the clearest REDESIGN signal in the state model: there is no default Airflow
task that waits for a human click. Options, in order of preference for a 3.3+ target: a
purpose-built HITL operator if the estate's scale justifies building one, or a deferrable sensor
polling an external approval system, or (least preferred) an explicit manual runbook step with
the DAG paused until acted on. Never scaffold a stub that pretends this is automated.
