---
topic: artifact-checklist
family: assessment
skill: assess-estate-discovery
verified_against:
  autosys: "12.0"
last_verified: 2026-09-17
confidence: cited
signals: []
---

# Discovery artifact checklist

One row per artifact `discovery_checklist.py` tracks. "Required" artifacts block the `collected`
gate if missing without a waiver; "optional" ones don't, but their absence should be named in
the eventual report as a scope limitation.

| Artifact | Required? | Command | Who runs it | Unlocks |
|---|---|---|---|---|
| JIL job export | **Required** | `autorep -J ALL -q` (or an existing scheduled JIL dump) — see `reference/autorep-and-export-commands.md` for chunking on huge estates | Platform team | Everything — this is the primary input to `build_estate_manifest.py` |
| Machine export | **Required** | `autorep -M ALL -q` | Platform team | `Machine.opsys`/`max_load`/`factor`; without it, OS/load are heuristic-only |
| Global variables | Optional | `autorep -G ALL` | Platform team | `VALUE()` condition resolution, `%%VAR%%` cross-reference in `command_analysis.py` |
| Virtual resources | Optional | `autorep -R ALL` | Platform team | Resource-dependency completeness; only relevant if `insert_resource` is used |
| External instances | Optional (**required** if multi-instance) | `autorep -X ALL` per instance | Platform team | Cross-instance (`job^INST`) condition resolution |
| Calendars | **Required** if any job uses `run_calendar`/`exclude_calendar`/`date_conditions` | `autocal_asc -l` or `autocal_asc -E export_file ALL` | Platform team | Calendar-driven schedule expansion (`calendar_expand.py`) — **do not assume `insert_calendar` blocks in the JIL export carry dates**; they usually don't [plan §1.2 defect A8] |
| Run history (90 days) | Optional but strongly recommended | `autorep -J ALL -r -N` or, better, a DBA export of `ujo_job_runs` | Platform team or DBA | `history_stats.py`: duration/failure/retry stats, concurrency curve, dead-job detection |
| Event archive | Optional but strongly recommended | `archive_events` output, or a DBA export of `ujo_event`/`ujo_proc_event` | DBA | Manual-intervention frequency (`FORCE_STARTJOB`/`KILLJOB`/etc. counts) — the single best REDESIGN/HITL signal available |
| `config.$AUTOSERV` | Optional | Copy of the file, per instance | Platform team | `MaxRestartTrys`/`RestartConstant`/`GlobalAutoHold`/etc. — see `autosys-reference/reference/commands.md` and `_lib/autosys_jil/registry/config_params.yaml` |
| `agentparm.txt` (per agent class, not per machine) | Optional | Copy of one representative file per distinct agent configuration | Platform team | Agent plugin capabilities (`config.agent_capabilities()`) — which job-type families an agent can actually run |
| EEM `safex` export | Optional (**required** if native security is in use, per `autosys-reference/reference/security-eem-and-native.md`) | `as_safetool` + `safex` export, per that file's procedure | Security team | `rbac_map.py`'s EEM-policy → Astro-role proposal |
| WCC monitor/report definitions | Optional | Captured as part of the JIL export (`insert_monbro` blocks) — no separate export needed | — | Partial WCC-usage inventory; dashboard *layout* itself is not exportable, see `reference/what-jil-cannot-tell-you.md` |
| AEWS access logs | Optional | Web-server access logs for the AEWS REST endpoint, if retained | Platform/infra team | Finding inbound callers that must be repointed at the Airflow REST API at cutover |
| Script corpus | Optional, second round | The list `command_analysis.py` emits (`--scripts-out scripts_to_fetch.txt`) once inventory has run once | Platform team | Otto/hand-translation both need script bodies, not just the JIL `command:` line referencing them |
| Existing Astro/Airflow inventory (brownfield only) | Optional | `astro deployment list -o json`, `astro deployment inspect -o yaml`, `astro workspace list -o json` — customer-collected, no live call from this skill | Customer's Astro admin | `astro_inventory.py` (in `assess-astro-target-architecture`) |

## Sizing note

On a very large estate, `autorep -J ALL` can be slow or produce an unwieldy file — chunk by
prefix (`autorep -J 'PREFIX%' -q`) or by `application`/`group` and merge; see
`reference/autorep-and-export-commands.md`.
