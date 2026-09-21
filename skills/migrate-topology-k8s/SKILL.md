---
name: migrate-topology-k8s
description: Guide for migrating an AutoSys Workload Automation deployment that already runs containerized/on Kubernetes to Astronomer on Kubernetes (Astro Hybrid or Astronomer Software). Use when the source estate's Application Server, Event Server, or agents already run as pods, not on bare-metal/VM hosts. This is a control-plane and platform-parity migration, not an execution-topology one: namespaces, RBAC, network policies, executor/autoscaling choice, CI/CD, and observability. Requires `estate_manifest.json` from `assess-estate-inventory` (job semantics must already be inventoried); load the assess-* family first, this skill second. Load reference/control-plane-parity.md before proposing a target namespace/RBAC model.
hooks:
  PostToolUse:
    - matcher: "Edit"
      hooks:
        - type: command
          command: "echo 'Parity worksheet edited: consider re-running python3 -m autosys_jil.status --manifest k8s_parity_manifest.json summary --workflow k8s-parity'"
---

# AutoSys-on-k8s → Astronomer-on-k8s

Migrate an AutoSys estate that's *already containerized* — Application Server, Event Server, and/or agents running as pods — to Astronomer running on Kubernetes (Astro Hybrid, or self-hosted Astronomer Software). This is a narrower, more mechanical migration than the on-prem-distributed case: the substrate doesn't change, so the work is control-plane and platform parity — namespaces, RBAC, network policies, secrets, executor/autoscaling model, CI/CD, and observability — not "where does this even run now."

This skill assumes `assess-estate-inventory` has already produced `estate_manifest.json`, and that `migrate-jil-to-airflow-translation` handles job translation itself. This skill's job is exclusively the platform layer for a Kubernetes-native source estate; it does not re-translate JIL. The executor decision `assess-astro-target-architecture` proposes estate-wide should be treated as the starting position here, refined against the actual k8s object evidence this skill scans.

## Requirements

- `estate_manifest.json` from `assess-estate-inventory`.
- The source estate's Kubernetes manifests (Deployments, StatefulSets, Services, NetworkPolicies, ConfigMaps, Secrets, ServiceAccounts, HPA/autoscaler configs, Ingress) for the AutoSys components, or at minimum a `kubectl get -o yaml` export of the relevant namespace(s).
- Target: confirm whether the destination is Astro Hybrid (Astronomer-managed control plane, customer-managed data plane on their own Kubernetes) or Astronomer Software (fully self-hosted) — the parity checklist differs slightly between the two; `reference/control-plane-parity.md` covers both and says which rows apply to which target.

## Hard rules

1. **Parity is verified against real manifests, not assumed from architecture diagrams.** `scripts/k8s_parity_scan.py` reads actual YAML; a claim like "RBAC is handled" needs a `Role`/`RoleBinding` object found in the export, not a description of intent.
2. **No silent omissions.** Every checklist row in `reference/control-plane-parity.md` gets a disposition (`direct-port` / `needs-translation` / `superseded`, recorded via `--disposition` on `autosys_jil.status advance`) for the source estate before the migration is called planned.
3. **Executor/autoscaling choice is a decision, not a default.** Don't assume CeleryExecutor or KubernetesExecutor without checking the workload's actual shape (task count, duration distribution, isolation needs) against `reference/executor-and-autoscaling.md`.
4. **Secrets migrate through a secrets backend, never through copy-pasted YAML.** A `Secret` object found in a source export is a signal of what needs a home in the target's secrets backend, not something to transcribe into a new manifest verbatim.
5. **CI/CD parity is part of "done."** A migration that translates DAGs but leaves deployment as a manual `kubectl apply` is not complete — `reference/cicd-and-gitops.md` is a required phase, not optional polish.

## Workflow

### Phase 1: Export and scan

```
python3 scripts/k8s_parity_scan.py --manifests-dir ./k8s-export --out k8s_parity_manifest.json
```

Parses every YAML file in the export, categorizes objects by `kind`, and checks each against the parity checklist (`reference/control-plane-parity.md`): namespaces, RBAC (Roles/RoleBindings/ServiceAccounts), NetworkPolicies, resource requests/limits, ConfigMaps/Secrets, autoscaling objects (HPA/KEDA ScaledObject), Ingress. Every checklist row starts `state: pending`, no disposition.

### Phase 2: Classify and plan

For each present object, classify with `python3 -m autosys_jil.status --manifest k8s_parity_manifest.json advance <item> --workflow k8s-parity --status classified --disposition <direct-port|needs-translation|superseded>`: does it port directly to the Astronomer-managed namespace model, does it need translation (e.g., a custom NetworkPolicy written against AutoSys's own pod labels needs rewriting against Airflow's worker/scheduler/webserver labels), or is it superseded entirely (e.g., a custom autoscaler script replaced by Astro's managed autoscaling)? Use `reference/control-plane-parity.md`'s table.

- **Executor and autoscaling**: `reference/executor-and-autoscaling.md` — decide KubernetesExecutor vs. CeleryExecutor (+ KEDA) from the actual workload shape found in `estate_manifest.json` (task count, concurrency, duration variance) and `assess-astro-target-architecture`'s executor recommendation, not by default.
- **Secrets and network policy**: `reference/secrets-and-networkpolicy.md`.
- **CI/CD**: `reference/cicd-and-gitops.md` — map however JIL/config changes currently reach the cluster (a custom pipeline, a sidecar syncing JIL from a repo, manual `kubectl apply`) to `astro deploy`-based CI/CD (see also `migrate-astro-platform-buildout/reference/cicd-pipeline.md`).
- **Observability**: `reference/observability-parity.md` — map existing container/pod monitoring (Prometheus/Grafana dashboards watching AutoSys pods) to Astro Observe/OpenLineage plus whatever of the existing stack still applies to the surrounding infrastructure.

### Phase 3: Trial

Stand up a target namespace with one migrated DAG (from `migrate-jil-to-airflow-translation`) running under the chosen executor, prove RBAC/network-policy parity by testing actual access (a user in a mapped role can/cannot do what the equivalent AutoSys role could/couldn't), and prove the CI/CD path actually deploys a DAG change end to end.

### Phase 4: Migrate

Track each parity checklist row through to `complete` (`python3 -m autosys_jil.status --manifest k8s_parity_manifest.json advance <item> --workflow k8s-parity --status planned|piloted|complete`), and each DAG through `migrate-jil-to-airflow-translation`'s own per-job state. Cut over namespace by namespace or environment by environment (dev → staging → prod), never all at once.

### Phase 5: Final report

`python3 -m autosys_jil.status --manifest k8s_parity_manifest.json summary --workflow k8s-parity` must pass (exit 0 — every row terminal, every disposition recorded). The report: the full parity checklist with dispositions, the executor/autoscaling decision and its rationale, the secrets migration map, the CI/CD pipeline description, and the observability mapping.

## Reference routing

| Question | Read |
|---|---|
| What existing k8s objects need a home in the target, and where? | `reference/control-plane-parity.md` |
| KubernetesExecutor vs. CeleryExecutor, autoscaling | `reference/executor-and-autoscaling.md` |
| Secrets backend, NetworkPolicy translation | `reference/secrets-and-networkpolicy.md` |
| Deploy pipeline, GitOps | `reference/cicd-and-gitops.md` |
| Monitoring/alerting/lineage parity | `reference/observability-parity.md` |
| Validating the parity claims | `reference/validation.md` |
| Failure classes seen before | `reference/troubleshooting.md` |

## Scripts

| Script | Purpose |
|---|---|
| `scripts/k8s_parity_scan.py` | Parse a k8s manifest export → parity checklist manifest |
| `_lib.autosys_jil.status` (`--workflow k8s-parity`) | Per-checklist-row state + disposition machine and completeness gate; replaces the old per-skill `scripts/status.py` |
