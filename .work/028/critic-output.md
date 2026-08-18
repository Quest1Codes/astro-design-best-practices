# Critic Output — 028

*(Critic note: fresh-context review — only draft and fact-sheet consulted.)*

## Verdict: **PASS with one minor flag**

## Unsourced claims
- **Cleared**: All citation markers map correctly to researcher fact-sheet rows.
- **B3** (restart scheduler after restoring to avoid zombie tasks): researcher flags this as `PRACTITIONER JUDGMENT`. The draft surfaces this correctly in the "Key risks" table without a citation marker, which is appropriate for practitioner judgment. ✓
- **B4** (AutoSys Event Server comparison): referenced in intro as practitioner judgment context; the text is directionally correct. ✓

## Execution-check-required items
- **A1-4** (BYOD WAL archiving + PITR validation): correctly flagged `NEEDS_EXEC_CHECK` in both the researcher and the draft's NOTE block. ✓
- Astronomer Hosted DR SLA specifics (RPO/RTO numbers): correctly flagged "contact Astronomer support" in the dispatch table. ✓

## Papered-over gaps
- **Flag — RPO/RTO numbers for mid-size estates** (4–8 hours in the scale table): the researcher fact-sheet does not have a specific tier-1 or tier-2 source for this range. The "4–8 hours" figure in the Axis B table (`Mid / production → 4–8 hours`) is not attributable to any researcher row. This is practitioner judgment that should be marked as such. **Severity: Low-medium** — the table is presented as a design starting point, not a guarantee, but it lacks a `{syn: ...}` transparency marker. Recommend adding `{syn: RPO-targets-practitioner-judgment}` or a NOTE below the table stating that RPO targets depend on business requirements and are not prescribed by Astronomer.

## Consistency conflicts with shipped files
- `reference/executor-and-worker/autoscaling-design-for-bursty-batch-workloads.md`: discusses worker recovery; the "restart scheduler after restoring" advice in Topic 028 is consistent. ✓

## Axis coverage check
- **Deployment model (H)**: ✓ Full table (Hosted / dedicated / cloud BYOD / self-hosted BYOD)
- **Estate scale (H)**: ✓ RPO/RTO planning table present
- **Vertical/compliance (M)**: ✓ SOX 7-year retention callout present [E1]

## Recommendation
**PASS with one change before shipping:**
Add `{syn: RPO-targets-practitioner-judgment}` inline on the "4–8 hours" row of the scale table, or add a NOTE below the RPO/RTO table stating: "RPO/RTO targets in this table are design starting points; the actual targets for your estate must be defined by business and compliance requirements, not by this reference file."
