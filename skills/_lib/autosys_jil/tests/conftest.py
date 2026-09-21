from __future__ import annotations

from pathlib import Path

import pytest

FIXTURES = Path(__file__).resolve().parent / "fixtures"
JIL_FILES = sorted((FIXTURES / "jil_files").glob("*.jil"))
PDF_EXAMPLES = sorted((FIXTURES / "pdf_examples").glob("*.jil"))


@pytest.fixture(scope="session")
def jil_files() -> list[Path]:
    return JIL_FILES


@pytest.fixture(scope="session")
def pdf_example_files() -> list[Path]:
    return PDF_EXAMPLES


@pytest.fixture(scope="session")
def fixture_estate():
    from autosys_jil.parser import parse_files
    return parse_files(JIL_FILES, instance="ACE")
