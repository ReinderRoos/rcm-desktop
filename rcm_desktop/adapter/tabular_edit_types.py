"""Gedeelde types voor tabulaire edit-services (slice 90)."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class CellErrorView:
    code: str
    message: str
    severity: str = "error"


@dataclass(frozen=True)
class BulkChangeResult:
    ok: bool
    errors: tuple[str, ...]
    applied_count: int


class MaterializeBlockedError(RuntimeError):
    """Raised when materialize is called while validation errors exist."""


# Back-compat alias tijdens migratie (verwijderen zodra callers bijgewerkt zijn).
FaalwijzenMaterializeBlockedError = MaterializeBlockedError
