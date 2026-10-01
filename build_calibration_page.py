"""Draw the Calibration page (Set_Calibration) after Sang's "Hieu chinh bon can" form.

Run:  python build_calibration_page.py <project.dpa> <asset folder>

Four blocks under the page title (title and X come from build_setting_page.py):

  HIEU CHINH         silo, number of points, tare / zero with undo, latched
                     point, frames read, point + weight -> HIEU CHINH / HUY
  status bar         the PLC's message for the last action
  GIAM SAT 4 KENH    zero point, net and tare for CH1..CH4
  THAM SO CHUC NANG  a scale function, its value now, a new value, DOC / GHI

Every drop-down is the Fill page's field + pop-up list: silo and function
names come from the PLC, the point counts are fixed 1..6. Static artwork is
one picture per block; numbers, fields and buttons are elements over it. No PLC
addresses exist yet, so every element points at internal memory - ADDRESSES is
the list to rebind. Re-runnable: elements named "cal_" are removed first.
"""

from __future__ import annotations

import copy
import sys
from pathlib import Path

from PIL import Image, ImageDraw

import build_fill_page as fill
import build_silo_frame as frame
from build_fill_page import CARD_LINE, CENTRE, FIELD_LINE, LEFT, TILE, bind, clear_links, picture_on, rounded, text_style
from build_setting_page import CONTENT_TOP
from build_silo_frame import INK, MUTED, NAV_INK, PAGE, WHITE, bgr, font, icon, rgb
from dpa import edit, macro
from dpa.model import Project

SCREEN = "Set_Calibration"
DARK, DARK_DOWN = "#5A6068", "#43484F"     # primary button
HEAD = "#E9EEF3"                           # table header row
VALUE = "#2B3644"

ADDRESSES = {
    "cal_silo": "$500",          # silo picked, 0..5
    "cal_silo_name": "$502",     # its name, 20 chars (PLC copies it)
    **{f"cal_silo_name_{i + 1}": f"${310 + 10 * i}" for i in range(6)},  # the Fill page's silo names
    "cal_points": "$512",        # number of calibration points, 1..6
    "cal_point": "$513",         # point being calibrated, 1..6
    "cal_weight": "$514",        # its reference weight, kg x10
    "cal_latched": "$515",       # point latched now
    "cal_frames": "$516",        # frames read from the scale
    "cal_tare": "$520.0", "cal_tare_undo": "$520.1",
    "cal_zero": "$520.2", "cal_zero_undo": "$520.3",
    "cal_apply": "$520.4", "cal_cancel": "$520.5",
    "cal_read": "$520.6", "cal_write": "$520.7",
    "cal_open": "$521.0",        # spare bit the list openers write
    "cal_message": "$650",       # PLC message for the last action, 40 chars
    **{f"cal_zero_ch{c}": f"${530 + c - 1}" for c in range(1, 5)},   # zero point, kg x10
    **{f"cal_net_ch{c}": f"${534 + c - 1}" for c in range(1, 5)},    # net, kg x10
    **{f"cal_tare_ch{c}": f"${538 + c - 1}" for c in range(1, 5)},   # tare taken, kg x10
    "cal_func": "$542",          # scale function picked, 0..5
    "cal_func_name": "$544",     # its name, 20 chars (PLC copies it)
    **{f"cal_func_name_{i + 1}": f"${560 + 10 * i}" for i in range(6)},  # function names
    "cal_func_hint": "$620",     # range and effect of the function, 40 chars
    "cal_func_now": "$640",      # value in the scale now
    "cal_func_new": "$641",      # value to write
}

ROWS, ROW_H = 6, 36
NAME_CHARS, MESSAGE_CHARS = 20, 40

# Panel layout: content x 100..1016, y 66..592.
CARD_A = (100, CONTENT_TOP, 916, 158)
STATUS = (100, 272, 916, 36)
CARD_C = (100, 318, 916, 150)
CARD_D = (100, 478, 916, 106)

R1_LABEL, R1 = 136, 148          # row 1 of card A: label centre, control top
R2_LABEL, R2 = 200, 212
CTRL_H = 36
# Silo names can be long: the first column takes the room, the two read-outs stay just wider than their labels.
SILO_FIELD = (112, R1, 266, CTRL_H)
POINTS_FIELD = (112, R2, 266, CTRL_H)
TARE_BTN, TARE_UNDO = (400, R1, 92, CTRL_H), (498, R1, 52, CTRL_H)
ZERO_BTN, ZERO_UNDO = (574, R1, 92, CTRL_H), (672, R1, 52, CTRL_H)
LATCHED = (748, R1, 116, CTRL_H)
FRAMES = (888, R1, 116, CTRL_H)
POINT_FIELD = (400, R2, 150, CTRL_H)
WEIGHT = (574, R2, 178, CTRL_H)
APPLY_BTN, CANCEL_BTN = (762, R2, 140, CTRL_H), (910, R2, 94, CTRL_H)
DIVIDERS = ((388, 120, 248), (562, 120, 248), (736, 120, 184), (876, 120, 184))

TABLE_X, TABLE_W, FIRST_COL = 112, 892, 200
HEAD_Y, HEAD_H, TROW_H = 346, 26, 30
CH_W = (TABLE_W - FIRST_COL) // 4

D_LABEL, D = 512, 526
FUNC_FIELD = (112, D, 236, CTRL_H)
FUNC_NOW = (372, D, 130, CTRL_H)
FUNC_NEW = (514, D, 130, CTRL_H)
READ_BTN, WRITE_BTN = (668, D, 160, CTRL_H), (840, D, 164, CTRL_H)
HINT = (514, 486, 490, 20)


# --- pictures -----------------------------------------------------------------

def canvas(box):
    _, _, w, h = box
    s = 4
    big = Image.new("RGBA", (w * s, h * s), rgb(PAGE) + (255,))
    return big, ImageDraw.Draw(big), s


def local(box, card):
    return (box[0] - card[0], box[1] - card[1], box[2], box[3])


def well(d, box, card):
    rounded(d, local(box, card), fill=TILE, outline=TILE, radius=6)


def entry_box(d, box, card):
    rounded(d, local(box, card), fill=WHITE, outline=FIELD_LINE, radius=6)


def label(t, x, y, words, card, size=14, colour=INK):
    t.text((x - card[0], y - card[1]), words, font=font("arial.ttf", size), fill=colour, anchor="lm")


def section_head(t, x, y, words, card, colour=MUTED):
    t.text((x - card[0], y - card[1]), words, font=font("arialbd.ttf", 12), fill=colour, anchor="lm")


def card_a() -> Image.Image:
    big, d, s = canvas(CARD_A)
    rounded(d, (0, 0, CARD_A[2], CARD_A[3]))
    for x, y0, y1 in DIVIDERS:
        d.line(((x - CARD_A[0]) * s, (y0 - CARD_A[1]) * s, (x - CARD_A[0]) * s, (y1 - CARD_A[1]) * s),
               fill=CARD_LINE, width=s)
    for box in (LATCHED, FRAMES):
        well(d, box, CARD_A)
    entry_box(d, WEIGHT, CARD_A)
    image = big.resize(CARD_A[2:], Image.LANCZOS)
    t = ImageDraw.Draw(image)
    section_head(t, 112, 120, "HIỆU CHỈNH", CARD_A)
    for x, words in ((112, "Chọn silo"), (400, "Trừ bì"), (574, "Zero"), (748, "Điểm đang chốt"), (888, "Số khung đã đọc")):
        label(t, x, R1_LABEL, words, CARD_A)
    for x, words in ((112, "Số điểm"), (400, "Điểm hiệu chỉnh"), (574, "Trọng lượng (kg)")):
        label(t, x, R2_LABEL, words, CARD_A)
    return image


def status_face() -> Image.Image:
    big, d, s = canvas(STATUS)
    w, h = STATUS[2:]
    rounded(d, (0, 0, w, h))
    d.line((130 * s, 8 * s, 130 * s, (h - 8) * s), fill=CARD_LINE, width=s)
    image = big.resize((w, h), Image.LANCZOS)
    image.alpha_composite(icon("circle-check", 20, MUTED, px=1.75, cut=WHITE), (14, (h - 20) // 2))
    ImageDraw.Draw(image).text((42, h / 2), "Trạng thái", font=font("arial.ttf", 14), fill=MUTED, anchor="lm")
    return image


def card_c() -> Image.Image:
    big, d, s = canvas(CARD_C)
    rounded(d, (0, 0, CARD_C[2], CARD_C[3]))
    x0, y0 = TABLE_X - CARD_C[0], HEAD_Y - CARD_C[1]
    d.rectangle((x0 * s, y0 * s, (x0 + TABLE_W) * s, (y0 + HEAD_H) * s), fill=HEAD)
    for r in range(1, 4):
        y = y0 + HEAD_H + TROW_H * r
        d.line((x0 * s, y * s, (x0 + TABLE_W) * s, y * s), fill=CARD_LINE, width=s)
    for c in range(1, 4):
        x = x0 + FIRST_COL + CH_W * c
        d.line((x * s, (y0 + HEAD_H) * s, x * s, (y0 + HEAD_H + 3 * TROW_H) * s), fill=CARD_LINE, width=s)
    image = big.resize(CARD_C[2:], Image.LANCZOS)
    t = ImageDraw.Draw(image)
    t.text((12, 16), "GIÁM SÁT 4 KÊNH", font=font("arialbd.ttf", 13), fill=INK, anchor="lm")
    mid = y0 + HEAD_H / 2
    t.text((x0 + 12, mid), "Thông số", font=font("arialbd.ttf", 14), fill=INK, anchor="lm")
    for c in range(4):
        t.text((x0 + FIRST_COL + CH_W * c + CH_W / 2, mid), f"CH{c + 1}", font=font("arialbd.ttf", 14), fill=INK, anchor="mm")
    for r, words in enumerate(("Điểm không (kg)", "Khối lượng tịnh (kg)", "Đã trừ bì (kg)")):
        t.text((x0 + 12, y0 + HEAD_H + TROW_H * r + TROW_H / 2), words, font=font("arial.ttf", 14), fill=INK, anchor="lm")
    return image


def card_d() -> Image.Image:
    big, d, s = canvas(CARD_D)
    rounded(d, (0, 0, CARD_D[2], CARD_D[3]))
    for x in (360, 656):
        d.line(((x - CARD_D[0]) * s, (D_LABEL - 10 - CARD_D[1]) * s, (x - CARD_D[0]) * s, (D + CTRL_H - CARD_D[1]) * s),
               fill=CARD_LINE, width=s)
    well(d, FUNC_NOW, CARD_D)
    entry_box(d, FUNC_NEW, CARD_D)
    image = big.resize(CARD_D[2:], Image.LANCZOS)
    t = ImageDraw.Draw(image)
    section_head(t, 112, 494, "THAM SỐ CHỨC NĂNG", CARD_D)
    for x, words in ((112, "Chức năng"), (372, "Đang có"), (514, "Giá trị mới"), (668, "Đọc về"), (840, "Ghi xuống")):
        label(t, x, D_LABEL, words, CARD_D)
    return image


def field_face(w: int, h: int, open_: bool, up: bool = False) -> Image.Image:
    """The drop-down field. Open, it is the list's header - or its footer when the list opens upward."""
    s = 4
    big = Image.new("RGBA", (w * s, h * s), rgb(WHITE) + (255,))
    d = ImageDraw.Draw(big)
    if open_ and up:
        d.rounded_rectangle((0, -8 * s, w * s - 1, h * s - 1), radius=6 * s, fill=WHITE, outline=FIELD_LINE, width=s)
        d.line((0, 0, w * s, 0), fill=CARD_LINE, width=s)
    elif open_:
        d.rounded_rectangle((0, 0, w * s - 1, (h + 8) * s), radius=6 * s, fill=WHITE, outline=FIELD_LINE, width=s)
        d.line((0, (h - 1) * s, w * s, (h - 1) * s), fill=CARD_LINE, width=s)
    else:
        rounded(d, (0, 0, w, h), outline=FIELD_LINE)
    image = big.resize((w, h), Image.LANCZOS)
    image.alpha_composite(icon("chevron-up" if open_ != up else "chevron-down", 18, MUTED, px=1.75, cut=WHITE),
                          (w - 28, (h - 18) // 2))
    return image


def row_face(w: int, i: int, number_only: bool, up: bool = False) -> Image.Image:
    """One list row; a number list prints the value, a name list only its slot number."""
    h, s = ROW_H, 4
    big = Image.new("RGBA", (w * s, h * s), rgb(WHITE) + (255,))
    d = ImageDraw.Draw(big)
    if up and i == 0:  # top of a list that opens upward
        d.rounded_rectangle((0, 0, w * s - 1, (h + 8) * s), radius=6 * s, fill=WHITE, outline=FIELD_LINE, width=s)
        d.line((10 * s, (h - 1) * s, (w - 10) * s, (h - 1) * s), fill=CARD_LINE, width=s)
    elif up:
        d.rectangle((0, -8 * s, w * s - 1, h * s + 8 * s), fill=WHITE, outline=FIELD_LINE, width=s)
        d.line((10 * s, (h - 1) * s, (w - 10) * s, (h - 1) * s), fill=CARD_LINE, width=s)
    elif i == ROWS - 1:
        d.rounded_rectangle((0, -8 * s, w * s - 1, h * s - 1), radius=6 * s, fill=WHITE, outline=FIELD_LINE, width=s)
    else:
        d.rectangle((0, -8 * s, w * s - 1, h * s + 8 * s), fill=WHITE, outline=FIELD_LINE, width=s)
        d.line((10 * s, (h - 1) * s, (w - 10) * s, (h - 1) * s), fill=CARD_LINE, width=s)
    image = big.resize((w, h), Image.LANCZOS)
    t = ImageDraw.Draw(image)
    if number_only:
        t.text((12, h / 2), str(i + 1), font=font("arialbd.ttf", 16), fill=INK, anchor="lm")
    else:
        t.text((18, h / 2), str(i + 1), font=font("arial.ttf", 14), fill=MUTED, anchor="mm")
    return image


def button_face(w: int, h: int, words: str, dark: bool, pressed: bool) -> Image.Image:
    s = 4
    big = Image.new("RGBA", (w * s, h * s), rgb(WHITE) + (255,))
    d = ImageDraw.Draw(big)
    if dark:
        rounded(d, (0, 0, w, h), fill=DARK_DOWN if pressed else DARK, outline=DARK_DOWN if pressed else DARK, radius=6)
    else:
        rounded(d, (0, 0, w, h), fill=TILE if pressed else WHITE, outline=FIELD_LINE, radius=6)
    image = big.resize((w, h), Image.LANCZOS)
    ImageDraw.Draw(image).text((w / 2, h / 2), words, font=font("arialbd.ttf", 14),
                               fill=WHITE if dark else INK, anchor="mm")
    return image


BUTTONS = {  # name: box, words, dark
    "cal_tare": (TARE_BTN, "TRỪ BÌ", True), "cal_tare_undo": (TARE_UNDO, "BỎ", False),
    "cal_zero": (ZERO_BTN, "ZERO", True), "cal_zero_undo": (ZERO_UNDO, "BỎ", False),
    "cal_apply": (APPLY_BTN, "HIỆU CHỈNH", True), "cal_cancel": (CANCEL_BTN, "HỦY", False),
    "cal_read": (READ_BTN, "ĐỌC", False), "cal_write": (WRITE_BTN, "GHI", True),
}

# drop-down: name -> field box, pop-up screen, shown text address or None, names or None, value of row 0
# A field in the bottom card opens its list upward so it stays on the panel.
UP = {"cal_func"}
LISTS = {
    "cal_silo": (SILO_FIELD, "pop_CalSilo", "cal_silo_name", "cal_silo_name_", 0),
    "cal_points": (POINTS_FIELD, "pop_CalPoints", None, None, 1),
    "cal_point": (POINT_FIELD, "pop_CalPoint", None, None, 1),
    "cal_func": (FUNC_FIELD, "pop_CalFunc", "cal_func_name", "cal_func_name_", 0),
}


def render(folder: Path) -> dict[str, Path]:
    faces = {
        "cal_card_a": frame.static("cal_card_a", card_a), "cal_status": frame.static("cal_status", status_face),
        "cal_card_c": frame.static("cal_card_c", card_c), "cal_card_d": frame.static("cal_card_d", card_d),
    }
    for name, (box, words, dark) in BUTTONS.items():
        for p in (0, 1):
            faces[f"{name}_{p}"] = button_face(box[2], box[3], words, dark, bool(p))
    for name, (box, _, shown, names, _) in LISTS.items():
        faces[f"{name}_field_0"] = field_face(box[2], box[3], False)
        faces[f"{name}_field_1"] = field_face(box[2], box[3], True, name in UP)
        for i in range(ROWS):
            faces[f"{name}_row_{i}"] = row_face(box[2], i, names is None, name in UP)
    folder.mkdir(parents=True, exist_ok=True)
    paths = {}
    for key, image in faces.items():
        path = folder / f"{key}.png"
        image.save(path)
        paths[key] = path
    return paths


def main(path: str, asset_dir: str) -> None:
    project = Project(path)
    donor = Project(fill.DONOR)
    page = project.screen(SCREEN)
    frame.remember_labels(project)
    for element in [e for e in page.elements if e.name.startswith("cal_")][::-1]:
        edit.delete_element(project, page, element.index)

    popups = {}
    for name, (box, popup_name, *_rest) in LISTS.items():
        popup = fill.silo_popup(project, donor, popup_name)
        x, y, w, h = box
        top = y - ROW_H * ROWS if name in UP else y
        for key, value in (("Width", w), ("Height", h + ROW_H * ROWS), ("DocSizeX", w), ("DocSizeY", h + ROW_H * ROWS),
                           ("SubScreenX", x), ("SubScreenY", top)):
            popup.section.set(key, value)
        popups[name] = popup
    frame.prune_bank(project)

    tpl_rect = donor.element("scr_MainScreen", 1)
    tpl_num = donor.element("scr_Calibcation", 19)
    tpl_entry = donor.element("scr_Discharge", 52)
    tpl_push = donor.element("scr_Calibcation", 4)
    text_donor = Project(fill.DONOR_TEXT).element("Screen_1", 2)
    set_donor = Project(fill.DONOR_SET).element("Fill", 62)

    assets = render(Path(asset_dir))
    bank = frame.Bank(project)
    for key, file in assets.items():
        bank.add(key, file)
    bank.commit()
    A = ADDRESSES

    def picture(key, x, y):
        _, _, w, h = bank.where[key]
        item = edit.clone_element(project, tpl_rect, page, 0, 0, 10, 10, key)
        clear_links(item)
        frame.face(item, bank, key)
        frame.flat(item, PAGE)
        for state in item.states:
            state.set("TransColor", bgr(PAGE))
        frame.picture_rect(item, x, y, w, h)
        frame.labels(project, page, key, x, y)
        return item

    def number(screen, name, box, size, digits, decimals, address=None, entry=False, align=CENTRE):
        x, y, w, h = box
        item = edit.clone_element(project, tpl_entry if entry else tpl_num, screen, x, y, w, h, name)
        clear_links(item)
        for key in ("ReadVar", "WriteVar"):
            if item.section.get(key) not in (None, "None"):
                item.section.set(key, address or A[name])
        item.section.set("IntNum", digits)
        item.section.set("DotNum", decimals)
        if entry:  # one signed word like the displays, value x10 - not the donor's 2-word REAL
            item.section.set("MemFmt", 2)
            item.section.set("MemLen", 1)
        item.section.set("Style", 3)
        text_style(item, size, VALUE, True, align)
        return item

    def text(screen, name, box, size, bold, chars, colour=INK, address=None):
        x, y, w, h = box
        item = edit.clone_element(project, text_donor, screen, x, y, w, h, name)
        clear_links(item)
        item.section.set("ReadVar", address or A[name])
        item.section.set("StringLen", chars)
        item.section.set("Style", 3)
        text_style(item, size, colour, bold, LEFT)
        return item

    def push(screen, name, box, faces, address, on_macro=None):
        x, y, w, h = box
        item = edit.clone_element(project, tpl_push, screen, x, y, w, h, name)
        clear_links(item)
        bind(item, address)
        item.section.set("Style", 3)
        macro.set_macro(item.section, "ButtonOnMacroLen", on_macro)
        macro.set_macro(item.section, "ButtonOffMacroLen", None)
        for i, key in enumerate(faces):
            edit.set_state_text(item, "", "", state=i)
            picture_on(item, i, bank, key, x, y, w, h, WHITE)
        return item

    # --- artwork --------------------------------------------------------------------
    for key, box in (("cal_card_a", CARD_A), ("cal_status", STATUS), ("cal_card_c", CARD_C), ("cal_card_d", CARD_D)):
        picture(key, box[0], box[1])

    # --- values -----------------------------------------------------------------------
    number(page, "cal_latched", LATCHED, 18, 2, 0)
    number(page, "cal_frames", FRAMES, 18, 5, 0)
    number(page, "cal_weight", (WEIGHT[0] + 8, WEIGHT[1], WEIGHT[2] - 16, WEIGHT[3]), 18, 5, 1, entry=True)
    text(page, "cal_message", (STATUS[0] + 142, STATUS[1] + 6, 760, 24), 14, False, MESSAGE_CHARS, INK)
    for c in range(4):
        x = TABLE_X + FIRST_COL + CH_W * c + 4
        for r, (key, size) in enumerate((("cal_zero_ch", 16), ("cal_net_ch", 18), ("cal_tare_ch", 16))):
            y = HEAD_Y + HEAD_H + TROW_H * r + 2
            number(page, f"{key}{c + 1}", (x, y, CH_W - 8, TROW_H - 4), size, 5, 1)
    number(page, "cal_func_now", FUNC_NOW, 18, 3, 0)
    number(page, "cal_func_new", (FUNC_NEW[0] + 8, FUNC_NEW[1], FUNC_NEW[2] - 16, FUNC_NEW[3]), 18, 3, 0, entry=True)
    text(page, "cal_func_hint", HINT, 12, False, MESSAGE_CHARS, MUTED)

    for name, (box, _, _) in BUTTONS.items():
        push(page, name, box, (f"{name}_0", f"{name}_1"), A[name])

    # --- drop-downs: field on the page, list in its own pop-up -------------------------
    for name, (box, _, shown, names, first) in LISTS.items():
        popup = popups[name]
        x, y, w, h = box
        opener = macro.screen_statement(macro.OPENSCREEN, popup.id)
        close = macro.screen_statement(macro.CLOSESUBSCREEN, popup.id)
        push(page, f"{name}_field", box, (f"{name}_field_0", f"{name}_field_0"), A["cal_open"], opener)
        up = name in UP
        head_y, rows_y = (ROW_H * ROWS, 0) if up else (0, h)
        push(popup, f"{name}_close", (0, head_y, w, h), (f"{name}_field_1", f"{name}_field_1"), A["cal_open"], close)
        for screen, dx, dy in ((page, x, y), (popup, 0, head_y)):
            if shown:
                text(screen, f"{name}_shown", (dx + 10, dy + 6, w - 44, 24), 16, True, NAME_CHARS, address=A[shown])
            else:
                number(screen, f"{name}_shown", (dx + 10, dy + 6, w - 44, 24), 16, 1, 0, address=A[name], align=LEFT)
        for i in range(ROWS):
            ry = rows_y + ROW_H * i
            row = edit.clone_element(project, set_donor, popup, 0, ry, w, ROW_H, f"{name}_row_{i + 1}")
            clear_links(row)
            row.section.set("WriteVar", A[name])
            row.section.set("SetValue", first + i)
            row.section.set("Style", 3)
            macro.set_macro(row.section, "BeforeExecMacroLen", None)
            macro.set_macro(row.section, "AfterExecMacroLen", close)
            row.states[0].items = copy.deepcopy(tpl_push.states[0].items)
            edit.set_state_text(row, "", "", state=0)
            picture_on(row, 0, bank, f"{name}_row_{i}", 0, ry, w, ROW_H, WHITE)
            if names:
                text(popup, f"{name}_name_{i + 1}", (34, ry + 6, w - 44, 24), 14, False, NAME_CHARS,
                     address=A[f"{names}{i + 1}"])

    print(project.save(path))
    print(f"{SCREEN}: {len(page.elements)} elements; pop-ups " + ", ".join(f"{p.name}={p.id}" for p in popups.values()))


if __name__ == "__main__":
    if len(sys.argv) != 3:
        raise SystemExit(__doc__)
    main(*sys.argv[1:])
