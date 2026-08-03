# Global variables and `%%variable%%` substitution → Airflow templating

AutoSys jobs reference shared values via `%%variable_name%%` tokens substituted into attributes like `command:` at run time. Sources of these values vary by shop: some are set centrally (global variables maintained via WCC or a `GLOBAL.variable_name` convention), some are box-scoped (a variable meaningful only within one box's children), and some are populated by a preceding job via `sendevent -E CHANGE_STATUS` or similar runtime mechanisms.

**Verify which mechanism is actually in play before translating** — this is one of the areas most likely to vary by AutoSys version and shop convention; do not assume a single global-variable syntax applies estate-wide without checking the export.

## Translation approach

| Source pattern | Airflow target | Disposition |
|---|---|---|
| A fixed value substituted into a command at every run | Airflow `Variable` (`Variable.get(...)`) or, if it never changes across environments, a plain Python constant/`params` default | MECH |
| A value that differs per environment (dev/test/prod) | Airflow `Variable` scoped per Deployment, or an Astro Environment Manager variable, resolved via Jinja templating (`{{ var.value.x }}`) in the task | MECH |
| A value set by an upstream job for a downstream job to consume within the same run | XCom (`ti.xcom_push`/`xcom_pull`), scoped to the DAG run — this is the correct replacement for "job A sets it, job B in the same box reads it" | MECH |
| A value that persists across runs (a counter, a last-processed watermark) | Airflow `Variable` used as external state, or better, a proper external store (the job's own database/state table) if the value represents business state rather than orchestration state | JUDG — prefer moving genuine business state out of orchestrator variables entirely; note this as an improvement, not a strict requirement, in the report |
| Runtime job templating (one JIL "template" job cloned N times via `sendevent`/scripted `jil` generation) | Airflow dynamic task mapping (`.expand(...)`) | REDESIGN — the cloning logic has to be reconstructed as a mapping input, not transliterated line-by-line |

## What NOT to do

Do not hardcode a `%%variable%%`'s *current* observed value into the migrated DAG as a literal. That silently converts a parameter into a constant and is exactly the kind of undocumented semantic delta the hard rules in `SKILL.md` forbid — even if it happens to produce identical output on the day of migration.
