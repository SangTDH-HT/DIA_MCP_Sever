"""Draw the Discharge and Blend pages of the new Silo HMI after Sang's Vietnamese forms.

Run:  python build_home_pages.py <project.dpa> <asset folder>

Both pages share one layout, in the Fill page's style (build_fill_page.py):
left, a TRANG THAI bar over the process - GHFV on the vacuum line into the
discharge hopper (PHEU XA, its valve Y-002 with Thu cong / Xa lieu), the silo
with its SDV at the bottom and the material line (green) back up into the
hopper, the suction motor M-009 on the vacuum line (cyan); right, TRONG LUONG
XA, the silo / recipe pick, BAT DAU and the THU CONG / TU DONG mode.

  Home_Discharge  "Xa lieu silo": the weight is entered, a silo is picked
  Home_Blend      "Cong thuc":    the weight comes from the recipe, a recipe
                                  is picked, and a gear opens Setting

No PLC addresses exist yet, so every element points at internal memory; each
page's ADDRESSES is the list to rebind. Re-runnable: elements with the page's
prefix are removed first, its list pop-up is emptied, the bank is pruned.
"""

from __future__ import annotations

import copy
import sys
from pathlib import Path

from PIL import Image, ImageDraw

import build_fill_page as fill
import build_silo_frame as frame
from build_fill_page import (CARD_LINE, CENTRE, FIELD_LINE, LEADER, LEFT, MATERIAL, RIGHT, ROW_H, ROWS, TILE, VACUUM,
                             arrowhead, bind, clear_links, dashed, line_art, local, picture_on, polyline, rounded,
                             text_style)
from build_silo_frame import INK, MUTED, NAV_INK, PAGE, WHITE, bgr, font, icon, rgb
from dpa import edit, macro
from dpa.model import Project

ICONS = fill.ICONS
OK = "#2BB35A"            # done tick

PAGES = {
    "dc": {
        "screen": "Home_Discharge", "popup": "pop_SiloXa", "select": "CHỌN BỒN XẢ", "entry": True, "gear": False,
        "addresses": {
            "dc_status": "$220", "dc_status_silo": "$221", "dc_status_time": "$222",
            "dc_hopper": "$223",       # hopper weight, kg x10
            "dc_rate": "$224",         # discharge rate, kg/min x10
            "dc_current": "$225",      # silo weight, kg x10
            "dc_pressure": "$226",     # kPa x10
            "dc_dec_time": "$227",     # s
            "dc_target": "$228",       # discharge weight the operator enters, kg x10
            "dc_sdv_no": "$231",       # SDV number
            "dc_silo": "$229",         # picked silo, 0..5
            "dc_open": "$232.0",       # spare bit the list opener writes
            "dc_name": "$370",         # name of the picked silo, 20 chars (PLC copies it)
            **{f"dc_name_{i + 1}": f"${310 + 10 * i}" for i in range(ROWS)},  # the Fill page's silo names
            "dc_mode": "$230.0",       # 0 THU CONG, 1 TU DONG
            "dc_valve_man": "$230.1",  # hopper valve Y-002 in manual
            "dc_valve_run": "$230.2",  # Xa lieu, momentary
            "dc_ghfv": "$230.3", "dc_sdv": "$230.4",
            "dc_start": "$230.5",      # BAT DAU / DUNG, momentary; the PLC toggles the run
            "dc_running": "$230.6",
            "dc_done": "$230.7",       # discharge weight reached: the tick turns green
        },
    },
    "bl": {
        "screen": "Home_Blend", "popup": "pop_CongThuc", "select": "CHỌN CÔNG THỨC", "entry": False, "gear": True,
        "addresses": {
            "bl_status": "$240", "bl_status_silo": "$241", "bl_status_time": "$242",
            "bl_hopper": "$243", "bl_rate": "$244", "bl_current": "$245",
            "bl_pressure": "$246", "bl_dec_time": "$247",
            "bl_target": "$248",       # discharge weight from the recipe, kg x10
            "bl_sdv_no": "$251",
            "bl_silo": "$249",         # picked recipe, 0..5
            "bl_open": "$252.0",
            "bl_name": "$380",         # name of the picked recipe, 20 chars (PLC copies it)
            **{f"bl_name_{i + 1}": f"${390 + 10 * i}" for i in range(ROWS)},  # recipe names
            "bl_mode": "$250.0", "bl_valve_man": "$250.1", "bl_valve_run": "$250.2",
            "bl_ghfv": "$250.3", "bl_sdv": "$250.4", "bl_start": "$250.5", "bl_running": "$250.6",
            "bl_done": "$250.7",
        },
    },
}

# Panel layout, the Fill page's grid: content x 100..1016, y 66..592.
STATUS, PROCESS = fill.STATUS, fill.PROCESS
WEIGHT, SILO, COMBO, START, MODE_BTN, MODE_RULE = fill.WEIGHT, fill.SILO, fill.COMBO, fill.START, fill.MODE_BTN, fill.MODE_RULE
TARGET = (808, 115, 167, 75)          # same box as the Fill page's weight
TICK = (982, 84, 26, 26)
GEAR = (978, 236, 30, 30)

HOPPER_CARD = (100, 212, 106, 88)
VALVE_CARD = (100, 334, 146, 136)
VALVE_BTN = ((108, 392, 62, 70), (176, 392, 62, 70))
RATE_CARD = (204, 500, 118, 88)
CURRENT_CARD = (462, 280, 150, 108)
VAC_CARD = (626, 280, 148, 120)
GHFV_AT = (246, 168)                  # valve picture, 26x26
GHFV_TAG = (290, 166, 60, 30)
HOPPER_AT, HOPPER_W = (216, 214), 80
SILO_AT, SILO_H = (352, 150), 340
SDV_AT = (390, 500)
SDV_TAG = (436, 500, 70, 28)
PUMP = (700, 470)
LINE_X = 336                          # material line's riser, silo -> hopper
VAC_X = 618                           # vacuum line's riser, GHFV -> pump


def inked(art: Image.Image, ink: str = "#2F3A45") -> Image.Image:
    """Recolour a drawing's lines to the page ink (Silo_3.png is drawn in red)."""
    grey = art.convert("L")
    dark = Image.new("RGBA", art.size, rgb(ink) + (255,))
    out = Image.new("RGBA", art.size, rgb(PAGE) + (255,))
    mask = grey.point(lambda v: 255 - v if v < 235 else 0)  # page grey stays clear
    out.paste(dark, (0, 0), mask.point(lambda a: min(255, a * 2)))
    return out


def card_title(t: ImageDraw.ImageDraw, cx: float, y: int, words: str, width: int, size: int = 12) -> None:
    """The Fill page's card title, one size smaller until it fits the card."""
    while size > 11 and t.textlength(words, font=font("arial.ttf", size)) > width - 12:
        size -= 1
    fill.card_title(t, cx, y, words, size)


def heading(t: ImageDraw.ImageDraw, x: int, y: float, words: str, room: int, size: int = 15) -> None:
    while size > 11 and t.textlength(words, font=font("arialbd.ttf", size)) > room:
        size -= 1
    t.text((x, y), words, font=font("arialbd.ttf", size), fill=INK, anchor="lm")


def device_head(d, image_draw_later, box, origin):
    """Icon tile of a device card (VAN XA PHEU, DONG CO HUT)."""
    x, y, _, _ = local(box, origin)
    rounded(d, (x + 8, y + 8, 32, 32), fill=TILE, outline=TILE, radius=5)


def process_drawing() -> Image.Image:
    ox, oy, w, h = PROCESS
    s = 4
    big = Image.new("RGBA", (w * s, h * s), rgb(PAGE) + (255,))
    d = ImageDraw.Draw(big)
    L = lambda p: (p[0] - ox, p[1] - oy)
    o = (ox, oy)

    for box in (HOPPER_CARD, VALVE_CARD, RATE_CARD, CURRENT_CARD, VAC_CARD):
        rounded(d, local(box, o))
    for tag in (GHFV_TAG, SDV_TAG):
        rounded(d, local(tag, o), outline="#C9D0D8", radius=5)
    for box in (VALVE_CARD, VAC_CARD):
        device_head(d, None, box, o)
    vx, vy, vw, vh = local(VAC_CARD, o)
    d.line(((vx + 8) * s, (vy + 48) * s, (vx + vw - 8) * s, (vy + 48) * s), fill=CARD_LINE, width=s)
    d.line(((vx + vw // 2) * s, (vy + 54) * s, (vx + vw // 2) * s, (vy + vh - 6) * s), fill=CARD_LINE, width=s)
    kx, ky, kw, kh = local(VALVE_CARD, o)
    mid = (VALVE_BTN[0][0] + VALVE_BTN[0][2] + VALVE_BTN[1][0]) // 2 - ox
    d.line((mid * s, (ky + 60) * s, mid * s, (ky + kh - 10) * s), fill=CARD_LINE, width=s)

    # vacuum line: pump inlet <- riser <- over the top <- GHFV <- hopper lid
    gx = GHFV_AT[0] + 13
    hop_top = HOPPER_AT[1]
    polyline(d, [L((gx, hop_top)), L((gx, 131)), L((VAC_X, 131)), L((VAC_X, PUMP[1] + 15)), L((PUMP[0] - 34, PUMP[1] + 15))],
             VACUUM)
    arrowhead(d, *L((PUMP[0] - 26, PUMP[1] + 15)), "right", VACUUM)
    # material line: SDV -> floor -> riser -> into the hopper's side
    sx = SDV_AT[0] + 13
    inlet_y = HOPPER_AT[1] + 22
    polyline(d, [L((sx, SDV_AT[1] + 26)), L((sx, 574)), L((LINE_X, 574)), L((LINE_X, inlet_y)), L((HOPPER_AT[0] + HOPPER_W + 10, inlet_y))],
             MATERIAL)
    arrowhead(d, *L((HOPPER_AT[0] + HOPPER_W + 2, inlet_y)), "left", MATERIAL)
    # hopper outlet: butterfly valve Y-002, then the discharge arrow
    out_x = HOPPER_AT[0] + HOPPER_W // 2
    polyline(d, [L((out_x, 330)), L((out_x, 432))], MATERIAL)
    arrowhead(d, *L((out_x, 440)), "down", MATERIAL)
    bx, by = L((out_x, 382))
    for sign in (-1, 1):
        d.polygon([((bx - 9) * s, (by + sign * 11) * s), ((bx + 9) * s, (by + sign * 11) * s), (bx * s, by * s)],
                  fill=WHITE, outline=NAV_INK, width=6)

    # leaders from the cards into the process
    dashed(d, [L((HOPPER_CARD[0] + HOPPER_CARD[2], 256)), L((HOPPER_AT[0] + 2, 256))])
    dashed(d, [L((VALVE_CARD[0] + VALVE_CARD[2], 382)), L((out_x - 10, 382))])
    dashed(d, [L((RATE_CARD[0] + RATE_CARD[2], 544)), L((LINE_X, 544))])
    dashed(d, [L((SILO_AT[0] + 98, 334)), L((CURRENT_CARD[0], 334))])
    dashed(d, [L((GHFV_AT[0] + 26, 181)), L((GHFV_TAG[0], 181))])
    dashed(d, [L((SDV_AT[0] + 26, 514)), L((SDV_TAG[0], 514))])
    dashed(d, [L((697, VAC_CARD[1] + VAC_CARD[3])), L((697, PUMP[1] - 28))])

    # suction motor: the Fill page's pump
    cx, cy = L(PUMP)
    r = 24
    d.ellipse(((cx - r) * s, (cy - r) * s, (cx + r) * s, (cy + r) * s), fill=TILE, outline=NAV_INK, width=2 * s)
    d.rectangle(((cx + 4) * s, (cy - r - 1) * s, (cx + r + 10) * s, (cy - r + 9) * s), fill=TILE, outline=NAV_INK, width=2 * s)
    d.line(((cx - 20) * s, (cy + r + 5) * s, (cx + 20) * s, (cy + r + 5) * s), fill=NAV_INK, width=2 * s)
    for sx2 in (-1, 1):
        d.line(((cx + sx2 * 11) * s, (cy + r) * s, (cx + sx2 * 15) * s, (cy + r + 5) * s), fill=NAV_INK, width=2 * s)

    image = big.resize((w, h), Image.LANCZOS)

    silo = inked(line_art("Silo_3.png", height=SILO_H))
    image.paste(silo, L((SILO_AT[0] + (103 - silo.width) // 2, SILO_AT[1])))
    image.paste(line_art("PhieuChua.png", width=HOPPER_W), L(HOPPER_AT))
    image.alpha_composite(icon("fan", 30, NAV_INK, px=1.75), (cx - 15, cy - 15))
    image.alpha_composite(icon("fan", 22, NAV_INK, px=1.5, cut=TILE), (vx + 13, vy + 13))
    image.alpha_composite(icon("funnel", 22, NAV_INK, px=1.5, cut=TILE), (kx + 13, ky + 13))
    t = ImageDraw.Draw(image)

    tx, ty, tw, th = local(GHFV_TAG, o)
    t.text((tx + tw / 2, ty + th / 2), "GHFV", font=font("arialbd.ttf", 15), fill=INK, anchor="mm")
    sx3, sy3, sw3, sh3 = local(SDV_TAG, o)
    t.text((sx3 + 8, sy3 + sh3 / 2), "SDV :", font=font("arial.ttf", 14), fill=INK, anchor="lm")

    hx, hy, hw, hh = local(HOPPER_CARD, o)
    card_title(t, hx + hw / 2, hy + 16, "PHỄU XẢ", hw)
    t.text((hx + hw - 12, hy + 60), "kg", font=font("arial.ttf", 14), fill=INK, anchor="rm")
    heading(t, kx + 48, ky + 17, "VAN XẢ PHỄU", kw - 56, 13)
    t.text((kx + 48, ky + 33), "Y-002", font=font("arial.ttf", 12), fill=MUTED, anchor="lm")
    rx, ry, rw, rh = local(RATE_CARD, o)
    card_title(t, rx + rw / 2, ry + 16, "TỐC ĐỘ XẢ", rw)
    t.text((rx + rw - 12, ry + 60), "kg/p", font=font("arial.ttf", 14), fill=INK, anchor="rm")
    cx2, cy2, cw, ch = local(CURRENT_CARD, o)
    card_title(t, cx2 + cw / 2, cy2 + 18, "TRỌNG LƯỢNG HIỆN TẠI", cw)
    t.text((cx2 + cw - 12, cy2 + 70), "kg", font=font("arial.ttf", 15), fill=INK, anchor="rm")
    heading(t, vx + 48, vy + 17, "ĐỘNG CƠ HÚT", vw - 56, 13)
    t.text((vx + 48, vy + 33), "M-009", font=font("arial.ttf", 12), fill=MUTED, anchor="lm")
    t.text((vx + vw / 4, vy + 64), "Áp suất [kPa]", font=font("arial.ttf", 11), fill=INK, anchor="mm")
    t.text((vx + vw * 3 / 4, vy + 64), "Dec.Time [s]", font=font("arial.ttf", 11), fill=INK, anchor="mm")
    return image


def status_bar() -> Image.Image:
    x, y, w, h = STATUS
    s = 4
    big = Image.new("RGBA", (w * s, h * s), rgb(PAGE) + (255,))
    d = ImageDraw.Draw(big)
    rounded(d, (0, 0, w, h))
    d.rectangle((0, 0, 4 * s, h * s - 1), fill=LEADER)
    rounded(d, (12, 8, 46, 30), fill=TILE, outline=TILE, radius=5)
    for dx in (480, 580):
        d.line((dx * s, 8 * s, dx * s, (h - 8) * s), fill=CARD_LINE, width=s)
    image = big.resize((w, h), Image.LANCZOS)
    t = ImageDraw.Draw(image)
    t.text((70, h / 2), "TRẠNG THÁI", font=font("arial.ttf", 13), fill=MUTED, anchor="lm")
    t.text((492, h / 2), "BỒN", font=font("arial.ttf", 14), fill=MUTED, anchor="lm")
    image.alpha_composite(icon("clock", 20, NAV_INK, px=1.5, cut=WHITE), (592, (h - 20) // 2))
    t.text((664, h / 2), "s", font=font("arial.ttf", 14), fill=MUTED, anchor="lm")
    return image


def weight_card(entry: bool) -> Image.Image:
    x, y, w, h = WEIGHT
    big, d = fill.card_base(WEIGHT)
    if entry:  # a grey well says the number can be typed
        tx, ty, tw, th = local(TARGET, (x, y))
        rounded(d, (tx - 4, ty + 2, tw - 2, th - 4), fill=TILE, outline=TILE, radius=6)  # ends 8 px before "kg"
    image = big.resize((w, h), Image.LANCZOS)
    image.alpha_composite(icon("target", 22, NAV_INK, px=1.5, cut=TILE), (16, 16))
    t = ImageDraw.Draw(image)
    heading(t, 56, 27, "TRỌNG LƯỢNG XẢ", TICK[0] - x - 64)
    t.text((w - 22, 92), "kg", font=font("arial.ttf", 18), fill=INK, anchor="rm")
    mid = w // 2 - 14
    for dx, colour in ((-44, CARD_LINE), (0, NAV_INK), (44, CARD_LINE)):
        t.line((mid + dx - 16, 136, mid + dx + 16, 136), fill=colour, width=2 if colour == NAV_INK else 1)
    return image


def select_card(title: str, gear: bool) -> Image.Image:
    x, y, w, h = SILO
    big, d = fill.card_base(SILO)
    s = 4
    ry = MODE_RULE - y
    d.line((16 * s, ry * s, (w - 16) * s, ry * s), fill=CARD_LINE, width=s)
    rounded(d, (10, ry + 10, 34, 34), fill=TILE, outline=TILE, radius=5)
    image = big.resize((w, h), Image.LANCZOS)
    image.alpha_composite(icon("cylinder", 22, NAV_INK, px=1.5, cut=TILE), (16, 16))
    image.alpha_composite(icon("sliders-horizontal", 22, NAV_INK, px=1.5, cut=TILE), (16, ry + 16))
    t = ImageDraw.Draw(image)
    heading(t, 56, 27, title, (GEAR[0] - x - 60) if gear else w - 72)
    heading(t, 56, ry + 27, "CHẾ ĐỘ", 120)
    return image


def tick_face(done: bool) -> Image.Image:
    _, _, w, h = TICK
    image = Image.new("RGBA", (w, h), rgb(WHITE) + (255,))
    image.alpha_composite(icon("circle-check" if done else "circle", w, OK if done else CARD_LINE, px=2.0), (0, 0))
    return image


def gear_face() -> Image.Image:
    _, _, w, h = GEAR
    image = Image.new("RGBA", (w, h), rgb(WHITE) + (255,))
    image.alpha_composite(icon("settings", 24, NAV_INK, px=1.75), ((w - 24) // 2, (h - 24) // 2))
    return image


def valve_button_face(label: str, name: str, on: bool) -> Image.Image:
    """Y-002's buttons: grey tile idle, white and bold when on / held."""
    w, h = VALVE_BTN[0][2], VALVE_BTN[0][3]
    s = 4
    back = WHITE if on else "#F6F7F9"
    big = Image.new("RGBA", (w * s, h * s), rgb(WHITE) + (255,))
    d = ImageDraw.Draw(big)
    rounded(d, (0, 0, w, h), fill=back, outline="#8E959C" if on else CARD_LINE, radius=6, width=2 if on else 1)
    image = big.resize((w, h), Image.LANCZOS)
    image.alpha_composite(icon(name, 24, INK if on else NAV_INK, px=1.75), ((w - 24) // 2, 12))
    t = ImageDraw.Draw(image)
    t.text((w / 2, 52), label, font=font("arialbd.ttf" if on else "arial.ttf", 12), fill=INK, anchor="mm")
    return image


def render(folder: Path, p: str, cfg: dict) -> dict[str, Path]:
    faces = {
        f"{p}_process": process_drawing(),
        f"{p}_status_bar": status_bar(),
        f"{p}_weight_card": weight_card(cfg["entry"]),
        f"{p}_select_card": select_card(cfg["select"], cfg["gear"]),
        f"{p}_start_0": fill.start_face(False, "BẮT ĐẦU", "DỪNG", 15),
        f"{p}_start_1": fill.start_face(True, "BẮT ĐẦU", "DỪNG", 15),
        f"{p}_mode_0": fill.mode_face(False, ("THỦ CÔNG", "TỰ ĐỘNG"), 12),
        f"{p}_mode_1": fill.mode_face(True, ("THỦ CÔNG", "TỰ ĐỘNG"), 12),
        f"{p}_tick_0": tick_face(False),
        f"{p}_tick_1": tick_face(True),
        f"{p}_man_0": valve_button_face("Thủ công", "hand", False),
        f"{p}_man_1": valve_button_face("Thủ công", "hand", True),
        f"{p}_run_0": valve_button_face("Xả liệu", "arrow-down-to-line", False),
        f"{p}_run_1": valve_button_face("Xả liệu", "arrow-down-to-line", True),
        f"{p}_valve_0": fill._flat(ICONS / "Van_Off.png", PAGE),
        f"{p}_valve_1": fill._flat(ICONS / "Van_On.png", PAGE),
        f"{p}_field_0": fill.field_face(False),
        f"{p}_field_1": fill.field_face(True),
        **{f"{p}_row_{i}_0": fill.row_face(i, False) for i in range(ROWS)},
    }
    if cfg["gear"]:
        faces[f"{p}_gear"] = gear_face()
    folder.mkdir(parents=True, exist_ok=True)
    paths = {}
    for key, image in faces.items():
        path = folder / f"{key}.png"
        image.save(path)
        paths[key] = path
    return paths


def build(project: Project, donor: Project, asset_dir: str, p: str) -> None:
    cfg = PAGES[p]
    A = cfg["addresses"]
    page = project.screen(cfg["screen"])

    for element in [e for e in page.elements if e.name.startswith(f"{p}_")][::-1]:
        edit.delete_element(project, page, element.index)
    popup = fill.silo_popup(project, donor, cfg["popup"])
    frame.prune_bank(project)

    tpl_rect = donor.element("scr_MainScreen", 1)
    tpl_num = donor.element("scr_Calibcation", 19)
    tpl_entry = donor.element("scr_Discharge", 52)
    tpl_multi = donor.element("scr_Discharge", 97)
    tpl_graphic = donor.element("scr_MainScreen", 2)
    tpl_push = donor.element("scr_Calibcation", 4)
    text_donor = Project(fill.DONOR_TEXT).element("Screen_1", 2)
    set_donor = Project(fill.DONOR_SET).element("Fill", 62)
    tpl_goto = next(e for e in page.elements if e.name == "nav_setting")

    assets = render(Path(asset_dir), p, cfg)
    bank = frame.Bank(project)
    for key, file in assets.items():
        bank.add(key, file)
    bank.commit()

    def picture(key, x, y, back=PAGE):
        _, _, w, h = bank.where[key]
        item = edit.clone_element(project, tpl_rect, page, 0, 0, 10, 10, key)
        clear_links(item)
        frame.face(item, bank, key)
        frame.flat(item, back)
        for state in item.states:
            state.set("TransColor", bgr(back))
        frame.picture_rect(item, x, y, w, h)
        return item

    def number(name, box, size, digits, decimals, align=CENTRE, colour=INK, template=None):
        x, y, w, h = box
        item = edit.clone_element(project, template or tpl_num, page, x, y, w, h, name)
        clear_links(item)
        for key in ("ReadVar", "WriteVar"):
            if item.section.get(key) not in (None, "None"):
                item.section.set(key, A[name])
        item.section.set("IntNum", digits)
        item.section.set("DotNum", decimals)
        if cfg["entry"] and template is tpl_entry:  # one signed word like the displays, value x10 - not the donor's 2-word REAL
            item.section.set("MemFmt", 2)
            item.section.set("MemLen", 1)
        item.section.set("Style", 3)
        text_style(item, size, colour, True, align)
        return item

    def graphic(name, keys, x, y, w, h, back):
        item = edit.clone_element(project, tpl_graphic, page, 0, 0, 10, 10, name)
        clear_links(item)
        item.section.set("ReadVar", A[name])
        for i, key in enumerate(keys):
            picture_on(item, i, bank, key, x, y, w, h, back)
        frame.flat(item, back)
        frame.picture_rect(item, x, y, w, h)
        return item

    def push(screen, name, box, faces, address, read=None, on_macro=None):
        x, y, w, h = box
        item = edit.clone_element(project, tpl_push, screen, x, y, w, h, name)
        clear_links(item)
        bind(item, address)
        if read:
            item.section.set("ReadVar", read)
        item.section.set("Style", 3)
        macro.set_macro(item.section, "ButtonOnMacroLen", on_macro)
        macro.set_macro(item.section, "ButtonOffMacroLen", None)
        for i, key in enumerate(faces):
            edit.set_state_text(item, "", "", state=i)
            picture_on(item, i, bank, key, x, y, w, h, WHITE)
        return item

    def toggle(name, box, faces):
        x, y, w, h = box
        item = edit.clone_element(project, tpl_multi, page, x, y, w, h, name)
        clear_links(item)
        bind(item, A[name])
        for i, key in enumerate(faces):
            edit.set_state_text(item, "", "", state=i)
            picture_on(item, i, bank, key, x, y, w, h, WHITE)
        return item

    def name_text(screen, key, x, y, w, h, size, bold):
        item = edit.clone_element(project, text_donor, screen, x, y, w, h, key)
        clear_links(item)
        item.section.set("ReadVar", A[key])
        item.section.set("StringLen", fill.NAME_CHARS)
        item.section.set("Style", 3)
        text_style(item, size, INK, bold, LEFT)
        return item

    # --- static artwork first ---------------------------------------------------
    picture(f"{p}_process", PROCESS[0], PROCESS[1])
    picture(f"{p}_status_bar", STATUS[0], STATUS[1])
    picture(f"{p}_weight_card", WEIGHT[0], WEIGHT[1])
    picture(f"{p}_select_card", SILO[0], SILO[1])

    # --- status bar and process ---------------------------------------------------
    sx, sy = STATUS[0], STATUS[1]
    number(f"{p}_status", (sx + 14, sy + 11, 42, 24), 18, 3, 0)
    number(f"{p}_status_silo", (sx + 530, sy + 11, 40, 24), 18, 2, 0)
    number(f"{p}_status_time", (sx + 616, sy + 11, 44, 24), 18, 4, 0, align=RIGHT)

    graphic(f"{p}_ghfv", (f"{p}_valve_0", f"{p}_valve_1"), *GHFV_AT, 26, 26, PAGE)
    graphic(f"{p}_sdv", (f"{p}_valve_0", f"{p}_valve_1"), *SDV_AT, 26, 26, PAGE)
    number(f"{p}_sdv_no", (SDV_TAG[0] + 44, SDV_TAG[1] + 3, 22, 22), 16, 1, 0, align=LEFT)

    hx, hy, hw, hh = HOPPER_CARD
    number(f"{p}_hopper", (hx + 6, hy + 45, 60, 30), 24, 3, 1, align=RIGHT)
    rx, ry, rw, rh = RATE_CARD
    number(f"{p}_rate", (rx + 6, ry + 45, 68, 30), 24, 3, 1, align=RIGHT)
    cx, cy, cw, ch = CURRENT_CARD
    number(f"{p}_current", (cx + 6, cy + 53, 90, 32), 24, 5, 1, align=RIGHT)
    vx, vy, vw, vh = VAC_CARD
    number(f"{p}_pressure", (vx + 4, vy + 78, vw // 2 - 8, 28), 20, 3, 1)
    number(f"{p}_dec_time", (vx + vw // 2 + 4, vy + 78, vw // 2 - 8, 28), 20, 2, 0)
    toggle(f"{p}_valve_man", VALVE_BTN[0], (f"{p}_man_0", f"{p}_man_1"))
    push(page, f"{p}_valve_run", VALVE_BTN[1], (f"{p}_run_0", f"{p}_run_1"), A[f"{p}_valve_run"])

    # --- right column ------------------------------------------------------------------
    graphic(f"{p}_done", (f"{p}_tick_0", f"{p}_tick_1"), *TICK, WHITE)
    number(f"{p}_target", TARGET, 64, 3, 1, colour="#2B3644", template=tpl_entry if cfg["entry"] else None)
    if cfg["gear"]:  # opens Setting, like the side bar's own Setting entry
        gx, gy, gw, gh = GEAR
        gear = edit.clone_element(project, tpl_goto, page, gx, gy, gw, gh, f"{p}_gear")
        frame.face(gear, bank, f"{p}_gear")
        frame.flat(gear, WHITE)

    fx, fy, fw, fh = COMBO
    push(page, f"{p}_silo_field", COMBO, (f"{p}_field_0", f"{p}_field_0"), A[f"{p}_open"],
         on_macro=macro.screen_statement(macro.OPENSCREEN, popup.id))
    name_text(page, f"{p}_name", fx + 12, fy + 9, fw - 50, 24, 16, True)

    close = macro.screen_statement(macro.CLOSESUBSCREEN, popup.id)
    push(popup, f"{p}_silo_close", (0, 0, fw, fh), (f"{p}_field_1", f"{p}_field_1"), A[f"{p}_open"], on_macro=close)
    name_text(popup, f"{p}_name", 12, 9, fw - 50, 24, 16, True)
    for i in range(ROWS):
        y = fh + ROW_H * i
        row = edit.clone_element(project, set_donor, popup, 0, y, fw, ROW_H, f"{p}_row_{i + 1}")
        clear_links(row)
        row.section.set("WriteVar", A[f"{p}_silo"])
        row.section.set("SetValue", i)
        row.section.set("Style", 3)
        macro.set_macro(row.section, "BeforeExecMacroLen", None)
        macro.set_macro(row.section, "AfterExecMacroLen", close)
        row.states[0].items = copy.deepcopy(tpl_push.states[0].items)
        edit.set_state_text(row, "", "", state=0)
        picture_on(row, 0, bank, f"{p}_row_{i}_0", 0, y, fw, ROW_H, WHITE)
        name_text(popup, f"{p}_name_{i + 1}", 40, y + 8, fw - 52, 24, 14, False)

    push(page, f"{p}_start", START, (f"{p}_start_0", f"{p}_start_1"), A[f"{p}_start"], read=A[f"{p}_running"])
    toggle(f"{p}_mode", MODE_BTN, (f"{p}_mode_0", f"{p}_mode_1"))

    print(f"{cfg['screen']}: {len(page.elements)} elements, {cfg['popup']}: {len(popup.elements)}")


def main(path: str, asset_dir: str) -> None:
    project = Project(path)
    donor = Project(fill.DONOR)
    for p in PAGES:
        build(project, donor, asset_dir, p)
    print(project.save(path))


if __name__ == "__main__":
    if len(sys.argv) != 3:
        raise SystemExit(__doc__)
    main(*sys.argv[1:])
