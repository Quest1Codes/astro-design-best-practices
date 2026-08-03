# Scheduler HA and Leader Election

AutoSys's HA model is primary/shadow/tie-breaker: three distinct scheduler processes, heartbeat-monitored via `HAPollInterval` (default 15s), with an explicit failover event (`EP_ROLLOVER`) when the primary goes silent. Airflow's model is architecturally different, not a drop-in replacement of the same pattern.

## Core mechanics

- Airflow does **not** use a leader/follower model for scheduler HA. Every Scheduler instance is fully active simultaneously ("active-active"), not a leader with standbys [F1].
- The metadata database itself is the shared coordination mechanism — schedulers use it as a shared queue and synchronization point, which is why no separate leader-election protocol or additional network configuration is needed [F1].
- Running multiple Scheduler replicas both provides high availability (no single point of failure) and horizontal scaling (more replicas increase task-scheduling throughput under load) [F1][F2a].
- Astronomer recommends provisioning 2 or more schedulers for production Deployments, with up to 4 supported per Deployment on Airflow 2.0+ [F2a].

## {syn: F1,F2a} Design guidance

Do not attempt to replicate AutoSys's primary/shadow/tie-breaker three-role model on Astro — there is no equivalent role structure to map onto, and building one would fight the platform rather than use it. The correct translation is structural, not role-for-role: AutoSys's "avoid a single scheduling brain going down" *goal* is met by Astro's active-active scheduler replication, not by manually designating one Airflow scheduler as primary and others as standby. Provision at least 2 schedulers on any production Deployment as the baseline HA posture [F2a].

## Deployment-model callout

This is provided by the Airflow Scheduler component itself and is available regardless of Astro Cloud, Hybrid, or Software — the difference across deployment models is *how many* replicas are practical to run and how they're provisioned (managed automatically on Astro Cloud/Hybrid vs. explicitly sized on Astro Software), not whether active-active HA exists at all.

## What AutoSys operators should unlearn

There is no "primary scheduler" to check the status of, no manual failover to trigger, and no `EP_ROLLOVER`-equivalent alarm to alert on — under active-active HA, a scheduler replica going down is a capacity reduction handled by the remaining replicas continuing to read from the shared metadata DB, not a failover event requiring any operator action. Alerting design for "we lost a scheduler replica" is a capacity/observability concern (see the Observability & Alerting cluster), not a failover-detection concern.

## Sources

- [F1] Astronomer Blog — Benefits of the Airflow 2.0 Scheduler (active-active model, shared-DB coordination): https://www.astronomer.io/blog/airflow-2-scheduler/ (tier 1)
- [F2a] Astronomer Docs — Configure a Deployment on Astronomer Software (scheduler replica-count guidance, "2+, up to 4"): https://www.astronomer.io/docs/astro-private-cloud/v-0-37/configure-deployment (tier 1) — **NEEDS_EXEC_CHECK**: this is Astronomer *Software* (self-hosted, v0.37) documentation; re-confirm the exact replica cap against current Astro Cloud/Hybrid Deployment settings before treating "up to 4" as universal across all three deployment models.
- [F3] Apache Airflow Improvement Proposal — AIP-15 Support Multiple-Schedulers for HA & Better Scheduling Performance (background design rationale, not current operational guidance): https://cwiki.apache.org/confluence/pages/viewpage.action?pageId=103092651 (tier 2)
