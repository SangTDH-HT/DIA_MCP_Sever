"""Redraw the Silo HMI frame to the current measurements, on a file DIAScreen has saved.

Run:  python restyle_silo_frame.py <project.dpa> <asset folder>

DIAScreen rewrites the picture bank when it saves - renumbering, moving to
PicBank01 and shrinking faces to fit inside the button body - so this does not
patch pictures in place. It renders every face again at full size, builds a new
bank from nothing, and points each frame element at its face by element name.
"""
import sys
from pathlib import Path

import build_silo_frame as frame
from dpa import edit, picbank
from dpa.model import Project

project = Project(sys.argv[1])
assets = frame.render_assets(Path(sys.argv[2]))
DONOR = r"C:\OTL\OTL_SILO\OTL_Silo6\Code_Silo_AThanh\HMI_AThanh.dpa"

# Dividers are Line elements. A Rectangle cannot be one: the panel draws its
# border black whatever the colour keys say, and a 1 px fill does not show.
# A Line takes its colour from the state's FontColor (not FgColor), and
# LineStyle 1 is an arrow; Style 769 runs across, 1025 runs down.
base = project.screen("Khung_Chung")
donor = Project(DONOR)
line_across = donor.element("scr_Overview", 1)
line_down = donor.element("scr_I/O", 0)
rules = {
    "fr_rule_header": (line_across, 0, frame.HEADER_H, 1024, 1),
    "fr_rule_sidebar": (line_down, frame.SIDEBAR_W, frame.HEADER_H, 1, 600 - frame.HEADER_H),
}
# The Fill form has no bottom bar, so the old footer line goes.
for element in [e for e in base.elements if e.name == "fr_rule_footer"]:
    edit.delete_element(project, base, element.index)
# Logo and user block are Goto Screen buttons, not Rectangles: a Rectangle
# draws a 1 px light bevel round its picture and shrinks the picture 4/1 px
# whatever its Style; a Goto with Style=3 draws the picture alone, full size.
goto_tpl = donor.element("pop_Setting", 5)
screens = {s.name: s for s in project.screens}
for name, destination in (("fr_logo", screens["Home_Fill"]), ("fr_user", screens["Setting"])):
    old = [e for e in base.elements if e.name == name]
    if old and old[0].type_code == "1.10":
        continue
    if old:
        edit.delete_element(project, base, old[0].index)
    button = edit.clone_element(project, goto_tpl, base, 0, 0, 10, 10, name)
    button.section.set("Level", 0)
    button.section.set("GoToScreenID", destination.id)
    for entry in button.section.entries("GoToScreenName"):
        entry.value = destination.name.encode("latin1")

for name, (template, x, y, w, h) in rules.items():
    old = [e for e in base.elements if e.name == name]
    if old and old[0].type_code == "10.1":
        line = old[0]
        for key, value in zip(("X", "Y", "Width", "Height"), (x, y, w, h)):
            line.section.set(key, value)
    else:
        if old:
            edit.delete_element(project, base, old[0].index)
        line = edit.clone_element(project, template, base, x, y, w, h, name)
    line.section.set("LineStyle", 0)  # 0 plain; the donor's 1 draws an arrowhead
    for state in line.states:
        state.set("FontColor", frame.bgr(frame.RULE))  # a Line's colour is its FontColor
        state.set("FgColor", frame.bgr(frame.RULE))

bank = frame.Bank(project)
# Pictures the frame does not own (the pages' artwork) are carried over as
# they are; the frame's own faces start over, since DIAScreen's copies of
# them may have been shrunk.
FRAME = ("nav_", "tab_", "fr_")
by_offset, pos = {}, len(picbank.MAGIC)
for picture in bank.pictures:
    by_offset[pos] = picture.record
    pos += len(picture.record)
kept = []  # (state, record)
for screen in project.screens:
    for element in screen.elements:
        if element.name.startswith(FRAME):
            continue
        for state in element.states:
            offset = state.get("PictureOffset")
            if offset and int(offset) in by_offset:
                kept.append((state, by_offset[int(offset)]))
bank.pictures = []
for key, path in assets.items():
    if not key.startswith("rule"):
        bank.add(key, path)
placed = {}
for state, record in kept:
    if record not in placed:
        offset = len(picbank.MAGIC) + sum(len(p.record) for p in bank.pictures)
        index = len(bank.pictures) + 1
        width, height = record[8:12], record[12:16]
        bank.pictures.append(picbank.Picture(index, int.from_bytes(width, "little"), abs(int.from_bytes(height, "little", signed=True)), record))
        placed[record] = (f"{bank.prefix}{index:05d}", offset)
    name, offset = placed[record]
    state.set("Picture Name", name)
    state.set("PictureOffset", offset)
bank.commit()

lit_nav = {"Home_Fill": "home", "Home_Discharge": "home", "Home_Blend": "home", "Setting": "setting", "Data": "data"}
lit_tab = {"Home_Fill": "fill", "Home_Discharge": "discharge", "Home_Blend": "blend"}
nav_y = dict(zip(("home", "setting", "data"), frame.NAV_Y))
tab_x = dict(zip(("fill", "discharge", "blend"), frame.TAB_X))


def place(element, x, y, w, h):
    for key, value in zip(("X", "Y", "Width", "Height"), (x, y, w, h)):
        element.section.set(key, value)


for screen in project.screens:
    for element in screen.elements:
        name = element.name
        if name.startswith("nav_"):
            key = name[4:]
            place(element, frame.NAV_X, nav_y[key], frame.NAV_W, frame.NAV_H)
            frame.face(element, bank, f"nav_{key}_{'on' if lit_nav[screen.name] == key else 'off'}")
            frame.flat(element)
        elif name.startswith("tab_"):
            key = name[4:]
            place(element, tab_x[key], frame.TAB_Y, frame.TAB_W, frame.TAB_H)
            frame.face(element, bank, f"tab_{key}_{'on' if lit_tab[screen.name] == key else 'off'}")
            frame.flat(element)
        elif name == "fr_logo":
            _, _, w, h = bank.where["logo"]
            place(element, *frame.LOGO_XY, w, h)
            frame.face(element, bank, "logo")
            frame.flat(element)
        elif name == "fr_user":
            place(element, *frame.USER_XY, frame.USER_W, frame.USER_H)
            frame.face(element, bank, "user")
            frame.flat(element)
        elif name in ("fr_time", "fr_date"):
            place(element, 4, 541 if name == "fr_time" else 560, frame.SIDEBAR_W - 8, 19)
            for state in element.states:
                for slot in (0, 1):
                    if state.get(f"FontSize{slot}") is not None:
                        state.set(f"FontSize{slot}", 13)

print(project.save(sys.argv[1]))
print(f"bank: {len(picbank.read(bank.entry.blob))} pictures")
