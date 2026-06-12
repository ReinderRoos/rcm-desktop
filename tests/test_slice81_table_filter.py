"""Slice 81 issue 01 — tabel-filter parser + proxy."""

from __future__ import annotations

import pytest

pytest.importorskip("PySide6")

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication

from rcm_desktop.adapter.fm_results_table_model import FMResultsTableModel, RAW_ROLE
from rcm_desktop.adapter.result_view_service import FMResultRow
from rcm_desktop.adapter.table_column_filter_proxy import TableColumnFilterProxy
from rcm_desktop.adapter.table_filter_parser import (
    BoolFilterPredicate,
    parse_numeric_filter,
    parse_text_filter,
    row_matches_column_filters,
    row_matches_text_filters,
)


@pytest.mark.parametrize(
    ("raw", "value", "expected"),
    [
        ("", "Pomp A", True),
        ("pomp", "Pomp A", True),
        ("POMP", "pomp a", True),
        ("xyz", "Pomp A", False),
    ],
)
def test_text_filter_case_insensitive_substring(raw, value, expected) -> None:
    pred = parse_text_filter(raw)
    assert pred.matches(value) is expected


def _row(fm_id: str, bouwdeel: str, oms: str) -> FMResultRow:
    return FMResultRow(
        fm_id=fm_id,
        faalwijze_omschrijving=oms,
        pbs_id="PBS-1",
        bouwdeel_naam=bouwdeel,
        expected_failures=1.0,
        expected_total_downtime_hr=1.0,
        total_cost_eur=1.0,
    )


def test_en_combination_over_two_text_columns() -> None:
    preds = {
        1: parse_text_filter("pomp"),
        2: parse_text_filter("leak"),
    }
    assert row_matches_text_filters({1: "Pomp", 2: "Leak"}, preds) is True
    assert row_matches_text_filters({1: "Motor", 2: "Leak"}, preds) is False


@pytest.mark.parametrize(
    ("raw", "value", "expected"),
    [
        (">100", 150.0, True),
        (">100", 50.0, False),
        ("<=0.5", 0.5, True),
        ("<=0.5", 0.6, False),
        ("10..50", 25.0, True),
        ("10..50", 5.0, False),
        ("123", 123.0, True),
        ("123", 124.0, False),
        ("0,5", 0.5, True),
        ("", 999.0, True),
    ],
)
def test_numeric_filter_expressions(raw, value, expected) -> None:
    pred = parse_numeric_filter(raw).predicate
    assert pred.matches(value) is expected


def test_numeric_filter_invalid_expression_matches_all() -> None:
    parsed = parse_numeric_filter(">>100")
    assert parsed.invalid is True
    assert parsed.predicate.matches(0.0) is True
    assert parsed.predicate.matches(9999.0) is True


def test_combined_text_bool_numeric_filters_and() -> None:
    text = {1: parse_text_filter("pomp")}
    bool_ = {3: BoolFilterPredicate(required=True)}
    numeric = {7: parse_numeric_filter(">100").predicate}
    row_ok = {1: "Pomp A", 3: True, 7: 150.0}
    row_bad_text = {1: "Motor", 3: True, 7: 150.0}
    assert row_matches_column_filters(row_ok, text=text, bool_=bool_, numeric=numeric) is True
    assert row_matches_column_filters(row_bad_text, text=text, bool_=bool_, numeric=numeric) is False


def test_filter_proxy_numeric_kosten_column() -> None:
    app = QApplication.instance() or QApplication([])
    del app
    rows = [
        FMResultRow(
            fm_id="FM-1",
            faalwijze_omschrijving="A",
            pbs_id="PBS-1",
            bouwdeel_naam="Pomp",
            expected_failures=1.0,
            expected_total_downtime_hr=1.0,
            total_cost_eur=50.0,
        ),
        FMResultRow(
            fm_id="FM-2",
            faalwijze_omschrijving="B",
            pbs_id="PBS-1",
            bouwdeel_naam="Motor",
            expected_failures=1.0,
            expected_total_downtime_hr=1.0,
            total_cost_eur=200.0,
        ),
    ]
    source = FMResultsTableModel(rows)
    filter_proxy = TableColumnFilterProxy(
        text_columns=frozenset(),
        numeric_columns=frozenset({7}),
        raw_role=RAW_ROLE,
    )
    filter_proxy.setSourceModel(source)
    filter_proxy.set_numeric_filter(7, ">100")
    visible = [
        filter_proxy.data(filter_proxy.index(r, 0), RAW_ROLE)
        for r in range(filter_proxy.rowCount())
    ]
    assert visible == ["FM-2"]


def test_filter_proxy_stacked_with_sort() -> None:
    app = QApplication.instance() or QApplication([])
    del app
    rows = [
        _row("FM-1", "Pomp A", "Leak"),
        _row("FM-2", "Motor", "Leak"),
        _row("FM-3", "Pomp B", "Crack"),
    ]
    source = FMResultsTableModel(rows)
    filter_proxy = TableColumnFilterProxy(text_columns=frozenset({1, 2}), raw_role=RAW_ROLE)
    filter_proxy.setSourceModel(source)
    filter_proxy.set_text_filter(1, "pomp")
    visible = [
        filter_proxy.data(filter_proxy.index(r, 0), RAW_ROLE)
        for r in range(filter_proxy.rowCount())
    ]
    assert visible == ["FM-1", "FM-3"]
