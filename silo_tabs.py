"""The header tabs of the Silo HMI's Home pages: OVERVIEW, FILL, DISCHARGE, BLEND, CLEAN.

Every Home page carries the same row of Goto Screen buttons, its own lit. The
row is drawn here and nowhere else, so a page script that adds or redraws a
Home page calls clear() before it prunes the picture bank, adds faces() to the
bank and calls place() - and every Home page gets the same row again. A tab
whose page the project does not have yet is left out.

The words are the buttons' own text, three languages (silo_i18n).
"""

from __future__ import annotations

from PIL import Image

import build_silo_frame as frame
import silo_i18n as i18n
from build_silo_frame import INK, MUTED, bgr
from dpa import edit
from dpa.model import Project

# Five tabs between the logo (ends near x 176) and the user menu (starts at 834).
TAB_W, TAB_H, TAB_Y, TAB_GAP = 119, 52, 3, 4
TAB_LEFT = 196
TABS = (  # element name, screen, (English, Vietnamese, French)
    ("tab_overview", "Home_Overview", ("OVERVIEW", "TỔNG QUAN", "APERÇU")),
    ("tab_fill", "Home_Fill", ("FILL", "NẠP LIỆU", "REMPLIR")),
    ("tab_discharge", "Home_Discharge", ("DISCHARGE", "XẢ LIỆU", "VIDANGE")),
    ("tab_blend", "Home_Blend", ("BLEND", "PHỐI TRỘN", "MÉLANGE")),
    ("tab_clean", "Home_Clean", ("CLEAN", "LÀM SẠCH", "NETTOYAGE")),
)
CENTRE = 34


def pages(project: Project) -> list:
    """The Home pages this project has, in tab order."""
    have = {screen.name: screen for screen in project.screens}
    return [have[name] for _, name, _ in TABS if name in have]


def clear(project: Project) -> None:
    """Remove the tab row from every Home page."""
    for screen in pages(project):
        for element in screen.elements[::-1]:
            if element.name.startswith("tab_"):
                edit.delete_element(project, screen, element.index)


def faces() -> dict[str, Image.Image]:
    frame.TAB_W = TAB_W        # tab_face() reads the module's width
    return {"tab_on": frame.tab_face("", True), "tab_off": frame.tab_face("", False)}


def place(project: Project, bank: frame.Bank) -> None:
    """Draw the tab row on every Home page; the bank must hold faces()."""
    home = pages(project)
    template = next(e for e in project.screen("Home_Fill").elements if e.name == "nav_home")
    for screen in home:
        for slot, (name, target, texts) in enumerate(TABS):
            destination = next((s for s in home if s.name == target), None)
            if destination is None:
                continue
            lit = destination is screen
            x = TAB_LEFT + slot * (TAB_W + TAB_GAP)
            item = edit.clone_element(project, template, screen, x, TAB_Y, TAB_W, TAB_H, name)
            item.section.set("GoToScreenID", destination.id)
            for entry in item.section.entries("GoToScreenName"):
                entry.value = destination.name.encode("latin1")
            frame.face(item, bank, "tab_on" if lit else "tab_off")
            frame.flat(item)
            size = 18 if lit else 14
            for state in item.states:
                state.set("FontColor", bgr(INK if lit else MUTED))
                state.set("FontBold", 1 if lit else 0)
                state.set("FontAlign", CENTRE)
            i18n.words(item, texts, size, margin=12)
