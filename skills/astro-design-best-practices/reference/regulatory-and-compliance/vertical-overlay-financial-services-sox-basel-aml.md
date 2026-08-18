# Vertical Overlay: Financial Services (SOX / Basel / AML)

This file translates the general compliance architecture patterns (Topics 074–077) into specific design decisions for financial services pipelines. It focuses on the three most common regulatory frameworks: SOX (internal controls), Basel III/IV (risk data quality), and AML (transaction monitoring).

## SOX — Sarbanes-Oxley Act (Internal Controls over Financial Reporting)

SOX Section 404 requires documented, operating internal controls over financial reporting pipelines. Airflow must be treated as a production financial system.

**Technical Controls to Implement:**

| Control | SOX Requirement | Astro Implementation |
|---|---|---|
| **Change Management** | All pipeline changes must follow a formal approval process | Git-based CI/CD with mandatory PR review and branch-protection rules [B1]. |
| **Segregation of Duties** | Developers cannot approve their own changes OR access audit logs | RBAC: separate `Dev`, `Reviewer`, and `Auditor` roles across Workspaces; audit logs exported to a restricted SIEM [B1][B2]. |
| **Automated Controls** | Pipelines must include preventative/detective controls | Embed pre- and post-load validation tasks (schema check, null count, record count reconciliation) in every financial pipeline [B1]. |
| **Auditability** | Prove the pipeline ran as designed, not altered post-run | Immutable audit logs (see topic 074) + OpenLineage for data provenance [B2]. |

## AML — Anti-Money Laundering

AML transaction monitoring models depend on high-quality, traceable data. The risk: if input data is tampered with or incorrectly processed, suspicious transaction flags may be suppressed or fabricated.

**Design Decisions:**
- **Feature engineering pipelines** (building AML model inputs) must have OpenLineage tracing enabled so auditors can prove that sensitive customer data was handled according to retention and masking policies [B3].
- **Automated reconciliation tasks** should verify that the row count and aggregated value of AML input tables match the expected values from the source systems before model scoring runs.
- **Alert on pipeline failure** immediately — a failed AML pipeline is a regulatory event, not just an operational event. Use Astro Alerts with escalation to the compliance team (see topic 050).

## Basel III / IV (BCBS 239) — Risk Data Quality

BCBS 239 requires banks to accurately aggregate and report risk data. Principle 6 (Accuracy) and Principle 7 (Completeness) directly apply to Airflow pipelines processing risk data:
- Every pipeline feeding a risk report must have **data quality gate tasks** that halt the pipeline if accuracy thresholds are not met (preventative control).
- OpenLineage lineage graphs provide auditors with automated, always-current evidence of the pipeline-to-report mapping required by BCBS 239's traceability mandate [B3].

## Sources

[B1] Astronomer Blog — SOX compliance architecture for data pipelines (accessed 2026-08-10)
[B2] Astronomer Docs — Audit logs, RBAC, and CI/CD for regulated environments (accessed 2026-08-10)
[B3] Astronomer — OpenLineage for financial services lineage and AML data traceability (accessed 2026-08-10)
