# Vertical Overlay: Financial Services (SOX / Basel / AML)

This file translates the general compliance architecture patterns (Topics 074–077) into specific design decisions for financial services pipelines. It focuses on the three most common regulatory frameworks: SOX (internal controls), Basel III/IV (risk data quality), and AML (transaction monitoring).

## SOX — Sarbanes-Oxley Act (Internal Controls over Financial Reporting)

SOX Section 404 requires documented, operating internal controls over financial reporting pipelines [B-SOX]. Airflow must be treated as a production financial system.

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

BCBS 239 requires banks to accurately aggregate and report risk data. **Correction**: an earlier draft of this file cited "Principle 6 (Accuracy) and Principle 7 (Completeness)" with no source — both numbers were wrong. BCBS 239's actual numbering is **Principle 3 (Accuracy and Integrity)** and **Principle 4 (Completeness)** [B-BCBS239], and these directly apply to Airflow pipelines processing risk data:
- Every pipeline feeding a risk report must have **data quality gate tasks** that halt the pipeline if accuracy thresholds are not met (preventative control).
- OpenLineage lineage graphs provide auditors with automated, always-current evidence of the pipeline-to-report mapping required by BCBS 239's traceability mandate [B3].

## Sources

[B1] Astronomer Blog — SOX compliance architecture for data pipelines (no Astronomer Docs match found on this pass — likely a specific blog post not indexed by the docs search; verify separately)
[B2] Astronomer Docs — Audit logs: https://www.astronomer.io/docs/astro/audit-logs and Astro user permissions reference (RBAC): https://www.astronomer.io/docs/astro/user-permissions (tier 1, URLs added on citation review — CI/CD-specific guidance for regulated environments wasn't independently re-verified on this pass)
[B3] Astronomer Docs — Configure OpenLineage on Astro: https://www.astronomer.io/docs/astro/observe-openlineage (tier 1, URL added on citation review — covers OpenLineage generally; AML-specific data-traceability framing is a project-internal application of it, not a distinct Astronomer doc page)
[B-SOX] U.S. Securities and Exchange Commission / SOX legislative text — Sarbanes-Oxley Act Section 404 (internal controls over financial reporting): https://www.sec.gov/spotlight/sarbanes-oxley.htm (tier 3 — external legal/regulatory text, not an Astronomer source; added on Critic-pass review since this is a load-bearing legal claim the original draft left uncited)
[B-BCBS239] Basel Committee on Banking Supervision — BCBS 239, "Principles for effective risk data aggregation and risk reporting" (Principle 3: Accuracy and Integrity; Principle 4: Completeness): https://www.bis.org/publ/bcbs239.pdf (tier 3 — external regulatory text, not an Astronomer source; added on Critic-pass review, corrects the wrong principle numbers above)
