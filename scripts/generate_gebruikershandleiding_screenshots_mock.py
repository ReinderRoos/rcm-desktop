#!/usr/bin/env python3
"""Mock UI-screenshots voor de gebruikershandleiding (geen Qt nodig).

Labels komen uit rcm_desktop.messages. Voor echte UI-grabs:
  python scripts/capture_gebruikershandleiding_screenshots.py
"""

from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = REPO_ROOT / "docs" / "gebruiker" / "screenshots"

if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

# Kleuren (RCM2-achtig: donkerblauw + lichtgrijs)
BG = (245, 247, 250)
PANEL = (255, 255, 255)
BORDER = (200, 206, 214)
ACCENT = (26, 82, 118)
TEXT = (33, 37, 41)
MUTED = (108, 117, 125)
CHART_A = (52, 120, 175)
CHART_B = (180, 95, 60)
SIDEBAR_W = 280
HEADER_H = 52
TOOLBAR_H = 40


def _font(size: int, bold: bool = False):
    from PIL import ImageFont

    try:
        name = "arialbd.ttf" if bold else "arial.ttf"
        return ImageFont.truetype(name, size)
    except OSError:
        return ImageFont.load_default()


def _new_canvas(w: int = 1400, h: int = 900):
    from PIL import Image, ImageDraw

    img = Image.new("RGB", (w, h), BG)
    return img, ImageDraw.Draw(img)


def _header(draw, y0: int, title: str, path: str = "") -> int:
    from PIL import Image

    draw.rectangle((0, y0, 1400, y0 + HEADER_H), fill=ACCENT)
    draw.text((16, y0 + 14), title, fill=(255, 255, 255), font=_font(16, True))
    if path:
        draw.text((400, y0 + 16), path, fill=(220, 230, 240), font=_font(11))
    return y0 + HEADER_H


def _toolbar(draw, y0: int, buttons: list[str], active: str | None = None) -> int:
    draw.rectangle((0, y0, 1400, y0 + TOOLBAR_H), fill=PANEL, outline=BORDER)
    x = 12
    for label in buttons:
        is_active = label == active
        pad = draw.textbbox((0, 0), label, font=_font(11, is_active))
        bw = pad[2] - pad[0] + 16
        bh = 26
        fill = ACCENT if is_active else (230, 234, 238)
        fg = (255, 255, 255) if is_active else TEXT
        draw.rounded_rectangle((x, y0 + 7, x + bw, y0 + 7 + bh), radius=4, fill=fill)
        draw.text((x + 8, y0 + 12), label, fill=fg, font=_font(11, is_active))
        x += bw + 8
    return y0 + TOOLBAR_H


def _sidebar(draw, y0: int, h: int, selected: str | None = None):
    draw.rectangle((0, y0, SIDEBAR_W, y0 + h), fill=PANEL, outline=BORDER)
    draw.text((12, y0 + 10), "Componenten", fill=ACCENT, font=_font(12, True))
    items = ["▸ ROOT", "  ▸ POMP-A", "  ▸ MOTOR-1", "  ▸ TANK-02"]
    yy = y0 + 36
    for item in items:
        col = ACCENT if selected and selected in item else TEXT
        if selected and selected in item:
            draw.rectangle((4, yy - 2, SIDEBAR_W - 4, yy + 18), fill=(230, 240, 248))
        draw.text((16, yy), item.replace("▸ ", ""), fill=col, font=_font(11))
        yy += 24


def _bar_chart(draw, x0: int, y0: int, w: int, h: int, title: str, values: list[float]):
    draw.rectangle((x0, y0, x0 + w, y0 + h), fill=PANEL, outline=BORDER)
    draw.text((x0 + 12, y0 + 10), title, fill=TEXT, font=_font(12, True))
    if not values:
        draw.text((x0 + 12, y0 + 40), "(geen data — start analyse-run)", fill=MUTED, font=_font(11))
        return
    max_v = max(values) or 1.0
    bar_w = (w - 40) // len(values)
    base_y = y0 + h - 30
    for i, v in enumerate(values):
        bh = int((h - 70) * (v / max_v))
        bx = x0 + 20 + i * bar_w
        draw.rectangle((bx, base_y - bh, bx + bar_w - 8, base_y), fill=CHART_A)
    draw.text((x0 + 12, y0 + h - 22), "Top 10 — niet-beschikbaarheid %", fill=MUTED, font=_font(10))


def _save(img, name: str) -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    path = OUT_DIR / name
    img.save(path, "PNG", optimize=True)
    print(f"  {path.name}")


def shot_01_overview():
    from rcm_desktop import messages

    img, draw = _new_canvas()
    y = _header(draw, 0, messages.WORKSPACE_WINDOW_TITLE, str(REPO_ROOT / "tests/fixtures/sample_project.rcm.json")[-40:])
    y = _toolbar(
        draw,
        y,
        [
            messages.WORKSPACE_PBS_TOGGLE_LABEL,
            messages.WORKSPACE_SHOW_WHOLE_PROJECT_BUTTON,
            messages.WORKSPACE_MODE_BIJDRAGEN,
            messages.WORKSPACE_MODE_LCC,
            messages.WORKSPACE_MODE_FM_DETAIL,
            messages.REPORT_GENERATE_BUTTON_LABEL,
        ],
        active=messages.WORKSPACE_MODE_BIJDRAGEN,
    )
    body_h = 900 - y
    _sidebar(draw, y, body_h)
    _bar_chart(
        draw,
        SIDEBAR_W + 16,
        y + 120,
        1080,
        320,
        messages.WORKSPACE_MODE_BIJDRAGEN,
        [42, 28, 19, 14, 11, 8, 6, 5, 4, 3],
    )
    draw.rectangle((SIDEBAR_W + 16, y + 16, 1384, y + 100), fill=PANEL, outline=BORDER)
    draw.text((SIDEBAR_W + 28, y + 28), "KPI — lifecycle totalen (scenario A | B)", fill=TEXT, font=_font(11, True))
    _save(img, "01-werkruimte-overzicht.png")


def shot_02_toolbar():
    img, draw = _new_canvas(1400, 200)
    y = _header(draw, 0, "RCM2 desktop — projectpad", "tests/fixtures/sample_project.rcm.json")
    draw.rectangle((12, y + 8, 1388, y + 48), fill=(255, 255, 220), outline=(200, 180, 60))
    draw.text(
        (24, y + 18),
        "Project inladen  ·  padveld  ·  status: done",
        fill=TEXT,
        font=_font(12),
    )
    _save(img, "02-toolbar-project-pad.png")


def shot_03_pbs_scope():
    from rcm_desktop import messages

    img, draw = _new_canvas()
    y = _header(draw, 0, messages.WORKSPACE_WINDOW_TITLE)
    y = _toolbar(draw, y, [messages.WORKSPACE_SHOW_WHOLE_PROJECT_BUTTON, messages.WORKSPACE_MODE_BIJDRAGEN], active=messages.WORKSPACE_MODE_BIJDRAGEN)
    _sidebar(draw, y, 900 - y, selected="TANK-02")
    draw.text((SIDEBAR_W + 16, y + 12), "Scope: TANK-02 (geselecteerd component)", fill=ACCENT, font=_font(11, True))
    _bar_chart(draw, SIDEBAR_W + 16, y + 48, 1080, 400, "Top 10 — gefilterd op scope", [35, 22, 15])
    _save(img, "03-pbs-scope-geselecteerd.png")


def shot_04_top10():
    from rcm_desktop import messages

    img, draw = _new_canvas()
    y = _header(draw, 0, messages.WORKSPACE_WINDOW_TITLE)
    y = _toolbar(draw, y, [messages.WORKSPACE_MODE_BIJDRAGEN], active=messages.WORKSPACE_MODE_BIJDRAGEN)
    _sidebar(draw, y, 900 - y)
    draw.text((SIDEBAR_W + 16, y + 8), messages.WORKSPACE_TOP10_SUBBAR_LABEL, fill=TEXT, font=_font(11))
    subs = [
        messages.WORKSPACE_SOURCE_TOGGLE_PBS,
        messages.WORKSPACE_METRIC_NIET_BESCHIKBAARHEID,
        messages.WORKSPACE_CONTRIBUTION_HORIZON_LIFECYCLE,
    ]
    sx = SIDEBAR_W + 16
    for s in subs:
        draw.rounded_rectangle((sx, y + 28, sx + 120, y + 50), radius=4, fill=(230, 234, 238))
        draw.text((sx + 8, y + 34), s, fill=TEXT, font=_font(10))
        sx += 130
    _bar_chart(draw, SIDEBAR_W + 16, y + 60, 1080, 500, messages.WORKSPACE_MODE_BIJDRAGEN, [40, 25, 18, 12, 9, 7, 5, 4, 3, 2])
    _save(img, "04-modus-top10.png")


def shot_05_lcc():
    from rcm_desktop import messages

    img, draw = _new_canvas()
    y = _header(draw, 0, messages.WORKSPACE_WINDOW_TITLE)
    y = _toolbar(draw, y, [messages.WORKSPACE_MODE_LCC], active=messages.WORKSPACE_MODE_LCC)
    _sidebar(draw, y, 900 - y)
    draw.rectangle((SIDEBAR_W + 16, y + 8, 1384, y + 80), fill=PANEL, outline=BORDER)
    draw.text((SIDEBAR_W + 28, y + 20), messages.WORKSPACE_LCC_WHATIF_BAR_TITLE, fill=ACCENT, font=_font(11, True))
    draw.text((SIDEBAR_W + 28, y + 42), messages.WORKSPACE_LCC_WHAT_IF_TOGGLE, fill=TEXT, font=_font(10))
    # stacked bars mock
    x0, y0, w, h = SIDEBAR_W + 16, y + 96, 1080, 360
    draw.rectangle((x0, y0, x0 + w, y0 + h), fill=PANEL, outline=BORDER)
    draw.text((x0 + 12, y0 + 10), "LCC — kosten per kalenderjaar", fill=TEXT, font=_font(12, True))
    base = y0 + h - 36
    for i in range(12):
        bx = x0 + 30 + i * 80
        draw.rectangle((bx, base - 50, bx + 30, base), fill=CHART_A)
        draw.rectangle((bx, base - 90, bx + 30, base - 50), fill=CHART_B)
    draw.text((x0 + 12, y0 + h - 24), messages.WORKSPACE_UNAVAILABILITY_PROXY_DISCLAIMER[:80] + "…", fill=MUTED, font=_font(9))
    _save(img, "05-modus-tijdsplot-planning.png")


def shot_06_fm_detail():
    from rcm_desktop import messages

    img, draw = _new_canvas()
    y = _header(draw, 0, messages.WORKSPACE_WINDOW_TITLE)
    y = _toolbar(draw, y, [messages.WORKSPACE_MODE_FM_DETAIL], active=messages.WORKSPACE_MODE_FM_DETAIL)
    _sidebar(draw, y, 900 - y)
    # table
    tx, ty = SIDEBAR_W + 16, y + 16
    draw.rectangle((tx, ty, tx + 520, ty + 200), fill=PANEL, outline=BORDER)
    headers = ["FM-id", "Faalwijze", "PBS-id", "Faalmomenten", "Kosten EUR"]
    hx = tx + 8
    for h in headers:
        draw.text((hx, ty + 8), h, fill=MUTED, font=_font(9, True))
        hx += 95
    draw.rectangle((tx + 4, ty + 32, tx + 516, ty + 56), fill=(230, 240, 248))
    draw.text((tx + 12, ty + 38), "FM-A  ·  Lager uitval  ·  POMP-A", fill=TEXT, font=_font(10))
    # inspector
    ix = tx + 540
    draw.rectangle((ix, ty, ix + 520, ty + 400), fill=PANEL, outline=BORDER)
    draw.text((ix + 12, ty + 12), "FM-inspector", fill=ACCENT, font=_font(12, True))
    draw.text((ix + 12, ty + 40), "FM-A — lifecycle totalen", fill=TEXT, font=_font(11))
    draw.text((ix + 12, ty + 68), messages.WORKSPACE_FM_INSPECTOR_HASH_PREFIX + " a3f9…", fill=MUTED, font=_font(10))
    _save(img, "06-modus-fm-detail-inspector.png")


def shot_07_report_dialog():
    from rcm_desktop import messages

    img, draw = _new_canvas(560, 520)
    draw.rectangle((0, 0, 560, 520), fill=PANEL, outline=BORDER)
    draw.rectangle((0, 0, 560, 40), fill=ACCENT)
    draw.text((16, 10), messages.REPORT_DIALOG_TITLE, fill=(255, 255, 255), font=_font(13, True))
    fields = [
        messages.REPORT_DIALOG_OUTPUT_PATH + ":  …/rapporten/project_2026-06-02.docx",
        "☑ " + messages.REPORT_DIALOG_GENERATE_PDF,
        messages.REPORT_DIALOG_NB_THRESHOLD + ": 1.0",
        messages.REPORT_DIALOG_COST_THRESHOLD + ": 2.0",
        "☐ " + messages.REPORT_DIALOG_INCLUDE_BELOW,
        "☐ " + messages.REPORT_DIALOG_PBS_DEEPDIVE,
        messages.REPORT_DIALOG_PREVIEW + ": Enkele analyse — 4 NB-functies, 3 kosten-functies",
    ]
    yy = 56
    for line in fields:
        draw.text((20, yy), line, fill=TEXT, font=_font(11))
        yy += 32
    draw.rectangle((360, 460, 540, 500), fill=ACCENT)
    draw.text((400, 472), "Genereren", fill=(255, 255, 255), font=_font(11, True))
    _save(img, "07-rapport-dialoog.png")


def shot_08_no_run():
    from rcm_desktop import messages

    img, draw = _new_canvas()
    y = _header(draw, 0, messages.WORKSPACE_WINDOW_TITLE)
    y = _toolbar(
        draw,
        y,
        [messages.REPORT_GENERATE_BUTTON_LABEL],
        active=None,
    )
    draw.text((SIDEBAR_W + 16, y + 16), messages.WORKSPACE_DETAIL_EMPTY_STATE, fill=MUTED, font=_font(12))
    draw.rectangle((1200, y + 8, 1370, y + 32), fill=(220, 220, 220))
    draw.text((1210, y + 12), messages.REPORT_GENERATE_BUTTON_LABEL, fill=MUTED, font=_font(10))
    _save(img, "08-werkruimte-zonder-run.png")


def main() -> int:
    try:
        from PIL import Image  # noqa: F401
    except ImportError:
        print("Pillow ontbreekt. Voer uit: pip install Pillow")
        return 1

    print(f"Mock screenshots -> {OUT_DIR}")
    shot_01_overview()
    shot_02_toolbar()
    shot_03_pbs_scope()
    shot_04_top10()
    shot_05_lcc()
    shot_06_fm_detail()
    shot_07_report_dialog()
    shot_08_no_run()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
