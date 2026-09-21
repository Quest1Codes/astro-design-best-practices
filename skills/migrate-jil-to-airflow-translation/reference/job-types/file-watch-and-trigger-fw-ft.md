---
topic: file-watch-and-trigger-fw-ft
family: migration
skill: migrate-jil-to-airflow-translation
verified_against:
  airflow: "3.3.1"
  astro_runtime: "3.3-2"
  autosys: "12.0"
  autosys_doc_pages: [2551]
last_verified: 2026-09-17
confidence: mixed
signals: [calendar_not_cron]
---

# File watch and trigger: FW, FT

**FT = File Trigger** (event-driven watcher), **not a transfer type** — the pre-refactor skill's
`mapping.md` line 17 said "FT = File transfer," which is wrong; transfer types are `FTP`/`SCP`
(`reference/file-transfer-ftp-scp.md`). Verified against `autosys-reference/reference/job-types.md`.

| Code | Default target | Disposition | Attributes consumed | Delta |
|---|---|---|---|---|
| `FW` (File Watcher) | `FileSensor` (`mode="reschedule"`) if literally polling a filesystem — but if the file is produced by another Airflow-owned DAG, redesign as an Asset-triggered schedule instead of polling | JUDG | `watch_file` | Polling cadence/timeout need explicit values, not defaults copied from AutoSys's own polling interval without checking it |
| `FT` (File Trigger) | Event-driven: an `@asset` fed by an external watcher publishing via the Airflow REST API, or a `FileSensor` fallback | JUDG | `watch_file_type`, `watch_file_change_type`, `watch_file_min_size`, `watch_no_change`, `watch_file_recursive` | The event-driven vs. polling choice materially changes latency and infra footprint — state which was chosen and why |

## `watch_file_type` / `watch_file_change_type` / `watch_file_min_size` / `watch_no_change` / `watch_file_recursive`

These control *what counts as arrival* — a new file, a file that stopped changing (size
stability, common for large transfers), a minimum size threshold, or recursive directory
watching. Translate each explicitly into the sensor/Asset-producer's own logic; do not assume
"file exists" is sufficient when `watch_no_change`/`watch_file_min_size` was set — those exist
specifically because "file exists" was proven insufficient for that job.

## z/OS-adjacent FW/FT

An `FW`/`FT` job watching for mainframe-produced data (dataset-naming patterns, MFT keywords) is
also a `migrate-topology-mainframe-boundary` signal — check
`boundary_job_scanner.py`'s findings before translating in isolation.

## What the scaffolder emits vs. leaves as TODO

Emits the `FileSensor`/`@asset` skeleton with the watched path parameterized; leaves
`# TODO(JUDG:polling-vs-event)` for the polling-vs-event-driven decision and
`# TODO(JUDG:watch-semantics)` wherever `watch_no_change`/`watch_file_min_size` needs custom
logic beyond a bare existence check.
