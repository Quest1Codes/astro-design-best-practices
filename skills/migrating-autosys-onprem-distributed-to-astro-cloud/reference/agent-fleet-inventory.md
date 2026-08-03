# Agent fleet inventory

## Why this needs its own inventory pass

The core skill's `manifest.json` records a `machine:` value per job because that's what JIL carries — a name. It does not (and cannot) tell you what that machine actually *provides*: installed local software the job's script assumes is present, mapped network drives, a specific ODBC driver version, a service account's Kerberos/domain membership, locale/timezone configuration baked into the OS image, or firewall rules already open from that specific host. All of that has to be gathered separately, from the platform team or the machine itself, before deciding where a job's replacement task can run.

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

The script's `os_guess` and `flags` fields exist to focus attention, not to be copied into the plan verbatim. In particular:

- `os_guess_confidence: "heuristic"` means it was inferred from command syntax (backslashes, `.exe`/`.bat`/`.ps1` vs. `.sh`/forward-slashes) — always confirm against the registry CSV or the platform team when a machine group is heading toward a real Hosted/Hybrid decision.
- `ft_partner_machine` flags mean a file-transfer job's counterpart machine needs its own network path considered jointly — moving one side of an FT pair without planning the other is a common source of post-cutover breakage.
- `raw_extra` flags (carried over from the core skill's manifest) mean the job has attributes the core skill's inventory didn't recognize — often FT-specific — and those frequently encode machine-to-machine specifics (transfer protocol, port) relevant to this skill's networking plan too.

## Grouping machines for planning

Group machines by what they have in common, not just by name — jobs that share a database, a file share, or a business calendar are natural migration-wave candidates (see `reference/cutover-waves.md`), even if they're superficially different machines. A single machine used by only one job is a different planning unit than a shared "etl-prod-01"-style host serving many teams' jobs; call out shared machines explicitly since they can't move on one team's timeline alone.
