"""Draw the Clean-line page of the Silo HMI (Home_Clean) and give Home its fourth tab.

Run:  python build_clean_page.py <project.dpa> <asset folder> <hmi_map.json>

The page drives FB "Clean_Line" of PLC_SILO_6_Sa through DB "HMI".Cl:

  left   status bar (code, message, silo, seconds left)
         LINE      which line to sweep: fill, discharge or both
         SILOS     six chips, each with the silo's own name and its state
         CONDITIONS / SETTINGS  why it may not start; sweep time, time limit, pump speed
  right  PROGRESS  percent
         START / STOP on the round button, line and step under it

Everything said in words is an element text in three languages (silo_i18n) -
pictures carry no words, so every label is edited in DIAScreen. The page is a
Home page, so the header tabs (silo_tabs.py) are redrawn on every Home page.

Elements are cloned from the project's own pages (number from fl_rate, button
from fl_start, ...), so the project must already have the Fill and Parameter
pages. Re-runnable: elements named "cl_" and "tab_" are removed first.
"""

from __future__ import annotations

import copy
import json
import sys
from pathlib import Path

from PIL import Image, ImageDraw

import build_fill_page as fill
import build_silo_frame as frame
import silo_i18n as i18n
import silo_tabs as tabs
from build_fill_page import CARD_LINE, FIELD_LINE, TILE, clear_links, picture_on, rounded
from build_silo_frame import INK, MUTED, NAV_INK, NAV_ON, PAGE, WHITE, bgr, icon, rgb
from dpa import edit
from dpa.model import Project

SCREEN = "Home_Clean"
LEFT, CENTRE, RIGHT = 33, 34, 36
GOOD, BAD, BUSY = "#2BB35A", "#F0405A", "#1F6FB2"
VALUE = "#2B3644"
CHIP_ON = "#EAF2FA"

# Panel layout, the Home grid: content x 100..1016, y 66..592.
STATUS = (100, 66, 674, 46)
LINE_CARD = (100, 120, 674, 96)
SILO_CARD = (100, 226, 674, 178)
COND_CARD = (100, 414, 330, 178)
SET_CARD = (440, 414, 334, 178)
PROGRESS = (784, 66, 232, 144)
RUN = (784, 222, 232, 370)
SEG = [(120 + 212 * i, 174, 210, 30) for i in range(3)]
CHIP_W, CHIP_H = 206, 56
CHIPS = [(116 + 218 * (i % 3), 276 + 64 * (i // 3), CHIP_W, CHIP_H) for i in range(6)]
ENTRY = [(686, 456 + 44 * i, 66, 34) for i in range(3)]
DISC = (835, 270, 130, 130)
RUN_RULE = 424

LINES = (("Fill line", "Đường nạp", "Ligne de remplissage"),
         ("Discharge line", "Đường xả", "Ligne de vidange"),
         ("Both lines", "Cả hai đường", "Les deux lignes"))
# "HMI".Cl.Msg 0..19 - the order of the CASE in FB "HMI_Map" REGION 8.
MESSAGES = (
    (("Ready", "Sẵn sàng", "Prêt"), MUTED),
    (("Sweeping the fill line", "Đang quét đường nạp", "Balayage de la ligne de remplissage"), BUSY),
    (("Sweeping the discharge line", "Đang quét đường xả", "Balayage de la ligne de vidange"), BUSY),
    (("Waiting for valves and motor", "Đang chờ van và động cơ", "Attente des vannes et du moteur"), BUSY),
    (("Emptying the hopper", "Đang xả phễu", "Vidange de la trémie"), BUSY),
    (("Clearing the pipe before the next silo", "Đang xả ống trước bồn kế", "Purge du tuyau avant le silo suivant"), BUSY),
    (("Silo timed out, moving on", "Bồn vừa rồi hết giờ, chuyển bồn", "Délai dépassé, silo suivant"), BAD),
    (("Finished", "Đã xong", "Terminé"), GOOD),
    (("Roaster is running", "Máy đang rang", "Torréfacteur en marche"), BAD),
    (("Filling or discharging is running", "Hệ nạp / xả đang chạy", "Remplissage ou vidange en cours"), BAD),
    (("Manual mode is on", "Đang ở chế độ tay", "Mode manuel actif"), BAD),
    (("Selected silos hold more than the hopper", "Bồn chọn nhiều hơn sức chứa phễu", "Silos choisis : plus que la trémie"), BAD),
    (("Select a silo first", "Chưa chọn bồn", "Choisissez un silo"), BAD),
    (("Select a line first", "Chưa chọn đường", "Choisissez une ligne"), BAD),
    (("Sweep time is out of range", "Thời gian quét ngoài khoảng", "Durée de balayage hors plage"), BAD),
    (("Time limit is out of range", "Thời gian tối đa ngoài khoảng", "Durée maximale hors plage"), BAD),
    (("Suction motor stopped during cleaning", "Mất động cơ hút giữa chừng", "Moteur arrêté pendant le nettoyage"), BAD),
    (("Suction motor is not ready", "Động cơ hút chưa sẵn sàng", "Moteur d'aspiration non prêt"), BAD),
    (("Stopped before the end", "Đã dừng giữa chừng", "Arrêté avant la fin"), BAD),
    (("Finished, but a silo is not empty", "Xong, nhưng còn bồn chưa sạch", "Terminé, mais un silo n'est pas vide"), BAD),
)
SILO_STATES = (  # "HMI".Cl.SiloSt 0..6
    (("Not selected", "Không chọn", "Non sélectionné"), MUTED),
    (("Not cleaned yet", "Chưa làm sạch", "Pas encore nettoyé"), INK),
    (("Waiting its turn", "Chờ tới lượt", "En attente"), INK),
    (("Sweeping fill line", "Đang quét đường nạp", "Balayage remplissage"), BUSY),
    (("Sweeping discharge line", "Đang quét đường xả", "Balayage vidange"), BUSY),
    (("Clean", "Đã sạch", "Propre"), GOOD),
    (("Timed out, not empty", "Hết giờ, chưa sạch", "Délai dépassé, non vide"), BAD),
)
IDLE_STATES = (  # "HMI".Cl.IdleSt 0..4
    (("System is idle", "Hệ thống đang rảnh", "Système libre"), GOOD),
    (("Roaster is running", "Máy đang rang", "Torréfacteur en marche"), BAD),
    (("Filling or discharging is running", "Hệ nạp / xả đang chạy", "Remplissage ou vidange en cours"), BAD),
    (("Manual mode is on", "Đang ở chế độ tay", "Mode manuel actif"), BAD),
    (("Suction motor is not ready", "Động cơ hút chưa sẵn sàng", "Moteur d'aspiration non prêt"), BAD),
)
WEIGHT_STATES = (  # "HMI".Cl.WeightSt 0..3
    (("Fill line only: weight is not checked", "Chỉ đường nạp: không xét trọng lượng", "Remplissage seul : poids non vérifié"), MUTED),
    (("No silo selected", "Chưa chọn bồn", "Aucun silo choisi"), INK),
    (("Selected silos fit the hopper", "Bồn chọn vừa sức chứa phễu", "Les silos choisis tiennent dans la trémie"), GOOD),
    (("Selected silos hold more than the hopper", "Bồn chọn nhiều hơn sức chứa phễu", "Silos choisis : plus que la trémie"), BAD),
)
NOW_STATES = ((("–", "–", "–"), MUTED), (("Fill", "Nạp", "Remplissage"), VALUE), (("Discharge", "Xả", "Vidange"), VALUE))
SETTINGS = (  # label, member of "HMI".Cl, unit, min, max
    (("Fill line: sweep time per silo", "Đường nạp: thời gian quét mỗi bồn", "Remplissage : balayage par silo"), "Cl.PurgeSec", "s", 3, 300),
    (("Discharge line: time limit per silo", "Đường xả: thời gian tối đa mỗi bồn", "Vidange : durée max. par silo"), "Cl.DisSec", "s", 10, 1800),
    (("Pump speed", "Tốc độ bơm", "Vitesse de la pompe"), "Cl.Speed", "%", 0, 100),
)


# --- pictures (no words in any of them) --------------------------------------------

def canvas(w, h, back=PAGE):
    big = Image.new("RGBA", (w * 4, h * 4), rgb(back) + (255,))
    return big, ImageDraw.Draw(big)


def card(box, glyph: str | None, draw_more=None) -> Image.Image:
    _, _, w, h = box
    big, d = canvas(w, h)
    rounded(d, (0, 0, w, h))
    if glyph:
        rounded(d, (10, 10, 34, 34), fill=TILE, outline=TILE, radius=5)
    if draw_more:
        draw_more(d)
    image = big.resize((w, h), Image.LANCZOS)
    if glyph:
        image.alpha_composite(icon(glyph, 22, NAV_INK, px=1.5, cut=TILE), (16, 16))
    return image


def status_bar() -> Image.Image:
    _, _, w, h = STATUS
    big, d = canvas(w, h)
    rounded(d, (0, 0, w, h))
    d.rectangle((0, 0, 16, h * 4 - 1), fill=fill.LEADER)
    rounded(d, (12, 8, 46, 30), fill=TILE, outline=TILE, radius=5)
    for dx in (480, 580):
        d.line((dx * 4, 32, dx * 4, (h - 8) * 4), fill=CARD_LINE, width=4)
    image = big.resize((w, h), Image.LANCZOS)
    image.alpha_composite(icon("clock", 20, NAV_INK, px=1.5, cut=WHITE), (592, (h - 20) // 2))
    return image


def line_card() -> Image.Image:
    return card(LINE_CARD, "waypoints", lambda d: rounded(d, (16, 50, 642, 38), fill=TILE, outline=TILE, radius=8))


def cond_card() -> Image.Image:
    def more(d):
        for y in (80, 114):
            d.line((16 * 4, y * 4, (COND_CARD[2] - 16) * 4, y * 4), fill=CARD_LINE, width=4)
    return card(COND_CARD, "shield-check", more)


def set_card() -> Image.Image:
    ox, oy = SET_CARD[0], SET_CARD[1]
    return card(SET_CARD, "sliders-horizontal",
                lambda d: [rounded(d, (x - ox, y - oy, w, h), outline=FIELD_LINE) for x, y, w, h in ENTRY])


def run_card() -> Image.Image:
    w = RUN[2]
    ry = RUN_RULE - RUN[1]
    return card(RUN, "wind", lambda d: d.line((16 * 4, ry * 4, (w - 16) * 4, ry * 4), fill=CARD_LINE, width=4))


def seg_face(on: bool) -> Image.Image:
    _, _, w, h = SEG[0]
    big, d = canvas(w, h, TILE)
    if on:
        rounded(d, (0, 0, w, h), fill=WHITE, outline=FIELD_LINE, radius=6)
    return big.resize((w, h), Image.LANCZOS)


def chip_face(on: bool) -> Image.Image:
    big, d = canvas(CHIP_W, CHIP_H, WHITE)
    rounded(d, (0, 0, CHIP_W, CHIP_H), fill=CHIP_ON if on else WHITE, outline=NAV_ON if on else FIELD_LINE, radius=6)
    image = big.resize((CHIP_W, CHIP_H), Image.LANCZOS)
    back = CHIP_ON if on else WHITE
    glyph = icon("circle-check", 22, NAV_ON, px=1.75, cut=back) if on else icon("circle", 22, FIELD_LINE, px=1.75, cut=back)
    image.alpha_composite(glyph, (CHIP_W - 34, (CHIP_H - 22) // 2))
    return image


def render(folder: Path) -> dict[str, Path]:
    faces = {
        "cl_status_bar": status_bar(), "cl_line_card": line_card(), "cl_silo_card": card(SILO_CARD, "cylinder"),
        "cl_cond_card": cond_card(), "cl_set_card": set_card(), "cl_progress_card": card(PROGRESS, "gauge"),
        "cl_run_card": run_card(),
        "cl_seg_0": seg_face(False), "cl_seg_1": seg_face(True),
        "cl_chip_0": chip_face(False), "cl_chip_1": chip_face(True),
        "cl_start_0": fill.start_face(False, "", ""), "cl_start_1": fill.start_face(True, "", ""),
        **tabs.faces(),
    }
    folder.mkdir(parents=True, exist_ok=True)
    paths = {}
    for key, image in faces.items():
        paths[key] = folder / f"{key}.png"
        image.save(paths[key])
    return paths


# --- elements ---------------------------------------------------------------------------

def add_states(project: Project, element, count: int) -> None:
    """Grow an indicator to `count` states: copies of its last state, valued 0..count-1."""
    doc = project.doc
    while len(element.states) < count:
        state = copy.deepcopy(element.states[-1])
        state.set("Value", len(element.states))
        at = max(i for i, s in enumerate(doc.sections) if s is element.states[-1]) + 1
        doc.sections.insert(at, state)
        element.states.append(state)


def find(project: Project, screen: str, name: str):
    return next(e for e in project.screen(screen).elements if e.name == name)


def main(path: str, asset_dir: str, map_file: str) -> None:
    address = {k: v["address"] for k, v in json.load(open(map_file, encoding="utf-8"))["members"].items()}
    project = Project(path)
    i18n.ensure_languages(project)

    existing = [s for s in project.screens if s.name == SCREEN]
    page = existing[0] if existing else edit.clone_screen(project, project.screen("Home_Fill"), SCREEN)
    for slot in i18n.SLOTS:
        for entry in page.section.entries(f"wScreenDESCTextLen00{slot}"):
            entry.set_text(SCREEN)
    tabs.clear(project)
    for element in page.elements[::-1]:
        if element.name.startswith(("cl_", "nav_")):
            edit.delete_element(project, page, element.index)

    # templates, all from pages the project already has
    home = "Home_Fill"
    tpl_rect, tpl_text = find(project, home, "fl_process"), find(project, home, "fl_status_bar_txt1")
    tpl_num, tpl_ind = find(project, home, "fl_rate"), find(project, home, "fl_fill_mode")
    tpl_push, tpl_name = find(project, home, "fl_start"), find(project, home, "fl_silo_name")
    tpl_goto = find(project, home, "nav_home")
    tpl_entry = find(project, "Set_Parameter", "pr_1_1")
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

    def picture(key, box, back=PAGE):
        x, y, w, h = box
        item = edit.clone_element(project, tpl_rect, page, 0, 0, 10, 10, key)
        clear_links(item)
        frame.face(item, bank, key)
        frame.flat(item, back)
        for state in item.states:
            state.set("TransColor", bgr(back))
        frame.picture_rect(item, x, y, w, h)

    def text(name, box, texts, size=14, colour=INK, bold=False, align=LEFT, screen=None):
        x, y, w, h = box
        item = edit.clone_element(project, tpl_text, screen or page, x, y, w, h, name)
        style(item, size, colour, bold, align)
        i18n.words(item, texts, size)
        return item

    def number(name, box, member, size, digits, decimals=0, align=CENTRE, colour=INK):
        x, y, w, h = box
        item = edit.clone_element(project, tpl_num, page, x, y, w, h, name)
        clear_links(item)
        item.section.set("ReadVar", address[member])
        item.section.set("IntNum", digits)
        item.section.set("DotNum", decimals)
        style(item, size, colour, True, align)
        return item

    def indicator(name, box, member, states, size, align=LEFT, bold=False):
        x, y, w, h = box
        item = edit.clone_element(project, tpl_ind, page, x, y, w, h, name)
        clear_links(item)
        item.section.set("ReadVar", address[member])
        item.section.set("MemLen", 1)          # a word: the state is the value
        item.section.set("AutoResizeByText", 0)
        add_states(project, item, len(states))
        style(item, size, INK, bold, align)
        for n, (texts, colour) in enumerate(states):
            item.states[n].set("FontColor", bgr(colour))
            i18n.words(item, texts, size, state=n)
        return item

    def push(name, box, press, shown, faces, back, labels=None, size=14):
        """Momentary: writes the press bit, shows the state the PLC reports."""
        x, y, w, h = box
        item = edit.clone_element(project, tpl_push, page, x, y, w, h, name)
        clear_links(item)
        item.section.set("WriteVar", address[press])
        item.section.set("ReadVar", address[shown])
        item.section.set("Style", 3)
        for n, key in enumerate(faces):
            picture_on(item, n, bank, key, x, y, w, h, back)
        if labels:
            for n, (texts, colour, bold) in enumerate(labels):
                item.states[n].set("FontColor", bgr(colour))
                item.states[n].set("FontBold", 1 if bold else 0)
                item.states[n].set("FontAlign", CENTRE)
                i18n.words(item, texts, size, state=n)
        else:
            i18n.words(item, "")
        return item

    # --- header: sidebar on the new page, the tab row on every Home page ---------------
    for button in nav:
        edit.clone_element(project, button, page)
    tabs.place(project, bank)

    # --- artwork first -----------------------------------------------------------------
    for key, box in (("cl_status_bar", STATUS), ("cl_line_card", LINE_CARD), ("cl_silo_card", SILO_CARD),
                     ("cl_cond_card", COND_CARD), ("cl_set_card", SET_CARD), ("cl_progress_card", PROGRESS),
                     ("cl_run_card", RUN)):
        picture(key, box)

    # --- status bar -------------------------------------------------------------------------
    sx, sy = STATUS[0], STATUS[1]
    number("cl_code", (sx + 14, sy + 11, 42, 24), "Cl.MsgCode", 18, 2)
    indicator("cl_msg", (sx + 66, sy + 10, 408, 26), "Cl.Msg", MESSAGES, 14)
    text("cl_t_silo", (sx + 488, sy + 12, 52, 21), ("SILO", "BỒN", "SILO"), 14, MUTED)
    number("cl_silo", (sx + 530, sy + 11, 40, 24), "Cl.SiloNow", 18, 1)
    number("cl_time", (sx + 616, sy + 11, 44, 24), "Cl.TimeLeft", 18, 4, align=RIGHT)
    text("cl_t_s", (sx + 660, sy + 12, 14, 21), "s", 14, MUTED)

    # --- line -------------------------------------------------------------------------------
    lx, ly = LINE_CARD[0], LINE_CARD[1]
    text("cl_t_line", (lx + 52, ly + 17, 420, 21), ("LINE TO CLEAN", "ĐƯỜNG CẦN LÀM SẠCH", "LIGNE À NETTOYER"), 14, INK, True)
    for n, (box, texts) in enumerate(zip(SEG, LINES), 1):
        push(f"cl_line_{n}", box, f"Cl.BtnLine{n}", f"Cl.Line{n}", ("cl_seg_0", "cl_seg_1"), TILE,
             ((texts, MUTED, False), (texts, INK, True)))

    # --- silos ------------------------------------------------------------------------------
    cx, cy = SILO_CARD[0], SILO_CARD[1]
    text("cl_t_silos", (cx + 52, cy + 17, 420, 21), ("SILOS TO CLEAN", "BỒN CẦN LÀM SẠCH", "SILOS À NETTOYER"), 14, INK, True)
    for n, (x, y, w, h) in enumerate(CHIPS, 1):
        push(f"cl_chip_{n}", (x, y, w, h), f"Cl.BtnSel{n}", f"Cl.Sel{n}", ("cl_chip_0", "cl_chip_1"), WHITE)
        name = edit.clone_element(project, tpl_name, page, x + 12, y + 7, 156, 22, f"cl_name_{n}")
        clear_links(name)
        name.section.set("ReadVar", address[f"SiloName[{n}]"])
        style(name, 14, INK, True)
        indicator(f"cl_state_{n}", (x + 12, y + 30, 156, 20), f"Cl.SiloSt[{n}]", SILO_STATES, 12)

    # --- conditions -------------------------------------------------------------------------
    kx, ky = COND_CARD[0], COND_CARD[1]
    text("cl_t_cond", (kx + 52, ky + 17, 260, 21), ("CONDITIONS", "ĐIỀU KIỆN", "CONDITIONS"), 14, INK, True)
    indicator("cl_idle", (kx + 16, ky + 52, 298, 24), "Cl.IdleSt", IDLE_STATES, 14)
    indicator("cl_weight", (kx + 16, ky + 86, 298, 24), "Cl.WeightSt", WEIGHT_STATES, 14)
    text("cl_t_sum", (kx + 16, ky + 134, 150, 21), ("Selected silos", "Bồn đã chọn", "Silos choisis"), 14, MUTED)
    number("cl_sum", (kx + 166, ky + 130, 74, 28), "Cl.SumKg", 20, 4, 1, RIGHT, VALUE)
    text("cl_t_sum_of", (kx + 244, ky + 134, 74, 21), "/ 120 kg", 14, MUTED)

    # --- settings ---------------------------------------------------------------------------
    tx, ty = SET_CARD[0], SET_CARD[1]
    text("cl_t_set", (tx + 52, ty + 17, 260, 21), ("SETTINGS", "CÀI ĐẶT", "RÉGLAGES"), 14, INK, True)
    for n, ((texts, member, unit, low, high), (x, y, w, h)) in enumerate(zip(SETTINGS, ENTRY), 1):
        text(f"cl_t_set_{n}", (tx + 16, y + 7, x - tx - 24, 21), texts, 14, INK)
        item = edit.clone_element(project, tpl_entry, page, x, y, w, h, f"cl_set_{n}")
        clear_links(item)
        for key in ("ReadVar", "WriteVar"):
            item.section.set(key, address[member])
        for key, value in (("IntNum", 4), ("DotNum", 0), ("MinValue", f"{low}.0"), ("MaxValue", f"{high}.0")):
            item.section.set(key, value)
        style(item, 18, VALUE, True, CENTRE)
        text(f"cl_t_unit_{n}", (x + w + 4, y + 7, 18, 21), unit, 14, MUTED)

    # --- progress ---------------------------------------------------------------------------
    px, py = PROGRESS[0], PROGRESS[1]
    text("cl_t_progress", (px + 52, py + 17, 172, 21), ("PROGRESS", "TIẾN TRÌNH", "PROGRESSION"), 14, INK, True)
    number("cl_pct", (px + 14, py + 49, 150, 75), "Cl.Pct", 64, 3, align=RIGHT, colour=VALUE)
    text("cl_t_pct", (px + 168, py + 78, 34, 27), "%", 18, INK)

    # --- start / stop -----------------------------------------------------------------------
    rx, ry = RUN[0], RUN[1]
    text("cl_t_run", (rx + 52, ry + 17, 172, 21), ("CLEAN THE LINE", "LÀM SẠCH ỐNG", "NETTOYER"), 14, INK, True)
    # the word sits under the icon: an empty first line pushes it below the middle
    push("cl_start", DISC, "Cl.Press", "Cl.Running", ("cl_start_0", "cl_start_1"), WHITE,
         ((("\nSTART", "\nBẮT ĐẦU", "\nDÉMARRER"), fill.FACE_INK, True), (("\nSTOP", "\nDỪNG", "\nARRÊTER"), fill.FACE_INK, True)), 16)
    text("cl_t_now", (rx + 16, RUN_RULE + 22, 96, 21), ("Line", "Đường", "Ligne"), 14, MUTED)
    indicator("cl_now", (rx + 96, RUN_RULE + 20, 120, 24), "Cl.LineNow", NOW_STATES, 16, RIGHT, True)
    text("cl_t_step", (rx + 16, RUN_RULE + 62, 96, 21), ("Step", "Bước", "Étape"), 14, MUTED)
    number("cl_step", (rx + 136, RUN_RULE + 60, 30, 24), "Cl.StepNo", 16, 2, align=RIGHT, colour=VALUE)
    text("cl_t_of", (rx + 168, RUN_RULE + 62, 14, 21), "/", 14, MUTED, align=CENTRE)
    number("cl_steps", (rx + 184, RUN_RULE + 60, 30, 24), "Cl.StepTotal", 16, 2, align=LEFT, colour=VALUE)

    i18n.ensure_languages(project)
    print(project.save(path))
    print(f"{SCREEN} (id {page.id}): {len(page.elements)} elements; tabs on {', '.join(s.name for s in tabs.pages(project))}")


if __name__ == "__main__":
    if len(sys.argv) != 4:
        raise SystemExit(__doc__)
    main(*sys.argv[1:])
