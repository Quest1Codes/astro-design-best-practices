---
topic: secrets-and-identity
family: migration
skill: migrate-astro-platform-buildout
verified_against:
  airflow: "3.3.1"
  astro_runtime: "3.3-2"
  autosys: "12.0"
last_verified: 2026-09-17
confidence: mixed
signals: [credential_hits]
---

# Secrets

MERGE ← `migrate-topology-onprem-distributed/reference/secrets-and-identity.md`'s secrets half.

## What AutoSys does today

Confirm which applies before assuming a translation — do not infer from JIL alone:

- **OS-level service accounts**: the agent runs the job as a specific local/domain account
  already granted access; the "credential" is the account the agent runs as, not something the
  job definition carries explicitly.
- **CA/Broadcom credential management**: some configurations store profile/credential
  references the job definition points to, resolved by the Application Server at run time.
- **External vault integration**: some shops wire AutoSys to an external secret store (e.g.
  CyberArk) so the agent fetches a credential at run time.

`_lib.autosys_jil.commands.analyze()`'s `credential_hits` (pattern name, never value) is the
mechanical signal for credentials embedded directly in commands — a fourth, less disciplined
pattern worth naming explicitly in the report as a security finding.

## Translating to Airflow/Astro

| Source pattern | Target |
|---|---|
| Fixed credential per job/system | An Airflow Connection, backed by the secrets backend from `manifest.architecture.decisions.secrets_backend` — never stored in plaintext in the metadata DB |
| Domain/Kerberos-based service account auth | Depends on whether the target execution environment is domain-joined — Hosted workers generally are not; this pushes toward Hybrid or a non-domain credential path for that system |
| External vault integration already in place | Point Airflow's secrets backend at the same vault rather than re-platforming credential storage — lowest-risk path, preserves existing rotation/audit practices |
| Credential embedded directly in a command (`credential_hits`) | Extract into a Connection immediately; this is technical debt on the AutoSys side too, not something to carry forward as-is |

## Connection naming

`<system>_<environment>` (e.g. `bloomberg_prod`) as a default absent an existing convention;
check `dag_conventions_scan.py`'s brownfield findings first.

## What to verify before cutover

- The migrated Connection actually authenticates from the **new** execution location (Hosted
  egress IP, or the Hybrid node) — a credential valid from an on-prem agent's network position
  is not guaranteed valid from a different one, especially with IP allow-listing downstream.
- Secret rotation continues to work post-migration — if AutoSys's mechanism auto-rotated
  (vault-integrated), confirm the Airflow-side secrets backend is wired to the same rotation
  source, not a static copy taken at migration time.
