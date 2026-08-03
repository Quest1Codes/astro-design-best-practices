# Autoscaling Design for Bursty Batch Workloads

AutoSys estates are almost universally bursty by nature — heavy overnight/end-of-day batch windows, near-idle stretches between them. AutoSys itself doesn't autoscale (its agents are fixed, pre-provisioned machines); the burst is simply absorbed by however much fixed capacity was provisioned, with jobs queuing if capacity is insufficient. Astro's worker autoscaling is a genuinely new capability the source estate never had — worth designing deliberately rather than defaulting to fixed sizing out of habit.

## Core mechanics

- Astro worker queues autoscale based on a min/max worker-count range and a per-queue concurrency setting [F1].
- The underlying autoscaling mechanism (KEDA — see `keda-based-autoscaling.md` for the specific formula, polling interval, and an important correction about cool-down behavior found during Critic review) recalculates the needed worker count on a polling interval and includes cool-down behavior intended to avoid thrashing on a brief lull [F1]. **Corrected per Critic pass**: an earlier draft of this sentence cited a specific interval/cool-down framing to [F2] (the KEDA blog post), which does not actually state those specifics — see `keda-based-autoscaling.md` for the properly-sourced (and appropriately hedged) version of these numbers; this file only relies on the general behavior, not any specific figure.

## {syn: F1} Design guidance — sizing for AutoSys-shaped burst patterns

- **Min workers**: size to whatever steady, non-batch-window load exists (ad-hoc triggers, small recurring jobs outside the main batch window) — not zero, unless the queue is genuinely idle outside batch windows and a few minutes of cold-start latency at the start of the window is acceptable.
- **Max workers**: size to the estate's actual peak concurrent job count during its heaviest batch window, not an arbitrary round number — this is directly derivable from the assessment data already produced by the simulator's own dependency-wave analysis (peak concurrent jobs per wave), not a fresh estimate.
- **Concurrency setting per worker**: this determines how many workers the min/max range translates to for a given task volume — a lower per-worker concurrency spreads the same task volume across more, smaller workers (finer-grained scaling, more pod overhead); a higher per-worker concurrency uses fewer, busier workers (coarser scaling, less overhead). For bursty batch workloads with a sharp ramp, prefer the finer-grained end of this tradeoff, since it lets the autoscaler track a sharp burst more responsively than a small number of large workers can.

## Estate-scale callout

At small-to-medium scale, one autoscaling worker queue tuned to the overall batch-window peak is usually sufficient. At large scale, cross-reference `worker-queue-segregation-mirroring-machine-groups.md` — if the estate has genuinely distinct functional worker queues, each needs its own min/max sizing based on *its* peak, not a single estate-wide number, since different functional categories of work don't necessarily peak at the same time within the batch window.

## What AutoSys operators should unlearn

There is no equivalent of "provision enough fixed machines to survive the worst batch night" to reason about anymore — capacity that was a static, manually-sized fleet becomes a range with real cost implications at both ends (too-low max still causes queuing delays during genuine peaks; too-high max is paying for capacity that's rarely used). This is a genuinely new tuning surface, not a re-labeling of an old one.

## Sources

- [F1] Astronomer Docs — Configure worker queues (min/max worker autoscaling, concurrency setting): https://www.astronomer.io/docs/astro/configure-worker-queues (tier 1)
- [F2] Astronomer Blog — How to Use KEDA as an Autoscaler for Airflow (scale-down cool-down behavior): https://www.astronomer.io/blog/the-keda-autoscaler/ (tier 1)
