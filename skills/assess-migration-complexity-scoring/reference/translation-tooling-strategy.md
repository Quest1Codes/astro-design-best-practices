---
topic: translation-tooling-strategy
family: assessment
skill: assess-migration-complexity-scoring
verified_against:
  airflow: "3.3.1"
  astro_runtime: "3.3-2"
last_verified: 2026-09-17
confidence: mixed
signals: []
---

# Translation tooling strategy

`manifest.scores.estate.tooling_hint` (`otto_candidate` when MECH share ≥ 70% and zero
hidden-control-flow findings, else `hybrid_or_hand`) is a single-signal starting point. This
file's decision table adds the prerequisites that actually determine whether a tool applies.

confidence: mixed — Otto and Orbiter capability claims here should be re-verified against current
Astronomer documentation before being presented to a customer as fact; this session did not have
MCP access to Astronomer's live docs (see `skills/docs/HANDOFF.md` §5).

## Decision table

| Condition | Recommendation | Why |
|---|---|---|
| `tooling_hint: otto_candidate` AND script corpus collected AND customer has (or will grant) Astro access for the review workflow | **Otto-assisted** | High mechanical share with low hidden-risk findings is exactly the profile Otto-assisted translation suits — see `astro-design-best-practices/reference/migration-execution-and-coexistence/otto-assisted-translation-workflow.md` |
| `tooling_hint: otto_candidate` but script corpus NOT collected | **Otto-assisted, blocked on discovery** | Otto (like hand translation) needs the actual script bodies, not just the JIL `command:` line referencing them — route back to `assess-estate-discovery`'s script-corpus artifact row |
| MECH share moderate (40-70%), `hidden_flow` count low, large `template_clusters` present | **Hybrid: Otto/factory-pattern for the MECH clusters, hand for the rest** | Template clusters are exactly where a dag-factory approach and/or Otto's batch translation pays off fastest; low-MECH-share residue needs individual attention regardless of tooling |
| `hidden_flow` count high, or REDESIGN share high | **Hand translation, tooling as a first-draft aid only** | Hidden control-flow and REDESIGN-heavy estates need a human reading actual behavior, not a pattern-matched translation — any tool's first draft here is a starting point to review carefully, not a result to trust |
| Estate is small (roughly < 50 jobs) regardless of other signals | **Hand translation** | Tooling setup/review overhead isn't worth it below a certain estate size; use judgment on the exact threshold per engagement |
| No PAM/script-repo access granted | **Hand translation only, until access exists** | Neither Otto nor a dag-factory approach can proceed without the actual script bodies |

## What each approach cannot do

- **Otto**: cannot originate REDESIGN-class translations (no stock Airflow shape to draft
  against) or resolve a hidden `sendevent` dependency it wasn't told about — those still need
  human translation regardless of how Otto-friendly the rest of the estate is.
- **Orbiter** (open-source translation framework): treat as an alternative first-draft generator
  with different coverage/maturity tradeoffs than Otto — re-verify current capability against
  Astronomer's docs before recommending either over the other for a specific job-type mix.
- **Hand translation**: doesn't scale to hundreds of near-identical MECH jobs efficiently — a
  large `MECH`-heavy estate translated entirely by hand is usually a process failure, not a
  thoroughness win.

## Recording the decision

State the chosen strategy per wave (a pilot wave might deliberately use hand translation even in
an Otto-candidate estate, specifically to build the human review muscle before scaling tooling
use) in the report's "Translation tooling strategy" section, informed by but not copied verbatim
from `tooling_hint`.
