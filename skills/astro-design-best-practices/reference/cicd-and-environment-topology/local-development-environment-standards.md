# Local Development Environment Standards (`astro dev`)

AutoSys development often occurred directly against a shared development database, causing conflicts and preventing offline work. The industry standard for Airflow development is to use the **Astro CLI** to run containerized, isolated environments locally on developer machines [B1][B2].

## Core standards for local development

To eliminate "it works on my machine" discrepancies, mandate the following standards for all DAG developers:

### 1. Always use the Astro CLI
- Do not install Airflow via `pip install apache-airflow` globally. 
- Use `astro dev init` to generate the standardized project structure (`dags/`, `plugins/`, `include/`) [B2][B8].
- Use `astro dev start` to orchestrate the Webserver, Scheduler, and Metadata DB locally [B3][B6].

### 2. Containerized workflow
By default, the CLI uses Docker (or Podman) [B6][B7]. This is critical because it ensures developers are testing against the exact same base image and Python dependencies that will run in the cloud production environment [B3][B4].

### 3. Tighten the Dev Loop
- When editing Python files in the `dags/` folder, the local Airflow scheduler hot-reloads them automatically. No restart required.
- When editing `requirements.txt`, `packages.txt`, or the `Dockerfile`, developers must run `astro dev restart` to rebuild the container image with the new dependencies [B6][B10].
- When a clean slate is needed (e.g., DB state is corrupted locally), use `astro dev kill` to destroy all containers and volumes, then restart [B6].

### 4. Standalone Mode (Airflow 3+)
For rapid iteration without Docker overhead, Airflow 3 introduces Standalone Mode.
- Run `astro dev start --standalone`.
- This boots Airflow in a local Python virtual environment (`venv`). It is faster, but lacks the strict environment parity of the Docker method. Use Standalone for logic testing, but verify in Docker before opening a PR [B6][B7].

## IDE Integration

Enhance productivity by standardizing IDE setups.
- **VS Code Dev Containers**: Use the Dev Containers extension to run the IDE *inside* the Astro Docker container. This ensures autocompletion, linting, and syntax highlighting correctly reflect the project's specific dependency versions (e.g., catching if an import is missing from `requirements.txt`) [B11].

## Configuration handling

- Do not hardcode credentials in DAG files.
- Store project-level configurations in `.astro/config.yaml`.
- Store local development secrets in a local `.env` file that is ignored by Git, allowing `astro dev start` to load them as environment variables without exposing them to source control [B16][B17].

## Sources

[B1, B3, B4] Astronomer Docs & Architecture Guides — Astro CLI local development standards (accessed 2026-08-08)
[B2, B8, B18] Astronomer Docs & GitHub — `astro dev init` and project structure (accessed 2026-08-08)
[B6, B7, B10] Astronomer Docs — CLI commands (`start`, `restart`, `kill`, standalone) (accessed 2026-08-08)
[B11] Astronomer Docs — VS Code Dev Containers integration (accessed 2026-08-08)
[B16, B17] Astronomer Docs — Local configuration and secrets management (accessed 2026-08-08)
