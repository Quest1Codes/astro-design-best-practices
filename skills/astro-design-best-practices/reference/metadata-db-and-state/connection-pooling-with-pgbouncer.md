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
| `metadataPoolSize` | ~10 | Server connections reserved for Airflow metadata DB [B5] |
| `resultBackendPoolSize` | ~5 | Server connections for Celery result backend [B5] |
| `maxClientConn` | — | Maximum inbound Airflow-side connections to PgBouncer [B5] |

> **Note**: default values ("~10" and "~5") are from documentation search summaries; verify against the current Astronomer Helm chart before production configuration. `NEEDS_EXEC_CHECK`

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

[B1–B7, A1-1–A1-4, B-S1–B-S2] Astronomer PgBouncer configuration docs (accessed 2026-08-08)
[B7] Apache Airflow Helm Chart docs (accessed 2026-08-08)
[A1-4] Astronomer — Kerberos authentication with PgBouncer (accessed 2026-08-08)
