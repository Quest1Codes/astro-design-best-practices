---
topic: manifest-schema
family: assessment
skill: assess-estate-inventory
verified_against:
  autosys: "12.0"
last_verified: 2026-09-17
confidence: cited
signals: []
---

# Estate Manifest Schema

Generated from `skills/_lib/autosys_jil/models.py` -- the single typed vocabulary every
assessment script reads and writes. "Filled by" names the script that populates a field
(top-level `Estate` enrichment fields only; `Instance`/`Job`/etc. core fields are all filled by
`build_estate_manifest.py`, the JIL parser itself, and are not repeated per row).

<!-- GENERATED: DO NOT EDIT BELOW THIS LINE -->

## `Provenance`

| Field | Type | Filled by |
|---|---|---|
| `file` | `str` |  |
| `line` | `int` |  |
| `block_index` | `int` |  |
| `instance` | `str` |  |
| `subcommand` | `str` |  |

## `Attr`

| Field | Type | Filled by |
|---|---|---|
| `name` | `str` |  |
| `raw` | `str` |  |
| `value` | `Any` |  |
| `known` | `bool` |  |
| `pdf_page` | `int | None` |  |
| `family` | `str | None` |  |
| `warnings` | `list[str]` |  |

## `Schedule`

| Field | Type | Filled by |
|---|---|---|
| `date_conditions` | `bool` |  |
| `days_of_week` | `list[str]` |  |
| `start_times` | `list[str]` |  |
| `start_mins` | `list[int]` |  |
| `run_window` | `tuple[str, str] | None` |  |
| `run_calendar` | `str | None` |  |
| `exclude_calendar` | `str | None` |  |
| `timezone` | `str | None` |  |
| `must_start_times` | `list[str]` |  |
| `must_complete_times` | `list[str]` |  |

## `SLA`

| Field | Type | Filled by |
|---|---|---|
| `term_run_time` | `int | None` |  |
| `max_run_alarm` | `int | None` |  |
| `min_run_alarm` | `int | None` |  |
| `n_retrys` | `int | None` |  |
| `max_exit_success` | `int | None` |  |
| `success_codes` | `list[int]` |  |

## `Load`

| Field | Type | Filled by |
|---|---|---|
| `job_load` | `int | None` |  |
| `priority` | `int | None` |  |
| `resources` | `list[dict[str, Any]]` |  |
| `machine` | `list[str]` |  |

## `Alerting`

| Field | Type | Filled by |
|---|---|---|
| `alarm_if_fail` | `bool | None` |  |
| `alarm_if_terminated` | `bool | None` |  |
| `alarm_if_success` | `bool | None` |  |
| `send_notification` | `bool | None` |  |
| `notification_emails` | `list[str]` |  |
| `notification_msg` | `str | None` |  |
| `svcdesk` | `dict[str, str]` |  |

## `IO`

| Field | Type | Filled by |
|---|---|---|
| `std_in_file` | `str | None` |  |
| `std_out_file` | `str | None` |  |
| `std_err_file` | `str | None` |  |
| `profile` | `str | None` |  |
| `envvar` | `list[str]` |  |

## `Job`

| Field | Type | Filled by |
|---|---|---|
| `name` | `str` |  |
| `job_type` | `str` |  |
| `job_type_known` | `bool` |  |
| `attrs` | `dict[str, Attr]` |  |
| `provenance` | `Provenance` |  |
| `box_name` | `str | None` |  |
| `command` | `str | None` |  |
| `owner` | `str | None` |  |
| `application` | `str | None` |  |
| `group` | `str | None` |  |
| `description` | `str | None` |  |
| `condition_raw` | `str | None` |  |
| `condition` | `Any` |  |
| `condition_error` | `str | None` |  |
| `schedule` | `Schedule` |  |
| `sla` | `SLA` |  |
| `load` | `Load` |  |
| `alerting` | `Alerting` |  |
| `io` | `IO` |  |
| `box_terminator` | `bool | None` |  |
| `job_terminator` | `bool | None` |  |
| `box_success` | `str | None` |  |
| `box_failure` | `str | None` |  |
| `auto_hold` | `bool | None` |  |
| `auto_delete` | `int | None` |  |
| `permission` | `list[str]` |  |
| `extras` | `dict[str, str]` |  |
| `modified_by` | `list[Provenance]` |  |
| `deleted` | `bool` |  |
| `warnings` | `list[str]` |  |

## `Box`

| Field | Type | Filled by |
|---|---|---|
| `name` | `str` |  |
| `children` | `list[str]` |  |
| `parent` | `str | None` |  |
| `depth` | `int` |  |
| `inferred` | `bool` |  |

## `Machine`

| Field | Type | Filled by |
|---|---|---|
| `name` | `str` |  |
| `type` | `str | None` |  |
| `opsys` | `str | None` |  |
| `node_name` | `str | None` |  |
| `agent_name` | `str | None` |  |
| `max_load` | `int | None` |  |
| `factor` | `float | None` |  |
| `members` | `list[str]` |  |
| `port` | `int | None` |  |
| `encryption_type` | `str | None` |  |
| `description` | `str | None` |  |
| `extras` | `dict[str, str]` |  |
| `provenance` | `Provenance | None` |  |

## `Resource`

| Field | Type | Filled by |
|---|---|---|
| `name` | `str` |  |
| `res_type` | `str | None` |  |
| `amount` | `int | None` |  |
| `machine` | `str | None` |  |
| `description` | `str | None` |  |
| `provenance` | `Provenance | None` |  |

## `Xinst`

| Field | Type | Filled by |
|---|---|---|
| `name` | `str` |  |
| `xtype` | `str | None` |  |
| `xmachine` | `str | None` |  |
| `xport` | `int | None` |  |
| `xcrypt_type` | `str | None` |  |
| `xmanager` | `str | None` |  |
| `provenance` | `Provenance | None` |  |

## `Calendar`

| Field | Type | Filled by |
|---|---|---|
| `name` | `str` |  |
| `dates` | `list[date]` |  |
| `source` | `str` |  |
| `provenance` | `Provenance | None` |  |

## `GlobalVar`

| Field | Type | Filled by |
|---|---|---|
| `name` | `str` |  |
| `value` | `str` |  |
| `last_changed` | `str | None` |  |

## `GenericObject`

monbro, connection profile, blob/glob, job_type definition.

| Field | Type | Filled by |
|---|---|---|
| `kind` | `str` |  |
| `name` | `str` |  |
| `attrs` | `dict[str, str]` |  |
| `provenance` | `Provenance | None` |  |

## `Unknowns`

| Field | Type | Filled by |
|---|---|---|
| `job_types` | `dict[str, list[str]]` |  |
| `attributes` | `dict[str, list[str]]` |  |
| `object_kinds` | `dict[str, list[str]]` |  |
| `condition_parse_failures` | `list[dict[str, str]]` |  |
| `unresolved_refs` | `list[dict[str, str]]` |  |

## `Instance`

| Field | Type | Filled by |
|---|---|---|
| `id` | `str` |  |
| `jobs` | `dict[str, Job]` |  |
| `boxes` | `dict[str, Box]` |  |
| `machines` | `dict[str, Machine]` |  |
| `resources` | `dict[str, Resource]` |  |
| `xinsts` | `dict[str, Xinst]` |  |
| `calendars` | `dict[str, Calendar]` |  |
| `globals` | `dict[str, GlobalVar]` |  |
| `objects` | `dict[str, GenericObject]` |  |
| `overrides` | `list[dict[str, Any]]` |  |
| `config` | `dict[str, str]` |  |
| `agent_capabilities` | `dict[str, list[str]]` |  |
| `unknowns` | `Unknowns` |  |
| `warnings` | `list[str]` |  |

## `Evidence`

| Field | Type | Filled by |
|---|---|---|
| `path` | `str` |  |
| `sha256` | `str` |  |
| `kind` | `str` |  |
| `size` | `int` |  |
| `received_at` | `str` |  |

## `Estate`

| Field | Type | Filled by |
|---|---|---|
| `instances` | `dict[str, Instance]` | build_estate_manifest.py |
| `evidence` | `list[Evidence]` | validate_artifacts.py, manifest.add_evidence() |
| `nfr` | `dict[str, Any]` | discovery_checklist.py (from --nfr answers.yaml) |
| `stats` | `dict[str, Any]` | inventory_stats.py |
| `graph` | `dict[str, Any]` | condition_graph.py |
| `schedules` | `dict[str, Any]` | calendar_expand.py |
| `commands` | `dict[str, Any]` | command_analysis.py |
| `command_summary` | `dict[str, Any]` | command_analysis.py |
| `history` | `dict[str, Any]` | history_stats.py |
| `scores` | `dict[str, Any]` | score_estate.py |
| `architecture` | `dict[str, Any]` | recommend_architecture.py, size_target.py, estimate_cost.py |
| `waves` | `list[dict[str, Any]]` | propose_waves.py |
| `brownfield` | `dict[str, Any]` | astro_inventory.py, dag_conventions_scan.py |
| `notes` | `dict[str, Any]` | human-authored (reading-the-inventory.md interpretation) |
| `status` | `dict[str, Any]` | _lib/autosys_jil/status.py |

