# CA EEM vs. Native OS Security-Provider Migration → Astro RBAC Provider Design

AutoSys supports two authentication security models: **Native OS** (permissions granted based on OS-level users) and **CA EEM (Embedded Entitlements Manager)** — the default enterprise model. EEM centralizes authentication and authorization, integrating with LDAP/Active Directory and defining Security Policies that map group membership to AutoSys resource access. CA EEM also provides SSO integration via CA SiteMinder [B1].

**CA EEM cannot be used as an IdP for Astro.** Astro requires modern OIDC/SAML-compatible identity providers [B2]. The migration strategy is to use the corporate IdP (which EEM was already federating to) as the new unified source of truth.

## Security Model Migration

{syn: CA EEM Security Policy → Astro RBAC role assignment; CA EEM user/group → Astro Team; AutoSys native OS security → Astro local user with no IdP}

| AutoSys Security Concept | Astro Equivalent | Notes |
|---|---|---|
| **CA EEM Security Policy** | Astro RBAC role assignment (Org/Workspace/Deployment) | Policies become role assignments tied to Teams [B2]. |
| **EEM user group (from LDAP/AD)** | **Astro Team** (mapped from IdP group via SCIM) | Teams in Astro are the group-level access unit [B2]. |
| **LDAP/AD group → EEM → AutoSys** | **LDAP/AD group → IdP (Okta/Entra ID) → Astro** | Remove EEM from the chain; IdP becomes the direct Astro provider [B2]. |
| **Native OS security** | Astro local user account | Acceptable only for non-enterprise/dev scenarios; enforce SSO for prod [B2]. |

## Supported Identity Providers on Astro

Astro natively supports SAML/OIDC SSO integration with [B2]:
- **Microsoft Entra ID** (formerly Azure AD)
- **Okta**
- **OneLogin**
- **Ping Identity**

SCIM provisioning (automated user and team sync) is supported for **Okta** and **Entra ID** [B2].

## Migration Design Decision

**If your organization already uses Okta or Entra ID (which CA EEM was federating against)**: Configure Astro SSO directly against that IdP. Map existing AD/LDAP groups to Astro Teams. This is a straight-line migration with no new IdP required.

**If your organization only used EEM native user store**: You must provision a modern IdP (Okta or Entra ID is recommended) as part of the migration. This is an infrastructure dependency that must be sequenced before Astro onboarding.

## CI/CD Service Accounts

AutoSys automation used EEM service accounts for cross-system integration. On Astro:
- Use **Astro API Tokens** (scoped to Organization, Workspace, or Deployment level) for CI/CD pipelines [B2].
- Never use human user credentials for automation. API tokens are the correct abstraction.

## Sources

[B1] Broadcom AutoSys Documentation — CA EEM integration, native OS security provider, LDAP/AD federation, Security Policy model, CA SiteMinder SSO (accessed 2026-08-11)
[B2] Astronomer Docs — SSO configuration (Okta, Entra ID, OneLogin, Ping), SCIM provisioning, Teams, Astro RBAC roles, API Tokens (accessed 2026-08-11)
