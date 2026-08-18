---
name: astro-design-best-practices
description: >
  Production-grade Astro/Airflow architecture and design-best-practice guidance
  for teams migrating from AutoSys (CA WA AE), organized by design concern
  (scheduler/DAG design, executor/worker architecture, metadata DB, security,
  observability, CI/CD, config/secrets, HA/DR, regulatory/compliance, and
  more) rather than by JIL construct. Use this skill when the question is
  "how should we architect this on Astro," not "what does this JIL attribute
  map to" — the companion `migrating-autosys-*` skills cover the latter.
metadata:
  author: Quest1
  version: "0.1.0"
  status: "COMPLETE — all 130 of 130 planned topics shipped"
  source_project: astro-design-best-practices
---

# astro-design-best-practices

## Overview

130 planned topic files across 19 clusters (see `tasks/README.md` in this repo
for the full roadmap and the axis relevance matrix), each produced by the
Researcher → Human Source Check → Generator → Critic → Human Sign-off
pipeline defined in `AGENTS.md`. Every claim in every file traces to a
`## Sources` section; every recommendation that bridges an AutoSys mechanism
to an Astro/Airflow design is marked `{syn: ...}` and built transparently
from cited facts, per `AGENTS.md` Design Principle #6.

**Topics 001-020 (all of Cluster 1 — Scheduler & DAG Design, plus the first 7
of Cluster 2 — Executor & Worker Architecture) were generated autonomously,
with the mandatory Human Source Check and Human Sign-off gates explicitly
skipped per direct instruction** — a fresh-context Critic pass was still run
on each batch (001-010: `research/cluster-1-topics-001-010-critic-report.md`;
011-020: `research/topics-011-020-critic-report.md`), and found real defects
in both batches — including, in the second batch, two outright `FAIL`
verdicts on files that had fabricated specific numbers or cited a source that
didn't actually support the claim. All findings were fixed directly in the
shipped files. Nothing in either batch has had a human open the cited
sources, run the `NEEDS_EXEC_CHECK` items, or formally sign off. Treat every
file in both batches as **draft-quality, Critic-checked but not
human-verified**, until someone completes `.agents/signoff-checklist.md` for
each.

## Reference Files — Cluster 1: Scheduler & DAG Design

- `reference/scheduler-and-dag/dag-factory-pattern-for-large-estates.md` — config-driven DAG generation for estates too large to hand-write one DAG per box; estate-scale decision table.
- `reference/scheduler-and-dag/dag-versioning-and-change-management.md` — Airflow 3 DAG bundles/versioning vs. JIL's in-place mutation model; Git-backed bundle recommendation.
- `reference/scheduler-and-dag/scheduler-ha-and-leader-election.md` — Airflow's active-active scheduler HA vs. AutoSys's primary/shadow/tie-breaker model.
- `reference/scheduler-and-dag/dag-parsing-performance-budget.md` — `min_file_process_interval`/`parsing_processes` tuning, tied directly to the DAG-factory topic's top-level-code rule.
- `reference/scheduler-and-dag/taskgroups-vs-separate-dags.md` — extends the imported skill's box→DAG decision tree with the concurrency-isolation signal.
- `reference/scheduler-and-dag/cross-dag-dependencies-datasets-vs-triggerdagrun-vs-externaltasksensor.md` — Asset (formerly Dataset) vs. `TriggerDagRunOperator` vs. `ExternalTaskSensor`, mapped onto AutoSys cross-box condition patterns.
- `reference/scheduler-and-dag/dynamic-task-mapping-design.md` — `.partial()`/`.expand()` design for AutoSys's runtime job-cloning pattern.
- `reference/scheduler-and-dag/custom-timetable-design-for-autosys-calendars.md` — custom `Timetable` design for `run_calendar`/`exclude_calendar`, extending the imported skill's calendar rules.
- `reference/scheduler-and-dag/dag-level-sla-and-catchup-backfill-policy.md` — Airflow 3's SLA removal (replaced by experimental Deadline Alerts in 3.1) and the new `catchup=False` default; **flags a staleness conflict in the imported `alerting-and-sla.md` file, not yet corrected**.
- `reference/scheduler-and-dag/idempotency-and-retry-design.md` — `n_retrys` → `retries` migration requires an idempotency classification step JIL never had.
- `reference/scheduler-and-dag/concurrency-controls-pools-and-max-active-runs.md` — Pools vs. `max_active_runs` mechanics, mapped onto `machine-load-and-virtual-resources` cluster's AutoSys `max_load`/`job_load`/virtual-resource concepts.
- `reference/scheduler-and-dag/naming-and-tagging-conventions-at-scale.md` — `dag_id`/`tags` mapped onto AutoSys's `box_name` (structural) vs. `group`/`application` (cross-cutting classification) two-axis model.
- `reference/scheduler-and-dag/one-off-and-ad-hoc-job-design.md` — Params/`dag_run.conf` design for genuinely one-off jobs, kept separate from the DAG-factory's recurring-box config schema.

Cluster 1 (Scheduler & DAG Design, 13 topics) is now complete.

## Reference Files — Cluster 2: Executor & Worker Architecture (in progress, 7 of 11)

- `reference/executor-and-worker/celeryexecutor-vs-kubernetesexecutor-decision-framework.md` — decision table keyed off AutoSys `machine:` pinning patterns and job-volume burstiness.
- `reference/executor-and-worker/worker-queue-segregation-mirroring-machine-groups.md` — classifies *why* AutoSys machine groups existed before translating them into Astro worker queues, rather than a 1:1 machine→queue mapping.
- `reference/executor-and-worker/autoscaling-design-for-bursty-batch-workloads.md` — min/max/concurrency sizing for AutoSys-shaped batch-window bursts.
- `reference/executor-and-worker/per-task-resource-requests-and-limits.md` — `executor_config`/`pod_override` sizing from AutoSys machine-tier signals; a Critic pass caught and corrected an inverted claim about Kubernetes' actual admission-time failure behavior.
- `reference/executor-and-worker/node-affinity-and-taints-for-specialized-jobs.md` — taints/tolerations vs. soft affinity, mapped onto *why* a job was machine-pinned, not just that it was.
- `reference/executor-and-worker/keda-based-autoscaling.md` — the specific autoscaling formula and polling/cool-down mechanics; **contains an unresolved `NEEDS_EXEC_CHECK`** on a real ambiguity between two different cool-down figures found in different sources.
- `reference/executor-and-worker/hybrid-executor-strategy.md` — distinguishes `CeleryKubernetesExecutor` (queue-level routing) from `KubernetesPodOperator` (operator-level, executor-independent) as two genuinely different hybrid mechanisms.

## Reference Files — Cluster 8: HA & DR Design (complete, 5 of 5)

- `reference/ha-and-dr/scheduler-ha-what-astro-provides-vs-what-you-design.md` — Active-active vs AutoSys primary/shadow model, tie-breaker elimination, replica count and DB HA responsibility split.
- `reference/ha-and-dr/multi-region-dr-strategy.md` — Control Plane/Data Plane DR roles, warm standby, one-click failover, Remote Execution agent gap, Enterprise Business Critical tier requirement.
- `reference/ha-and-dr/backup-cadence-and-rto-rpo-design.md` — Managed Cloud RTO < 1hr / RPO < 15min targets, Velero + PITR for Private Cloud self-hosted, RTO tier design table.
- `reference/ha-and-dr/dr-runbook-design.md` — Decision matrix for failover triggers, pre-failover checklist, Astro UI execution steps, post-failover validation, failback procedure, IaC for secondary region networking.
- `reference/ha-and-dr/chaos-and-failure-testing-strategy.md` — Failure mode map (worker/scheduler/DB), LitmusChaos and Toxiproxy tooling, steady-state definition, idempotency validation.

## Reference Files — Cluster 9: Regulatory & Compliance Design (complete, 7 of 7)

- `reference/regulatory-and-compliance/audit-trail-immutability-design.md` — Two-layer audit model (Astro control-plane log vs. Airflow execution log), 90-day default retention, WORM storage patterns, SIEM hash-chaining.
- `reference/regulatory-and-compliance/data-retention-and-erasure-lifecycle-design.md` — `airflow db clean`, Deletion DAG pattern for GDPR Right-to-be-Forgotten, cryptographic erasure, WORM backup warning.
- `reference/regulatory-and-compliance/data-lineage-for-regulatory-reporting.md` — OpenLineage pre-installed in Astro Runtime, Listener API, Marquez/Atlan/Astro Observe backends, SOX/AML/GDPR use-cases.
- `reference/regulatory-and-compliance/access-control-granularity-for-regulated-data.md` — Hierarchical RBAC (Org/Workspace/Deployment/DAG), DAG-level roles on Runtime 3.1-12+, physical vs. logical isolation, sensitive data masking keywords.
- `reference/regulatory-and-compliance/vertical-overlay-financial-services-sox-basel-aml.md` — SOX Section 404 controls, AML data traceability, Basel BCBS 239 accuracy/completeness controls.
- `reference/regulatory-and-compliance/vertical-overlay-healthcare-hipaa.md` — BAA pre-condition, dedicated single-tenant cluster requirement, PHI-in-logs prohibition, query-in-place architecture.
- `reference/regulatory-and-compliance/vertical-overlay-government-fedramp-data-residency.md` — FedRAMP status flagged NEEDS_EXEC_CHECK, data residency via Private Cloud/Remote Execution, Terraform for ConMon IaC.

## Reference Files — Cluster 10: Integration & Enterprise Mesh Design (complete, 6 of 6)

- `reference/integration-and-enterprise-mesh/erp-batch-integration-patterns.md` — Trigger-and-Poll vs. flat-file patterns for homegrown ERP; Deferrable Operators for long batch windows; dedicated worker queues.
- `reference/integration-and-enterprise-mesh/edi-and-file-transfer-integration-patterns.md` — `SFTPToS3Operator`/`S3ToSFTPOperator`, AS2 via AWS Transfer Family, `SFTPSensor` with `mode='reschedule'`.
- `reference/integration-and-enterprise-mesh/ticketing-and-itsm-integration-design.md` — Airflow → PagerDuty → ServiceNow hub-and-spoke model, `dedup_key` for retry deduplication, severity-to-priority mapping.
- `reference/integration-and-enterprise-mesh/siem-export-integration-design.md` — Dual log stream architecture (Audit Log API + Vector sidecar for task logs), Splunk HEC and Sentinel integration.
- `reference/integration-and-enterprise-mesh/bi-and-reporting-layer-integration.md` — Event-driven data-first refresh pattern, Looker/Power BI/Tableau operators, Write-Audit-Publish pattern.
- `reference/integration-and-enterprise-mesh/mainframe-boundary-astro-side-architecture.md` — Orchestration Swap (Zowe CLI) vs. Replatformed Runtime patterns, JCL-to-Airflow concept mapping.

## Reference Files — Cluster 11: Migration Execution & Coexistence Architecture (complete, 4 of 4)

- `reference/migration-execution-and-coexistence/dual-run-shadow-dag-architecture.md` — Three coexistence modes (AutoSys-Triggered, Side-by-Side, Airflow-Controlled), feature-flag kill switch, staging output paths.
- `reference/migration-execution-and-coexistence/data-reconciliation-architecture-for-parity-verification.md` — Dedicated reconciliation DAG, schema/row-count/hash checks, JSON parity report, N-cycle exit criteria.
- `reference/migration-execution-and-coexistence/cutover-architecture-per-box.md` — Pre-conditions checklist, ON_HOLD quiesce sequence, cross-domain dependency bridging (ExternalTaskSensor/Datasets), 2-4 cycle observation period.
- `reference/migration-execution-and-coexistence/rollback-architecture-during-cutover.md` — Go/No-Go threshold table, 4-step rollback execution, data integrity orphan cleanup, no-shared-DB rule.

## Reference Files — Cluster 12: Cost & Capacity Governance (complete, 4 of 4)

- `reference/cost-and-capacity-governance/cost-allocation-and-chargeback-design.md` — Showback (native) vs. chargeback (your ERP); Workspace-as-cost-center; naming convention as tagging substitute; Terraform enforcement.
- `reference/cost-and-capacity-governance/capacity-planning-from-job-count-and-schedule-density.md` — AU definition (0.1 vCPU + 0.375 GiB), Small/Medium/Large/XL templates by DAG count, schedule density impact on DAG Processor, Triggerer ~1,000 trigger capacity.
- `reference/cost-and-capacity-governance/autoscaling-cost-optimization-patterns.md` — Scale-to-zero managed autoscaling, queue segregation for long-running tasks, KEDA/HPA conflict warning, Deferrable Operators as idle reduction.
- `reference/cost-and-capacity-governance/idle-resource-reclamation-design.md` — Deployment Hibernation (Development Mode required), Wake Schedule configuration, ephemeral CI/CD Deployment pattern, right-sizing via Analytics dashboard.

## Reference Files — Cluster 13: Governance & Operating Model (complete, 6 of 6)

- `reference/governance-and-operating-model/centralized-vs-federated-operating-model.md` — Centralized bottleneck vs. federated CoE model; Workspace-per-domain team; CoE owns guardrails (infra, RBAC, Golden Path); domain teams own DAGs.
- `reference/governance-and-operating-model/dag-ownership-and-support-model-design.md` — `owner` field + `tags` for UI discoverability; `doc_md` runbook standard; task-level SLA alerts; anti-patterns (anonymous ownership, Confluence-only docs).
- `reference/governance-and-operating-model/legacy-job-deprecation-process.md` — Scream test, burn-in period (2–8 weeks by criticality), blast-radius assessment, JIL archive in Git, 5-phase decommission sequence.
- `reference/governance-and-operating-model/documentation-as-code-strategy.md` — `doc_md=__doc__` pattern, standard 6-section header (Purpose/Owner/SLA/Dependencies/Recovery/Impact), task-level doc_md.
- `reference/governance-and-operating-model/training-enablement-for-autosys-ops-staff.md` — JIL→Airflow mental model table, 3 role-based training tracks, 6-week program structure, pilot-before-rollout principle.
- `reference/governance-and-operating-model/vendor-lock-in-and-exit-strategy-design.md` — Lock-in vector matrix, exit steps (DAG portability, variable export, Helm deployment), `ObjectStoragePath` for cloud-agnostic storage.

## Reference Files — Cluster 14: Multi-Instance & Cross-Instance Architecture (complete, 5 of 5)

- `reference/multi-instance-and-cross-instance/multi-instance-topology-mapping.md` — AutoSys instance/`$AUTOSERV`/`$AUTOUSER` → Astro Deployment; per-instance Event Server → per-Deployment metadata DB; instance scheduler → Deployment scheduler pod.
- `reference/multi-instance-and-cross-instance/ca-cci-cross-instance-to-cross-deployment-triggering.md` — CAICCI `sendevent` → Airflow REST API trigger; AS2 gateway pattern; cross-Deployment REST pattern using `SimpleHttpOperator`; Datasets as modern replacement.
- `reference/multi-instance-and-cross-instance/cross-instance-dependencies-to-dataset-rest-patterns.md` — `CHANGE_STATUS` → `ExternalTaskSensor` (status) or Datasets (data); critical `execution_delta` gotcha; cross-Deployment sentinel-file bridge pattern.
- `reference/multi-instance-and-cross-instance/job-classification-group-application-to-tagging-namespacing.md` — `group`/`application` → `tags`; `application` → `dag_id` namespace prefix; hierarchical `dag_id` convention; tag vocabulary for operational filtering.
- `reference/multi-instance-and-cross-instance/multi-timezone-autotimezone-to-pendulum-design.md` — `autotimezone`/JIL `timezone` → `pendulum.datetime(..., tz=...)` `start_date`; UTC-internal storage; spring-forward gap and fall-back overlap DST edge cases; `timedelta` as DST-agnostic alternative.

## Reference Files — Cluster 15: Machine Load, Queuing & Virtual Resources (complete, 4 of 4)

- `reference/machine-load-and-virtual-resources/max-load-job-load-to-airflow-pools-sizing.md` — `max_load` (capacity) → Pool slots; `job_load` (weight) → `pool_slots` parameter; sizing formula; `default_pool` 128-slot default warning.
- `reference/machine-load-and-virtual-resources/virtual-resources-to-airflow-pools-and-dag-concurrency.md` — Named virtual resource (semaphore) → named Pool; Pool is global per-Deployment; `max_active_tasks_per_dag` and `max_active_runs_per_dag` as additional controls with no AutoSys equivalent; migration decision tree.
- `reference/machine-load-and-virtual-resources/virtual-machine-groups-to-executor-queue-design.md` — Virtual machine (machine group) → CeleryExecutor named queue (`queue` parameter) or KubernetesExecutor node selector (`executor_config`); executor choice decision matrix.
- `reference/machine-load-and-virtual-resources/que-wait-to-queued-state-observability.md` — `QUE_WAIT` → Airflow `queued` state; three root causes (pool exhaustion, worker capacity, scheduler health); key metrics (`executor.queued_tasks`, `pool.open_slots`, `scheduler.heartbeats`).

## Reference Files — Cluster 16: Native Security & Credential Architecture (complete, 4 of 4)

- `reference/native-security-and-credentials/ca-eem-to-astro-rbac-provider-design.md` — CA EEM cannot be used as Astro IdP; use corporate AD/LDAP via Okta/Entra ID directly; EEM group → Astro Team via SCIM; API Tokens replace EEM service accounts for CI/CD.
- `reference/native-security-and-credentials/autosys-secure-to-astro-rbac-bootstrap.md` — `autosys_secure` bootstrap → Astro SSO config + SCIM + Terraform Workspace/Deployment creation; bootstrap checklist; SSO enforcement (disable basic auth) as equivalent of security-mode lock-in.
- `reference/native-security-and-credentials/pam-credential-vaulting-to-astro-secrets-backend.md` — PAM → Secrets Backend (Vault/AWS Secrets Manager/GCP/Azure); `AIRFLOW__SECRETS__BACKEND` config; cascading lookup order; `Variable.set()` read-only gotcha; Workload Identity for authentication.
- `reference/native-security-and-credentials/rsa-ig-access-review-to-astro-periodic-access-review.md` — Explicit gap: no native access-certification automation; Astro API/CLI for programmatic user-role export; review cadence by risk level; JML controls; compliance evidence collection.

## Reference Files — Cluster 17: Reporting, Forecasting & Operational Visibility (complete, 3 of 3)

- `reference/reporting-and-forecasting/forecast-feature-capability-gap-design.md` — Explicit gap: AutoSys Forecast is a forward-looking simulation; Airflow Gantt chart is backward-looking observability — NOT equivalent. Three design options: simulation DAG, Astro Observe + Prometheus, ITSM integration. DAG pause/unpause as maintenance window mechanism.
- `reference/reporting-and-forecasting/autorep-to-airflow-metadata-db-reporting.md` — `autorep -J/-M/-c/-G` flags mapped to REST API or SQL equivalents; key tables (`dag_run`, `task_instance`, `variable`); read-replica requirement for analytics queries; REST API as scheduler-safe operational query path.
- `reference/reporting-and-forecasting/cross-instance-to-multi-deployment-dashboard-design.md` — AutoSys WCC → Astro Organization Dashboard + Astro Observe; explicit gap: no cross-Deployment task search in single query; federated Prometheus + Grafana as enterprise-grade alternative.

## Reference Files — Cluster 18: Native ERP & Web-Service Integration Agents (complete, 5 of 5)

- `reference/native-erp-and-webservice-agents/sap-application-job-to-airflow-sap-provider.md` — `apache-airflow-providers-sap`; SAP NWRFC SDK in Dockerfile; `SAPRfcHook`; `JOB_OPEN`/`JOB_SUBMIT`/`JOB_CLOSE` RFC pattern for background ABAP jobs; SAP HANA is a separate provider.
- `reference/native-erp-and-webservice-agents/peoplesoft-agent-to-airflow-custom-operator.md` — No native provider (gap); custom `PeopleSoftHook` + `PeopleSoftProcessOperator`; Integration Broker REST target; `PS_PMN_PRCSLIST` polling with `mode='reschedule'`.
- `reference/native-erp-and-webservice-agents/oracle-ebs-agent-to-airflow-custom-operator.md` — No native provider (gap); `OracleHook` + `fnd_request.submit_request`; `fnd_global.apps_initialize` required; phase_code `C`/status_code `N` for success detection; `OracleSqlSensor(mode='reschedule')`.
- `reference/native-erp-and-webservice-agents/ws-job-type-to-http-operator-design.md` — `job_type: WS` (no wrapper script) → `HttpOperator`; SOAP requires `zeep` in custom `PythonOperator`; `HttpSensor(mode='reschedule')` for polling; credentials in Airflow Connections.
- `reference/native-erp-and-webservice-agents/aews-rest-api-to-airflow-rest-api-parity.md` — AEWS is inbound control-plane API (distinct from WS job type); `FORCE_START_JOB` → `POST /dagRuns`; `ON_ICE` → `PATCH /dags` `is_paused`; `dag_run_id` for idempotent triggers (409 on duplicate).

## Reference Files — Cluster 19: Container-Native Agent & Legacy-Estate Precision (complete, 9 of 9)

- `reference/container-native-and-legacy-precision/k8s-container-agent-to-kubernetespodoperator.md` — AutoSys K8s job type (Connection Profile, no in-container agent) → KubernetesPodOperator; `container_resources`, `env_vars`, `get_logs` mapping.
- `reference/container-native-and-legacy-precision/multi-container-pod-exec-parity-design.md` — Explicit gap: no native `target_container` exec in KPO; three design alternatives (dedicated image recommended; `full_pod_spec` init container; `kubectl exec` anti-pattern).
- `reference/container-native-and-legacy-precision/legacy-machine-type-inventory-cleanup.md` — Only `a`-type is current; `n`/`l`/`L`/`r` deprecated; cannot change type in-place (delete + recreate); `force: y` for jobs with active references; cleanup procedure with `autorep -M ALL`.
- `reference/container-native-and-legacy-precision/client-surface-inventory-to-astro-parity-mapping.md` — Full inventory: `jil`/`autorep`/`sendevent`/WCC/AEWS/SDK → DAG code/REST API/Astro CLI/Airflow UI; WCC ECLI gap explicitly flagged; per-team migration readiness checklist.
- `reference/container-native-and-legacy-precision/event-server-rdbms-to-metadata-db-migration-source.md` — Oracle/SQL Server/Sybase/PostgreSQL Event Server dialects; DataMigrator utility; AutoSys history MUST NOT be imported to Airflow metadata DB (schema incompatibility); archive to data warehouse instead.
- `reference/container-native-and-legacy-precision/native-db-job-type-to-sql-operator-design.md` — Native DB job type → `SQLExecuteQueryOperator` (unified) / `PostgresOperator`/`OracleOperator`/`MsSqlOperator`; SQL in `include/sql/`; `SQLColumnCheckOperator` as Airflow-native value-add.
- `reference/container-native-and-legacy-precision/ha-poll-interval-to-airflow-scheduler-ha-design.md` — AutoSys Active/Passive (Primary/Shadow, `HAPollInterval` 15s) → Airflow Active/Active multi-scheduler; `scheduler.heartbeat_interval` 5s; `scheduler_health_check_threshold` 30s; no separate tie-breaker needed.
- `reference/container-native-and-legacy-precision/ep-rollover-to-astro-failover-alerting.md` — `EP_ROLLOVER`/`DB_ROLLOVER` alarms → `scheduler.heartbeats == 0` Prometheus alert; `sendevent -E STOP_DEMON -v FAILOVER` → scale scheduler replicas for controlled test; no processing pause in Airflow failover.
- `reference/container-native-and-legacy-precision/job-history-audit-trail-to-metadata-db-migration.md` — DBMaint utility; archive EventServer history (Oracle/SQL Server/Sybase) to data warehouse; `airflow db clean --clean-before-timestamp` maintenance DAG; compliance continuity: AutoSys archive = pre-cutover trail; Airflow metadata = post-cutover trail.

## Known open items

- A fresh-context Critic pass found and fixed 6 real defects across this batch (wrong parameter name, two unsupported citations, one citation-number swap, one now-outdated sub-claim, one already-resolvable `NEEDS_EXEC_CHECK`) — see `research/cluster-1-topics-001-010-critic-report.md`. What remains open genuinely requires a human running something real, not just re-reading:
  - `dag-factory-pattern-for-large-estates.md` — confirm `is_paused_upon_creation` behaves as documented (an open Airflow GitHub issue questions its reliability).
  - `scheduler-ha-and-leader-election.md` — the "2+, up to 4 schedulers" guidance is sourced from Astronomer *Software* v0.37 docs; re-confirm against current Cloud/Hybrid.
  - `dag-level-sla-and-catchup-backfill-policy.md` — confirm Deadline Alerts' production-readiness on the actual target Astro Runtime version (still marked experimental upstream).
- The 011-020 batch's Critic pass found and fixed 5 more defects, including **2 outright FAILs** (see `research/topics-011-020-critic-report.md`): a fabricated polling-interval/cool-down number in `keda-based-autoscaling.md`, and two claims in `per-task-resource-requests-and-limits.md` cited to a source that supported neither (one was corrected — and in the process, found to be *backwards*: real Kubernetes behavior is a clean admission-time rejection, not a silent stuck pod — the other was removed entirely since no real source could be found). What remains open:
  - `keda-based-autoscaling.md` — a genuine, unresolved ambiguity between the Airflow Helm chart's general `cooldownPeriod: 30`s default and separate KEDA documentation describing a 300s/5-minute cool-down specific to scale-to-zero. Needs resolving against a real deployed `ScaledObject`, not further documentation research.
- `dag-level-sla-and-catchup-backfill-policy.md` flags that the imported `skills/migrating-autosys-to-astronomer/reference/alerting-and-sla.md` needs a correction (its "Airflow 3: SLA callbacks" line is stale — SLA was removed in 3.0, confirmed independently by both the original research and the Critic pass). Not fixed here; that's a different skill's file.
- `SETUP-4` (seed source list) and `SETUP-6` (formal scaffold task) were done informally as part of generating this batch, not as their own gated tasks — see `tasks/README.md` for the formal tracker state.
