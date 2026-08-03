# Task SETUP-6 — `astro-design-best-practices` Skill Scaffold

**Phase**: Setup (prerequisite — not one of the 100 numbered topic tasks)
**Priority**: P0 (blocking all 100 topic tasks — they write into this structure)
**Status**: NOT STARTED

---

## Description

Create the skeleton that every one of the 100 topic tasks writes into: the
skill's manifest and the 13 cluster subdirectories under `reference/`. Without
this existing first, Task 001 (and every task after it) has nowhere defined to
put its output.

## Deliverables

- `skills/astro-design-best-practices/SKILL.md` — manifest with YAML
  frontmatter (name/description/metadata, matching `autosys-astronomer-expert/SKILL.md`'s
  shape) and an empty "Reference Files" index, one line added per topic as
  each Task 001-100 completes Human Sign-off
- 13 empty subdirectories under `skills/astro-design-best-practices/reference/`:
  `scheduler-and-dag/`, `executor-and-worker/`, `metadata-db-and-state/`,
  `security-and-multitenancy/`, `observability-and-alerting/`,
  `cicd-and-environment-topology/`, `config-and-secrets/`, `ha-and-dr/`,
  `regulatory-and-compliance/`, `integration-and-enterprise-mesh/`,
  `migration-execution-and-coexistence/`, `cost-and-capacity-governance/`,
  `governance-and-operating-model/`

## Acceptance Criteria

- [ ] `SKILL.md` exists with valid frontmatter and an (initially empty)
      Reference Files index
- [ ] All 13 cluster subdirectories exist under `reference/`
- [ ] Directory names match exactly what `tasks/README.md`'s Phase 2 cluster
      headers specify (no naming drift between the roadmap and the actual
      filesystem)

## Dependencies

- SETUP-3

## References

- `skills/migrating-autosys-to-astronomer/SKILL.md` and
  `skills/*/SKILL.md` more broadly — format template
