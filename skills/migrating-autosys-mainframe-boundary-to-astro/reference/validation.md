# Validation gates (boundary-specific)

Additive to the core skill's per-job gates (import, lint, execution, output parity, safe re-run). These validate the parts of a boundary job that a generic job-semantics gate wouldn't catch.

## Gate B1: Protocol/mechanism actually works end to end

Run the migrated task against the real mainframe-adjacent system (or its confirmed test/staging equivalent, if direct production testing isn't appropriate) and confirm the file/JCL submission genuinely completes — not just that the Airflow task exits zero, since a misconfigured SFTP/Connect:Direct call can sometimes report success locally while the far side rejects or ignores the payload.

## Gate B2: Security boundary sign-off obtained and verified

Confirm the mainframe/security team's explicit sign-off (per `reference/coexistence-and-security.md`) was actually obtained for any network-position or credential change — and confirm the sign-off matches what's actually deployed (a signed-off IP range that doesn't match the Astro Hosted egress range actually in use is a Gate B2 failure, not a documentation nitpick).

## Gate B3: Timing/coexistence held across a full relevant cycle

For jobs with any timing dependency on the mainframe side (a file expected by a certain hour, a delivery window), run the migrated version across at least one full occurrence of the integration's real cadence (daily is not sufficient validation for a month-end-only integration) before calling it complete.

## Gate B4: Mainframe side confirmed unaffected (or its change explicitly documented)

Get an explicit confirmation from the mainframe-side owner that their job/process behaved identically across the validation period — don't infer this from "no complaints were received." Silence is not confirmation.

## Recording results

Each boundary job's record in `boundary_manifest.json` should show which gates passed and when, plus the mainframe-side owner's confirmation (Gate B4) by name/date — this is what lets `scripts/status.py summary` distinguish a genuinely validated `complete` from one marked done on assumption.
