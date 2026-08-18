# Branching Strategy for DAG Code

Because Airflow pipelines are written in Python, they inherit modern software engineering practices. AutoSys teams migrating to Astro must shift from editing jobs directly in the GUI/CLI to managing DAG code via standard Git branching strategies.

## Environment-to-Branch Mapping

The most robust strategy for Astro is mapping long-lived Git branches directly to permanent Astro Deployments [B1][B2].

| Git Branch | Astro Deployment | Purpose |
|---|---|---|
| `main` (or `production`) | Production Deployment | The source of truth. Highly protected. Deploys here are automated via CI upon PR merge. |
| `staging` (or `release`) | Staging Deployment | Pre-production environment. Code here is actively being integration-tested. |
| `develop` | Development Deployment | Integration branch for feature development. |
| `feature/*` | Ephemeral / Local only | Short-lived branches created by individual developers to build new DAGs. |

## The Developer Workflow

1. A developer creates `feature/new-sales-dag` from the `develop` branch.
2. They write code and test it locally using `astro dev start` (see topic 062) [B3].
3. They open a Pull Request (PR) against the `develop` branch.
4. The CI pipeline runs Parse Gates (topic 055).
5. Upon approval and merge, the CI pipeline automatically runs `astro deploy` to push the `develop` branch to the Dev Deployment [B1].

## Astronomer Native GitHub Integration

Astronomer provides a native GitHub integration that dramatically simplifies this mapping [B1].
- You can map the `main` branch to the Production deployment directly in the Astro UI.
- When a commit is merged to `main`, Astronomer detects the webhook and handles the deployment automatically, removing the need for custom GitHub Actions deployment scripts.
- **Visibility**: This integration surfaces the Git commit hash, commit message, and author directly in the Astro UI for full auditability [B1].

## Anti-Patterns

- **Direct pushes to `main`**: All long-lived branches must be protected. Force teams to use PRs to ensure the parse gate runs.
- **Manual deployments**: Do not allow developers to run `astro deploy` from their laptops targeting Production. Disable local deploy permissions for the Production workspace.

## Sources

[B1, B2] Astronomer Docs — CI/CD branching strategies and Native GitHub Integration (accessed 2026-08-08)
[B3] Astronomer Docs — Local development workflow (accessed 2026-08-08)
