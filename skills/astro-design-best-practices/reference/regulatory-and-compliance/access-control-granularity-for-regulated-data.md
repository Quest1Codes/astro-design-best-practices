# Access-Control Granularity for Regulated Data

In regulated environments, "who can see what pipeline" is as important as "who can see what data." Astro's RBAC model supports multi-level access control, from Organization-wide administrator rights down to individual DAG visibility.

## Astro's Hierarchical RBAC Model

Access control flows through three nested scopes [B1]:

```
Organization
  └── Workspace
        └── Deployment
              └── DAG (DAG-level roles — Astro Runtime 3.1-12+)
```

Each level has a set of roles. Higher-level roles inherit permissions from lower levels; lower-level roles can be independently restricted [B1].

## DAG-Level Access Control

For regulated multi-team environments (e.g., Finance and Risk teams sharing one Deployment):
- Assign **DAG-level roles** to restrict which users, teams, or API tokens can view, trigger, or modify individual DAGs or groups of DAGs (by tag) [B1].
- Users without DAG-level access cannot see the DAG in the Airflow UI at all — it is fully hidden, not just read-only.

> **Important**: DAG-level roles are available on **Astro Runtime 3.1-12 or later**. Verify your target Astro Runtime version supports this feature before relying on it in a compliance design [B1].

## Physical Isolation vs. Logical Isolation

DAG-level RBAC is **logical** isolation within a shared Deployment. For strictly regulated data (HIPAA PHI, SOX financial data, classified data), consider **physical isolation** via separate Deployments or Workspaces [B1][B2]:

| Isolation Level | Mechanism | When to Use |
|---|---|---|
| **Logical** | DAG-level roles within one Deployment | Different teams on the same cluster with low cross-contamination risk. |
| **Physical** | Separate Deployments per team/regulation | HIPAA, SOX, or PCI-DSS use-cases where strict resource and metadata isolation is required. |
| **Network** | Astro Private Cloud or Remote Execution | Maximum isolation — data never leaves your perimeter. |

## Sensitive Data Masking in Task Logs

Airflow automatically masks values in task logs, rendered templates, and the Variables UI when the variable or connection field name contains substrings like `password`, `secret`, `token`, `key`, or `api` [B2]. You can extend this with custom sensitive field keywords to ensure regulated data (e.g., `ssn`, `dob`, `phi`) is always redacted before log ingestion [B2].

## Least-Privilege for API Tokens in CI/CD

Apply role-scoped API tokens to CI/CD automation pipelines. A deployment token that can only trigger specific DAGs and read task status should NOT have admin-level permissions [B1]. This prevents a compromised CI/CD secret from becoming a platform-wide incident.

## Sources

[B1] Astronomer Docs — RBAC model, DAG-level roles, Workspace and Deployment permission scopes (accessed 2026-08-10)
[B2] Astronomer Docs & Apache Airflow Docs — Sensitive data masking and custom keywords (accessed 2026-08-10)
