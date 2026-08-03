# migrating-autosys-mainframe-boundary-to-astro

A companion to `migrating-autosys-to-astronomer` for the subset of an estate's jobs that touch a mainframe (z/OS) system at the boundary: watching for mainframe-produced files, delivering files to the mainframe, or triggering mainframe batch via JCL submission.

## The scope, stated precisely

AutoSys is a distributed scheduler. It has never run on z/OS — mainframe scheduling is a different Broadcom product line (CA Workload Automation for z/OS, formerly CA-7). So this skill is not "migrate the mainframe workload to Astro" — that's not what's being asked, and it's not what AutoSys ever did. It's "migrate the AutoSys-side jobs that happen to interact with a mainframe system, while that mainframe system keeps running exactly as it does today." Keeping this distinction explicit matters for scoping conversations with a customer — overclaiming here (implying mainframe compute itself is moving) sets the wrong expectation.

## How it works

1. **Detect boundary jobs**: [`scripts/boundary_job_scanner.py`](scripts/boundary_job_scanner.py) scans the core skill's `manifest.json` for signals — z/OS-style dataset naming conventions, MFT/Connect:Direct keyword references, FT job types, gateway-suggestive hostnames — and flags candidates. These are heuristic flags, not confirmed boundary jobs.
2. **Confirm with the platform/mainframe team**: every flagged job gets a real answer — what's actually on the other side, what protocol, whether the mainframe side has any timing dependency on this job.
3. **Plan the translation**: pick the Airflow operator matching the confirmed protocol ([`reference/operator-mapping.md`](reference/operator-mapping.md)), and plan the security/coexistence approach ([`reference/coexistence-and-security.md`](reference/coexistence-and-security.md)) — the mainframe side is assumed unchanged unless told otherwise.
4. **Trial and validate** 1-2 representative jobs with explicit security sign-off before scaling.
5. **Migrate the rest**, tracked by [`scripts/status.py`](scripts/status.py).

## Using it

```bash
claude "Use the migrating-autosys-to-astronomer skill on ~/estate.jil, then the migrating-autosys-mainframe-boundary-to-astro skill to identify and migrate the mainframe-boundary jobs"
```

## What the detection looks like

```
python3 scripts/boundary_job_scanner.py --manifest manifest.json --out boundary_manifest.json
```

```json
{
  "job": "watch_mainframe_extract",
  "signals": ["dataset_naming_pattern: PROD.FINANCE.DAILY.EXTRACT", "job_type_ft"],
  "confidence": "medium",
  "status": "flagged",
  "confirmed": null
}
```

`confidence` reflects how many independent signals matched, not certainty about the underlying system — every row still needs a human/platform-team confirmation pass before being treated as real.

## Status

First draft. The detection heuristics (dataset naming pattern, keyword matching) are deliberately conservative about claiming certainty — silence from the scanner is not proof a job isn't boundary-related, and a flag is not proof it is. Both directions need confirmation.
