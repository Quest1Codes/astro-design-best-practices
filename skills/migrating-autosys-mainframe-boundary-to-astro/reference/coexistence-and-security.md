# Coexistence and security

## The default assumption

The mainframe side of every boundary integration is unchanged by this migration unless a stakeholder explicitly asks otherwise. Design every translated job to interoperate with the mainframe exactly as the AutoSys job did — same file naming conventions, same delivery windows, same submission mechanism — for at least the full validation period. Do not propose changes to mainframe-side conventions as part of this migration; that's a separate initiative with its own owners.

## Security boundary changes need explicit sign-off

Moving the distributed-side orchestration to Astro can change things the mainframe/security team cares about, even when the AutoSys-side *logic* doesn't change at all:

- **Source IP/network position**: if the migrated task runs from Astro Hosted, its egress IPs differ from the old on-prem AutoSys agent's. Any firewall/DMZ rule on the mainframe-adjacent gateway that allow-lists specific source IPs needs updating — and that update needs the security team's sign-off, not just a network ticket.
- **Service account / credential**: if the migration also changes which credential authenticates across the boundary (see the core skill's `reference/global-variables-and-templating.md` and the on-prem-distributed skill's `reference/secrets-and-identity.md`), confirm the mainframe/gateway side's access control (often RACF-governed) has been updated to recognize it, before cutover, not after a failure.
- **New network path through a DMZ/gateway**: if the target execution environment sits somewhere genuinely new relative to the boundary (e.g., Astro Hybrid inside a different segment than the old on-prem agent), the path through any DMZ/gateway may need its own explicit approval, distinct from a same-segment credential swap.

None of these are this skill's or its user's call to make unilaterally — they go to whoever owns the mainframe-side security posture, with enough lead time for their own change-control process, which is often slower-moving than a typical Airflow migration and should be planned around explicitly.

## Coexistence validation period

Because these integrations are often timing-sensitive (a mainframe job that waits for a file, a delivery window agreed upon between teams), run the migrated boundary job side by side with (or immediately following the retirement of) the AutoSys original for a full cycle — and longer if the integration only exercises certain paths periodically (e.g., a month-end-only delivery needs at least one month-end cycle validated, not just a few days of a normal week).

## What to document explicitly in the report

State plainly, for every migrated boundary job: "the mainframe side required zero changes" (the expected, common case) or, if untrue, exactly what changed on that side and why, who approved it, and when. Burying a mainframe-side change inside a routine-sounding migration note is exactly the kind of undocumented delta the core skill's hard rules exist to prevent — apply the same standard here to the security boundary specifically.
