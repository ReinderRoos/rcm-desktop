"""Genormaliseerde effect-taxonomie (slice 70 issue 11)."""

from __future__ import annotations

CATEGORIE_BESCHIKBAARHEID = "beschikbaarheid"
CATEGORIE_VEILIGHEID = "veiligheid"
CATEGORIE_KOSTEN = "kosten"
CATEGORIE_OVERIG = "overig"

_AW_TYPE_TO_CATEGORIE: dict[str, str] = {
    "schutten": CATEGORIE_BESCHIKBAARHEID,
    "keren": CATEGORIE_BESCHIKBAARHEID,
    "kruisen": CATEGORIE_BESCHIKBAARHEID,
    "spuien": CATEGORIE_BESCHIKBAARHEID,
    "vgm": CATEGORIE_VEILIGHEID,
}


def map_aw_effect_type(aw_type: str) -> tuple[str, str | None]:
    """Map ruwe AW ``RcmEffects.Type`` naar genormaliseerde categorie.

    Returns (categorie, warning_or_none).
    """
    raw = (aw_type or "").strip()
    if not raw:
        return CATEGORIE_OVERIG, "Onbekend AW effecttype: (leeg)"
    key = raw.lower()
    if key in _AW_TYPE_TO_CATEGORIE:
        return _AW_TYPE_TO_CATEGORIE[key], None
    if key == "kosten":
        return CATEGORIE_KOSTEN, None
    return CATEGORIE_OVERIG, f"Onbekend AW effecttype: {raw}"
