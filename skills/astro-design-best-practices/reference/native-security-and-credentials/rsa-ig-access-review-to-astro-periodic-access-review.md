# RSA Identity Governance ACL/Access-Review Automation → Astro Periodic Access-Review Design

AutoSys environments integrated with **RSA Identity Governance** (formerly RSA Archer / RSA Via Lifecycle) to automate access certification campaigns — periodic reviews where managers approved or revoked users' access to AutoSys jobs and calendars. RSA IG pulled ACL data from CA EEM, presented it to reviewers, and wrote back revocations automatically [B1].

Astro has no native access-certification automation equivalent. The Astro periodic access review process is designed manually, with tooling automation possible via the Astro API and CLI.

## Access Review Design for Astro

### What to Review

| Scope | Review Subject | Tool |
|---|---|---|
| **Organization level** | Organization Owners, Billing Admins | Astro UI → Organization → Users |
| **Workspace level** | Workspace Owners, Operators, Authors | Astro UI → Workspace → Members |
| **Deployment level** | Deployment Admins, custom Deployment roles | Astro UI → Deployment → Members |
| **API Tokens** | Scoped tokens in use for CI/CD | Astro UI → API Tokens |
| **DAG-level access** (if Runtime 3.1-12+) | DAG-tag role assignments | Airflow UI → DAG-level permissions |

### Review Cadence (by Risk Level)

| Access Level | Recommended Review Frequency |
|---|---|
| Organization Owner | Quarterly |
| Workspace Owner | Quarterly |
| Workspace Operator/Author | Semi-annually |
| Deployment-scoped API Tokens | Quarterly (or on project completion) |
| SCIM-synced team memberships | Driven by IdP JML (Joiner/Mover/Leaver) process |

### Automation: Generating the Access Report

Use the Astro API to pull current user/role state programmatically — replacing manual UI screenshots:

```bash
# List all users in an Organization
astro organization user list --output json > org_users_$(date +%Y%m%d).json

# List all users in a specific Workspace
astro workspace user list --workspace-id <id> --output json > ws_users_$(date +%Y%m%d).json
```

Feed the output into your GRC (Governance, Risk, Compliance) tool or a simple spreadsheet for reviewer sign-off [B2].

### Joiner-Mover-Leaver (JML) Controls

If SCIM is enabled, the IdP handles automatic provisioning/deprovisioning. For teams without SCIM:
- **Leaver**: Immediately revoke Astro access when a user leaves (manual deactivation in Astro UI → Users → Deactivate).
- **Mover**: Review role assignments whenever a user changes teams.
- **Joiner**: Assign the minimum required role at onboarding; do not default new joiners to Workspace Owner.

### Compliance Evidence

For SOC 2 / ISO 27001 audit evidence, document:
- Date of review.
- Who performed the review (name and title).
- List of access reviewed (the JSON export from the CLI above).
- Actions taken (approved/revoked) and the ticket or approval record.

## Sources

[B1] RSA Identity Governance (RSA IG) documentation — ACL access certification campaigns, CA EEM integration for AutoSys access review (accessed 2026-08-11)
[B2] Astronomer Docs — Astro RBAC hierarchy (Org/Workspace/Deployment/DAG), Astro CLI `user list` commands, SCIM provisioning, API Token management (accessed 2026-08-11)
