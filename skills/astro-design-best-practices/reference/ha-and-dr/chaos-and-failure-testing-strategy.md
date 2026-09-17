# Chaos and Failure-Testing Strategy

AutoSys's HA had deterministic failure modes: if the primary scheduler's heartbeat missed a threshold, the shadow promoted itself. Airflow's distributed architecture has different, less obvious failure paths. Proactive chaos testing is required to validate assumptions about resilience before a real incident exposes them.

**Citation-quality note (Critic-pass finding)**: nearly every claim in this file cites [B1] or [B2], but both Sources entries are themselves flagged "no Astronomer Docs match found — verify separately." That makes most of the `[B1]`/`[B2]` markers below functionally decorative rather than real traceability — they point at a *category* of source ("Airflow OSS behavior," "chaos-engineering community practice"), not a specific verified page. The individual behavioral claims (task-marked-failed-on-pod-kill, active-active double-trigger risk on boundary failures, standard Kubernetes/chaos-engineering tooling) reflect well-established Airflow/Kubernetes operational knowledge and are plausible, but none of them has been independently re-verified against a live source on this pass. Treat this file as a lower-confidence, `NEEDS_EXEC_CHECK` reference until someone runs the actual chaos drills it describes — which is, appropriately, exactly what the file itself recommends doing before trusting any resilience assumption.

## Failure Mode Map

| Component | Failure Scenario | Expected Airflow Behavior | Test Method |
|---|---|---|---|
| **Worker Pod** | Pod killed mid-task execution | Task marked as `failed`; scheduler reschedules it (if retries > 0) [B1] | `kubectl delete pod <worker-pod>` in a staging deployment |
| **Scheduler Pod** | Scheduler crashes | Other active scheduler replicas continue; crashed replica restarts via K8s [B1] | `kubectl delete pod <scheduler-pod>` |
| **Metadata DB** | DB latency spike | Task state changes slow; scheduler heartbeat may lag | Inject latency using `tc netem` or a proxy (e.g., Toxiproxy) |
| **Metadata DB** | DB failover (RDS Multi-AZ) | Brief connectivity loss (typically 30–60s); scheduler reconnects | Trigger an RDS failover event from the AWS console |
| **External Dependency** | Downstream API timeout | Task fails; retry with exponential backoff (if configured) | Use Toxiproxy to introduce timeout on the connection |
| **Resource Exhaustion** | Worker CPU/Memory at limit | Task gets OOMKilled; pod restarts | Run a resource-heavy task in a constrained environment |

## Chaos Testing Principles

1. **Minimize blast radius**: Always test on isolated staging Deployments, never production [B1].
2. **Define steady-state first**: Know what "healthy" looks like (task completion rate, scheduler heartbeat interval, DAG parse time) before injecting failures [B1].
3. **Test incrementally**: Start with single-pod kills before testing DB failovers or full region outages.

## Tooling

- **Kubernetes-native**: `kubectl delete pod` for worker and scheduler pod termination tests [B1].
- **LitmusChaos**: An open-source Kubernetes chaos engineering framework for structured failure injection (pod kills, network delays, disk pressure) [B1].
- **Toxiproxy**: A proxy for simulating network conditions (latency, connection drops) between Airflow components and external dependencies.

## What to Validate in Each Test

| What to Validate | Why |
|---|---|
| Tasks retry correctly after worker failure | Confirms `retries` and `retry_delay` are configured correctly [B1]. |
| Scheduler heartbeat recovers within expected SLA | Validates replica count is sufficient for your load [B2]. |
| DAGs are **idempotent** after task retry | Critical — active-active schedulers can trigger tasks twice on boundary failures [B2]. |
| No zombie tasks accumulate after repeated pod kills | Tests scheduler cleanup logic and `scheduler_zombie_task_threshold` configuration [B2]. |

## Integration with CI/CD

Incorporate a lightweight resilience check in your staging deployment pipeline [B1]:
- Run `dag.test()` on critical DAGs to catch import errors or dependency failures early.
- Use `astro dev parse` as a pre-merge gate.
- Consider a weekly scheduled chaos drill on the staging environment, treating resilience as a continuous practice rather than a one-time validation.

## Sources

[B1] Astronomer Docs and Community — Chaos engineering principles for Airflow deployments (no Astronomer Docs match found on this pass — likely community/blog content or general chaos-engineering practice, not a dedicated Astronomer product page; verify separately)
[B2] Apache Airflow Docs — Scheduler HA, zombie task handling, idempotency best practices (no Astronomer Docs match found on this pass — this is Apache Airflow OSS content not indexed in the Astronomer docs MCP; verify against airflow.apache.org directly)
