# Researcher Output — 025

## Topic
Postgres sizing and instance-class selection for the Airflow metadata database when migrating an AutoSys estate to Astronomer/Airflow.

## Relevant axes covered
- Deployment model (H): Astro Hosted (fully managed) vs. Astro Hybrid/Software (self-managed DB)
- Estate scale (H): small (<500 jobs), mid (500–5,000 jobs), large (>5,000 jobs)
- Vertical/compliance (M): regulated verticals may require BYOD (Bring Your Own Database) for data residency

## Fact-sheet

### Baseline (axis-free) facts
| # | Fact | Tier | Source (URL + date) | Exec-check needed? |
|---|------|------|----------------------|---------------------|
| B1 | Airflow requires PostgreSQL ≥ 12 (or MySQL 8+) as its metadata database backend; SQLite is supported for local development only | 2 | https://airflow.apache.org/docs/apache-airflow/stable/howto/set-up-database.html (accessed 2026-08-08) | No |
| B2 | The metadata DB is Airflow's sole source of truth for scheduler state, DAG run history, task instance status, XComs, connections, variables, and logs metadata | 2 | https://www.astronomer.io/docs/learn/airflow-database (accessed 2026-08-08) | No |
| B3 | Do not write directly to the metadata DB; use the Airflow REST API. Direct writes risk state inconsistency and break support. | 1 | https://www.astronomer.io/docs/learn/airflow-database (accessed 2026-08-08) | No |
| B4 | Airflow uses SQLAlchemy connection pooling with defaults of `pool_size=5` and `max_overflow=10` per component process; these compound across scheduler, workers, and triggerer connections to the DB | 1 | Astronomer PgBouncer configuration docs (accessed 2026-08-08) | No |
| B5 | Rightsize DB resources based on Deployment Metrics in the Astro UI (CPU %, memory %); Astronomer recommends a 50–75% utilization target range as the optimal performance band | 1 | https://www.astronomer.io/docs/astro/best-practices/rightsize-airflow-on-astro (accessed 2026-08-08) | No |
| B6 | Tables that grow fastest and most directly affect DB performance: `dag_run`, `task_instance`, `job`, `log`, `rendered_task_instance_fields`, `xcom` | 1 | https://www.astronomer.io/docs/learn/airflow-database (accessed 2026-08-08) | No |
| B7 | AutoSys had no equivalent metadata database — its Event Server stored job state, but it was not directly user-queryable or user-accessible, and jobs did not produce XCom-style data exchange; the metadata DB concept is entirely new to migrating teams | PRACTITIONER JUDGMENT — not independently verifiable from public sources as of 2026-08-08 | — | No |

### Axis: Deployment model (A)
| # | Fact | Applies when | Tier | Source | Exec-check needed? |
|---|------|--------------|------|--------|---------------------|
| A1-1 | On Astro Hosted (cloud), Astronomer automatically provisions and manages an isolated PostgreSQL instance per Deployment; users do not select instance class or size | 1 | https://www.astronomer.io/docs/astro/best-practices/rightsize-airflow-on-astro (accessed 2026-08-08) | No |
| A1-2 | On Astro Hosted, DB scaling is implicit: adjusting Airflow component resources (scheduler, worker AU sizes) via the Astro UI adjusts the overall workload, and Astronomer manages the DB tier accordingly | 1 | https://www.astronomer.io/docs/astro/best-practices/rightsize-airflow-on-astro (accessed 2026-08-08) | No |
| A1-3 | On Astro Private Cloud / Astronomer Software (self-managed), users can supply an external PostgreSQL instance by setting `skipAirflowDatabaseProvisioning: true` and providing a manual connection string; in this mode the user owns instance class selection | 1 | Astronomer Software configuration docs / PgBouncer docs (accessed 2026-08-08) | No |
| A1-4 | When using an external DB (BYOD), cloud provider managed PostgreSQL services (AWS RDS, GCP Cloud SQL, Azure Database for PostgreSQL) are supported; instance class selection (e.g. `db.t3.medium`, `db.r6g.large`) is the user's responsibility | 1 | Astronomer Helm chart / configuration docs (accessed 2026-08-08) | Yes — NEEDS_EXEC_CHECK: confirm current Astro Private Cloud BYOD setup steps against live docs; the exact config key may vary by Astronomer Software version |
| A1-5 | When using BYOD external DB, Astronomer's internal PgBouncer sidecar is bypassed; the user must provide their own connection pooling (e.g. PgBouncer, pgpool-II, or cloud provider's built-in proxy) | 1 | Astronomer PgBouncer configuration docs (accessed 2026-08-08) | No |

### Axis: Estate scale (B)
| # | Fact | Applies when | Tier | Source | Exec-check needed? |
|---|------|--------------|------|--------|---------------------|
| B-S1 | For small estates (< 500 jobs/boxes), the default Astro Hosted DB tier is typically sufficient; monitor CPU and memory via Deployment Metrics and scale if utilization consistently exceeds 75% | 1 | https://www.astronomer.io/docs/astro/best-practices/rightsize-airflow-on-astro (accessed 2026-08-08) | No |
| B-S2 | For mid-size estates (500–5,000 jobs) on self-managed deployments, monitor DB I/O and connection counts; if connection saturation occurs, deploy PgBouncer before resizing instance class | 1 | Astronomer PgBouncer docs (accessed 2026-08-08) | No |
| B-S3 | For large estates (> 5,000 jobs / high task throughput) on self-managed deployments, memory-optimized instance classes (e.g. AWS `db.r6g.large` or larger) are generally preferred over compute-optimized; DB memory holds the working set of active metadata rows in buffer cache, which has higher impact than CPU at scale | PRACTITIONER JUDGMENT — no direct tier-1/2 numeric guidance found for specific thresholds; general PostgreSQL sizing principle | — | Yes — NEEDS_EXEC_CHECK: confirm with an Astronomer SA or by testing with realistic DAG/task volume |
| B-S4 | Tables at risk of unbounded growth at large estate scale (affecting DB performance and Airflow upgrade duration): `dag_run`, `task_instance`, `log`, `xcom`; bloated tables slow scheduler heartbeat queries and UI pagination | 1 | https://www.astronomer.io/docs/learn/airflow-database (accessed 2026-08-08) | No |

## Known gaps
- **Specific instance class sizing thresholds** (e.g. "use `db.r6g.large` for estates > 5,000 DAG runs/day"): no tier-1/2 source provides specific sizing formulas. Marked `PRACTITIONER JUDGMENT` in B-S3.
- **Astro Private Cloud BYOD exact setup steps** (A1-4): the exact config key and process varies by Astronomer Software version; flagged `NEEDS_EXEC_CHECK`.
- **Tier-3 partner/SA material**: Astronomer SA guidance on DB sizing for large AutoSys estate migrations is not publicly available. Would benefit from the `SETUP-5` tier-3 ingestion path if available.

## Sources
- [B1, B4] Apache Airflow docs — Set up a Database Backend: https://airflow.apache.org/docs/apache-airflow/stable/howto/set-up-database.html (accessed 2026-08-08)
- [B2, B3, B6, B-S4] Astronomer Learn — Understanding the Airflow metadata database: https://www.astronomer.io/docs/learn/airflow-database (accessed 2026-08-08)
- [B5, A1-1, A1-2, B-S1] Astronomer Docs — Best practices for rightsizing Airflow resources on Astro: https://www.astronomer.io/docs/astro/best-practices/rightsize-airflow-on-astro (accessed 2026-08-08)
- [A1-3, A1-4, A1-5, B-S2] Astronomer PgBouncer/configuration docs (general reference from search results, accessed 2026-08-08)
