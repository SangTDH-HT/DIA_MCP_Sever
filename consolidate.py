"""Put everything into one project and tidy the experiments away.

Run:  python consolidate.py <project.dpa> <icon folder> <donor.dpa> [more donors]

Working files piled up while the format was being worked out - probe swatches,
spare copies, a screen full of colour tests. This rebuilds the real project from
scratch: a clean home screen with two navigation buttons, the login screen, and
the roasting screen, and nothing else.
"""

from __future__ import annotations

import sys
from pathlib import Path

import add_nav
import build_roast
from dpa import edit
from dpa.model import Project


def strip_screen(project: Project, name: str) -> int:
    screen = project.screen(name)
    removed = len(screen.elements)
    while screen.elements:
        edit.delete_element(project, screen, len(screen.elements) - 1)
    return removed


def drop_element(project: Project, screen_name: str, element_name: str) -> bool:
    screen = project.screen(screen_name)
    for i, element in enumerate(screen.elements):
        if element.name == element_name:
            edit.delete_element(project, screen, i)
            return True
    return False


def main(path: str, icon_dir: str, *donors: str) -> None:
    project = Project(path)

    # 1. clear the home screen of every experiment left on it
    print(f"Screen_1: removed {strip_screen(project, 'Screen_1')} test elements")

    # 2. the login screen keeps only what can be true - no standing error line
    if drop_element(project, "scr_Login", "lg_error"):
        print("scr_Login: removed the error label that was always showing")

    # 3. drop an earlier roasting screen so rebuilding cannot leave two
    for screen in list(project.screens):
        if screen.name == "scr_Roast":
            strip_screen(project, "scr_Roast")
            for section in ([screen.section] + [s for s in project.doc.sections
                                                if s.name == "AuxKeyElement"][:0]):
                project.doc.sections.remove(section)
            project.screens.remove(screen)
            print("removed the previous scr_Roast")

    # 4. empty the picture bank - rebuilding appends icons, so a second run
    #    would otherwise stack a duplicate set and shift every index
    entry = project.doc.first("Picture").entries("Size")[0]
    entry.blob, entry.value, entry.blob_eol = None, b"0", True
    print("picture bank cleared before rebuild")

    project.save(path)

    # 5. rebuild the roasting screen, then wire navigation
    build_roast.main(path, icon_dir, *donors)
    add_nav.main(path, *donors)

    # 6. the home screen needs a way into the login screen too
    project = Project(path)
    donor_projects = [Project(d) for d in donors]
    home = project.screen("Screen_1")
    add_nav.nav_button(project, donor_projects, home, project.screen("scr_Login"),
                       80, 480, 300, 72, "ĐĂNG NHẬP", "LOG IN", "nav_login")
    project.save(path)

    final = Project(path)
    for screen in final.screens:
        print(f"   {screen.id}  {screen.name:12} {len(screen.elements)} elements")


if __name__ == "__main__":
    if len(sys.argv) < 4:
        raise SystemExit(__doc__)
    main(*sys.argv[1:])
