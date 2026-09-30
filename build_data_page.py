"""Draw the Data page: the alarm list, and the alarms it lists.

Run:  python build_data_page.py <project.dpa> <asset folder>

Page    "Cảnh báo" title like the Settings page, "XÁC NHẬN TẤT CẢ" on the same
        row at the right, an Alarm History Table (11.1) under them over the
        width of the Settings tiles. Rows are coloured by alarm state: raised
        red, acknowledged amber, cleared white.
Alarms  the eight alarms of the old silo HMI (HMI_AThanh), in Vietnamese, one
        bit each. No PLC addresses exist yet: every alarm reads an internal bit
        $900.n, and ALARMS keeps the old PLC address to rebind to.

Re-runnable: elements named "dt_" are removed and the alarm list is rewritten.
"""

from __future__ import annotations

import sys
from pathlib import Path

from PIL import Image

import build_fill_page as fill
import build_silo_frame as frame
from build_calibration_page import HEAD, button_face
from build_fill_page import CARD_LINE, bind, clear_links, picture_on
from build_setting_page import LEFT, TITLE, title_face
from build_silo_frame import INK, MUTED, PAGE, WHITE, bgr
from dpa import edit, macro
from dpa.document import Entry
from dpa.model import Project

SCREEN = "Data"

# message, internal bit, address in the old silo PLC
ALARMS = (
    ("Quá tải động cơ hút chân không", "$900.0", "I0.1"),
    ("Áp suất chân không thấp", "$900.1", "M69.1"),
    ("Lỗi lưu lượng đường ống", "$900.2", "M70.1"),
    ("Bồn đầy", "$900.3", "M85.2"),
    ("Không đủ áp suất hút", "$900.4", "M85.1"),
    ("Khối lượng cao", "$900.5", "M71.7"),
    ("Khối lượng thấp", "$900.6", "M84.7"),
    ("Vượt giới hạn khối lượng", "$900.7", "MW76 = 1"),
)
ACK_ALL = "$910.0"   # alarm setting "Acknowledge all alarms"; the button pulses it

RAISED = "#FDE4E8"   # same light red as the DỪNG button's outer ring
ACKED = "#FFF3D9"
RIGHT_EDGE = 983     # right edge of the Settings tiles
ACK_BTN = (RIGHT_EDGE - 180, 105, 180, 40)   # centred on the title words (y 125)
TABLE = (LEFT, 180, RIGHT_EDGE - LEFT, 400)

# Alarm History Table columns: key number -> (title, width); the rest are hidden.
# 2 trigger time, 3 message, 5 recovery time, 6 count. Widths sum to TABLE width.
TIME_W, COUNT_W = 160, 76
COLUMNS = {
    2: ("Giờ xảy ra", TIME_W),
    3: ("Nội dung", TABLE[2] - 2 * TIME_W - COUNT_W),
    5: ("Giờ hết", TIME_W),
    6: ("Số lần", COUNT_W),
}
ORDER = (2, 3, 5, 6)


def write_alarms(project: Project) -> None:
    section = project.doc.first("Alarm")
    items = [i for i in section.items
             if not (isinstance(i, Entry) and i.key[:5] == b"Alarm" and i.key[-3:].isdigit()
                     or isinstance(i, Entry) and i.key.startswith(b"wMessageLen"))]
    section.items = items
    for key, value in (("ContinueAddr", 0), ("Hold", 1), ("AckAllAlarmVar", ACK_ALL)):
        if not section.set(key, value):
            raise KeyError(key)
    for n, (words, address, _) in enumerate(ALARMS, 1):
        message = Entry(f"wMessageLen{n:03d}-000".encode(), b"")
        message.set_text(words)
        section.items += [
            Entry(f"AlarmEnable{n:03d}".encode(), b"1"),
            Entry(f"AlarmVar{n:03d}".encode(), address.encode()),
            message,
            Entry(f"AlarmColor{n:03d}".encode(), str(bgr(INK)).encode()),
        ]


def main(path: str, asset_dir: str) -> None:
    project = Project(path)
    donor = Project(fill.DONOR)
    page = project.screen(SCREEN)
    for element in [e for e in page.elements if e.name.startswith("dt_")][::-1]:
        edit.delete_element(project, page, element.index)
    frame.prune_bank(project)
    write_alarms(project)

    folder = Path(asset_dir)
    folder.mkdir(parents=True, exist_ok=True)
    faces = {"dt_title": title_face("Cảnh báo")}
    for p in (0, 1):
        faces[f"dt_ack_{p}"] = button_face(ACK_BTN[2], ACK_BTN[3], "XÁC NHẬN TẤT CẢ", True, bool(p))
    bank = frame.Bank(project)
    for key, image in faces.items():
        file = folder / f"{key}.png"
        image.save(file)
        bank.add(key, file)
    bank.commit()

    tpl_rect = donor.element("scr_MainScreen", 1)
    tpl_push = donor.element("scr_Calibcation", 4)
    tpl_table = donor.element("ALARM", 3)

    _, _, w, h = bank.where["dt_title"]
    title = edit.clone_element(project, tpl_rect, page, 0, 0, 10, 10, "dt_title")
    clear_links(title)
    frame.face(title, bank, "dt_title")
    frame.flat(title, PAGE)
    for state in title.states:
        state.set("TransColor", bgr(PAGE))
    frame.picture_rect(title, TITLE[0], TITLE[1], w, h)

    x, y, w, h = ACK_BTN
    ack = edit.clone_element(project, tpl_push, page, x, y, w, h, "dt_ack")
    clear_links(ack)
    bind(ack, ACK_ALL)
    ack.section.set("Style", 3)
    macro.set_macro(ack.section, "ButtonOnMacroLen", None)
    macro.set_macro(ack.section, "ButtonOffMacroLen", None)
    for i in (0, 1):
        edit.set_state_text(ack, "", "", state=i)
        picture_on(ack, i, bank, f"dt_ack_{i}", x, y, w, h, PAGE)

    x, y, w, h = TABLE
    table = edit.clone_element(project, tpl_table, page, x, y, w, h, "dt_alarms")
    clear_links(table)
    s = table.section
    for key, value in (
        ("BorderColor", bgr(CARD_LINE)), ("GridColor", bgr(CARD_LINE)),
        ("RowColor", bgr(WHITE)), ("RowAlternateColor", bgr(WHITE)),
        ("RowSelectColor", bgr(HEAD)), ("RowHoverColor", bgr(HEAD)),
        ("RowColorMode", 1), ("RowActiveColor", bgr(RAISED)), ("RowAckColor", bgr(ACKED)),
        ("RowNormalColor", bgr(WHITE)), ("StateColor", bgr(INK)),
        ("TitleAlignment", 1), ("TitleBkgColor", bgr(HEAD)), ("TitleFontColor", bgr(MUTED)),
        ("ShowGridLine", 1), ("FieldFontSize", 14), ("Print", 0),
    ):
        if not s.set(key, value):
            raise KeyError(key)
    for n in range(1, 9):
        shown = n in COLUMNS
        s.set(f"EnableCol{n}", 1 if shown else 0)
        s.set(f"DisplayOrder{n}", ORDER.index(n) if shown else 60)
        if shown:
            words, width = COLUMNS[n]
            s.set(f"ColWidth{n}", width)
            for entry in s.entries(f"TitleTextLen{n}-000") + s.entries(f"TitleTextLen{n}-001"):
                entry.set_text(words)
    for state in table.states:
        state.set("BgColor", bgr(WHITE))
        state.set("FgColor", bgr(CARD_LINE))
        state.set("FontColor", bgr(INK))
        for slot in (0, 1):
            state.set(f"FontSize{slot}", 14)
        state.set("FontAlign", 33)

    print(project.save(path))
    print(f"{SCREEN}: {len(page.elements)} elements; {len(ALARMS)} alarms from $900.0, ack all {ACK_ALL}")


if __name__ == "__main__":
    if len(sys.argv) != 3:
        raise SystemExit(__doc__)
    main(*sys.argv[1:])
