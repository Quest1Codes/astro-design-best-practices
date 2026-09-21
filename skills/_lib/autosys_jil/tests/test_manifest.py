import json

from autosys_jil import manifest
from autosys_jil.models import IO, Estate, Instance, Job, Provenance


def _job(name="test_job", command=None):
    prov = Provenance("<test>", 1, 0, "ACE", "insert_job")
    return Job(name=name, job_type="CMD", job_type_known=True, attrs={}, provenance=prov,
              command=command, io=IO())


def test_round_trip_is_byte_identical_on_fixture_estate(fixture_estate):
    estate = Estate(instances={"ACE": fixture_estate})
    text = manifest.to_json(estate, tool="test")
    estate2 = manifest.from_dict(json.loads(text))
    text2 = manifest.to_json(estate2, tool="test")
    assert text == text2


def test_round_trip_preserves_job_count(fixture_estate):
    estate = Estate(instances={"ACE": fixture_estate})
    text = manifest.to_json(estate, tool="test")
    estate2 = manifest.from_dict(json.loads(text))
    assert len(estate2.instances["ACE"].jobs) == len(fixture_estate.jobs)


def test_round_trip_reparses_condition_ast(fixture_estate):
    estate = Estate(instances={"ACE": fixture_estate})
    text = manifest.to_json(estate, tool="test")
    estate2 = manifest.from_dict(json.loads(text))
    cond_jobs = [j for j in fixture_estate.jobs.values() if j.condition is not None]
    assert cond_jobs
    for j in cond_jobs[:5]:
        rt = estate2.instances["ACE"].jobs[j.name]
        assert rt.condition is not None
        assert rt.condition.to_string() == j.condition.to_string()


def test_validate_clean_on_fixture_estate(fixture_estate):
    estate = Estate(instances={"ACE": fixture_estate})
    assert manifest.validate(estate) == []


def test_validate_catches_unresolved_box_name():
    job = _job()
    job.box_name = "does_not_exist"
    inst = Instance(id="ACE", jobs={"test_job": job})
    estate = Estate(instances={"ACE": inst})
    problems = manifest.validate(estate)
    assert any("box_name" in p for p in problems)


def test_redact_scrubs_connect_string_password_not_hostname():
    job = _job(command="sqlplus scott/tiger@PRODDB @script.sql")
    inst = Instance(id="ACE", jobs={"test_job": job})
    estate = Estate(instances={"ACE": inst})
    hits = manifest.redact(estate)
    assert hits.get("connect_string") == 1
    cmd = estate.instances["ACE"].jobs["test_job"].command
    assert "tiger" not in cmd
    assert "PRODDB" in cmd  # hostname is not sensitive, must survive
    assert "scott" in cmd  # username is not the redacted group either


def test_redact_scrubs_password_flag_value():
    job = _job(command="mytool -p Secr3t!")
    inst = Instance(id="ACE", jobs={"test_job": job})
    estate = Estate(instances={"ACE": inst})
    manifest.redact(estate)
    assert "Secr3t!" not in estate.instances["ACE"].jobs["test_job"].command


def test_redact_is_a_noop_on_clean_text():
    job = _job(command="/scripts/x/run.sh --date %%DATE%%")
    inst = Instance(id="ACE", jobs={"test_job": job})
    estate = Estate(instances={"ACE": inst})
    hits = manifest.redact(estate)
    assert hits == {}
    assert estate.instances["ACE"].jobs["test_job"].command == "/scripts/x/run.sh --date %%DATE%%"


def test_upgrade_v1_produces_loadable_schema_2_manifest():
    v1 = {
        "jobs": {"old_job": {"job_type": "CMD", "command": "echo hi", "condition": "success(other_job)"}},
        "unknown_job_types": ["ZZZ"], "unknown_attributes": ["weird_attr"],
    }
    upgraded = manifest.upgrade_v1(v1)
    assert upgraded["schema_version"] == manifest.SCHEMA_VERSION
    estate = manifest.from_dict(upgraded)
    job = estate.instances["DEFAULT"].jobs["old_job"]
    assert job.job_type == "CMD"
    assert job.condition is not None and job.condition.to_string() == "success(other_job)"
    assert "ZZZ" in estate.instances["DEFAULT"].unknowns.job_types


def test_from_dict_refuses_newer_major_schema_version():
    d = {"schema_version": "99.0", "instances": {}}
    try:
        manifest.from_dict(d)
        assert False, "should have raised ManifestVersionError"
    except manifest.ManifestVersionError:
        pass


def test_add_evidence_hashes_file(tmp_path):
    p = tmp_path / "artifact.txt"
    p.write_text("hello world")
    estate = Estate()
    ev = manifest.add_evidence(estate, p, kind="jil_export")
    import hashlib
    assert ev.sha256 == hashlib.sha256(b"hello world").hexdigest()
    assert estate.evidence == [ev]
