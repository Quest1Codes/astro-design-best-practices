---
topic: hadoop-hdfs-hive-pig-oozie-sqoop
family: migration
skill: migrate-jil-to-airflow-translation
verified_against:
  airflow: "3.3.1"
  astro_runtime: "3.3-2"
  autosys: "12.0"
  autosys_doc_pages: [2551]
last_verified: 2026-09-17
confidence: mixed
signals: []
---

# Hadoop: HDFS, HIVE, PIG, OOZIE, SQOOP

| Code | Default target | Disposition | Delta |
|---|---|---|---|
| `HDFS` [AS p.2551] | `apache-airflow-providers-apache-hdfs` | JUDG | None expected for a plain HDFS operation |
| `HIVE` [AS p.2551] | `apache-airflow-providers-apache-hive` | JUDG | None expected for a plain query |
| `PIG` [AS p.2551] | `apache-airflow-providers-apache-pig` (or a `@task.bash` wrapper if the provider's coverage is thin for the specific script) | JUDG | Verify current provider coverage — Pig is a less actively maintained ecosystem than Hive/Spark |
| `OOZIE` [AS p.2551] | **REDESIGN** — an Oozie workflow becomes an Airflow DAG, not a single task | REDESIGN | The Oozie workflow's own DAG structure (actions, decision nodes, fork/join) has to be reconstructed as Airflow tasks/branching — this is a real re-authoring effort proportional to the Oozie workflow's complexity, not a 1:1 operator swap |
| `SQOOP` | `@task.bash sqoop ...`, or the target-specific provider transfer if the destination has one (e.g. a JDBC-to-object-storage load) | JUDG | PRACTITIONER JUDGMENT — not found in the ingested 12.0 corpus (`autosys-reference/reference/job-types.md`'s coverage note) |

## `OOZIE` deserves its own effort line

Unlike every other REDESIGN-scored job type in this reference set, an `OOZIE` job type usually
represents an entire **workflow**, not a single unit of work — treat it as its own migration
sub-project (read the Oozie workflow XML, not just the JIL `command:` line) rather than folding
its effort into the surrounding box's estimate.

## What the scaffolder emits vs. leaves as TODO

Emits provider-operator skeletons for `HDFS`/`HIVE`/`PIG`/`SQOOP`; refuses to scaffold `OOZIE`
jobs at all (REDESIGN units are refused per the hard rule), listing them separately with a note
to read the underlying workflow XML.
