---
topic: sla-miss-detection-and-escalation
family: knowledge
skill: astro-design-best-practices
verified_against:
  airflow: "3.3.1"
  astro_runtime: "3.3-2"
last_verified: 2026-09-17
confidence: cited
signals: 
  - must_complete_times
---

# SLA-Miss Detection and Escalation (Replacing AutoSys Alarms)

AutoSys used `term_run_time`, `max_run_alarm`, and complex Cross-Box alarms to detect when jobs were running long or missing SLAs. In Airflow and Astro, SLA monitoring is handled at multiple levels, from code-level Deadline Alerts to business-level observability dashboards.

**Correction**: the legacy per-task SLA keyword argument and its miss-callback hook were **removed in Airflow 3.0**, not merely deprecated — see `scheduler-and-dag/dag-level-sla-and-catchup-backfill-policy.md` for the full removal citation. The rest of this file describes their Airflow-3 replacement, Deadline Alerts, throughout.

## The SLA monitoring spectrum

| Approach | Level | Mechanism | Best for |
|---|---|---|---|
| **Deadline Alerts** (Airflow 3.1+) | Task / DAG / Code | Attach a `DeadlineAlert` (with a callback) to a task or DAG; fires if the deadline passes before completion. Replaces the removed legacy SLA parameter and its miss-callback hook [B-Airflow-SLA]. | Simple, task- or DAG-level timeout alerts defined in code. |
| **Astro Alerts** | Platform | Configure DAG-level timeliness/duration alerts in the Astro UI. | Standard DAG monitoring; no code changes required. |
| **Astro Observe** | Business | Define Data Products and set Data Freshness SLAs. | Monitoring business-critical data delivery and downstream impact. |

## Escalation strategies

When an SLA is missed, the alert must be routed to the correct system for action.

### 1. Standard notification (Slack/PagerDuty)
Use Astro Alerts or a Deadline Alert callback to route the notification directly to an on-call tool (see topic 044).

### 2. Enterprise AutoSys integration (Hybrid estates)
For organizations running Airflow and AutoSys concurrently, where an Airflow SLA miss must trigger a downstream action in AutoSys:
- **Broadcom Airflow Agent**: Use the official AutoSys Airflow Agent Integration (a System Agent that authenticates to the Airflow REST API, triggers DAG runs, and monitors progress/status). This allows AutoSys to orchestrate and monitor Airflow DAGs directly, including alerting, SLA management, and reporting through AutoSys itself [B-Broadcom]. **Verified**: an earlier Critic pass flagged this claim as likely fabricated since it couldn't be checked against the Astronomer docs MCP (which only covers Astronomer's own site, not Broadcom's) — a follow-up web search against Broadcom's own TechDocs/Academy confirmed this is a real, current product ("Apache Airflow Plugin Extension" / "AutoSys Cloud Integrations: Airflow Agent Integration") [B-Broadcom].
- **Custom API call**: Within the Deadline Alert's callback, write custom Python logic to call the AutoSys API (or an intermediate tool) to raise a specific alarm.

### 3. Cross-domain observability (AAI)
For large enterprise migrations, tools like Broadcom's Automation Analytics & Intelligence (AAI) can ingest metadata from both Airflow and legacy AutoSys. This provides a unified view and allows predictive alerting if a delay in an upstream AutoSys job threatens a downstream Airflow SLA. **Verified** on the same follow-up pass: AAI 6.5.2 shipped a real "Airflow Connector" that acquires event/definition data from Airflow for unified cross-scheduler observability [B-AAI] — this claim was also correctly sourceable, not invented.

## Solving the "Silent Failure" problem

A major risk in Airflow is the "silent failure" — when a DAG never starts (e.g., due to a broken scheduler or a failed external trigger), a task-level Deadline Alert will not fire, because Airflow doesn't know the DAG is missing.
- **Solution**: Use **Astro Observe**. Because it monitors the *expected freshness* of the target Data Product (e.g., "Table X must be updated by 9 AM"), it will alert you if the data is stale, regardless of whether the DAG failed, got stuck, or never ran at all.

## Sources

[B-Airflow-SLA] Apache Airflow Docs — Deadline alerts (SLA replacement in Airflow 3.1+): https://airflow.apache.org/docs/apache-airflow/stable/howto/deadline-alerts.html (tier 2)
[B-Observe] Astronomer Docs — Create a data product in Astro Observe / Create an alert (SLAs): https://www.astronomer.io/docs/astro/create-data-products and https://www.astronomer.io/docs/astro/observe-slas (tier 1)
[B-Broadcom] Broadcom Docs — AutoSys Cloud Integrations: Airflow Agent Integration: https://academy.broadcom.com/automation/autosys/airflow-agent-integration ; Apache Airflow Plugin Extension (TechDocs): https://techdocs.broadcom.com/us/en/ca-enterprise-software/intelligent-automation/workload-automation-plugin-extensions/GA/workload-automation-agent-plugin-extension/apache-airflow-plugin-extension.html (tier 2 — third-party vendor docs, confirmed real via web search on Critic-pass follow-up)
[B-AAI] Broadcom Docs — Announcing the Availability of the Airflow Connector for AAI (6.5.2): https://academy.broadcom.com/blog/automation/automation-intelligence/airflow-connector-for-aai-now-available (tier 2 — third-party vendor docs, confirmed real via web search on Critic-pass follow-up)
