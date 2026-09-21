---
name: assess-astro-target-architecture
description: Fourth phase of an AutoSys estate assessment — recommends a target Astro architecture (deployment model, executor, queues, sizing, consumption estimate) from the scored estate manifest, with every recommendation traceable to manifest fields and (where possible) a KB topic. Use once assess-migration-complexity-scoring has produced manifest.scores. Confidence on Astro-side claims is mixed by default in this refactor (no Astronomer MCP access when this skill was authored) — re-verify before presenting to a customer as settled fact.
---

# Astro target architecture

Turn the scored estate manifest into a concrete target-platform recommendation: deployment
model, executor, worker queues, sizing, and a labeled consumption estimate. Every decision row
names the manifest fields and (when one exists) the KB topic that justify it; every sizing number
states whether it's `observed` (from real `max_load`/`job_load`/history data) or `floor`
(job-count-only, a lower bound that must be labeled as such, never presented as final).

## Requirements

- `estate_manifest.json` with `scores{}` populated (`assess-migration-complexity-scoring`).
- If brownfield (existing Astro/Airflow footprint): customer-collected `astro` CLI exports and,
  ideally, read access to the existing DAG repo.

## Workflow

### Phase 1: Brownfield check (if applicable)

```
python3 scripts/astro_inventory.py --manifest estate_manifest.json --deployments deployments.json --workspaces workspaces.json
python3 scripts/dag_conventions_scan.py --manifest estate_manifest.json --dags-dir ./existing-dags
```

Skip this phase entirely for a greenfield engagement (`nfr.brownfield_astro` unset or false).

### Phase 2: Recommend architecture

```
python3 scripts/recommend_architecture.py --manifest estate_manifest.json
```

Evaluates `scripts/decision-tables.yaml` against the manifest, writing
`manifest.architecture.decisions{}` (one row per decision: `choice`, `confidence`, `reason`,
`kb_topics[]`) and `manifest.architecture.kb_routing[]` (the union of every decision's KB topics
— a starting reading list, not the full `kb-routing.md` signal table, which needs Phase 2 of the
refactor's KB front-matter pass to exist).

### Phase 3: Size the target

```
python3 scripts/size_target.py --manifest estate_manifest.json
python3 scripts/estimate_cost.py --manifest estate_manifest.json
```

Writes `manifest.architecture.sizing{}` (pool slots, worker fleet, scheduler/DAG-processor/
triggerer size, metadata-DB tier) and `manifest.architecture.cost_estimate{}` (explicitly labeled
an estimate — `pricing_dimensions.yaml` ships with placeholder figures, replace with real,
dated Astronomer pricing before this goes in front of a customer).

### Phase 4: Review and override

Per `reference/decision-tables.md`: review each recommendation row against
`reference/sizing-methodology.md`'s worked examples and override where judgment differs —
`recommend_architecture.py --override <id>=<choice> --reason "..."` records the override
auditable, never a silent edit.

### Phase 5: Confirm KB routing

Per `reference/kb-routing.md`: confirm the routed topic list actually covers what this estate
needs, adding any signal-specific topic the generic decision table missed.

### Gate

`python3 -m autosys_jil.status --manifest estate_manifest.json summary --workflow assessment`
should read `architected` once this phase is done.

## Reference routing

| Question | Read |
|---|---|
| Every decision, its inputs, and the KB topic that justifies it | `reference/decision-tables.md` |
| The sizing formulas with worked examples | `reference/sizing-methodology.md` |
| Signal → KB topic list | `reference/kb-routing.md` |

## Scripts

| Script | Purpose |
|---|---|
| `scripts/decision-tables.yaml` | Machine-readable decision rules — first match wins per decision |
| `scripts/recommend_architecture.py` | Evaluates the decision tables; supports `--override` |
| `scripts/size_target.py` | `pool_slots`, `worker_fleet`, `scheduler_size`, `dag_processor_size`, `triggerer_size`, `db_tier` |
| `scripts/estimate_cost.py` | Labeled consumption-range estimate (never a license-cost comparison unless `nfr.autosys_license_cost` is supplied) |
| `scripts/astro_inventory.py` | Parses customer-collected `astro` CLI exports (brownfield) |
| `scripts/dag_conventions_scan.py` | AST-scans an existing DAG repo for naming/tagging/default_args conventions (brownfield) |
