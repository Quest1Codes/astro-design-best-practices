# Troubleshooting: known failure classes

Seed entries below are anticipated from the on-prem-distributed topology; expand with actually-observed failures as they occur, fixing the class rather than the instance each time.

## "Job worked in the pilot but fails from a different worker in the same wave"

**Cause**: an environment dependency the pilot machine happened to have (a driver version, a cached file, a specific locale setting) that wasn't actually captured in the container image / Hybrid node provisioning — the pilot passed by accident, not because the dependency was properly packaged.

**Fix the class**: treat every environment dependency discovered during a pilot as something to add to the base image/provisioning spec, not a one-off fix on the machine that happened to need it. Re-run Gate T3 (`reference/validation.md`) against a *second*, independently-provisioned worker before trusting a pilot result.

## "Network path worked in testing, fails on the actual cutover date"

**Cause**: firewall rules were requested and confirmed via ticket status ("done") but never actually connection-tested from the real environment, or a rule was scoped to a specific IP that changed (common with Hosted egress ranges, which are platform-maintained and can shift).

**Fix the class**: never mark Gate T1 passed from a ticket status alone — require an actual connection test result, and re-verify egress ranges are current (not cached from when the ticket was filed) immediately before cutover, not just at planning time.

## "Credential works via direct testing but the scheduled run still fails auth"

**Cause**: the Connection was tested manually (e.g., via the Airflow UI's "test connection" button or a manual script) using an interactively-obtained token, but the scheduled task's actual auth path (e.g., a service-account flow, or a secrets-backend lookup) differs from the manual test path.

**Fix the class**: test auth through the same code path the scheduled task actually uses, not a manual substitute — if the task pulls a secret from a secrets backend at run time, test by actually running the task, not by manually fetching the secret and testing it out of band.

## "Wave rollback plan was never actually tried, and doesn't work when needed"

**Cause**: rollback (`OFF_ICE` + pause DAG) was documented but only tested conceptually, not executed, before the first real wave went live.

**Fix the class**: rollback must be a rehearsed action during the Phase 4 trial, on the pilot machine group, before any wave with real business impact is scheduled — "we could roll back" is not the same claim as "we rolled back and it worked."

## "Capacity looked fine in the pilot, workers saturate during month-end"

**Cause**: the pilot ran during a normal week; the capacity estimate wasn't validated against the estate's actual peak period (month-end, quarter-end, or whatever the business calendar's heaviest day is).

**Fix the class**: Gate T4 monitoring has to span at least one occurrence of the machine group's own peak cadence before capacity is considered validated — a job whose real stress case is month-end cannot be capacity-validated by a week of average-load monitoring.
