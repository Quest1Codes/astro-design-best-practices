# Cutover waves

## Grouping principle

Group machines/jobs into waves by shared risk and shared blast radius, not by convenience of alphabetical order or arbitrary batch size. Good grouping signals, in rough priority order:

1. **Team ownership** — a wave should belong to one team where possible, so there's a single point of contact who can validate the wave's own jobs and make the go/no-go call for it.
2. **Business calendar** — jobs sharing a `run_calendar` (e.g., all month-end jobs) are natural to move together and test together against the same calendar edge cases.
3. **Shared machine** — jobs on the same physical/logical machine often share the fate of that machine's topology decision (Hosted/Hybrid/bridge) and should move in the same wave rather than splitting a machine's jobs across waves arbitrarily.
4. **Dependency order** — a wave containing a job should also contain (or have already migrated) everything it depends on via `condition:` strings; migrating a downstream job before its upstream creates a broken dependency mid-wave.

## Wave sequencing

- **First wave: lowest risk, highest learning value.** Pick a machine group that's Hosted-eligible (simplest topology decision), has few cross-machine conditions, and isn't on the critical path for a business-critical SLA. The goal is validating the whole pipeline (topology decision → secrets → network → capacity → cutover → rollback) on something survivable if wrong.
- **Middle waves: the bulk of the estate**, ordered by dependency and team readiness once the first wave's lessons are folded into `reference/troubleshooting.md`.
- **Last waves: highest risk / most Hybrid-or-bridge-heavy groups**, migrated once the process is proven and any bridge-only exceptions have documented, agreed timelines.

## Per-wave cutover mechanics

1. Confirm the wave's machine groups are all `piloted` (per `SKILL.md`'s state machine) before scheduling a cutover date.
2. Put the AutoSys jobs in the wave `ON_ICE` (or the box-level equivalent) at the agreed cutover time; unpause the corresponding Airflow DAGs.
3. Run the first live cycle side by side where feasible (AutoSys job frozen but not deleted, Airflow DAG live) — if a true side-by-side isn't feasible for a time-sensitive job, at minimum keep the AutoSys job definition intact and `OFF_ICE`-able for fast rollback.
4. Rollback path: `OFF_ICE` the AutoSys job(s), pause the Airflow DAG(s). This must be tested — not just described — before the first real wave, ideally during the Phase 4 trial.
5. Only after a wave has run clean for an agreed number of cycles (matching its actual schedule — a monthly job needs a longer soak than a daily one) does it move to `complete`; don't decommission the AutoSys definition until then.

## What "clean" means

Not just "didn't error." Confirm output parity (per the core skill's validation gate, executed from the new location), confirm alerting actually fired correctly when tested, and confirm no downstream consumer of the job's output was surprised by a timing or format change. A wave that ran without exceptions but silently changed output shape is not clean.
