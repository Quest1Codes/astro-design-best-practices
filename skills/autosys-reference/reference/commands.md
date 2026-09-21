---
topic: commands
family: knowledge
skill: autosys-reference
verified_against:
  autosys: "12.0"
  autosys_doc_pages: [2239, 2256, 2307, 2313, 2353, 2384, 2393]
last_verified: 2026-09-17
confidence: cited
signals: []
---

# AutoSys 12.0 CLI commands

The **export recipe** — the exact commands `assess-estate-discovery` asks a customer to run —
lives in `assess-estate-discovery/reference/autorep-and-export-commands.md`; this file is the
underlying command reference each of those recipes is built from.

## `autorep` — report job, machine, and variable information [AS p.2353-2366]

| Flag | Report |
|---|---|
| `-J job_name\|ALL` | Job summary report (`Job Name / Last Start / Last End / ST/Ex / Run/Ntry / Pri-Xit`) |
| `-J ... -d` | Detail report: the summary row plus a per-job `Status/[Event]` timeline |
| `-J ... -r N` | Report a specific previous run (relative offset, e.g. `-r -1` = previous run) |
| `-M machine\|ALL` | Machine report (`Machine Name / Max Load / Current Load / Factor / O/S / Status`) |
| `-G global_var\|ALL` | Global variable report |
| `-R resource\|ALL` | Virtual resource report |
| `-X xinst\|ALL` | External instance report |
| `-o` | Override report — shows the current one-time `override_job` in effect, if any |
| `-q` | Quiet: full, non-truncated object names |
| `-s` | Summary status only |
| `-L` | Apply `-L` (nesting) to jobs inside a reported box |
| `-z` | Report on blobs/globs (supports `%`/`*`/`?` wildcards) |

**Output shape is fixed-width per invocation, not whitespace-delimited** — column widths are
sized to the widest value at generation time, confirmed against two real examples with different
widths for the same report type [AS p.2363-2364]. `_lib.autosys_jil.history.parse_autorep_r`/
`parse_autorep_d` derive column offsets from the report's own underscore/dash separator line for
exactly this reason; do not write a new parser against this format using a naive
whitespace-split.

ST column abbreviations and ES (event-state) abbreviations are reproduced in
`reference/job-states-and-events.md` and `_lib.autosys_jil.history.ST_ABBREV`/`ES_ABBREV`.

## `sendevent` — post an event [AS p.2237+, one page per event family]

```
sendevent -E EVENT [-J job_name | -B group [-I application] | -I application]
          [-S autoserv_instance] [-P priority] [-T "time_of_event"] [OPTIONS]
```

The full event catalog lives in `_lib/autosys_jil/registry/events.json`
(`reference/job-states-and-events.md` has the prose table). Grouped by what `sendevent` actually
does:

| Group | Events | Effect |
|---|---|---|
| Start/stop control | `STARTJOB`, `FORCE_STARTJOB`, `KILLJOB`, `RESTARTJOB`, `RESUMEJOB`, `SUSPENDJOB`, `SEND_SIGNAL`, `DELETEJOB`, `CHK_BOX_TERM` | Directly starts/stops/deletes a job — the classic manual-intervention events |
| Hold/ice/noexec | `JOB_ON_HOLD`/`JOB_OFF_HOLD`, `JOB_ON_ICE`/`JOB_OFF_ICE`, `JOB_ON_NOEXEC`/`JOB_OFF_NOEXEC` | See `reference/job-states-and-events.md`'s hold/ice/noexec comparison |
| State/priority | `CHANGE_STATUS`, `CHANGE_PRIORITY`, `REPLY_RESPONSE` (answers a `WAIT_REPLY`), `RESEND_EXTERNAL_STATUS`, `REFRESH_EXTINST` | Mutates job state directly, bypassing the normal event flow |
| Global variables | `SET_GLOBAL` | Sets/deletes a global (feeds `VALUE()` conditions) |
| Machine/resource | `MACH_OFFLINE`, `MACH_ONLINE`, `MACH_UNQUAL_OFFLINE`, `RELEASE_RESOURCE` | Machine/resource state |
| Admin | `COMMENT`, `ALARM`, `STOP_DEMON`, `AGGREGATE`, `REFRESH_BROKER`, `REFRESH_AUTH_HOST` | Logging/admin only — no job-flow effect |

A `sendevent` call embedded inside a job's `command:` string (rather than issued by an operator)
is exactly the "hidden control flow" `_lib.autosys_jil.commands.analyze()` extracts — see
plan §11.2's "#1 source of surprise in migrations."

## `jil` — run the JIL processor [AS p.2313-2314]

```
jil [-q] [-S autoserv_instance] [-V {none|job|session|batch|syntax}]
```

`-V syntax` validates a JIL file without writing anything to the database — useful for a
dry-run sanity check of hand-edited fixtures. `-V` other modes control *when* job-dependency
(condition) references are checked; `session` (checks only jobs submitted in this run) is the
default. Two ways to invoke: pipe a script file in (batch maintenance — this is how a customer
would apply generated JIL) or run interactively.

## `autocal_asc` — manage calendars [AS p.2307-2308]

```
autocal_asc -l [c|e|s]                              # list calendars (this instance's inventory)
autocal_asc -E export_file {-c|-e|-s} {name|ALL}     # export dates for discovery
autocal_asc -D {-c|-e|-s} calendar_name              # delete
autocal_asc -I import_file [-F]                      # import
```

Three calendar kinds: **standard** (fixed date list, e.g. holidays), **cycle** (date-range
periods), **extended** (criteria that generate a fixed-date list; command-line options do not
support *regenerating* an extended calendar after its criteria change — use the interactive
utility for that). Dates default to `MM/DD/YYYY`; `-f date_format` overrides on import/export.
`_lib.autosys_jil.calendars.parse_autocal_asc()` parses `-l`/export-style output.

**Discovery must run `autocal_asc -E ... ALL` (or `-l`), not assume `insert_calendar` blocks in a
JIL export carry calendar dates** — calendars are managed and stored separately from job
definitions [plan §1.2 defect A8].

## `archive_events` — archive/purge run history [AS p.2239-2240]

```
archive_events -A -j num_days [-B batch_size] [-C delimiter] [-d directory_name]
```

Archives (and, with `-A`, also deletes) rows older than `num_days` from `ujo_proc_event`,
`ujo_job_runs`, `ujo_audit_info`, `ujo_chkpnt_rstart`, `ujo_audit_msg`, `ujo_alarm`,
`ujo_event2`, `ujo_extended_jobrun_info` to a flat file (default `$AUTOUSER/archive`, CSV-style,
comma-delimited by default). Runs daily by default via the `DBMaint` maintenance script. **This
is the authoritative source for `_lib.autosys_jil.history.parse_event_archive_csv()` /
`parse_run_history_csv()`** — a DBA-exported archive is a far more reliable input for
`history_stats.py` than reconstructing history from `autorep -r`/`-d` text output (see that
module's docstring). Ask the DBA team for recent `archive_events` output (or direct
`ujo_job_runs`/`ujo_event` table extracts) during discovery, not just JIL.

## `job_depends` — dependency/condition reports [AS p.2393-2394]

```
job_depends -c|-d|-r|-t [-J job_name | -B group] [-F from] [-T to] [-L print_level]
```

`-c`/`-d`/`-r`/`-t` are mutually exclusive: current state + dependents (`-c`), starting
conditions with box nesting (`-d`), virtual-resource dependencies (`-r`), or a scheduled-interval
report (`-t`). Independently cross-checking `_lib.conditions`' parse of a `condition:` string
against a live `job_depends -d` run (where a live system is available) is the most direct way to
validate the condition parser against real AutoSys semantics beyond the PDF's own worked
examples.

## `autosyslog` — display log files [AS p.2256-2261]

```
autosyslog [-e] [-J job_name] [-j job_name] [-r N]
```

Reads scheduler/application-server/agent log files directly (equivalent to reading the
underlying log file path on UNIX). Useful for troubleshooting a specific job's execution
timeline outside the event-archive path.

## `autotrack` — database change history [AS p.2384]

Tracks who changed which object definition and when — the closest AutoSys-native audit trail;
relevant to `security-eem-and-native.md` and any compliance/audit-trail assessment questions.
