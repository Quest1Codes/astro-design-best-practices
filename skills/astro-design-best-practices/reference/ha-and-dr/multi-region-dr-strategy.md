# Multi-Region Disaster Recovery Strategy

Astro's Control Plane / Data Plane separation directly enables a managed multi-region DR capability. This is a significant architectural advantage over AutoSys's dual-Event-Server DR model, which required customers to manually synchronize schema and state across locations.

## Architecture: Control Plane vs. Data Plane in DR Context

| Layer | DR Behavior |
|---|---|
| **Control Plane** (Astronomer-managed) | Remains globally available. Manages failover orchestration, state replication, and deployment metadata. It does NOT process your DAG tasks [B1]. |
| **Data Plane — Primary** | Runs in your selected primary region. Executes all Airflow tasks, stores task logs, manages the metadata DB [B1][B2]. |
| **Data Plane — Secondary** | Runs in a separate region in **warm standby**. Continuously synchronized with the primary. Does not execute tasks unless failover is triggered [B1][B2]. |

## What Gets Replicated Automatically

Astro handles replication of the following to the secondary region [B2][B3]:
- Airflow Deployment metadata (connections, variables, DAG run history, task instances)
- Task logs (via multi-region object storage, e.g., S3/GCS cross-region replication)
- Customer-deployed container images

## Triggering Failover

- **Mechanism**: Single-click failover in the Astro UI or via the Astro API [B1][B3].
- **User-Facing Impact**: Deployment hostnames (Airflow UI URL, API URL) remain unchanged after failover — the control plane updates its DNS routing automatically [B1].
- **Failback**: Once the primary region recovers, a single-click failback synchronizes state in the reverse direction [B1].

## Platform Tier Requirement

Cross-region DR is available for **Enterprise Business Critical** tier customers on dedicated clusters only — this is a hard gate, not a soft recommendation, and applies regardless of cloud provider [B1][B3][B4]. **Correction**: an earlier draft of this file stated Azure support was "a roadmap item" — this is wrong. Current docs show full, documented cluster-creation and existing-cluster-enablement paths for **all three providers — AWS, Azure, and GCP** [B4]. Azure is actually the most self-service of the three (enable DR directly from the Astro UI or API, no support ticket or maintenance window required, unlike AWS/GCP, which both require a support request and a maintenance window) [B4]. Note the overall cross-region DR capability is documented as **Preview** as of the most recent release notes covering it [B5] — confirm current GA/Preview status before treating it as a fully supported production dependency, but do not describe Azure specifically as behind AWS/GCP; the docs show it ahead if anything.

## Components NOT Covered by Astro's Managed DR

Your runbook must explicitly cover these even when using managed DR [B2]:
- **Remote Execution Agents**: If using Remote Execution, the execution plane runs in your own infrastructure and is excluded from Astro's failover. You must deploy standby agents in the secondary region [B2].
- **Networking & DNS**: Customer-managed routing (VPC peering, Transit Gateway, PrivateLink) must be pre-configured for the secondary region [B2].
- **External Data Dependencies**: Databases, secrets managers, and third-party APIs that DAGs connect to must be accessible from the secondary region [B2].

## Sources

[B1] Astronomer Docs — Disaster recovery overview: https://www.astronomer.io/docs/astro/disaster-recovery (tier 1, URL added on citation review)
[B2] Astronomer Docs — Shared responsibility model: https://www.astronomer.io/docs/astro/shared-responsibility-model (tier 1, URL added on citation review)
[B3] Astronomer Docs — Cross-region disaster recovery, RTO/RPO targets: https://www.astronomer.io/docs/astro/disaster-recovery#cross-region-disaster-recovery (tier 1, URL added on citation review)
[B4] Astronomer Docs — Create a dedicated Astro cluster (DR creation/enablement steps documented for AWS, Azure, and GCP; Azure enablement is self-service with no support ticket or maintenance window, unlike AWS/GCP): https://www.astronomer.io/docs/astro/create-dedicated-cluster (tier 1, added on doc-verification review — corrects the "Azure is a roadmap item" claim above)
[B5] Astronomer Docs — Release notes, March 11 2026 ("Cross-region disaster recovery for AWS dedicated clusters now in Preview"): https://www.astronomer.io/docs/astro/release-notes#march-11-2026 (tier 1, added on doc-verification review — confirms the feature's Preview status as of its most recent documented release; re-check current status before relying on GA availability)
