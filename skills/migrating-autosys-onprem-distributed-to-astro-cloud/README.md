# migrating-autosys-onprem-distributed-to-astro-cloud

A companion to `migrating-autosys-to-astronomer` for estates where the hard part isn't the job DSL, it's the fleet: dozens to thousands of on-prem Unix/Windows machines running AutoSys agents. This skill decides, machine group by machine group, whether jobs move to Astro Cloud (Hosted), need Astro Hybrid, or have to stay bridged to a shrinking on-prem residual fleet for now — and carries that decision through secrets, networking, capacity, and a wave-based cutover.

## Why this is separate from the core skill

`migrating-autosys-to-astronomer` handles job semantics (JIL → DAG code) the same way regardless of where a job runs. But *where it runs* is a genuinely different problem with its own failure modes — network reachability, credential propagation, OS-specific dependencies, capacity planning — that don't fit naturally into a job-by-job translation workflow. This skill picks up right where the core skill's manifest leaves off.

## How it works

1. **Inventory the fleet**: [`scripts/agent_fleet_inventory.py`](scripts/agent_fleet_inventory.py) reads the core skill's `manifest.json` and derives per-machine job counts, OS heuristics, and cross-machine flags — optionally merged with a platform-supplied machine registry CSV (AutoSys has no standard textual export for its machine registry the way JIL covers jobs).
2. **Classify each machine group**: containerizable → Astro Cloud Hosted; network-bound (compliance, data locality, systems only reachable from inside the customer network) → Astro Hybrid; genuinely can't move yet → a documented bridge via a small residual on-prem execution point. [`reference/execution-topology-mapping.md`](reference/execution-topology-mapping.md) has the decision tree.
3. **Plan the platform layer**: secrets/identity ([`reference/secrets-and-identity.md`](reference/secrets-and-identity.md)), networking ([`reference/networking.md`](reference/networking.md)), capacity ([`reference/capacity-and-scaling.md`](reference/capacity-and-scaling.md)).
4. **Trial one machine group** end to end, proving actual network reachability from the new location, not assumed reachability.
5. **Migrate wave by wave**, tracked by [`scripts/status.py`](scripts/status.py), grouped by team/business-calendar/risk rather than all at once ([`reference/cutover-waves.md`](reference/cutover-waves.md)).

## Using it

```bash
claude "Use the migrating-autosys-to-astronomer skill on ~/estate.jil, then the migrating-autosys-onprem-distributed-to-astro-cloud skill to plan the execution-topology migration"
```

## What the inventory looks like

```
python3 scripts/agent_fleet_inventory.py --manifest manifest.json --machines-csv registry.csv --out topology_manifest.json
```

produces, per machine, something like:

```json
{
  "name": "etl01",
  "job_count": 3,
  "jobs": ["extract_orders", "load_orders", "transfer_report"],
  "os_guess": "unix",
  "os_guess_confidence": "heuristic",
  "flags": ["ft_partner_machine: reporting02 -- confirm network path"],
  "recommended_target": "needs-review",
  "status": "pending"
}
```

Note `recommended_target` is always `needs-review` out of the box — the script surfaces evidence, it does not make the Hosted/Hybrid/bridge call, since that depends on compliance and cost tradeoffs no script can see.

## Status

First draft. The heuristics in `agent_fleet_inventory.py` (OS guessing from command syntax, cross-machine flagging) are meant to focus human review, not replace it — confirm every flag against the platform team's actual knowledge of the fleet before finalizing a topology decision.
