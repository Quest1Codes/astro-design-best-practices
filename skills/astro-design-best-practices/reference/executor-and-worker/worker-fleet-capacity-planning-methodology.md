# Worker Fleet Capacity-Planning Methodology

This file is about sizing the **worker fleet** — how many workers, what worker type, what min/max autoscaling bounds — from aggregate estate-wide job count and schedule density. It is **not** about per-machine unit translation (`max_load`/`job_load` → Pool slots, already covered in `reference/machine-load-and-virtual-resources/max-load-job-load-to-airflow-pools-sizing.md`) or scheduler/DAG-Processor sizing (already covered in `reference/cost-and-capacity-governance/capacity-planning-from-job-count-and-schedule-density.md`, the Small/Medium/Large/XL Deployment templates). Read this file for "how many workers, what type," not "how many pool slots" or "what scheduler tier."

## Why this is a different problem than AutoSys machine-fleet planning

{syn: F1} AutoSys's machine pool was provisioned once, largely statically — you sized the physical/VM fleet for peak load and it sat there, over-provisioned outside the peak window, because scaling a physical machine pool up and down per batch window wasn't practical. Astro worker queues autoscale continuously per queue [F1] — the planning question shifts from "how big is the fleet" to "what's the right min/max range and worker type per queue," since the fleet's actual size at any moment is a runtime function of current load, not a static provisioning decision.

## Core sizing mechanics

- Each worker queue autoscales between a **Min # Workers** and **Max # Workers** bound (defaults: min 1, max 10) [F2].
- Worker count is a direct function of load: **number of workers = (queued tasks + running tasks) ÷ concurrency**, recomputed on a polling interval — this is the same KEDA formula already documented in `reference/executor-and-worker/keda-based-autoscaling.md`; use that file's formula and figures, don't restate a different one here [F3].
- **Concurrency** (the per-worker task-slot setting) defaults to 16, and directly determines how many workers a given task volume produces via the formula above [F2].
- **Worker type** sets the resource ceiling per worker, not the task count directly — each worker type has both a **default task concurrency** and a **max task concurrency** [F4]:

| Worker Type | vCPU | Memory | Default task concurrency | Max task concurrency |
|---|---|---|---|---|
| A5 | 1 | 2 GiB | 5 | 15 |
| A10 | 2 | 4 GiB | 10 | 30 |
| A20 | 4 | 8 GiB | 20 | 60 |
| A40 | 8 | 16 GiB | 40 | 120 |
| A60 | 12 | 24 GiB | 60 | 180 |
| A120 | 24 | 48 GiB | 120 | 360 |
| A160 | 32 | 64 GiB | 160 | 480 |

[F4]

## {syn: F2,F3,F4} Methodology: from "N jobs, schedule density D" to a worker queue config

1. **Estimate peak concurrent task volume**, not total daily job count — this is the same schedule-density distinction `capacity-planning-from-job-count-and-schedule-density.md` makes for scheduler sizing, and it applies identically here: 500 jobs spread evenly across a day produce a very different peak from 500 jobs that all fire at the top of the hour. Use the estate's actual AutoSys box/calendar schedule to estimate the peak, not a flat daily average.
2. **Pick a worker type from expected per-task resource footprint**, not from job count — a fleet of many small A5 workers and a fleet of few large A60 workers can serve the same total concurrency; the choice depends on whether individual tasks are memory/CPU-heavy (favor fewer, larger workers) or numerous and light (favor more, smaller workers with higher concurrency headroom per worker).
3. **Set Concurrency** to the number of tasks you want a single worker to run in parallel before a new worker is added, bounded by the chosen worker type's max task concurrency [F4] — this is the same "primary tuning lever" role `keda-based-autoscaling.md` already assigns to Concurrency; don't re-derive separately, apply that file's tuning guidance here.
4. **Set Max # Workers** to `peak concurrent task volume ÷ Concurrency`, rounded up — sizing this too low silently caps throughput during a genuine peak without producing an error, the same failure mode already flagged in `keda-based-autoscaling.md`.
5. **Set Min # Workers** based on whether the queue has a genuinely idle period (AutoSys-shaped nightly-batch estates: min can be 0-1, since the queue is legitimately empty for hours) or needs a warm worker for latency reasons (min ≥ 1) [F5].

## Estate-scale callout

| Estate shape | Worker fleet approach |
|---|---|
| Single dominant nightly batch window (typical AutoSys estate) | One or two worker queues sized to that window's peak; low min-worker count, since idle daytime hours are genuinely idle — don't provision for 24/7 peak capacity. |
| Multiple distinct job populations with different resource profiles (e.g. light ETL checks + heavy nightly reconciliation jobs) | Separate worker queues per population, each independently sized per the methodology above — see `reference/executor-and-worker/worker-queue-segregation-mirroring-machine-groups.md` for *why* to segregate, this file for *how big* each resulting queue should be. |
| Estate-wide migration with no historical Airflow load data yet | Start from the AutoSys estate's own peak concurrent-job telemetry (if available) as the peak-concurrency input to step 4 above; treat the first weeks post-cutover as a calibration period and resize from actual Deployment Analytics rather than trusting the initial estimate long-term. |

## Sources

- [F1] Astronomer Docs — Configure worker queues, Hosted Deployment worker types (per-queue autoscaling architecture): https://www.astronomer.io/docs/astro/configure-worker-queues#hosted-deployment-worker-types (tier 1)
- [F2] Astronomer Docs — Astro executor, "Configure Astro worker scaling in Hosted execution mode" (Concurrency default 16; Min/Max Worker Count defaults 1/10): https://www.astronomer.io/docs/astro/astro-executor#configure-astro-worker-scaling-in-hosted-execution-mode (tier 1)
- [F3] This skill's own `reference/executor-and-worker/keda-based-autoscaling.md` — worker-count formula, polling interval, cool-down mechanics; deliberately not restated here to avoid a second, potentially drifting copy of the same formula.
- [F4] Astronomer Docs — Astro worker types (vCPU/memory/default and max task concurrency per worker type): https://www.astronomer.io/docs/astro/resource-reference-hosted#astro-worker-types (tier 1)
- [F5] Astronomer Docs — Create a sub-second worker queue, Min # Workers guidance ("Sub-second startup depends on having a worker already warm and ready, so scale-to-zero defeats the purpose") — cited for the general min-worker-for-latency principle, not the sub-second feature itself: https://www.astronomer.io/docs/astro/sub-second-pipelines#create-a-sub-second-worker-queue (tier 1)
