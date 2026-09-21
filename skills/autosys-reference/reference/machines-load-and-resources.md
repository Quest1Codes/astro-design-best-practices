---
topic: machines-load-and-resources
family: knowledge
skill: autosys-reference
verified_against:
  autosys: "12.0"
  autosys_doc_pages: [2547, 2548, 2861, 2867, 2868, 2872, 2873, 2874, 2880, 2881, 2882, 2887, 2888]
last_verified: 2026-09-17
confidence: cited
signals: [job_load_present, virtual_resources]
---

# Machines, load, and virtual resources

## Real vs. virtual machines, and `type` [AS p.2861, p.2874]

`insert_machine` defines either a real machine (one physical/virtual host running an agent) or a
virtual machine (a named pool of component real machines, listed via repeated `machine:` lines
inside the block). The `type` attribute values, current vs. legacy:

| `type` | Meaning | Status |
|---|---|---|
| `a` | Agent-based (current) | Current |
| `n`, `l`, `L`, `r` | Legacy remote-agent types | Deprecated — pre-dates the Workload Automation Agent; a machine still using one of these is a decommission or agent-upgrade candidate before migration, not something to containerize as-is |

`_lib.autosys_jil.models.Machine.type` carries the raw value uninterpreted;
`migrate-jil-to-airflow-translation/reference/job-types/core-cmd-box.md`'s Windows options and
`legacy-machine-type-inventory-cleanup.md` (knowledge KB) both key off it.

## `max_load` / `factor` / `job_load` arithmetic [AS p.2547-2548, p.2867, p.2872]

Three independent numbers, all **arbitrary, user-defined scales** (no fixed unit):

- **`max_load`** (machine, `insert_machine`/`update_machine`): the load ceiling a machine can
  reasonably carry. `0` = unlimited; unset = AutoSys does not limit load on that machine at all
  [AS p.2872].
- **`job_load`** (job, any type): the relative load a job consumes. **Default is `0`, meaning
  "unrestricted" — a job with no `job_load` set runs without any load check whatsoever**
  [AS p.2548]. This is the opposite of a conservative default; an estate can have `max_load`
  carefully tuned per machine and still see it ignored wholesale if `job_load` was never set on
  the jobs.
- **`factor`** (machine, real machines and virtual-machine components only, not `type` `c`/`u`):
  a multiplier applied to available CPU cycles — `(Available CPU Cycles) × factor = Relative
  Processing Power`. When a job names multiple candidate machines, AutoSys picks the one with the
  highest calculated usage; a `factor` of `0` doesn't disqualify a machine, it's only chosen when
  every other candidate is *also* `0` [AS p.2867]. Default `1.0`; range `0-1024`, ≤ 2 decimal
  places [AS p.2868].

**Priority interaction** [AS p.2548]: default job `priority` is `0`, which means "run
immediately, ignore load units" — `job_load` only actually gates scheduling once `priority` is
set to `1` or higher. A job with `job_load` set but `priority` left at the default is not really
load-managed. **`priority`/`job_load` cannot be used together with a user-defined load-balancing
script in the `machine:` attribute** [AS p.2548] — check for that before trusting either number.

A forced start (`sendevent -E FORCE_STARTJOB`) runs the job even if it would exceed the target
machine's `max_load` [AS p.2548] — one more reason `history.manual_intervention()`'s
`FORCE_STARTJOB` count matters for capacity assessment, not just for the REDESIGN/HITL signal it
already feeds into scoring.

{syn: this is the exact input `assess-astro-target-architecture/scripts/size_target.py`'s
`pool_slots()` uses — `max_load` sums to a Pool's total capacity, `job_load` to each task's
`pool_slots` consumption, `[AS p.2872, p.2547]`. Trust these numbers only where `job_load` was
actually set **and** `priority >= 1` on the relevant jobs; otherwise treat the estate as
effectively unmanaged-load and size from `history.concurrency_curve` instead.}

## Machine wait states [`reference/job-states-and-events.md`]

- **`PEND_MACH`** — the target machine is offline/unreachable.
- **`QUE_WAIT`** — eligible to run, waiting on `max_load`/priority.
- **`RESWAIT`** — waiting on a virtual resource (below).

## Virtual resources [AS p.2880-2888]

`insert_resource` defines a named, machine-scoped (or global) countable resource a job can
depend on via the `resources:` job attribute. `res_type` has **three** values, not two:

| `res_type` | Behavior |
|---|---|
| `D` | **Depletable** — consumed permanently on use; must be replenished via `update_resource` to reuse. |
| `R` | **Renewable** — borrowed for the job's duration, returned on completion (or held for manual release, per the job's dependency definition). |
| `T` | **Threshold** — a sizing gate: only jobs requesting `<=` the threshold amount are submitted; units are never actually removed from the pool. |

A resource's `res_type` cannot be changed via `update_resource` — changing it requires delete +
re-add [AS p.2887]. `_lib.autosys_jil.models.Resource.res_type` carries the raw value; treat `D`
and `R` as the two that map naturally onto an Airflow `pool` (a depletable-style pool needs an
explicit replenishment step modeled somewhere, a renewable one maps directly), and `T` as closer
to a `pool_slots` ceiling than either.
