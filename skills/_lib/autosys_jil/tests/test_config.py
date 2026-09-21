from pathlib import Path

from autosys_jil import config

FIXTURES = Path(__file__).parent / "fixtures" / "synthetic"


def test_parse_config_autoserv_hash_is_a_comment():
    text = "AUTOSERV=ACE\n# this is a comment\nMaxRestartTrys=5\n"
    cfg = config.parse_config_autoserv(text)
    assert cfg == {"AUTOSERV": "ACE", "MaxRestartTrys": "5"}


def test_parse_config_autoserv_trailing_comment_stripped():
    cfg = config.parse_config_autoserv("MaxRestartTrys=5   # override default\n")
    assert cfg["MaxRestartTrys"] == "5"


def test_parse_config_fixture_file():
    cfg = config.parse_config_autoserv((FIXTURES / "config.ACE").read_text())
    assert cfg["AUTOSERV"] == "ACE"
    assert cfg["MaxRestartTrys"] == "5"
    assert cfg["RestartConstant"] == "30"


def test_semantic_params_enriches_known_keys_with_pdf_page():
    cfg = {"MaxRestartTrys": "5", "SomeUnknownParam": "xyz"}
    sp = config.semantic_params(cfg)
    assert "MaxRestartTrys" in sp and sp["MaxRestartTrys"]["pdf_page"] == 892
    assert "SomeUnknownParam" not in sp


def test_semantic_params_on_fixture_file():
    cfg = config.parse_config_autoserv((FIXTURES / "config.ACE").read_text())
    sp = config.semantic_params(cfg)
    assert set(sp) >= {"MaxRestartTrys", "RestartConstant", "RestartFactor", "GlobalAutoHold"}


def test_parse_agentparm_hash_and_bang_are_comments():
    text = "# comment\n! also a comment\nplugin.oracle.enabled=true\n"
    ap = config.parse_agentparm(text)
    assert ap == {"plugin.oracle.enabled": "true"}


def test_parse_agentparm_fixture_file():
    ap = config.parse_agentparm((FIXTURES / "agentparm_oracle.txt").read_text())
    assert ap["plugin.oracle.enabled"] == "true"


def test_agent_capabilities_detects_oracle_and_ftp():
    ap = config.parse_agentparm((FIXTURES / "agentparm_oracle.txt").read_text())
    caps = config.agent_capabilities(ap)
    assert "erp-oracle" in caps
    assert "file-transfer" in caps


def test_agent_capabilities_empty_for_no_plugin_hints():
    caps = config.agent_capabilities({"agent.name": "x", "agent.port": "7501"})
    assert caps == set()
