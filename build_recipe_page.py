"""Blend recipes of the Silo HMI: kept in the panel (Enhanced Recipe), made, changed and cleared on their own page.

Run:  python build_recipe_page.py <project.dpa> <asset folder> <hmi_map.json>

The panel's Enhanced Recipe holds the recipes: one row a recipe, seven fields -
the name (20 words) and the kg taken from silo 1..6 (floating, 3.1). The setup
is the one of the old silo panel (HMISiloFinal.dpa), copied section for section.
Registers: ENRCPNO the row in use, ENRCP0 its name, ENRCP1..6 its weights;
row k of the store itself is ENRCP(7k) .. ENRCP(7k+6).

What this script does, re-runnable:

  setup        [EnhanceRcp] and the recipe control / status words ($20.., $30..)
               as in the old project; the recipe's PLC address is "HMI".Rc.
  Set_Recipe   the recipe page, opened from the gear on the Blend page's recipe card:
                 left   RECIPES  ten rows, tap one to work on it (blue bar = in use)
                 right  the row in use: name, kg of each silo, total, Clear recipe;
                        a total over 120 kg turns the total row red ("HMI".Rc.Over)
               A new recipe is an empty row given a name and weights; clearing
               blanks the name and zeroes the weights (the panel asks first).
  Home_Blend   the recipe field and its list read the names from the panel and
               write ENRCPNO; the list is ten rows in two columns, its header as
               wide as both; the card's gear (it used to open Setting) opens Set_Recipe.
  to the PLC   while the Blend page or the recipe page is shown, the page's cycle
               macro copies the row in use to "HMI".Rc (six REAL, then the row
               number). FB "HMI_Map" REGION 11 takes it from there, never during
               a blend batch.

Everything said in words is an element text in three languages (silo_i18n).
Elements made here are named "rc_". Run it after build_home_pages.py /
bind_plc.py (they put the recipe list back on PLC names) and before
close_popups_on_leave.py.
"""

from __future__ import annotations

import copy
import json
import sys
from pathlib import Path

from PIL import Image, ImageDraw

import build_silo_frame as frame
import silo_i18n as i18n
from build_clean_page import BAD, VALUE, add_states, canvas, card, find
from build_fill_page import CARD_LINE, FIELD_LINE, STOP, TILE, clear_links, picture_on, rounded
from build_setting_page import CONTENT_TOP
from build_silo_frame import INK, MUTED, NAV_ON, PAGE, WHITE, bgr, font, icon
from dpa import edit, macro
from dpa.model import Project

SETUP_DONOR = r"C:\OTL\17.OTL_SILO\OTL_Silo6\HMI\HMISiloFinal.dpa"
SCREEN, BLEND, POPUP = "Set_Recipe", "Home_Blend", "pop_CongThuc"
LEFT, CENTRE, RIGHT = 33, 34, 36
FIELDS = 7                    # name + six weights: row k starts at ENRCP(7k)
ROWS = 10                     # rows the pages show (the store has 20)
NAME_CHARS = 20
MAX_KG = 120                  # one blend batch, the limit FB "Silo_Control" checks
CYCLE_MS = 500
CLEAR_BIT = "$254.0"          # the Clear button's own bit, inside the panel

# Recipe page: content x 100..1016, y CONTENT_TOP..592.
LIST = (100, CONTENT_TOP, 300, 488)
EDIT = (410, CONTENT_TOP, 606, 488)
ROW = [(116, CONTENT_TOP + 54 + 42 * i, 268, 38) for i in range(ROWS)]
MARK = (106, ROW[0][1], 4, 42 * ROWS - 4)
NAME_BOX = (500, CONTENT_TOP + 52, 500, 40)
TILE_W, TILE_H = 186, 104
TILES = [(426 + 196 * (i % 3), CONTENT_TOP + 110 + 114 * (i // 3), TILE_W, TILE_H) for i in range(6)]
EDIT_RULE = CONTENT_TOP + 346
CLEAR = (826, CONTENT_TOP + 420, 178, 44)

OVER = (EDIT[0] + 10, EDIT_RULE + 8, EDIT[2] - 20, 48)      # the total row, red when over the limit
# The list on the Blend page: header over the recipe field, ten rows in two columns under it.
POP_COLS, POP_ROW_W, POP_ROW_H, POP_HEAD_H = 2, 200, 40, 42
POP_RIGHT = 1000              # the recipe field ends here; the list hangs from the same edge

CLEAR_WORDS = ("Clear recipe", "Xoá công thức", "Effacer la recette")
LIMIT_WORDS = (
    ((f"One batch takes {MAX_KG} kg at most", f"Một mẻ tối đa {MAX_KG} kg", f"Un lot : {MAX_KG} kg au maximum"), MUTED, False),
    ((f"Over {MAX_KG} kg: this recipe will not start", f"Vượt {MAX_KG} kg: công thức này sẽ không chạy",
      f"Plus de {MAX_KG} kg : la recette ne démarrera pas"), BAD, True),
)


# --- pictures (no words in any of them) --------------------------------------------

def edit_card() -> Image.Image:
    ox, oy = EDIT[0], EDIT[1]

    def more(d):
        x, y, w, h = NAME_BOX
        rounded(d, (x - ox, y - oy, w, h), outline=FIELD_LINE)
        for tx, ty, tw, th in TILES:
            rounded(d, (tx - ox, ty - oy, tw, th), fill=WHITE, outline=CARD_LINE)
            rounded(d, (tx - ox + 12, ty - oy + 10, 24, 24), fill=TILE, outline=TILE, radius=5)
            rounded(d, (tx - ox + 12, ty - oy + 48, 118, 44), outline=FIELD_LINE)
        ry = EDIT_RULE - oy
        d.line((16 * 4, ry * 4, (EDIT[2] - 16) * 4, ry * 4), fill=CARD_LINE, width=4)
    return card(EDIT, "square-pen", more)


def row_face() -> Image.Image:
    _, _, w, h = ROW[0]
    big, d = canvas(w, h, WHITE)
    rounded(d, (0, 0, w, h), fill=WHITE, outline=FIELD_LINE, radius=6)
    rounded(d, (8, (h - 26) // 2, 26, 26), fill=TILE, outline=TILE, radius=5)
    return big.resize((w, h), Image.LANCZOS)


def mark_face(row: int) -> Image.Image:
    """The bar beside the row in use; row 0 is no bar."""
    _, _, w, h = MARK
    big, d = canvas(w, h, WHITE)
    if row:
        y = (ROW[row - 1][1] - MARK[1]) * 4
        d.rounded_rectangle((0, y + 24, w * 4 - 1, y + ROW[0][3] * 4 - 25), radius=8, fill=NAV_ON)
    return big.resize((w, h), Image.LANCZOS)


def clear_face(pressed: bool) -> Image.Image:
    _, _, w, h = CLEAR
    big, d = canvas(w, h, WHITE)
    rounded(d, (0, 0, w, h), fill=STOP[0] if pressed else WHITE, outline=BAD, radius=6)
    return big.resize((w, h), Image.LANCZOS)


def over_face(over: bool) -> Image.Image:
    _, _, w, h = OVER
    big, d = canvas(w, h, WHITE)
    if over:
        rounded(d, (0, 0, w, h), fill=STOP[0], outline=BAD, radius=6)
    return big.resize((w, h), Image.LANCZOS)


def pop_head_face() -> Image.Image:
    """The open list's header: the recipe field's own look, as wide as both columns."""
    w, h = POP_COLS * POP_ROW_W, POP_HEAD_H
    big, d = canvas(w, h, WHITE)
    d.rounded_rectangle((0, 0, w * 4 - 1, (h + 8) * 4), radius=24, fill=WHITE, outline=FIELD_LINE, width=4)
    d.line((0, (h - 1) * 4, w * 4, (h - 1) * 4), fill=CARD_LINE, width=4)
    image = big.resize((w, h), Image.LANCZOS)
    image.alpha_composite(icon("chevron-up", 18, MUTED, px=1.75, cut=WHITE), (w - 30, (h - 18) // 2))
    return image


def pop_row_face(n: int) -> Image.Image:
    """Row n of the list (1..ROWS, down the left column first): its number, the name is a live element over it."""
    w, h = POP_ROW_W, POP_ROW_H
    per = ROWS // POP_COLS
    column, last = (n - 1) // per, (n - 1) % per == per - 1
    big, d = canvas(w, h, WHITE)
    edge = w * 4 - 2
    d.line((1, 0, 1, h * 4), fill=FIELD_LINE if column == 0 else CARD_LINE, width=4)
    if column == POP_COLS - 1:
        d.line((edge, 0, edge, h * 4), fill=FIELD_LINE, width=4)
    if last:
        d.line((0, h * 4 - 2, w * 4, h * 4 - 2), fill=FIELD_LINE, width=4)
    else:
        d.line((12 * 4, h * 4 - 2, (w - 12) * 4, h * 4 - 2), fill=CARD_LINE, width=4)
    image = big.resize((w, h), Image.LANCZOS)
    ImageDraw.Draw(image).text((20, h / 2), str(n), font=font("arial.ttf", 14), fill=MUTED, anchor="mm")
    return image


def render(folder: Path) -> dict[str, Path]:
    faces = {"rc_list": card(LIST, "list-checks"), "rc_edit": edit_card(), "rc_row": row_face(),
             "rc_clear_0": clear_face(False), "rc_clear_1": clear_face(True),
             "rc_over_0": over_face(False), "rc_over_1": over_face(True), "rc_pop_head": pop_head_face(),
             **{f"rc_pop_row_{n}": pop_row_face(n) for n in range(1, ROWS + 1)},
             **{f"rc_mark_{n}": mark_face(n) for n in range(ROWS + 1)}}
    folder.mkdir(parents=True, exist_ok=True)
    paths = {}
    for key, image in faces.items():
        paths[key] = folder / f"{key}.png"
        image.save(paths[key])
    return paths


# --- setup and macros --------------------------------------------------------------

def setup(project: Project, recipe_address: str) -> None:
    """The Enhanced Recipe and its control block, as the old silo panel had them."""
    donor = Project(SETUP_DONOR)
    section = project.doc.first("EnhanceRcp")
    section.items = copy.deepcopy(donor.doc.first("EnhanceRcp").items)
    section.set("ReadEnRecipeVar", recipe_address)
    application, theirs = project.doc.first("Application"), donor.doc.first("Application")
    for entry in theirs.items:
        key = getattr(entry, "key", b"").decode("latin1")
        if key.startswith(("Ctrl", "Status", "ReadCtrl", "ReadStatus")) and "Recipe" in key or key in ("ReadCtrlVar", "ReadStatusVar"):
            application.set(key, entry.value.decode("latin1"))


def send_macro(address: dict[str, str]) -> bytes:
    """The row in use, to the PLC: the six weights first, the row number last."""
    lines = [macro.fmov_statement(address[f"Rc.Kg[{n}]"], f"ENRCP{n}") for n in range(1, 7)]
    lines.append(macro.assign_statement(address["Rc.No"], "ENRCPNO"))
    return macro.program(*lines)


def clear_macro() -> bytes:
    """Blank the name of the row in use and zero its six weights."""
    lines = [macro.fillasc_statement("ENRCP0", " " * (2 * NAME_CHARS))]
    lines += [macro.fmov_statement(f"ENRCP{n}", "0") for n in range(1, 7)]
    return macro.program(*lines)


# --- elements ---------------------------------------------------------------------------

def main(path: str, asset_dir: str, map_file: str) -> None:
    address = {k: v["address"] for k, v in json.load(open(map_file, encoding="utf-8"))["members"].items()}
    project = Project(path)
    i18n.ensure_languages(project)
    setup(project, address["Rc.NameRaw[1]"].replace("DBB", "DBD"))

    blend, popup = project.screen(BLEND), project.screen(POPUP)
    existing = [s for s in project.screens if s.name == SCREEN]
    page = existing[0] if existing else edit.clone_screen(project, project.screen("Setting"), SCREEN)
    for slot in i18n.SLOTS:
        for entry in page.section.entries(f"wScreenDESCTextLen00{slot}"):
            entry.set_text(SCREEN)
    for screen in (page, blend, popup):
        for element in screen.elements[::-1]:
            if element.name.startswith("rc_") or (screen is page and element.name.startswith("nav_")):
                edit.delete_element(project, screen, element.index)

    home = "Home_Fill"
    tpl_rect, tpl_text = find(project, home, "fl_process"), find(project, home, "fl_status_bar_txt1")
    tpl_num, tpl_name = find(project, home, "fl_rate"), find(project, home, "fl_silo_name")
    tpl_ind = find(project, home, "fl_fill_mode")
    tpl_push, tpl_graphic = find(project, home, "fl_start"), find(project, home, "fl_sfv")
    tpl_entry, tpl_chars = find(project, "Set_Parameter", "pr_1_1"), find(project, "Login", "ln_user")
    tpl_row = find(project, POPUP, "bl_row_1")
    tpl_back, tpl_head = find(project, "Set_IO", "st_back"), find(project, "Set_IO", "st_head_Set_IO")
    tpl_head_text = find(project, "Set_IO", "st_head_Set_IO_txt1")
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

    def picture(key, box):
        x, y, w, h = box
        item = edit.clone_element(project, tpl_rect, page, 0, 0, 10, 10, key)
        clear_links(item)
        frame.face(item, bank, key)
        frame.flat(item, PAGE)
        for state in item.states:
            state.set("TransColor", bgr(PAGE))
        frame.picture_rect(item, x, y, w, h)

    def text(name, box, texts, size=14, colour=INK, bold=False, align=LEFT, screen=None):
        x, y, w, h = box
        item = edit.clone_element(project, tpl_text, screen or page, x, y, w, h, name)
        style(item, size, colour, bold, align)
        i18n.words(item, texts, size)
        return item

    def number(name, box, read, size, digits, decimals=0, align=RIGHT, colour=VALUE):
        x, y, w, h = box
        item = edit.clone_element(project, tpl_num, page, x, y, w, h, name)
        clear_links(item)
        item.section.set("ReadVar", read)
        item.section.set("IntNum", digits)
        item.section.set("DotNum", decimals)
        style(item, size, colour, True, align)
        return item

    def chars(name, box, read, size, colour=INK, bold=True, screen=None):
        x, y, w, h = box
        item = edit.clone_element(project, tpl_name, screen or page, x, y, w, h, name)
        clear_links(item)
        item.section.set("ReadVar", read)
        item.section.set("StringLen", NAME_CHARS)
        style(item, size, colour, bold)
        return item

    def goto(screen, name, template, destination, box, texts=None, key=None):
        x, y, w, h = box
        item = edit.clone_element(project, template, screen, x, y, w, h, name)
        item.section.set("GoToScreenID", destination.id)
        for entry in item.section.entries("GoToScreenName"):
            entry.value = destination.name.encode("latin1")
        if key:
            frame.face(item, bank, key)
            frame.flat(item, WHITE)
        if texts is not None:
            i18n.words(item, texts)
        return item

    # --- setup of the two pages that hand the recipe to the PLC ---------------------------
    for screen in (blend, page):
        macro.set_macro(screen.section, "CycleMacroLen", send_macro(address))
        screen.section.set("CycleMacroDelayTime", CYCLE_MS)
        screen.section.set("EnableCycleMacro", 1)

    # --- Blend page: names from the panel, the list picks ENRCPNO, the gear opens the page ---
    for screen in (blend, popup):
        find(project, screen.name, "bl_name").section.set("ReadVar", "ENRCP0")
    per = ROWS // POP_COLS
    pw, ph = POP_COLS * POP_ROW_W, POP_HEAD_H + POP_ROW_H * per
    for key, value in (("Width", pw), ("Height", ph), ("DocSizeX", pw), ("DocSizeY", ph), ("SubScreenX", POP_RIGHT - pw)):
        popup.section.set(key, value)
    close = find(project, POPUP, "bl_silo_close")
    for key, value in (("X", 0), ("Y", 0), ("Width", pw), ("Height", POP_HEAD_H)):
        close.section.set(key, value)
    for n in range(len(close.states)):
        picture_on(close, n, bank, "rc_pop_head", 0, 0, pw, POP_HEAD_H, WHITE)
    find(project, POPUP, "bl_name").section.set("X", pw - POP_ROW_W + 12)       # still over the field on the page
    text("rc_pop_title", (12, 10, pw - POP_ROW_W - 20, 21), ("Recipes", "Công thức", "Recettes"), 14, MUTED, screen=popup)
    have = {e.name: e for e in popup.elements}
    for n in range(1, ROWS + 1):
        x, y = POP_ROW_W * ((n - 1) // per), POP_HEAD_H + POP_ROW_H * ((n - 1) % per)
        row = have.get(f"bl_row_{n}") or edit.clone_element(project, have["bl_row_1"], popup, x, y, POP_ROW_W, POP_ROW_H, f"bl_row_{n}")
        shown = have.get(f"bl_name_{n}") or edit.clone_element(project, have["bl_name_1"], popup, x, y, 148, 24, f"bl_name_{n}")
        for key, value in (("X", x), ("Y", y), ("Width", POP_ROW_W), ("Height", POP_ROW_H), ("WriteVar", "ENRCPNO"), ("SetValue", n)):
            row.section.set(key, value)
        picture_on(row, 0, bank, f"rc_pop_row_{n}", x, y, POP_ROW_W, POP_ROW_H, WHITE)
        for key, value in (("X", x + 40), ("Y", y + 8), ("ReadVar", f"ENRCP{FIELDS * n}")):
            shown.section.set(key, value)
    gear = find(project, BLEND, "bl_gear")
    gear.section.set("GoToScreenID", page.id)
    for entry in gear.section.entries("GoToScreenName"):
        entry.value = SCREEN.encode("latin1")

    # --- recipe page: frame -------------------------------------------------------------------
    for button in nav:
        edit.clone_element(project, button, page)
    back = goto(page, "rc_back", tpl_back, blend, tuple(tpl_back.section.get_int(k) for k in ("X", "Y", "Width", "Height")),
                None)
    # six spaces carry the words past the chevron in the face, as build_system_tiles.py does for "Settings"
    i18n.words(back, tuple("      " + t for t in ("Blend", "Phối trộn", "Mélange")), 14, margin=0)
    head = edit.clone_element(project, tpl_head, page, *(tpl_head.section.get_int(k) for k in ("X", "Y", "Width", "Height")), "rc_head")
    title = edit.clone_element(project, tpl_head_text, page, *(tpl_head_text.section.get_int(k) for k in ("X", "Y")), 300,
                               tpl_head_text.section.get_int("Height"), "rc_head_txt1")
    i18n.words(title, ("Recipes", "Công thức", "Recettes"))
    del back, head

    for key, box in (("rc_list", LIST), ("rc_edit", EDIT)):
        picture(key, box)

    # --- the rows ---------------------------------------------------------------------------
    lx, ly, lw, _ = LIST
    text("rc_t_list", (lx + 52, ly + 17, lw - 68, 21), ("RECIPES", "CÔNG THỨC", "RECETTES"), 14, INK, True)
    mark = edit.clone_element(project, tpl_graphic, page, 0, 0, 10, 10, "rc_mark")
    clear_links(mark)
    mark.section.set("ReadVar", "ENRCPNO")
    mark.section.set("MemLen", 1)           # a word: the state is the row number
    add_states(project, mark, ROWS + 1)
    for n in range(ROWS + 1):
        picture_on(mark, n, bank, f"rc_mark_{n}", *MARK, WHITE)
    frame.flat(mark, WHITE)
    frame.picture_rect(mark, *MARK)
    for n, (x, y, w, h) in enumerate(ROW, 1):
        row = edit.clone_element(project, tpl_row, page, x, y, w, h, f"rc_row_{n}")
        clear_links(row)
        row.section.set("WriteVar", "ENRCPNO")
        row.section.set("SetValue", n)
        macro.set_macro(row.section, "AfterExecMacroLen", None)
        picture_on(row, 0, bank, "rc_row", x, y, w, h, WHITE)
        i18n.words(row, "")
        text(f"rc_t_no_{n}", (x + 8, y + 8, 26, 21), str(n), 14, MUTED, True, CENTRE)
        chars(f"rc_name_{n}", (x + 44, y + 7, w - 54, 24), f"ENRCP{FIELDS * n}", 14)

    # --- the row in use -------------------------------------------------------------------
    ex, ey, ew, _ = EDIT
    text("rc_t_edit", (ex + 52, ey + 17, 130, 21), ("RECIPE", "CÔNG THỨC", "RECETTE"), 14, INK, True)
    number("rc_no", (ex + 184, ey + 15, 30, 24), "ENRCPNO", 16, 2, align=LEFT, colour=INK)
    nx, ny, nw, nh = NAME_BOX
    text("rc_t_name", (ex + 16, ny + 10, 70, 21), ("Name", "Tên", "Nom"), 14, MUTED)
    name = edit.clone_element(project, tpl_chars, page, nx + 8, ny + 4, nw - 16, nh - 8, "rc_name")
    clear_links(name)
    for key in ("ReadVar", "WriteVar"):
        name.section.set(key, "ENRCP0")
    name.section.set("StringLen", NAME_CHARS)
    name.section.set("Style", 3)
    style(name, 18, INK, True)
    for n, (x, y, w, h) in enumerate(TILES, 1):
        text(f"rc_t_silo_{n}", (x + 12, y + 12, 24, 21), str(n), 14, MUTED, True, CENTRE)
        chars(f"rc_silo_{n}", (x + 44, y + 11, w - 52, 22), address[f"SiloName[{n}]"], 14)
        kg = edit.clone_element(project, tpl_entry, page, x + 16, y + 52, 110, 36, f"rc_kg_{n}")
        clear_links(kg)
        for key in ("ReadVar", "WriteVar"):
            kg.section.set(key, f"ENRCP{n}")
        for key, value in (("MemFmt", 5), ("MemLen", 2), ("IntNum", 3), ("DotNum", 1), ("MinValue", "0.0"),
                           ("MaxValue", f"{MAX_KG}.0"), ("Style", 3)):
            kg.section.set(key, value)                     # floating, two words, as the recipe field
        style(kg, 22, VALUE, True, RIGHT)
        text(f"rc_t_kg_{n}", (x + 138, y + 60, 30, 21), "kg", 14, MUTED)
    # the total comes back from the PLC ("HMI".Rc.Sum of what the cycle macro sent); over the limit the row turns red
    band = edit.clone_element(project, tpl_graphic, page, 0, 0, 10, 10, "rc_over")
    clear_links(band)
    band.section.set("ReadVar", address["Rc.Over"])
    for n, key in enumerate(("rc_over_0", "rc_over_1")):
        picture_on(band, n, bank, key, *OVER, WHITE)
    frame.flat(band, WHITE)
    frame.picture_rect(band, *OVER)
    text("rc_t_total", (ex + 20, EDIT_RULE + 20, 106, 24), ("Total", "Tổng", "Total"), 16, INK)
    number("rc_total", (ex + 126, EDIT_RULE + 14, 110, 36), address["Rc.Sum"], 26, 4, 1)
    text("rc_t_total_kg", (ex + 240, EDIT_RULE + 22, 30, 21), "kg", 14, MUTED)
    limit = edit.clone_element(project, tpl_ind, page, ex + 280, EDIT_RULE + 21, 306, 24, "rc_limit")
    clear_links(limit)
    limit.section.set("ReadVar", address["Rc.Over"])
    limit.section.set("AutoResizeByText", 0)
    style(limit, 14, MUTED)
    for n, (texts, colour, bold) in enumerate(LIMIT_WORDS):
        limit.states[n].set("FontColor", bgr(colour))
        limit.states[n].set("FontBold", 1 if bold else 0)
        i18n.words(limit, texts, 14, state=n)
    text("rc_t_hint", (ex + 16, CLEAR[1] + 2, 380, 40),
         ("Tap a row, then enter its name and weights.\nAn empty row is free for a new recipe.",
          "Chạm một dòng rồi nhập tên và khối lượng.\nDòng trống là chỗ cho công thức mới.",
          "Touchez une ligne, puis saisissez nom et poids.\nUne ligne vide est libre."), 12, MUTED)

    # --- clear: the panel asks first, then the macro blanks the row in use ---------------
    x, y, w, h = CLEAR
    wipe = edit.clone_element(project, tpl_push, page, x, y, w, h, "rc_clear")
    clear_links(wipe)
    for key in ("ReadVar", "WriteVar"):
        wipe.section.set(key, CLEAR_BIT)
    wipe.section.set("Style", 3)
    wipe.section.set("ConFirmWindow", 1)
    macro.set_macro(wipe.section, "ButtonOnMacroLen", clear_macro())
    for n, key in enumerate(("rc_clear_0", "rc_clear_1")):
        picture_on(wipe, n, bank, key, x, y, w, h, WHITE)
        wipe.states[n].set("FontColor", bgr(BAD))
        wipe.states[n].set("FontBold", 1)
        wipe.states[n].set("FontAlign", CENTRE)
        i18n.words(wipe, CLEAR_WORDS, 14, state=n, margin=12)

    i18n.ensure_languages(project)
    print(project.save(path))
    print(f"{SCREEN} (id {page.id}): {len(page.elements)} elements; recipe at {project.doc.first('EnhanceRcp').get('ReadEnRecipeVar')}")


if __name__ == "__main__":
    if len(sys.argv) != 4:
        raise SystemExit(__doc__)
    main(*sys.argv[1:])
