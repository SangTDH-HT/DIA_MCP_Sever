"""Put the pages of the Silo HMI drawn before 01/10/2026 into English, Vietnamese and French.

Run:  python translate_silo.py <project.dpa> <asset folder>

The Fill page was drawn in English, Discharge / Blend / Calibration / Parameter
in Vietnamese. This pass leaves the layout alone and gives every word its three
languages:

  labels      Text elements and indicator states are looked up in WORDS by
              what they say now (any of the three forms), rewritten in all
              three, and each language sized to fit. A label too narrow for
              its longest form is widened first, towards its free side.
  buttons     faces that had their words painted in (sidebar, START, mode
              switch, Y-002 buttons, calibration buttons, acknowledge) are
              redrawn without words; the words become the button's own text.
  alarm list  column titles of the Alarm History Table.

A label Sang rewrote by hand into something WORDS does not know is left as it
is and listed at the end. Re-runnable.
"""

from __future__ import annotations

import sys
from pathlib import Path

from PIL import Image, ImageDraw

import build_calibration_page as cal
import build_fill_page as fill
import build_home_pages as home
import build_silo_frame as frame
import silo_i18n as i18n
from build_fill_page import FIELD_LINE, TILE, picture_on, rounded
from build_silo_frame import INK, MUTED, NAV_INK, NAV_LABEL, PAGE, WHITE, bgr, icon, rgb
from dpa.document import Entry
from dpa.model import Project

# (English, Vietnamese, French), then any older wording still found in the file.
WORDS = (
    # --- Home pages
    ("Hopper", "Phễu", "Trémie"),
    ("FILLING RATE", "TỐC ĐỘ NẠP", "DÉBIT"),
    ("DISCHARGE RATE", "TỐC ĐỘ XẢ", "DÉBIT"),
    ("kg/m", "kg/p", "kg/m", "kg/min", "kg/ph"),
    ("CAPACITY LEFT", "SỨC CHỨA CÒN LẠI", "CAPACITÉ RESTANTE", "CAPACITY WEIGHT"),
    ("VACUUM", "ĐỘNG CƠ HÚT", "ASPIRATION", "VACCUM"),
    ("Pressure [kPa]", "Áp suất [kPa]", "Pression [kPa]"),
    ("FILL MODE", "CHẾ ĐỘ NẠP", "MODE"),
    ("COUNTDOWN", "ĐẾM NGƯỢC", "DÉCOMPTE"),
    ("STATUS", "TRẠNG THÁI", "ÉTAT"),
    ("SILO", "BỒN", "SILO"),
    ("CURRENT WEIGHT", "TRỌNG LƯỢNG HIỆN TẠI", "POIDS ACTUEL"),
    ("SELECT SILO", "CHỌN BỒN", "CHOISIR LE SILO"),
    ("SILO TO DISCHARGE", "CHỌN BỒN XẢ", "SILO À VIDER"),
    ("SELECT RECIPE", "CHỌN CÔNG THỨC", "CHOISIR LA RECETTE"),
    ("MODE", "CHẾ ĐỘ", "MODE"),
    ("PULSED", "NGẮT QUÃNG", "PULSÉ"),
    ("CONTINUOUS", "LIÊN TỤC", "CONTINU"),
    ("HOPPER", "PHỄU XẢ", "TRÉMIE"),
    ("HOPPER VALVE", "VAN XẢ PHỄU", "VANNE TRÉMIE"),
    ("DISCHARGE WEIGHT", "TRỌNG LƯỢNG XẢ", "POIDS À VIDER"),
    ("Alarms", "Cảnh báo", "Alarmes"),
    # --- Parameter page
    ("DISCHARGE SETTINGS", "CÀI ĐẶT XẢ LIỆU", "RÉGLAGES DE VIDANGE"),
    ("Silo valve opening delay", "Trễ mở van xả bồn", "Retard d'ouverture vanne silo"),
    ("Hopper valve open time", "Thời gian mở van xả phễu", "Durée d'ouverture vanne trémie"),
    ("Max suction time per batch", "Thời gian hút tối đa mỗi mẻ", "Aspiration max. par lot"),
    ("Silo change time", "Thời gian chuyển bồn", "Durée de changement de silo"),
    ("GHFV open – motor start delay", "Mở GHFV – trễ chạy động cơ", "GHFV ouverte – retard moteur"),
    ("Motor off – GHFV close delay", "Tắt động cơ – trễ đóng GHFV", "Moteur arrêté – retard GHFV"),
    ("FILL SETTINGS", "CÀI ĐẶT NẠP LIỆU", "RÉGLAGES DE REMPLISSAGE"),
    ("Pipe settling time", "Ổn định đường ống", "Stabilisation du tuyau"),
    ("Total fill time per batch", "Tổng thời gian nạp mỗi mẻ", "Durée totale par lot"),
    ("Pulsed fill – valve open", "Nạp ngắt quãng – van mở", "Pulsé – vanne ouverte"),
    ("Pulsed fill – pause", "Nạp ngắt quãng – nghỉ", "Pulsé – pause"),
    ("Silo change – hopper valve off", "Chuyển bồn – đóng van phễu", "Changement – vanne trémie",
     "Silo change – hopper valve closed", "Changement – vanne trémie fermée"),
    ("Silo valve closing delay", "Trễ đóng van bồn", "Retard de fermeture vanne silo"),
    ("GENERAL & SPEED", "CÀI ĐẶT CHUNG & TỐC ĐỘ", "GÉNÉRAL ET VITESSE"),
    ("Maximum weight", "Trọng lượng tối đa", "Poids maximal"),
    ("Pressure limit", "Giới hạn áp suất", "Limite de pression"),
    ("Pipe purge time", "Thời gian xả đường ống", "Durée de purge du tuyau"),
    ("Discharge / blend – drive speed", "Xả / phối trộn – tốc độ biến tần", "Vidange / mélange – vitesse"),
    # --- Calibration page
    ("CALIBRATION", "HIỆU CHỈNH", "ÉTALONNAGE"),
    ("Silo", "Chọn silo", "Silo"),
    ("Tare", "Trừ bì", "Tare"),
    ("Zero", "Zero", "Zéro"),
    ("Points stored", "Điểm đang chốt", "Points mémorisés"),
    ("Frames read", "Số khung đã đọc", "Trames lues"),
    ("Points", "Số điểm", "Nombre de points"),
    ("Calibration point", "Điểm hiệu chỉnh", "Point d'étalonnage"),
    ("Weight (kg)", "Trọng lượng (kg)", "Poids (kg)"),
    ("Status", "Trạng thái", "État"),
    ("4-CHANNEL MONITOR", "GIÁM SÁT 4 KÊNH", "SUIVI DES 4 VOIES"),
    ("Value", "Thông số", "Valeur"),
    ("Zero point (kg)", "Điểm không (kg)", "Point zéro (kg)"),
    ("Net weight (kg)", "Khối lượng tịnh (kg)", "Poids net (kg)"),
    ("Tared (kg)", "Đã trừ bì (kg)", "Taré (kg)"),
    ("SCALE PARAMETERS", "THAM SỐ CHỨC NĂNG", "PARAMÈTRES DE LA BALANCE"),
    ("Parameter", "Chức năng", "Paramètre"),
    ("Current", "Đang có", "Actuel"),
    ("New value", "Giá trị mới", "Nouvelle valeur"),
    ("Read", "Đọc về", "Lire"),
    ("Write", "Ghi xuống", "Écrire"),
    # --- About
    ("About", "Giới thiệu", "À propos"),
    ("Version", "Phiên bản", "Version"),
    ("Tax Code", "Mã số thuế", "N° fiscal"),
    ("Office", "Văn phòng", "Bureau"),
    ("Mobile", "Di động", "Mobile"),
)
SAME = {"SFV :", "SDV :", "GHFV", "kg", "s", "M-008", "M-009", "Y-002", "Dec.Time [s]", "CH1", "CH2", "CH3", "CH4",
        "I/O", "OTL Roaster", "SILO 6", "1.0.0", "Website", "Email"}   # said the same in every language
# A left-aligned label may grow to the right up to this width before its type shrinks instead.
MAX_WIDTH = {"Set_Parameter": 186, "Set_Calibration": 170}
# On these pages the row labels share one size per language: the size their longest label needs.
EVEN_SIZE = {"Set_Parameter": "pr_page_txt"}
TEXT_PAD = frame.TEXT_PAD

NAV = {"nav_home": ("house", ("HOME", "TRANG CHỦ", "ACCUEIL")),
       "nav_setting": ("settings", ("SETTING", "CÀI ĐẶT", "RÉGLAGES")),
       "nav_data": ("database", ("DATA", "DỮ LIỆU", "DONNÉES"))}
START = (("START", "BẮT ĐẦU", "DÉMARRER"), ("STOP", "DỪNG", "ARRÊTER"))
MODE = (("MANUAL", "THỦ CÔNG", "MANUEL"), ("AUTO", "TỰ ĐỘNG", "AUTO"))
VALVE = {"valve_man": ("hand", ("Manual", "Thủ công", "Manuel")),
         "valve_run": ("arrow-down-to-line", ("Discharge", "Xả liệu", "Vider"))}
CAL_BUTTONS = {"cal_tare": (("TARE", "TRỪ BÌ", "TARE"), True), "cal_tare_undo": (("UNDO", "BỎ", "ÔTER"), False),
               "cal_zero": (("ZERO", "ZERO", "ZÉRO"), True), "cal_zero_undo": (("UNDO", "BỎ", "ÔTER"), False),
               "cal_apply": (("CALIBRATE", "HIỆU CHỈNH", "ÉTALONNER"), True),
               "cal_cancel": (("CANCEL", "HỦY", "ANNULER"), False),
               "cal_read": (("READ", "ĐỌC", "LIRE"), False), "cal_write": (("WRITE", "GHI", "ÉCRIRE"), True),
               "dt_ack": (("ACKNOWLEDGE ALL", "XÁC NHẬN TẤT CẢ", "TOUT ACQUITTER"), True)}
ALARM_COLUMNS = {2: ("Raised", "Giờ xảy ra", "Début"), 3: ("Message", "Nội dung", "Message"),
                 5: ("Cleared", "Giờ hết", "Fin"), 6: ("Count", "Số lần", "Nombre")}


def lookup() -> dict[str, tuple[str, str, str]]:
    # English first, then Vietnamese and older wordings, French last: a French word
    # that is another label's English ("MODE") must not claim it.
    table = {}
    for pick in (lambda r: r[:1], lambda r: r[1:2] + r[3:], lambda r: r[2:3]):
        for row in WORDS:
            for form in pick(row):
                table.setdefault(form, row[:3])
    return table


def mode_face(auto: bool) -> Image.Image:
    """The mode switch without words: the active half raised, the other half shows its icon."""
    _, _, w, h = fill.MODE_BTN
    big = Image.new("RGBA", (w * 4, h * 4), rgb(WHITE) + (255,))
    d = ImageDraw.Draw(big)
    rounded(d, (0, 0, w, h), fill=TILE, outline=TILE, radius=8)
    half = w // 2
    rounded(d, (half + 4 if auto else 4, 4, half - 8, h - 8), fill=WHITE, outline=FIELD_LINE, radius=6)
    image = big.resize((w, h), Image.LANCZOS)
    idle = 0 if auto else 1
    image.alpha_composite(icon(("hand", "cog")[idle], 18, MUTED, px=1.5, cut=TILE), (idle * half + (half - 18) // 2, (h - 18) // 2))
    return image


def shifted(text: str, size: int, bold: bool, shift: float) -> str:
    """Centred words moved `shift` px sideways by spaces on the other side."""
    space = i18n.text_width(" " * 20, size, bold) / 20
    pad = " " * max(0, round(2 * abs(shift) / space))
    return text + pad if shift < 0 else pad + text


def widen(element, screen_name: str, texts, size: int, bold: bool) -> None:
    """Give a Text room for its longest language, on the side its alignment leaves free."""
    section = element.section
    x, width = section.get_int("X"), section.get_int("Width")
    need = round(max(i18n.text_width(t, size, bold) for t in texts)) + 2 * TEXT_PAD + 4
    align = element.states[0].get_int("FontAlign", 33)
    if align & 1:
        need = min(need, MAX_WIDTH.get(screen_name, 320))
    if need <= width:
        return
    if align & 4:
        return                    # a unit: what is to its left is the number it belongs to
    if align & 2:
        section.set("X", x - (need - width) // 2)
    section.set("Width", need)


def main(path: str, asset_dir: str) -> None:
    project = Project(path)
    i18n.ensure_languages(project)
    table = lookup()
    folder = Path(asset_dir)
    folder.mkdir(parents=True, exist_ok=True)

    # --- labels and indicator states ------------------------------------------------
    unknown = set()
    done = 0
    for screen in project.screens:
        rows = []
        for element in screen.elements:
            if element.type_code not in ("10.6", "2.1") or element.name.startswith(("cl_", "st_", "lg_", "ac_", "ln_", "fr_")):
                continue
            for n, state in enumerate(element.states):
                entries = state.entries("wTextLen0")
                now = entries[0].text.strip() if entries else ""
                if not now or now in SAME or any(ch.isdigit() for ch in now[:1]) or "://" in now or "@" in now:
                    continue
                if now not in table:
                    if screen.name == "Set_About":
                        continue          # company name, address, numbers
                    unknown.add(f"{screen.name}/{element.name}: {now}")
                    continue
                texts = table[now]
                size = max(state.get_int(f"FontSize{slot}", 0) for slot in i18n.SLOTS)
                if element.type_code == "10.6":
                    widen(element, screen.name, texts, size, state.get("FontBold") == "1")
                i18n.words(element, texts, size, state=n, margin=2 * TEXT_PAD)
                done += 1
                if element.name.startswith(EVEN_SIZE.get(screen.name, "-")) and state.get("FontBold") != "1":
                    rows.append(state)
            if element.type_code == "2.1":       # an indicator keeps one size through its states
                for slot in i18n.SLOTS:
                    smallest = min(state.get_int(f"FontSize{slot}", 16) for state in element.states)
                    for state in element.states:
                        state.set(f"FontSize{slot}", smallest)
        for slot in i18n.SLOTS:
            if rows:
                smallest = min(state.get_int(f"FontSize{slot}") for state in rows)
                for state in rows:
                    state.set(f"FontSize{slot}", smallest)

    # --- alarm table column titles --------------------------------------------------
    for screen in project.screens:
        for element in screen.elements:
            if element.type_code != "11.1":
                continue
            section = element.section
            for column, texts in ALARM_COLUMNS.items():
                first = section.entries(f"TitleTextLen{column}-000")
                if not first:
                    continue
                at = section.items.index(first[0])
                for slot, text in zip(i18n.SLOTS, texts):
                    found = section.entries(f"TitleTextLen{column}-00{slot}")
                    if not found:
                        twin = Entry(f"TitleTextLen{column}-00{slot}".encode(), b"")
                        section.items.insert(at + slot, twin)
                        found = [twin]
                    found[0].set_text(text)

    # --- button faces without words --------------------------------------------------
    frame.TAB_W = 138
    faces = {}
    for name, (glyph, _) in NAV.items():
        for lit in (False, True):
            faces[f"{name}_{int(lit)}"] = frame.nav_face(glyph, "", lit)
    for p in (0, 1):
        faces[f"start_{p}"] = fill.start_face(bool(p), "", "")
        faces[f"mode_{p}"] = mode_face(bool(p))
        for key, (glyph, _) in VALVE.items():
            faces[f"{key}_{p}"] = home.valve_button_face("", glyph, bool(p))
    buttons = {}
    for screen in project.screens:
        for element in screen.elements:
            if element.name in CAL_BUTTONS:
                buttons[element.name] = (screen, element)
                _, _, w, h = element.rect
                for p in (0, 1):
                    faces[f"{element.name}_{p}"] = cal.button_face(w, h, "", CAL_BUTTONS[element.name][1], bool(p))
    frame.prune_bank(project)
    bank = frame.Bank(project)
    for key, image in faces.items():
        image.save(folder / f"i18n_{key}.png")
        bank.add(key, folder / f"i18n_{key}.png")
    bank.commit()

    def style(state, colour, bold, align=34):
        state.set("FontColor", bgr(colour))
        state.set("FontBold", 1 if bold else 0)
        state.set("FontAlign", align)

    for screen in project.screens:
        lit_nav = ("nav_home" if screen.name.startswith("Home_") else
                   "nav_data" if screen.name == "Data" else "nav_setting")
        for element in screen.elements:
            name = element.name
            x, y, w, h = element.rect
            if name in NAV:
                lit = name == lit_nav
                frame.face(element, bank, f"{name}_{int(lit)}")
                frame.flat(element)
                style(element.states[0], WHITE if lit else NAV_LABEL, lit)
                # the word sits under the icon: empty lines above push it below the middle
                i18n.words(element, tuple("\n\n\n" + t for t in NAV[name][1]), 12, margin=4)
            elif name in ("fl_start", "dc_start", "bl_start"):
                for p in (0, 1):
                    picture_on(element, p, bank, f"start_{p}", x, y, w, h, WHITE)
                    style(element.states[p], fill.FACE_INK, True)
                    i18n.words(element, tuple("\n" + t for t in START[p]), 16, state=p, width=84)
            elif name in ("fl_mode", "dc_mode", "bl_mode"):
                for p in (0, 1):
                    picture_on(element, p, bank, f"mode_{p}", x, y, w, h, WHITE)
                    state = element.states[p]
                    style(state, INK, True)
                    # one word, in the raised half: a quarter of the width left or right of centre
                    for slot, text in zip(i18n.SLOTS, MODE[p]):
                        size = i18n.fit(text, w // 2 - 8, 14, True, 10)
                        for entry in state.entries(f"wTextLen{slot}"):
                            entry.set_text(shifted(text, size, True, (w / 4) * (1 if p else -1)))
                        state.set(f"FontName{slot}", "Arial")
                        state.set(f"FontSize{slot}", size)
            elif name[3:] in VALVE and name[:3] in ("dc_", "bl_"):
                for p in (0, 1):
                    picture_on(element, p, bank, f"{name[3:]}_{p}", x, y, w, h, WHITE)
                    style(element.states[p], INK, bool(p))
                    i18n.words(element, tuple("\n\n" + t for t in VALVE[name[3:]][1]), 12, state=p, margin=4)
            elif name in CAL_BUTTONS:
                texts, dark = CAL_BUTTONS[name]
                for p in (0, 1):
                    picture_on(element, p, bank, f"{name}_{p}", x, y, w, h, WHITE if name != "dt_ack" else PAGE)
                    style(element.states[p], WHITE if dark else INK, True)
                    i18n.words(element, texts, 14, state=p, margin=10)

    i18n.ensure_languages(project)
    print(project.save(path))
    print(f"{done} labels in three languages, {len(faces)} button faces redrawn without words")
    for line in sorted(unknown):
        print("left as it is:", line)


if __name__ == "__main__":
    if len(sys.argv) != 3:
        raise SystemExit(__doc__)
    main(*sys.argv[1:])
