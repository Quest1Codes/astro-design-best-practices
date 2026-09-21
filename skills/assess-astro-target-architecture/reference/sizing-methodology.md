---
topic: sizing-methodology
family: assessment
skill: assess-astro-target-architecture
verified_against:
  airflow: "3.3.1"
  astro_runtime: "3.3-2"
  autosys: "12.0"
  autosys_doc_pages: [2547, 2548, 2872]
last_verified: 2026-09-17
confidence: mixed
signals: [job_load_present]
---

# Sizing methodology

REWRITE ← `migrate-topology-onprem-distributed/reference/capacity-and-scaling.md` +
`assess-migration-complexity-scoring`'s history-driven approach: the formulas below are now
implemented as code (`scripts/size_target.py`), not prose — this file explains the formulas and
gives worked examples from the fixture estate; the function docstrings carry the citations.

**Mandatory input**: a history concurrency curve (`history_stats.py`, itself needing real
`run_history`/`event_archive` artifacts). Job-count-only sizing is explicitly labeled `basis:
floor` everywhere it's used — a floor is a lower bound, never presented as a real capacity
number. See `assess-estate-inventory/reference/reading-the-inventory.md`'s "History" section.

## `pool_slots()` — [AS p.2547-2548, p.2872]

```
pool_slots(machine.max_load, sum(job.job_load for jobs referencing that machine))
```

Trustworthy **only** where `job_load` is set on the referencing jobs **and** `priority >= 1` —
per [AS p.2548], the default priority (`0`) means "run immediately, ignore load units," so
`job_load` is silently unenforced without an explicit priority. `size_target.py` marks each
machine's result `basis: observed` only when this condition holds; otherwise `basis: floor` with
an explicit note.

**Worked example** (fixture estate): a machine with `max_load: 100` and three referencing jobs
each `job_load: 10` sums to 30 — well under capacity, `basis: observed` if those jobs also set
`priority >= 1`. If none set `priority`, the same numbers are reported `basis: floor` with the
note that `max_load` is likely not actually enforced for that machine.

## `worker_fleet()`

```
worker_fleet(concurrency_curve) -> {min, max}
```

`min = peak_concurrency // 3`, `max = peak_concurrency * 1.3` — a starting-point heuristic
(PRACTITIONER JUDGMENT multipliers, not a cited formula), always `basis: floor` without a
`task_duration_p95` input, `basis: observed` with one. Never trust a `worker_fleet` result
computed from a job-count proxy in place of `concurrency_curve` — `size_target.py` refuses to
produce one in that case (`value: None`) rather than silently substituting a weaker number.

## `scheduler_size()` / `dag_processor_size()` / `triggerer_size()` / `db_tier()`

PRACTITIONER JUDGMENT thresholds throughout (small/medium/large bands on DAG count, task count,
schedule density, sensor count, job count, and history-row volume) — this refactor did not have
access to a current, cited Astronomer sizing table when these were authored. Treat the resulting
band as a conversation starter with Astronomer's own sizing guidance, not a substitute for it.

`triggerer_size()`'s `sensor_count` input is the count of `FW`/`FT` job types in the estate — a
proxy for "how many jobs will likely translate to a deferrable sensor," not a precise count of
what `scaffold_dags.py` will actually emit (that number only exists once translation has run).

## What "floor" means in a report

Every `basis: floor` number in the report's sizing section must be presented as a lower bound
("at least this many workers," not "this many workers") — this is a structural label the scripts
attach automatically, but the report's prose still has to honor it; a `floor` number formatted
identically to an `observed` one in a table is a reporting defect, not just an imprecise
estimate.
