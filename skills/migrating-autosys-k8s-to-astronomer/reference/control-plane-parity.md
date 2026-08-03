# Control-plane parity checklist

Every row below gets a disposition for the source estate: **direct-port** (works as-is or with trivial relabeling), **needs-translation** (the concept applies but the object must be rewritten against Astronomer's model), or **superseded** (Astronomer/Astro provides this natively; the source object is dropped, not migrated).

## Namespaces

AutoSys-on-k8s deployments typically isolate the Application Server, Event Server, and agent pods within one or a few namespaces. Astronomer (Hybrid or Software) has its own namespace model per Deployment/environment. **Needs-translation** in almost all cases: map the source namespace boundary (what it isolates — environment? team? both?) onto Astro's Deployment/Workspace boundary, don't assume a 1:1 namespace copy is meaningful.

## RBAC (Roles, RoleBindings, ServiceAccounts)

| Source pattern | Disposition |
|---|---|
| ServiceAccounts scoped to specific AutoSys components (Application Server, agent) | needs-translation — Astronomer/Airflow has its own ServiceAccount model per component (scheduler, workers, webserver, triggerer); map intent (least-privilege per component), not object names |
| Roles/RoleBindings granting human operators access to the AutoSys namespace | needs-translation — this is a candidate for Astro RBAC (Workspace/Deployment roles via SSO) rather than direct k8s RBAC, if humans were interacting through a UI/CLI rather than `kubectl` directly. If they genuinely need `kubectl` access to the underlying cluster (Hybrid data plane), k8s RBAC still applies and needs separate mapping |
| A custom controller/operator's own RBAC (if AutoSys-on-k8s used a custom operator to manage job pods) | needs-translation, scoped down — Astronomer's own operators (for Hybrid) supersede a custom job-launching controller; audit whether the custom controller did anything beyond what KubernetesExecutor/KubernetesPodOperator already provides before assuming it needs a replacement at all |

## NetworkPolicies

Direct-port is rare because policies are usually written against AutoSys's own pod labels (`app: autosys-agent`, etc.). **Needs-translation**: rewrite the same *intent* (which namespaces/pods can reach the scheduler, workers, metadata DB, and which egress paths are allowed) against Airflow's actual component labels. Absent policies aren't necessarily a gap — confirm whether the source cluster relied on a broader network boundary (e.g., a dedicated node pool with its own firewall) instead of NetworkPolicy objects before assuming policy needs to be authored from scratch.

## Resource requests/limits

Direct-port of the *numbers* is usually wrong even when the *practice* (setting requests/limits) is right — AutoSys agent pods and Airflow worker/KubernetesPodOperator pods have different resource profiles for the same job (different base image, different sidecar overhead). Use source requests/limits as a starting reference point, then validate against actual observed usage post-migration (same principle as capacity planning in the on-prem-distributed skill).

## ConfigMaps and Secrets

| Source pattern | Disposition |
|---|---|
| ConfigMaps holding non-secret config (calendar files, environment flags) | direct-port of content, needs-translation of delivery mechanism — likely becomes `include/` data in the Astro project rather than a live-mounted ConfigMap, unless the config genuinely needs to change independently of a DAG deploy |
| Secret objects (credentials, tokens) | **never direct-port** — see `reference/secrets-and-networkpolicy.md`. A Secret found in the export is evidence of what needs a home in the target secrets backend, not something to copy into a new Secret object |

## Autoscaling (HPA / custom autoscalers / KEDA)

See `reference/executor-and-autoscaling.md` — disposition depends entirely on the workload shape, not a direct mapping from whatever the source used.

## Ingress / external access

If WCC or an API was exposed via Ingress for human/external access, this is superseded by Astro's own UI/API exposure model (Hybrid: Astronomer-managed ingress to the control plane; Software: the platform's own ingress config) — needs-translation only if there's a genuinely custom external integration (a third-party system calling AutoSys's REST API) that needs an equivalent path to Airflow's REST API.
