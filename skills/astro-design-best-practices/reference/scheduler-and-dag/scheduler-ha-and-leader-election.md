# Scheduler HA and Leader Election

AutoSys's HA model is primary/shadow/tie-breaker: three distinct scheduler processes, heartbeat-monitored via `HAPollInterval` (default 15s), with an explicit failover event (`EP_ROLLOVER`) when the primary goes silent. Airflow's model is architecturally different, not a drop-in replacement of the same pattern.

## Core mechanics

- Airflow does **not** use a leader/follower model for scheduler HA. Every Scheduler instance is fully active simultaneously ("active-active"), not a leader with standbys [F1].
- The metadata database itself is the shared coordination mechanism — schedulers use it as a shared queue and synchronization point, which is why no separate leader-election protocol or additional network configuration is needed [F1].
- Running multiple Scheduler replicas both provides high availability (no single point of failure) and horizontal scaling (more replicas increase task-scheduling throughput under load) [F1][F2a][F2b].
- **The replica model is genuinely different across deployment models, not just a difference in defaults — resolved below.**

## {syn: F1,F2a,F2b} Design guidance

Do not attempt to replicate AutoSys's primary/shadow/tie-breaker three-role model on Astro — there is no equivalent role structure to map onto, and building one would fight the platform rather than use it. The correct translation is structural, not role-for-role: AutoSys's "avoid a single scheduling brain going down" *goal* is met by Astro's active-active scheduler replication, not by manually designating one Airflow scheduler as primary and others as standby.

## Deployment-model callout (resolves the earlier `NEEDS_EXEC_CHECK`)

The "2+, up to 4 schedulers" guidance was originally sourced from Astronomer *Software* v0.37 docs and flagged for reconfirmation against current Cloud/Hybrid. Reconfirming against current docs shows the model has genuinely diverged by platform, not just by version:

- **Astro Private Cloud / Hybrid**: still a configurable replica count, **up to 4 by default** (platform administrators can override the cap) [F2b]. Provision 2+ for production HA, same guidance as before.
- **Astro Hosted**: this is **not** a configurable replica count at all. A Deployment runs a **single scheduler by default**; enabling the **High Availability** toggle runs exactly **two** schedulers (and two PgBouncer instances) — there is no path to 3 or 4 on Hosted [F2a]. Treat HA on Astro Hosted as binary (on/off), not as a slider.

Design accordingly: on Hosted, "provision at least 2 schedulers" means "turn on the High Availability toggle," full stop — there is no additional tuning available. On Private Cloud/Hybrid, replica count is a real sizing decision with headroom up to 4.

## What AutoSys operators should unlearn

There is no "primary scheduler" to check the status of, no manual failover to trigger, and no `EP_ROLLOVER`-equivalent alarm to alert on — under active-active HA, a scheduler replica going down is a capacity reduction handled by the remaining replicas continuing to read from the shared metadata DB, not a failover event requiring any operator action. Alerting design for "we lost a scheduler replica" is a capacity/observability concern (see the Observability & Alerting cluster), not a failover-detection concern.

## Sources

- [F1] Astronomer Blog — Benefits of the Airflow 2.0 Scheduler (active-active model, shared-DB coordination): https://www.astronomer.io/blog/airflow-2-scheduler/ (tier 1)
- [F2a] Astronomer Docs — Scheduler (Astro Hosted): single scheduler by default; the **High Availability** toggle runs exactly two schedulers (and two PgBouncer instances) — not a configurable count: https://www.astronomer.io/docs/astro/deployment-resources#scheduler (tier 1)
- [F2b] Astronomer Docs — Airflow system components, "Horizontal scaling" (Astro Private Cloud / Hybrid): Scheduler supports up to 4 replicas by default: https://www.astronomer.io/docs/astro-private-cloud/v-2-x/airflow-system-components#horizontal-scaling (tier 1) — confirms the "up to 4" figure still holds for Private Cloud/Hybrid on current docs, resolving the earlier `NEEDS_EXEC_CHECK`; it does **not** apply to Astro Hosted, see F2a.
- [F3] Apache Airflow Improvement Proposal — AIP-15 Support Multiple-Schedulers for HA & Better Scheduling Performance (background design rationale, not current operational guidance): https://cwiki.apache.org/confluence/pages/viewpage.action?pageId=103092651 (tier 2)
