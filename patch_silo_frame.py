"""Apply the borderless faces and the three divider rules to HMI_Silo.dpa as DIAScreen saved it.

Run:  python patch_silo_frame.py <in.dpa> <out.dpa>
"""
import sys

from build_silo_frame import HEADER_H, SIDEBAR_W, flat, rule
from dpa import edit
from dpa.model import Project

FOOTER_Y = 536  # top of the Operation mode / START bar

project = Project(sys.argv[1])
base = project.screen("Khung_Chung")
for screen in project.screens:
    for element in screen.elements:
        if element.name in ("fr_rule_header", "fr_rule_sidebar", "fr_rule_footer"):
            continue
        if element.type_code in ("1.10", "10.2"):
            flat(element)

header = next(e for e in base.elements if e.name == "fr_rule_header")
sidebar = next(e for e in base.elements if e.name == "fr_rule_sidebar")
for element, (x, y, w, h) in ((header, (0, HEADER_H, 1024, 1)), (sidebar, (SIDEBAR_W, HEADER_H, 1, 600 - HEADER_H))):
    for key, value in zip(("X", "Y", "Width", "Height"), (x, y, w, h)):
        element.section.set(key, value)
    rule(element)
if not any(e.name == "fr_rule_footer" for e in base.elements):
    footer = edit.clone_element(project, header, base, SIDEBAR_W, FOOTER_Y, 1024 - SIDEBAR_W, 1, "fr_rule_footer")
    rule(footer)
print(project.save(sys.argv[2]))
