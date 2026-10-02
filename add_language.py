"""Give a one-language DIAScreen project its second language.

Run:  python add_language.py <project.dpa> [name of language 1] [name of language 2]

The Silo HMI was drawn with one language (English). DIAScreen keeps, for every
language, its own font and text in each element state (`FontSize1`, `FontRatio1`,
`FontName1`, `wTextLen1`), its own description in each element and screen, and
one entry in [Multi-Language]. This adds language slot 1 everywhere as a copy
of slot 0, so nothing changes on screen until the second texts are written.

Slot 0 stays the default. Names follow HMI_AThanh: "Tiếng Anh", "Tiếng Việt".
Re-runnable: a project that already has slot 1 is left alone.
"""

from __future__ import annotations

import copy
import sys

from dpa.document import Entry
from dpa.model import Project

# (section, key of slot 0, key of slot 1). The copy goes right behind the last slot-0 key of its run.
STATE_KEYS = (("FontSize0", "FontSize1"), ("FontRatio0", "FontRatio1"), ("FontName0", "FontName1"), ("wTextLen0", "wTextLen1"))
SCREEN_KEYS = (("wScreenDESCTextLen000", "wScreenDESCTextLen001"), ("TitleTextFontName000", "TitleTextFontName001"),
               ("TitleTextFontSize000", "TitleTextFontSize001"), ("wTitleTextLen000", "wTitleTextLen001"))


def clone_after(section, pairs) -> int:
    """Insert slot-1 copies of the given keys after the last of their slot-0 keys."""
    have = {i.key for i in section.items if isinstance(i, Entry)}
    made = 0
    out = []
    pending = []
    wanted = {a.encode(): b.encode() for a, b in pairs}
    for item in section.items:
        if pending and not (isinstance(item, Entry) and item.key in wanted):
            out.extend(pending)
            pending = []
        out.append(item)
        if isinstance(item, Entry) and item.key in wanted and wanted[item.key] not in have:
            twin = copy.deepcopy(item)
            twin.key = wanted[item.key]
            pending.append(twin)
            made += 1
    out.extend(pending)
    section.items = out
    return made


def main(path: str, first: str = "Tiếng Anh", second: str = "Tiếng Việt") -> None:
    project = Project(path)
    doc = project.doc
    languages = doc.first("Multi-Language")
    if languages.entries("LanguageValue1"):
        print("the project already has a second language")
        return

    for entry in languages.entries("wLanguageNameLen0"):
        entry.set_text(first)
    block = []
    for item in languages.items:
        if isinstance(item, Entry) and item.key.endswith(b"0") and item.key != b"UseTextBankFont":
            twin = copy.deepcopy(item)
            twin.key = item.key[:-1] + b"1"
            if twin.key == b"wLanguageNameLen1":
                twin.set_text(second)
            if twin.key == b"LanguageValue1":
                twin.value = b"1"
            block.append(twin)
    languages.items += block

    counts = {"State": 0, "Element": 0, "Screen": 0, "Alarm": 0}
    for section in doc.sections:
        if section.name == "State":
            counts["State"] += clone_after(section, STATE_KEYS)
        elif section.name == "Element":
            counts["Element"] += clone_after(section, (("wDescTextLen0", "wDescTextLen1"),))
        elif section.name == "Screen":
            counts["Screen"] += clone_after(section, SCREEN_KEYS)
        elif section.name == "Alarm":
            pairs = [(i.key.decode(), i.key.decode()[:-3] + "001") for i in section.items
                     if isinstance(i, Entry) and i.key.startswith(b"wMessageLen") and i.key.endswith(b"-000")]
            counts["Alarm"] += clone_after(section, pairs)

    print(project.save(path))
    print("second language added:", counts)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        raise SystemExit(__doc__)
    main(*sys.argv[1:])
