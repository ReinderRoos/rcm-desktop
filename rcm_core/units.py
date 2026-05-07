"""
units.py — Tijdseenheden en conversies.

Alle beschikbaarheidsberekeningen gebruiken kalenderuren (24/7).
Leeftijden en MTTF zijn altijd in jaren.
Hersteltijden en taakinspanningen worden opgegeven in de gewenste eenheid
en automatisch omgezet naar uren of jaren.
"""
from __future__ import annotations
from dataclasses import dataclass
from enum import Enum


class TimeUnit(str, Enum):
    HOURS  = "uur"
    DAYS   = "dag"
    WEEKS  = "week"
    MONTHS = "maand"
    YEARS  = "jaar"


# Kalenderuren per eenheid (geen werkuren — beschikbaarheid is 24/7)
HOURS_PER: dict[TimeUnit, float] = {
    TimeUnit.HOURS:  1.0,
    TimeUnit.DAYS:   24.0,
    TimeUnit.WEEKS:  168.0,   # 7 × 24
    TimeUnit.MONTHS: 730.0,   # 365/12 × 24, afgerond
    TimeUnit.YEARS:  8760.0,  # 365 × 24
}

HOURS_PER_YEAR = 8760.0


@dataclass
class TimeDuration:
    value: float
    unit: TimeUnit

    def to_hours(self) -> float:
        """Converteer naar kalenderuren."""
        return self.value * HOURS_PER[self.unit]

    def to_years(self) -> float:
        """Converteer naar jaren (op basis van 8760 uur/jaar)."""
        return self.to_hours() / HOURS_PER_YEAR

    def to_dict(self) -> dict:
        return {"value": self.value, "unit": self.unit.value}

    @classmethod
    def from_dict(cls, d: dict) -> "TimeDuration":
        return cls(value=float(d["value"]), unit=TimeUnit(d["unit"]))

    def __repr__(self) -> str:
        return f"TimeDuration({self.value} {self.unit.value})"
