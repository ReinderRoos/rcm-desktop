from __future__ import annotations


def _grouped_number(value: str) -> str:
    parts: list[str] = []
    while value:
        parts.append(value[-3:])
        value = value[:-3]
    return ".".join(reversed(parts)) if parts else "0"


def format_int(n: int) -> str:
    sign = "-" if n < 0 else ""
    grouped = _grouped_number(str(abs(n)))
    return f"{sign}{grouped}"


def format_float(x: float, decimals: int = 2) -> str:
    sign = "-" if x < 0 else ""
    fixed = f"{abs(x):.{decimals}f}"
    whole, _, fractional = fixed.partition(".")
    grouped_whole = _grouped_number(whole)
    return f"{sign}{grouped_whole},{fractional}"


def format_eur(x: float, decimals: int = 2) -> str:
    return f"€ {format_float(x, decimals=decimals)}"
