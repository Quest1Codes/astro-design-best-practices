---
topic: stakeholder-questions
family: assessment
skill: assess-estate-discovery
verified_against:
  autosys: "12.0"
last_verified: 2026-09-17
confidence: practitioner-judgment
signals: [residency, hipaa, sox, fedramp, brownfield_astro]
---

# Stakeholder questionnaire

Structured so each answer maps to exactly one `manifest.nfr.<key>` field, which
`assess-astro-target-architecture/scripts/recommend_architecture.py` then reads. Record answers
in an `answers.yaml` keyed by the `nfr.<key>` names below; `discovery_checklist.py --nfr
answers.yaml` validates it against this schema.

PRACTITIONER JUDGMENT — this questionnaire's structure (which questions, which decision-table
row each feeds) is this project's own design, not sourced from AutoSys or Astronomer
documentation; the underlying facts it collects (SLAs, RTO/RPO, compliance posture) are
universally relevant to any migration, but the specific `nfr.<key>` schema is ours.

## SLAs and business calendars

| Question | `nfr` key | Feeds |
|---|---|---|
| Are there business-side deadlines not encoded in `must_complete_times`? What are they? | `nfr.unencoded_slas` (free text) | Report §14 "Risks, losses, stay-signals" |
| Are there change-freeze windows (quarter-end, year-end, regulatory reporting periods)? | `nfr.change_freeze` (date ranges) | `propose_waves.py` — waves must not cross a freeze |

## RTO / RPO / DR

| Question | `nfr` key | Feeds |
|---|---|---|
| What's the required Recovery Time Objective for this workload? | `nfr.rto_hours` (number) | HA/DR deployment-model decision |
| What's the required Recovery Point Objective? | `nfr.rpo_minutes` (number) | Metadata-DB backup/replication recommendation |
| Is there an existing DR runbook this must match? | `nfr.dr_runbook_exists` (bool) | `astro-design-best-practices/reference/ha-and-dr/dr-runbook-design.md` routing |

## Residency and compliance

| Question | `nfr` key | Feeds |
|---|---|---|
| Does any data have a residency requirement (must stay in-region/in-country)? | `nfr.residency` (region code or null) | Deployment-model decision (Hosted vs. Dedicated vs. Hybrid) |
| Which regulatory overlays apply? (SOX, HIPAA, FedRAMP, GDPR, other) | `nfr.compliance` (list) | Routes to the matching `vertical-overlay-*.md` KB topic |
| Is FIPS mode enabled on the source AutoSys instance? | `nfr.fips_enabled` (bool, cross-check against `EnableFIPSMode` config) | Same |

## Security and identity

| Question | `nfr` key | Feeds |
|---|---|---|
| Native security or CA EEM? | `nfr.security_mode` (`native`/`eem`) | Whether a `safex` export is required |
| Is a PAM/vault solution in use for credentials (CyberArk, HashiCorp Vault, other)? | `nfr.pam_solution` (free text or null) | Secrets-backend recommendation |
| SSO/IdP in use today? | `nfr.idp` (free text) | Astro SSO/RBAC bootstrap recommendation |

## Operations

| Question | `nfr` key | Feeds |
|---|---|---|
| On-call model — who gets paged, how? | `nfr.oncall_model` (free text) | Alerting/ITSM routing recommendation |
| Who has Web UI/WCC access today, and to what? | `nfr.wcc_users` (free text) | Astro RBAC role-shape design |
| How often are manual interventions (force-start, kill, hold) used, and by whom? | (cross-checked against `history_stats.py`'s `manual_intervention()` output, not asked blind) | REDESIGN/HITL signal corroboration |
| CAB / change-management process for scheduling changes? | `nfr.change_management` (free text) | `migrate-astro-platform-buildout`'s CI/CD pipeline design |

## Target platform constraints

| Question | `nfr` key | Feeds |
|---|---|---|
| Is there an existing Astro/Airflow footprint (brownfield)? | `nfr.brownfield_astro` (bool) | Triggers `astro_inventory.py`/`dag_conventions_scan.py` |
| Cloud provider and region constraints? | `nfr.cloud_provider`, `nfr.region` | Deployment-model decision |
| Network posture — can Astro Hosted reach the estate's systems, or is everything inside a private network? | `nfr.network_posture` (`open`/`private`/`mixed`) | Hosted vs. Hybrid vs. Remote Execution decision |

## Commercial

| Question | `nfr` key | Feeds |
|---|---|---|
| AutoSys/CA WA AE license end date? | `nfr.autosys_license_end` (date) | Wave-planning urgency; only feeds a cost *comparison* if `nfr.autosys_license_cost` is also supplied |
| AutoSys license cost, if the customer wants a cost comparison in the report | `nfr.autosys_license_cost` (number or null) | `estimate_cost.py` — a comparison is **never** generated without this being explicitly supplied |
| Overall engagement timeline / target cutover date | `nfr.target_cutover_date` (date) | Wave-planning pacing |
