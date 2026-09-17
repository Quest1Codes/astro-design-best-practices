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

**SCIM provisioning itself is limited to Okta and Microsoft Entra ID** [B1][B11] — there is no generic-OIDC path for SCIM specifically. **Correction**: an earlier draft of this file added "Generic OIDC is also supported for non-standard IdP configurations" directly after the SCIM-scope sentence, citing [B14][B15] — but those citations were never independently confirmed (the file's own Sources note says so), and the claim itself likely conflates two different things: OIDC is an alternative *SSO* protocol to SAML (a separate capability, see the Core Integration section above), not a SCIM provisioning mechanism. If you need SCIM-equivalent provisioning with a non-Okta/Entra IdP, treat that as a gap to design around (SCIM API tokens / manual provisioning), not as something Generic OIDC solves — `NEEDS_EXEC_CHECK` if this needs to be relied on.

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
[B4, B7, B9, B10, B13] Astronomer Docs — Set up SSO (SAML), configuration steps (same page as B2/B3): https://www.astronomer.io/docs/astro/configure-idp (tier 1, URL added on citation review)
[B5] CyberArk — SAML integration with Astronomer (third-party, out of scope for Astronomer docs MCP; not re-verified on this pass)
[B6] GitHub — Astronomer SAML setup (third-party, out of scope for Astronomer docs MCP; not re-verified on this pass)
[B8] Astronomer Docs — Set up SSO (SAML) (no dedicated standalone "domain verification" page found; closest confirmed match is the general SSO setup page): https://www.astronomer.io/docs/astro/configure-idp (tier 1, URL added on citation review)
[B14, B15] Astronomer Docs — Generic OIDC configuration (no confident page match found on this pass — search results for this exact topic were inconclusive; verify separately before relying on this citation)
[B16] Astronomer Docs — Astro Private Cloud SSO specifics (no confident page match found on this pass; verify separately)
