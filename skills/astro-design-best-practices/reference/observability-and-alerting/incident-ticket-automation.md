# Incident-Ticket Automation (Replacing Service Desk)

AutoSys often relied on proprietary plugins or OS-level scripts to create incident tickets in tools like ServiceNow or BMC Remedy upon job failure. In Astro, automating incident creation is achieved via API-driven orchestration or event-driven middleware.

## Architectural approaches

### 1. Airflow-driven orchestration (Direct API)
Use Airflow's native callback system to create tickets programmatically.

- **Implementation**: Define an `on_failure_callback` at the DAG or task level.
- **Mechanism**: The callback executes a Python script using the `requests` library to call the ServiceNow Table API or Jira REST API.
- **Security**: Store the API credentials (tokens/passwords) in Airflow Connections (`http` type) or a secrets backend (Vault, AWS Secrets Manager). Never hardcode credentials in the callback.

### 2. Event-driven integration (Middleware)
For robust ITSM workflows, decouple ticket creation from the Airflow worker.

- **Mechanism**: Use Astro Alerts to send a failure notification to a webhook or an intermediate routing tool (like PagerDuty or an Enterprise Service Bus).
- **ServiceNow IntegrationHub**: Use the ServiceNow Jira Spoke to automatically generate Jira issues for engineering teams when a ServiceNow incident is created by the Airflow alert.
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
[B-Airflow-Callbacks] Apache Airflow Docs — Callbacks and context variables (accessed 2026-08-08)
