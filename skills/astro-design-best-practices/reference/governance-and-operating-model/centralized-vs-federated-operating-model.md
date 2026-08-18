# Centralized vs. Federated Operating Model Design

AutoSys was almost always run as a centralized service: one operations team owned all job definitions, schedules, and incidents. Airflow on Astro supports both models, but large-scale enterprises migrating from AutoSys inevitably encounter a design choice about who owns what in the new world.

## The Two Models

### Centralized Model

A single platform/ops team owns all Airflow infrastructure and DAG development.

**Advantages**: Consistent standards, simpler security posture, single point of expertise.

**Disadvantages**: Becomes a bottleneck at scale. Every new pipeline requires a ticket to the central team. Business unit engineers cannot self-serve. Replicas the same problem that made legacy AutoSys operations painful.

### Federated Model (Recommended at Scale)

A **Center of Excellence (CoE)** or Platform Team owns the guardrails; domain teams own their DAGs.

| Responsibility | CoE / Platform Team | Domain Team |
|---|---|---|
| Infrastructure (clusters, Workspaces) | ✅ Owns | Does not manage |
| Security, RBAC, network policies | ✅ Owns | Consumes |
| DAG standards, CI/CD templates ("Golden Path") | ✅ Defines | Follows |
| Actual DAG code | Provides templates only | ✅ Owns and develops |
| On-call for DAG-level incidents | Escalation path only | ✅ Primary owner |
| Cost governance | ✅ Monitors | ✅ Accountable per Workspace |

## Astro's Organizational Hierarchy Maps to the Federated Model

```
Organization (CoE-managed)
  └── Workspace (Domain Team A — Finance)
        └── Deployment: finance-prod
        └── Deployment: finance-dev
  └── Workspace (Domain Team B — Marketing)
        └── Deployment: marketing-prod
```

The CoE manages the Organization; domain teams manage their own Workspaces within it [B1]. RBAC prevents domain teams from crossing into other Workspaces [B1].

## Practical Migration Consideration

AutoSys operations staff transitioning to Airflow must evolve from reactive job operators to active pipeline co-owners. This is a cultural change, not just a technical one. The federated model accelerates this by giving domain teams real ownership [B1][B2].

## Sources

[B1] Astronomer Docs — Organization/Workspace/Deployment hierarchy, RBAC for federated team isolation (accessed 2026-08-11)
[B2] Astronomer Blog — Center of Excellence design for data platform teams (accessed 2026-08-11)
