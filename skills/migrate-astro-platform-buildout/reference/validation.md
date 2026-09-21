---
topic: validation
family: migration
skill: migrate-astro-platform-buildout
verified_against:
  airflow: "3.3.1"
  astro_runtime: "3.3-2"
last_verified: 2026-09-17
confidence: mixed
signals: []
---

# Platform validation gates (P1-P6)

Unlike `migrate-jil-to-airflow-translation/reference/validation.md`'s per-job/box gates, these
validate the platform itself — run once per environment, not once per job.

## Gate P1: Login/SSO

Confirm a real user (not just an admin service account) can log in via the configured
IdP/SSO integration (`reference/identity-and-rbac.md`). Test with a non-privileged account,
not just the account that did the provisioning.

## Gate P2: RBAC enforces

Confirm the RBAC mapping from `rbac_map.py`'s proposal actually restricts access as intended —
a user mapped to a Deployment-scoped role should NOT be able to see/operate a different
Deployment. Test the negative case explicitly (what a role *cannot* do), not just the positive.

## Gate P3: Secret resolves at runtime

Confirm a Connection backed by the chosen secrets backend actually resolves inside a running
task, from the actual target execution environment (Hosted egress IP or Hybrid node) — see
`reference/secrets-and-identity.md`'s "what to verify before cutover."

## Gate P4: Deploy and rollback

Confirm `astro deploy` succeeds, and confirm the rollback path (previous image/bundle redeploy)
actually works — tested, not just assumed available. This is the gate most often skipped in
practice and most costly to discover broken during an actual incident.

## Gate P5: Alert fires end-to-end

Trigger a real failure (a deliberately-failing test task) and confirm the alert actually reaches
the configured destination (ITSM ticket, Slack, PagerDuty) — configuring routing and never
testing it fire is not "done" (`reference/alerting-and-observability-wiring.md`).

## Gate P6: RE agent / worker queue reachability

For any machine group using a Remote Execution agent or a dedicated worker queue
(`migrate-topology-onprem-distributed`/`migrate-topology-k8s`), confirm actual network
reachability from that specific execution point to every system the group's jobs touch — a
network path that works from the control plane does not guarantee it works from a
Hybrid/RE-agent execution point.

## Recording gate results

Track via `_lib.autosys_jil.status --manifest estate_manifest.json advance <component> --workflow platform --status <state>` per platform component (identity, secrets, pipelines, observability, worker-queues) — `summary --workflow platform` should read `validated` for every component before this skill's phase is called done.
