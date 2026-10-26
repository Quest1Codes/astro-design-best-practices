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
  version: "0.2.0"
  status: "DRAFT — 137 of 137 planned topics drafted; 24 Critic-checked; 0 human-signed-off"
  source_project: astro-design-best-practices
---

# astro-design-best-practices

## Overview

137 topic files across 19 clusters (see `tasks/README.md` in this repo for
the full roadmap and the axis relevance matrix). **This KB is a draft, not
verified content.** The Researcher → Human Source Check → Generator → Critic →
Human Sign-off pipeline in `AGENTS.md` has only partly run, and no topic has
passed either human gate. Treat every file as unreviewed until its row below
says otherwise.

**Provenance, by topic range** (from the 2026-10-22 whole-skill assessment,
`.work/_skill-assessment/critic-output.md`):

| Topics | Fact-sheet on record | Critic report on record | Human gates |
|---|---|---|---|
| 001–020 | `research/*-fact-sheet.md` (batched) | `research/*-critic-report.md` | Both skipped |
| 025–028 | `research/0NN-*.md` | `.work/0NN/critic-output.md` | Both skipped |
| 021–024, 029–130 | None | **None.** `.work/029–068/status.md` says "Critic DONE (inline)", but no Critic output exists, so treat these as not checked | Not run |
| 131–137 (Phase 2 refresh) | None (authored directly) | None | Not run |

Known quality gaps across the corpus: 13 files have no inline citation
markers; in 34 files the `{syn: ...}` tag lists fact rows that are never
cited in the body, or wraps prose instead of row IDs; only 24 files address
the relevance-matrix axes. The `verified_against` / `last_verified`
front-matter has not been machine-checked: the `versions.yaml`,
`tools/refresh_check.py` and `tools/lint_terms.py` that earlier versions of
this file referenced are not in the repo.

## Reference Files — Cluster 1: Scheduler & DAG Design

- `reference/scheduler-and-dag/dag-factory-pattern-for-large-estates.md` — config-driven DAG generation for estates too large to hand-write one DAG per box; estate-scale decision table.
- `reference/scheduler-and-dag/dag-versioning-and-change-management.md` — Airflow 3 DAG bundles/versioning vs. JIL's in-place mutation model; Git-backed bundle recommendation.
- `reference/scheduler-and-dag/scheduler-ha-and-leader-election.md` — Airflow's active-active scheduler HA vs. AutoSys's primary/shadow/tie-breaker model.
- `reference/scheduler-and-dag/dag-parsing-performance-budget.md` — `min_file_process_interval`/`parsing_processes` tuning, tied directly to the DAG-factory topic's top-level-code rule.
- `reference/scheduler-and-dag/taskgroups-vs-separate-dags.md` — extends the imported skill's box→DAG decision tree with the concurrency-isolation signal.
- `reference/scheduler-and-dag/cross-dag-dependencies-datasets-vs-triggerdagrun-vs-externaltasksensor.md` — Asset (formerly Dataset) vs. `TriggerDagRunOperator` vs. `ExternalTaskSensor`, mapped onto AutoSys cross-box condition patterns.
- `reference/scheduler-and-dag/dynamic-task-mapping-design.md` — `.partial()`/`.expand()` design for AutoSys's runtime job-cloning pattern.
- `reference/scheduler-and-dag/custom-timetable-design-for-autosys-calendars.md` — custom `Timetable` design for `run_calendar`/`exclude_calendar`, extending the imported skill's calendar rules.
- `reference/scheduler-and-dag/dag-level-sla-and-catchup-backfill-policy.md` — Airflow 3's SLA removal (replaced by experimental Deadline Alerts in 3.1) and the new `catchup=False` default; the staleness conflict it flagged in `migrate-jil-to-airflow-translation/reference/alerting-and-sla.md` has since been fixed (that file was rewritten for Airflow 3).
- `reference/scheduler-and-dag/idempotency-and-retry-design.md` — `n_retrys` → `retries` migration requires an idempotency classification step JIL never had.
- `reference/scheduler-and-dag/concurrency-controls-pools-and-max-active-runs.md` — Pools vs. `max_active_runs` mechanics, mapped onto `machine-load-and-virtual-resources` cluster's AutoSys `max_load`/`job_load`/virtual-resource concepts.
- `reference/scheduler-and-dag/naming-and-tagging-conventions-at-scale.md` — `dag_id`/`tags` mapped onto AutoSys's `box_name` (structural) vs. `group`/`application` (cross-cutting classification) two-axis model.
- `reference/scheduler-and-dag/one-off-and-ad-hoc-job-design.md` — Params/`dag_run.conf` design for genuinely one-off jobs, kept separate from the DAG-factory's recurring-box config schema.
- `reference/scheduler-and-dag/deadline-alerts-status-and-fallbacks.md` — Deadline Alerts' current maturity status, mapping from `must_complete_times`/`max_run_alarm`/`term_run_time`, and fallback order (Astro Alerts, Astro Observe) if the target Runtime's Deadline Alerts aren't mature enough.
- `reference/scheduler-and-dag/human-in-the-loop-operators-for-wait-reply.md` — `WAIT_REPLY`/`ZOSM`/`PAREQ` manual-dependency mechanisms mapped onto Airflow 3's human-in-the-loop task pattern.

Cluster 1 (Scheduler & DAG Design, 15 topics) is now complete.

## Reference Files — Cluster 2: Executor & Worker Architecture (complete, 11 of 11)

- `reference/executor-and-worker/celeryexecutor-vs-kubernetesexecutor-decision-framework.md` — decision table keyed off AutoSys `machine:` pinning patterns and job-volume burstiness; now leads with the Astro executor (Airflow 3.x default, only option in Remote Execution mode) before the original Celery-vs-Kubernetes framing.
- `reference/executor-and-worker/worker-queue-segregation-mirroring-machine-groups.md` — classifies *why* AutoSys machine groups existed before translating them into Astro worker queues, rather than a 1:1 machine→queue mapping.
- `reference/executor-and-worker/autoscaling-design-for-bursty-batch-workloads.md` — min/max/concurrency sizing for AutoSys-shaped batch-window bursts.
- `reference/executor-and-worker/per-task-resource-requests-and-limits.md` — `executor_config`/`pod_override` sizing from AutoSys machine-tier signals; a Critic pass caught and corrected an inverted claim about Kubernetes' actual admission-time failure behavior.
- `reference/executor-and-worker/node-affinity-and-taints-for-specialized-jobs.md` — taints/tolerations vs. soft affinity, mapped onto *why* a job was machine-pinned, not just that it was.
- `reference/executor-and-worker/keda-based-autoscaling.md` — the specific autoscaling formula and polling/cool-down mechanics. **Update**: the cool-down ambiguity (30s OSS chart default vs. 300s) is now resolved — 300s (5 minutes) is confirmed correct for Astro-managed Deployments across three separate doc surfaces. One narrower `NEEDS_EXEC_CHECK` remains: whether the 10-second polling interval is a per-Deployment tunable (not currently documented either way).
- `reference/executor-and-worker/hybrid-executor-strategy.md` — `KubernetesPodOperator` (operator-level, works under any executor) as the outlier-isolation mechanism; `CeleryKubernetesExecutor` corrected to legacy/not-selectable-on-Astro status, with dedicated worker queues under the Astro/Celery executor as the actual current replacement.
- `reference/executor-and-worker/legacy-server-access-via-sshoperator.md` — `SSHOperator`/`SSHHook` as the durable replacement for `machine:` pinning to a legacy/vendor host that won't containerize; Secrets-Backend-resolved SSH connections; a design-smell table for when SSH-wrapping signals a job needs re-platforming instead.
- `reference/executor-and-worker/worker-fleet-capacity-planning-methodology.md` — aggregate worker-fleet sizing (worker count/type/min-max) from estate-wide job count and schedule density, distinct from per-machine Pool sizing and scheduler/DAG-Processor sizing covered elsewhere; the A5–A160 worker-type table and a 5-step sizing methodology.
- `reference/executor-and-worker/zombie-task-detection-and-handling.md` — AutoSys `chase`/`PROCESS_MIA` reconciliation mapped to Airflow's zombie/undead-task detection; Astro-specific heartbeat-timeout defaults (60s standard, **120s on the Astro executor**); the Airflow 3+ metric rename.
- `reference/executor-and-worker/gpu-specialized-compute-worker-design.md` — two real, documented patterns for GPU workloads on Astro: `KubernetesPodOperator` into an external GPU cluster (Hosted mode) vs. Remote Execution Agent GPU node targeting; explicitly flags that standard Astro worker types have no documented GPU support.

## Reference Files — Cluster 3: Metadata DB & State Design (complete, 9 of 9)

- `reference/metadata-db-and-state/postgres-sizing-and-instance-class-selection.md` — Event Server RDBMS (Oracle/SQL Server/Sybase, DBA-managed) → Postgres metadata DB; deployment-model decision table, Hosted rightsizing vs. BYOD instance-class guidance, tables to monitor.
- `reference/metadata-db-and-state/connection-pooling-with-pgbouncer.md` — AutoSys's fixed-client binary protocol (no connection pool to design) → PgBouncer; full connection chain (scheduler/worker/triggerer → SQLAlchemy pool → PgBouncer → Postgres), estate-scale sizing table.
- `reference/metadata-db-and-state/metadata-retention-and-cleanup-policy.md` — Event Server RDBMS retention (DBA-set, outside AutoSys) → no built-in Airflow purge mechanism; `airflow db clean` reference, archive → VACUUM lifecycle, high-churn tables.
- `reference/metadata-db-and-state/backup-and-point-in-time-recovery.md` — Event Server RDBMS DBA backup procedures → Postgres PITR; deployment-model decision table, self-managed and cloud-managed PITR checklists, RPO/RTO planning.
- `reference/metadata-db-and-state/read-replica-strategy-for-reporting.md` — direct Event Server reporting queries (scheduler-performance risk) → dedicated Postgres read-replica architecture for reporting, keeping the primary DB isolated from ad hoc load.
- `reference/metadata-db-and-state/db-migration-strategy-across-airflow-upgrades.md` — schema-migration discipline for major-version upgrades (Airflow 2 → 3); pre-migration checklist, downtime and component-state handling.
- `reference/metadata-db-and-state/metadata-db-growth-at-scale.md` — DB tuning at thousands-of-DAGs scale: maintenance as the most critical factor, DAG-authoring load reduction, infrastructure tuning, to avoid slow scheduling and UI timeouts.
- `reference/metadata-db-and-state/custom-xcom-backend-design.md` — AutoSys's global-variable job-to-job state passing → XCom; why the default DB-backed backend fails at scale, `Common IO` provider custom-backend design.
- `reference/metadata-db-and-state/airflow-2-to-3-in-place-upgrade-constraints.md` — brownfield in-place Airflow 2→3 upgrade constraints for an existing Astro Deployment, vs. standing up a new Airflow 3 Deployment and cutting over.

## Reference Files — Cluster 4: Security & Multi-Tenancy Design (complete, 11 of 11)

- `reference/security-and-multitenancy/workspace-and-deployment-boundary-design.md` — AutoSys `group`/`application` JIL classification tags (not isolation boundaries) → Astro's Organization/Workspace/Deployment hierarchy; the primary Deployment-boundary-placement design question.
- `reference/security-and-multitenancy/rbac-role-shape-design-mirrored-from-eem-entitlements.md` — CA EEM job-group/application entitlements → Astro's hierarchical, additive RBAC (Organization/Workspace/Deployment/DAG roles); EEM → Astro role-mapping pattern.
- `reference/security-and-multitenancy/secrets-backend-selection.md` — Event Server RDBMS/OS keystore credential storage → Airflow's secret lookup priority across Variables/Connections/Secrets Backend; backend option matrix and the `Variable.get()`-in-top-level-code pitfall.
- `reference/security-and-multitenancy/connection-scoping-and-least-privilege.md` — JIL-embedded `machine:`/`login:` credentials with no cross-job scoping → Airflow Connections' global-within-Deployment visibility risk; least-privilege worker IAM and Workload Identity design.
- `reference/security-and-multitenancy/sso-oauth-integration-design.md` — OS-level PAM/LDAP/AD or EEM-managed auth → Astro's SAML 2.0 SSO plus SCIM 2.0 automated user-lifecycle management.
- `reference/security-and-multitenancy/network-isolation-and-vpc-peering.md` — OS-level TCP Event Server ↔ agent connectivity (no VPC model) → Astro Standard vs. Dedicated Cluster decision; private connectivity and Remote Execution hybrid networking.
- `reference/security-and-multitenancy/audit-log-design-for-access-and-actions.md` — DBA-controlled OS/RDBMS audit trails → Astro's two-layer audit architecture (platform audit log + Airflow task-execution history); SIEM integration and compliance-standard mapping.
- `reference/security-and-multitenancy/federated-vs-centralized-self-service-design.md` — one-AutoSys-instance-per-business-unit vs. single shared-instance topologies → Workspace/Deployment-per-domain self-service design (an earlier draft recommended upstream Airflow 3 Multi-Team mode as an alternative; corrected — that mode isn't supported on Astro).
- `reference/security-and-multitenancy/api-token-service-account-lifecycle-management.md` — OS-level, LDAP/AD-managed AutoSys service accounts → scoped Astro API tokens; token-type/lifecycle design, Workload Identity as the preferred alternative for cloud resources.
- `reference/security-and-multitenancy/encryption-at-rest-and-in-transit-design.md` — Event Server TDE and OS-level TLS → Astro's default-on Hosted encryption posture; Fernet key management and BYOK for self-managed/BYOD contexts.
- `reference/security-and-multitenancy/multi-team-config-scoping.md` — why there is no within-Deployment, multi-team config-scoping alternative to Workspace/Deployment-per-BU on Astro (corrected from an earlier draft that recommended Airflow 3 multi-team mode, which isn't supported on Astro); `tags`-based logical grouping is the only lighter-weight option for shared-instance AutoSys topologies.

## Reference Files — Cluster 5: Observability & Alerting Design (complete, 10 of 10)

- `reference/observability-and-alerting/on_failure_callback-design-patterns.md` — AutoSys's native job-failure alerting → Airflow's programmatic task/DAG-level callbacks; layered-alerting pattern and callback error-handling pitfalls.
- `reference/observability-and-alerting/astronomer-alerts-routing-and-escalation.md` — enterprise-event-manager alarm routing by job criticality → the two-tier Astro Alerts (platform-level) plus Airflow callback (code-level) routing and escalation design.
- `reference/observability-and-alerting/alert-fatigue-and-deduplication-strategy.md` — manual console-level alarm suppression → architectural deduplication and anti-"flappy"-alert design for Airflow retries and cascade failures.
- `reference/observability-and-alerting/openlineage-data-lineage-integration.md` — AutoSys's job-dependency-only visibility (no data-asset tracking) → OpenLineage's data-supply-chain lineage; rollout strategy, namespace consistency, temporary-table handling.
- `reference/observability-and-alerting/astronomer-observe-integration.md` — AutoSys/WCC's job-centric reporting → Astro Observe's data-product-centric observability model (timeliness, health, cost over individual task status).
- `reference/observability-and-alerting/metrics-export-prometheus-datadog.md` — proprietary SNMP-trap/DB-query metrics → native Airflow metrics exported via the Universal Metrics Exporter (Prometheus/Grafana) or native Datadog integration.
- `reference/observability-and-alerting/log-architecture-remote-storage-and-retention.md` — local agent-filesystem logs (`$AUTOSYS/out`) → externalized log storage for Astro's ephemeral pods (Elasticsearch on Private Cloud, S3/GCS, CloudWatch).
- `reference/observability-and-alerting/sla-miss-detection-and-escalation.md` — `term_run_time`/`max_run_alarm`/Cross-Box alarms → the Airflow/Astro SLA-monitoring spectrum, from code-level callbacks to Astro Observe.
- `reference/observability-and-alerting/incident-ticket-automation.md` — proprietary OS-level/plugin ServiceNow or BMC Remedy ticket creation → API-driven orchestration or event-driven middleware ticket automation on Astro.
- `reference/observability-and-alerting/dashboard-design-for-stakeholder-visibility.md` — AutoSys WCC stakeholder reporting → a tiered dashboard strategy (Astro Observe, Grafana, custom BI), since Airflow's native UI targets data engineers, not business stakeholders.

## Reference Files — Cluster 6: CI/CD & Environment Topology (complete, 11 of 11)

- `reference/cicd-and-environment-topology/astro-cli-deploy-pipeline-design.md` — custom shell scripts and manual JIL imports (`jil < job.jil`) → `astro` CLI-driven CI/CD pipeline design and authentication.
- `reference/cicd-and-environment-topology/dev-staging-prod-deployment-topology.md` — AutoSys's single massive shared instance → isolated per-lifecycle-stage Astro Deployments, since Airflow is not natively multi-tenant and a bad DAG can crash a shared scheduler.
- `reference/cicd-and-environment-topology/dag-testing-and-parse-gates-before-merge.md` — post-import `chk_auto_up`/runtime JIL validation → a pre-merge CI testing pyramid (parse/integrity check, unit tests, ephemeral integration tests).
- `reference/cicd-and-environment-topology/branching-strategy-for-dag-code.md` — direct GUI/CLI job editing → Git branching strategy mapped to environments, plus Astronomer's native GitHub integration.
- `reference/cicd-and-environment-topology/environment-promotion-process.md` — manual JIL extract/import with machine-name tweaks between environments → immutable-image, Git-based promotion (code promotion, image promotion, config-difference handling).
- `reference/cicd-and-environment-topology/gitops-design-for-dag-deployment.md` — JIL-file import against a database → the `GitDagBundle` GitOps architecture; repo organization, DAG hashing, bundle selection by estate scale.
- `reference/cicd-and-environment-topology/rollback-strategy-design.md` — manual re-import of an older JIL version → Astro's "Deploy Rollbacks" feature as a faster alternative to reverting Git commits during an outage.
- `reference/cicd-and-environment-topology/multi-region-deployment-topology-at-scale.md` — distributed multi-region AutoSys instances (e.g. NA/EMEA) → Astro's control-plane/data-plane separation; multi-cluster, Remote Execution, and cross-region DR strategies.
- `reference/cicd-and-environment-topology/feature-flagging-for-gradual-dag-rollout.md` — unique-named or `ON ICE` job streams → Airflow 3 DAG versioning, Variable-based logic flags, and DAG-only fast-iteration deploys for gradual rollout.
- `reference/cicd-and-environment-topology/local-development-environment-standards.md` — shared dev-database development → containerized `astro dev` local environments, including Airflow 3+ Standalone Mode.
- `reference/cicd-and-environment-topology/airflowctl-and-astro-cli-division-of-labor.md` — `airflowctl` (Airflow-instance-level operations) vs. `astro` CLI (platform-level operations) division of labor; replaces the old base skill's `platform-and-cli-equivalents.md` Astro-side half.

## Reference Files — Cluster 7: Config & Secrets Design (complete, 6 of 6)

- `reference/config-and-secrets/variables-vs-connections-vs-secrets-backend-decision-framework.md` — AutoSys's flat global `%%VAR%%` store → Airflow's config/credential split across Variables, Connections, and Secrets Backend, with security-precedence guidance.
- `reference/config-and-secrets/per-environment-variable-scoping.md` — environment-specific hardcoding anti-pattern (`if env == 'dev'`) → per-environment variable scoping and sensitive-variable masking, avoiding top-level-code lookups.
- `reference/config-and-secrets/global-variable-sprawl-remediation.md` — the AutoSys `%%VAR%%` lift-and-shift trap (thousands of flat Airflow Variables) → remediation strategy split by variable purpose (task communication, repetitive config, environment targeting, secrets).
- `reference/config-and-secrets/config-as-code-for-dag-factory-inputs.md` — DAG-factory (topic 001) input-file management: storage/format, modularity vs. monoliths, preventing DB lookups during parsing, CI/CD validation.
- `reference/config-and-secrets/secret-rotation-strategy.md` — manual DB-stored credential updates → Secrets Backend-driven rotation strategy and security best practices.
- `reference/config-and-secrets/environment-specific-connection-management.md` — the requirement that DAG code stay identical across Dev/Prod → Astro Environment Manager, external secrets backend, and environment-variable connection-resolution strategies.

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

## Reference Files — Cluster 11: Migration Execution & Coexistence Architecture (complete, 6 of 6)

- `reference/migration-execution-and-coexistence/dual-run-shadow-dag-architecture.md` — Three coexistence modes (AutoSys-Triggered, Side-by-Side, Airflow-Controlled), feature-flag kill switch, staging output paths.
- `reference/migration-execution-and-coexistence/data-reconciliation-architecture-for-parity-verification.md` — Dedicated reconciliation DAG, schema/row-count/hash checks, JSON parity report, N-cycle exit criteria.
- `reference/migration-execution-and-coexistence/cutover-architecture-per-box.md` — Pre-conditions checklist, ON_HOLD quiesce sequence, cross-domain dependency bridging (ExternalTaskSensor/Assets), 2-4 cycle observation period.
- `reference/migration-execution-and-coexistence/rollback-architecture-during-cutover.md` — Go/No-Go threshold table, 4-step rollback execution, data integrity orphan cleanup, no-shared-DB rule.
- `reference/migration-execution-and-coexistence/otto-assisted-translation-workflow.md` — where an AI-assisted translation tool (Otto) fits alongside this project's own `scaffold_dags.py` and hand translation; inputs, review/traceability discipline, and REDESIGN/NONE stop conditions.
- `reference/migration-execution-and-coexistence/orbiter-vs-otto-vs-hand-translation.md` — decision table across `scaffold_dags.py`/Orbiter/Otto/hand translation by disposition, volume, and condition-graph complexity.

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

Provenance by topic range is in the Overview table above. This section lists only items that
still need a human (or a session with live docs access) to run something, not just re-read a file:

- `dag-factory-pattern-for-large-estates.md` — confirm `is_paused_upon_creation` behaves as
  documented (an open Airflow GitHub issue questions its reliability).
- `dag-level-sla-and-catchup-backfill-policy.md` / `deadline-alerts-status-and-fallbacks.md` —
  confirm Deadline Alerts' production-readiness on the actual target Astro Runtime version (still
  marked experimental upstream as of this KB's last verification pass).
- The 7 topics added in the Phase 2 KB refresh (`otto-assisted-translation-workflow.md`,
  `orbiter-vs-otto-vs-hand-translation.md`, `airflowctl-and-astro-cli-division-of-labor.md`,
  `multi-team-config-scoping.md`, `human-in-the-loop-operators-for-wait-reply.md`,
  `airflow-2-to-3-in-place-upgrade-constraints.md`, `deadline-alerts-status-and-fallbacks.md`)
  were directly-authored with `NEEDS_EXEC_CHECK` markers on mechanism-specific claims.
  **Update**: a subsequent astronomer-docs verification pass fully resolved
  `multi-team-config-scoping.md` and `airflow-2-to-3-in-place-upgrade-constraints.md` (no
  remaining markers), and narrowed `human-in-the-loop-operators-for-wait-reply.md` to only its
  timeout/escalation-config claim. `otto-assisted-translation-workflow.md`,
  `orbiter-vs-otto-vs-hand-translation.md`, `airflowctl-and-astro-cli-division-of-labor.md`, and
  `deadline-alerts-status-and-fallbacks.md` still carry open markers — their claims are outside
  astronomer-docs' coverage (third-party tools, upstream OSS CLI surface) or inherently
  version-dependent. **Update 2026-10-22**: `orbiter-vs-otto-vs-hand-translation.md`'s claim
  that neither tool supports AutoSys JIL was wrong and has been corrected against live sources.
- `SETUP-4` (seed source list) and `SETUP-6` (formal scaffold task) were done informally as part
  of generating the original 130 topics, not as their own gated tasks — see `tasks/README.md` for
  the formal tracker state.
