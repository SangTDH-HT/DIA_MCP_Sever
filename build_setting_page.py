"""Draw the Setting page of the new Silo HMI after Sang's Settings mockup.

Run:  python build_setting_page.py <project.dpa> <asset folder>

A "Settings" title and a 4 x 2 grid of tiles - Parameter, I/O, Calibration,
Account Management, Date and time, Language, Screen Brightness, About. Each tile
is one Goto Screen whose face is rendered here (Lucide icon + label).

The pages behind the tiles do not exist yet, so each tile gets an empty page of
its own: the Setting page's frame and side bar (Setting lit), a back link to
Settings and the page title. Their content comes later.

Re-runnable: elements named "st_" are removed first, the sub-pages are emptied
and refilled, and the picture bank is pruned.
"""

from __future__ import annotations

import sys
from pathlib import Path

from PIL import Image, ImageDraw

import build_fill_page as fill
import build_silo_frame as frame
from build_fill_page import FIELD_LINE, clear_links, rounded
from build_silo_frame import INK, MUTED, NAV_INK, NAV_ON, PAGE, WHITE, font, icon, rgb
from dpa import edit
from dpa.model import Project, Screen

TILES = (  # screen, label, icon
    ("Set_Parameter", "Parameter", "sliders-vertical"),
    ("Set_IO", "I/O", "arrow-left-right"),
    ("Set_Calibration", "Calibration", "scale"),
    ("Set_Account", "Account\nManagement", "users"),
    ("Set_DateTime", "Date and time", "clock"),
    ("Set_Language", "Language", "languages"),
    ("Set_Brightness", "Screen Brightness", "monitor"),
    ("Set_About", "About", "info"),
)

# Pages with a builder of their own: their title and content come from it, and
# this script only refreshes their side bar and back link.
OWN_CONTENT = {  # page -> keeps this script's "< Settings" link (the others close with their own X)
    "Set_Calibration": True,     # build_calibration_page.py
    "Set_Parameter": False,      # build_info_pages.py
    "Set_About": False,          # build_info_pages.py
}

# Content area x 93..1024, y 59..600.
LEFT = 133
TITLE = (LEFT, 100, 400, 64)          # title picture: words + the blue bar under them
TILE_W, TILE_H, GAP = 202, 176, 14
TILE_Y = (180, 180 + TILE_H + GAP)
BACK = (LEFT - 6, 70, 120, 26)       # sub-pages: "< Settings"
SUB_TITLE = (LEFT, 98, 500, 56)


def title_face(words: str, size: int = 34) -> Image.Image:
    _, _, w, h = TITLE if size == 34 else SUB_TITLE
    s = 4
    big = Image.new("RGBA", (w * s, h * s), rgb(PAGE) + (255,))
    d = ImageDraw.Draw(big)
    bar_y = h - 8
    d.rounded_rectangle((0, bar_y * s, 44 * s, (bar_y + 4) * s), radius=2 * s, fill=NAV_ON)
    image = big.resize((w, h), Image.LANCZOS)
    t = ImageDraw.Draw(image)
    t.text((0, (bar_y - 6) / 2), words, font=font("arialbd.ttf", size), fill=INK, anchor="lm")
    return image


def tile_face(label: str, name: str) -> Image.Image:
    s = 4
    big = Image.new("RGBA", (TILE_W * s, TILE_H * s), rgb(PAGE) + (255,))
    d = ImageDraw.Draw(big)
    rounded(d, (0, 0, TILE_W, TILE_H), fill=WHITE, outline=FIELD_LINE, radius=6)
    image = big.resize((TILE_W, TILE_H), Image.LANCZOS)
    size = 56
    top = 34 if "\n" not in label else 26
    image.alpha_composite(icon(name, size, NAV_INK, px=2.25, cut=WHITE), ((TILE_W - size) // 2, top))
    if name == "monitor":  # the mockup's brightness glyph: a sun on the screen
        image.alpha_composite(icon("sun", 22, NAV_INK, px=1.75, cut=WHITE), ((TILE_W - 22) // 2, top + 9))
    t = ImageDraw.Draw(image)
    face = font("arial.ttf", 18)
    lines = label.split("\n")
    y0 = top + size + 32 - 11 * (len(lines) - 1)
    for i, line in enumerate(lines):
        t.text((TILE_W / 2, y0 + 22 * i), line, font=face, fill=INK, anchor="mm")
    return image


def back_face() -> Image.Image:
    _, _, w, h = BACK
    image = Image.new("RGBA", (w, h), rgb(PAGE) + (255,))
    image.alpha_composite(icon("chevron-left", 18, MUTED, px=1.75), (2, (h - 18) // 2))
    ImageDraw.Draw(image).text((24, h / 2), "Settings", font=font("arial.ttf", 15), fill=MUTED, anchor="lm")
    return image


def render(folder: Path) -> dict[str, Path]:
    faces = {"st_title": title_face("Settings"), "st_back": back_face()}
    for screen, label, name in TILES:
        faces[f"st_tile_{screen}"] = tile_face(label, name)
        faces[f"st_title_{screen}"] = title_face(label.replace("\n", " "), 28)
    folder.mkdir(parents=True, exist_ok=True)
    paths = {}
    for key, image in faces.items():
        path = folder / f"{key}.png"
        image.save(path)
        paths[key] = path
    return paths


def sub_page(project: Project, setting: Screen, name: str) -> Screen:
    """An empty page on the Setting frame; this script's own elements removed if a previous run made it."""
    found = [s for s in project.screens if s.name == name]
    if found:
        screen = found[0]
        for element in screen.elements[::-1]:
            if element.name.startswith(("st_", "nav_")):
                edit.delete_element(project, screen, element.index)
        return screen
    return edit.clone_screen(project, setting, name)


def main(path: str, asset_dir: str) -> None:
    project = Project(path)
    setting = project.screen("Setting")
    for element in [e for e in setting.elements if e.name.startswith("st_")][::-1]:
        edit.delete_element(project, setting, element.index)
    subs = {screen: sub_page(project, setting, screen) for screen, _, _ in TILES}
    frame.prune_bank(project)

    donor = Project(fill.DONOR)
    tpl_rect = donor.element("scr_MainScreen", 1)
    nav = [e for e in setting.elements if e.name.startswith("nav_")]
    goto = nav[0]

    assets = render(Path(asset_dir))
    bank = frame.Bank(project)
    for key, file in assets.items():
        bank.add(key, file)
    bank.commit()

    def picture(screen, key, x, y):
        _, _, w, h = bank.where[key]
        item = edit.clone_element(project, tpl_rect, screen, 0, 0, 10, 10, key)
        clear_links(item)
        frame.face(item, bank, key)
        frame.flat(item, PAGE)
        frame.picture_rect(item, x, y, w, h)
        return item

    def goto_button(screen, key, destination, x, y, name):
        _, _, w, h = bank.where[key]
        item = edit.clone_element(project, goto, screen, x, y, w, h, name)
        item.section.set("GoToScreenID", destination.id)
        for entry in item.section.entries("GoToScreenName"):
            entry.value = destination.name.encode("latin1")
        frame.face(item, bank, key)
        frame.flat(item, PAGE)
        return item

    picture(setting, "st_title", TITLE[0], TITLE[1])
    for i, (screen, _, _) in enumerate(TILES):
        x = LEFT + (i % 4) * (TILE_W + GAP)
        y = TILE_Y[i // 4]
        goto_button(setting, f"st_tile_{screen}", subs[screen], x, y, f"st_tile_{i + 1}")

    for screen, label, _ in TILES:
        page = subs[screen]
        for item in nav:  # side bar with Setting lit, as on the Setting page
            edit.clone_element(project, item, page)
        if OWN_CONTENT.get(screen, True):
            goto_button(page, "st_back", setting, BACK[0], BACK[1], "st_back")
        if screen not in OWN_CONTENT:
            picture(page, f"st_title_{screen}", SUB_TITLE[0], SUB_TITLE[1])

    print(project.save(path))
    print(f"Setting: {len(setting.elements)} elements; sub-pages " + ", ".join(f"{s.name}={s.id}" for s in subs.values()))


if __name__ == "__main__":
    if len(sys.argv) != 3:
        raise SystemExit(__doc__)
    main(*sys.argv[1:])
