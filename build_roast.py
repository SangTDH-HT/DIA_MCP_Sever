"""Build a roasting screen: one hero curve, one hero number, a quiet rest.

Run:  python build_roast.py <project.dpa> <icon folder> <donor.dpa> [more donors]

This is a redesign of OTL-120's PROGRAM MANUAL 2, not a copy. That screen packs
104 elements into five framing styles and gives bean temperature - the number a
roaster watches all batch - the same weight as the fan percentage. Here the
curve and the bean temperature carry the screen; everything else stays quiet.

Three groups answer three questions: where is the batch (curve + bean temp),
what is the machine doing (gas, air, weight), what do I press next (action bar).

Two things the format makes easy to get wrong, both learned the hard way:

* Font size is per language - `FontSize0` / `FontSize1`, never `FontSize`.
  Setting the wrong key silently leaves the donor's font, and the panel then
  warns "Text width exceeds the element width" at compile.
* A button's face is a bitmap from the picture bank, not a colour, so a button
  cloned out of another project points at a picture that does not exist here and
  draws blank. Buttons are therefore drawn as a rectangle plus a label, with a
  picture-less button laid over the top to take the touch. That overlay must
  keep the donor's `Style`: setting `Style=0` makes the panel draw its own grey
  button body, which then hides the icon and the label underneath.
* A State Graphic picks its image from the value of an address, so it must have
  one. Cleared to "None" it fails to compile with "Element address input error",
  even when the icon never changes.
* A trend needs a history buffer to exist - without one the project will not
  compile ("Element buffer is undefined") - so buffer 1 is configured here.
"""

from __future__ import annotations

import copy
import re
import sys
from pathlib import Path

from dpa import edit, picbank
from dpa.model import Project


def bgr(hex_rgb: str) -> int:
    value = int(hex_rgb.lstrip("#"), 16)
    r, g, b = (value >> 16) & 0xFF, (value >> 8) & 0xFF, value & 0xFF
    return (b << 16) | (g << 8) | r


# OTL-30 HOME tone: flat, square, quiet.
HEADER = bgr("#60656B")
PAGE = bgr("#F5F6F8")
CARD = bgr("#FFFFFF")
HAIR = bgr("#CDD0D5")
INK = bgr("#60656B")
WHITE = bgr("#FFFFFF")
BEAN = bgr("#2F3438")
GAS = bgr("#FF4444")

# FontAlign is a bit mask: 32 = vertically centred, +1 left, +2 centre, +4 right.
# 36 is therefore right aligned, which is what made every button label hug its
# right edge.
LEFT, CENTRE = 33, 34

W, H = 1024, 600
GUTTER = 24
HEADER_H = 56
BAR_H = 96
BAR_Y = H - BAR_H
CHART_X, CHART_Y = GUTTER, HEADER_H + GUTTER
CHART_W, CHART_H = 616, BAR_Y - CHART_Y - GUTTER
SIDE_X = CHART_X + CHART_W + GUTTER
SIDE_W = W - SIDE_X - GUTTER

SOLID = 1  # FillStyle; see fill_probe.py

ACTIONS = [
    ("Nạp", "Charge", "$2100.0", "Charge.png"),
    ("Xả", "Drop", "$2100.1", "Drop.png"),
    ("Thoát", "Escape", "$2100.2", "Auto.png"),
    ("Trộn", "Mixer", "$2100.3", "Mixer_1.png"),
    ("Hồ sơ", "Profile", "$2100.4", "Profile_On.png"),
]


def find(donors, *codes):
    for wanted in codes:
        for donor in donors:
            for screen in donor.screens:
                for element in screen.elements:
                    if element.type_code == wanted:
                        return element
    raise LookupError(f"no donor holds an element of type {codes}")


# The history channel keys, as a project that has a working trend writes them.
CHANNEL = re.compile(r"(01$|^Column|^CSVTitle)")
TREND_BUFFER_ADDR = "$2200"
TREND_BUFFER_WORDS = 10
# The action-bar icons never change, but the element still needs an address to
# choose a state from; they all read one word that stays at zero.
ICON_STATE_ADDR = "$2300"
# Which bank a project's own images live in tracks its colour depth: the
# 65536-colour DOP-110WS projects use PicBank02, the True Colour DOP-115WX ones
# use PicBank01.
ICON_BANK = "PicBank02"


def configure_history(project: Project, donor: Project) -> None:
    """Give buffer 1 a definition, copied from a project whose trend works.

    A trend element reads a numbered buffer out of `[History]`. A fresh project
    declares `HistoryCount=0` and none of the per-channel keys, so the copied
    trend refers to a buffer that does not exist. Rather than invent the twenty
    keys a channel needs, take them from a project that has them and repoint the
    source at internal memory.
    """
    ours = project.doc.first("History")
    theirs = donor.doc.first("History")
    have = {e.key for e in ours.items if hasattr(e, "key")}
    for entry in theirs.items:
        key = getattr(entry, "key", None)
        if key is None or key in have or not CHANNEL.search(key.decode("latin1")):
            continue
        ours.items.append(copy.deepcopy(entry))
    ours.set("HistoryCount", 1)
    ours.set("ReadVar01", TREND_BUFFER_ADDR)
    ours.set("ReadMemLen01", TREND_BUFFER_WORDS)
    ours.set("EnableInterlock01", 0)
    ours.set("InterlockVar01", "None")


def clear_bindings(element) -> None:
    for key in ("ReadVar", "WriteVar", "InterLockVar", "VisibleVar"):
        if element.section.get(key) not in (None, "None"):
            element.section.set(key, "None")
    for state in element.states:
        for key in ("Picture Name", "PIB Name"):
            if state.get(key) is not None:
                state.set(key, "")


def set_font(element, size: int, colour: int, bold: int = 0, align: int = LEFT) -> None:
    """Font settings live per language slot, so every slot has to be told."""
    for state in element.states:
        state.set("FontColor", colour)
        state.set("FontBold", bold)
        state.set("FontAlign", align)
        for slot in (0, 1):
            state.set(f"FontSize{slot}", size)
            state.set(f"FontName{slot}", "Arial")


def main(path: str, icon_dir: str, *donor_paths: str) -> None:
    project = Project(path)
    donors = [Project(p) for p in donor_paths]

    rect = find(donors, "10.2")
    text = find(donors, "10.6")
    number = find(donors, "5.1")
    button = find(donors, "1.1", "1.3", "1.4", "1.5")
    graphic = find(donors, "7.1")
    trend = find(donors, "9.1")

    configure_history(project, next(d for d in donors if d.doc.first("History").get("HistoryCount") == "1"))

    # --- icons into the bank; the index an image lands at is its name ------
    folder = Path(icon_dir)
    wanted = [folder / a[3] for a in ACTIONS]
    missing = [p.name for p in wanted if not p.exists()]
    if missing:
        raise SystemExit(f"icons not found in {folder}: {missing}")

    section = project.doc.first("Picture")
    entry = section.entries("Size")[0]
    blob, added = picbank.append(entry.blob or b"", wanted, background=(0x60, 0x65, 0x6B))
    entry.blob, entry.value, entry.blob_eol = blob, str(len(blob)).encode("ascii"), True
    prefix = project.doc.first("Application").as_dict().get("Name") or "NewHMI"
    print(f"bank: {len(picbank.read(blob))} images; added {[p.index for p in added]} as {prefix}#####")

    screen = edit.clone_screen(project, project.screens[0], "scr_Roast")
    screen.section.set("BgColor", PAGE)
    screen.section.set("DocSizeX", W)
    screen.section.set("DocSizeY", H)

    def panel(x, y, w, h, fill, name, border=None):
        item = edit.clone_element(project, rect, screen, x, y, w, h, name)
        item.section.set("FillStyle", SOLID)
        item.section.set("GradFillMode", 0)
        item.section.set("GradFillStartColor", fill)
        item.section.set("GradFillEndColor", fill)
        item.section.set("BorderColor", border if border is not None else fill)
        item.section.set("RoundRadius", 0)
        item.section.set("EnableCustomRadius", 0)
        clear_bindings(item)
        for state in item.states:
            state.set("BgColor", fill)
            state.set("FgColor", fill)
        return item

    def label(x, y, w, h, vi, en, colour, size, name, bold=0, align=LEFT):
        item = edit.clone_element(project, text, screen, x, y, w, h, name)
        edit.set_state_text(item, vi, en)
        clear_bindings(item)
        set_font(item, size, colour, bold, align)
        return item

    def readout(x, y, w, h, addr, colour, size, name, decimals=1, align=CENTRE):
        item = edit.clone_element(project, number, screen, x, y, w, h, name)
        clear_bindings(item)
        item.section.set("ReadVar", addr)
        item.section.set("IntNum", 3)
        item.section.set("DotNum", decimals)
        set_font(item, size, colour, 1, align)
        for state in item.states:
            state.set("BgColor", CARD)
            state.set("FgColor", CARD)
        return item

    # --- header ----------------------------------------------------------
    panel(0, 0, W, HEADER_H, HEADER, "hd_bar")
    label(GUTTER, 16, 320, 28, "Rang thủ công", "Manual roast", WHITE, 16, "hd_title", bold=1)
    label(W - 260, 18, 236 - GUTTER, 24, "Hồ sơ 12", "Profile 12", WHITE, 12, "hd_profile")

    # --- the curve --------------------------------------------------------
    panel(CHART_X, CHART_Y, CHART_W, CHART_H, CARD, "ch_card", HAIR)
    label(CHART_X + 16, CHART_Y + 12, 300, 22, "Đường rang", "Roast curve", INK, 12, "ch_title")
    curve = edit.clone_element(
        project, trend, screen,
        CHART_X + 16, CHART_Y + 40, CHART_W - 32, CHART_H - 56, "ch_trend",
    )
    clear_bindings(curve)
    curve.section.set("ReadBuffer", 1)

    # --- bean temperature -------------------------------------------------
    y = CHART_Y
    panel(SIDE_X, y, SIDE_W, 150, CARD, "bt_card", HAIR)
    readout(SIDE_X + 16, y + 24, SIDE_W - 90, 70, "$2000", BEAN, 44, "bt_value")
    label(SIDE_X + SIDE_W - 66, y + 52, 50, 32, "°C", "°C", INK, 18, "bt_unit")
    label(SIDE_X + 16, y + 108, SIDE_W - 32, 24, "Nhiệt hạt", "Bean temp", INK, 12, "bt_label")

    # --- the readings that qualify it -------------------------------------
    y += 150 + 16
    panel(SIDE_X, y, SIDE_W, 104, CARD, "et_card", HAIR)
    for i, (vi, en, addr, key) in enumerate(
        [("Khí thải", "Exhaust", "$2004", "et"), ("Tốc độ tăng", "Rate of rise", "$2008", "ror")]
    ):
        row = y + 14 + i * 44
        label(SIDE_X + 16, row + 4, 150, 22, vi, en, INK, 12, f"{key}_label")
        readout(SIDE_X + SIDE_W - 126, row, 110, 28, addr, INK, 18, f"{key}_value")

    # --- what the machine is doing ----------------------------------------
    y += 104 + 16
    rows = [
        ("Gas", "Gas", "$2012", GAS, "gas"),
        ("Gió", "Airflow", "$2016", INK, "air"),
        ("Khối lượng", "Batch", "$2020", INK, "kg"),
    ]
    panel(SIDE_X, y, SIDE_W, 44 * len(rows) + 16, CARD, "mc_card", HAIR)
    for i, (vi, en, addr, colour, key) in enumerate(rows):
        row = y + 10 + i * 44
        label(SIDE_X + 16, row + 4, 150, 22, vi, en, INK, 12, f"{key}_label")
        readout(SIDE_X + SIDE_W - 126, row, 110, 28, addr, colour, 18, f"{key}_value")

    # --- action bar: icon over verb, five equal slots ---------------------
    panel(0, BAR_Y, W, 1, HAIR, "ab_rule")
    slot = (W - GUTTER * 2) // len(ACTIONS)
    for i, ((vi, en, addr, _), picture) in enumerate(zip(ACTIONS, added)):
        x = GUTTER + i * slot
        panel(x, BAR_Y + 12, slot - 12, BAR_H - 28, HEADER, f"ab_bg_{i}")

        icon = edit.clone_element(
            project, graphic, screen, x + (slot - 12) // 2 - 16, BAR_Y + 18, 32, 32, f"ab_icon_{i}"
        )
        clear_bindings(icon)
        icon.section.set("ReadVar", ICON_STATE_ADDR)
        for state in icon.states:
            state.set("PIB Name", ICON_BANK)
            state.set("Picture Name", f"{prefix}{picture.index:05d}")
            state.set("PictureStretch", 1)

        label(x, BAR_Y + 54, slot - 12, 24, vi, en, WHITE, 14, f"ab_label_{i}", bold=1, align=CENTRE)

        hit = edit.clone_element(project, button, screen, x, BAR_Y + 12, slot - 12, BAR_H - 28, f"ab_hit_{i}")
        clear_bindings(hit)
        hit.section.set("ReadVar", addr)
        hit.section.set("WriteVar", addr)
        edit.set_state_text(hit, "", "")

    print(project.save(path))
    print(f"{screen.name} id={screen.id}: {len(screen.elements)} elements")


if __name__ == "__main__":
    if len(sys.argv) < 4:
        raise SystemExit(__doc__)
    main(*sys.argv[1:])
