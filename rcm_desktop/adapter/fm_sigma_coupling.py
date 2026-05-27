"""MTTF/sigma-koppeling voor de faalwijze-editor (15%-standaard)."""

from __future__ import annotations

DEFAULT_SIGMA_FRACTION = 0.15


def coupled_sigma(mttf_jaar: float) -> float:
    return DEFAULT_SIGMA_FRACTION * float(mttf_jaar)


def sigma_epsilon(mttf_jaar: float) -> float:
    return max(1e-6, 0.001 * float(mttf_jaar))


def is_sigma_manual(mttf_jaar: float, sigma_jaar: float) -> bool:
    """True als sigma bewust afwijkt van 15% × MTTF."""
    mttf = float(mttf_jaar)
    sigma = float(sigma_jaar)
    if mttf <= 0:
        return sigma > 0
    expected = coupled_sigma(mttf)
    return abs(sigma - expected) > sigma_epsilon(mttf)
