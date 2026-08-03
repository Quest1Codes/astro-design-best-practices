---
name: migrating-autosys-onprem-distributed-to-astro-cloud
description: Guide for migrating a distributed on-prem AutoSys agent fleet (many Unix/Windows machines) to Astro Cloud (Hosted) and/or Astro Hybrid. Use when the estate's `machine:` definitions span dozens to thousands of on-prem hosts and the question is where jobs execute after migration, not just how job definitions translate. Covers agent-fleet inventory, execution-topology decisions (hosted/hybrid/bridge), secrets and identity migration, networking/firewall changes, capacity sizing, and wave-based cutover. Requires manifest.json from the migrating-autosys-to-astronomer skill (job semantics must already be inventoried); load that skill first, this one second. Always load reference/execution-topology-mapping.md before recommending a target for any machine group.
hooks:
  PostToolUse:
    - matcher: "Edit"
      hooks:
        - type: command
          command: "echo 'Topology plan edited: consider re-running python3 scripts/status.py summary against topology_manifest.json'"
---

# On-prem distributed AutoSys → Astro Cloud/Hybrid

Migrate the *execution environment* for a distributed AutoSys agent fleet — potentially hundreds or thousands of on-prem Unix/Windows machines — to Astro. This skill assumes `migrating-autosys-to-astronomer` has already produced `manifest.json` (every job classified, condition strings resolved, DAG boundaries planned); this skill's job is the platform layer that manifest doesn't cover: where does each job's replacement task actually *run*, and what does it need reachable from there.

The central decision, made per machine group rather than once for the whole estate: **Astro Cloud (Hosted)**, **Astro Hybrid**, or — for the minority that genuinely cannot move yet — a **bridge** to a shrinking on-prem residual fleet. Most real estates end up mixed, not uniform.

## Requirements

- `manifest.json` from `migrating-autosys-to-astronomer` (this skill reads it, does not regenerate it).
- The AutoSys machine/agent registry. There is no single standard textual export for this (unlike JIL for jobs) — it typically has to come from the platform team as a CSV or spreadsheet: machine name, OS, agent version, hostname/IP, and any notes on what's locally installed. Ask for this explicitly; do not assume it can be derived from JIL alone (JIL only tells you which machine name each job references, not what that machine actually provides).
- Network topology knowledge (or a contact who has it): what each machine group needs to reach (databases, file shares, MQ, mainframe gateways, internal APIs) and from where Astro Hosted workers vs. an Astro Hybrid node would sit relative to that.

## Hard rules

1. **Never claim reachability without testing it.** "Should be fine" is not a validation gate. A network path is `verified-reachable` only after an actual connection attempt from the actual target execution environment succeeds.
2. **No silent omissions.** Every machine group ends `complete` or `deferred (reason)` in the topology manifest, same discipline as the core skill.
3. **Recommend, don't auto-decide.** `scripts/agent_fleet_inventory.py` never assigns a final Hosted/Hybrid/Bridge disposition — it produces heuristic hints for a human/agent judgment call, because that decision depends on compliance, data locality, and cost tradeoffs no script can see.
4. **Capacity numbers come from observed data, not job counts.** Sizing a worker pool or node group from "how many jobs reference this machine" ignores concurrency. Pull actual overlap data (`autorep` history, job start/end timestamps) before finalizing a pool size; a job-count-based estimate gets labeled a floor, never a final number.
5. **Bridge is a documented exception, not a default.** Every job left on a bridge (SSHOperator/WinRM-style call into a residual on-prem host) needs a written reason it can't containerize or run under Hybrid, plus a target date or trigger condition for revisiting that decision.

## Workflow

### Phase 1: Fleet inventory

```
python3 scripts/agent_fleet_inventory.py --manifest manifest.json --out topology_manifest.json
python3 scripts/agent_fleet_inventory.py --manifest manifest.json --machines-csv registry.csv --out topology_manifest.json
```

Derives, per machine referenced in `manifest.json`: job count, job names, boxes touched, an OS heuristic from command syntax (`.exe`/`.bat`/`.ps1`/backslash paths → Windows hint; `.sh`/shebang-style → Unix hint — heuristics only, confirm against the registry CSV when available), and flags (FT-job cross-machine transfer partners, jobs carrying unverified `raw_extra` attributes, condition strings that cross machine boundaries). Merges the platform-supplied registry CSV by machine name when given; unmatched CSV rows (registered machines with no jobs in this manifest slice) are reported separately — they may be decommissioned, or simply outside this export's scope.

### Phase 2: Classify each machine group

Per `reference/execution-topology-mapping.md`'s decision tree, assign each machine group one of: containerizable-Hosted, network-bound-Hybrid, or bridge-only. Record the reasoning, not just the label — the report needs it later.

### Phase 3: Plan

- **Secrets and identity**: `reference/secrets-and-identity.md` — map AutoSys credential handling (OS-level service accounts, CA credential vault, or external CyberArk/vault integration) to Airflow Connections + a secrets backend, and WCC/LDAP-driven human permissions to Astro RBAC/SSO.
- **Networking**: `reference/networking.md` — firewall/egress rules, VPN/PrivateLink, Hosted vs. Hybrid network posture per machine group.
- **Capacity**: `reference/capacity-and-scaling.md` — worker pool / node group sizing per machine group, from real concurrency data.
- **Cutover waves**: `reference/cutover-waves.md` — group machines into waves by team/business-calendar/risk, not all at once.

### Phase 4: Trial

Pilot one machine group end-to-end: containerize (or Hybrid-provision) its jobs, prove network reachability from the new location for every downstream system that group's jobs touch, run one full job through the core skill's output-parity gate *from the new location specifically* (this catches environment-specific failures — a missing local driver, a mapped drive, a locale/timezone difference — that inventory alone won't surface).

### Phase 5: Migrate wave by wave

Per machine group, the state machine (tracked in `topology_manifest.json`):

```
pending → assessed → planned → piloted → migrating → cutover → complete
                                                     ↘ deferred (reason required)
```

Advance with `scripts/status.py advance <machine> --status <state> --note ...`. Validate per `reference/validation.md` before advancing past `piloted`.

### Phase 6: Final report

`scripts/status.py summary` must pass. The report: topology disposition per machine group with rationale, secrets/identity map, network changes made (firewall rules opened, by whom, when), capacity numbers with their data source, waves completed with dates, and every bridge-only exception with its written reason and revisit trigger.

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
| `scripts/agent_fleet_inventory.py` | Derive a per-machine topology worksheet from `manifest.json` (+ optional registry CSV) |
| `scripts/status.py` | Per-machine-group state machine + completeness gate over `topology_manifest.json` |
