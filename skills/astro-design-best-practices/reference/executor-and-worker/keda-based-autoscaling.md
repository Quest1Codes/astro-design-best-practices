# KEDA-Based Autoscaling

This file covers the specific mechanics behind the general autoscaling design principles in `autoscaling-design-for-bursty-batch-workloads.md` — how Astro's worker autoscaling actually computes worker count, which matters for tuning it correctly rather than just setting a min/max and hoping.

**Correction note**: an earlier draft of this file stated the polling interval as "10 seconds" and the scale-down cool-down as "5 minutes," both cited to a single Astronomer blog post. A Critic pass live-fetched that post and found it contains the formula below but **no interval or cool-down numbers at all** — those specific figures were unsupported. This version replaces them with the actual values found in the Apache Airflow Helm chart source, properly hedged given real ambiguity across sources (see below).

## Core mechanics

- The KEDA autoscaler for Airflow workers runs a SQL query against the metadata DB, at a configurable polling interval, to count running and queued tasks [F1].
- The formula: **number of workers = (queued tasks + running tasks) ÷ concurrency** (the per-worker concurrency setting configured on the worker queue) [F1][F2].
- The Apache Airflow Helm chart's own default values (read directly from `chart/values.yaml` in the `apache/airflow` repository) are `pollingInterval: 5` (seconds) and `cooldownPeriod: 30` (seconds) [F3].
- **Important, non-obvious distinction**: KEDA's `cooldownPeriod` only governs scaling the **last** worker down to **zero** — scaling down from N workers to N-1 (the common case during a tapering batch window, not the final worker) is handled by the underlying Kubernetes Horizontal Pod Autoscaler, not by `cooldownPeriod` at all [F2]. Some KEDA documentation states a 300-second (5-minute) default specifically for this scale-to-zero cool-down, which is a different number for a different, narrower situation than the chart's general `cooldownPeriod: 30` default [F2] — **`NEEDS_EXEC_CHECK`**: these two figures were not reconciled in this research pass (possibly different KEDA/chart versions, or `cooldownPeriod` and the scale-to-zero-specific cool-down are genuinely two different settings). Do not treat either specific number as settled; confirm against the actual deployed `ScaledObject` on the target Astro Deployment (`kubectl get scaledobject -o yaml`) rather than any documentation source, including this file, before tuning against it.

## {syn: F1,F2} What this formula means for tuning

Because worker count is a direct function of `(queued + running tasks) / concurrency`, the two levers that actually control how many workers you get for a given task volume are:

- **The per-worker `concurrency` setting**: this is the number workers actually scale against, so it's the primary tuning lever, not something to set once and forget. A concurrency of 1 means the formula essentially becomes "one worker per queued/running task" (maximum responsiveness, maximum pod overhead); a high concurrency means fewer, busier workers (less responsive to sudden bursts, less overhead).
- **Max worker count**: this is a hard ceiling on the formula's output, independent of how high `(queued+running)/concurrency` computes — sizing this too low silently caps throughput during a genuine peak even if the formula would otherwise scale further, and this failure mode is easy to miss since it doesn't produce an error, just slower drain of the queue.
- **The polling interval** [F3] determines how quickly the worker count *reacts* to a sudden change in queue depth — a genuinely sharp AutoSys-style batch-window ramp is better served by a shorter interval, within whatever range is actually configurable/supported on Astro; confirm the configurable range rather than assuming the OSS chart's default applies unchanged.

## Estate-scale callout

For a single dominant nightly batch window (the common AutoSys shape), a straightforward min/max range sized to that window's peak, with a moderate concurrency setting, is usually sufficient — don't over-engineer multiple KEDA-tuned queues for a single-peak workload. Multiple genuinely distinct peak periods (e.g. an overnight batch window plus a separate intraday near-real-time queue) are the actual signal for splitting into multiple independently-autoscaled worker queues, cross-referencing `worker-queue-segregation-mirroring-machine-groups.md`.

## Sources

- [F1] Astronomer Blog — How to Use KEDA as an Autoscaler for Airflow (SQL-query-based task counting, worker-count formula): https://www.astronomer.io/blog/the-keda-autoscaler/ (tier 1) — corrected per Critic pass: this source does **not** state a specific polling interval or cool-down duration; do not attribute either to it.
- [F2] KEDA project docs — ScaledObject specification (`cooldownPeriod` semantics, scale-to-zero-specific behavior, HPA governs N→N-1 scale-down): https://keda.sh/docs/2.20/reference/scaledobject-spec/ (tier 2 — KEDA upstream project docs, not Airflow/Astronomer-specific, but authoritative for KEDA's own mechanics)
- [F3] Apache Airflow Helm chart source — `chart/values.yaml`, `pollingInterval: 5` / `cooldownPeriod: 30` defaults: https://github.com/apache/airflow/blob/main/chart/templates/workers/worker-kedaautoscaler.yaml (tier 2 — read directly from source, not a docs page; the OSS Helm chart's defaults are not guaranteed to match Astro's managed KEDA configuration, hence the `NEEDS_EXEC_CHECK` above)
