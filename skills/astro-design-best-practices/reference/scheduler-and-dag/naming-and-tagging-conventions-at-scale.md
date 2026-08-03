# Naming and Tagging Conventions at Scale

AutoSys already has two independent, orthogonal ways to classify a job — `box_name` (structural membership) [P1] and the `group`/`application` attributes (logical classification, independent of box membership) [F2]. Airflow's `dag_id` and `tags` map onto that same two-axis shape, and a large translated estate needs both, not just one.

## Core mechanics

- `dag_id` should be descriptive and follow a consistent naming convention — one commonly cited shape is `{collection_id}_{name}`, so that DAGs belonging to the same logical collection group together alphabetically in the UI [F1].
- DAG `tags` (a list argument in the DAG definition, e.g. `tags=["etl", "finance", "production"]`) provide filtering/grouping in the UI independent of `dag_id` naming, and should mirror whatever classification scheme the platform already uses (business unit, project, environment) [F1].

**Confidence note**: the specific naming-convention advice above is drawn from general Airflow community practice (blog-level sources, not an Astronomer/Apache primary doc specifically about naming) rather than an authoritative tier-1/2 specification — Airflow itself does not enforce or prescribe a `dag_id` format. Treat the *principle* ("be consistent, encode both structural collection and cross-cutting classification") as solid; treat the exact `{collection_id}_{name}` shape as one reasonable convention among several, not a fixed rule.

## {syn: P1,F2} Design guidance — mapping AutoSys's two classification axes

- **`box_name` / DAG-factory structural grouping** (`dag-factory-pattern-for-large-estates.md`) [P1] → encode in `dag_id`, following whatever collection convention the platform adopts (e.g. `{business_unit}_{box_name}`).
- **`group`/`application` JIL attributes** (cross-cutting classification independent of box structure) [F2] → encode as `tags`, not folded into `dag_id` — this preserves the original AutoSys distinction between "which box owns this job" and "which business classification(s) does it belong to," which JIL itself kept as two separate concepts.

## Estate-scale callout

At small scale, a single flat tagging scheme is fine. At large scale (thousands of DAG-factory-generated DAGs), tags become the primary UI-filtering mechanism a platform team actually uses day to day — treat the tag taxonomy itself as a piece of the factory's config schema (one config field per tag dimension, e.g. `business_unit`, `criticality`, `migration_wave`) rather than something added ad hoc per DAG, so it stays consistent across thousands of generated DAGs by construction rather than by discipline.

## Sources

- [F1] General Airflow community practice on DAG naming/tagging conventions (`dag_id` collection-prefix pattern, `tags` for cross-cutting classification) — sourced from community blog posts during this research pass, not an Astronomer/Apache primary specification. Treat as **`PRACTITIONER JUDGMENT`** for the specific naming shape; the underlying `tags` feature itself is a real, documented Airflow DAG argument.
- [F2] Broadcom TechDocs — "How Job Groupings Are Created" (`group`/`application` JIL attributes, independent of box membership): https://techdocs.broadcom.com/us/en/ca-enterprise-software/intelligent-automation/autosys-workload-automation/12-1-01/scheduling/ae-scheduling/box-jobs-overview/how-job-groupings-are-created.html (tier 1 — vendor primary documentation, sourced during this project's earlier AutoSys-architecture research pass)
- [P1] Project-internal — `skills/migrating-autosys-to-astronomer/reference/mapping.md` (box structural membership)
