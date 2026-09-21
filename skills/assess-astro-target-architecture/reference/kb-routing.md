---
topic: kb-routing
family: assessment
skill: assess-astro-target-architecture
verified_against:
  autosys: "12.0"
last_verified: 2026-09-17
confidence: cited
signals: []
---

# KB Routing

Which of the `astro-design-best-practices` topics apply to a given estate, keyed off
inventory signals (booleans/flags computed by `inventory_stats.py`, `condition_graph.py`,
`command_analysis.py`, `score_estate.py`). Do not load all 130 topics for every engagement --
route from the manifest's signals through this table instead.

**Signal vocabulary** (~40 signals; add here when a new one is introduced in a KB file's
front-matter): `or_conditions, lookback, cross_instance, hidden_flow, mutex_n, job_load_present,
virtual_resources, calendar_not_cron, run_window, must_complete_times, svcdesk, erp_sap, erp_ps,
erp_oracle, zos, windows, credential_hits, factory_candidate, deep_boxes, multi_instance,
multi_owner, brownfield_astro, residency, hipaa, sox, fedramp`.

<!-- GENERATED: DO NOT EDIT BELOW THIS LINE -->

## Signal -> topics

### `brownfield_astro`

- `container-native-and-legacy-precision/client-surface-inventory-to-astro-parity-mapping.md`
- `container-native-and-legacy-precision/k8s-container-agent-to-kubernetespodoperator.md`
- `container-native-and-legacy-precision/legacy-machine-type-inventory-cleanup.md`
- `container-native-and-legacy-precision/multi-container-pod-exec-parity-design.md`
- `migration-execution-and-coexistence/dual-run-shadow-dag-architecture.md`

### `calendar_not_cron`

- `scheduler-and-dag/custom-timetable-design-for-autosys-calendars.md`

### `credential_hits`

- `config-and-secrets/environment-specific-connection-management.md`
- `config-and-secrets/secret-rotation-strategy.md`
- `config-and-secrets/variables-vs-connections-vs-secrets-backend-decision-framework.md`
- `native-security-and-credentials/autosys-secure-to-astro-rbac-bootstrap.md`
- `native-security-and-credentials/ca-eem-to-astro-rbac-provider-design.md`
- `native-security-and-credentials/pam-credential-vaulting-to-astro-secrets-backend.md`
- `native-security-and-credentials/rsa-ig-access-review-to-astro-periodic-access-review.md`
- `regulatory-and-compliance/access-control-granularity-for-regulated-data.md`
- `security-and-multitenancy/api-token-service-account-lifecycle-management.md`
- `security-and-multitenancy/connection-scoping-and-least-privilege.md`
- `security-and-multitenancy/rbac-role-shape-design-mirrored-from-eem-entitlements.md`

### `cross_instance`

- `multi-instance-and-cross-instance/ca-cci-cross-instance-to-cross-deployment-triggering.md`
- `multi-instance-and-cross-instance/cross-instance-dependencies-to-dataset-rest-patterns.md`
- `scheduler-and-dag/cross-dag-dependencies-datasets-vs-triggerdagrun-vs-externaltasksensor.md`

### `deep_boxes`

- `migration-execution-and-coexistence/cutover-architecture-per-box.md`
- `scheduler-and-dag/taskgroups-vs-separate-dags.md`

### `erp_oracle`

- `integration-and-enterprise-mesh/erp-batch-integration-patterns.md`
- `native-erp-and-webservice-agents/oracle-ebs-agent-to-airflow-custom-operator.md`

### `erp_ps`

- `integration-and-enterprise-mesh/erp-batch-integration-patterns.md`
- `native-erp-and-webservice-agents/peoplesoft-agent-to-airflow-custom-operator.md`

### `erp_sap`

- `integration-and-enterprise-mesh/erp-batch-integration-patterns.md`
- `native-erp-and-webservice-agents/sap-application-job-to-airflow-sap-provider.md`

### `factory_candidate`

- `migration-execution-and-coexistence/orbiter-vs-otto-vs-hand-translation.md`
- `migration-execution-and-coexistence/otto-assisted-translation-workflow.md`
- `scheduler-and-dag/dag-factory-pattern-for-large-estates.md`

### `fedramp`

- `regulatory-and-compliance/vertical-overlay-government-fedramp-data-residency.md`

### `hipaa`

- `regulatory-and-compliance/vertical-overlay-healthcare-hipaa.md`

### `job_load_present`

- `cost-and-capacity-governance/capacity-planning-from-job-count-and-schedule-density.md`
- `executor-and-worker/autoscaling-design-for-bursty-batch-workloads.md`
- `executor-and-worker/worker-fleet-capacity-planning-methodology.md`
- `machine-load-and-virtual-resources/max-load-job-load-to-airflow-pools-sizing.md`
- `machine-load-and-virtual-resources/que-wait-to-queued-state-observability.md`
- `metadata-db-and-state/metadata-db-growth-at-scale.md`
- `scheduler-and-dag/concurrency-controls-pools-and-max-active-runs.md`

### `multi_instance`

- `multi-instance-and-cross-instance/ca-cci-cross-instance-to-cross-deployment-triggering.md`
- `multi-instance-and-cross-instance/multi-instance-topology-mapping.md`
- `multi-instance-and-cross-instance/multi-timezone-autotimezone-to-pendulum-design.md`
- `reporting-and-forecasting/cross-instance-to-multi-deployment-dashboard-design.md`
- `security-and-multitenancy/multi-team-config-scoping.md`

### `multi_owner`

- `governance-and-operating-model/centralized-vs-federated-operating-model.md`
- `governance-and-operating-model/dag-ownership-and-support-model-design.md`
- `multi-instance-and-cross-instance/job-classification-group-application-to-tagging-namespacing.md`
- `scheduler-and-dag/naming-and-tagging-conventions-at-scale.md`
- `security-and-multitenancy/federated-vs-centralized-self-service-design.md`
- `security-and-multitenancy/multi-team-config-scoping.md`
- `security-and-multitenancy/workspace-and-deployment-boundary-design.md`

### `must_complete_times`

- `observability-and-alerting/sla-miss-detection-and-escalation.md`
- `scheduler-and-dag/dag-level-sla-and-catchup-backfill-policy.md`
- `scheduler-and-dag/deadline-alerts-status-and-fallbacks.md`

### `residency`

- `regulatory-and-compliance/vertical-overlay-government-fedramp-data-residency.md`

### `sox`

- `regulatory-and-compliance/audit-trail-immutability-design.md`
- `regulatory-and-compliance/vertical-overlay-financial-services-sox-basel-aml.md`

### `svcdesk`

- `integration-and-enterprise-mesh/ticketing-and-itsm-integration-design.md`

### `virtual_resources`

- `executor-and-worker/gpu-specialized-compute-worker-design.md`
- `executor-and-worker/node-affinity-and-taints-for-specialized-jobs.md`
- `executor-and-worker/worker-queue-segregation-mirroring-machine-groups.md`
- `machine-load-and-virtual-resources/virtual-machine-groups-to-executor-queue-design.md`
- `machine-load-and-virtual-resources/virtual-resources-to-airflow-pools-and-dag-concurrency.md`

### `zos`

- `integration-and-enterprise-mesh/mainframe-boundary-astro-side-architecture.md`

## Unrouted (no `signals:` front-matter yet)

- `cicd-and-environment-topology/airflowctl-and-astro-cli-division-of-labor.md`
- `cicd-and-environment-topology/astro-cli-deploy-pipeline-design.md`
- `cicd-and-environment-topology/branching-strategy-for-dag-code.md`
- `cicd-and-environment-topology/dag-testing-and-parse-gates-before-merge.md`
- `cicd-and-environment-topology/dev-staging-prod-deployment-topology.md`
- `cicd-and-environment-topology/environment-promotion-process.md`
- `cicd-and-environment-topology/feature-flagging-for-gradual-dag-rollout.md`
- `cicd-and-environment-topology/gitops-design-for-dag-deployment.md`
- `cicd-and-environment-topology/local-development-environment-standards.md`
- `cicd-and-environment-topology/multi-region-deployment-topology-at-scale.md`
- `cicd-and-environment-topology/rollback-strategy-design.md`
- `config-and-secrets/config-as-code-for-dag-factory-inputs.md`
- `config-and-secrets/global-variable-sprawl-remediation.md`
- `config-and-secrets/per-environment-variable-scoping.md`
- `container-native-and-legacy-precision/ep-rollover-to-astro-failover-alerting.md`
- `container-native-and-legacy-precision/event-server-rdbms-to-metadata-db-migration-source.md`
- `container-native-and-legacy-precision/ha-poll-interval-to-airflow-scheduler-ha-design.md`
- `container-native-and-legacy-precision/job-history-audit-trail-to-metadata-db-migration.md`
- `container-native-and-legacy-precision/native-db-job-type-to-sql-operator-design.md`
- `cost-and-capacity-governance/autoscaling-cost-optimization-patterns.md`
- `cost-and-capacity-governance/cost-allocation-and-chargeback-design.md`
- `cost-and-capacity-governance/idle-resource-reclamation-design.md`
- `executor-and-worker/celeryexecutor-vs-kubernetesexecutor-decision-framework.md`
- `executor-and-worker/hybrid-executor-strategy.md`
- `executor-and-worker/keda-based-autoscaling.md`
- `executor-and-worker/legacy-server-access-via-sshoperator.md`
- `executor-and-worker/per-task-resource-requests-and-limits.md`
- `executor-and-worker/zombie-task-detection-and-handling.md`
- `governance-and-operating-model/documentation-as-code-strategy.md`
- `governance-and-operating-model/legacy-job-deprecation-process.md`
- `governance-and-operating-model/training-enablement-for-autosys-ops-staff.md`
- `governance-and-operating-model/vendor-lock-in-and-exit-strategy-design.md`
- `ha-and-dr/backup-cadence-and-rto-rpo-design.md`
- `ha-and-dr/chaos-and-failure-testing-strategy.md`
- `ha-and-dr/dr-runbook-design.md`
- `ha-and-dr/multi-region-dr-strategy.md`
- `ha-and-dr/scheduler-ha-what-astro-provides-vs-what-you-design.md`
- `integration-and-enterprise-mesh/bi-and-reporting-layer-integration.md`
- `integration-and-enterprise-mesh/edi-and-file-transfer-integration-patterns.md`
- `integration-and-enterprise-mesh/siem-export-integration-design.md`
- `metadata-db-and-state/airflow-2-to-3-in-place-upgrade-constraints.md`
- `metadata-db-and-state/backup-and-point-in-time-recovery.md`
- `metadata-db-and-state/connection-pooling-with-pgbouncer.md`
- `metadata-db-and-state/custom-xcom-backend-design.md`
- `metadata-db-and-state/db-migration-strategy-across-airflow-upgrades.md`
- `metadata-db-and-state/metadata-retention-and-cleanup-policy.md`
- `metadata-db-and-state/postgres-sizing-and-instance-class-selection.md`
- `metadata-db-and-state/read-replica-strategy-for-reporting.md`
- `migration-execution-and-coexistence/data-reconciliation-architecture-for-parity-verification.md`
- `migration-execution-and-coexistence/rollback-architecture-during-cutover.md`
- `native-erp-and-webservice-agents/aews-rest-api-to-airflow-rest-api-parity.md`
- `native-erp-and-webservice-agents/ws-job-type-to-http-operator-design.md`
- `observability-and-alerting/alert-fatigue-and-deduplication-strategy.md`
- `observability-and-alerting/astronomer-alerts-routing-and-escalation.md`
- `observability-and-alerting/astronomer-observe-integration.md`
- `observability-and-alerting/dashboard-design-for-stakeholder-visibility.md`
- `observability-and-alerting/incident-ticket-automation.md`
- `observability-and-alerting/log-architecture-remote-storage-and-retention.md`
- `observability-and-alerting/metrics-export-prometheus-datadog.md`
- `observability-and-alerting/on_failure_callback-design-patterns.md`
- `observability-and-alerting/openlineage-data-lineage-integration.md`
- `regulatory-and-compliance/data-lineage-for-regulatory-reporting.md`
- `regulatory-and-compliance/data-retention-and-erasure-lifecycle-design.md`
- `reporting-and-forecasting/autorep-to-airflow-metadata-db-reporting.md`
- `reporting-and-forecasting/forecast-feature-capability-gap-design.md`
- `scheduler-and-dag/dag-parsing-performance-budget.md`
- `scheduler-and-dag/dag-versioning-and-change-management.md`
- `scheduler-and-dag/dynamic-task-mapping-design.md`
- `scheduler-and-dag/human-in-the-loop-operators-for-wait-reply.md`
- `scheduler-and-dag/idempotency-and-retry-design.md`
- `scheduler-and-dag/one-off-and-ad-hoc-job-design.md`
- `scheduler-and-dag/scheduler-ha-and-leader-election.md`
- `security-and-multitenancy/audit-log-design-for-access-and-actions.md`
- `security-and-multitenancy/encryption-at-rest-and-in-transit-design.md`
- `security-and-multitenancy/network-isolation-and-vpc-peering.md`
- `security-and-multitenancy/secrets-backend-selection.md`
- `security-and-multitenancy/sso-oauth-integration-design.md`

