"""Qt-vrije tabel-filter parser (slice 81)."""

from __future__ import annotations

import re
from dataclasses import dataclass
from enum import Enum
from typing import Callable


class TableColumnFilterKind(str, Enum):
    TEXT = "text"
    BOOL = "bool"
    NUMERIC = "numeric"


@dataclass(frozen=True)
class TextFilterPredicate:
    needle: str

    def matches(self, raw_value: object) -> bool:
        if not self.needle:
            return True
        hay = _normalize_text(raw_value)
        return self.needle in hay


@dataclass(frozen=True)
class BoolFilterPredicate:
    required: bool | None = None

    def matches(self, raw_value: object) -> bool:
        if self.required is None:
            return True
        return bool(raw_value) == self.required


@dataclass(frozen=True)
class NumericFilterPredicate:
    _match: Callable[[float], bool] | None = None

    def matches(self, raw_value: object) -> bool:
        if self._match is None:
            return True
        try:
            value = float(raw_value)
        except (TypeError, ValueError):
            return False
        return self._match(value)


@dataclass(frozen=True)
class ParsedNumericFilter:
    predicate: NumericFilterPredicate
    invalid: bool = False


def _normalize_text(value: object) -> str:
    return str(value).casefold().strip()


def parse_text_filter(raw: str) -> TextFilterPredicate:
    return TextFilterPredicate(needle=_normalize_text(raw))


def parse_bool_filter(required: bool | None) -> BoolFilterPredicate:
    return BoolFilterPredicate(required=required)


def _parse_number(raw: str) -> float:
    return float(raw.strip().replace(",", "."))


def _exact_match(target: float) -> Callable[[float], bool]:
    return lambda value: abs(value - target) < 1e-9


def parse_numeric_filter(raw: str) -> ParsedNumericFilter:
    text = raw.strip()
    if not text:
        return ParsedNumericFilter(predicate=NumericFilterPredicate())

    range_match = re.fullmatch(r"(.+?)\.\.(.+)", text)
    if range_match is not None:
        try:
            lo = _parse_number(range_match.group(1))
            hi = _parse_number(range_match.group(2))
        except ValueError:
            return ParsedNumericFilter(
                predicate=NumericFilterPredicate(),
                invalid=True,
            )
        return ParsedNumericFilter(
            predicate=NumericFilterPredicate(_match=lambda v, lo=lo, hi=hi: lo <= v <= hi)
        )

    for pattern, op in (
        (r">=(.+)", lambda v, t: v >= t),
        (r"<=(.+)", lambda v, t: v <= t),
        (r">(.+)", lambda v, t: v > t),
        (r"<(.+)", lambda v, t: v < t),
        (r"=(.+)", lambda v, t: abs(v - t) < 1e-9),
    ):
        match = re.fullmatch(pattern, text)
        if match is not None:
            try:
                threshold = _parse_number(match.group(1))
            except ValueError:
                return ParsedNumericFilter(
                    predicate=NumericFilterPredicate(),
                    invalid=True,
                )
            return ParsedNumericFilter(
                predicate=NumericFilterPredicate(_match=lambda v, op=op, threshold=threshold: op(v, threshold))
            )

    try:
        exact = _parse_number(text)
    except ValueError:
        return ParsedNumericFilter(
            predicate=NumericFilterPredicate(),
            invalid=True,
        )
    return ParsedNumericFilter(predicate=NumericFilterPredicate(_match=_exact_match(exact)))


def row_matches_text_filters(
    raw_values_by_column: dict[int, object],
    filters_by_column: dict[int, TextFilterPredicate],
) -> bool:
    """EN-combinatie: elke actieve tekstfilter moet matchen."""
    for col, pred in filters_by_column.items():
        if not pred.matches(raw_values_by_column.get(col, "")):
            return False
    return True


def row_matches_column_filters(
    raw_values_by_column: dict[int, object],
    *,
    text: dict[int, TextFilterPredicate],
    bool_: dict[int, BoolFilterPredicate],
    numeric: dict[int, NumericFilterPredicate],
) -> bool:
    """EN-combinatie over tekst-, bool- en numerieke kolomfilters."""
    for col, pred in text.items():
        if not pred.matches(raw_values_by_column.get(col, "")):
            return False
    for col, pred in bool_.items():
        if not pred.matches(raw_values_by_column.get(col, False)):
            return False
    for col, pred in numeric.items():
        if not pred.matches(raw_values_by_column.get(col, 0)):
            return False
    return True
