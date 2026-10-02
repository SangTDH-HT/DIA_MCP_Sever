"""Close a page's list popups when the operator leaves the page.

Run:  python close_popups_on_leave.py <project.dpa>

The pick lists of the Silo HMI (silo, recipe, calibration point...) are
sub-screens a field button opens with `OPENSCREEN n`. A sub-screen floats over
whatever page is shown, and a Goto Screen button does not close it - its
`CloseScreen=1` only closes a sub-screen the button itself sits on (seen on the
emulator 01/10/2026: the silo list stayed open over Settings). Screen Open /
Close macros may not use CLOSESUBSCREEN (error -83), so the closing goes on the
buttons: every Goto Screen on a page gets a Before Execute macro that closes
the popups this page can open. The frame's own Goto buttons (logo, user) are on
every page, so they close every popup of the project.

The popups of a page are read from its buttons' `OPENSCREEN n` macros, nothing
is listed here. Re-runnable, and it has to run last: every page script draws
its Goto buttons again without the macro.
"""

from __future__ import annotations

import sys

from dpa import macro
from dpa.model import Project

KEY = "BeforeExecMacroLen"
OPEN_KEYS = ("ButtonOnMacroLen", "ButtonOffMacroLen", "BeforeExecMacroLen", "AfterExecMacroLen")


def popups_of(screen) -> list[int]:
    """Sub-screen numbers the buttons of this page open, in the order met."""
    found = []
    for element in screen.elements:
        for key in OPEN_KEYS:
            for entry in element.section.entries(key):
                for line in macro.statements(entry.blob or b""):
                    if line.startswith("OPENSCREEN"):
                        number = int(line.replace("(", " ").replace(")", " ").split()[1])
                        if number not in found:
                            found.append(number)
    return found


def main(path: str) -> None:
    project = Project(path)
    # OPENSCREEN also opens whole pages (sign out -> Login): only a sub-screen is a popup to close
    floating = {screen.id for screen in project.screens if screen.section.get("IsSubScreen") == "1"}
    by_page = {screen.id: [n for n in popups_of(screen) if n in floating] for screen in project.screens}
    everything = sorted({n for numbers in by_page.values() for n in numbers})
    bases = {screen.section.get_int("BaseScreenID", 0) for screen in project.screens} - {0}

    changed = 0
    for screen in project.screens:
        numbers = everything if screen.id in bases else by_page[screen.id]
        blob = macro.program(*(macro.screen_statement(macro.CLOSESUBSCREEN, n) for n in numbers)) if numbers else None
        for element in screen.elements:
            if element.type_code != "1.10":
                continue
            entry = element.section.entries(KEY)[0]
            if (entry.blob or None) != blob:
                macro.set_macro(element.section, KEY, blob)
                changed += 1
        if numbers:
            print(f"{screen.name}: Goto buttons close {numbers}")
    print(project.save(path) if changed else "nothing to change")
    print(f"{changed} buttons changed")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise SystemExit(__doc__)
    main(sys.argv[1])
