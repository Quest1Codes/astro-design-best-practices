---
topic: global-variables-and-templating
family: migration
skill: migrate-jil-to-airflow-translation
verified_against:
  airflow: "3.3.1"
  astro_runtime: "3.3-2"
  autosys: "12.0"
  autosys_doc_pages: [2343, 2440]
last_verified: 2026-09-17
confidence: mixed
signals: [credential_hits]
---

# Global variables and `%%variable%%` substitution → Airflow templating

REWRITE ← the pre-refactor skill's 19-line version, extended with the four usage patterns
`_lib.autosys_jil.commands.analyze()`'s `global_var_refs[]` actually finds in practice, and how
they're produced/consumed.

AutoSys jobs reference shared values via `%%variable_name%%` tokens substituted into attributes
like `command:` at run time. **Verify which mechanism is actually in play before translating** —
this varies by shop convention more than almost any other JIL surface.

## The four uses found by `command_analysis.py`

| Use | How to tell | Airflow target | Disposition |
|---|---|---|---|
| **Config** — a fixed value substituted at every run | Same value across every job referencing it; cross-check `autorep -G` export | Airflow `Variable` (`Variable.get(...)`), or a plain constant/`params` default if truly static | MECH |
| **Environment targeting** — differs per dev/test/prod | Name pattern often includes the environment, or the value is instance-specific | Airflow `Variable` scoped per Deployment, or an Astro Environment Manager variable, via Jinja (`{{ var.value.x }}`) | MECH |
| **Inter-job state** — job A sets it (`sendevent -E SET_GLOBAL` [AS p.2343], found as a `hidden_control_flow` edge by `command_analysis.py`), job B in the same run reads it | The variable's producer is another job in the same box/run, not a static config source | XCom (`ti.xcom_push`/`xcom_pull`), scoped to the DAG run — the correct replacement for this exact pattern | MECH |
| **Secrets** — a credential value substituted into a command | Flagged by `_lib.autosys_jil.commands.analyze()`'s `credential_hits` (pattern name only, value never captured) | An Airflow Connection / the target secrets backend (`migrate-astro-platform-buildout/reference/secrets-and-identity.md`) — never a `Variable`, and never copy the observed value forward | MECH once the secrets backend is chosen |

A value that persists across runs (a counter, a last-processed watermark) is a fifth, rarer
pattern: prefer moving genuine business state out of orchestrator variables into the job's own
database/state table, and note this as an improvement, not a strict requirement, in the report
(JUDG).

## Runtime job templating (REDESIGN)

One JIL "template" job cloned N times via `sendevent`/scripted `jil` generation →
Airflow dynamic task mapping (`.expand(...)`). The cloning logic has to be reconstructed as a
mapping input, not transliterated line-by-line. `command_analysis.py`'s `template_clusters`
(≥5-member near-duplicate command groups) is the mechanical signal that a job family is a
dynamic-task-mapping candidate — check it before assuming a set of similar jobs was hand-written
independently.

## What NOT to do

Do not hardcode a `%%variable%%`'s *current* observed value into the migrated DAG as a literal.
That silently converts a parameter into a constant and is exactly the undocumented semantic
delta the hard rules forbid — even if it happens to produce identical output on the day of
migration. This applies doubly to secrets: never write an observed credential value into
generated code, a data file, or the manifest itself (`manifest.redact()` already prevents the
latter by default).
