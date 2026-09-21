---
topic: agent-fleet-inventory
family: migration
skill: migrate-topology-onprem-distributed
verified_against:
  airflow: "3.3.1"
  astro_runtime: "3.3-2"
  autosys: "12.0"
last_verified: 2026-09-17
confidence: mixed
signals: [windows, multi_owner]
---

# Agent fleet inventory

## Why this needs its own inventory pass

`assess-estate-inventory`'s `estate_manifest.json` records a `machine:` value per job because that's what JIL carries — a name. It does not (and cannot) tell you what that machine actually *provides*: installed local software the job's script assumes is present, mapped network drives, a specific ODBC driver version, a service account's Kerberos/domain membership, locale/timezone configuration baked into the OS image, or firewall rules already open from that specific host. All of that has to be gathered separately, from the platform team or the machine itself, before deciding where a job's replacement task can run.

## What to gather, and from where

| Fact needed | Typical source |
|---|---|
| OS and version | Platform team / CMDB; `agent_fleet_inventory.py`'s OS heuristic is a fallback, not a source of truth |
| Agent version | Platform team — matters if any job behavior depends on agent-version-specific features |
| Locally installed software/drivers the job's command depends on | Read the actual script/command, not just its name; a heuristic can flag "this command runs a `.sh` invoking `sqlplus`" but a human confirms Oracle client is actually what's needed and where it comes from in the new environment |
| Mapped drives / local file paths | grep the job's `command` and any config files it reads for local paths (`\\server\share`, `/mnt/...`) — these become either a network mount in the new environment or an S3/blob-storage redesign |
| Service account and its auth model | Platform team — this determines whether a straight Airflow Connection swap works or whether Hybrid (staying inside the domain-joined network) is required |
| What each machine can reach today | Network team / existing firewall rule documentation — this is the baseline the new environment's rules must reproduce or intentionally change |

## Using `agent_fleet_inventory.py`'s output as a start, not an answer

The script's `os_guess`/`os_guess_confidence`/`flags` fields exist to focus attention, not to be
copied into the plan verbatim. In particular:

- `os_guess_confidence: "command-heuristic"` means it was inferred from command-text signals
  (backslashes, `.exe`/`.bat`/`.ps1`/`cmd /c` vs. absolute-unix-path/`.sh`) — always confirm
  against the registry CSV or the platform team when a machine group is heading toward a real
  Hosted/Hybrid decision. `"machine.opsys [AS p.2873]"` means the JIL export itself defined the
  machine with an `opsys` value — trust that one. `"platform registry CSV"` means a
  `--machines-csv` row overrode both.
- A flag reading `job '<name>' (FTP) references host '<host>' in its command` means a
  file-transfer job's counterpart host needs its own network path considered jointly — moving
  one side of a transfer pair without planning the other is a common source of post-cutover
  breakage.
- `cross_machine_condition_edges` (a list of `{from_job, to_job, to_machine}`) surfaces jobs on
  one machine that condition-depend on a job that runs on a different machine — plan the network
  path between the two if they land in different targets.
- `credential_hits` (a count, never a value — see `_lib.autosys_jil.commands`) on a machine group
  is a signal for `migrate-astro-platform-buildout`'s secrets-backend planning, not something to
  resolve here.

## Grouping machines for planning

Group machines by what they have in common, not just by name — jobs that share a database, a file share, or a business calendar are natural migration-wave candidates (see `reference/cutover-waves.md`), even if they're superficially different machines. A single machine used by only one job is a different planning unit than a shared "etl-prod-01"-style host serving many teams' jobs; call out shared machines explicitly since they can't move on one team's timeline alone.
