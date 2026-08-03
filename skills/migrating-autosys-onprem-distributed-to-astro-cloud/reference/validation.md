# Validation gates (topology-specific)

These are additive to the core skill's per-job validation gates (import, lint, execution, output parity, safe re-run). This skill adds environment/location-specific checks that a job-semantics-only migration wouldn't catch.

## Gate T1: Network reachability

From the actual target execution environment (a real Hosted worker/pod, or the actual Hybrid node — not a developer's laptop, not a guess), confirm every downstream system the machine group's jobs touch is reachable on the required port/protocol. Record the check per system, not just "network looks fine" for the whole group.

## Gate T2: Credential validity from the new location

Confirm the migrated Connection actually authenticates successfully *from the new location*. A credential valid from the old on-prem agent's network position can fail from a different network position (IP allow-listing, domain-join requirements) even with identical username/password — this is a distinct failure mode from Gate T1 and needs its own check.

## Gate T3: Environment parity

Confirm any local dependency the original machine silently provided is actually present in the new environment: the right interpreter/runtime version, required drivers/libraries, locale and timezone settings the job's output format depends on, and any mapped-drive-equivalent storage access. This is the gate most likely to surface a "worked in the trial, failed at cutover" gap if skipped — a trial run on a lightly-loaded pilot machine group can mask a dependency the pilot happened to have that a later wave's machine group doesn't.

## Gate T4: Capacity under real load

After a wave goes live, monitor actual queue times and worker/node utilization against the capacity estimate from `reference/capacity-and-scaling.md` for at least a few full cycles (matching the job's own schedule cadence). This gate doesn't block cutover, but it does block calling capacity planning `complete` for that machine group — record it as `piloted, capacity monitoring in progress` until real data confirms the sizing.

## Recording results

Same discipline as the core skill: each machine group's `topology_manifest.json` record should show which gates passed and when, not just a final status — this is what lets `scripts/status.py summary` distinguish a genuinely validated `complete` from one marked done on assumption.
