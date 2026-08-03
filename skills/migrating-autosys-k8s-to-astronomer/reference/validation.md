# Validation gates (control-plane-specific)

Additive to the core skill's per-job gates. These validate the platform layer this skill is responsible for.

## Gate K1: RBAC actually enforces what it claims

For each mapped role, log in (or exec) as a representative user in that role and confirm they can do what the equivalent AutoSys/WCC role allowed, and cannot do what it didn't. Don't validate RBAC by reading the Role/RoleBinding YAML — validate it by testing as the role.

## Gate K2: NetworkPolicy allows the required paths and blocks the rest

From an actual pod in the target namespace, test reachability to everything the workload needs (positive test) and confirm at least one deliberately-unrelated path is blocked (negative test) — a policy that accidentally allows everything "passes" the positive test while providing no isolation at all; the negative test is what catches that.

## Gate K3: Executor/autoscaling behaves as sized under real load

Run the pilot slice (Phase 3) under conditions approximating real concurrency and confirm pod startup latency, queue time, and resource utilization are within acceptable range — same principle as the on-prem-distributed skill's capacity gate, applied to the chosen executor rather than a VM-based worker pool.

## Gate K4: CI/CD deploy path works end to end, including rollback

Make an actual DAG change, merge it, confirm it deploys through the real pipeline (not a manual workaround), and confirm rollback to the prior version works — both directions need to be exercised, not just forward deploy.

## Gate K5: Secrets resolve correctly at runtime, not just in manual testing

Same principle as the on-prem-distributed skill's Gate T2: test secret resolution through the actual scheduled-task code path, not a manual fetch-and-verify done out of band.

## Recording results

Each parity checklist row in `k8s_parity_manifest.json` should carry which gates applied and passed, not just a final disposition — this is what `scripts/status.py summary` checks for before allowing a `complete` claim.
