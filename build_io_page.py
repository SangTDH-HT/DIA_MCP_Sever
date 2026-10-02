"""Draw the manual-control page of the Silo HMI (Set_IO, the "I/O" tile of Settings).

Run:  python build_io_page.py <project.dpa> <asset folder> <hmi_map.json>

The page is the Delta counterpart of OTL-30's Overview_Silo in manual mode: one
button for each valve and for the suction motor, named as on OTL-30 (SFV1..6,
SDV1..6, GHFV, GHDV, HOPPER, VACUUM), driving the PLC's manual mode (FC
"Call_Manual" -> "Manual_Silo", DB "Data_Manual") through DB "HMI".Io.

  top    status bar: interlock code and message, seconds before a valve may close
         AUTO | MANUAL switch, Reset fault
  left   SILO VALVES   a column a silo: SFV on top, the silo, SDV under it,
                       the silo's name and weight
  right  MOTOR AND HOPPERS   VACUUM, HOPPER, GHFV, GHDV; motor feedback, pressure

Locks, as on OTL-30:
  - a device button answers only in manual mode: its interlock is "HMI".Io.ModeManual,
    so outside manual mode the panel itself refuses the press;
  - the MANUAL button answers only while the line is free ("HMI".Io.Free: the
    arbiter has given the line to nobody, or to manual mode);
  - in manual mode every press still goes through the interlocks of "Manual_Silo";
    a refused press drops the button again and the status bar says why.
A button shows the real state of its %Q terminal, not the command.

Back link and title come from build_setting_page.py, like every Settings
sub-page. Everything said in words is an element text in three languages
(silo_i18n); pictures carry no words. Elements are cloned from the project's
own pages, so the Fill page must exist. Re-runnable: elements named "io_" are
removed first. Run it after translate_silo.py; the addresses come straight
from hmi_map.json, so bind_plc.py has nothing to do for this page.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

from PIL import Image

import build_fill_page as fill
import build_silo_frame as frame
import silo_i18n as i18n
from build_clean_page import BAD, BUSY, VALUE, add_states, canvas, card, find
from build_fill_page import CARD_LINE, FIELD_LINE, TILE, clear_links, line_art, picture_on, rounded
from build_setting_page import CONTENT_TOP
from build_silo_frame import INK, MUTED, NAV_INK, PAGE, WHITE, bgr, icon, rgb
from dpa import edit
from dpa.document import Entry
from dpa.model import Project

SCREEN = "Set_IO"
LEFT, CENTRE, RIGHT = 33, 34, 36
ON_FILL, ON_LINE = fill.GO[0], fill.GO[2]        # a device that is on: the START green
BAD_FILL = fill.STOP[0]

# Content x 100..1016, y CONTENT_TOP..592.
STATUS = (100, CONTENT_TOP, 560, 46)
SEG_TRACK = (670, CONTENT_TOP, 220, 46)
SEG = [(673, CONTENT_TOP + 3, 106, 40), (781, CONTENT_TOP + 3, 106, 40)]
RESET = (900, CONTENT_TOP, 116, 46)
VALVES = (100, 158, 640, 434)
SIDE = (750, 158, 266, 434)

COL_X = [170 + 100 * i for i in range(6)]        # centre line of each silo's column
BTN_W, BTN_H = 84, 48
SFV_Y, SILO_Y, SILO_H, SDV_Y = 208, 266, 184, 460
NAME_Y, WEIGHT_Y = 516, 540
DEV_X, DEV_W, DEV_H = 766, 104, 52
DEV_Y = [208 + 62 * i for i in range(4)]
SIDE_RULE = 462
DOT = 16

DEVICES = (  # button, press, shown, what it is (English, Vietnamese, French)
    ("VACUUM", "Io.BtnMotor", "Io.Motor", ("Suction motor", "Động cơ hút", "Aspiration")),
    ("HOPPER", "Io.BtnHopper", "Io.Hopper", ("Feed hopper", "Van phễu nạp", "Trémie d'alim.")),
    ("GHFV", "Io.BtnGhfv", "Io.Ghfv", ("Hopper inlet", "Van vào phễu xả", "Entrée trémie")),
    ("GHDV", "Io.BtnGhdv", "Io.Ghdv", ("Hopper outlet", "Van xả phễu xả", "Sortie trémie")),
)
RESET_WORDS = ("Reset fault", "Xoá lỗi", "Acquitter")
# "HMI".Io.Msg 0..21 - the order of the CASE in FB "HMI_Map" REGION 9 (MsgCode of "Manual_Silo" / "Call_Manual").
MESSAGES = (
    (("Ready", "Sẵn sàng", "Prêt"), MUTED),
    (("Switch to MANUAL first", "Chưa vào chế độ tay", "Passez d'abord en MANUEL"), BAD),                                    # 10
    (("Another SFV is open: close it first", "Đã có van nạp bồn khác mở: đóng van đó trước",
      "Une autre SFV est ouverte"), BAD),                                                                                # 11
    (("SFV: the discharge side is open", "Van nạp: nhánh xả đang mở", "SFV : côté vidange ouvert"), BAD),                 # 12
    (("SFV stays open: the pipe is being cleared", "Van nạp chưa đóng được: đang xả đường ống",
      "SFV maintenue ouverte : purge du tuyau"), BUSY),                                                                  # 13
    (("HOPPER: open an SFV and run the motor first", "Phễu nạp: mở van bồn và chạy động cơ trước",
      "HOPPER : ouvrir une SFV et démarrer le moteur"), BAD),                                                            # 14
    (("VACUUM: open a valve first", "Động cơ: chưa mở van nào", "VACUUM : ouvrir d'abord une vanne"), BAD),               # 21
    (("VACUUM stays on: close the SDV first", "Chưa tắt được động cơ: đóng van xả bồn trước",
      "VACUUM maintenu : fermer la SDV"), BAD),                                                                          # 22
    (("VACUUM is clearing the pipe and stops by itself", "Động cơ đang xả đường ống, xong sẽ tự tắt",
      "Purge du tuyau : le moteur s'arrêtera seul"), BUSY),                                                              # 23
    (("Leaving manual mode: devices are shutting down", "Đang thoát chế độ tay: thiết bị tắt dần",
      "Sortie du mode manuel : arrêt des appareils"), BUSY),                                                             # 24
    (("Manual mode is giving way to an automatic command", "Chế độ tay đang nhường cho lệnh tự động",
      "Le mode manuel cède à une commande automatique"), BUSY),                                                          # 25
    (("A batch is running: manual mode refused", "Đang chạy mẻ tự động: không vào được chế độ tay",
      "Lot en cours : mode manuel refusé"), BAD),                                                                        # 26
    (("SDV: open GHFV first", "Van xả bồn: chưa mở GHFV", "SDV : ouvrir d'abord GHFV"), BAD),                              # 31
    (("SDV: the motor is not running", "Van xả bồn: động cơ chưa chạy", "SDV : moteur à l'arrêt"), BAD),                   # 32
    (("Another silo is already discharging", "Đã có bồn khác đang xả", "Un autre silo est déjà en vidange"), BAD),        # 33
    (("SDV: the fill side is open", "Van xả bồn: nhánh nạp đang mở", "SDV : côté remplissage ouvert"), BAD),              # 34
    (("GHFV: the fill side is open", "GHFV: nhánh nạp đang mở", "GHFV : côté remplissage ouvert"), BAD),                  # 41
    (("GHFV stays open: close the SDV first", "GHFV chưa đóng được: còn van xả bồn mở",
      "GHFV maintenue : fermer la SDV"), BAD),                                                                           # 42
    (("GHFV stays open: the pipe is being cleared", "GHFV chưa đóng được: đang xả đường ống",
      "GHFV maintenue ouverte : purge du tuyau"), BUSY),                                                                 # 43
    (("GHDV closed itself: another device opened", "GHDV tự đóng: có thiết bị khác mở",
      "GHDV refermée : un autre appareil est ouvert"), BAD),                                                             # 51
    (("Suction motor overload: press Reset fault", "Quá tải động cơ hút: bấm Xoá lỗi",
      "Surcharge du moteur : appuyer sur Acquitter"), BAD),                                                              # 91
    (("Pressure over the limit: press Reset fault", "Áp suất vượt ngưỡng: bấm Xoá lỗi",
      "Pression hors limite : appuyer sur Acquitter"), BAD),                                                             # 92
)


# --- pictures (no words in any of them) --------------------------------------------

def status_bar() -> Image.Image:
    _, _, w, h = STATUS
    big, d = canvas(w, h)
    rounded(d, (0, 0, w, h))
    d.rectangle((0, 0, 16, h * 4 - 1), fill=fill.LEADER)
    rounded(d, (12, 8, 46, 30), fill=TILE, outline=TILE, radius=5)
    d.line(((w - 106) * 4, 32, (w - 106) * 4, (h - 8) * 4), fill=CARD_LINE, width=4)
    image = big.resize((w, h), Image.LANCZOS)
    image.alpha_composite(icon("clock", 20, NAV_INK, px=1.5, cut=WHITE), (w - 96, (h - 20) // 2))
    return image


def track_face() -> Image.Image:
    _, _, w, h = SEG_TRACK
    big, d = canvas(w, h)
    rounded(d, (0, 0, w, h), fill=TILE, outline=TILE, radius=8)
    return big.resize((w, h), Image.LANCZOS)


def silo_art(height: int) -> Image.Image:
    """Sang's silo drawing (drawn in red) in the page ink, on the card's white."""
    art = line_art("Silo_3.png", height=height, back=WHITE)
    mask = art.convert("L").point(lambda v: min(255, (255 - v) * 2) if v < 235 else 0)
    out = Image.new("RGBA", art.size, rgb(WHITE) + (255,))
    out.paste(Image.new("RGBA", art.size, rgb(NAV_INK) + (255,)), (0, 0), mask)
    return out


def valves_card() -> Image.Image:
    ox, oy = VALVES[0], VALVES[1]

    def more(d):
        for cx in COL_X:        # a stub from each button to its silo
            for y0, y1 in ((SFV_Y + BTN_H, SILO_Y), (SILO_Y + SILO_H, SDV_Y)):
                d.line(((cx - ox) * 4, (y0 - oy) * 4, (cx - ox) * 4, (y1 - oy) * 4), fill=FIELD_LINE, width=8)
    image = card(VALVES, "cylinder", more)
    silo = silo_art(SILO_H)
    for cx in COL_X:
        image.alpha_composite(silo, (cx - ox - silo.width // 2, SILO_Y - oy))
    return image


def side_card() -> Image.Image:
    ry = SIDE_RULE - SIDE[1]
    return card(SIDE, "fan", lambda d: d.line((16 * 4, ry * 4, (SIDE[2] - 16) * 4, ry * 4), fill=CARD_LINE, width=4))


def button_face(w: int, h: int, on: bool) -> Image.Image:
    big, d = canvas(w, h, WHITE)
    rounded(d, (0, 0, w, h), fill=ON_FILL if on else WHITE, outline=ON_LINE if on else FIELD_LINE, radius=6,
            width=2 if on else 1)
    return big.resize((w, h), Image.LANCZOS)


def seg_face(on: bool) -> Image.Image:
    _, _, w, h = SEG[0]
    big, d = canvas(w, h, TILE)
    if on:
        rounded(d, (0, 0, w, h), fill=WHITE, outline=FIELD_LINE, radius=6)
    return big.resize((w, h), Image.LANCZOS)


def reset_face(fault: bool) -> Image.Image:
    _, _, w, h = RESET
    big, d = canvas(w, h)
    rounded(d, (0, 0, w, h), fill=BAD_FILL if fault else WHITE, outline=BAD if fault else FIELD_LINE, radius=6)
    return big.resize((w, h), Image.LANCZOS)


def dot_face(colour: str | None) -> Image.Image:
    big, d = canvas(DOT, DOT, WHITE)
    if colour:
        d.ellipse((4, 4, DOT * 4 - 5, DOT * 4 - 5), fill=colour)
    else:
        d.ellipse((6, 6, DOT * 4 - 7, DOT * 4 - 7), fill=TILE, outline=FIELD_LINE, width=6)
    return big.resize((DOT, DOT), Image.LANCZOS)


def render(folder: Path) -> dict[str, Path]:
    faces = {
        "io_status_bar": status_bar(), "io_track": track_face(), "io_valves": valves_card(), "io_side": side_card(),
        "io_btn_0": button_face(BTN_W, BTN_H, False), "io_btn_1": button_face(BTN_W, BTN_H, True),
        "io_dev_0": button_face(DEV_W, DEV_H, False), "io_dev_1": button_face(DEV_W, DEV_H, True),
        "io_seg_0": seg_face(False), "io_seg_1": seg_face(True),
        "io_reset_0": reset_face(False), "io_reset_1": reset_face(True),
        "io_dot_0": dot_face(None), "io_dot_1": dot_face(ON_LINE), "io_dot_bad": dot_face(BAD),
    }
    folder.mkdir(parents=True, exist_ok=True)
    paths = {}
    for key, image in faces.items():
        paths[key] = folder / f"{key}.png"
        image.save(paths[key])
    return paths


# --- elements ---------------------------------------------------------------------------

def interlock(element, address: str) -> None:
    """The button answers only while this bit is ON; off, the panel shows it locked."""
    section = element.section
    for key, value in (("InterLockLink", "1"), ("InterLockVar", address)):
        if section.entries(key):
            section.set(key, value)
        else:   # the template never had one: the pair goes where DIAScreen keeps it, right before InterLockLevel
            at = next(i for i, item in enumerate(section.items) if isinstance(item, Entry) and item.key == b"InterLockLevel")
            section.items.insert(at, Entry(key=key.encode(), value=value.encode(), blob=None, blob_eol=True))
    section.set("InterLockLevel", 1)        # operable while the bit is ON
    section.set("InterLockViewMode", 1)     # locked: the panel draws its no-entry mark on the button


def main(path: str, asset_dir: str, map_file: str) -> None:
    address = {k: v["address"] for k, v in json.load(open(map_file, encoding="utf-8"))["members"].items()}
    project = Project(path)
    i18n.ensure_languages(project)
    page = project.screen(SCREEN)
    for element in [e for e in page.elements if e.name.startswith("io_")][::-1]:
        edit.delete_element(project, page, element.index)

    home = "Home_Fill"
    tpl_rect, tpl_text = find(project, home, "fl_process"), find(project, home, "fl_status_bar_txt1")
    tpl_num, tpl_ind = find(project, home, "fl_rate"), find(project, home, "fl_fill_mode")
    tpl_push, tpl_graphic = find(project, home, "fl_start"), find(project, home, "fl_sfv")
    tpl_name = find(project, home, "fl_silo_name")
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

    def text(name, box, texts, size=14, colour=INK, bold=False, align=LEFT):
        x, y, w, h = box
        item = edit.clone_element(project, tpl_text, page, x, y, w, h, name)
        style(item, size, colour, bold, align)
        i18n.words(item, texts, size)
        return item

    def number(name, box, member, size, digits, decimals=0, align=CENTRE, colour=INK, bold=True):
        x, y, w, h = box
        item = edit.clone_element(project, tpl_num, page, x, y, w, h, name)
        clear_links(item)
        item.section.set("ReadVar", address[member])
        item.section.set("IntNum", digits)
        item.section.set("DotNum", decimals)
        style(item, size, colour, bold, align)
        return item

    def indicator(name, box, member, states, size):
        x, y, w, h = box
        item = edit.clone_element(project, tpl_ind, page, x, y, w, h, name)
        clear_links(item)
        item.section.set("ReadVar", address[member])
        item.section.set("MemLen", 1)          # a word: the state is the value
        item.section.set("AutoResizeByText", 0)
        add_states(project, item, len(states))
        style(item, size, INK)
        for n, (texts, colour) in enumerate(states):
            item.states[n].set("FontColor", bgr(colour))
            i18n.words(item, texts, size, state=n)
        return item

    def push(name, box, press, shown, faces, back, labels, size=14, lock=None):
        """Momentary: writes the press bit, shows the state the PLC reports."""
        x, y, w, h = box
        item = edit.clone_element(project, tpl_push, page, x, y, w, h, name)
        clear_links(item)
        item.section.set("WriteVar", address[press])
        item.section.set("ReadVar", address[shown])
        item.section.set("Style", 3)
        for n, key in enumerate(faces):
            picture_on(item, n, bank, key, x, y, w, h, back)
        for n, (texts, colour, bold) in enumerate(labels):
            item.states[n].set("FontColor", bgr(colour))
            item.states[n].set("FontBold", 1 if bold else 0)
            item.states[n].set("FontAlign", CENTRE)
            i18n.words(item, texts, size, state=n, margin=12)
        if lock:
            interlock(item, address[lock])
        return item

    def lamp(name, x, y, member, lit="io_dot_1"):
        item = edit.clone_element(project, tpl_graphic, page, 0, 0, 10, 10, name)
        clear_links(item)
        item.section.set("ReadVar", address[member])
        for n, key in enumerate(("io_dot_0", lit)):
            picture_on(item, n, bank, key, x, y, DOT, DOT, WHITE)
        frame.flat(item, WHITE)
        frame.picture_rect(item, x, y, DOT, DOT)
        return item

    def device(name, box, press, shown, faces, words, size=16):
        return push(name, box, press, shown, faces, WHITE, ((words, INK, True), (words, INK, True)), size, lock="Io.ModeManual")

    # --- artwork first -----------------------------------------------------------------
    for key, box in (("io_status_bar", STATUS), ("io_track", SEG_TRACK), ("io_valves", VALVES), ("io_side", SIDE)):
        picture(key, box)

    # --- status bar, mode, reset ------------------------------------------------------------
    sx, sy, sw, _ = STATUS
    number("io_code", (sx + 14, sy + 11, 42, 24), "Io.MsgCode", 18, 2)
    indicator("io_msg", (sx + 66, sy + 10, sw - 180, 26), "Io.Msg", MESSAGES, 14)
    number("io_hold", (sx + sw - 70, sy + 11, 44, 24), "Io.HoldLeft", 18, 4, align=RIGHT)
    text("io_t_s", (sx + sw - 24, sy + 12, 18, 21), "s", 14, MUTED)
    push("io_auto", SEG[0], "Io.BtnAuto", "Io.ModeAuto", ("io_seg_0", "io_seg_1"), TILE,
         ((("AUTO", "TỰ ĐỘNG", "AUTO"), MUTED, False), (("AUTO", "TỰ ĐỘNG", "AUTO"), INK, True)))
    push("io_manual", SEG[1], "Io.BtnManual", "Io.ModeManual", ("io_seg_0", "io_seg_1"), TILE,
         ((("MANUAL", "TAY", "MANUEL"), MUTED, False), (("MANUAL", "TAY", "MANUEL"), INK, True)), lock="Io.Free")
    push("io_reset", RESET, "Io.BtnReset", "Io.Fault", ("io_reset_0", "io_reset_1"), PAGE,
         ((RESET_WORDS, INK, False), (RESET_WORDS, BAD, True)))

    # --- silo valves: SFV over the silo, SDV under it ---------------------------------------
    vx, vy, vw, _ = VALVES
    text("io_t_valves", (vx + 52, vy + 17, 200, 21), ("SILO VALVES", "VAN BỒN", "VANNES DES SILOS"), 14, INK, True)
    text("io_t_legend", (vx + 260, vy + 18, vw - 276, 19),
         ("SFV fill valve, SDV discharge valve", "SFV van nạp, SDV van xả", "SFV remplissage, SDV vidange"), 12, MUTED, align=RIGHT)
    for n, cx in enumerate(COL_X, 1):
        x = cx - BTN_W // 2
        device(f"io_sfv_{n}", (x, SFV_Y, BTN_W, BTN_H), f"Io.BtnFill{n}", f"Io.Fill{n}", ("io_btn_0", "io_btn_1"), f"SFV{n}")
        device(f"io_sdv_{n}", (x, SDV_Y, BTN_W, BTN_H), f"Io.BtnDis{n}", f"Io.Dis{n}", ("io_btn_0", "io_btn_1"), f"SDV{n}")
        name = edit.clone_element(project, tpl_name, page, cx - 48, NAME_Y, 96, 20, f"io_name_{n}")
        clear_links(name)
        name.section.set("ReadVar", address[f"SiloName[{n}]"])
        style(name, 12, INK, True, CENTRE)
        number(f"io_weight_{n}", (cx - 44, WEIGHT_Y, 62, 24), f"Ov.Weight[{n}]", 16, 4, 1, RIGHT, VALUE)
        text(f"io_t_kg_{n}", (cx + 20, WEIGHT_Y + 3, 26, 19), "kg", 12, MUTED)

    # --- motor and hoppers ------------------------------------------------------------------
    dx, dy, dw, _ = SIDE
    text("io_t_side", (dx + 52, dy + 17, dw - 68, 21), ("MOTOR AND HOPPERS", "ĐỘNG CƠ VÀ PHỄU", "MOTEUR ET TRÉMIES"), 14, INK, True)
    for n, (y, (words, press, shown, about)) in enumerate(zip(DEV_Y, DEVICES), 1):
        device(f"io_dev_{n}", (DEV_X, y, DEV_W, DEV_H), press, shown, ("io_dev_0", "io_dev_1"), words)
        text(f"io_t_dev_{n}", (DEV_X + DEV_W + 10, y + 15, dw - DEV_W - 42, 21), about, 14, MUTED)
    text("io_t_run", (dx + 40, SIDE_RULE + 14, 150, 21), ("Motor running", "Động cơ đang chạy", "Moteur en marche"), 14, INK)
    lamp("io_run", dx + 16, SIDE_RULE + 17, "Io.DiRun")
    text("io_t_trip", (dx + 40, SIDE_RULE + 44, 150, 21), ("Motor fault", "Động cơ báo lỗi", "Défaut du moteur"), 14, INK)
    lamp("io_trip", dx + 16, SIDE_RULE + 47, "Io.DiTrip", "io_dot_bad")
    text("io_t_pressure", (dx + 16, SIDE_RULE + 82, 96, 21), ("Pressure", "Áp suất", "Pression"), 14, INK)
    number("io_pressure", (dx + 112, SIDE_RULE + 78, 96, 28), "Io.Pressure", 20, 4, 1, RIGHT, VALUE)
    text("io_t_kpa", (dx + 212, SIDE_RULE + 82, 40, 21), "kPa", 14, MUTED)

    i18n.ensure_languages(project)
    print(project.save(path))
    print(f"{SCREEN} (id {page.id}): {len(page.elements)} elements")


if __name__ == "__main__":
    if len(sys.argv) != 4:
        raise SystemExit(__doc__)
    main(*sys.argv[1:])
