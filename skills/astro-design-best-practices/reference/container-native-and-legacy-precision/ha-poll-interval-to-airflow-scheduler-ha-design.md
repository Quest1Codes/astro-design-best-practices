# Heartbeat/HAPollInterval Failover-Detection → Airflow Scheduler HA Heartbeat/Leader-Election Design

AutoSys HA uses a **Primary/Shadow (Active/Passive)** model. The primary scheduler writes heartbeats to the shared Event Server database; the shadow scheduler polls the database at the `HAPollInterval` (default 15 seconds) [B1]. If the shadow detects that the primary's heartbeat has not updated within the poll interval window, it initiates takeover. A tie-breaker scheduler resolves split-brain scenarios in the dual Event Server (HADS) configuration [B1].

Airflow 2.0+ uses an **Active/Active multi-scheduler** model — fundamentally different from AutoSys's Active/Passive approach.

## Architecture Comparison

{syn: AutoSys `HAPollInterval` → Airflow `scheduler.heartbeat_interval`; AutoSys Primary/Shadow → Airflow multi-scheduler Active/Active}

| Aspect | AutoSys HA | Airflow HA |
|---|---|---|
| **Model** | Active/Passive (Primary + Shadow) | Active/Active (multiple concurrent schedulers) |
| **Coordination mechanism** | Heartbeats written to shared Event Server DB | Heartbeats written to shared PostgreSQL metadata DB; row-level locking for task assignment [B2] |
| **Poll interval** | `HAPollInterval` (default: 15 seconds) | `scheduler.heartbeat_interval` (default: 5 seconds) [B2] |
| **Tie-breaker** | Third scheduler process (HADS) | Database row locking (no separate tie-breaker needed) [B2] |
| **Failover trigger** | Shadow detects missed heartbeats → promotes to primary | Failed scheduler instance simply stops; remaining schedulers absorb load automatically [B2] |
| **Recovery** | Shadow takes over — brief lag while agents are notified | No failover event — load redistributes transparently across remaining schedulers |

## Airflow Multi-Scheduler HA Design on Astro

On Astro, how you set the scheduler count depends on the deployment model — this isn't a single uniform slider. **Astro Hosted**: no configurable replica count; a Deployment runs a single scheduler by default, and the **High Availability** toggle is a binary on/off switch to exactly two schedulers. **Astro Private Cloud/Hybrid**: a real configurable replica count, up to 4 by default [B4]. See `reference/scheduler-and-dag/scheduler-ha-and-leader-election.md` for the full platform split and sourcing.

```
Astro Hosted            → High Availability: On/Off (2 schedulers when on)
Astro Private Cloud/Hybrid → Scheduler → Replicas: 2-4 (configurable)
```

The Airflow scheduler writes a heartbeat row to the `job` table in the metadata DB. Each scheduler instance has a unique ID. The `scheduler_heartbeat_sec` determines how frequently this is written (default: 5 seconds) [B2].

## Monitoring Scheduler Health

| AutoSys Monitoring | Airflow Equivalent |
|---|---|
| Check if shadow is running (`autostatus`) | `GET /api/v2/health` — returns scheduler status |
| `EP_ROLLOVER` alarm on failover | Astro alert on scheduler health degradation; `airflow_scheduler_heartbeat` metric |
| `HAPollInterval` timeout | `scheduler.heartbeat_interval` × `scheduler_health_check_threshold` |

Scheduler health check threshold: if a scheduler's last heartbeat is older than `scheduler_health_check_threshold` seconds (default: 30 seconds), the scheduler is considered unhealthy [B2].

## Sources

[B1] Broadcom AutoSys Documentation — `HAPollInterval` parameter (default 15s), Primary/Shadow HA model, HADS tie-breaker, heartbeat-to-Event-Server mechanism, shadow takeover behavior (accessed 2026-08-18)
[B2] Apache Airflow Docs — Multi-scheduler Active/Active architecture, `scheduler.heartbeat_interval` (default 5s), `scheduler_health_check_threshold` (default 30s), database row-level locking for task assignment, `GET /api/v2/health` scheduler status (accessed 2026-08-18). **Correction**: the health endpoint was originally cited as `/api/v1/health`; Airflow 3 uses the v2 REST API — see https://www.astronomer.io/docs/astro/airflow-api (tier 1, added on doc-verification review). Also corrects `scheduler.heartbeats` (StatsD-style) to the real metric name `airflow_scheduler_heartbeat`, confirmed at https://www.astronomer.io/docs/astro-private-cloud/v-2-x/platform-alerts (tier 1).
[B4] Astronomer Docs — Airflow system components, "Horizontal scaling" (Astro Private Cloud/Hybrid): Scheduler supports up to 4 replicas by default: https://www.astronomer.io/docs/astro-private-cloud/v-2-x/airflow-system-components#horizontal-scaling (tier 1); Scheduler (Astro Hosted): single scheduler by default, High Availability toggle runs exactly two, not a configurable count: https://www.astronomer.io/docs/astro/deployment-resources#scheduler (tier 1) — added on consistency review to align with `reference/scheduler-and-dag/scheduler-ha-and-leader-election.md`
