---
name: assess-migration-complexity-scoring
description: Third phase of an AutoSys estate assessment — scores every job and box's migration complexity (MECH/JUDG/REDESIGN/NONE/DECOMMISSION), aggregates to effort estimates, and proposes migration waves. Use once assess-estate-inventory has produced a fully enriched estate_manifest.json (stats, graph, schedules, commands, and ideally history all populated). Never hand-edit a score — change a rule in scoring_rules.yaml (a PR) or record an override with a reason.
---

# Migration complexity scoring

Turn the enriched estate manifest into a disposition and effort-point score per job and box,
then a wave proposal. The rules are a versioned, hand-authored YAML file
(`scripts/scoring_rules.yaml`) — every score traces to a specific rule, and every rule traces to
a rationale in `reference/scoring-rules.md`.

## Requirements

- `estate_manifest.json` with `stats{}`, `graph{}` populated (`assess-estate-inventory` Phase 2);
  `schedules{}`/`commands{}`/`history{}` are optional but improve scoring quality when present —
  their absence just means the rules that key off them contribute nothing, not an error.

## Hard rule

**Never edit a score by hand.** If a score looks wrong, either the rule is wrong (open a PR
against `scripts/scoring_rules.yaml`, which changes the score for every job that rule affects,
not just the one you noticed) or a genuine judgment override is warranted — record it via
`score_estate.py --override KEY=DISPOSITION:reason`, which is tracked in
`manifest.scores.overrides[]` and auditable, never a silent edit.

## Workflow

### Phase 1: Score

```
python3 scripts/score_estate.py --manifest estate_manifest.json
python3 scripts/score_estate.py --manifest estate_manifest.json --explain ACE:some_job_name
```

Writes `manifest.scores{jobs{}, boxes{}, estate{totals, by_disposition, by_flag, effort_points,
effort_days_range, mech_share, tooling_hint}, rules_version}`. `--explain` prints the full rule
trace for one unit — use this whenever a score looks surprising, before assuming it's wrong.

### Phase 2: Review the extremes

Look at the top-N `REDESIGN`/`NONE`/`DECOMMISSION` units against
`reference/disposition-definitions.md`'s precise tests. These are the units most worth a second
look before the number gets used to plan effort.

### Phase 3: Propose waves

```
python3 scripts/propose_waves.py --manifest estate_manifest.json --max-wave-points 150
```

Groups top-level boxes into waves under a points budget, and picks a pilot wave (one MECH box,
one box with a nontrivial condition string, one calendar-driven box — the three-kind trial rule).
Every wave is written `proposed: true` — this is a starting point for Phase 4, not the final plan.

### Phase 4: Edit waves (judgment)

Per `reference/wave-planning.md`: adjust the proposal for dependency closure the greedy grouping
missed, real ownership boundaries, business-calendar constraints, and risk tolerance. Record the
final wave assignment back into `manifest.waves[]` with `proposed: false` once a human has
actually reviewed and (possibly) changed it.

### Phase 5: Tooling recommendation

Per `reference/translation-tooling-strategy.md`: `manifest.scores.estate.tooling_hint` is a
starting signal (Otto candidate if MECH share ≥ 70% and no hidden-control-flow findings), not a
decision — the reference file's decision table adds script-corpus availability, Astro access, and
convention-capture prerequisites before recommending Otto, Orbiter, hand-translation, or a hybrid.

### Gate

`python3 -m autosys_jil.status --manifest estate_manifest.json summary --workflow assessment`
should read `scored` once this phase is done.

## Reference routing

| Question | Read |
|---|---|
| What each rule does and why, effort-point → person-day factors | `reference/scoring-rules.md` |
| Precise MECH/JUDG/REDESIGN/NONE/DECOMMISSION definitions with examples | `reference/disposition-definitions.md` |
| How to group and sequence waves | `reference/wave-planning.md` |
| Otto vs. Orbiter vs. hand vs. hybrid | `reference/translation-tooling-strategy.md` |

## Scripts

| Script | Purpose |
|---|---|
| `scripts/scoring_rules.yaml` | The versioned rules — THE source of truth for every score |
| `scripts/score_estate.py` | Applies the rules; `--explain` for a per-unit trace |
| `scripts/propose_waves.py` | Groups top-level boxes into a wave proposal + pilot pick |
