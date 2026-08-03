# CI/CD and GitOps

## What to find out first

Before proposing a target pipeline, establish how JIL/config changes reach the source cluster today. Common patterns, each with a different translation:

| Source pattern | Target pattern |
|---|---|
| Manual `kubectl apply` / manual JIL load against a running Application Server | The clearest win available in this migration — replace with `astro deploy` (or the CI/CD pipeline pattern below) from day one; there is no reason to preserve a manual-apply workflow |
| A custom CI pipeline that builds an image and applies JIL/config via a script | Map the pipeline's stages 1:1 where possible: build → test → deploy becomes build (DAG image/bundle) → test (the core skill's validation gates: import, lint, execution) → `astro deploy` |
| A GitOps controller (Argo CD/Flux) reconciling JIL/config from a Git repo | The closest existing pattern to Airflow's own "DAGs as code" model — keep the GitOps controller if the target is Astronomer Software/Hybrid and it already manages other cluster resources; point it at the Astro project repo structure instead of the AutoSys config repo, or use `astro deploy` directly if GitOps was only ever used for this one purpose |
| A sidecar or init-container syncing JIL from a repo into a running Application Server | Superseded — Airflow doesn't need a live-syncing sidecar; DAG files ship with the deploy itself |

## What "done" looks like

A complete CI/CD parity story includes:

1. **Source control**: DAG code (and `include/` data, requirements) lives in a Git repo, same as the JIL-in-Git pattern if one existed, or a genuine improvement (version control, review) if JIL was previously managed by hand through WCC.
2. **Automated validation**: the core skill's Gate 1/2 (import, lint) run in CI on every PR, not just locally before a manual deploy.
3. **Deploy mechanism**: `astro deploy` (or the target's CI/CD integration) triggered by merge to the appropriate branch, mapped to the appropriate environment (dev/staging/prod) — mirroring whatever branch/environment mapping the source pipeline used, don't invent a new branching model unless asked.
4. **Rollback**: confirm the deploy mechanism supports a fast rollback (previous image/bundle redeploy) and that it's been tested, not just assumed available.

## What NOT to carry forward

Any manual, undocumented step in the source deployment process ("someone SSHs in and restarts the agent after a JIL load") is a smell to eliminate, not preserve — flag it in the report as a gap being closed, and confirm with the platform team there isn't a reason (a manual approval gate, a compliance sign-off) that step was actually serving before removing it outright.
