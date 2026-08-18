# autosys_secure Security Bootstrap → Astro Workspace/Deployment RBAC Bootstrap Design

`autosys_secure` is the AutoSys command used to perform system-level security configuration — setting up the security database, initializing encryption keys, and bootstrapping the security provider (EEM or native) for a new AutoSys instance [B1]. It is the one-time setup step that makes the instance security-aware.

In Astro, there is no equivalent single-command bootstrap — RBAC is configured through the Astro UI or API using a declarative, layered model. The equivalent of "security bootstrap" is the initial Workspace/Deployment creation and role assignment sequence, which should be managed as Infrastructure as Code (Terraform).

## Bootstrapping Sequence on Astro

### Step 1: Configure SSO at the Organization Level
Configure your IdP (Okta/Entra ID) in **Astro UI → Settings → Security** [B2]. This is the equivalent of pointing AutoSys to its EEM security provider. Until SSO is configured, users log in with local credentials — enforce SSO and disable alternative login methods for production.

### Step 2: Enable SCIM Provisioning (Optional but Recommended)
Enable SCIM in **Astro UI → Settings → Security** with an Organization API token that has Organization Owner permissions [B2]. SCIM syncs IdP group membership to Astro Teams automatically — eliminating manual user provisioning (the `autosys_secure` equivalent for ongoing user management).

### Step 3: Create Workspaces and Assign Team Roles
```bash
# Terraform-managed bootstrap (recommended approach)
resource "astro_workspace" "finance_prod" {
  name              = "finance-prod"
  cicd_enforced     = true
}

resource "astro_workspace_team_role" "finance_engineers" {
  workspace_id = astro_workspace.finance_prod.id
  team_id      = data.astro_team.finance_engineers.id
  role         = "WORKSPACE_OPERATOR"
}
```

Manage all Workspace and Deployment creation through **Terraform (Astro Terraform Provider)** [B2]. This makes the bootstrap reproducible, auditable, and version-controlled.

### Step 4: Bootstrap Deployment API Tokens for CI/CD
Create scoped API tokens for each Deployment's CI/CD pipeline:
```bash
astro deployment token create --name "finance-prod-ci" \
  --role DEPLOYMENT_ADMIN \
  --deployment-id <deployment-id>
```

Store the token in your CI/CD secrets manager (not in code) [B2].

## Security Bootstrap Checklist

| Step | AutoSys Equivalent | Astro Action |
|---|---|---|
| Initialize security provider | `autosys_secure` | Configure SSO IdP in Astro UI Settings |
| Define encryption/auth keys | `autosys_secure` key setup | Managed by Astronomer infrastructure |
| Create service accounts | EEM service accounts | Create Deployment-scoped API Tokens |
| Assign initial admin | EEM SuperUser | Assign Organization Owner role to bootstrap user |
| Enforce security policy | EEM policy creation | Enable SSO enforcement; disable basic auth |

## Sources

[B1] Broadcom AutoSys Documentation — `autosys_secure` command, security database initialization, EEM bootstrap (accessed 2026-08-11)
[B2] Astronomer Docs — SSO configuration, SCIM prerequisite (Org API token with Owner permissions), Astro Terraform Provider, Deployment-scoped API Tokens, SSO enforcement (accessed 2026-08-11)
