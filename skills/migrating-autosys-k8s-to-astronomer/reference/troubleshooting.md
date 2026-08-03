# Troubleshooting: known failure classes

Seed entries below are anticipated from the k8s-to-k8s topology; expand with actually-observed failures, fixing the class each time.

## "RBAC translation passed YAML review but a user can't do their job"

**Cause**: the Role/RoleBinding was translated by matching verbs/resources structurally against the source, without confirming the *effective* permission set (aggregated roles, default-deny gaps) matches what the user actually needs day to day.

**Fix the class**: always run Gate K1 (actual login-and-test) before trusting a structural YAML comparison; add the missing permission to the role definition, not as a one-off `kubectl` grant to the individual user.

## "NetworkPolicy translation blocks a path nobody remembered was needed"

**Cause**: the source policy's intent was inferred from its selector/rule structure without cross-checking against an actual traffic-flow log (or the platform team's knowledge) of everything that legitimately used that path — an intent-only rewrite silently drops rarely-used-but-real paths (e.g., a monthly job that talks to a system daily jobs don't touch).

**Fix the class**: before finalizing a NetworkPolicy rewrite, check the source estate's actual traffic (flow logs, or a review with whoever operates the affected jobs) for at least one full business-calendar cycle, not just the common daily paths.

## "Executor choice made estate-wide, then one domain's jobs perform badly"

**Cause**: the executor/autoscaling decision was made once for the whole estate from an average workload-shape read, missing a specific domain whose jobs are meaningfully different (much larger, much more isolation-sensitive) from the estate average.

**Fix the class**: re-examine `reference/executor-and-autoscaling.md`'s "mixed executor is normal" guidance — apply per-domain overrides rather than forcing every DAG onto the estate-wide default once a mismatched domain is found.

## "CI/CD pipeline deploys correctly but rollback fails the first time it's needed"

**Cause**: rollback was assumed to work because forward-deploy worked and the mechanism is "the same pipeline in reverse," but rollback was never actually executed before being needed for real.

**Fix the class**: Gate K4 requires exercising rollback specifically, during the trial phase, before any environment with real business impact is cut over — same discipline as the on-prem-distributed skill's cutover-rollback rule.

## "Secret 'migrated' but the workload still fails auth in the target"

**Cause**: the Kubernetes `Secret` object's value was copied into the new secrets backend, but the *reference* to it (Connection config, environment variable name, mount path) wasn't updated to match how the target backend actually exposes it — the value moved, the wiring didn't.

**Fix the class**: validate secret resolution through Gate K5 (actual scheduled-task run), not by confirming the value exists in the new backend's console/UI.
