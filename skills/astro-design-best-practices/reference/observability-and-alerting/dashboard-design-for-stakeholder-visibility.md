# Dashboard Design for Stakeholder Visibility

AutoSys provided stakeholder reporting through the Workload Control Center (WCC), generating operational status reports. Airflow's native UI is highly technical and designed for data engineers, making it unsuitable for business stakeholders. To bridge this gap, organizations must adopt a tiered dashboarding strategy.

## The visibility gap

Business stakeholders ask: *"Is the Executive Sales Report data ready?"*
Airflow reports: *"Task `extract_sales` succeeded; `transform_sales` is queued."*

To translate technical state into business value, deploy specific tools for specific audiences:

| Audience | Tool | Focus |
|---|---|---|
| **Data Engineers / SREs** | Astronomer Grafana | Infrastructure health, resource usage, scheduler latency, pod metrics [B6][B7]. |
| **Business Stakeholders** | Astro Observe | SLA tracking, Data Product readiness, end-to-end data health [B1][B2]. |
| **Compliance / PMO** | Custom BI (Tableau/Looker) | Formatted historical reports, SLA trends over time, WCC-style status reports. |

## Strategy 1: Astro Observe for business stakeholders

Astro Observe is the primary tool for translating Airflow runs into business terms [B1]:
- **Data Products**: Group pipelines into logical products (e.g., "Marketing Analytics"). Stakeholders monitor the product, not the DAG [B1][B2].
- **SLA Dashboards**: Visualize whether the data will be delivered on time [B1][B4].
- **Lineage**: Provide transparency into upstream dependencies without requiring stakeholders to read DAG code [B1][B5].

## Strategy 2: Tailoring Grafana for operational leadership

Astronomer provides pre-built Grafana dashboards for cluster and deployment monitoring [B6][B7]. While intended for engineers, you can create custom "Executive Views" within Grafana:
- Hide low-level metrics (e.g., Kubernetes memory pressure).
- Surface high-level KPIs: Pipeline Success Rate, DAG Duration Trends, and Active Alert counts [B4][B11].

> **Security Note**: Ensure Grafana dashboards exposing operational metrics are protected behind your organization's IdP (SSO) and that access is restricted to authorized users [B11].

## Strategy 3: Custom BI reporting (Replacing WCC)

For formal, structured reporting (similar to legacy WCC output):
1. **Metadata Tagging**: Enforce strict tagging on all DAGs (e.g., `tags=['department:finance', 'priority:high']`) [B9].
2. **Airflow REST API**: Use a script to extract metadata (run status, durations, failures) via the Airflow REST API [B13][B14].
3. **Centralized BI**: Pipe this data into a data warehouse and use your organization's existing BI tool (Tableau, PowerBI, Looker) to generate formatted, scheduled status reports for PMO and compliance teams.

## Sources

[B1, B2, B4] Astronomer Docs — Astro Observe Data Products and SLAs (accessed 2026-08-08)
[B5] DBTA — Astro Observe lineage and health (accessed 2026-08-08)
[B6, B7] Astronomer Docs — Grafana cluster and deployment dashboards (accessed 2026-08-08)
[B9] Orchestra — Airflow metadata tagging best practices (accessed 2026-08-08)
[B11] Hoop.dev — Grafana access management (accessed 2026-08-08)
[B13, B14] Apache Airflow Docs — REST API reference (accessed 2026-08-08)
