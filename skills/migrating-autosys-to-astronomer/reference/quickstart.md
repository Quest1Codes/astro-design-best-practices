# Quickstart

## Hour one

```bash
# 1. Get a JIL export of the estate (or a representative slice to start)
#    From a live AutoSys instance, the platform team typically runs:
#      autorep -j ALL -q > estate.jil     (status/report form)
#      jil (interactive) or a scheduled JIL dump job may already produce a text export
#    Either way, get the export as a starting artifact rather than assuming
#    live instance access.

# 2. Inventory it, read-only
python3 scripts/jil_inventory.py estate.jil --out manifest.json

# 3. Look at what's in it before doing anything else
python3 -c "import json; m=json.load(open('manifest.json')); print(len(m['jobs']), 'jobs,', len(m['boxes']), 'boxes')"

# 4. Check completeness/state at any point
python3 scripts/status.py summary
```

## Glossary

| Term | Meaning |
|---|---|
| JIL | Job Information Language — the text DSL used to define AutoSys jobs/boxes/calendars |
| Box job | A container job; other jobs join it via their own `box_name` attribute (membership is declared bottom-up) |
| Condition | A boolean expression over other jobs' statuses (`s()`, `f()`, `n()`, `d()`) gating when a job is eligible to run |
| Calendar | A named, reusable list of eligible/excluded dates referenced by `run_calendar`/`exclude_calendar` |
| Agent | The AutoSys process installed on a target machine that actually executes jobs and reports status back |
| WCC | Workload Control Center — the web UI for defining, monitoring, and operating AutoSys jobs |
| `autorep` | CLI for reporting job/box status |
| `sendevent` | CLI for sending control events (start, force-start, freeze/thaw, manual status override) |
| ON_ICE / OFF_ICE | Freeze / thaw a job so it won't (or will again) run on schedule — the AutoSys equivalent of pausing |

## What can and cannot break

- **Cannot break during Phases 0-3**: nothing is written back to AutoSys; inventory and planning are read-only against the JIL export.
- **Can break starting Phase 4**: the target Astro project is being written to (new DAG files, `include/` data). This does not affect AutoSys.
- **Can break starting Phase 6**: cutover changes AutoSys job state (`ON_ICE`) and Airflow DAG pause state. This is the only phase with production blast radius — always confirm rollback (`OFF_ICE` + pause DAG) works before flipping the first box, and flip one box/machine-group at a time, never the whole estate at once.

## First-session checklist

1. Confirm target Astro Runtime version (`astro version`, `astro deployment inspect` if targeting a real Deployment).
2. Get the JIL export.
3. Run Phase 0 estate classification — check for mainframe-boundary signals, agent/machine fleet size, and containerization before deciding which companion skill(s) to load.
4. Run the inventory script.
5. Start classifying records against `reference/mapping.md`.
