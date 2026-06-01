"""Normalisatie van optionele FK-waarden in de adapterlaag."""

from __future__ import annotations

from typing import Any


def normalize_optional_fk(value: Any) -> str | None:
    """Map lege, None, ``"None"`` en ``"null"`` naar ``None``; anders gestripte id."""
    if value is None:
        return None
    s = str(value).strip()
    if s == "" or s.lower() in ("none", "null"):
        return None
    return s


def is_empty_fk_key(value: Any) -> bool:
    """Of een waarde als lege FK telt (inclusief legacy ``None``-strings)."""
    return normalize_optional_fk(value) is None
