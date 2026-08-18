# Multi-Container Pod Targeted-Execution → Airflow K8s Exec-Into-Container Design

AutoSys's Kubernetes job type supports targeting a specific container within a multi-container pod — a feature useful when running a sidecar-pattern pod where the primary container is a long-running service and the AutoSys job needs to exec a command into the secondary (sidecar) container [B1].

**Airflow's `KubernetesPodOperator` has no native `target_container` parameter** for exec-ing into a sidecar after pod startup [B2]. This is an explicit gap. The design alternatives below provide equivalent outcomes.

## Gap Analysis

| AutoSys K8s Feature | Airflow Status |
|---|---|
| Run a command in a specific named container | **No native equivalent** in `KubernetesPodOperator` |
| Target primary (first) container | Supported via `cmds`/`arguments` |
| Exec into a sidecar container | **Not supported** — requires design workaround |

## Design Alternatives

### Option 1: Redesign for Single-Purpose Container (Recommended)

The cleanest migration is to redesign the workload so the target command becomes the container's entrypoint. Create a dedicated image for the operation that was previously a sidecar exec:

```python
# Instead of exec-ing into a sidecar, build a dedicated image
KubernetesPodOperator(
    task_id="run_sidecar_equivalent",
    image="company-registry/finance-cleanup-job:latest",  # Purpose-built image
    cmds=["python", "-m", "cleanup.main"],
    namespace="airflow-jobs",
)
```

### Option 2: `full_pod_spec` with Multi-Container Init Pattern

If the sidecar container must be present (e.g., for shared volume access), use `full_pod_spec` to define the complete pod spec. Sequence the containers by using an init container to run the exec-equivalent logic before the main container starts:

```python
from kubernetes.client import models as k8s

pod_spec = k8s.V1Pod(
    spec=k8s.V1PodSpec(
        init_containers=[
            k8s.V1Container(
                name="exec-target",
                image="company-registry/sidecar:latest",
                command=["python", "-m", "sidecar.task"],
                volume_mounts=[...],
            )
        ],
        containers=[
            k8s.V1Container(
                name="main",
                image="busybox",
                command=["sh", "-c", "echo done"],
            )
        ],
    )
)

KubernetesPodOperator(
    task_id="multi_container_ordered",
    full_pod_spec=pod_spec,
    namespace="airflow-jobs",
)
```

### Option 3: `kubectl exec` via BashOperator (Anti-Pattern — Avoid in Production)

Issuing `kubectl exec -c <container-name>` via a `BashOperator` or `SSHOperator` against a pre-existing pod is possible but is fragile (pod must be running, pod name must be known) and ties Airflow to mutable infrastructure state. **Do not use this pattern for production workloads.**

## Sources

[B1] Broadcom AutoSys Documentation — Kubernetes job type multi-container pod support, targeting a specific container for command execution (accessed 2026-08-18)
[B2] Apache Airflow Docs / CNCF Kubernetes Provider — `KubernetesPodOperator` parameters; absence of native `target_container` exec parameter; `full_pod_spec` for advanced pod definitions (accessed 2026-08-18)
