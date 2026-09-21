---
name: migrate-topology-onprem-distributed
description: Guide for migrating a distributed on-prem AutoSys agent fleet (many Unix/Windows machines) to Astro Cloud (Hosted) and/or Astro Hybrid. Use when the estate's `machine:` definitions span dozens to thousands of on-prem hosts and the question is where jobs execute after migration, not just how job definitions translate. Covers agent-fleet inventory, execution-topology decisions (hosted/hybrid/bridge), secrets and identity migration, networking/firewall changes, capacity sizing, and wave-based cutover. Requires `estate_manifest.json` from `assess-estate-inventory` (job semantics must already be inventoried) and, ideally, `manifest.architecture` from `assess-astro-target-architecture`; load those first, this skill second. Always load reference/execution-topology-mapping.md before recommending a target for any machine group.
hooks:
  PostToolUse:
    - matcher: "Edit"
      hooks:
        - type: command
          command: "echo 'Topology plan edited: consider re-running python3 -m autosys_jil.status --manifest topology_manifest.json summary --workflow topology'"
---

# On-prem distributed AutoSys → Astro Cloud/Hybrid

Migrate the *execution environment* for a distributed AutoSys agent fleet — potentially hundreds or thousands of on-prem Unix/Windows machines — to Astro. This skill assumes `assess-estate-inventory` has already produced `estate_manifest.json` (every job parsed, condition strings resolved, box tree built); this skill's job is the platform layer that manifest doesn't cover: where does each job's replacement task actually *run*, and what does it need reachable from there.

The central decision, made per machine group rather than once for the whole estate: **Astro Cloud (Hosted)**, **Astro Hybrid**, or — for the minority that genuinely cannot move yet — a **bridge** to a shrinking on-prem residual fleet. Most real estates end up mixed, not uniform. `assess-astro-target-architecture`'s `recommend_architecture.py` already proposes a deployment model from estate-wide signals; this skill validates and refines that per machine group, and is the one that actually plans the cutover.

## Requirements

- `estate_manifest.json` from `assess-estate-inventory` (this skill reads it, does not regenerate it). `agent_fleet_inventory.py` reads `Machine.opsys`/`type`/`max_load`/`factor` directly from it when the JIL export included `insert_machine` blocks, and falls back to a command-text OS heuristic when it didn't.
- Optionally, a platform-supplied registry CSV (`--machines-csv`) for facts JIL cannot provide at all (agent version, IP/hostname, install notes) — see `reference/agent-fleet-inventory.md` and the discovery skill's `what-jil-cannot-tell-you.md`. Not required; the manifest alone is enough to start.
- Network topology knowledge (or a contact who has it): what each machine group needs to reach (databases, file shares, MQ, mainframe gateways, internal APIs) and from where Astro Hosted workers vs. an Astro Hybrid node would sit relative to that.

## Hard rules

1. **Never claim reachability without testing it.** "Should be fine" is not a validation gate. A network path is `verified-reachable` only after an actual connection attempt from the actual target execution environment succeeds.
2. **No silent omissions.** Every machine group ends `complete` or `deferred (reason)` in the topology manifest, same discipline as `migrate-jil-to-airflow-translation`.
3. **Recommend, don't auto-decide.** `scripts/agent_fleet_inventory.py` never assigns a final Hosted/Hybrid/Bridge disposition — it produces heuristic hints for a human/agent judgment call, because that decision depends on compliance, data locality, and cost tradeoffs no script can see.
4. **Capacity numbers come from observed data, not job counts.** Sizing a worker pool or node group from "how many jobs reference this machine" ignores concurrency. Pull actual overlap data (`autorep` history, job start/end timestamps) before finalizing a pool size; a job-count-based estimate gets labeled a floor, never a final number.
5. **Bridge is a documented exception, not a default.** Every job left on a bridge (SSHOperator/WinRM-style call into a residual on-prem host) needs a written reason it can't containerize or run under Hybrid, plus a target date or trigger condition for revisiting that decision.

## Workflow

### Phase 1: Fleet inventory

```
python3 scripts/agent_fleet_inventory.py --manifest estate_manifest.json --out topology_manifest.json
python3 scripts/agent_fleet_inventory.py --manifest estate_manifest.json --machines-csv registry.csv --out topology_manifest.json
```

Derives, per machine group: job count, job names, boxes touched, job-type mix, OS (from `Machine.opsys` when the JIL export defined the machine [AS p.2873], else a command-text heuristic, else the registry CSV if given), agent plugin capabilities (from `agentparm.txt` data if present in the manifest), environment-coupling signals (hardcoded hosts, absolute paths, UNC paths, mapped drives — inputs to the containerization-effort conversation), credential-hit counts (never values), FTP/SCP/FT/FW transfer-partner hints, and cross-machine condition edges. Machine groups present only in a supplied registry CSV (no jobs in this manifest slice) are reported separately — they may be decommissioned, or simply outside this export's scope.

### Phase 2: Classify each machine group

Per `reference/execution-topology-mapping.md`'s decision tree, assign each machine group one of: containerizable-Hosted, network-bound-Hybrid, or bridge-only. Cross-check against `assess-astro-target-architecture`'s estate-wide deployment-model recommendation (if available) rather than deciding from a blank slate. Record the reasoning, not just the label — the report needs it later.

### Phase 3: Plan

- **Secrets and identity**: `astro-platform-buildout/reference/identity-and-rbac.md` and `.../secrets-and-identity.md` — map AutoSys credential handling (OS-level service accounts, CA credential vault, or external CyberArk/vault integration) to Airflow Connections + a secrets backend, and WCC/LDAP-driven human permissions to Astro RBAC/SSO. `reference/secrets-and-identity.md` here is a thin pointer to that skill.
- **Networking**: `reference/networking.md` — firewall/egress rules, VPN/PrivateLink, Hosted vs. Hybrid network posture per machine group.
- **Capacity**: `reference/capacity-and-scaling.md` points to `assess-astro-target-architecture/scripts/size_target.py` (`worker_fleet()`) — worker pool / node group sizing per machine group, from real concurrency data (`estate.history.concurrency_curve`, not job counts).
- **Cutover waves**: `reference/cutover-waves.md` points to `assess-migration-complexity-scoring/reference/wave-planning.md` and `migrate-parallel-run-and-cutover/reference/cutover-runbook.md` — group machines into waves by team/business-calendar/risk, not all at once.

### Phase 4: Trial

Pilot one machine group end-to-end: containerize (or Hybrid-provision) its jobs, prove network reachability from the new location for every downstream system that group's jobs touch, run one full job through `migrate-parallel-run-and-cutover`'s parity gate *from the new location specifically* (this catches environment-specific failures — a missing local driver, a mapped drive, a locale/timezone difference — that inventory alone won't surface).

### Phase 5: Migrate wave by wave

Per machine group, the state machine (`_lib.autosys_jil.status`, `topology` workflow, tracked in `topology_manifest.json`):

```
pending → assessed → planned → piloted → migrating → cutover → complete
                                                     ↘ deferred (reason required)
```

Advance with `python3 -m autosys_jil.status --manifest topology_manifest.json advance <machine> --workflow topology --status <state> --note ...`. Validate per `reference/validation.md` before advancing past `piloted`.

### Phase 6: Final report

`python3 -m autosys_jil.status --manifest topology_manifest.json summary --workflow topology` must pass (exit 0). The report: topology disposition per machine group with rationale, secrets/identity map, network changes made (firewall rules opened, by whom, when), capacity numbers with their data source, waves completed with dates, and every bridge-only exception with its written reason and revisit trigger.

## Reference routing

| Question | Read |
|---|---|
| What does this machine group actually need, and what's its job load? | `reference/agent-fleet-inventory.md` |
| Hosted, Hybrid, or bridge? | `reference/execution-topology-mapping.md` |
| Credentials, service accounts, human RBAC | `reference/secrets-and-identity.md` |
| Firewall rules, VPN/PrivateLink, network posture | `reference/networking.md` |
| Worker pool / node group sizing | `reference/capacity-and-scaling.md` |
| How to group and sequence cutover waves | `reference/cutover-waves.md` |
| Reachability and environment-parity checks | `reference/validation.md` |
| Failure classes seen before | `reference/troubleshooting.md` |

## Scripts

| Script | Purpose |
|---|---|
| `scripts/agent_fleet_inventory.py` | Derive a per-machine-group topology worksheet from `estate_manifest.json` (+ optional registry CSV) |
| `_lib.autosys_jil.status` (`--workflow topology`) | Per-machine-group state machine + completeness gate over `topology_manifest.json`; replaces the old per-skill `scripts/status.py` |
