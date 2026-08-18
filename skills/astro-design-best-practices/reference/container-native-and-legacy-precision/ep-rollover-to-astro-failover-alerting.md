# EP_ROLLOVER Alarm and Failover-Event Handling → Astro Failover Alerting Design

`EP_ROLLOVER` (Event Processor Rollover) is the AutoSys alarm name for the event that fires when the shadow scheduler takes over from a failed primary [B1]. In dual Event Server mode (HADS), a related `DB_ROLLOVER` alarm fires when one Event Server database fails over to the other [B1]. These alarms are routed via SNMP traps or the AutoSys alarm manager to operations teams.

On Astro, there is no single named "EP_ROLLOVER" event — Airflow's multi-scheduler Active/Active model means there is no "failover" in the traditional sense. However, scheduler health degradation and Deployment unavailability need equivalent alerting coverage.

## EP_ROLLOVER Alarm → Astro Alert Equivalents

{syn: AutoSys `EP_ROLLOVER` → Astro scheduler health alert; AutoSys `DB_ROLLOVER` → Astro metadata DB connectivity alert}

| AutoSys Alarm | Astro/Airflow Equivalent | Alert Mechanism |
|---|---|---|
| **`EP_ROLLOVER`** (shadow takes over) | Scheduler replica count drops below 2 OR `scheduler.heartbeats == 0` | Astro Deployment alert + Prometheus alert on `scheduler.heartbeats` metric [B2] |
| **`DB_ROLLOVER`** (Event Server DB failover) | Metadata DB connection failure | Astro platform alert (infrastructure-level); Airflow health endpoint returns `unhealthy` [B2] |
| **Scheduler process crash** | Scheduler pod `CrashLoopBackOff` or restart | Kubernetes pod restart alert via Astro + PagerDuty/Opsgenie integration [B2] |

## Recommended Alerting Configuration

### 1. Astro Platform Alerts
Configure in Astro UI → Deployment → Alerts:
- Alert when `DAG run failure rate > threshold` — downstream symptom of scheduler issues.
- Alert when Deployment is in a degraded state.

### 2. Prometheus Alerting Rules (Enterprise Pattern)
```yaml
# Scheduler heartbeat silence = EP_ROLLOVER equivalent
- alert: AirflowSchedulerDown
  expr: airflow_scheduler_heartbeat == 0
  for: 1m
  labels:
    severity: critical
  annotations:
    summary: "Airflow scheduler is not heartbeating (equivalent to EP_ROLLOVER)"

# Metadata DB connection failures
- alert: AirflowMetadataDBUnhealthy
  expr: airflow_health_metadatabase{status="unhealthy"} == 1
  for: 30s
  labels:
    severity: critical
```

### 3. Controlled Failover Testing (EP_ROLLOVER Equivalent)

AutoSys used `sendevent -E STOP_DEMON -v FAILOVER` for controlled failover rehearsals [B1]. On Astro:
- Scale the Deployment's scheduler replicas to 1 via the Astro UI, observe graceful degradation, then scale back to 2.
- This tests whether your alerting detects reduced scheduler capacity before a real failure.

## Key Behavioral Difference

AutoSys `EP_ROLLOVER` involves a **brief job processing pause** while the shadow notifies agents that it is now the active scheduler [B1]. Airflow has no equivalent pause — remaining active schedulers continue processing tasks immediately without any agent notification required. This is architecturally superior for availability.

## Sources

[B1] Broadcom AutoSys Documentation — `EP_ROLLOVER` alarm definition, `DB_ROLLOVER` alarm, SNMP trap routing, HADS dual Event Server failover behavior, `sendevent -E STOP_DEMON -v FAILOVER` (accessed 2026-08-18)
[B2] Astronomer Docs & Apache Airflow Docs — Deployment alerts, scheduler health endpoint (`GET /api/v1/health`), `scheduler.heartbeats` StatsD metric, Prometheus alerting integration (accessed 2026-08-18)
