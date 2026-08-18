# Variables vs. Connections vs. Secrets Backend Decision Framework

In AutoSys, everything from file paths to database passwords was often stored in global variables (`%%VAR%%`), leading to security and management issues. Airflow distinguishes between configuration and credentials, and Astronomer adds enterprise-grade secrets management.

Use this decision table to map legacy global variables to the correct Airflow mechanism.

## Decision Framework

| Use Case | Legacy AutoSys Pattern | Recommended Astro Mechanism | Why? |
|---|---|---|---|
| **External system credentials** (e.g., DB passwords, API keys) | Plaintext `VAR`, or external CyberArk integration | **Secrets Backend** (AWS Secrets Manager, HashiCorp Vault) | Secure storage, auditability, automated rotation. Airflow fetches at runtime, bypassing the metadata DB entirely [B1][B2]. |
| **Connection routing** (e.g., Host, Port, Login) | Machine definitions or `VAR` | **Airflow Connections** (stored in a Secrets Backend) | Native Airflow object designed for interfacing with external systems. Storing them in a backend secures the connection string [B1]. |
| **Non-sensitive global config** (e.g., Environment flags, batch limits) | `VAR` | **Airflow Variables** or **Astro Environment Manager** | Key-value store. Astro Environment Manager allows sharing these across multiple Deployments within a Workspace [B3]. |
| **Runtime environment data** (e.g., deployment region, k8s namespace) | System variables | **Environment Variables** (`os.getenv()`) | Best for static configuration that doesn't need to change dynamically. Defined in the Dockerfile or Astro UI [B4]. |
| **Local Development overrides** | Local text files | **Local `.env` file** | Git-ignored file used by `astro dev start` to mimic production secrets safely [B3]. |

## Security Precedence

When the same key exists in multiple places, Airflow resolves them in this order (highest to lowest):
1. **Secrets Backend**
2. **Environment Variables**
3. **Airflow Metadata Database** (Variables/Connections set in the UI) [B1]

> **Security Callout**: While you *can* store Connections and Variables in the Airflow UI, doing so stores them in the metadata database. For production, **always** use a Secrets Backend for sensitive data [B2].

## Sources

[B1] Astronomer Docs — Managing Secrets and Connections (accessed 2026-08-08)
[B2, B3] Astronomer Docs — Astro Environment Manager and Secrets Backends (accessed 2026-08-08)
[B4] Apache Airflow Docs — Environment Variables precedence (accessed 2026-08-08)
