"""Copy a project's picture bank into another project, then clone an icon button.

Run:  python copy_picbank.py <target.dpa> <donor.dpa> <screen>

A Delta button and every icon are drawn from bitmaps in the project's picture
bank - the `[Picture]` section, one `Size=N` byte count followed by N bytes that
hold both the images and their names.  Elements refer to an image by name
(`Picture Name` + `PIB Name`), so a project with an empty bank draws cloned
buttons blank, which is why they came out white.

This copies the whole bank across and clones one icon button on top, to find out
whether a bank is portable between projects or whether it is tied to the project
that built it.
"""

from __future__ import annotations

import sys

from dpa import edit
from dpa.model import Project


def bank(project: Project):
    section = project.doc.first("Picture")
    if section is None:
        raise LookupError("project has no [Picture] section")
    entries = section.entries("Size")
    if not entries:
        raise LookupError("[Picture] has no Size entry")
    return section, entries[0]


def copy_bank(target: Project, donor: Project) -> dict:
    _, theirs = bank(donor)
    _, ours = bank(target)
    before = int(ours.value or 0)
    ours.blob = theirs.blob
    ours.value = theirs.value
    ours.blob_eol = theirs.blob_eol
    return {"bank_was": before, "bank_now": int(ours.value), "bytes": len(theirs.blob or b"")}


def icon_button(project: Project):
    """A button whose first state carries a picture - i.e. one that shows an icon."""
    for screen in project.screens:
        for element in screen.elements:
            if element.type_code.startswith("1.") and element.states:
                if element.states[0].as_dict().get("Picture Name"):
                    return element
    raise LookupError("donor has no icon button")


def main(target_path: str, donor_path: str, screen_name: str) -> None:
    target = Project(target_path)
    donor = Project(donor_path)

    print("bank:", copy_bank(target, donor))

    source = icon_button(donor)
    picture = source.states[0].as_dict()
    print(f"cloning {source.name!r} which wears {picture.get('PIB Name')}/{picture.get('Picture Name')}")

    screen = target.screen(screen_name)
    clone = edit.clone_element(target, source, screen, 40, 380, 160, 120, "probe_icon")
    for key in ("ReadVar", "WriteVar", "InterLockVar", "VisibleVar"):
        if clone.section.get(key) not in (None, "None"):
            clone.section.set(key, "None")

    print(target.save(target_path))


if __name__ == "__main__":
    if len(sys.argv) != 4:
        raise SystemExit(__doc__)
    main(*sys.argv[1:])
