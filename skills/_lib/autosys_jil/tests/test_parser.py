from pathlib import Path

from autosys_jil.parser import parse_files, parse_text

FIXTURES = Path(__file__).parent / "fixtures"


def test_all_54_fixture_files_parse_without_exception(jil_files):
    assert len(jil_files) == 54
    inst = parse_files(jil_files, instance="ACE")
    assert len(inst.jobs) > 0


def test_fixture_estate_has_expected_shape(fixture_estate):
    assert len(fixture_estate.jobs) == 297
    box_jobs = [j for j in fixture_estate.jobs.values() if j.is_box]
    assert len(box_jobs) == 50
    assert len(fixture_estate.boxes) >= 50


def test_fixture_estate_has_zero_condition_parse_failures(fixture_estate):
    assert fixture_estate.unknowns.condition_parse_failures == []


def test_fixture_estate_has_zero_unresolved_refs(fixture_estate):
    assert fixture_estate.unknowns.unresolved_refs == []


def test_all_534_pdf_example_blocks_parse_without_exception(pdf_example_files):
    assert len(pdf_example_files) > 400
    for f in pdf_example_files:
        parse_files([f], instance="PDF")  # must not raise


def test_job_type_alias_resolution():
    text = "insert_job: a\njob_type: c\n\ninsert_job: b\njob_type: b\n\ninsert_job: c\njob_type: f\n"
    inst = parse_text(text, file="<test>")
    assert inst.jobs["a"].job_type == "CMD" and inst.jobs["a"].job_type_known
    assert inst.jobs["b"].job_type == "BOX" and inst.jobs["b"].job_type_known
    assert inst.jobs["c"].job_type == "FW" and inst.jobs["c"].job_type_known


def test_missing_job_type_defaults_to_cmd():
    inst = parse_text("insert_job: a\ncommand: echo hi\n", file="<test>")
    assert inst.jobs["a"].job_type == "CMD"


def test_unknown_job_type_is_flagged_not_dropped():
    inst = parse_text("insert_job: a\njob_type: NOTAREALTYPE\n", file="<test>")
    assert inst.jobs["a"].job_type == "NOTAREALTYPE"
    assert not inst.jobs["a"].job_type_known
    assert "NOTAREALTYPE" in inst.unknowns.job_types


def test_unknown_attribute_kept_in_extras_and_unknowns():
    inst = parse_text("insert_job: a\njob_type: CMD\nsome_made_up_attr: 1\n", file="<test>")
    assert inst.jobs["a"].extras["some_made_up_attr"] == "1"
    assert "a" in inst.unknowns.attributes["some_made_up_attr"]


def test_update_job_merges_and_records_provenance():
    text = "insert_job: a\njob_type: CMD\nn_retrys: 1\n\nupdate_job: a\nn_retrys: 3\n"
    inst = parse_text(text, file="<test>")
    job = inst.jobs["a"]
    assert job.sla.n_retrys == 3
    assert len(job.modified_by) == 1
    assert job.modified_by[0].subcommand == "update_job"


def test_override_job_kept_separately_not_merged():
    text = "insert_job: a\njob_type: CMD\ncommand: real\n\noverride_job: a\ncommand: overridden\n"
    inst = parse_text(text, file="<test>")
    assert inst.jobs["a"].command == "real"  # override does NOT merge into the live definition
    assert len(inst.overrides) == 1
    assert inst.overrides[0]["job"] == "a"
    assert inst.overrides[0]["attrs"]["command"] == "overridden"


def test_delete_job_marks_deleted_not_removed():
    text = "insert_job: a\njob_type: CMD\n\ndelete_job: a\n"
    inst = parse_text(text, file="<test>")
    assert "a" in inst.jobs
    assert inst.jobs["a"].deleted is True


def test_synthetic_override_and_update_fixture():
    inst = parse_files([FIXTURES / "synthetic" / "override_and_update.jil"], instance="ACE")
    job = inst.jobs["monthly_close"]
    assert job.sla.n_retrys == 3  # from update_job
    assert job.sla.max_run_alarm == 120  # from update_job
    assert job.command == "/scripts/fin/monthly_close.sh"  # override_job does not merge
    assert len(inst.overrides) == 1


def test_typed_normalization_days_of_week_and_bool():
    text = ("insert_job: a\njob_type: CMD\ndate_conditions: 1\ndays_of_week: mo,we,fr\n"
           "alarm_if_fail: n\n")
    inst = parse_text(text, file="<test>")
    job = inst.jobs["a"]
    assert job.schedule.date_conditions is True
    assert job.schedule.days_of_week == ["mo", "we", "fr"]
    assert job.alerting.alarm_if_fail is False


def test_attribute_on_unsupported_job_type_warns():
    # watch_file is an FW attribute, not a CMD attribute [AS p.2549]
    text = "insert_job: a\njob_type: CMD\nwatch_file: /tmp/x\n"
    inst = parse_text(text, file="<test>")
    assert any("watch_file" in w for w in inst.jobs["a"].warnings)


def test_multi_instance_cross_instance_condition_resolves():
    ace = FIXTURES / "multi_instance" / "ACE.jil"
    prd = FIXTURES / "multi_instance" / "PRD.jil"
    inst_ace = parse_files([ace], instance="ACE")
    inst_prd = parse_files([prd], instance="PRD")
    job = inst_prd.jobs["prd_settlement_consume"]
    assert job.condition is not None
    assert job.condition.cross_instance_refs == ["ace_settlement_feed^ACE"]
    assert "ACE" in inst_prd.xinsts


def test_hidden_sendevent_fixture_parses_and_has_no_jil_visible_dependency():
    inst = parse_files([FIXTURES / "synthetic" / "hidden_sendevent.jil"], instance="ACE")
    downstream = inst.jobs["downstream_reconcile"]
    assert downstream.condition is None  # dependency is hidden inside the OTHER job's command
    assert "sendevent" in inst.jobs["nightly_trigger"].command


def test_windows_estate_fixture_parses():
    inst = parse_files([FIXTURES / "synthetic" / "windows_estate.jil"], instance="ACE")
    assert inst.jobs["win_nightly_extract"].owner == "CORP\\svc_autosys"
    assert "cmd /c" in inst.jobs["win_nightly_extract"].command
