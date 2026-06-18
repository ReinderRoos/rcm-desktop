"""Patch Haarlem demo fixture: NMF-validator + import-klare aging-defaults (slice C)."""
from __future__ import annotations

import json
from pathlib import Path

from rcm_core.models import RCMProject, TaskType
from rcm_core.validators import validate_project

path = Path("tests/fixtures/awzi_haarlem_waarderpolder_demo.rcm.json")
data = json.loads(path.read_text(encoding="utf-8"))

proj = RCMProject.from_dict(data)
needs_evident: list[str] = []
for fm_id, fm in proj.faalwijzes.items():
    if fm.is_evident is not False:
        continue
    has_detection = any(
        pm.fm_id == fm_id and pm.taak_type in (TaskType.IN, TaskType.TST)
        for pm in proj.pm_tasks.values()
    )
    if not has_detection:
        needs_evident.append(fm_id)

for fm_id in needs_evident:
    data["faalwijzes"][fm_id]["is_evident"] = True
    note = (
        "is_evident=true: geen IN/TST in demo; validator FM_NMF_REQUIRES_TEST (slice C)."
    )
    existing = (data["faalwijzes"][fm_id].get("notes") or "").strip()
    if note not in existing:
        data["faalwijzes"][fm_id]["notes"] = f"{existing} {note}".strip() if existing else note

cfg = data.setdefault("config", {})
cfg["default_aging_distribution"] = "weibull_2p"
cfg["default_beta_jaar"] = 2.5
data.setdefault("projectnaam", "AWZI Haarlem Waarderpolder (demo)")
data.setdefault("modelleur", "RCM2 demo")

path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

proj2 = RCMProject.from_dict(data)
errs = validate_project(proj2)
print(f"flipped_evident={len(needs_evident)} errors={len(errs)}")
if errs:
    for e in errs[:5]:
        print(e)
