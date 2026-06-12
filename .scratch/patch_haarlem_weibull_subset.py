"""One-off: seed Haarlem demo with AWZI Weibull bibliotheek + subset (slice 51 issue 04)."""
from __future__ import annotations

import json
from pathlib import Path

path = Path("tests/fixtures/awzi_haarlem_waarderpolder_demo.rcm.json")
data = json.loads(path.read_text(encoding="utf-8"))
bron = "NIST/AWZI-HWP faalmodeltabel (demomodel slice 51); MTTF = 1,2 x OLT"
data["bibliotheek"]["BIB-AWZI-AGING-POMP"] = {
    "bibliotheek_id": "BIB-AWZI-AGING-POMP",
    "categorie": "aging_defaults",
    "omschrijving": "AWZI pomp / roerder — Weibull shape default",
    "waarde": "Weibull 2p; beta=2.5; wear-out mechanisch",
    "bron": bron,
    "toelichting": "Representatieve HWP-component; FM materialiseert beta_jaar.",
}
data["bibliotheek"]["BIB-AWZI-AGING-KLEP"] = {
    "bibliotheek_id": "BIB-AWZI-AGING-KLEP",
    "categorie": "aging_defaults",
    "omschrijving": "AWZI klep / afsluiter — Weibull shape default",
    "waarde": "Weibull 2p; beta=3.0; slijtage openingscycli",
    "bron": bron,
    "toelichting": "Representatieve HWP-component; FM materialiseert beta_jaar.",
}
data["bibliotheek"]["BIB-AWZI-AGING-MECH"] = {
    "bibliotheek_id": "BIB-AWZI-AGING-MECH",
    "categorie": "aging_defaults",
    "omschrijving": "AWZI mechanische aandrijving — Weibull shape default",
    "waarde": "Weibull 2p; beta=2.8; lagers/afdichtingen",
    "bron": bron,
    "toelichting": "Representatieve HWP-component; FM materialiseert beta_jaar.",
}
refs: list[tuple[str, float]] = [
    ("BIB-AWZI-AGING-POMP", 2.5),
    ("BIB-AWZI-AGING-KLEP", 3.0),
    ("BIB-AWZI-AGING-MECH", 2.8),
]
candidates = sorted(
    fm_id
    for fm_id, fm in data["faalwijzes"].items()
    if fm.get("failure_type") == "aging"
    and "slice 42" in (fm.get("aanname_faalmodel") or "").lower()
)
subset = candidates[:20]
for i, fm_id in enumerate(subset):
    bib, beta = refs[i % len(refs)]
    fm = data["faalwijzes"][fm_id]
    fm["aging_distribution"] = "weibull_2p"
    fm["beta_jaar"] = beta
    fm["library_ref"] = bib
    mttf = fm.get("mttf_jaar")
    fm["aanname_faalmodel"] = (
        f"Weibull 2p; beta={beta} ({bib}); MTTF={mttf} jr; slice 51 demo-subset."
    )
path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
weibull_count = sum(
    1 for fm in data["faalwijzes"].values() if fm.get("aging_distribution") == "weibull_2p"
)
print(f"weibull_count={weibull_count} subset_size={len(subset)}")
