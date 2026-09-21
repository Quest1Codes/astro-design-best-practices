---
topic: decision-tables
family: assessment
skill: assess-astro-target-architecture
verified_against:
  airflow: "3.3.1"
  astro_runtime: "3.3-2"
last_verified: 2026-09-17
confidence: mixed
signals: [residency, windows, zos, erp_sap]
---

# Decision tables — human mirror of `scripts/decision-tables.yaml`

confidence: mixed throughout — every Astro-side capability claim here should be re-verified
against current Astronomer documentation before being presented to a customer; this refactor did
not have Astronomer MCP access when these tables were authored (see `skills/docs/HANDOFF.md` §5).

Each row: condition on manifest/`nfr` fields → recommendation → KB topic(s) → confidence. First
matching rule wins; `recommend_architecture.py --override` records any human deviation with a
reason.

## Deployment model

| Condition | Recommendation |
|---|---|
| `nfr.residency` set | Dedicated (single-tenant, region-pinned) |
| `nfr.network_posture == private` | Hybrid |
| `nfr.brownfield_astro` truthy | Extend the existing footprint (see `astro_inventory.py` output) |
| (default) | Hosted |

KB: `ha-and-dr/scheduler-ha-what-astro-provides-vs-what-you-design.md`.

## Executor

| Condition | Recommendation |
|---|---|
| Brownfield signal shows an existing containerized/k8s footprint | KubernetesExecutor |
| ERP-family job share > 10% of the estate | KubernetesExecutor, or per-task `KubernetesPodOperator` override under CeleryExecutor |
| (default) | CeleryExecutor |

KB: `executor-and-worker/celeryexecutor-vs-kubernetesexecutor-decision-framework.md`.

## Worker queues

| Condition | Recommendation |
|---|---|
| ≥10 distinct machine groups referenced across the estate | One queue class per machine-group purpose cluster (see `manifest.stats.machine_load_pressure`) |
| (default) | Single default queue |

KB: `machine-load-and-virtual-resources/virtual-machine-groups-to-executor-queue-design.md`.

## Remote Execution agents

| Condition | Recommendation |
|---|---|
| ≥10 distinct machine groups | Evaluate Remote Execution agents per machine group — see `migrate-topology-onprem-distributed`; this is a hint to check per-group, not a per-group answer |
| (default) | Not evaluated |

## Metadata-DB tier

| Condition | Recommendation |
|---|---|
| Job count > 2000 | Larger instance class — see `size_target.db_tier()` |
| `nfr.dr_runbook_exists` truthy | Confirm retention/backup cadence matches the DR runbook |
| (default) | Standard instance class |

KB: `metadata-db-and-state/postgres-sizing-and-instance-class-selection.md`.

## Secrets backend

| Condition | Recommendation |
|---|---|
| `nfr.pam_solution` set | Integrate the existing PAM/vault as the Astro secrets backend |
| (default) | Astro-managed secrets backend or environment-variable Connections |

KB: `security-and-multitenancy/secrets-backend-selection.md`.

## Identity

| Condition | Recommendation |
|---|---|
| `nfr.idp` set | SSO via the existing IdP |
| (default) | Astro-native user management (small teams only) |

KB: `security-and-multitenancy/sso-oauth-integration-design.md`.

## Alerting / ITSM

| Condition | Recommendation |
|---|---|
| Any job flagged `itsm` (has `svcdesk_*` attributes, from `score_estate.py`) | Wire Astro Alerts to the existing ITSM tool |
| (default) | Astro Alerts to email/Slack |

KB: `observability-and-alerting/incident-ticket-automation.md`.

## Compliance overlay

| Condition | Recommendation |
|---|---|
| `nfr.compliance` set | Route to the matching `regulatory-and-compliance/vertical-overlay-*.md` topic(s) |
| (default) | No specific overlay identified |

## Greenfield vs. extend

| Condition | Recommendation |
|---|---|
| `nfr.brownfield_astro` truthy | Extend |
| (default) | Greenfield |
