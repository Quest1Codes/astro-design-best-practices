# migrate-topology-onprem-distributed

A companion to the `migrate-jil-to-airflow-translation` skill (and the `assess-*` family that
feeds it) for estates where the hard part isn't the job DSL, it's the fleet: dozens to thousands
of on-prem Unix/Windows machines running AutoSys agents. This skill decides, machine group by
machine group, whether jobs move to Astro Cloud (Hosted), need Astro Hybrid, or have to stay
bridged to a shrinking on-prem residual fleet for now — and carries that decision through
secrets, networking, capacity, and a wave-based cutover.

## Why this is separate

Job translation (JIL → DAG code) works the same way regardless of where a job runs. But *where
it runs* is a genuinely different problem with its own failure modes — network reachability,
credential propagation, OS-specific dependencies, capacity planning — that don't fit naturally
into a job-by-job translation workflow. This skill picks up right where `assess-estate-inventory`'s
`estate_manifest.json` leaves off.

## How it works

1. **Inventory the fleet**: [`scripts/agent_fleet_inventory.py`](scripts/agent_fleet_inventory.py) reads `estate_manifest.json` and derives per-machine-group job counts, OS (from `Machine.opsys` when available, else a command-text heuristic), agent capabilities, environment-coupling signals, and cross-machine flags — optionally merged with a platform-supplied machine registry CSV (AutoSys has no standard textual export for its machine registry the way JIL covers jobs).
2. **Classify each machine group**: containerizable → Astro Cloud Hosted; network-bound (compliance, data locality, systems only reachable from inside the customer network) → Astro Hybrid; genuinely can't move yet → a documented bridge via a small residual on-prem execution point. [`reference/execution-topology-mapping.md`](reference/execution-topology-mapping.md) has the decision tree.
3. **Plan the platform layer**: secrets/identity (points to `migrate-astro-platform-buildout`), networking ([`reference/networking.md`](reference/networking.md)), capacity (points to `assess-astro-target-architecture`'s `size_target.py`).
4. **Trial one machine group** end to end, proving actual network reachability from the new location, not assumed reachability.
5. **Migrate wave by wave**, tracked by `_lib.autosys_jil.status --workflow topology`, grouped by team/business-calendar/risk rather than all at once ([`reference/cutover-waves.md`](reference/cutover-waves.md)).

## Using it

```bash
claude "Run assess-estate-discovery and assess-estate-inventory on ~/estate.jil, then use migrate-topology-onprem-distributed to plan the execution-topology migration"
```

## What the inventory looks like

```
python3 scripts/agent_fleet_inventory.py --manifest estate_manifest.json --machines-csv registry.csv --out topology_manifest.json
```

produces, per machine group, something like:

```json
{
  "name": "etl01",
  "job_count": 3,
  "jobs": ["extract_orders", "load_orders", "transfer_report"],
  "os_guess": "unix",
  "os_guess_confidence": "command-heuristic",
  "flags": ["job 'transfer_report' (FTP) references host 'reporting02' in its command -- likely transfer partner; confirm network path"],
  "recommended_target": "needs-review",
  "classification": "pending"
}
```

Note `recommended_target` is always `needs-review` out of the box — the script surfaces evidence, it does not make the Hosted/Hybrid/bridge call, since that depends on compliance and cost tradeoffs no script can see.

## Status

Rewritten onto `_lib.autosys_jil` (2026-09-17): `agent_fleet_inventory.py` now reads the shared
Estate manifest instead of the old skill-local `jil_inventory.py` output, and per-machine-group
state tracking moved to `_lib.autosys_jil.status --workflow topology`. The OS-guessing heuristic
(command-text signals when `Machine.opsys` isn't in the export) is meant to focus human review,
not replace it — confirm every flag against the platform team's actual knowledge of the fleet
before finalizing a topology decision.
