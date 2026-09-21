---
topic: autorep-and-export-commands
family: assessment
skill: assess-estate-discovery
verified_against:
  autosys: "12.0"
  autosys_doc_pages: [2307, 2353, 2439]
last_verified: 2026-09-17
confidence: cited
signals: []
---

# Export recipe

Copy-paste blocks for the customer's platform team to run. Full flag reference:
`autosys-reference/reference/commands.md`.

## JIL job export

```bash
# Full estate, quiet mode (no truncation):
autorep -J ALL -q > estate.jil

# A very large estate: chunk by prefix and concatenate, or by application/group:
autorep -J 'FIN%' -q  > estate_fin.jil
autorep -J 'RISK%' -q > estate_risk.jil
cat estate_fin.jil estate_risk.jil > estate.jil
```

Pitfalls:

- `-q` is required for full, non-truncated object names — without it, long job/machine names
  get cut off and `build_estate_manifest.py` will mis-key them.
- This is the **report form** of `autorep`, not a JIL re-export — it's what
  `_lib.autosys_jil.parser` is built to read (the same shape as `insert_job:`-style JIL). If the
  customer instead has a maintained JIL source file (many shops keep JIL under version control),
  that file is just as good an input and skips this step entirely — ask first.
- Windows quoting for prefix wildcards differs from UNIX shells; confirm the actual command that
  ran (some Windows shells eat the `%` wildcard) before treating a suspiciously small export as
  complete.
- Multi-instance estates need `-S <instance>` per instance, or run against each `$AUTOSERV`
  separately.

## Machine, global-variable, resource, external-instance exports

```bash
autorep -M ALL -q > machines.txt
autorep -G ALL     > globals.txt
autorep -R ALL     > resources.txt
autorep -X ALL     > xinsts.txt
```

## Calendars

```bash
autocal_asc -l                                   # list only (names/types/descriptions)
autocal_asc -E calendars_export.txt -c ALL        # export standard-calendar dates
autocal_asc -E calendars_export_ext.txt -e ALL    # export extended-calendar dates
```

Default date format is `MM/DD/YYYY`; add `-f date_format` to change it. Extended calendars can't
be *regenerated* from the command line (their generating criteria require the interactive
utility) — an export still gives the current fixed-date list, which is what `calendar_expand.py`
needs.

## Run history and event archive

```bash
# Quick-and-dirty, from the CLI (fixed-width text, best-effort parse):
autorep -J ALL -r -N > run_history.txt

# Better: ask the DBA for a direct export of the tables archive_events would otherwise purge:
#   ujo_job_runs        -> history CSV
#   ujo_event / ujo_proc_event -> event archive CSV
# Column names vary by DBA export -- assess-estate-inventory's history_stats.py takes a
# --columns map.yaml to handle that. Ask for column headers up front so the map can be built
# before the file arrives, not after.
```

`autorep`'s text-report columns are **fixed-width per invocation**, not delimited by runs of
whitespace — `_lib.autosys_jil.history` parses this correctly, but a hand-edited or
re-pasted copy of this output can silently break the column alignment. Prefer the DBA CSV path
whenever it's available.

## Platform config

```bash
# Per instance, copy the file directly (no command needed):
cat "$AUTOUSER/config.$AUTOSERV"

# Per distinct agent configuration (not per machine -- one representative copy per class):
cat installation_directory/SystemAgent/<agent_name>/agentparm.txt
```

## Security (native mode only)

If `reference/what-jil-cannot-tell-you.md`'s question about security mode comes back "native,"
skip `safex` — there's no EEM policy to export. If external (CA EEM, the default), see
`autosys-reference/reference/security-eem-and-native.md`'s `as_safetool`/`safex` procedure; that
export can only be run from the machine hosting the CA EEM back-end, and writes to `stderr` —
capture it to a file.

## Packaging and hashing before sending

Whatever arrives, record a SHA-256 immediately (`validate_artifacts.py` does this automatically
once files are in the received directory) — this is what makes the eventual report's evidence
appendix reproducible and tamper-evident (plan §11.6), and it's the cheapest way to confirm two
people didn't accidentally send two different versions of "the same" export.
