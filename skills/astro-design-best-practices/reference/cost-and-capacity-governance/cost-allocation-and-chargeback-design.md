# Cost Allocation and Chargeback Design Across Workspaces/Deployments

Astro's platform provides a native showback layer; the actual financial chargeback transaction (GL posting, internal cross-charge) happens in your finance system, not in Astro. The design challenge is building the bridge between Astro's usage data and your internal cost accounting process.

## Astro's Cost Hierarchy

{syn: AutoSys instance → Astro Deployment (cost unit), AutoSys application group → Astro Workspace}

| Astro Object | Cost Attribution Role |
|---|---|
| **Deployment** | The fundamental cost unit. Each Deployment has dedicated compute (scheduler, workers, webserver). Costs accrue per AU consumed by each component [B1]. |
| **Workspace** | Groups Deployments belonging to a team, department, or cost center. Primary aggregation level for showback reporting [B1]. |

## Showback: What Astro Provides Natively

- **Cost Breakdown Dashboard**: Available in the Astro UI, showing consumption by Workspace and Deployment broken down by component (scheduler, worker, webserver) [B1].
- **Astro API Export**: Programmatically pull usage metrics from the Astro Platform API to feed into your internal FinOps tooling or BI dashboard [B1].

## Chargeback: What You Build

Astro does not perform GL posting or internal budget transfers. You build this layer [B1]:

1. **Pull usage data** from the Astro API on a scheduled cadence (daily or monthly).
2. **Map Deployment names to cost center codes** using a maintained mapping table (e.g., `Deployment: finance-prod → Cost Center: CC-4521`).
3. **Push cross-charge data** to your ERP or finance system.

**Naming convention rule**: Astro does not support arbitrary key-value tagging on Deployments (unlike cloud provider resources). Your naming convention (`{team}-{env}-{domain}`) IS your cost attribution metadata — enforce it via Terraform and code review gates [B1][B2].

## Best Practices

| Practice | Rationale |
|---|---|
| **Every Workspace and Deployment must have a declared owner** | Prevents unattributed cost accumulation [B1]. |
| **One Workspace per cost center (at minimum)** | Simplifies showback query: `GROUP BY workspace_name = cost center` [B1]. |
| **Manage Deployments via Terraform** | Enforces naming convention at creation time; prevents ad-hoc Deployments with non-standard names [B2]. |
| **Export usage data to your BI layer monthly** | Integrates Astro costs into the same showback report as your cloud provider spend [B1]. |

## Sources

[B1] Astronomer Docs — Cost Breakdown Dashboard, Astro API usage export, Workspace-as-cost-center pattern, and FinOps guidance (accessed 2026-08-11)
[B2] Astronomer Docs — Astro Terraform Provider for Deployment management and naming convention enforcement (accessed 2026-08-11)
