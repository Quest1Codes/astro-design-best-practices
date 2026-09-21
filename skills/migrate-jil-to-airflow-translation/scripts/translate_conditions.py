#!/usr/bin/env python3
"""For every `condition:` string in the manifest, emit a recommended implementation + equivalence
row [spec §7.1]. See reference/conditions-and-dependencies.md for the rules this implements.

Deterministic: given the same manifest, output is byte-identical.
Reads the manifest and writes local files only; never contacts a live AutoSys or Astro system.

Output is a SEED for the report's equivalence rows -- a human accepts or edits every row
(`_lib.autosys_jil.status advance`), never auto-applied.

Usage:
    python3 translate_conditions.py --manifest estate_manifest.json --out equivalence_rows.json [--md equivalence_rows.md]
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

_LIB = Path(__file__).resolve().parents[2] / "_lib"
sys.path.insert(0, str(_LIB))

from autosys_jil import manifest as manifest_mod  # noqa: E402


def recommend_for_leaf(leaf) -> tuple[str, str, bool]:
    """Returns (target, delta, needs_decision) for one leaf node of a condition AST."""
    kind = type(leaf).__name__
    if kind == "Status":
        if leaf.lookback is not None:
            return (f"ExternalTaskSensor(execution_date_fn=...) for {leaf.ref} "
                    f"(look-back {leaf.lookback})",
                    "Look-back window must be reproduced explicitly, not dropped as a plain edge "
                    "(reference/conditions-and-dependencies.md#look-back).", True)
        if leaf.ref.instance:
            return (f"Cross-Deployment signal for {leaf.ref} (Asset or REST TriggerDagRunOperator)",
                    "Cross-instance dependency -- confirm both sides' migration status before "
                    "choosing the mechanism.", True)
        if leaf.fn == "notrunning":
            return ("max_active_runs=1 (self) or a shared Pool capacity 1 (cross-job)",
                    "notrunning() is a mutex, not a dependency -- confirm which case applies "
                    "before implementing.", True)
        if leaf.fn == "terminated":
            return ("Evaluator task checking TERMINATED-specific state",
                    "No stock trigger_rule distinguishes killed from failed.", True)
        trigger_rule = {"success": "all_success", "failure": "all_failed", "done": "all_done"}.get(leaf.fn)
        return (f"Upstream edge, trigger_rule={trigger_rule!r}",
                "None expected for a single-clause status condition.", False)
    if kind == "ExitCode":
        return (f"Evaluator/@task.branch on exitcode for {leaf.ref} {leaf.op} {leaf.value}",
                "Must be translated consistently with max_exit_success/success_codes on the "
                "same job if set (reference/alerting-and-sla.md).", True)
    if kind == "Value":
        return (f"Variable/Asset-event check or evaluator task for VALUE({leaf.global_name})",
                "Confirm the producer (sendevent SET_GLOBAL vs. static config) before choosing "
                "Variable vs. XCom (reference/global-variables-and-templating.md).", True)
    return ("Unrecognized leaf kind", "Manual review required.", True)


def translate_job_condition(job) -> dict | None:
    if job.condition is None:
        return None
    ast = job.condition
    leaves = ast.leaves
    per_leaf = [recommend_for_leaf(leaf) for leaf in leaves]
    needs_decision = ast.has_or or any(nd for _, _, nd in per_leaf) or (
        len(leaves) > 1 and len({type(leaf).__name__ for leaf in leaves}) > 1)

    if ast.shape == "single" and not needs_decision:
        target, delta, _ = per_leaf[0]
        classification = "MECH"
    elif ast.has_or:
        target = ("REDESIGN: Asset race (preferred) or an evaluator @task short-circuiting on "
                  "any-of-N upstream states")
        delta = "OR-combined condition has no native trigger_rule for a subset of upstreams."
        classification = "REDESIGN"
    elif ast.shape == "and_only" and len({type(leaf).__name__ for leaf in leaves}) == 1 and \
            all(getattr(leaf, "fn", None) == "success" for leaf in leaves):
        target = "Multiple upstream edges, default trigger_rule"
        delta = "None expected -- all-success AND."
        classification = "MECH"
    else:
        target = "Evaluator @task querying TaskInstance state per named upstream, gating a ShortCircuitOperator"
        delta = "Mixed-function AND -- trigger rules apply per-task, not per-upstream."
        classification = "JUDG"

    return {
        "job": job.name,
        "source_condition": job.condition_raw,
        "canonical": ast.to_string(),
        "shape": ast.shape,
        "classification": classification,
        "target": target,
        "delta": delta,
        "needs_decision": needs_decision,
        "per_leaf": [{"target": t, "delta": d, "needs_decision": nd} for t, d, nd in per_leaf],
    }


def translate_all(estate) -> list[dict]:
    rows = []
    for inst_id, inst in estate.instances.items():
        for job in inst.jobs.values():
            if job.deleted:
                continue
            row = translate_job_condition(job)
            if row:
                row["instance"] = inst_id
                rows.append(row)
    return rows


def render_md(rows: list[dict]) -> str:
    lines = ["# Condition equivalence rows", "",
            "| Job | Source | Classification | Target | Needs decision |",
            "|---|---|---|---|---|"]
    for r in rows:
        src = r["source_condition"].replace("|", "\\|") if r["source_condition"] else ""
        lines.append(f"| {r['job']} | `{src}` | {r['classification']} | {r['target']} | "
                     f"{'YES' if r['needs_decision'] else 'no'} |")
    return "\n".join(lines) + "\n"


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--manifest", type=Path, required=True)
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--md", type=Path, default=None)
    args = ap.parse_args(argv)

    if not args.manifest.exists():
        print(f"error: {args.manifest} not found -- run build_estate_manifest.py first", file=sys.stderr)
        return 1

    estate = manifest_mod.from_json(args.manifest)
    rows = translate_all(estate)
    args.out.write_text(json.dumps(rows, sort_keys=True, indent=2) + "\n")
    if args.md:
        args.md.write_text(render_md(rows))

    needs_decision = sum(1 for r in rows if r["needs_decision"])
    print(f"wrote {args.out}: {len(rows)} condition(s) translated, "
          f"{needs_decision} need a human decision", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
