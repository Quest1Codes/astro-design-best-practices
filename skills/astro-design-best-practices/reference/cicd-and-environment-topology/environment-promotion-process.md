# Environment Promotion Process

In legacy schedulers like AutoSys, promoting a job meant extracting JIL from the dev environment and importing it into prod, often requiring manual tweaks to machine names or file paths. In Astro, promotion relies on immutable container images and strict Git-based promotion.

## The Promotion Flow

Promoting a DAG from Development to Production should never involve manually copying files. It is an automated transition through the Git branching strategy (see topic 056).

### 1. Code Promotion (Git Flow)
1. **Dev → Staging**: A PR is opened to merge the `develop` branch into `staging`. The CI pipeline runs tests. Once merged, CI deploys the `staging` branch to the Staging Deployment.
2. **Staging → Prod**: After UAT, a PR merges `staging` into `main`. The CI pipeline deploys `main` to the Production Deployment.

### 2. Image Promotion (Container Flow)
For strict regulatory environments (Axis E), relying on Git merges can introduce risk if dependencies shift between the Staging build and the Production build.
- **Best Practice**: Instead of pushing source code and rebuilding the Docker image in Production, build the image *once* in Staging.
- After Staging is verified, promote the exact same **Docker Image Tag** to the Production Deployment using `astro deploy --image` (or updating the tag in the Helm chart if using Astro Private Cloud) [B1][B2]. This guarantees absolute parity between tested code and production code.

## Handling Configuration Differences

The code promoted must be 100% identical. How do you handle environment-specific logic (e.g., writing to the `dev` database vs the `prod` database)?

- **Do not use conditional logic in DAGs**: `if os.getenv('ENV') == 'prod': conn_id = 'prod_db'` is an anti-pattern.
- **Use abstracted Connection IDs**: The DAG code always uses `conn_id = 'data_warehouse'`.
- **Environment config**: In the Dev Deployment, configure the `data_warehouse` connection to point to the sandbox. In the Prod Deployment, configure it to point to production. The environment resolves the abstraction at runtime, requiring zero code changes during promotion.

## Rollbacks during promotion failure

If a promotion to Production causes immediate issues, utilize Astronomer's built-in **Deploy Rollbacks** feature (see topic 059) to instantly revert the Deployment to the previous known-good state via the Astro UI, bypassing the CI/CD pipeline for the emergency fix [B3].

## Sources

[B1, B2] Astronomer Docs & Architecture Guides — CI/CD image promotion and deploy commands (accessed 2026-08-08)
[B3] Astronomer Docs — Deploy Rollbacks (accessed 2026-08-08)
