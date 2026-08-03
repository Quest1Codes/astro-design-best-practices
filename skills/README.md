# Skills

## Imported (mentor-authored, unchanged — Task 002)

- `migrating-autosys-to-astronomer/` — the base migration-workflow skill: inventory, estate classification, condition/calendar translation, trial migration, cutover.
- `migrating-autosys-k8s-to-astronomer/` — companion, loaded when the source estate already runs on Kubernetes.
- `migrating-autosys-mainframe-boundary-to-astro/` — companion, loaded when jobs touch mainframe-produced data (MFT/Connect:Direct/JCL submission).
- `migrating-autosys-onprem-distributed-to-astro-cloud/` — companion, loaded for large on-prem Unix/Windows agent fleets moving to Astro Cloud/Hybrid.

These 4 are source-**topology** skills — the axis where the value genuinely changes the migration workflow itself (see `AGENTS.md` Design Principles #2), so each gets its own skill by design, not by accident.

## In progress (this pipeline builds it — Phases 1-3)

- `astro-design-best-practices/` — not yet scaffolded (Task 006). 100 topic files across 13 clusters (scheduler/DAG design, executor/worker architecture, metadata DB, security/multi-tenancy, observability/alerting, CI/CD topology, config/secrets, HA/DR, regulatory/compliance, integration/enterprise mesh, migration execution/coexistence, cost/capacity governance, governance/operating model), organized as `reference/{cluster}/{topic}.md`. Every other axis discussed (deployment model, estate scale, migration temporal strategy, org model, vertical, executor substrate, integration surface) lives as decision tables *inside* these files, per the cluster-level Axis Relevance Matrix in `tasks/README.md` — not as separate skills.

This is the whole scope of this project — building and verifying the 100 files. Consuming them (Shinro's report generation, an MCP server, or anything else) is explicitly out of scope here; see `tasks/README.md`'s "Explicitly out of scope" section.

See `tasks/README.md` for the full 100-topic list and phase-by-phase build order, and `AGENTS.md` for how each reference file gets produced.
