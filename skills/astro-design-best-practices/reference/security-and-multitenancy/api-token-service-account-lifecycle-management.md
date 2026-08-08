# API Token and Service-Account Lifecycle Management

AutoSys service accounts were OS-level accounts on the agent machines — managed by the enterprise LDAP/AD team. Astro's automation surface is API-token based: any CI/CD pipeline, Terraform, or external system that drives Astro does so via a scoped API token.

## Token types and scope

| Token type | Scope | Typical use |
|---|---|---|
| **Organization API token** | All Workspaces and Deployments in the org | SCIM setup; org-wide automation |
| **Workspace API token** | One Workspace | Workspace-level CI/CD; IaC provisioning |
| **Deployment API token** | One Deployment | DAG deployment; per-Deployment automation |

Always use the **narrowest scope** sufficient for the task — Deployment-level tokens for per-Deployment CI/CD, not Workspace or Org tokens.

## Token lifecycle design

```
Create (scoped, named, with expiry)
  → Store in secret manager (never in source code or plain env files)
  → Expose as $ASTRO_API_TOKEN to CI/CD
  → Monitor: lastUsedAt, endAt fields
  → Rotate before expiry: astro deployment token rotate
  → Revoke immediately if compromised: delete via Astro UI or CLI
```

## Lifecycle best practices

| Practice | Implementation |
|---|---|
| **Never hardcode tokens** | Store in GitHub Actions Secrets, HashiCorp Vault, or cloud-native secret manager |
| **Set explicit expiry** | Set a defined `endAt` on every token at creation; monitor `endAt` field |
| **Scheduled rotation** | Use `astro deployment token rotate` (CLI) in an automated pipeline; update secret manager with new value |
| **Revocation on compromise** | Delete immediately via Astro UI or CLI; verify no active automation depends on it before deleting |
| **Audit usage** | Monitor `lastUsedAt` via Astro API; clean up tokens not used in > 90 days |

## Workload Identity: the preferred alternative for cloud resources

For Airflow tasks accessing AWS, GCP, or Azure resources, **prefer Workload Identity over API tokens** [B-Workload]:

```
Worker pod → Kubernetes SA → Cloud IAM role binding → Cloud resource (S3, BigQuery, etc.)
```

No static credentials, no rotation, cloud-native audit trail per call. API tokens are for Astro _platform_ automation (CI/CD, Terraform); Workload Identity is for task-level _data_ access.

## Tools for token-driven automation

| Tool | Best fit |
|---|---|
| **Astro CLI** (`ASTRO_API_TOKEN`) | Local dev, manual admin tasks |
| **Astro API** | Complex automation, CI/CD pipelines, custom integrations |
| **Astro Terraform Provider** | IaC-driven infrastructure; declarative; version-controlled |

## Org model (Axis D — H rating)

| Org model | Token strategy |
|---|---|
| **Centralized platform team** | Platform team holds Org-level CI/CD tokens; teams get Deployment-level tokens |
| **Federated self-service** | Each team manages their own Deployment-level tokens; Platform team audits via Organization audit logs |

## Compliance callout (Axis E — H rating)

For SOX/HIPAA environments:
- All API token creation, rotation, and revocation events appear in Astro audit logs (see topic 039) — export to SIEM
- Enforce expiry on all tokens; indefinite tokens are a compliance risk
- SCIM deprovisioning removes user access but does not automatically revoke API tokens created by that user — implement a token inventory audit process

## Sources

[API token lifecycle] Astronomer Docs — API token management: https://www.astronomer.io/docs/astro/api-tokens (accessed 2026-08-08)
[astro token rotate] Astronomer CLI Docs — `astro deployment token rotate` (accessed 2026-08-08)
[B-Workload] Astronomer Docs — Workload Identity: https://www.astronomer.io/docs/astro/authorize-deployments-to-your-cloud (accessed 2026-08-08)
[Terraform] Astronomer Docs — Astro Terraform Provider (accessed 2026-08-08)
