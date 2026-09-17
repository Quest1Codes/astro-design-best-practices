# KEDA-Based Autoscaling

This file covers the specific mechanics behind the general autoscaling design principles in `autoscaling-design-for-bursty-batch-workloads.md` — how Astro's worker autoscaling actually computes worker count, which matters for tuning it correctly rather than just setting a min/max and hoping.

**Correction note**: an earlier draft of this file stated the polling interval as "10 seconds" and the scale-down cool-down as "5 minutes," both cited to a single Astronomer blog post. A Critic pass live-fetched that post and found it contains the formula below but **no interval or cool-down numbers at all** — those specific figures were unsupported at the time. This version resolves the numbers against Astro's own current product docs rather than the generic upstream Airflow Helm chart, which is the correct source for what Astro-managed Deployments actually do (see the resolution note below).

## Core mechanics

- The KEDA autoscaler for Airflow workers runs a SQL query against the metadata DB, at a configurable polling interval, to count running and queued tasks [F1].
- The formula: **number of workers = (queued tasks + running tasks) ÷ concurrency** (the per-worker concurrency setting configured on the worker queue) [F1][F4][F5].
- On Astro Hosted (both the Celery executor and the Astro executor), KEDA recomputes this formula **every 10 seconds** [F4][F5]. This is an Astro-specific, currently-documented figure, not the OSS Helm chart's `pollingInterval` default.
- **Scale-down cool-down is 5 minutes (300 seconds) on Astro**, and — unlike the ambiguity flagged in the earlier draft — this is **not** limited to the last-worker-to-zero case: Astro's own docs state plainly that "when KEDA determines that it can scale down a worker, it waits for five minutes after the last running task on the worker finishes before terminating the worker Pod" [F4][F5]. The same 300-second default is confirmed independently for Remote Execution Agent workers via the `keda.cooldownPeriod` Helm value [F6].
- **Resolution of the earlier `NEEDS_EXEC_CHECK`**: the OSS Airflow Helm chart's generic `cooldownPeriod: 30` default [F3] is **not what Astro-managed Deployments run** — Astro's own product docs (tier 1, Astro-specific) consistently document 300s across three separate surfaces (Celery executor, Astro executor, Remote Execution Agent workers), which supersedes the generic chart default. Treat 300s (5 minutes) as the correct figure for Astro; the 30s chart value only applies to a self-managed OSS Helm install that hasn't had this value overridden.

## {syn: F1,F2} What this formula means for tuning

Because worker count is a direct function of `(queued + running tasks) / concurrency`, the two levers that actually control how many workers you get for a given task volume are:

- **The per-worker `concurrency` setting**: this is the number workers actually scale against, so it's the primary tuning lever, not something to set once and forget. A concurrency of 1 means the formula essentially becomes "one worker per queued/running task" (maximum responsiveness, maximum pod overhead); a high concurrency means fewer, busier workers (less responsive to sudden bursts, less overhead).
- **Max worker count**: this is a hard ceiling on the formula's output, independent of how high `(queued+running)/concurrency` computes — sizing this too low silently caps throughput during a genuine peak even if the formula would otherwise scale further, and this failure mode is easy to miss since it doesn't produce an error, just slower drain of the queue.
- **The polling interval** (10 seconds on Astro [F4][F5]) determines how quickly the worker count *reacts* to a sudden change in queue depth — this is fast relative to most AutoSys-style batch-window ramps, so it's rarely the bottleneck. Astro's docs don't currently describe this as a per-Deployment tunable; **`NEEDS_EXEC_CHECK`** if a genuinely sharp ramp motivates confirming whether it can be overridden.

## Estate-scale callout

For a single dominant nightly batch window (the common AutoSys shape), a straightforward min/max range sized to that window's peak, with a moderate concurrency setting, is usually sufficient — don't over-engineer multiple KEDA-tuned queues for a single-peak workload. Multiple genuinely distinct peak periods (e.g. an overnight batch window plus a separate intraday near-real-time queue) are the actual signal for splitting into multiple independently-autoscaled worker queues, cross-referencing `worker-queue-segregation-mirroring-machine-groups.md`.

## Sources

- [F1] Astronomer Blog — How to Use KEDA as an Autoscaler for Airflow (SQL-query-based task counting, worker-count formula): https://www.astronomer.io/blog/the-keda-autoscaler/ (tier 1) — corrected per Critic pass: this source does **not** state a specific polling interval or cool-down duration; do not attribute either to it.
- [F2] KEDA project docs — ScaledObject specification (`cooldownPeriod` semantics, scale-to-zero-specific behavior, HPA governs N→N-1 scale-down): https://keda.sh/docs/2.20/reference/scaledobject-spec/ (tier 2 — KEDA upstream project docs, not Airflow/Astronomer-specific, but authoritative for KEDA's own mechanics)
- [F3] Apache Airflow Helm chart source — `chart/values.yaml`, `pollingInterval: 5` / `cooldownPeriod: 30` defaults: https://github.com/apache/airflow/blob/main/chart/templates/workers/worker-kedaautoscaler.yaml (tier 2 — read directly from source; **these are the generic OSS chart defaults, not what Astro-managed Deployments run** — see F4/F5/F6, which supersede this for anything running on Astro)
- [F4] Astronomer Docs — Configure the Celery executor, "Celery worker autoscaling logic" (10-second KEDA polling interval; 5-minute/300s scale-down cool-down after a worker's last task finishes): https://www.astronomer.io/docs/astro/celery-executor#celery-worker-autoscaling-logic (tier 1)
- [F5] Astronomer Docs — Astro executor, "Astro worker autoscaling logic in Hosted execution mode" (same 10-second polling interval and 5-minute cool-down, confirmed independently for the Astro executor): https://www.astronomer.io/docs/astro/astro-executor#astro-worker-autoscaling-logic-in-hosted-execution-mode (tier 1)
- [F6] Astronomer Docs — Autoscale Remote Execution Agent workers on queue depth, "Scale down without task failures" (`keda.cooldownPeriod` default `300`): https://www.astronomer.io/docs/astro/remote-execution/remote-agents-autoscale-workers#scale-down-without-task-failures (tier 1)
