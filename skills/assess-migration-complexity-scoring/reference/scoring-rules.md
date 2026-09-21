---
topic: scoring-rules
family: assessment
skill: assess-migration-complexity-scoring
verified_against:
  airflow: "3.3.1"
  astro_runtime: "3.3-2"
  autosys: "12.0"
last_verified: 2026-09-17
confidence: practitioner-judgment
signals: []
---

# Scoring rules — human mirror of `scripts/scoring_rules.yaml`

PRACTITIONER JUDGMENT throughout — these point values and the disposition-per-job-type defaults
are this project's own v1 calibration (`calibration_source: assumption` in the YAML), not
independently verifiable facts. They're a reasonable starting position for a first engagement,
meant to be refined by real completed-migration data (plan §11.9) — never treated as ground
truth on their own.

## Why job-type points differ

The base point value per job type is a rough proxy for translation effort *independent of any
condition/schedule/command complexity that job also happens to have*:

- **1pt** (`CMD`, `SQL`/`DBPROC`/`SQLAGENT`, `PROXY`): a near-mechanical operator swap
  (`BashOperator`, `SQLExecuteQueryOperator`, `SSHOperator`).
- **2pt** (`BOX`, `FW`, `FTP`/`SCP`, `HTTP`/`WBSVC`/`WSDOC`, `HDFS`/`HIVE`/`PIG`/`SQOOP`): a real
  decision is needed (box boundary, sensor mode, provider operator choice) but a stock Airflow
  component almost always fits.
- **3pt** (`FT`, `DBMON`/`DBTRIG`, `I5`/`MICROFOCUS`, java family, pam-informatica family): the
  target requires either a less-common provider or a judgment call with real translation-quality
  risk (CDC redesign for `DBTRIG`, container-exec for java types).
- **4pt** (`HTTP`/`WBSVC`/`WSDOC` messaging siblings `JMS*`/`JMX*`/`SNMP*`, ERP family, `OOZIE`):
  provider-less or workflow-rewrite territory.
- **5pt** (unknown job type): scored pessimistically on purpose — an unrecognized type is a real
  risk until proven otherwise, not a rounding error.
- **0pt / NONE** (`OM*` monitors, `WOL`): translated as "do this elsewhere" by default, not
  scored as translation work at all.

## Why the additive modifiers exist

Every modifier targets a *specific*, previously-identified source of undercounted complexity
(plan §1.2/§11's audit findings), not a generic "make it bigger" fudge factor:

| Rule | Why |
|---|---|
| `cond.or_present: +3, floor REDESIGN` | An OR-combined condition has no single stock `trigger_rule` — this is the audit's own example of an undocumented-delta risk if scored as MECH. |
| `cond.lookback: +2, floor JUDG` | Look-back needs an explicit `ExternalTaskSensor`/Asset-window decision, never a default. |
| `cond.cross_instance: +3, flag multi_deployment` | Signals a genuine multi-Deployment topology question, not just translation work. |
| `cond.notrunning: +2, floor JUDG, flag mutex` | `notrunning()` is AutoSys's native mutex primitive — deciding "dependency vs. mutex" per plan §5 is a real per-job call, not mechanical. |
| `sched.calendar_not_cron: +2` | Directly from `calendar_expand.py`'s `cron_equivalent()` result — a non-cron-expressible schedule needs real Timetable authoring, not a one-line cron string. |
| `cmd.hidden_sendevent: +3, floor REDESIGN, flag hidden_flow` | Plan's own "#1 source of surprise in migrations" — scored at REDESIGN severity deliberately, since a hidden dependency edge missed at translation time is a production incident, not a nuisance. |
| `cmd.os_windows: +2, flag windows` | Astro workers are Linux — any Windows-hosted command needs an explicit bridge/containerize/re-platform decision (plan §11.11), never silent. |
| `cmd.template_cluster_ge5: -1, flag factory_candidate` | The only *negative* modifier — a large template cluster is cheaper per-unit once dag-factory/dynamic-task-mapping is applied to the whole cluster at once, and is flagged as an efficiency opportunity, not a cost. |
| `hist.dead: disposition -> DECOMMISSION` | The only outcome cheaper than `NONE` — a job with no run in the window and no calendar/condition eligibility is a decommission candidate, not a translation task at all. |
| `hist.manual_interventions_gt10_per_90d: +2, flag hitl` | High manual-intervention frequency is direct evidence of REDESIGN-worthy operational fragility that JIL alone would never surface. |

## Aggregation

Box effort = sum of children's effort points + the box job's own points. Box disposition = the
most severe disposition among itself and its children
(`NONE < MECH < JUDG < REDESIGN < DECOMMISSION`), unless a human override is recorded.

## Effort-point → person-day factors (v1, `calibration_source: assumption`)

| Disposition | Factor |
|---|---|
| `MECH` | 0.25 |
| `JUDG` | 0.75 |
| `REDESIGN` | 2.0 |
| `NONE` | 0.1 |
| `DECOMMISSION` | 0.05 |

`score_estate.py` reports a **range** (±30% around the point-weighted sum), never a single
number — effort estimation has real variance this v1 calibration cannot resolve. Every completed
migration should produce a calibration record under `research/effort-calibration/*.md` that
refines these factors for the next engagement.

## Tooling hint

`mech_share >= 0.70` and zero `hidden_flow`-flagged units → `otto_candidate`; otherwise
`hybrid_or_hand`. This is a *hint* consumed by `reference/translation-tooling-strategy.md`'s
fuller decision table, never a final recommendation on its own.
