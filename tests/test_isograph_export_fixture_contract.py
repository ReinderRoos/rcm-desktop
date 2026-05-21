"""Contract tests for Isograph RCM-Cost export layout (phase 0 gate)."""

from __future__ import annotations

from pathlib import Path

import pytest

from rcm_core.isograph_export_contract import (
    EXPECTED_SHEET_NAMES,
    MUST_V1_SHEET_HEADERS,
    load_workbook_headers,
)

FIXTURE = Path(__file__).resolve().parent / "fixtures" / "RCMCostdata export_leeg.xlsx"
MATRIX = (
    Path(__file__).resolve().parents[1]
    / ".scratch/rcm-desktop-slice35-rcm-cost-excel-import/IMPORT_MATRIX.md"
)


@pytest.fixture(scope="module")
def fixture_headers() -> dict[str, tuple[str, ...]]:
    return load_workbook_headers(FIXTURE)


def test_fixture_has_all_expected_sheets(fixture_headers: dict[str, tuple[str, ...]]) -> None:
    assert set(fixture_headers) == EXPECTED_SHEET_NAMES


def test_must_v1_sheets_have_required_columns(fixture_headers: dict[str, tuple[str, ...]]) -> None:
    for sheet, required in MUST_V1_SHEET_HEADERS.items():
        present = set(fixture_headers[sheet])
        missing = [col for col in required if col not in present]
        assert not missing, f"{sheet} missing columns: {missing}"


def test_import_matrix_document_exists() -> None:
    assert MATRIX.is_file(), "IMPORT_MATRIX.md must exist (issue 01 deliverable)"
