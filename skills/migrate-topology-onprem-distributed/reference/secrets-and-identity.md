---
topic: secrets-and-identity
family: migration
skill: migrate-topology-onprem-distributed
verified_against:
  airflow: "3.3.1"
  astro_runtime: "3.3-2"
  autosys: "12.0"
last_verified: 2026-09-17
confidence: mixed
signals: [credential_hits]
---

# Secrets and identity

Moved. Full content (source patterns, translation table, `rbac_map.py` procedure, what to verify
before cutover) now lives in `migrate-astro-platform-buildout`:

- **Secrets**: `migrate-astro-platform-buildout/reference/secrets-and-identity.md`
- **Identity/RBAC**: `migrate-astro-platform-buildout/reference/identity-and-rbac.md`

This companion's `reference/execution-topology-mapping.md` still covers the Hosted-vs-Hybrid
network-posture question that credential domain-joining interacts with — read that alongside the
platform-buildout skill's secrets file, not instead of it.
