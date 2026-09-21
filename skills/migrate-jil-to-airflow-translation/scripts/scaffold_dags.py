#!/usr/bin/env python3
"""Emit DAG skeletons for a wave's MECH/JUDG units [spec §7.1].

Deterministic: given the same manifest and wave, output is byte-identical.
Reads the manifest and writes local `.py`/`traceability.json` files only; never contacts a live
AutoSys, Astro, or network endpoint, and never executes anything it emits.

Sources:
  - skills/docs/REFACTOR-FILE-SPEC.md §7.1 (this script's spec)
  - `_emitters/` per family; `reference/job-types/*.md` for what each emitter should produce

Refuses to scaffold a REDESIGN or NONE unit outright (lists them instead of a fake skeleton) --
per SKILL.md's hard rule 6.

Usage:
    python3 scaffold_dags.py --manifest estate_manifest.json --wave 1 --out dags/ [--include include/]
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

_LIB = Path(__file__).resolve().parents[2] / "_lib"
sys.path.insert(0, str(_LIB))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from autosys_jil import manifest as manifest_mod  # noqa: E402
from autosys_jil.boxes import top_level_boxes  # noqa: E402
from autosys_jil.registry import job_types as job_types_registry  # noqa: E402

from _emitters import FAMILY_EMITTERS  # noqa: E402
from _emitters.base import EmittedTask, _safe_task_id, generic_bash_stub  # noqa: E402

REFUSED_DISPOSITIONS = {"REDESIGN", "NONE"}

_DAG_HEADER = '''"""Auto-scaffolded by scaffold_dags.py from AutoSys box "{box_name}" (instance {instance}).

Traceability: this DAG's tasks carry autosys_job_name/autosys_instance/autosys_box in `params`;
see traceability.json for the job -> dag_id.task_id mapping. Every # TODO(JUDG:...) marker below
needs a human decision before this DAG is production-ready -- see the referenced reference file.
"""
from __future__ import annotations

from datetime import timedelta

from airflow.sdk import dag, task
{extra_imports}

DEFAULT_ARGS = {{"owner": "{owner}", "retries": 1}}


@dag(
    dag_id="{dag_id}",
    schedule=None,  # TODO(JUDG:schedule): set from calendar_expand.py / translate_calendars.py output
    catchup=False,
    default_args=DEFAULT_ARGS,
    tags={tags!r},
    doc_md="""Scaffolded from AutoSys box `{box_name}` (instance `{instance}`).""",
)
def {dag_func}():
{task_bodies}

{dag_func}()
'''


def emit_task(job, jt_registry: dict) -> EmittedTask:
    family = jt_registry.get(job.job_type, {}).get("family", "")
    emitter = FAMILY_EMITTERS.get(family)
    if emitter:
        return emitter(job)
    return generic_bash_stub(job, f"no dedicated emitter for family {family!r}")


def scaffold_box(inst_id: str, inst, box_name: str, scores: dict) -> tuple[str, list[str], dict]:
    jt_registry = job_types_registry()
    child_names = inst.boxes[box_name].children
    tasks: list[EmittedTask] = []
    trace: dict[str, str] = {}
    all_imports: set[str] = set()
    owners = set()

    for child_name in child_names:
        job = inst.jobs.get(child_name)
        if job is None or job.deleted or job.is_box:
            continue  # nested boxes are a future extension: flatten one level for v1
        emitted = emit_task(job, jt_registry)
        tasks.append(emitted)
        all_imports.update(emitted.imports)
        dag_id = f"{inst_id.lower()}__{box_name.lower()}"
        trace[f"{inst_id}:{child_name}"] = f"{dag_id}.{emitted.task_id}"
        if job.owner:
            owners.add(job.owner)

    dag_id = f"{inst_id.lower()}__{box_name.lower()}"
    dag_func = _safe_task_id(dag_id)
    task_bodies = "\n".join("    " + line for t in tasks for line in t.code.strip("\n").splitlines())
    if not task_bodies:
        task_bodies = "    pass  # TODO(JUDG:empty-box): no translatable children found"

    text = _DAG_HEADER.format(
        box_name=box_name, instance=inst_id, dag_id=dag_id, dag_func=dag_func,
        owner=(sorted(owners)[0] if owners else "unknown"),
        tags=sorted({"autosys", inst_id.lower()}),
        extra_imports="\n".join(sorted(all_imports)),
        task_bodies=task_bodies,
    )
    todos = [t for et in tasks for t in et.todos]
    return text, todos, trace


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--manifest", type=Path, required=True)
    ap.add_argument("--wave", type=int, required=True)
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--include", type=Path, default=None)
    args = ap.parse_args(argv)

    if not args.manifest.exists():
        print(f"error: {args.manifest} not found -- run build_estate_manifest.py first", file=sys.stderr)
        return 1

    estate = manifest_mod.from_json(args.manifest)
    if not estate.scores or not estate.waves:
        print("error: manifest has no scores{}/waves[] -- this skill refuses to scaffold "
              "without a scored, waved manifest (see SKILL.md Requirements)", file=sys.stderr)
        return 1

    wave = next((w for w in estate.waves if w.get("wave") == args.wave), None)
    if wave is None:
        print(f"error: no wave {args.wave} found in manifest.waves[]", file=sys.stderr)
        return 1

    args.out.mkdir(parents=True, exist_ok=True)
    traceability: dict[str, str] = {}
    refused: list[str] = []
    scaffolded = 0
    all_todos: list[str] = []

    for key in wave.get("units", []):
        inst_id, _, box_name = key.partition(":")
        inst = estate.instances.get(inst_id)
        if inst is None or box_name not in inst.boxes:
            continue
        disposition = estate.scores.get("boxes", {}).get(key, {}).get("disposition", "JUDG")
        if disposition in REFUSED_DISPOSITIONS:
            refused.append(f"{key} ({disposition})")
            continue
        text, todos, trace = scaffold_box(inst_id, inst, box_name, estate.scores)
        (args.out / f"{inst_id.lower()}__{box_name.lower()}.py").write_text(text)
        traceability.update(trace)
        all_todos.extend(todos)
        scaffolded += 1

    (args.out / "traceability.json").write_text(json.dumps(traceability, sort_keys=True, indent=2) + "\n")

    print(f"scaffolded {scaffolded} DAG(s) from wave {args.wave} -> {args.out}", file=sys.stderr)
    if refused:
        print(f"refused {len(refused)} REDESIGN/NONE unit(s) (not scaffolded, needs human design):",
              file=sys.stderr)
        for r in refused:
            print(f"  {r}", file=sys.stderr)
    if all_todos:
        print(f"{len(all_todos)} TODO(JUDG:...) marker(s) across scaffolded DAGs -- review before Phase 3 trial",
              file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
