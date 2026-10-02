"""Draw the Overview page of the Silo HMI (Home_Overview): the six silos at a glance.

Run:  python build_overview_page.py <project.dpa> <asset folder> <hmi_map.json>

  top    TOTAL   the weight in all six silos, whole kg ("HMI".Ov.Total)
  below  six cards, three by two, one a silo: its number, its own name
         ("HMI".SiloName), its weight and how full it is ("HMI".Ov.Weight /
         .Pct), and two lamps - fill valve and discharge valve open
         ("HMI".Io.Fill n / .Dis n, the real %Q terminals)

The page is the first Home tab and the page HOME opens: the sidebar's HOME
button, the logo and the Login page's close button are pointed at it (the
start-up screen is Login - apply_security.py). The tab row comes from
silo_tabs.py and is redrawn on every Home page.

Everything said in words is an element text in three languages (silo_i18n);
pictures carry no words. Elements are cloned from the project's own pages, so
the Fill page must exist. Re-runnable: elements named "ov_" are removed first.
Run close_popups_on_leave.py afterwards - the tabs are new buttons.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

from PIL import Image

import build_fill_page as fill
import build_silo_frame as frame
import silo_i18n as i18n
import silo_tabs as tabs
from build_clean_page import VALUE, canvas, find
from build_fill_page import CARD_LINE, TILE, clear_links, line_art, picture_on, rounded
from build_io_page import DOT, ON_LINE, dot_face
from build_silo_frame import INK, MUTED, NAV_INK, PAGE, WHITE, bgr, icon, rgb
from dpa import edit
from dpa.model import Project

SCREEN = "Home_Overview"
HOME_LINKS = ("nav_home", "fr_logo", "ln_close")     # Goto buttons that mean "home"
LEFT, CENTRE, RIGHT = 33, 34, 36

# Home grid: content x 100..1016, y 66..592.
TOTAL = (100, 66, 916, 84)
CARD_W, CARD_H = 298, 211
CARD_X = (100, 409, 718)
CARD_Y = (160, 381)
CARDS = [(CARD_X[i % 3], CARD_Y[i // 3], CARD_W, CARD_H) for i in range(6)]
SILO_H = 170                    # the drawing, 16 px in from the card's left edge
TEXT_X = 96                     # where the words start inside a card
RULE_Y = 156


# --- pictures (no words in any of them) --------------------------------------------

def total_face() -> Image.Image:
    _, _, w, h = TOTAL
    big, d = canvas(w, h)
    rounded(d, (0, 0, w, h))
    rounded(d, (16, (h - 44) // 2, 44, 44), fill=TILE, outline=TILE, radius=6)
    image = big.resize((w, h), Image.LANCZOS)
    image.alpha_composite(icon("weight", 28, NAV_INK, px=1.5, cut=TILE), (24, (h - 28) // 2))
    return image


def silo_art(height: int) -> Image.Image:
    """Sang's silo drawing (drawn in red) in the page ink, on the card's white."""
    art = line_art("Silo_3.png", height=height, back=WHITE)
    mask = art.convert("L").point(lambda v: min(255, (255 - v) * 2) if v < 235 else 0)
    out = Image.new("RGBA", art.size, rgb(WHITE) + (255,))
    out.paste(Image.new("RGBA", art.size, rgb(NAV_INK) + (255,)), (0, 0), mask)
    return out


def silo_face() -> Image.Image:
    big, d = canvas(CARD_W, CARD_H)
    rounded(d, (0, 0, CARD_W, CARD_H))
    rounded(d, (CARD_W - 16 - 28, 14, 28, 28), fill=TILE, outline=TILE, radius=5)     # behind the silo's number
    d.line((TEXT_X * 4, RULE_Y * 4, (CARD_W - 16) * 4, RULE_Y * 4), fill=CARD_LINE, width=4)
    image = big.resize((CARD_W, CARD_H), Image.LANCZOS)
    silo = silo_art(SILO_H)
    image.alpha_composite(silo, (16 + (64 - silo.width) // 2, (CARD_H - SILO_H) // 2))
    return image


def render(folder: Path) -> dict[str, Path]:
    faces = {"ov_total": total_face(), "ov_card": silo_face(),
             "ov_dot_0": dot_face(None), "ov_dot_1": dot_face(ON_LINE), **tabs.faces()}
    folder.mkdir(parents=True, exist_ok=True)
    paths = {}
    for key, image in faces.items():
        paths[key] = folder / f"{key}.png"
        image.save(paths[key])
    return paths


# --- elements ---------------------------------------------------------------------------

def main(path: str, asset_dir: str, map_file: str) -> None:
    address = {k: v["address"] for k, v in json.load(open(map_file, encoding="utf-8"))["members"].items()}
    project = Project(path)
    i18n.ensure_languages(project)

    home = "Home_Fill"
    existing = [s for s in project.screens if s.name == SCREEN]
    page = existing[0] if existing else edit.clone_screen(project, project.screen(home), SCREEN)
    for slot in i18n.SLOTS:
        for entry in page.section.entries(f"wScreenDESCTextLen00{slot}"):
            entry.set_text(SCREEN)
    for element in page.elements[::-1]:
        if not existing or element.name.startswith(("ov_", "nav_")):
            edit.delete_element(project, page, element.index)
    tabs.clear(project)

    tpl_rect, tpl_text = find(project, home, "fl_process"), find(project, home, "fl_status_bar_txt1")
    tpl_num, tpl_name = find(project, home, "fl_rate"), find(project, home, "fl_silo_name")
    tpl_graphic = find(project, home, "fl_sfv")
    nav = [find(project, home, n) for n in ("nav_home", "nav_setting", "nav_data")]
    frame.prune_bank(project)

    bank = frame.Bank(project)
    for key, file in render(Path(asset_dir)).items():
        bank.add(key, file)
    bank.commit()

    def style(item, size, colour, bold=False, align=LEFT):
        for state in item.states:
            state.set("FontColor", bgr(colour))
            state.set("FontBold", 1 if bold else 0)
            state.set("FontAlign", align)
            for slot in i18n.SLOTS:
                state.set(f"FontName{slot}", "Arial")
                state.set(f"FontSize{slot}", size)

    def picture(name, key, box):
        x, y, w, h = box
        item = edit.clone_element(project, tpl_rect, page, 0, 0, 10, 10, name)
        clear_links(item)
        frame.face(item, bank, key)
        frame.flat(item, PAGE)
        for state in item.states:
            state.set("TransColor", bgr(PAGE))
        frame.picture_rect(item, x, y, w, h)

    def text(name, box, texts, size=14, colour=INK, bold=False, align=LEFT):
        x, y, w, h = box
        item = edit.clone_element(project, tpl_text, page, x, y, w, h, name)
        style(item, size, colour, bold, align)
        i18n.words(item, texts, size)
        return item

    def number(name, box, member, size, digits, decimals=0, align=RIGHT, colour=VALUE):
        x, y, w, h = box
        item = edit.clone_element(project, tpl_num, page, x, y, w, h, name)
        clear_links(item)
        item.section.set("ReadVar", address[member])
        item.section.set("IntNum", digits)
        item.section.set("DotNum", decimals)
        style(item, size, colour, True, align)
        return item

    def lamp(name, x, y, member):
        item = edit.clone_element(project, tpl_graphic, page, 0, 0, 10, 10, name)
        clear_links(item)
        item.section.set("ReadVar", address[member])
        for n, key in enumerate(("ov_dot_0", "ov_dot_1")):
            picture_on(item, n, bank, key, x, y, DOT, DOT, WHITE)
        frame.flat(item, WHITE)
        frame.picture_rect(item, x, y, DOT, DOT)

    # --- header: sidebar, the tab row on every Home page, "home" means this page ---------
    for button in nav:
        edit.clone_element(project, button, page)
    tabs.place(project, bank)
    for screen in project.screens:
        for element in screen.elements:
            if element.type_code == "1.10" and element.name in HOME_LINKS:
                element.section.set("GoToScreenID", page.id)
                for entry in element.section.entries("GoToScreenName"):
                    entry.value = SCREEN.encode("latin1")

    # --- total ------------------------------------------------------------------------------
    tx, ty, tw, th = TOTAL
    picture("ov_total", "ov_total", TOTAL)
    text("ov_t_total", (tx + 76, ty + 20, 420, 21), ("TOTAL WEIGHT", "TỔNG TRỌNG LƯỢNG", "POIDS TOTAL"), 14, INK, True)
    text("ov_t_total_of", (tx + 76, ty + 44, 420, 21), ("All six silos", "Cả 6 bồn", "Les six silos"), 14, MUTED)
    number("ov_total_kg", (tx + tw - 300, ty + 10, 230, 64), "Ov.Total", 52, 5)
    text("ov_t_total_unit", (tx + tw - 64, ty + 38, 44, 27), "kg", 18, INK)

    # --- one card a silo ------------------------------------------------------------------
    for n, (x, y, w, h) in enumerate(CARDS, 1):
        picture(f"ov_card_{n}", "ov_card", (x, y, w, h))
        text(f"ov_t_no_{n}", (x + w - 44, y + 17, 28, 21), str(n), 14, MUTED, True, CENTRE)
        name = edit.clone_element(project, tpl_name, page, x + TEXT_X, y + 16, w - TEXT_X - 52, 24, f"ov_name_{n}")
        clear_links(name)
        name.section.set("ReadVar", address[f"SiloName[{n}]"])
        style(name, 16, INK, True)
        number(f"ov_weight_{n}", (x + TEXT_X, y + 56, 116, 46), f"Ov.Weight[{n}]", 36, 4, 1)
        text(f"ov_t_kg_{n}", (x + TEXT_X + 120, y + 72, 30, 24), "kg", 16, INK)
        number(f"ov_pct_{n}", (x + TEXT_X, y + 112, 46, 26), f"Ov.Pct[{n}]", 18, 3, colour=INK)
        text(f"ov_t_pct_{n}", (x + TEXT_X + 50, y + 115, 120, 21), ("% full", "% đầy", "% plein"), 14, MUTED)
        lamp(f"ov_fill_{n}", x + TEXT_X, y + RULE_Y + 20, f"Io.Fill{n}")
        text(f"ov_t_fill_{n}", (x + TEXT_X + 22, y + RULE_Y + 17, 64, 21), ("Filling", "Nạp", "Rempl."), 14, MUTED)
        lamp(f"ov_dis_{n}", x + TEXT_X + 94, y + RULE_Y + 20, f"Io.Dis{n}")
        text(f"ov_t_dis_{n}", (x + TEXT_X + 116, y + RULE_Y + 17, 80, 21), ("Discharging", "Xả", "Vidange"), 14, MUTED)

    i18n.ensure_languages(project)
    print(project.save(path))
    print(f"{SCREEN} (id {page.id}): {len(page.elements)} elements; tabs on {', '.join(s.name for s in tabs.pages(project))}")


if __name__ == "__main__":
    if len(sys.argv) != 4:
        raise SystemExit(__doc__)
    main(*sys.argv[1:])
