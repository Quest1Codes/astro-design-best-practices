"""Registry completeness against the fixture corpus [spec §1.13 test_registry_coverage.py].

The 54-file customer-shaped fixture estate is expected to be (almost) fully covered by the
registry generated from the AutoSys 12.0 PDF -- any job type / attribute NOT covered must be
one of the small, explained set below (verified in the HANDOFF §3b diagnostic: these are
genuinely non-canonical names present in the fixture data itself, not gaps in `build_registry.py`
extraction). If this test starts failing with NEW names, that is a real registry gap to
investigate, not a fixture to "fix" the assertion around.
"""
from autosys_jil import registry

# From the HANDOFF §3b diagnostic: FILEWATCH is used in the fixtures as a job_type, but the
# real AutoSys 12.0 job type is `FW` [AS p.2549] -- FILEWATCH does not exist in the product.
EXPECTED_UNKNOWN_JOB_TYPES = {"FILEWATCH"}

# `host` (real machine attribute is `node_name` [AS p.2873]) and `send_report`/`job_on_hold`/
# `job_on_ice` (JOB_ON_HOLD/JOB_ON_ICE are sendevent EVENTS [AS commands p.2295], not JIL
# attributes) are not real AutoSys 12.0 fields.
EXPECTED_UNKNOWN_ATTRIBUTES = {"host", "send_report", "job_on_hold", "job_on_ice"}


def test_fixture_unknown_job_types_are_exactly_the_explained_set(fixture_estate):
    assert set(fixture_estate.unknowns.job_types) == EXPECTED_UNKNOWN_JOB_TYPES


def test_fixture_unknown_attributes_are_exactly_the_explained_set(fixture_estate):
    assert set(fixture_estate.unknowns.attributes) == EXPECTED_UNKNOWN_ATTRIBUTES


def test_every_job_type_used_in_fixtures_other_than_explained_set_is_registered(fixture_estate):
    used = {j.job_type for j in fixture_estate.jobs.values()}
    unregistered = used - set(registry.job_types()) - EXPECTED_UNKNOWN_JOB_TYPES
    assert unregistered == set()


def test_pdf_example_job_types_are_all_registered(pdf_example_files):
    from autosys_jil.parser import parse_files
    inst = parse_files(pdf_example_files, instance="PDF")
    used = {j.job_type for j in inst.jobs.values()}
    # 'C' is a legal alias for CMD that resolve_job_type already maps -- any survivor here
    # means alias resolution silently failed to recognise a real job_type token.
    unregistered = used - set(registry.job_types())
    assert unregistered == set(), f"unregistered job types found in PDF examples: {unregistered}"


def test_registry_has_state_machine_coverage():
    states = registry.states()
    for required in ("SUCCESS", "FAILURE", "TERMINATED", "RUNNING", "ON_HOLD", "ON_ICE"):
        assert required in states, f"{required} missing from states.json"


def test_registry_version_is_stable_string():
    v1 = registry.registry_version()
    v2 = registry.registry_version()
    assert v1 == v2 and v1.startswith("jt")
