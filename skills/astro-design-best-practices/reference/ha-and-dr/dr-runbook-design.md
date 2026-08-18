# DR Runbook Design

AutoSys dual-Event-Server / Shadow-Scheduler runbooks were complex: they documented manual promotion steps, `autosys_secure` commands, and tie-breaker reconfiguration. Astro's managed DR significantly simplifies execution steps, but a formal runbook remains essential for organizational readiness, RTO accountability, and audit trails.

## Runbook Sections

### 1. Failure Criteria (Decision Matrix)

Do not trigger a failover without clear criteria. Ambiguity causes delayed response or unnecessary migrations.

| Condition | Action |
|---|---|
| Primary region AZ failure (single AZ) | **Do nothing** — data plane is multi-AZ; Astro self-heals [B1]. |
| Primary region fully unavailable (all AZs down) | **Trigger failover** via Astro UI or API [B1][B2]. |
| Degraded task completion rate > X% for > Y minutes | **Escalate to on-call; assess root cause** before triggering DR. |
| Primary cluster unreachable from Astro UI | **Confirm via cloud provider console** before triggering failover [B2]. |

### 2. Pre-Failover Checklist

- [ ] Confirm primary cluster status in the Astro UI (Settings > Clusters).
- [ ] Verify the secondary cluster is in "warm standby" and replication is current [B1].
- [ ] Confirm external data services (DB, secrets manager, API endpoints) are accessible from the secondary region.
- [ ] Notify stakeholder communications chain (SLA owners, NOC, business owners).
- [ ] Document the failover start timestamp for RTO tracking.

### 3. Execution Steps (Astro Cloud with Managed DR)

1. Navigate to the **Astro UI > Clusters > [Primary Cluster] > Disaster Recovery**.
2. Click **"Failover to Secondary Region"** [B1][B2].
3. Confirm the operation. The control plane will reroute traffic; hostnames remain unchanged [B1].
4. Monitor the secondary cluster in the Astro UI until all Deployments show healthy.
5. If using **Remote Execution**: scale up or activate standby execution agents in the secondary region [B2].

### 4. Post-Failover Validation

- [ ] Verify all critical Deployments show "Running" health status.
- [ ] Confirm task logs are appearing correctly in the Airflow UI.
- [ ] Trigger a canary DAG run on each critical pipeline.
- [ ] Confirm external system integrations (DB writes, S3 reads, API calls) are functioning.
- [ ] Update the internal status page.

### 5. Failback Steps

Once the primary region is restored and verified:
1. Confirm primary cluster health in the Astro UI.
2. Click **"Failback to Primary Region"** [B1].
3. Allow the platform to re-synchronize state from the secondary back to the primary.
4. Validate all pipelines are running normally on the primary.
5. Debrief and update the runbook.

## Runbook Hygiene Rules

- **Treat the runbook as living documentation**: update after every drill or infrastructure change [B2].
- **Schedule a DR drill at least quarterly**: A DR plan is only as reliable as its last successful test [B2].
- **IaC for secondary region network config**: Use Terraform to pre-configure VPC peering, Transit Gateway routes, and PrivateLink for the secondary region. Manual configuration under outage pressure is error-prone [B2].

## Sources

[B1] Astronomer Docs — Astro Disaster Recovery one-click failover and failback (accessed 2026-08-10)
[B2] Astronomer Docs — DR shared responsibility model and runbook design guidance (accessed 2026-08-10)
