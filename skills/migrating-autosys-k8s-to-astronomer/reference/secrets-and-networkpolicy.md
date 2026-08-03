# Secrets and NetworkPolicy translation

## Secrets: never copy, always re-home

A `Secret` object appearing in the source k8s export is evidence that *something* needs a credential in the target, not something to base64-decode and re-encode into a new `Secret` object. Re-homing means:

1. Identify what the secret actually is (a database credential, an API token, a certificate) — the k8s `Secret`'s `data` keys and the workload that mounts it usually make this clear; if not, ask the platform team rather than guessing from a key name like `password`.
2. Put it in the target's actual secrets backend (Astro Environment Manager secrets, or whatever external secrets manager — Vault/AWS/GCP/Azure — the target Astronomer deployment is wired to), following that backend's own rotation and access-control model.
3. Reference it from Airflow as a Connection or Variable backed by that secrets backend — not as a raw Kubernetes `Secret` mounted into a pod, unless the target's secrets backend integration specifically works that way (some do, via a Secrets Manager backend that materializes as an env var or file — confirm the actual mechanism the target uses rather than assuming the source's mounting pattern carries over).

Copying secret *values* forward this way (re-entering them into the new backend, not transcribing YAML) is fine and expected; copying the *Kubernetes object* forward is the anti-pattern to avoid, since it usually means the new secrets backend's rotation/audit benefits get bypassed entirely.

## NetworkPolicy: rewrite the intent, not the selector

Source NetworkPolicies are almost always written against AutoSys-specific pod labels (whatever the source Helm chart/manifests used — commonly something like `app: autosys-agent` or `component: event-server`). These labels don't exist in an Astronomer deployment. For each source policy:

1. State its actual intent in plain language: what's allowed to reach what, and why (e.g., "agent pods can reach the Application Server on port X; nothing else can reach agent pods").
2. Find the equivalent boundary in the target: Airflow's own components (scheduler, workers/triggerer, webserver, metadata DB) and their actual labels in the target Helm chart/Astronomer deployment.
3. Author a new policy expressing the same intent against the new labels — don't attempt to relabel target pods to match the old policy's selectors, since that fights the platform's own conventions and breaks on the next upgrade.

## What "absent" means

If no NetworkPolicy objects are found in the export, don't assume none is needed for the target — the source cluster may have relied on a broader boundary instead (a dedicated node pool with its own network ACLs/security groups, or a service mesh's own policy layer not expressed as a Kubernetes `NetworkPolicy` object). Confirm which applied before deciding the target needs nothing added.

## Confirm both directions

For any two-directional flow (e.g., an FT-job partner relationship carried over from the core skill's manifest, agent-to-Application-Server callbacks), confirm the rewritten policy allows traffic both ways as the original relationship required — a policy correctly allowing egress from workers to a database but forgetting the metadata DB needs to reach back (rare, but possible for certain callback patterns) is a common one-directional-rewrite mistake.
