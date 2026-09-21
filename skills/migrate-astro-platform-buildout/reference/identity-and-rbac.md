---
topic: identity-and-rbac
family: migration
skill: migrate-astro-platform-buildout
verified_against:
  airflow: "3.3.1"
  astro_runtime: "3.3-2"
  autosys: "12.0"
last_verified: 2026-09-17
confidence: mixed
signals: []
---

# Identity and RBAC

MERGE ← `migrate-topology-onprem-distributed/reference/secrets-and-identity.md`'s identity half
(that file now carries a pointer here for the identity portion; its secrets portion stays there
as the topology-specific plan, and is also mirrored in `reference/secrets-and-identity.md` here
for the platform-buildout view).

## Human operator permissions

Who can view/operate which jobs in Web UI/WCC, typically LDAP/AD-group-driven → Astro RBAC
(Workspace/Deployment roles) mapped from the **same** LDAP/AD groups via SSO, so the access model
doesn't have to be rebuilt manually per person. See
`assess-astro-target-architecture/reference/decision-tables.md`'s `identity` decision for whether
an existing IdP was found (`nfr.idp`).

## EEM policy → Astro role procedure

```
python3 scripts/rbac_map.py --safex-export eem_policies.xml --out rbac_proposal.json --md rbac_proposal.md
```

Parses the `safex` XML export (format documented in
`autosys-reference/reference/security-eem-and-native.md`) into `(identity, resource class,
action)` triples, then proposes:

1. **Astro Organization roles** for identities with cross-instance/administrative policies.
2. **Workspace roles** for identities scoped to one team's Deployments.
3. **Deployment roles** for identities scoped to operate (not administer) a specific Deployment.
4. **Teams** grouping identities that share an identical policy set — reduces per-user role
   sprawl if the EEM export shows many identities with the same permissions.

**Flags EEM constructs with no Astro equivalent** explicitly — most commonly per-job ACL bits
(a policy granting one specific job's execute permission to one specific user), which don't map
cleanly onto Astro's Workspace/Deployment-level RBAC granularity. These become either a
documented gap (the access model gets coarser) or a candidate for Airflow's own DAG-level access
control if that's sufficient, never silently dropped.

## What to verify before cutover

Who owns the LDAP/AD groups being mapped to Astro RBAC, and whether that mapping needs its own
approval/change-control step separate from the DAG migration itself — RBAC changes are
organizationally sensitive even when technically straightforward.
