# SLA-Miss Detection and Escalation (Replacing AutoSys Alarms)

AutoSys used `term_run_time`, `max_run_alarm`, and complex Cross-Box alarms to detect when jobs were running long or missing SLAs. In Airflow and Astro, SLA monitoring is handled at multiple levels, from code-level callbacks to business-level observability dashboards.

## The SLA monitoring spectrum

| Approach | Level | Mechanism | Best for |
|---|---|---|---|
| **Native Airflow `sla` parameter** | Task / Code | Set `sla=timedelta(...)` on a task. Triggers `sla_miss_callback` if missed. | Simple, task-level timeout alerts (only works on scheduled DAGs). |
| **Astro Alerts** | Platform | Configure DAG-level timeliness/duration alerts in the Astro UI. | Standard DAG monitoring; no code changes required. |
| **Astro Observe** | Business | Define Data Products and set Data Freshness SLAs. | Monitoring business-critical data delivery and downstream impact. |

## Escalation strategies

When an SLA is missed, the alert must be routed to the correct system for action.

### 1. Standard notification (Slack/PagerDuty)
Use Astro Alerts or `sla_miss_callback` to route the notification directly to an on-call tool (see topic 044).

### 2. Enterprise AutoSys integration (Hybrid estates)
For organizations running Airflow and AutoSys concurrently, where an Airflow SLA miss must trigger a downstream action in AutoSys:
- **Broadcom Airflow Agent**: Use the official AutoSys Airflow agent. This allows AutoSys to monitor the DAG and trigger native AutoSys alarms or successor jobs based on the Airflow state.
- **Custom API call**: Within the `sla_miss_callback`, write custom Python logic to call the AutoSys API (or an intermediate tool) to raise a specific alarm.

### 3. Cross-domain observability (AAI)
For large enterprise migrations, tools like Broadcom's Automation Analytics & Intelligence (AAI) can ingest metadata from both Airflow and legacy AutoSys. This provides a unified view and allows predictive alerting if a delay in an upstream AutoSys job threatens a downstream Airflow SLA.

## Solving the "Silent Failure" problem

A major risk in Airflow is the "silent failure" — when a DAG never starts (e.g., due to a broken scheduler or a failed external trigger), the native Airflow `sla_miss_callback` will not fire, because Airflow doesn't know the DAG is missing.
- **Solution**: Use **Astro Observe**. Because it monitors the *expected freshness* of the target Data Product (e.g., "Table X must be updated by 9 AM"), it will alert you if the data is stale, regardless of whether the DAG failed, got stuck, or never ran at all.

## Sources

[B-Airflow-SLA] Apache Airflow Docs — SLAs and callbacks (accessed 2026-08-08)
[B-Observe] Astronomer Docs — Astro Observe Data Products and SLAs (accessed 2026-08-08)
[B-Broadcom] Broadcom Docs — AutoSys Airflow Agent Integration (accessed 2026-08-08)
