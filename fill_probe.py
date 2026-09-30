"""Put a strip of rectangles on a screen, each with a different fill recipe.

Run:  python fill_probe.py <project.dpa> <screen> [donor.dpa]

All of them ask for the same colour, #60656B. Whichever swatch actually shows
that colour, flat, tells us which of `FillStyle` / `Style` / `GradFillMode`
controls a Delta rectangle's fill - guessing from the key names has not worked.
Each swatch is labelled with the recipe it carries.
"""

from __future__ import annotations

import sys

from dpa import edit
from dpa.model import Project


def bgr(hex_rgb: str) -> int:
    value = int(hex_rgb.lstrip("#"), 16)
    r, g, b = (value >> 16) & 0xFF, (value >> 8) & 0xFF, value & 0xFF
    return (b << 16) | (g << 8) | r


TARGET = bgr("#60656B")
WHITE = bgr("#FFFFFF")
BLACK = 0

# (FillStyle, Style, GradFillMode)
RECIPES = [
    (0, 0, 0),
    (1, 0, 0),
    (1, 1, 0),
    (1, 0, 1),
    (0, 1, 0),
    (1, 3, 0),
]


def find(project: Project, code: str):
    for screen in project.screens:
        for element in screen.elements:
            if element.type_code == code:
                return element
    raise LookupError(code)


def main(path: str, screen_name: str, donor_path: str = "") -> None:
    project = Project(path)
    donor = Project(donor_path) if donor_path else project
    target = project.screen(screen_name)
    rect = find(donor, "10.2")
    text = find(donor, "10.6")

    x, y, w, h = 40, 60, 140, 90
    for i, (fill_style, style, grad) in enumerate(RECIPES):
        left = x + i * (w + 16)
        swatch = edit.clone_element(project, rect, target, left, y, w, h, f"probe_{i}")
        swatch.section.set("FillStyle", fill_style)
        swatch.section.set("Style", style)
        swatch.section.set("GradFillMode", grad)
        swatch.section.set("GradFillStartColor", TARGET)
        swatch.section.set("GradFillEndColor", TARGET)
        swatch.section.set("BorderColor", TARGET)
        swatch.section.set("RoundRadius", 0)
        for state in swatch.states:
            state.set("BgColor", TARGET)
            state.set("FgColor", TARGET)

        caption = edit.clone_element(project, text, target, left, y + h + 6, w, 24, f"probe_lbl_{i}")
        edit.set_state_text(caption, f"F{fill_style} S{style} G{grad}", f"F{fill_style} S{style} G{grad}")
        for state in caption.states:
            state.set("FontColor", BLACK)
            state.set("FontSize", 12)

    print(project.save(path))
    print(f"{target.name}: {len(RECIPES)} swatches, all asking for #60656B")


if __name__ == "__main__":
    if not 3 <= len(sys.argv) <= 4:
        raise SystemExit(__doc__)
    main(*sys.argv[1:])
