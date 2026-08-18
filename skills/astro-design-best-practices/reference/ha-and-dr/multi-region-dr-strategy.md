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

Cross-region DR is available for **Enterprise Business Critical** tier customers on dedicated clusters (AWS and GCP; Azure support is a roadmap item) [B1][B3].

> **NEEDS_EXEC_CHECK**: Validate current Azure DR availability and tier requirements against the Astro product page at time of contract renewal, as these are subject to change.

## Components NOT Covered by Astro's Managed DR

Your runbook must explicitly cover these even when using managed DR [B2]:
- **Remote Execution Agents**: If using Remote Execution, the execution plane runs in your own infrastructure and is excluded from Astro's failover. You must deploy standby agents in the secondary region [B2].
- **Networking & DNS**: Customer-managed routing (VPC peering, Transit Gateway, PrivateLink) must be pre-configured for the secondary region [B2].
- **External Data Dependencies**: Databases, secrets managers, and third-party APIs that DAGs connect to must be accessible from the secondary region [B2].

## Sources

[B1] Astronomer Docs — Astro Disaster Recovery overview (accessed 2026-08-10)
[B2] Astronomer Docs — DR shared responsibility model and runbook guidance (accessed 2026-08-10)
[B3] Astronomer Docs — Cross-region DR configuration, RTO/RPO targets (accessed 2026-08-10)
