---
name: assess-estate-inventory
description: Second phase of an AutoSys estate assessment — parses every collected artifact into one typed `estate_manifest.json`, then enriches it with histograms, a dependency graph, schedule expansion, command-payload analysis, and run-history stats. Use once assess-estate-discovery has validated the artifacts. Everything here is deterministic Python over _lib.autosys_jil; judgment (interpreting what the numbers mean) is reference/reading-the-inventory.md, not this skill's scripts.
---

# Estate inventory

Turn validated discovery artifacts into one manifest, then compute everything that's a fixed
function of that manifest — histograms, the dependency graph, schedule expansion,
command-payload analysis, run-history stats. Every script here is deterministic: given the same
inputs, byte-identical output. Interpretation of what a number *means* is a separate, explicit
step (`reference/reading-the-inventory.md`), not baked into any script.

## Requirements

- `_lib.autosys_jil` installed.
- Validated artifacts from `assess-estate-discovery` (`evidence.json`), and, ideally,
  `answers.yaml` from its stakeholder questionnaire.

## Workflow

### Phase 1: Build the manifest

```
python3 scripts/build_estate_manifest.py \
  --instance ACE=jobs.jil --instance ACE=machines.jil \
  --autocal ACE=calendars_export.txt --globals ACE=globals.txt \
  --config ACE=config.ACE --agentparm ACE=agentparm.txt \
  --evidence evidence.json --nfr answers.yaml \
  --out estate_manifest.json --strict
```

Repeat `--instance ID=path` for every file, in the order they should be applied (JIL
`update_job`/`override_job` semantics are order-sensitive). `--strict` exits nonzero if any
unknown job type/attribute or referential-integrity problem exists — see
`reference/unknowns-and-escalation.md` before deciding whether to proceed anyway.

### Phase 2: Enrich

Run in any order (each reads and re-writes the same manifest file):

```
python3 scripts/inventory_stats.py    --manifest estate_manifest.json --md stats.md
python3 scripts/condition_graph.py    --manifest estate_manifest.json --dot graph.dot
python3 scripts/calendar_expand.py    --manifest estate_manifest.json --from 2026-01-01 --to 2028-12-31
python3 scripts/command_analysis.py   --manifest estate_manifest.json --scripts-out scripts_to_fetch.txt
python3 scripts/history_stats.py      --manifest estate_manifest.json --history runs.csv --events events.csv
```

`history_stats.py` needs run-history/event-archive artifacts, which are optional in discovery —
skip it if they weren't collected, and say so explicitly in the eventual report (dead-job
detection and manual-intervention frequency simply aren't available without it).

### Phase 3: Read and interpret

Work through `reference/reading-the-inventory.md` for every generated table: what a healthy
estate looks like there, what a red flag looks like, what to write into `manifest.notes.inventory`
(a free-text field — this is the one place in this skill where judgment goes into the manifest
directly, clearly separated from the generated `stats{}`/`graph{}`/etc. sections).

### Phase 4: Resolve or escalate unknowns

Per `reference/unknowns-and-escalation.md`: every unknown job type, unknown attribute, condition
parse failure, and unresolved reference gets either resolved (a custom `insert_job_type`, a stale
export, a genuinely undefined job) or explicitly escalated back to discovery — never silently
dropped.

### Phase 5: Gate

`python3 -m autosys_jil.status --manifest estate_manifest.json summary --workflow assessment`
should read `parsed` once this phase is done.

## Reference routing

| Question | Read |
|---|---|
| What's in the manifest, field by field, and which script fills it | `reference/manifest-schema.md` |
| What a healthy vs. concerning number looks like | `reference/reading-the-inventory.md` |
| How to resolve an unknown job type/attribute/condition failure | `reference/unknowns-and-escalation.md` |

## Scripts

| Script | Purpose |
|---|---|
| `scripts/build_estate_manifest.py` | Parse every artifact into `estate_manifest.json` |
| `scripts/inventory_stats.py` | Job-type/attribute/machine/owner histograms, box-metric distribution, load pressure |
| `scripts/condition_graph.py` | Dependency graph: cycles, SCCs, longest chain, fan-in/out, hidden control-flow edges |
| `scripts/calendar_expand.py` | Concrete run instants per scheduled job, cron-expressibility, DST flags |
| `scripts/command_analysis.py` | Interpreter/OS detection, hidden control flow, credential exposure counts, template clustering |
| `scripts/history_stats.py` | Duration/failure/retry stats, concurrency curve, dead-job detection, manual-intervention frequency, SLA breaches |
