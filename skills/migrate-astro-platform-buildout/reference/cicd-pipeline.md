---
topic: cicd-pipeline
family: migration
skill: migrate-astro-platform-buildout
verified_against:
  airflow: "3.3.1"
  astro_runtime: "3.3-2"
last_verified: 2026-09-17
confidence: mixed
signals: []
---

# CI/CD pipeline

MERGE ← `migrate-topology-k8s/reference/cicd-and-gitops.md` (kept in full — the source-pattern
table and "what NOT to carry forward" prose apply beyond the k8s-specific companion).

## What to find out first

How JIL/config changes reach the source estate today, each with a different translation:

| Source pattern | Target pattern |
|---|---|
| Manual `jil` load / manual WCC edits against a running Application Server | The clearest win available — replace with `astro deploy` (or the pipeline pattern below) from day one; no reason to preserve a manual-apply workflow |
| A custom CI pipeline that builds and applies JIL/config via a script | Map stages 1:1: build → test → deploy becomes build (DAG bundle) → test (`migrate-jil-to-airflow-translation`'s Gates 1/2: import, lint) → `astro deploy` |
| A GitOps controller reconciling JIL/config from a Git repo | The closest existing pattern to Airflow's own "DAGs as code" model — keep the GitOps controller if the target is Astronomer Software/Hybrid and it already manages other cluster resources; point it at the Astro project structure, or use `astro deploy` directly if GitOps was only ever used for this one purpose |
| A sidecar/init-container syncing JIL from a repo into a running Application Server | Superseded — Airflow doesn't need a live-syncing sidecar; DAG files ship with the deploy itself |

## What "done" looks like

1. **Source control**: DAG code (and `include/` data, requirements) in Git — a genuine
   improvement if JIL was previously managed by hand through WCC.
2. **Automated validation**: `migrate-jil-to-airflow-translation`'s Gate 1/2 run in CI on every
   PR, not just locally before a manual deploy.
3. **Deploy mechanism**: `astro deploy` triggered by merge to the appropriate branch, mapped to
   the appropriate environment — mirror the source pipeline's branch/environment mapping, don't
   invent a new branching model unless asked.
4. **Rollback**: confirm the deploy mechanism supports a fast rollback (previous
   image/bundle redeploy) and that it's been **tested**, not just assumed available — this is
   platform validation gate P4.

## What NOT to carry forward

Any manual, undocumented step in the source deployment process ("someone SSHs in and restarts
the agent after a JIL load") is a smell to eliminate, not preserve — flag it in the report as a
gap being closed, and confirm with the platform team there isn't a reason (a manual approval
gate, a compliance sign-off) that step was actually serving before removing it outright.
