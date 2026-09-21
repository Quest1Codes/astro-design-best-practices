---
name: migrate-astro-platform-buildout
description: Build the target Astro platform itself — Organization/Workspace/Deployment provisioning, identity/RBAC, secrets backend, worker queues/RE agents, CI/CD pipeline, alerting/observability wiring. Use once assess-astro-target-architecture has produced manifest.architecture decisions. Runs alongside migrate-jil-to-airflow-translation (job translation) and migrate-topology-* (execution placement) — this skill is the platform layer those depend on existing.
---

# Astro platform buildout

Turn `manifest.architecture`'s decisions into an actual provisioned platform: Workspaces,
Deployments, RBAC, secrets, worker queues/Remote Execution agents, a CI/CD pipeline, and
alerting/observability wiring. This is infrastructure work, not job translation —
`migrate-jil-to-airflow-translation` depends on this skill's Deployment existing before its DAGs
have anywhere real to run.

## Requirements

- `estate_manifest.json` with `architecture{}` populated (`assess-astro-target-architecture`).
- Astro Organization access with provisioning rights (Terraform, or manual `astro` CLI/UI
  actions) — this is the first skill in the family that actually touches the target platform;
  everything upstream was read-only.
- EEM `safex` export (if native security is in scope) for `rbac_map.py`.

## Workflow

### Phase 1: Read the architecture decisions

Confirm `manifest.architecture.decisions` covers deployment model, executor, queues, secrets
backend, identity, alerting — re-run `assess-astro-target-architecture/scripts/recommend_architecture.py`
if anything changed since the assessment was finalized.

### Phase 2: Organization/Workspace/Deployment

```
python3 scripts/generate_terraform_skeleton.py --manifest estate_manifest.json --out terraform/
```

Emits a Terraform skeleton (Astro provider resources: workspaces, deployments with
executor/queues/sizes from `manifest.architecture.sizing`, teams, API token placeholders,
alerts) marking every value that needs human input. Per `reference/workspaces-and-deployments.md`
for the naming convention and per-environment topology.

### Phase 3: Identity and RBAC

```
python3 scripts/rbac_map.py --safex-export eem_policies.xml --out rbac_proposal.json --md rbac_proposal.md
```

Parses the EEM `safex` XML export into `(identity, resource class, action)` triples and proposes
an Astro Organization/Workspace/Deployment role and Team mapping, flagging any EEM construct with
no Astro equivalent (typically per-job ACL bits). Per `reference/identity-and-rbac.md`.

### Phase 4: Secrets

Per `reference/secrets-and-identity.md`: map AutoSys credential handling (OS-level service
accounts, CA credential vault, or external vault integration) to Airflow Connections + the
secrets backend decision from `manifest.architecture.decisions.secrets_backend`.

### Phase 5: Worker queues / Remote Execution agents

Per the sizing already computed by `assess-astro-target-architecture/scripts/size_target.py` and
the topology decisions from `migrate-topology-onprem-distributed`/`migrate-topology-k8s` — this
skill provisions what those decided, it doesn't re-decide.

### Phase 6: CI/CD pipeline

Per `reference/cicd-pipeline.md`: establish source control for DAG code, automated validation
(`migrate-jil-to-airflow-translation`'s Gates 1/2 in CI, not just local), `astro deploy` mapped to
the right branch/environment, and a tested rollback path.

### Phase 7: Alerting and observability

Per `reference/alerting-and-observability-wiring.md`: wire Astro Alerts to the ITSM tool
identified by `manifest.architecture.decisions.alerting_itsm`, and Astro Observe/OpenLineage per
whatever observability signals the assessment found (`svcdesk_*` usage, existing monitoring
stack).

### Phase 8: Validation

Per `reference/validation.md`'s gates P1-P6 (login/SSO, RBAC enforcement, secret resolution at
runtime, deploy + rollback, alert fires end-to-end, RE agent/worker queue reachability). Track
state via `_lib.autosys_jil.status --manifest estate_manifest.json --workflow platform`
(`pending → provisioned → identity → secrets → pipelines → observability → validated`, one unit
per platform component being validated).

## Reference routing

| Question | Read |
|---|---|
| Workspace/Deployment naming, per-environment topology | `reference/workspaces-and-deployments.md` |
| RBAC/Teams from EEM policy | `reference/identity-and-rbac.md` |
| Secrets backend, Connection naming, rotation | `reference/secrets-and-identity.md` |
| CI/CD pipeline design | `reference/cicd-pipeline.md` |
| Alerting/ITSM/observability wiring | `reference/alerting-and-observability-wiring.md` |
| Platform validation gates P1-P6 | `reference/validation.md` |

## Scripts

| Script | Purpose |
|---|---|
| `scripts/generate_terraform_skeleton.py` | `manifest.architecture` → Terraform skeleton with human-input markers |
| `scripts/rbac_map.py` | EEM `safex` export → Astro role/Team proposal |
