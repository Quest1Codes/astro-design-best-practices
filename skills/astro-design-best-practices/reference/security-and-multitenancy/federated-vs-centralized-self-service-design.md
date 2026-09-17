# Federated vs. Centralized Self-Service Design

AutoSys estates ran in two common topologies:
- **One AutoSys instance per business unit** (federated): each BU owned its event server, agent fleet, and JIL definitions
- **One shared enterprise-wide AutoSys instance** (centralized): a central team managed the single event server; BUs submitted JIL and depended on shared agent pools

This topology maps directly onto the Astro platform design question: **who controls Workspace and Deployment creation?**

This topic covers the self-service and governance model. For the instance-topology migration mechanics (how to map source AutoSys instances to Astro), see topic 101.

## The core design choice

| Model | Who creates Workspaces/Deployments | Control | Overhead |
|---|---|---|---|
| **Centralized** | Central platform team only | High governance, consistent policy | High ops burden on platform team |
| **Federated self-service** | Teams provision own Deployments via CI/CD + templates | High autonomy, fast iteration | Requires investment in templates and governance guardrails |
| **Hybrid** | Platform team creates Workspaces; teams manage Deployments within | Balanced | Recommended for most large estates |

Astronomer explicitly recommends **per-team isolated Deployments** managed via automated CI/CD rather than a shared monolithic instance, regardless of topology model [B1][B4][B5][B7].

## Airflow 3 Multi-Team mode note — corrected

An earlier draft of this file recommended upstream Airflow 3.3's experimental "Multi-Team" mode as a design option for smaller orgs or cost-constrained setups where a full per-team Deployment isn't feasible. **This was wrong and has been removed as a recommendation**: Astronomer's own docs state plainly that "the Airflow 3 multi-team model isn't supported on Astro" [B13]. Do not design around it. The federated/centralized/hybrid choice above (Workspace and Deployment boundaries) is the actual mechanism for team separation on Astro — Multi-Team mode is not an available substitute for a smaller or cost-constrained org, regardless of what upstream Airflow itself supports.

## AutoSys topology → Astro design mapping

| Source AutoSys topology | Recommended Astro design |
|---|---|
| **Per-BU AutoSys instance** | Per-BU Workspace, each BU owns their Deployments; BU leads = Workspace Owners |
| **Shared enterprise-wide instance** | Shared Organization, with one Workspace per team cluster; Platform team = Org Owner; team leads = Workspace Owners in their Workspace |

## Platform engineering path for federated self-service (Axis D — H rating)

For large estates (> 10 teams) adopting a federated model:

1. **Golden-path Deployment templates** (Terraform / Astro Terraform provider): standardize Deployment config (Runtime version, executor type, resource sizing, secrets backend)
2. **CI/CD automation** (GitHub Actions, GitLab CI): teams trigger Deployment creation via PR; CI validates against platform standards [B7][B11]
3. **Centralized observability** (Astro UI Organization view): Platform team sees all Workspaces in a single pane of glass [B12]
4. **Authorized Workspaces**: restrict teams to deploying only on clusters pre-approved by the platform team

## Compliance callout (Axis E — H rating)

In regulated estates (SOX, HIPAA), the platform governance model must enforce:
- No un-audited Deployment creation (all Deployment changes via CI/CD with audit trail)
- RBAC applied at Workspace creation (not retroactively)
- SCIM-based user provisioning to prevent orphaned accounts (see topic 037)

## Sources

[B1, B4, B5] Astronomer Docs — Multi-tenancy in Airflow: https://www.astronomer.io/docs/learn/airflow-multi-tenancy (accessed 2026-08-08)
[B7, B11] Astronomer Blog — Platform engineering for Airflow at scale: https://www.astronomer.io/blog/platform-engineering-airflow (accessed 2026-08-08)
[B8, B9, B10] Apache Airflow Docs — Multi-Team mode (Airflow 3.3), upstream OSS capability only — **not applicable on Astro, see B13**: https://airflow.apache.org/docs/apache-airflow/stable/multi-team.html (accessed 2026-08-08)
[B12] Astronomer Docs — Organization management: https://www.astronomer.io/docs/astro/manage-organization (accessed 2026-08-08)
[B13] Astronomer Docs — Airflow feature support on Astro ("The Airflow 3 multi-team model isn't supported on Astro"): https://www.astronomer.io/docs/astro/airflow-feature-support (tier 1, added on doc-verification review)
