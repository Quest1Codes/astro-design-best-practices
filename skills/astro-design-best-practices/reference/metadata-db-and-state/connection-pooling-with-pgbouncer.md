# Connection Pooling with PgBouncer

AutoSys's Event Server used a proprietary binary protocol with fixed client processes — there was no open SQL connection pool to design. Airflow is the opposite: every scheduler, worker, and triggerer process opens its own SQLAlchemy connection pool to PostgreSQL, and with many workers those connections compound rapidly without a pooler [B1].

PgBouncer is Astronomer's recommended and default-deployed connection pooler [B2]. It sits between Airflow components and PostgreSQL as a lightweight proxy, multiplexing many application-side connections onto a smaller number of server-side PostgreSQL connections.

## Connection chain

```
Airflow Component
    → SQLAlchemy pool (pool_size=5, max_overflow=10 per process default) [B4]
    → PgBouncer (transaction pool mode) [B3]
    → PostgreSQL
```

Transaction pool mode means a server connection is held only for the duration of a single transaction, then returned to the pool — enabling many more Airflow-side connections than PostgreSQL server connections. **Transaction mode does not support session-level features** (prepared statements, persistent `SET` commands) [B3].

## Deployment model decision table (Axis A — H rating)

| Deployment model | PgBouncer ownership | User action required |
|---|---|---|
| **Astro Hosted** | Astronomer-managed automatically [A1-1] | None |
| **Astro Hosted — BYOD external DB** | Internal PgBouncer bypassed [A1-2] | Deploy own pooler (e.g. AWS RDS Proxy, PgBouncer on EC2, pgpool-II) |
| **Astronomer Software / self-managed** | User-configurable via Helm [A1-3] | Set `pgbouncer.enabled: true`, tune `metadataPoolSize`, `resultBackendPoolSize` |
| **Astronomer Software — Kerberos** | PgBouncer used as GSSAPI proxy [A1-4] | Configure Kerberos authentication on PgBouncer |

## Key configuration parameters (self-managed)

| Parameter | Default | Purpose |
|---|---|---|
| `pgbouncer.enabled` | — | Enable/disable PgBouncer sidecar [B7] |
| `metadataPoolSize` | 10 | Server connections reserved for Airflow metadata DB [B8] |
| `resultBackendPoolSize` | 5 | Server connections for Celery result backend [B8] |
| `maxClientConn` | 100 | Maximum inbound Airflow-side connections to PgBouncer [B8] |

> **Resolved**: the earlier `NEEDS_EXEC_CHECK` on these defaults is closed — current Astronomer Private Cloud docs confirm the exact values above (`metadataPoolSize: 10`, `resultBackendPoolSize: 5`, `maxClientConn: 100`) [B8].

## Estate scale table (Axis B — H rating)

| Estate scale | Worker count signal | Pool sizing action |
|---|---|---|
| Small | Few workers | Default pool sizes sufficient; monitor `cl_waiting` |
| Mid / growing | Many Celery workers | {syn: B-S1,B5} Each worker process adds up to 15 SQLAlchemy connections before the pooler; increase `metadataPoolSize` if `cl_waiting > 0` consistently [B-S1][B6] |
| Large / high throughput | High worker count or KubernetesExecutor burst | Add PgBouncer replicas if single instance is the bottleneck [B-S2] |

## Monitoring signal

Watch `cl_waiting` in PgBouncer stats [B6]:
- `cl_waiting = 0` → pool is not saturated
- `cl_waiting > 0` consistently → increase `metadataPoolSize` or add PgBouncer replicas [B6]

## Sources

[B1–B7, A1-1–A1-4, B-S1–B-S2] Astronomer Docs — Private Cloud database architecture, connection pooling (PgBouncer): https://www.astronomer.io/docs/astro-private-cloud/v-2-x/database-architecture#connection-pooling-pgbouncer (tier 1, URL added on citation review)
[B7] Apache Airflow Helm chart production guide (PgBouncer rationale): https://airflow.apache.org/docs/helm-chart/stable/production-guide.html (tier 2, URL added on citation review)
[A1-4] Astronomer Docs — Kerberos database setup, PgBouncer as GSSAPI proxy: https://www.astronomer.io/docs/astro-private-cloud/v-2-x/kerberos-database-setup (tier 1, URL added on citation review)
[B8] Astronomer Docs — Private Cloud database architecture, pool sizes (`metadataPoolSize: 10`, `resultBackendPoolSize: 5`, `maxClientConn: 100`, matching Apache Airflow Helm chart defaults): https://www.astronomer.io/docs/astro-private-cloud/v-2-x/database-architecture#pool-sizes (tier 1, added on doc-verification review — resolves the prior `NEEDS_EXEC_CHECK`)
