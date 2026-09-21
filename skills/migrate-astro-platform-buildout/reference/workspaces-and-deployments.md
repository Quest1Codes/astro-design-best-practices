---
topic: workspaces-and-deployments
family: migration
skill: migrate-astro-platform-buildout
verified_against:
  airflow: "3.3.1"
  astro_runtime: "3.3-2"
last_verified: 2026-09-17
confidence: mixed
signals: [multi_instance, multi_owner]
---

# Workspaces and Deployments

Mapping from `manifest.architecture.decisions` to concrete Astro objects.

## Deployment count

One Deployment per (AutoSys instance × environment), as a starting position — an instance
already represents an operationally independent unit
(`autosys-reference/reference/architecture.md`'s instance model), and collapsing multiple
instances into one Deployment loses that isolation without a stated reason. Adjust down only
when `manifest.stats.*_histogram`'s `application`/`group` breakdown shows the instance is
actually one team's workload artificially split, or up when a single instance serves clearly
separable business units that would benefit from independent deploy cadences.

## Workspace layout

Group Deployments into Workspaces by owning team/business unit
(`manifest.stats.owner_histogram`), not by environment — environment (dev/staging/prod) is a
Deployment-count multiplier within a Workspace, not a Workspace boundary itself, unless the
customer's compliance posture (`nfr.compliance`) specifically requires environment-level
Workspace isolation.

## Naming convention

`<team-or-bu>-<instance>-<environment>` is a reasonable default absent an existing convention —
check `dag_conventions_scan.py`'s brownfield findings first if this is an extend, not greenfield,
engagement; match the existing convention rather than introducing a second one.

## Per-environment topology

See `astro-design-best-practices/reference/cicd-and-environment-topology/dev-staging-prod-deployment-topology.md`
for the general pattern this maps onto; this file only covers the AutoSys-side input to that
decision (instance/environment structure), not the Astro-side environment-topology design itself.
