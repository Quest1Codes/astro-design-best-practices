#!/usr/bin/env python3
"""Apply `scoring_rules.yaml` to every job/box in `estate_manifest.json`, writing
`manifest.scores{}` [spec §6.3].

Deterministic: given the same manifest and rules file, output is byte-identical.
Reads/writes local files only; never contacts a live AutoSys or Astro system.

Reads (when present -- each is optional, absence just means that rule group contributes
nothing): `manifest.commands` (command_analysis.py), `manifest.schedules` (calendar_expand.py),
`manifest.history` (history_stats.py), `manifest.command_summary.template_clusters`.

Never edit a score by hand -- change a rule in `scoring_rules.yaml` (a PR), or record an
override with a reason via `--override <job_or_box_key>=<disposition>:<reason>`.

Usage:
    python3 score_estate.py --manifest estate_manifest.json [--rules scoring_rules.yaml]
        [--explain JOB_KEY] [--override KEY=DISPOSITION:reason ...]
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import yaml

_LIB = Path(__file__).resolve().parents[2] / "_lib"
sys.path.insert(0, str(_LIB))

from autosys_jil import manifest as manifest_mod  # noqa: E402
from autosys_jil.boxes import box_metrics  # noqa: E402
from autosys_jil.registry import job_types as job_types_registry  # noqa: E402

SEVERITY_DEFAULT = ["NONE", "MECH", "JUDG", "REDESIGN", "DECOMMISSION"]


def _load_rules(path: Path) -> dict:
    return yaml.safe_load(path.read_text())


def _match_job_type_rule(job_type: str, family: str, rules: list[dict]) -> dict:
    for rule in rules:
        m = rule["match"]
        if m.get("default"):
            return rule
        if job_type in m.get("job_types", []):
            return rule
        if any(job_type.startswith(p) for p in m.get("job_type_prefix", [])):
            return rule
        if family and family in m.get("families", []):
            return rule
    return rules[-1]  # the default rule, if list is well-formed


def _severity_max(a: str, b: str, order: list[str]) -> str:
    ia = order.index(a) if a in order else 0
    ib = order.index(b) if b in order else 0
    return a if ia >= ib else b


class _Trace:
    def __init__(self):
        self.entries: list[str] = []

    def add(self, msg: str) -> None:
        self.entries.append(msg)


def score_job(job, family: str, rules: dict, trace: _Trace | None = None,
             schedule_info: dict | None = None) -> dict:
    jt_rule = _match_job_type_rule(job.job_type, family, rules["job_type_rules"])
    points = jt_rule["points"]
    disposition = jt_rule["disposition"]
    flags: set[str] = set(jt_rule.get("flags", []))
    order = rules["disposition_severity"]
    if trace:
        trace.add(f"job_type={job.job_type} family={family} -> {jt_rule['disposition']} +{jt_rule['points']}")

    if job.condition is not None:
        cond = job.condition
        checks = {
            "has_or": cond.has_or, "has_lookback": bool(cond.lookbacks),
            "has_exitcode": "exitcode" in cond.functions_used,
            "has_value": "value" in cond.functions_used,
            "has_cross_instance": bool(cond.cross_instance_refs),
            "has_notrunning": "notrunning" in cond.functions_used,
            "clause_count_gt5": cond.clause_count > 5,
        }
        for rule in rules["condition_rules"]:
            if checks.get(rule["when"]):
                points += rule.get("points", 0)
                flags.update(rule.get("flags", []))
                if "disposition_floor" in rule:
                    disposition = _severity_max(disposition, rule["disposition_floor"], order)
                if trace:
                    trace.add(f"{rule['id']} +{rule.get('points', 0)}")

    sched = job.schedule
    # "calendar_not_cron" needs calendar_expand.py's actual cron_equivalent() result, not a
    # guess from attribute presence alone -- schedule_info is manifest.schedules[key] when
    # that script has already run (optional; the rule contributes nothing if it hasn't).
    calendar_not_cron = bool(schedule_info) and not schedule_info.get("cron_expressible", True) \
        and (bool(sched.run_calendar) or bool(schedule_info.get("calendar_class")))
    sched_checks = {
        "calendar_not_cron": calendar_not_cron,
        "has_run_window": bool(sched.run_window),
        "has_must_complete_times": bool(sched.must_complete_times),
        "timezone_nondefault": bool(sched.timezone),
    }
    for rule in rules["scheduling_rules"]:
        if sched_checks.get(rule["when"]):
            points += rule.get("points", 0)
            flags.update(rule.get("flags", []))
            if trace:
                trace.add(f"{rule['id']} +{rule.get('points', 0)}")

    attr_checks = {
        "has_job_load_or_resources": bool(job.load.job_load) or bool(job.load.resources),
        "has_svcdesk": bool(job.alerting.svcdesk),
        "has_std_in_file": bool(job.io.std_in_file),
    }
    for rule in rules["attribute_rules"]:
        if attr_checks.get(rule["when"]):
            points += rule.get("points", 0)
            flags.update(rule.get("flags", []))
            if trace:
                trace.add(f"{rule['id']} +{rule.get('points', 0)}")

    return {"points": points, "disposition": disposition, "flags": sorted(flags), "trace": trace.entries if trace else None}


def apply_command_rules(base: dict, cmd_analyses: dict | None, rules: dict, order: list[str], trace: _Trace | None) -> dict:
    if not cmd_analyses:
        return base
    hidden = any(a.get("hidden_control_flow") for a in cmd_analyses.values())
    cred = any(a.get("credential_hits") for a in cmd_analyses.values())
    windows = any(a.get("os_hint") == "windows" for a in cmd_analyses.values())
    env_coupling = any(
        len(a.get("abs_paths", [])) + len(a.get("unc_paths", [])) + len(a.get("mapped_drives", [])) > 3
        for a in cmd_analyses.values()
    )
    checks = {"has_hidden_control_flow": hidden, "has_credential_hit": cred,
             "os_windows": windows, "env_coupling_gt3": env_coupling}
    points, disposition, flags = base["points"], base["disposition"], set(base["flags"])
    for rule in rules["command_rules"]:
        if checks.get(rule["when"]):
            points += rule.get("points", 0)
            flags.update(rule.get("flags", []))
            if "disposition_floor" in rule:
                disposition = _severity_max(disposition, rule["disposition_floor"], order)
            if trace:
                trace.add(f"{rule['id']} +{rule.get('points', 0)}")
    return {"points": points, "disposition": disposition, "flags": sorted(flags), "trace": base.get("trace")}


def _history_coverage_ratio(estate) -> float:
    """Fraction of the estate's own job names that appear anywhere in job_stats.

    Guards `hist.dead`: a history export that only covers a subset of the estate (wrong scope,
    partial extract) must NOT cause every job outside that subset to look "dead" -- that failure
    mode was found by this project's own end-to-end test (an unrelated small history fixture run
    against the full 297-job estate marked all 297 DECOMMISSION). Below the threshold, dead-job
    detection is reported as low-confidence and does not override disposition.
    """
    if not isinstance(estate.history, dict) or not estate.history.get("job_stats"):
        return 0.0
    history_job_names = set(estate.history["job_stats"])
    estate_job_names = {j.name for inst in estate.instances.values() for j in inst.jobs.values()
                        if not j.deleted}
    if not estate_job_names:
        return 0.0
    return len(history_job_names & estate_job_names) / len(estate_job_names)


MIN_HISTORY_COVERAGE_FOR_DEAD_JOB_OVERRIDE = 0.5


def score_estate(estate, rules: dict, explain_key: str | None = None) -> dict:
    order = rules["disposition_severity"]
    jt_registry = job_types_registry()
    job_scores: dict[str, dict] = {}
    history_coverage = _history_coverage_ratio(estate)
    trust_dead_job_detection = history_coverage >= MIN_HISTORY_COVERAGE_FOR_DEAD_JOB_OVERRIDE

    for inst_id, inst in estate.instances.items():
        for job in inst.jobs.values():
            if job.deleted or job.is_box:
                continue
            key = f"{inst_id}:{job.name}"
            family = jt_registry.get(job.job_type, {}).get("family", "")
            trace = _Trace() if explain_key == key else None
            schedule_info = estate.schedules.get(key) if isinstance(estate.schedules, dict) else None
            result = score_job(job, family, rules, trace, schedule_info)
            cmd_analyses = estate.commands.get(key) if isinstance(estate.commands, dict) else None
            result = apply_command_rules(result, cmd_analyses, rules, order, trace)

            hist = estate.history.get("job_stats", {}).get(job.name) if isinstance(estate.history, dict) else None
            dead_jobs = {d["job"] for d in estate.history.get("dead_job_candidates", [])} \
                if isinstance(estate.history, dict) else set()
            manual = estate.history.get("manual_intervention", {}).get("per_job", {}) \
                if isinstance(estate.history, dict) else {}
            sla_breach_jobs = {b["job"] for b in estate.history.get("sla_breaches", [])} \
                if isinstance(estate.history, dict) else set()

            if job.name in dead_jobs:
                if trust_dead_job_detection:
                    result["disposition"] = "DECOMMISSION"
                    result["flags"] = sorted(set(result["flags"]) | {"dead"})
                else:
                    result["flags"] = sorted(set(result["flags"]) | {"dead_low_confidence"})
            if manual.get(job.name, 0) > 10:
                result["points"] += 2
                result["flags"] = sorted(set(result["flags"]) | {"hitl"})
            if job.name in sla_breach_jobs:
                result["flags"] = sorted(set(result["flags"]) | {"sla_breach"})

            job_scores[key] = result

    box_scores: dict[str, dict] = {}
    for inst_id, inst in estate.instances.items():
        metrics = box_metrics(inst.boxes, inst.jobs)
        for box_name, box in inst.boxes.items():
            key = f"{inst_id}:{box_name}"
            own = job_scores.get(key, {"points": 0, "disposition": "NONE", "flags": []})
            child_points = 0
            child_disposition = own["disposition"]
            for child in box.children:
                child_key = f"{inst_id}:{child}"
                cscore = box_scores.get(child_key) or job_scores.get(child_key)
                if cscore:
                    child_points += cscore["points"]
                    child_disposition = _severity_max(child_disposition, cscore["disposition"], order)

            box_flags = set(own["flags"])
            m = metrics.get(box_name, {})
            for rule in rules["box_rules"]:
                cond = {
                    "depth_ge3": m.get("depth", 0) >= 3,
                    "mixed_owner": m.get("mixed_owners", False),
                    "in_large_template_cluster": False,  # requires job-name cross-ref; left as a future hook
                }.get(rule["when"], False)
                if cond:
                    child_points += rule.get("points", 0)
                    box_flags.update(rule.get("flags", []))
                    if "disposition_floor" in rule:
                        child_disposition = _severity_max(child_disposition, rule["disposition_floor"], order)

            box_scores[key] = {"points": own["points"] + child_points, "disposition": child_disposition,
                               "flags": sorted(box_flags)}

    totals_by_disposition: dict[str, int] = {}
    totals_by_flag: dict[str, int] = {}
    for scores in (job_scores, box_scores):
        for s in scores.values():
            totals_by_disposition[s["disposition"]] = totals_by_disposition.get(s["disposition"], 0) + 1
            for f in s["flags"]:
                totals_by_flag[f] = totals_by_flag.get(f, 0) + 1

    total_effort_points = sum(s["points"] for s in job_scores.values())
    factors = rules["effort_points_to_person_days"]
    effort_days_low = sum(s["points"] * factors.get(s["disposition"], 0.5) * 0.7 for s in job_scores.values())
    effort_days_high = sum(s["points"] * factors.get(s["disposition"], 0.5) * 1.3 for s in job_scores.values())

    mech_count = sum(1 for s in job_scores.values() if s["disposition"] == "MECH")
    mech_share = mech_count / len(job_scores) if job_scores else 0.0
    hidden_flow_count = totals_by_flag.get("hidden_flow", 0)
    otto_rule = rules["tooling_hint_rules"]["otto_candidate"]
    tooling_hint = "otto_candidate" if (
        mech_share >= otto_rule["min_mech_share"] and hidden_flow_count <= otto_rule["max_hidden_flow_count"]
    ) else "hybrid_or_hand"

    return {
        "jobs": job_scores, "boxes": box_scores,
        "estate": {
            "totals": {"job_count": len(job_scores), "box_count": len(box_scores)},
            "by_disposition": totals_by_disposition, "by_flag": totals_by_flag,
            "effort_points": total_effort_points,
            "effort_days_range": [round(effort_days_low, 1), round(effort_days_high, 1)],
            "mech_share": round(mech_share, 3), "tooling_hint": tooling_hint,
            "history_coverage_ratio": round(history_coverage, 3),
            "dead_job_detection_trusted": trust_dead_job_detection,
        },
        "rules_version": rules["version"], "overrides": [],
    }


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--manifest", type=Path, required=True)
    ap.add_argument("--rules", type=Path, default=Path(__file__).parent / "scoring_rules.yaml")
    ap.add_argument("--explain", default=None, metavar="INSTANCE:JOB")
    ap.add_argument("--override", action="append", default=[], metavar="KEY=DISPOSITION:reason")
    args = ap.parse_args(argv)

    if not args.manifest.exists():
        print(f"error: {args.manifest} not found -- run build_estate_manifest.py first", file=sys.stderr)
        return 1

    estate = manifest_mod.from_json(args.manifest)
    rules = _load_rules(args.rules)
    scores = score_estate(estate, rules, explain_key=args.explain)

    for ov in args.override:
        key, rest = ov.split("=", 1)
        disposition, _, reason = rest.partition(":")
        target = scores["jobs"].get(key) or scores["boxes"].get(key)
        if target is None:
            print(f"error: --override key {key!r} not found in scores", file=sys.stderr)
            return 1
        scores["overrides"].append({"key": key, "from": target["disposition"], "to": disposition, "reason": reason})
        target["disposition"] = disposition

    estate.scores = scores
    manifest_mod.to_json(estate, args.manifest, tool="score_estate.py")

    if args.explain:
        target = scores["jobs"].get(args.explain)
        if target:
            print(f"--- explain {args.explain} ---", file=sys.stderr)
            for line in target["trace"] or []:
                print(f"  {line}", file=sys.stderr)
            print(f"  => points={target['points']} disposition={target['disposition']} flags={target['flags']}",
                  file=sys.stderr)

    e = scores["estate"]
    print(f"updated {args.manifest}: {e['totals']['job_count']} jobs, {e['totals']['box_count']} boxes scored; "
          f"by_disposition={e['by_disposition']}; effort {e['effort_points']}pts, "
          f"{e['effort_days_range']} person-days; tooling_hint={e['tooling_hint']}", file=sys.stderr)
    history_was_collected = isinstance(estate.history, dict) and bool(estate.history.get("job_stats"))
    if not e["dead_job_detection_trusted"] and history_was_collected:
        print(f"warning: history covers only {e['history_coverage_ratio']:.0%} of the estate's "
              f"job names -- dead-job detection is NOT trusted (no DECOMMISSION overrides "
              f"applied); jobs with no history match are flagged 'dead_low_confidence' instead. "
              f"Confirm the history export's scope before assuming coverage is complete.", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
