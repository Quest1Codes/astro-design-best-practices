# Secrets and identity

## What AutoSys does today

Credential handling in a distributed AutoSys estate typically takes one of a few forms — confirm which applies before assuming a translation:

- **OS-level service accounts**: the agent runs the job as a specific local or domain service account already granted access to whatever the job touches; the "credential" is really the account the agent process runs as, not something the job definition carries explicitly.
- **CA/Broadcom credential management**: some AutoSys configurations store profile/credential references the job definition points to, resolved by the Application Server at run time.
- **External vault integration**: some shops wire AutoSys to an external secret store (e.g., CyberArk) so the agent fetches a credential at run time rather than storing it.

Because JIL's `machine:`/`owner:` attributes only name the job's execution identity, not its full auth model, the actual mechanism has to be confirmed with the platform team — do not infer it from JIL alone.

## Translating to Airflow/Astro

| Source pattern | Target |
|---|---|
| Fixed credential per job/system (username+password, API key, token) | An Airflow Connection, backed by a secrets backend (Astro Environment Manager secrets, HashiCorp Vault, AWS/GCP/Azure secret manager) rather than stored in plaintext in the metadata DB |
| Domain/Kerberos-based service account auth (common on Windows-agent jobs) | Depends on whether the *target* execution environment (Hosted vs. Hybrid, per `reference/execution-topology-mapping.md`) is domain-joined. Hosted workers generally are not — this is itself a signal pushing a machine group toward Hybrid, or toward re-provisioning a non-domain credential path for that specific system if the downstream system can support one |
| External vault integration already in place | Point Airflow's secrets backend at the same vault rather than re-platforming credential storage — this is usually the lowest-risk path and preserves existing rotation/audit practices |
| Human operator permissions (who can view/operate which jobs in WCC, typically LDAP/AD-group-driven) | Astro RBAC (Workspace/Deployment roles) mapped from the same LDAP/AD groups via SSO, so the access model doesn't have to be rebuilt manually per person |

## What to verify before cutover

- That the migrated Connection actually authenticates successfully from the *new* execution location (Hosted egress IP, or the Hybrid node) — a credential valid from an on-prem agent's network position is not guaranteed valid from a different network position, even with the same username/password, if the downstream system does IP allow-listing.
- That secret rotation continues to work post-migration — if AutoSys's credential mechanism auto-rotated (vault-integrated), confirm the Airflow-side secrets backend is wired to the same rotation source, not a static copy taken at migration time.
- Who owns the LDAP/AD groups being mapped to Astro RBAC, and whether that mapping needs its own approval/change-control step separate from the DAG migration itself.
