---
topic: wave-planning
family: assessment
skill: assess-migration-complexity-scoring
verified_against:
  airflow: "3.3.1"
  astro_runtime: "3.3-2"
  autosys: "12.0"
last_verified: 2026-09-17
confidence: mixed
signals: [multi_owner]
---

# Wave planning

MERGE ← `migrate-topology-onprem-distributed/reference/cutover-waves.md`'s grouping principle
and sequencing, generalized beyond machine groups to the whole estate (`propose_waves.py` groups
top-level boxes by points budget as a starting point; this file is the judgment layer on top of
that proposal). Per-wave cutover *mechanics* (freeze/thaw sequencing, what "clean" means,
rollback) live in `migrate-parallel-run-and-cutover/reference/cutover-runbook.md`, not here —
this file is about *which units go in which wave*, not how a wave is executed.

## Grouping principle

Group by shared risk and shared blast radius, not alphabetical order or arbitrary batch size.
Signals, in rough priority order:

1. **Dependency closure first.** A wave containing a box should also contain (or have already
   migrated) everything it depends on via `condition:` strings or hidden `sendevent` edges
   (`manifest.graph`) — migrating a downstream unit before its upstream creates a broken
   dependency mid-wave. `propose_waves.py` does not currently solve this automatically (its
   grouping is by points budget, ordered ascending); check `manifest.graph.cross_box_condition_edges`
   between proposed waves before finalizing.
2. **Team ownership.** A wave should belong to one team where possible, for a single
   point of contact who can validate and make the go/no-go call.
3. **Business calendar.** Boxes sharing a `run_calendar` (e.g. all month-end jobs) are natural to
   move and test together against the same calendar edge cases.
4. **Shared machine group.** Boxes on the same machine group often share the fate of that
   group's Hosted/Hybrid/bridge decision (`migrate-topology-onprem-distributed`) and should move
   together rather than splitting arbitrarily.
5. **`nfr.change_freeze` windows.** No wave's planned cutover date may fall inside a declared
   freeze window — `propose_waves.py` flags `change_freeze_conflict: true` on every wave when any
   freeze window exists; resolve this manually (the script does not parse dates against the
   window itself).

## Sequencing

- **First (pilot) wave: lowest risk, highest learning value.** `propose_waves.py` picks one
  candidate per kind automatically — one `MECH`-dispositioned box, one box with a nontrivial
  condition string (points ≥ 5), and one calendar-driven box (or the nearest available mix). The
  goal is validating the whole pipeline (translation → trial → parity → cutover → rollback) on
  something survivable if wrong, not picking the easiest possible unit in isolation.
- **Middle waves: the bulk of the estate**, ordered by dependency and team readiness, with the
  pilot wave's lessons folded into `migrate-jil-to-airflow-translation/reference/troubleshooting.md`
  before they start.
- **Last waves: highest-risk / most bridge-heavy / most REDESIGN-dense groups**, migrated once
  the process is proven and any bridge-only exceptions (`migrate-topology-onprem-distributed`)
  have documented, agreed timelines.

## Using `propose_waves.py`'s output

Its grouping (ascending by points, greedily bucketed under `--max-wave-points`) is a *reasonable
default ordering*, not a dependency-aware plan — always cross-check against `manifest.graph`
before accepting a wave boundary that splits a box from something it depends on. Record the
final, human-reviewed wave assignment back into `manifest.waves[]` with `proposed: false` (the
script always writes `proposed: true`) once actually reviewed and adjusted.
