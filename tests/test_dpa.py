"""Checks that matter for a format we reverse engineered: nothing must drift.

The round-trip test is the important one - if parsing and re-serialising every
real project is byte-identical, then a targeted edit changes only what we meant
to change, and DIAScreen sees a file it wrote itself.
"""

from __future__ import annotations

import glob
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from dpa import codec
from dpa.document import Document
from dpa.model import Project

PROJECTS = sorted(glob.glob(r"C:\OTL\**\*.dpa", recursive=True))
pytestmark = pytest.mark.skipif(not PROJECTS, reason="no .dpa projects on this machine")


@pytest.mark.parametrize("path", PROJECTS, ids=lambda p: Path(p).name)
def test_round_trip_is_byte_identical(path):
    original = Path(path).read_bytes()
    decoded = codec.decode(original)
    doc = Document.parse(decoded.payload)
    assert doc.to_bytes() == decoded.payload
    assert codec.DpaFile(decoded.thumbnail, doc.to_bytes()).to_bytes() == original


@pytest.mark.parametrize("path", PROJECTS, ids=lambda p: Path(p).name)
def test_model_reads_screens(path):
    project = Project(path)
    assert project.screens, "every project has at least one screen"
    assert project.info()["panel"], "panel model is readable"
    for screen in project.screens:
        assert screen.name
        for element in screen.elements:
            assert element.kind


def test_edit_touches_only_the_edited_property(tmp_path):
    source = PROJECTS[0]
    project = Project(source)
    before = project.doc.to_bytes()

    screen = project.screens[0]
    element = screen.elements[0]
    element.section.set("X", element.rect[0] + 7)
    after = project.doc.to_bytes()

    assert after != before
    assert abs(len(after) - len(before)) <= 2  # only the number changed

    out = tmp_path / "edited.dpa"
    project.save(out)
    reloaded = Project(out)
    assert reloaded.screens[0].elements[0].rect[0] == element.rect[0]


def test_text_edit_keeps_the_byte_count_in_step(tmp_path):
    project = Project(PROJECTS[0])
    for screen in project.screens:
        for element in screen.elements:
            for state in element.states:
                entries = state.entries("wTextLen0") or state.entries("wTextLen")
                if entries and entries[0].blob:
                    entries[0].set_text("Kiểm tra")
                    assert entries[0].text == "Kiểm tra"
                    assert int(entries[0].value) == len(entries[0].blob)
                    out = tmp_path / "text.dpa"
                    project.save(out)
                    assert Project(out)  # reparses cleanly
                    return
    pytest.skip("no text state found")
