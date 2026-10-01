"""Build a trend-only test project from OTL-30A that runs on the HMI alone (no PLC).

Run:  python build_test_trend.py <OTL-30A source .dpa> <target .dpa>

Press CHAY TREND and the trend draws by itself; DUNG TREND stops it where it is;
XOA TREND empties it. Every PLC address the trend uses moves to internal memory,
keeping the same spacing (W4NNNN -> $(NNNN - 39500), B1/B2 -> $600.0/$600.1):

* history buffer 1: $560..$569 (was W40060..), curves read $561 BT, $562 ET, $563, $567
* run / stop: the buffer's "Enable active bit" $600.0 - ON samples, OFF stops (manual p.532)
* clear: the buffer's "Data Clearing" bit $554.0 (was W40054). It clears on the rising
  edge and the HMI leaves the flag at 1 (emulator 30/09), so the cycle macro drops it
  back to 0 - otherwise every second press would only reset the flag
* Control Block $550..$557, Status Block $521..$522

The screen's cycle macro (every 1 s) makes the data: while $600 == 1 a counter $580
steps 300 -> 0 and repeats, and BT / ET / the other curves are ramps derived from it.
Only statements whose bytes were read off DIAScreen's own blobs are written: assign
(0x1E), subtract (0x01), multiply (0x02), IF == / > (0x48 / 0x4A), ENDIF (0x5D).
"""

from __future__ import annotations

import re
import struct
import sys

from dpa import edit, macro
from dpa.model import Project

SCREEN = "PROGRAM MANUAL"
RUN_BIT, RUN_WORD = "$600.0", "$600"
CLEAR_WORD = "$554"
KEEP = {"Historical Trend Graph_077", "Scale_073",
        "Text_000", "Rectangle_002", "Text_056", "Rectangle_058", "Text_069",   # legend
        "Numeric Display_022", "Numeric Display_026", "Text_023", "Text_027",   # BT / ET readouts
        "Text_029", "Text_030"}
GREEN, RED, INK = 0x008000, 0x0000E0, 0   # BGR


def internal(value: bytes) -> bytes:
    """A Link2 address as its internal-memory stand-in."""
    text = value.decode("latin1")
    text = re.sub(r"\{Link2\}1@W4(\d{4})", lambda m: f"${int(m.group(1)) + 500}", text)
    text = re.sub(r"\{Link2\}1@B(\d+)$", lambda m: f"$600.{int(m.group(1)) - 1}", text)
    return text.encode("latin1")


# --- macro records, framed as DIAScreen writes them ---------------------------------
def _field(s: str) -> bytes:
    return struct.pack("<I", len(s)) + s.encode("latin1")


_TAIL = b"\x01" * 4 + b"\x00" * 8


def assign(dest: str, src: str) -> bytes:
    return b"\x25\x07\x03\x1e" + b"".join(map(_field, (f"{dest} = {src}", dest, src, "Var3", "Var4"))) + _TAIL


def arith(dest: str, a: str, op: str, b: str) -> bytes:
    code = {"-": 0x01, "*": 0x02}[op]
    return (b"\x04\x0f\x07" + bytes([code]) + b"".join(map(_field, (f"{dest} = {a} {op} {b}", dest, a, b, "Var4")))
            + _TAIL)


def if_(a: str, cmp: str, b: str) -> bytes:
    code = {"==": 0x48, ">": 0x4A}[cmp]
    return b"\x14\x0e\x03" + bytes([code]) + b"".join(map(_field, (f"IF {a} {cmp} {b}  ", a, b, "Var3", "Var4"))) + _TAIL


def endif() -> bytes:
    return b"\x00\x00\x00\x5d" + b"".join(map(_field, ("ENDIF", "Var1", "Var2", "Var3", "Var4"))) + _TAIL


def blob(*records: bytes) -> bytes:
    return b"\x02REV" + b"".join(r + b"\r\n" for r in records)


GENERATOR = blob(
    # The buffer clears on the rising edge of $554.0 and the HMI does NOT reset the flag
    # (emulator 30/09): left at 1, the next press would only write 0. Drop it here, and
    # restart the ramp so the cleared trend draws from 0 again.
    # Dropped in the same pass it was set, the HMI can miss the edge (1st of 2 presses
    # did not clear, emulator 30/09) - so hold it one full pass (1 s): $590 remembers.
    if_("$590", "==", "1"),
    assign(CLEAR_WORD, "0"),
    assign("$590", "0"),
    endif(),
    if_(CLEAR_WORD, "==", "1"),
    assign("$590", "1"),
    assign("$580", "300"),
    endif(),
    if_(RUN_WORD, "==", "1"),        # only while running: stopped, the data holds too
    arith("$580", "$580", "-", "1"),
    endif(),
    if_("$580", ">", "300"),         # 0 - 1 wraps to 65535: start the ramp again
    assign("$580", "300"),
    endif(),
    arith("$581", "300", "-", "$580"),   # 0 .. 300 rising
    arith("$561", "$581", "*", "8"),     # BT   0.0 .. 240.0
    arith("$582", "$580", "*", "6"),
    arith("$562", "2900", "-", "$582"),  # ET 110.0 .. 290.0
    arith("$563", "$581", "*", "1"),     # third curve 0.0 .. 30.0
    assign("$567", "700"),               # burner 70.0
)


def drop_screen(project: Project, screen) -> None:
    doc = project.doc
    start = doc.sections.index(screen.section)
    end = edit._last_section_index(doc, screen)
    del doc.sections[start:end + 1]
    project.screens.remove(screen)


def main(source: str, target: str) -> None:
    project = Project(source)
    for screen in [s for s in project.screens if s.name != SCREEN]:
        drop_screen(project, screen)
    page = project.screen(SCREEN)

    tpl_button = next(e for e in page.elements if e.name == "Multistate_005" and e.type_code == "1.5")
    tpl_text = next(e for e in page.elements if e.name == "Text_029")
    for element in page.elements[::-1]:
        if element.name not in KEEP:
            edit.delete_element(project, page, element.index)

    # every remaining PLC address - elements, history buffer, control block - goes internal
    for section in project.doc.sections:
        for item in section.items:
            if getattr(item, "value", None) and b"{Link2}" in item.value and getattr(item, "blob", None) is None:
                item.value = internal(item.value)

    def text(words, x, y, w, h, size=14):
        item = edit.clone_element(project, tpl_text, page, x, y, w, h, words)
        edit.set_state_text(item, words, words)
        for state in item.states:
            state.set("FontSize0", size)
            state.set("FontSize1", size)
            state.set("FontColor", INK)
        return item

    def button(name, address, x, y, words, bit=False):
        item = edit.clone_element(project, tpl_button, page, x, y, 180, 60, name)
        item.section.set("WriteVar", address)
        item.section.set("ReadVar", "None")
        # A bit address wants MemLen 0 (as every bit button DIAScreen wrote has);
        # left at the donor's word length 1, compile fails "Element address input error".
        item.section.set("MemLen", 0 if bit else 1)
        # the donor START button is interlocked on PLC bit B3 and runs an After macro
        item.section.set("InterLockVar", "None")
        for key in ("BeforeExecMacroLen", "AfterExecMacroLen"):
            macro.set_macro(item.section, key, None)
        for i, (label, colour) in enumerate(words):
            edit.set_state_text(item, label, label, state=i)
            item.states[i].set("FontColor", colour)
            item.states[i].set("FontSize0", 18)
            item.states[i].set("FontSize1", 18)
        return item

    text("ĐIỀU KHIỂN TREND", 835, 328, 180, 22)
    button("Trend run", RUN_BIT, 835, 355, (("CHẠY TREND", GREEN), ("DỪNG TREND", RED)), bit=True)
    button("Trend clear", CLEAR_WORD, 835, 425, (("XOÁ TREND", RED), ("ĐANG XOÁ", RED)))
    text("Mô phỏng nội - không cần PLC", 835, 495, 185, 20, 12)

    page.section.set("CycleMacroDelayTime", 1000)
    page.section.set("EnableCycleMacro", 1)
    macro.set_macro(page.section, "CycleMacroLen", GENERATOR)

    project.doc.first("History").set("SampleCycle01", 1000)
    application = project.doc.first("Application")
    for key in ("BackgroundMacroLen", "ClockMacroLen"):
        macro.set_macro(application, key, None)
    macro.set_macro(application, "InitialMacroLen", blob(assign("$580", "300")))

    print(project.save(target))
    left = sorted({i.value.decode("latin1") for s in project.doc.sections for i in s.items
                   if getattr(i, "value", None) and b"{Link2}" in i.value})
    print(f"{SCREEN}: {len(page.elements)} elements; PLC addresses left: {left}")
    print("\n".join(macro.statements(GENERATOR)))


if __name__ == "__main__":
    if len(sys.argv) != 3:
        raise SystemExit(__doc__)
    main(*sys.argv[1:])
