# DAG Versioning and Change-Management Strategy

JIL's change model is in-place mutation: `insert_job`/`update_job`/`delete_job` edit the live definition in the Event Server, and AutoSys has no native concept of "the version of this job that a given run actually executed under." Airflow 3's DAG-versioning model is structurally different and closer to what a git-based estate actually needs.

## Core mechanics

- DAG bundles and DAG versioning were introduced in Airflow 3 specifically to address DAG change management [F1].
- A new DAG version is created automatically whenever a DAG run starts for a DAG that has had a **structural change** since its last run — structural changes include parameter changes, task-dependency changes, task-ID changes, or added/removed tasks [F1] (corrected citation per Critic pass — the exact phrasing is on F1, not F2 as originally cited). This tracking happens regardless of which DAG bundle type is used [F1].
- Each DAG run is associated with a specific DAG version, visible in the Airflow UI [F2].
- DAG bundles support versioning such that a DAG run can execute using one consistent version of the code for its entire run, even if the DAG file is updated mid-run [F3].
- The `LocalDagBundle` type (a local directory) does **not** support bundle versioning — tasks always run against the latest code on disk. Bundle types that integrate with Git repositories do support versioning [F4].

## {syn: F1,F2,F3,F4} Design guidance

For a production AutoSys migration, do not rely on `LocalDagBundle` — its lack of version pinning means a DAG file edited mid-run can change the behavior of an already-in-flight DAG run, which is a worse guarantee than AutoSys's own in-place JIL model gave (a running job at least finished under the definition it started with, absent an explicit `sendevent` override). Use a Git-backed DAG bundle so each DAG run is pinned to the commit that was live when it started, and the automatic version tracking [F2] becomes the audit trail JIL never had — every run is traceable to an exact DAG version, not just "whatever was live at some point."

## Estate-scale callout

At small-to-medium scale, one Git-backed bundle for the whole estate is sufficient. At large scale (thousands of DAG-factory-generated DAGs, Cluster 1's `dag-factory-pattern-for-large-estates.md`), consider whether structural-change detection at the *factory config* level (diffing YAML before it's regenerated into DAGs) is a useful pre-commit gate in addition to Airflow's own run-time version tracking — this is a process recommendation, not something F1-F4 establish directly, so treat it as a starting point to validate against the actual factory tooling chosen, not a settled claim.

## Migration-temporal callout

During coexistence, tag each DAG's version-controlled source with the corresponding AutoSys JIL revision it was translated from (a comment header or a factory-config field), so a rollback to "what AutoSys is still doing" and "what Airflow last ran" can be compared without cross-referencing two separate systems' change logs by hand.

## Sources

- [F1] Astronomer Docs — Dag Versioning and Dag Bundles: https://www.astronomer.io/docs/learn/airflow-dag-versioning (tier 1)
- [F2] Astronomer Docs — Dag versioning (Astro): https://www.astronomer.io/docs/astro/dag-versioning (tier 1)
- [F3] Apache Airflow docs — Dag Bundles: https://airflow.apache.org/docs/apache-airflow/stable/administration-and-deployment/dag-bundles.html (tier 2)
- [F4] Apache Airflow docs — Dag Bundles (`LocalDagBundle` versioning limitation): same as F3 (tier 2)
