# Incident-Ticket Automation (Replacing Service Desk)

AutoSys often relied on proprietary plugins or OS-level scripts to create incident tickets in tools like ServiceNow or BMC Remedy upon job failure. In Astro, automating incident creation is achieved via API-driven orchestration or event-driven middleware.

**Citation note**: an earlier draft of this file had no inline `[Bn]` markers anywhere in the body, despite a well-formed Sources list — fails the project's zero-tolerance traceability standard even though the underlying mechanisms are standard, well-documented integration patterns. Markers added below on Critic-pass review; claims that are pure architectural opinion (not a specific checkable fact) are left unmarked, as the project's own standard allows.

## Architectural approaches

### 1. Airflow-driven orchestration (Direct API)
Use Airflow's native callback system to create tickets programmatically.

- **Implementation**: Define an `on_failure_callback` at the DAG or task level [B-Airflow-Callbacks].
- **Mechanism**: The callback executes a Python script using the `requests` library to call the ServiceNow Table API or Jira REST API [B-ServiceNow][B-Jira].
- **Security**: Store the API credentials (tokens/passwords) in Airflow Connections (`http` type) or a secrets backend (Vault, AWS Secrets Manager). Never hardcode credentials in the callback.

### 2. Event-driven integration (Middleware)
For robust ITSM workflows, decouple ticket creation from the Airflow worker.

- **Mechanism**: Use Astro Alerts to send a failure notification to a webhook or an intermediate routing tool (like PagerDuty or an Enterprise Service Bus) [B-AstroAlerts].
- **ServiceNow IntegrationHub**: Use the ServiceNow Jira Spoke to automatically generate Jira issues for engineering teams when a ServiceNow incident is created by the Airflow alert [B-ServiceNow].
- **Benefits**: Reduces custom code in Airflow; centralizes incident routing logic in the ITSM platform.

## Ticket automation best practices

Automated ticket creation is prone to "ticket sprawl" if not designed carefully.

1. **Implement Deduplication**: Before making the API call to create a ticket, query the ITSM tool to check if an active ticket for that specific DAG/error signature already exists. If it does, append a comment rather than creating a duplicate.
2. **Handle Retries Gracefully**: If a task fails, retries, and fails again, do not open multiple tickets. Use idempotency keys (like `dag_id` + `execution_date`).
3. **Enrich Ticket Metadata**: A blank ticket is useless to on-call engineers. Ensure the automated payload includes:
   - DAG ID and Task ID
   - Execution Date/Time
   - Direct deep-link to the Airflow task logs (`{{ ti.log_url }}`)
   - Error message snippet (from the `exception` object in the callback context)
4. **Decouple Status Logic**: Use Airflow to *trigger* the ticket creation, but manage the ticket lifecycle (assignment, closure, escalation) natively within ServiceNow/Jira.

## Sources

[B-ServiceNow] ServiceNow Docs — Table API / IntegrationHub Jira Spoke (accessed 2026-08-08)
[B-Jira] Atlassian Docs — Jira REST API (accessed 2026-08-08)
[B-Airflow-Callbacks] Apache Airflow Docs — Callbacks and context variables: https://airflow.apache.org/docs/apache-airflow/stable/core-concepts/dags.html (tier 2)
[B-AstroAlerts] Astronomer Docs — Set up Astro alerts (webhook/PagerDuty/email routing on Dag failure): https://www.astronomer.io/docs/astro/alerts (tier 1, added on Critic-pass review)
