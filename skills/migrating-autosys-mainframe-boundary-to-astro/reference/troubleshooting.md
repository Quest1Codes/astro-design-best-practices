# Troubleshooting: known failure classes

Seed entries below are anticipated from mainframe-boundary integrations; expand with actually-observed failures, fixing the class each time.

## "Scanner flagged a job that isn't actually mainframe-related"

**Cause**: a dataset-naming-convention heuristic (all-caps, dot-separated tokens) matched a distributed-side naming convention that happens to look similar but has nothing to do with z/OS — some shops use similar naming for non-mainframe systems.

**Fix the class**: don't let a flag alone drive any translation decision — Phase 2's platform-team confirmation step is mandatory, not optional, exactly because the scanner is a keyword heuristic. Record confirmed false positives back into the scanner's pattern list as a tightened rule going forward, not just as a one-off dismissal.

## "SFTP task succeeds but the mainframe job never picks up the file"

**Cause**: the AutoSys original delivered the file with a specific naming/timing convention (e.g., a `.tmp` write followed by an atomic rename, or delivery to a specific subdirectory the mainframe job's own watcher polls) that the migrated task's naive SFTP put didn't replicate — Gate B1 caught task-level success but not far-side pickup.

**Fix the class**: for any file-delivery boundary job, explicitly confirm the exact delivery convention (atomic rename pattern, target path, any completion marker file expected) with the platform team before translating, and encode it in the migrated task rather than assuming a plain file put is equivalent.

## "Firewall/DMZ change was requested but not confirmed against the actual deployed source IPs"

**Cause**: a change request was filed against a documented or assumed Astro egress range that didn't match what was actually in use at cutover time (ranges can change, or the target ended up being Hybrid instead of Hosted after all).

**Fix the class**: Gate B2 requires verifying the sign-off matches the actual deployed configuration at cutover time, not just at planning time — re-check immediately before cutover, the same discipline the on-prem-distributed skill applies to its own network gate.

## "Coexistence looked fine for weeks, broke on the one day that mattered"

**Cause**: validation ran during a normal period and never covered the integration's actual stress case (month-end, a specific business-calendar date the mainframe job treats specially).

**Fix the class**: Gate B3 explicitly requires validating across the integration's real cadence, not an arbitrary number of calendar days — identify the actual relevant cycle (from the core skill's calendar analysis, `reference/calendars-and-scheduling.md` in the core skill) before declaring the validation window sufficient.

## "Connect:Direct CLI wrapper works interactively but fails when scheduled"

**Cause**: the CLI wrapper (per `reference/operator-mapping.md`) depended on an interactive session's environment (a profile, an already-authenticated session) that isn't present when Airflow invokes it non-interactively from a task.

**Fix the class**: test the wrapper exactly as the scheduled task will invoke it (same environment, same auth flow, non-interactively) during the trial phase, not via a manual interactive run that implicitly relies on session state a scheduled run won't have.
