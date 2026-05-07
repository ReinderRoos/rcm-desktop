from __future__ import annotations

from rcm_desktop.formatting import format_eur, format_float, format_int


def test_format_int_uses_dutch_thousands_separator():
    assert format_int(0) == "0"
    assert format_int(12345) == "12.345"


def test_format_float_uses_dutch_decimal_comma():
    assert format_float(0) == "0,00"
    assert format_float(1234.5) == "1.234,50"


def test_format_eur_prefixes_currency_symbol():
    assert format_eur(0) == "€ 0,00"
    assert format_eur(1200.0) == "€ 1.200,00"
