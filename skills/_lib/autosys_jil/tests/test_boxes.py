from autosys_jil.boxes import box_metrics, build_tree, descendants, top_level_boxes
from autosys_jil.parser import finalize, parse_text


def _inst(text):
    inst = parse_text(text, file="<test>")
    finalize(inst)
    return inst


def test_simple_tree_depth_and_children():
    text = """
insert_job: top_box
job_type: box

insert_job: child_job
job_type: CMD
box_name: top_box
command: echo hi
"""
    inst = _inst(text)
    boxes = inst.boxes
    assert "top_box" in boxes
    assert boxes["top_box"].children == ["child_job"]
    assert boxes["top_box"].depth == 0


def test_nested_boxes_depth():
    text = """
insert_job: outer
job_type: box

insert_job: inner
job_type: box
box_name: outer

insert_job: leaf
job_type: CMD
box_name: inner
command: echo hi
"""
    inst = _inst(text)
    assert inst.boxes["outer"].depth == 0
    assert inst.boxes["inner"].depth == 1
    assert descendants(inst.boxes, inst.jobs, "outer") == ["leaf"]


def test_orphan_box_name_is_inferred_and_flagged():
    text = """
insert_job: child_job
job_type: CMD
box_name: nonexistent_box
command: echo hi
"""
    inst = _inst(text)
    assert inst.boxes["nonexistent_box"].inferred is True
    assert any(r["kind"] == "box_name" for r in inst.unknowns.unresolved_refs)


def test_single_child_flag():
    text = """
insert_job: b1
job_type: box

insert_job: only_child
job_type: CMD
box_name: b1
command: echo hi
"""
    inst = _inst(text)
    metrics = box_metrics(inst.boxes, inst.jobs)
    assert metrics["b1"]["single_child"] is True


def test_top_level_boxes():
    text = """
insert_job: b1
job_type: box

insert_job: b2
job_type: box
box_name: b1
"""
    inst = _inst(text)
    assert top_level_boxes(inst.boxes) == ["b1"]


def test_cross_box_condition_edges():
    text = """
insert_job: box_a
job_type: box

insert_job: box_a_job
job_type: CMD
box_name: box_a
command: echo a

insert_job: box_b
job_type: box

insert_job: box_b_job
job_type: CMD
box_name: box_b
command: echo b
condition: success(box_a_job)
"""
    inst = _inst(text)
    metrics = box_metrics(inst.boxes, inst.jobs)
    assert metrics["box_b"]["cross_box_condition_edges_in"] == 1
    assert metrics["box_a"]["cross_box_condition_edges_out"] == 1
