"""Box-tree reconstruction and metrics.

Deterministic; no I/O.

Facts [AS p.2422 box_name; p.2400 BOX job type]: children declare membership via
`box_name`; the box job itself carries no child list. A box may be nested in another box.
"""
from __future__ import annotations

from .models import Box, Job


def build_tree(jobs: dict[str, Job]) -> dict[str, Box]:
    boxes: dict[str, Box] = {}
    for name, job in jobs.items():
        if job.is_box and not job.deleted:
            boxes[name] = Box(name=name)
    for name, job in jobs.items():
        if job.deleted or not job.box_name:
            continue
        parent = job.box_name
        if parent not in boxes:
            boxes[parent] = Box(name=parent, inferred=True)
        boxes[parent].children.append(name)
        if job.is_box and name in boxes:
            boxes[name].parent = parent
    for b in boxes.values():
        b.children.sort()
    # depth (0 = top-level). Guard against cycles from stale exports.
    for b in boxes.values():
        depth, seen, cur = 0, {b.name}, b.parent
        while cur is not None and cur in boxes and cur not in seen:
            depth += 1
            seen.add(cur)
            cur = boxes[cur].parent
        b.depth = depth
    return boxes


def top_level_boxes(boxes: dict[str, Box]) -> list[str]:
    return sorted(n for n, b in boxes.items() if b.parent is None)


def descendants(boxes: dict[str, Box], jobs: dict[str, Job], name: str) -> list[str]:
    """All jobs (transitively) inside a box, excluding nested box jobs themselves."""
    out: list[str] = []
    stack = [name]
    seen: set[str] = set()
    while stack:
        cur = stack.pop()
        if cur in seen or cur not in boxes:
            continue
        seen.add(cur)
        for child in boxes[cur].children:
            if child in boxes:
                stack.append(child)
            else:
                out.append(child)
    return sorted(out)


def box_metrics(boxes: dict[str, Box], jobs: dict[str, Job]) -> dict[str, dict]:
    """Per-box metrics used by scoring and the inventory report."""
    out: dict[str, dict] = {}
    for name, box in boxes.items():
        desc = descendants(boxes, jobs, name)
        child_jobs = [jobs[c] for c in box.children if c in jobs]
        machines = sorted({m for j in child_jobs for m in j.load.machine})
        owners = sorted({j.owner for j in child_jobs if j.owner})
        box_job = jobs.get(name)
        children_with_schedule = [j.name for j in child_jobs if j.schedule.has_schedule]
        cross_in = cross_out = 0
        for j in child_jobs:
            if j.condition is None:
                continue
            for ref in j.condition.referenced_job_names:
                rj = jobs.get(ref)
                if rj is not None and rj.box_name != name and ref != name:
                    cross_in += 1
        for jname, j in jobs.items():
            if j.condition is None or j.box_name == name:
                continue
            if any(r in set(box.children) | {name} for r in j.condition.referenced_job_names):
                cross_out += 1
        out[name] = {
            "depth": box.depth,
            "parent": box.parent,
            "child_count": len(box.children),
            "descendant_count": len(desc),
            "nested_boxes": sorted(c for c in box.children if c in boxes),
            "has_nested_boxes": any(c in boxes for c in box.children),
            "single_child": len(box.children) == 1,
            "inferred": box.inferred,
            "machines": machines,
            "mixed_machines": len(machines) > 1,
            "owners": owners,
            "mixed_owners": len(owners) > 1,
            "box_has_schedule": bool(box_job and box_job.schedule.has_schedule),
            "children_with_own_schedule": children_with_schedule,
            "cross_box_condition_edges_in": cross_in,
            "cross_box_condition_edges_out": cross_out,
        }
    return out
