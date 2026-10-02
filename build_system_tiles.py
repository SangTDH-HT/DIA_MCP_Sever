"""Settings page of the Silo HMI: tiles in three languages, three of them the panel's own functions.

Run:  python build_system_tiles.py <project.dpa> <asset folder>

  Date and time      opens the panel's date/time setting      (System Date and Time, 12.1)
  Screen Brightness  opens the panel's contrast / brightness  (Contrast Brightness, 12.4)
  Language           goes to Set_Language: one button a language, under its flag (Language Change, 12.12)

The other tiles stay Goto Screen buttons. Every tile face is redrawn without
its words: the label is the button's own text (silo_i18n), three empty lines
above it so it sits under the icon. The "< Settings" link of the sub-pages and
the page title get their three languages here too.

The three system buttons are cloned from Sang's older Silo HMI files (DONORS).
Re-runnable: the tiles are found by name (st_tile_1..8), Set_Language is
emptied of its "lg_" elements first.
"""

from __future__ import annotations

import math
import sys
from pathlib import Path

from PIL import Image, ImageDraw

import build_fill_page as fill
import build_setting_page as setting
import build_silo_frame as frame
import silo_i18n as i18n
from build_fill_page import FIELD_LINE, picture_on, rounded
from build_silo_frame import INK, MUTED, NAV_INK, NAV_ON, PAGE, WHITE, bgr, icon, rgb
from dpa import edit, macro
from dpa.model import Project

OLD = r"C:\OTL\17.OTL_SILO\OTL_Silo6\HMI"
DONORS = {  # type -> (file, screen, element index)
    "date": (OLD + r"\HMI_UPDATE.dpa", "pop_Setting", 13),
    "brightness": (OLD + r"\HMI_UPDATE.dpa", "pop_Setting", 11),
    "language": (OLD + r"\FILETEST.dpa", "pop_Setting", 0),
}
TILES = (  # tile number -> (icon, system function or None, (English, Vietnamese, French))
    ("sliders-vertical", None, ("Parameter", "Thông số", "Paramètres")),
    ("arrow-left-right", None, ("I/O", "I/O", "E/S")),
    ("scale", None, ("Calibration", "Hiệu chỉnh cân", "Étalonnage")),
    ("users", None, ("Account\nManagement", "Quản lý\ntài khoản", "Gestion des\ncomptes")),
    ("clock", "date", ("Date and time", "Ngày và giờ", "Date et heure")),
    ("languages", None, ("Language", "Ngôn ngữ", "Langue")),
    ("monitor", "brightness", ("Screen Brightness", "Độ sáng màn hình", "Luminosité de l'écran")),
    ("info", None, ("About", "Giới thiệu", "À propos")),
)
BACK_WORDS = ("Settings", "Cài đặt", "Réglages")
TITLE_WORDS = ("Settings", "Cài đặt", "Réglages")
HEADS = {  # sub-page -> its title beside the back link
    "Set_Parameter": ("Silo settings", "Cài đặt bồn cân", "Réglages des silos"),
    "Set_IO": ("I/O", "I/O", "E/S"),
    "Set_Calibration": ("Scale calibration", "Hiệu chỉnh bồn cân", "Étalonnage des silos"),
    "Set_Account": ("Account Management", "Quản lý tài khoản", "Gestion des comptes"),
    "Set_DateTime": ("Date and time", "Ngày và giờ", "Date et heure"),
    "Set_Language": ("Language", "Ngôn ngữ", "Langue"),
    "Set_Brightness": ("Screen Brightness", "Độ sáng màn hình", "Luminosité de l'écran"),
}
LANG_PAGE = "Set_Language"
SELECTED = ("● Selected", "● Đang chọn", "● Sélectionnée")   # shown under the language in use
SELECTED_INK = "#1F6FB2"
LANG_W, LANG_H = 202, 142
LANG_AT = [(133 + 216 * i, 124) for i in range(3)]


def tile_face(name: str, two_lines: bool) -> Image.Image:
    return setting.tile_face("\n" if two_lines else "", name)   # the script's own face, no words


def back_face() -> Image.Image:
    _, _, w, h = setting.BACK
    image = Image.new("RGBA", (w, h), rgb(PAGE) + (255,))
    image.alpha_composite(icon("chevron-left", 18, MUTED, px=1.75), (2, (h - 18) // 2))
    return image


FLAG_W, FLAG_H = 66, 44


def flag(slot: int) -> Image.Image:
    """The flag of a language slot - United Kingdom, Vietnam, France - drawn at 4x."""
    w, h = FLAG_W * 4, FLAG_H * 4
    art = Image.new("RGBA", (w, h), (255, 255, 255, 255))
    d = ImageDraw.Draw(art)
    if slot == 0:        # Union Jack: white and red saltire on blue, then the white and red cross
        d.rectangle((0, 0, w, h), fill="#012169")
        for a, b in (((0, 0), (w, h)), ((0, h), (w, 0))):
            d.line((a, b), fill="#FFFFFF", width=round(h * 0.2))
        for a, b in (((0, 0), (w, h)), ((0, h), (w, 0))):
            d.line((a, b), fill="#C8102E", width=round(h * 0.07))
        d.rectangle((w / 2 - h / 6, 0, w / 2 + h / 6, h), fill="#FFFFFF")
        d.rectangle((0, h / 2 - h / 6, w, h / 2 + h / 6), fill="#FFFFFF")
        d.rectangle((w / 2 - h / 10, 0, w / 2 + h / 10, h), fill="#C8102E")
        d.rectangle((0, h / 2 - h / 10, w, h / 2 + h / 10), fill="#C8102E")
    elif slot == 1:      # Vietnam: yellow five-pointed star on red
        d.rectangle((0, 0, w, h), fill="#DA251D")
        cx, cy, outer = w / 2, h / 2 + h * 0.02, h * 0.3
        inner = outer * 0.382
        points = []
        for k in range(10):
            radius = outer if k % 2 == 0 else inner
            angle = math.radians(-90 + 36 * k)
            points.append((cx + radius * math.cos(angle), cy + radius * math.sin(angle)))
        d.polygon(points, fill="#FFFF00")
    else:                # France: blue, white, red
        d.rectangle((0, 0, w / 3, h), fill="#0055A4")
        d.rectangle((2 * w / 3, 0, w, h), fill="#EF4135")
    mask = Image.new("L", (w, h), 0)
    ImageDraw.Draw(mask).rounded_rectangle((0, 0, w - 1, h - 1), radius=16, fill=255)
    art.putalpha(mask)
    ImageDraw.Draw(art).rounded_rectangle((0, 0, w - 1, h - 1), radius=16, outline=FIELD_LINE, width=4)
    return art.resize((FLAG_W, FLAG_H), Image.LANCZOS)


def lang_face(slot: int) -> Image.Image:
    big = Image.new("RGBA", (LANG_W * 4, LANG_H * 4), rgb(PAGE) + (255,))
    rounded(ImageDraw.Draw(big), (0, 0, LANG_W, LANG_H), fill=WHITE, outline=FIELD_LINE, radius=6)
    image = big.resize((LANG_W, LANG_H), Image.LANCZOS)
    image.alpha_composite(flag(slot), ((LANG_W - FLAG_W) // 2, 22))
    return image


def style(item, size, colour, bold=False, align=34):
    for state in item.states:
        state.set("FontColor", bgr(colour))
        state.set("FontBold", 1 if bold else 0)
        state.set("FontAlign", align)


def main(path: str, asset_dir: str) -> None:
    project = Project(path)
    i18n.ensure_languages(project)
    page = project.screen("Setting")
    lang_page = project.screen(LANG_PAGE)
    for element in lang_page.elements[::-1]:
        if element.name.startswith("lg_"):
            edit.delete_element(project, lang_page, element.index)

    tiles = {e.name: e for e in page.elements if e.name.startswith("st_tile_")}
    rects = {name: tuple(e.section.get_int(k) for k in ("X", "Y", "Width", "Height")) for name, e in tiles.items()}
    goto_tpl = tiles["st_tile_1"]
    # a tile that becomes a system button is replaced, so drop it before the bank is pruned
    for n, (_, system, _) in enumerate(TILES, 1):
        if system and tiles[f"st_tile_{n}"].type_code == "1.10":
            edit.delete_element(project, page, tiles[f"st_tile_{n}"].index)
            del tiles[f"st_tile_{n}"]
    frame.prune_bank(project)

    folder = Path(asset_dir)
    folder.mkdir(parents=True, exist_ok=True)
    faces = {f"st_tileface_{n}": tile_face(name, "\n" in texts[0]) for n, (name, _, texts) in enumerate(TILES, 1)}
    faces["st_backface"] = back_face()
    for slot in i18n.SLOTS:
        faces[f"lg_face_{slot}"] = lang_face(slot)
    bank = frame.Bank(project)
    for key, image in faces.items():
        image.save(folder / f"{key}.png")
        bank.add(key, folder / f"{key}.png")
    bank.commit()

    donors = {kind: Project(f).element(screen, index) for kind, (f, screen, index) in DONORS.items()}

    def system_button(kind, screen, name, box, key, back=PAGE):
        x, y, w, h = box
        item = edit.clone_element(project, donors[kind], screen, x, y, w, h, name)
        i18n.ensure_languages(project)        # the donor has two language slots
        item.section.set("Style", 3)
        item.section.set("Level", 0)
        item.section.set("AutoResizeByText", 0)
        if item.section.get("VisibleVar") is not None:
            item.section.set("VisibleVar", "None")
            item.section.set("VisibleCondition", 1)
        for macro_key in ("BeforeExecMacroLen", "AfterExecMacroLen"):
            macro.set_macro(item.section, macro_key, None)
        for state in item.states:
            for colour_key in ("FgColor", "BgColor"):
                state.set(colour_key, bgr(back))
        picture_on(item, 0, bank, key, x, y, w, h, back)
        for state in item.states:
            state.set("PIB Name", "PicBank02")
        return item

    # --- the eight tiles -------------------------------------------------------------
    for n, (_, system, texts) in enumerate(TILES, 1):
        name = f"st_tile_{n}"
        box = rects[name]
        if system:
            item = tiles.get(name) or system_button(system, page, name, box, f"st_tileface_{n}")
            picture_on(item, 0, bank, f"st_tileface_{n}", *box, PAGE)
        else:
            item = tiles[name]
            frame.face(item, bank, f"st_tileface_{n}")
            frame.flat(item)
        style(item, 18, INK)
        # the label sits under the icon: empty lines above push it below the middle
        lead = "\n\n" if "\n" in texts[0] else "\n\n\n"
        i18n.words(item, tuple(lead + t for t in texts), 18, margin=16)

    # --- page title and the back link of every sub-page ---------------------------------
    for element in page.elements:
        if element.name == "st_title_txt1":
            i18n.words(element, TITLE_WORDS)
    for screen in project.screens:
        for element in screen.elements:
            if element.name == "st_back":
                frame.face(element, bank, "st_backface")
                frame.flat(element)
                style(element, 14, MUTED, align=33)
                i18n.words(element, tuple("      " + t for t in BACK_WORDS), 14, margin=0)
            elif element.name == f"st_head_{screen.name}_txt1" and screen.name in HEADS:
                i18n.words(element, HEADS[screen.name], width=480)

    # --- Set_Language: one button a language, each named in its own language ----------
    # The panel has no address that tells which language is showing, so the mark of
    # the chosen one is made of the languages themselves: a button's name is larger
    # and its "selected" line has words only in that button's own language slot.
    label_tpl = next(e for e in lang_page.elements if e.name == f"st_head_{LANG_PAGE}_txt1")
    for slot, ((x, y), name) in enumerate(zip(LANG_AT, i18n.LANGUAGES)):
        item = system_button("language", lang_page, f"lg_{slot}", (x, y, LANG_W, LANG_H), f"lg_face_{slot}")
        item.section.set("LangValue", slot)
        style(item, 18, INK, True)
        i18n.words(item, "\n\n" + name, 18)
        for state in item.states:
            state.set(f"FontSize{slot}", 22)
        mark = edit.clone_element(project, label_tpl, lang_page, x + 16, y + LANG_H - 34, LANG_W - 32, 20, f"lg_sel_{slot}")
        style(mark, 12, SELECTED_INK, True)
        i18n.words(mark, tuple(SELECTED[s] if s == slot else "" for s in i18n.SLOTS), 12)

    i18n.ensure_languages(project)
    print(project.save(path))
    kinds = [e.type_code for e in project.screen("Setting").elements if e.name.startswith("st_tile_")]
    print(f"Setting: tiles {kinds}; {LANG_PAGE}: {len(i18n.LANGUAGES)} language buttons")


if __name__ == "__main__":
    if len(sys.argv) != 3:
        raise SystemExit(__doc__)
    main(*sys.argv[1:])
