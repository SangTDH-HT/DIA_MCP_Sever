"""Import PNG icons into a project's picture bank and show them on a screen.

Run:  python import_icons.py <project.dpa> <icon folder> <donor.dpa>

The bank stores bitmaps with no names; an element points at one by index
(`Picture Name` = prefix + 5-digit index) and by bank (`PIB Name`).  The prefix
and the bank name are the two things the format does not spell out, so each
icon is placed twice - once as PicBank01, once as PicBank02 - and whichever
column draws is the convention this project uses.

Delta panels do not composite alpha, so icons are flattened onto the colour
they will sit on.
"""

from __future__ import annotations

import sys
from pathlib import Path

from dpa import edit, picbank
from dpa.model import Project

ICONS = ["Charge.png", "Drop.png", "Mixer.png", "Auto.png", "Alarm.png"]
BAR = (0x60, 0x65, 0x6B)  # icons sit on the action bar, so flatten onto it


def find(donors, *codes):
    for wanted in codes:
        for donor in donors:
            for screen in donor.screens:
                for element in screen.elements:
                    if element.type_code == wanted:
                        return element
    raise LookupError(codes)


def main(path: str, icon_dir: str, *donor_paths: str) -> None:
    project = Project(path)
    donors = [Project(p) for p in donor_paths]

    folder = Path(icon_dir)
    files = [folder / n for n in ICONS if (folder / n).exists()]
    if not files:
        raise SystemExit(f"none of {ICONS} found in {folder}")

    section = project.doc.first("Picture")
    entry = section.entries("Size")[0]
    blob, added = picbank.append(entry.blob or b"", files, background=BAR)
    entry.blob = blob
    entry.value = str(len(blob)).encode("ascii")
    entry.blob_eol = True
    print(f"bank: {len(picbank.read(blob))} images, added {[(p.index, p.width, p.height) for p in added]}")

    graphic = find(donors, "7.1", "1.5")
    screen = project.screen("Screen_1")
    text = find(donors, "10.6")
    prefix = (project.doc.first("Application").as_dict().get("Name") or "NewHMI")

    for row, bank_name in enumerate(("PicBank01", "PicBank02")):
        for column, picture in enumerate(added):
            x = 40 + column * 120
            y = 300 + row * 130
            item = edit.clone_element(
                project, graphic, screen, x, y, 96, 96, f"ico_{bank_name}_{picture.index}"
            )
            for key in ("ReadVar", "WriteVar", "InterLockVar", "VisibleVar"):
                if item.section.get(key) not in (None, "None"):
                    item.section.set(key, "None")
            for state in item.states:
                state.set("PIB Name", bank_name)
                state.set("Picture Name", f"{prefix}{picture.index:05d}")
                state.set("PictureStretch", 1)
                state.set("PictureWidth", picture.width)
                state.set("PictureHeight", picture.height)
            label = edit.clone_element(
                project, text, screen, x, y + 98, 96, 22, f"ico_lbl_{bank_name}_{picture.index}"
            )
            edit.set_state_text(label, f"{bank_name[-2:]}-{picture.index}", f"{bank_name[-2:]}-{picture.index}")

    print(project.save(path))
    print(f"placed {len(added) * 2} icons on {screen.name}, prefix {prefix!r}")


if __name__ == "__main__":
    if len(sys.argv) < 4:
        raise SystemExit(__doc__)
    main(*sys.argv[1:])
