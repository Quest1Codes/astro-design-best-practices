# One-Off and Ad-Hoc Job Design

AutoSys handles a one-time job the same way as any other job — insert it, let it run once (or force-start it via `sendevent`), then leave it defined or delete it. Airflow's model separates "the DAG structure" from "this particular run's inputs" more explicitly, which changes how a genuinely one-off task should be designed rather than just translated.

## Core mechanics

- **Params** are Airflow's mechanism for runtime configuration passed into a DAG at trigger time [F1].
- When a DAG is triggered manually (via UI or API) rather than by its schedule, its Params can be modified for that specific run before the run starts — this is the "Trigger DAG w/ config" flow [F2].
- The trigger form for entering config values was hidden from the UI by default starting in Airflow 2.7.0, but the underlying functionality is unchanged and can be restored via the `show_trigger_form_if_no_params` setting [F2]. **Resolved during Critic review**: a fresh-context Critic pass independently re-searched this and confirmed the setting is still current as of the target Airflow 3.x line — closing the `NEEDS_EXEC_CHECK` this file originally carried on it.
- Inside a task, the passed configuration is available via `params` in the task context, or via `dag_run.conf` [F3].
- Manually-triggered runs have their Params fixed at trigger time (calculated once, shown on the trigger UI, then locked in for that run) — this differs from how a scheduled run's Params are evaluated [F1].

## {syn: F1,F2,F3} Design guidance

For an AutoSys job that only ever ran as a genuine one-off (force-started once, not on any recurring schedule): give it its own DAG with `schedule=None` and a `params` schema describing whatever inputs it needs, rather than folding it into a DAG-factory config meant for recurring boxes. This keeps the DAG-factory's per-box config schema (`dag-factory-pattern-for-large-estates.md`) clean — a one-off job's inputs are supplied at trigger time via Params, not baked into a static factory config record the way a recurring job's schedule/dependencies are.

For an AutoSys job that's *usually* scheduled but occasionally needs an ad-hoc manual re-run with different inputs (not just a retry of the same run): design its `params` schema up front as part of the regular translation, even though the recurring/scheduled runs won't typically override the defaults — this avoids having to retrofit a Params schema later purely to support the occasional ad-hoc case.

## What NOT to do

Do not model a genuinely one-off AutoSys job as a permanently-scheduled DAG that's simply left paused after its one run — this misrepresents its nature in the DAG-factory config/inventory (which should be tracking recurring boxes) and in any estate-wide reporting derived from that inventory (job counts, schedule density) that assumes DAGs correspond to recurring work.

## Sources

- [F1] Apache Airflow docs — Params (manually-triggered vs. scheduled-run Param evaluation): https://airflow.apache.org/docs/apache-airflow/2.4.0/concepts/params.html (tier 2 — note: this specific doc version is 2.4.0; core Params behavior is stable across 2.x/3.x but re-verify against the target Airflow 3 Params doc before treating version-specific details as current)
- [F2] Community source (Airflow blog, `blog.manugarri.com`) — "Trigger DAG w/ config" UI history and `show_trigger_form_if_no_params`: sourced during this research pass, not an Astronomer/Apache primary doc. Treat the underlying capability (manual trigger + config) as solid (corroborated by F1/F3), the specific UI-setting name/version as **`NEEDS_EXEC_CHECK`** against the current target Airflow 3 version.
- [F3] Community source — accessing `params`/`dag_run.conf` in task context: general, widely-corroborated Airflow pattern, not sourced to one authoritative page in this pass.
