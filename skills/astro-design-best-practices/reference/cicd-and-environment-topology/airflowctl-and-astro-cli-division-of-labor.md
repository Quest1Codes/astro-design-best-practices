---
topic: airflowctl-and-astro-cli-division-of-labor
family: knowledge
skill: astro-design-best-practices
verified_against:
  airflow: "3.3.1"
  astro_runtime: "3.3-2"
last_verified: 2026-09-17
confidence: mixed
signals: []
---

# `airflowctl` and `astro` CLI: Division of Labor

This is the Astro-side companion to `autosys-reference/reference/commands.md`'s `autorep`/
`sendevent` coverage — where those AutoSys operational actions land once translated. Replaces the
old base skill's `platform-and-cli-equivalents.md` command table (moved: the AutoSys-side half of
that table now lives in `autosys-reference/reference/commands.md`; this file covers the Astro-side
half in more depth than that table did).

> PRACTITIONER JUDGMENT: this file was written without live Astronomer/Apache Airflow docs MCP
> access this session. `airflowctl` (an official Apache Airflow project CLI, distinct from
> Astronomer's `astro` CLI) and its exact current command surface are described here at the level
> of general division-of-labor, not exact flag syntax — treat any specific subcommand named below
> as **NEEDS_EXEC_CHECK** against the installed Airflow/Astro CLI versions before scripting against
> it.

## The two CLIs are not interchangeable

- **`airflowctl`** operates against a *running Airflow instance's* own API — it is Airflow-project
  tooling, not Astronomer-specific, and works the same way whether that Airflow instance happens to
  be running on Astro, self-managed, or local. Actions in its scope: triggering/inspecting DAG
  runs, managing Variables/Connections/Pools through the Airflow REST API, and other
  instance-internal operations — the direct successor to what `sendevent`/`autorep` did against a
  single AutoSys instance.
- **`astro`** operates at the *platform* layer — Workspace/Deployment lifecycle, deploys (image and
  DAG-only), environment/Deployment-scoped configuration, local `astro dev` project scaffolding
  and testing, and CI/CD integration. It has no AutoSys-side analogue at all; AutoSys had no
  equivalent of "create a new isolated scheduler+metadata-DB environment" as a routine CLI
  operation the way `astro deployment create` does.

## Division-of-labor table

| Action | Tool | AutoSys equivalent |
|---|---|---|
| Trigger a DAG run | `airflowctl` (or the Airflow REST API directly, or the Airflow UI) | `sendevent -E STARTJOB -J <job>` |
| Pause/unpause a DAG | `airflowctl` | `sendevent -E JOB_ON_ICE` / `JOB_OFF_ICE` (job-granular vs. Airflow's DAG-granular pause — same caveat as `autosys-reference/reference/commands.md`) |
| Query DAG-run/task-instance status | `airflowctl`, or a REST API call, or `autorep-to-airflow-metadata-db-reporting.md`'s SQL/REST equivalents | `autorep -j <job> -q` |
| Manage Variables/Connections/Pools from a script | `airflowctl` | No direct AutoSys equivalent (`%%VAR%%` had no CLI-managed lifecycle) |
| Deploy new/changed DAG code | `astro deploy` (image or `--dags`-only) | `jil < file.jil` (definition load) |
| Create/configure a Workspace or Deployment | `astro workspace` / `astro deployment` | No AutoSys equivalent — closest conceptual analogue is provisioning a new AutoSys instance, which was an infrastructure project, not a CLI action |
| Local development/testing before deploy | `astro dev` | No AutoSys equivalent — JIL had no local-execution sandbox comparable to `astro dev` |
| CI/CD pipeline steps (parse-gate, deploy) | Both — `astro deploy` for the push, `airflowctl`/REST for any post-deploy smoke check that inspects DAG-run state | See `dag-testing-and-parse-gates-before-merge.md` |

## Design guidance

- Keep operational runbooks (the kind of thing `dag-ownership-and-support-model-design.md`'s
  `doc_md` standard captures) scoped to `airflowctl`/REST API actions — these are the ones an
  on-call engineer actually runs against a live incident, analogous to how `sendevent` commands
  showed up in AutoSys runbooks.
- Keep `astro` CLI actions in CI/CD pipeline definitions and local-dev documentation, not
  incident runbooks — provisioning/deploy actions are rarely what an on-call engineer needs
  mid-incident, the same way standing up a new AutoSys instance was never an incident-response step.

## Sources

- [P1] Project-internal — `skills/autosys-reference/reference/commands.md` (`autorep`/`sendevent` AutoSys-side reference, page-cited against the ingested AutoSys 12.0 PDF)
- NEEDS_EXEC_CHECK — current `airflowctl` and `astro` CLI command surfaces; not independently re-verified against live documentation this session.
