"""
config.py — Projectconfiguratie voor het RCM-model.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class RCMConfig:
    # Levensduur en tijdshorizon
    lifecycle_years: float = 80.0
    modeljaar: int = 2026  # standaard huidig jaar; pas aan zonder bouwdelen te wijzigen

    # Monte Carlo instellingen
    monte_carlo_n: int = 10_000
    monte_carlo_seed: Optional[int] = None

    # Verouderingsstandaarden (kunnen per faalwijze worden overschreven)
    default_mttf_multiplier: float = 1.25   # MTTF = 1,25 × ontwerpleeftijd (OLD)
    default_sigma_fraction: float = 0.15    # sigma = 0,15 × MTTF

    def to_dict(self) -> dict:
        return {
            "lifecycle_years": self.lifecycle_years,
            "modeljaar": self.modeljaar,
            "monte_carlo_n": self.monte_carlo_n,
            "monte_carlo_seed": self.monte_carlo_seed,
            "default_mttf_multiplier": self.default_mttf_multiplier,
            "default_sigma_fraction": self.default_sigma_fraction,
        }

    @classmethod
    def from_dict(cls, d: dict) -> "RCMConfig":
        known = {f.name for f in cls.__dataclass_fields__.values()}
        filtered = {k: v for k, v in d.items() if k in known}
        return cls(**filtered)
