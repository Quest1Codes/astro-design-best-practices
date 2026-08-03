# Capacity and scaling

## Why job count is not a sizing number

`agent_fleet_inventory.py` reports a `job_count` per machine — this is a floor, never a final worker pool or node group size. AutoSys agents on a shared machine ran jobs subject to that machine's own OS-level scheduling and resource limits; the number that actually matters for sizing Astro workers/node pools is **peak concurrency** (how many of that machine group's jobs were ever actually running at the same time), not the total count of distinct jobs that ever reference it.

## Getting real concurrency data

Pull actual historical run data before finalizing any capacity number:

- `autorep -J <job> -q` history (start/end timestamps) for the jobs in a machine group, over a representative window (ideally including the estate's actual peak period — month-end, quarter-end, whatever the business calendar's heaviest day is).
- Overlap these windows to compute observed peak concurrent job count per machine group, per hour-of-day, per day-of-week — capacity planning should be sized to the peak, with headroom, not the average.
- Where historical data isn't available (a new estate, or history not retained long enough), say so explicitly in the report rather than presenting a job-count-derived guess as a real number — mark it `capacity: estimated (no historical data)` and flag it for revisit after a few weeks of real Astro-side metrics.

## Sizing the target

| AutoSys pattern | Astro target |
|---|---|
| Machine group with steady, moderate concurrency | A worker queue / node pool sized to observed peak concurrency + headroom (a starting multiplier like 1.3-1.5x is reasonable absent other guidance, but say it's a starting point, not a guarantee) |
| Machine group with sharp bursts (e.g., a nightly batch window) | Autoscaling (KEDA-based, or Astro's managed autoscaling) rather than a fixed pool sized for the burst — a pool permanently sized for the burst wastes resources the rest of the day |
| Machine group with hard resource limits per job (e.g., a job that needs a specific memory floor) | Explicit resource requests/limits on the KubernetesPodOperator / task, not just concurrency-based pool sizing |

## Validating the sizing after cutover

Capacity numbers are a hypothesis until observed post-cutover. Monitor actual queue times and worker utilization for the first several cycles after a wave goes live, and revise the pool/node-group size from real data rather than treating the pre-migration estimate as final — this is worth stating plainly in the final report as a follow-up item, not something the report should imply is already settled.
