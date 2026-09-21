---
topic: database-sql-dbproc-dbmon-dbtrig-sqlagent
family: migration
skill: migrate-jil-to-airflow-translation
verified_against:
  airflow: "3.3.1"
  astro_runtime: "3.3-2"
  autosys: "12.0"
  autosys_doc_pages: [2549, 2551, 2457]
last_verified: 2026-09-17
confidence: mixed
signals: []
---

# Database: SQL, DBPROC, DBMON, DBTRIG, SQLAGENT

| Code | Default target | Disposition | Delta |
|---|---|---|---|
| `SQL` [AS p.2549] | `SQLExecuteQueryOperator` (`apache-airflow-providers-common-sql`) | MECH | None expected for a plain query/script execution |
| `DBPROC` [AS p.2551] | `SQLExecuteQueryOperator` calling the stored procedure | MECH | None expected |
| `DBMON` [AS p.2551] | `SqlSensor` (`mode="reschedule"`) | JUDG | Polling cadence needs an explicit value |
| `DBTRIG` [AS p.2551] | `SqlSensor` if genuinely polling for a row-level change; **flag as a CDC (change-data-capture) redesign candidate** if the monitored action is really "notify me when this table changes" at a granularity a sensor can't reasonably poll for | JUDG / REDESIGN (`scoring_rules.yaml`'s `jt.dbmon|dbtrig: flag:cdc`) | A naive polling translation of true CDC intent will either miss events or hammer the database — state which was chosen |
| `SQLAGENT` | `MsSqlOperator` calling `msdb.dbo.sp_start_job`, then a poll for completion | JUDG | PRACTITIONER JUDGMENT — not found in the ingested 12.0 corpus (`autosys-reference/reference/job-types.md`'s coverage note); confirm the real attribute set |

## `dbtype` attribute [AS p.2457]

AutoSys auto-adjusts multi-action monitoring syntax per database vendor (Microsoft SQL Server
uses commas, Oracle uses `or`). This vendor-specific syntax adaptation has no Airflow equivalent
to translate — the target `SqlSensor`'s SQL is hand-written per the actual monitored condition,
not transliterated from AutoSys's `dbtype`-adjusted syntax.

## What the scaffolder emits vs. leaves as TODO

Emits `SQLExecuteQueryOperator`/`SqlSensor` skeletons with the connection parameterized (Connection
ID via the target secrets backend, never an embedded credential); leaves
`# TODO(JUDG:cdc-redesign)` on every `DBTRIG` job flagged `cdc` for the polling-vs-CDC decision.
