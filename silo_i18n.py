"""Languages of the Silo HMI: English, Vietnamese, French - and words that fit.

DIAScreen keeps one text and one font per language in every element state
(`wTextLen0..2`, `FontSize0..2`, `FontName0..2`, `FontRatio0..2`), one
description per language in every element and screen, and the language list in
[Multi-Language]. `ensure_languages()` gives the whole project its slots (a new
slot starts as a copy of slot 0, so nothing moves on screen), `words()` writes
the three texts of one state and sizes each so it fits the element.

Slot order is fixed: 0 English (default), 1 Tiếng Việt, 2 Français. A Language
Change button (12.12) carries the slot number in `LangValue`.

Run:  python silo_i18n.py <project.dpa>      adds the slots, nothing else
"""

from __future__ import annotations

import copy
import sys
from pathlib import Path

from PIL import ImageFont

from dpa.document import Entry
from dpa.model import Project

LANGUAGES = ("English", "Tiếng Việt", "Français")
SLOTS = range(len(LANGUAGES))
FONTS = Path(r"C:\Windows\Fonts")
MIN_SIZE = 10

_STATE = ("FontSize", "FontRatio", "FontName", "wTextLen")
_SCREEN = ("wScreenDESCTextLen00", "TitleTextFontName00", "TitleTextFontSize00", "wTitleTextLen00")


def _clone_slots(section, stems, count: int) -> int:
    """After each run of slot-0 keys, add the missing copies for slots 1..count-1."""
    have = {i.key for i in section.items if isinstance(i, Entry)}
    zero = {(stem + "0").encode(): stem for stem in stems}
    out, pending, made = [], [], 0

    def flush():
        nonlocal pending, made
        for slot in range(1, count):
            for item in pending:
                key = (zero[item.key] + str(slot)).encode()
                if key not in have:
                    twin = copy.deepcopy(item)
                    twin.key = key
                    out.append(twin)
                    have.add(key)
                    made += 1
        pending = []

    last_slot_run = False
    for item in section.items:
        key = item.key if isinstance(item, Entry) else b""
        stem = next((s for s in stems if key.startswith(s.encode()) and key[len(s):].isdigit()), None)
        if stem is None:
            if last_slot_run:
                flush()
            last_slot_run = False
            out.append(item)
            continue
        last_slot_run = True
        out.append(item)
        if key in zero:
            pending.append(item)
    if last_slot_run:
        flush()
    section.items = out
    return made


def ensure_languages(project: Project) -> int:
    """Make every section carry all language slots. Returns how many keys were added."""
    doc = project.doc
    count = len(LANGUAGES)
    languages = doc.first("Multi-Language")
    made = 0
    for slot, name in enumerate(LANGUAGES):
        if not languages.entries(f"LanguageValue{slot}"):
            for item in [i for i in languages.items if isinstance(i, Entry) and i.key.endswith(b"0")
                         and i.key[:-1] + b"0" != b"UseTextBankFont0"]:
                twin = copy.deepcopy(item)
                twin.key = item.key[:-1] + str(slot).encode()
                if twin.key.startswith(b"LanguageValue"):
                    twin.value = str(slot).encode()
                languages.items.append(twin)
                made += 1
        for entry in languages.entries(f"wLanguageNameLen{slot}"):
            entry.set_text(name)
    for section in doc.sections:
        if section.name == "State":
            made += _clone_slots(section, _STATE, count)
        elif section.name == "Element":
            made += _clone_slots(section, ("wDescTextLen",), count)
        elif section.name == "Screen":
            made += _clone_slots(section, _SCREEN, count)
        elif section.name == "Alarm":
            stems = sorted({i.key.decode()[:-1] for i in section.items
                            if isinstance(i, Entry) and i.key.startswith(b"wMessageLen") and i.key.endswith(b"-000")})
            made += _clone_slots(section, stems, count)
    return made


def text_width(text: str, size: int, bold: bool) -> float:
    face = ImageFont.truetype(str(FONTS / ("arialbd.ttf" if bold else "arial.ttf")), size)
    return max(face.getlength(line) for line in text.split("\n"))


def fit(text: str, width: int, size: int, bold: bool, margin: int = 6) -> int:
    """The largest even size up to `size` at which the widest line fits the width."""
    size -= size % 2
    while size > MIN_SIZE and text_width(text, size, bold) > width - margin:
        size -= 2
    return size


def words(element, texts, size: int | None = None, state: int | None = None, width: int | None = None,
          margin: int = 6) -> None:
    """Write (English, Vietnamese, French) on one state - or on every state - and fit each.

    `size` is the size to aim for (default: what the state has in slot 0); a
    language whose words are too wide for the element gets a smaller one.
    Lines break at "\\n".
    """
    if isinstance(texts, str):
        texts = (texts,) * len(LANGUAGES)
    states = element.states if state is None else [element.states[state]]
    room = width if width is not None else element.section.get_int("Width", 0)
    for section in states:
        bold = section.get("FontBold") == "1"
        aim = size if size is not None else section.get_int("FontSize0", 16)
        for slot, text in zip(SLOTS, texts):
            for entry in section.entries(f"wTextLen{slot}"):
                entry.set_text(text.replace("\n", "\r\n"))
            section.set(f"FontName{slot}", "Arial")
            section.set(f"FontSize{slot}", fit(text, room, aim, bold, margin) if text.strip() else aim)


def describe(element, name: str) -> None:
    for slot in SLOTS:
        for entry in element.section.entries(f"wDescTextLen{slot}"):
            entry.set_text(name)


def main(path: str) -> None:
    project = Project(path)
    made = ensure_languages(project)
    print(project.save(path))
    print(f"languages: {', '.join(LANGUAGES)}; {made} keys added")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise SystemExit(__doc__)
    main(sys.argv[1])
