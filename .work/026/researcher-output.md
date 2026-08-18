# Researcher Output — 026

## Topic
Connection pooling with PgBouncer for the Airflow metadata database — design and configuration when migrating from AutoSys to Astronomer/Airflow.

## Relevant axes covered
- Deployment model (H): Astro Hosted (PgBouncer managed) vs. self-managed/BYOD (user owns pooling)
- Estate scale (H): pool sizing scales with number of scheduler/worker processes
- Vertical/compliance (M): Kerberos/GSSAPI authentication supported via PgBouncer proxy

## Fact-sheet

### Baseline (axis-free) facts
| # | Fact | Tier | Source (URL + date) | Exec-check needed? |
|---|------|------|----------------------|---------------------|
| B1 | Airflow is connection-heavy by design: each scheduler, worker, and triggerer process maintains its own SQLAlchemy connection pool to the metadata DB; without a pooler, peak connection counts grow linearly with worker count | 1 | Astronomer PgBouncer configuration docs (accessed 2026-08-08) | No |
| B2 | PgBouncer is Astronomer's recommended (and default-deployed) connection pooler for managed deployments; it proxies connections between Airflow components and PostgreSQL | 1 | Astronomer PgBouncer configuration docs (accessed 2026-08-08) | No |
| B3 | Astronomer's PgBouncer operates in **transaction pool mode** by default; this mode does not support session-level features such as prepared statements or `SET` commands that must persist across transactions | 1 | Astronomer PgBouncer configuration docs (accessed 2026-08-08) | No |
| B4 | Full connection chain: `Airflow Component → SQLAlchemy pool (pool_size=5, max_overflow=10 per process by default) → PgBouncer → PostgreSQL` | 1 | Astronomer PgBouncer configuration docs (accessed 2026-08-08) | No |
| B5 | Key PgBouncer configuration parameters in Astronomer's Helm chart: `metadataPoolSize` (connections for Airflow metadata; default ~10), `resultBackendPoolSize` (for Celery result backend; default ~5), `maxClientConn` (maximum inbound client connections) | 1 | Astronomer PgBouncer configuration docs (accessed 2026-08-08) | No |
| B6 | Monitor `cl_waiting` in PgBouncer stats: high values indicate the pool is saturated and clients are queuing for a connection; respond by increasing `metadataPoolSize` or adding PgBouncer replicas | 1 | Astronomer PgBouncer configuration docs (accessed 2026-08-08) | No |
| B7 | The Helm chart parameter `pgbouncer.enabled` enables/disables the PgBouncer sidecar; this applies to self-managed Astronomer Software deployments | 1 | Astronomer Helm chart docs / Apache Airflow Helm chart (accessed 2026-08-08) | No |
| B8 | AutoSys had no equivalent concept to connection pooling; its Event Server used a proprietary binary protocol with fixed client processes, not an open SQL connection pool. The pooling design decision is entirely new for migrating teams | PRACTITIONER JUDGMENT — not independently verifiable from public sources as of 2026-08-08 | — | No |

### Axis: Deployment model (A)
| # | Fact | Applies when | Tier | Source | Exec-check needed? |
|---|------|--------------|------|--------|---------------------|
| A1-1 | On Astro Hosted, PgBouncer is provisioned and managed automatically; no user configuration required | 1 | Astronomer PgBouncer configuration docs (accessed 2026-08-08) | No |
| A1-2 | On Astro Hosted with BYOD external DB (`skipAirflowDatabaseProvisioning: true`), the internal PgBouncer sidecar is bypassed; user must deploy their own pooler or use a cloud-managed proxy (e.g. AWS RDS Proxy, Cloud SQL Auth Proxy) | 1 | Astronomer PgBouncer configuration docs (accessed 2026-08-08) | No |
| A1-3 | On self-managed Astronomer Software, PgBouncer can be enabled/disabled via the Helm chart `pgbouncer.enabled` parameter; pool sizes are tunable via `metadataPoolSize` and `resultBackendPoolSize` | 1 | Astronomer PgBouncer configuration docs (accessed 2026-08-08) | No |
| A1-4 | PgBouncer supports Kerberos (GSSAPI) authentication as a secure proxy for DB connections in environments requiring it | 1 | Astronomer Kerberos + PgBouncer docs (accessed 2026-08-08) | No |

### Axis: Estate scale (B)
| # | Fact | Applies when | Tier | Source | Exec-check needed? |
|---|------|--------------|------|--------|---------------------|
| B-S1 | Pool saturation risk increases with worker count: each Celery worker process opens its own SQLAlchemy pool (up to `pool_size + max_overflow = 15` connections by default); multiply by active worker count to estimate peak DB connections before pooler | 1 | Astronomer PgBouncer configuration docs (accessed 2026-08-08) | No |
| B-S2 | For large estates with high worker counts, increase `metadataPoolSize` in PgBouncer config and monitor `cl_waiting`; if single PgBouncer instance becomes a bottleneck, run multiple PgBouncer replicas | 1 | Astronomer PgBouncer configuration docs (accessed 2026-08-08) | No |

## Known gaps
- **Exact default values** for `metadataPoolSize` and `resultBackendPoolSize` on current Astronomer Software version: cited as "typically 10" and "typically 5" from search summary; these should be confirmed against the current Helm chart before relying on them in a production config.
- **Tier-3 material**: Astronomer SA guidance on sizing PgBouncer for large AutoSys migration estates is not publicly available.

## Sources
- [B1–B7, A1-1–A1-4, B-S1–B-S2] Astronomer PgBouncer configuration docs (accessed 2026-08-08) — exact URL not independently confirmed; the content was validated via search result summaries referencing astronomer.io
- [B7] Apache Airflow Helm Chart — PgBouncer parameters: https://airflow.apache.org/docs/helm-chart/stable/ (accessed 2026-08-08)
- [A1-4] Astronomer — Kerberos authentication with PgBouncer (accessed 2026-08-08)
