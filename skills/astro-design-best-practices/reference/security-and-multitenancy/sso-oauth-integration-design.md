# SSO / OAuth Integration Design

AutoSys authentication was typically OS-level (PAM, LDAP, or AD) or EEM-managed. Astro uses a cloud-native identity model: SAML 2.0 for SSO and SCIM 2.0 for automated user lifecycle management.

## Core integration: SAML 2.0

Astro supports SAML 2.0 for enterprise SSO [B2][B3]. Setup flow:

1. In the Astro UI (`Security > Authentication`), create an SSO connection to obtain the Service Provider (SP) details:
   - Assertion Consumer Service (ACS) URL
   - Entity ID (SP Entity ID)
2. Create an application integration in your IdP (Okta, Microsoft Entra ID, CyberArk, etc.) using these SP details [B4][B5].
3. Paste the IdP's metadata (SSO URL, X.509 certificate) back into the Astro UI [B4][B6].
4. Verify one or more email domains to link them to the SSO connection [B7][B8].
5. Test with a non-admin user before enforcing [B4][B13].
6. Enable SSO enforcement to disable password/social login for mapped domains [B7][B9].

> **Configure the SSO bypass link** for admin break-glass access in case of IdP outage [B4][B10].

## SCIM 2.0: automated user lifecycle

SCIM automates user provisioning and deprovisioning from your IdP directly into Astro [B1][B11]:

| SCIM capability | Astro behaviour |
|---|---|
| Create user in IdP | User is provisioned in Astro |
| Remove user from IdP group | User is deprovisioned from Astro |
| Update user profile | Synced to Astro profile |
| Sync IdP group as Astro Team | Group → Team mapping (flat; nested groups not supported) [B1][B11] |

Prerequisites [B1][B12]:
- SSO connection must be configured first
- Organization API token with sufficient permissions to authorize the SCIM connector

Optimized for Okta and Microsoft Entra ID [B1][B11]. Generic OIDC is also supported for non-standard IdP configurations [B14][B15].

## Deployment model (Axis A — H rating)

| Deployment model | SSO/SCIM scope |
|---|---|
| **Astro Hosted** | Organization-level SSO; configure once, enforced across all Workspaces |
| **Astro Private Cloud** | SSO configured per deployment context; consult current docs for Private Cloud-specific parameters [B16] |

## Org model (Axis D — H rating)

| Org model | Identity approach |
|---|---|
| **One enterprise IdP, one Astro org** | Single SSO connection; SCIM groups → Astro Teams → Workspace roles |
| **Multiple BU IdPs** | One SSO connection per domain; combine with Authorized Workspaces per BU |
| **Federated / self-service teams** | Central IdP with per-team SCIM groups provisioning Workspace-level access |

## Compliance callout (Axis E — H rating)

For HIPAA/SOX estates:
- Enforce SSO to eliminate username/password authentication paths
- Use SCIM to ensure immediate deprovisioning when employees leave (no orphaned accounts)
- Export audit logs to SIEM to capture login events (see topic 039)

## Sources

[B1, B11, B12] Astronomer Docs — Set up SCIM: https://www.astronomer.io/docs/astro/set-up-scim (accessed 2026-08-08)
[B2, B3] Astronomer Docs — Set up SSO (SAML): https://www.astronomer.io/docs/astro/configure-idp (accessed 2026-08-08)
[B4, B7, B9, B10, B13] Astronomer Docs — SSO configuration steps (accessed 2026-08-08)
[B5] CyberArk — SAML integration with Astronomer (accessed 2026-08-08)
[B6] GitHub — Astronomer SAML setup (accessed 2026-08-08)
[B8] Astronomer Docs — Domain verification (accessed 2026-08-08)
[B14, B15] Astronomer Docs — Generic OIDC configuration (accessed 2026-08-08)
[B16] Astronomer Docs — Astro Private Cloud SSO specifics (accessed 2026-08-08)
