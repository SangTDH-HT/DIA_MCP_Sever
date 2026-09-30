"""Make the open DIAScreen window pick up a file this server just rewrote.

DIAScreen reads a .dpa fully when it opens and then releases the handle, so the
file can be rewritten underneath it.  What it will not do is notice.  Its main
window is MFC (`Afx:` class) and it accepts a path on the command line, so the
reload is: close that document window, then launch the editor on the file again.

The one thing that must never happen is losing work the user typed into the
editor.  So this module never answers a dialog.  If closing raises a prompt -
DIAScreen asking whether to save - it backs off, leaves the prompt on screen,
and reports that the user has unsaved changes to deal with first.
"""

from __future__ import annotations

import ctypes
import subprocess
import time
import winreg
from ctypes import wintypes
from pathlib import Path

user32 = ctypes.WinDLL("user32", use_last_error=True)

WM_CLOSE = 0x0010
DIALOG_CLASS = "#32770"
_ENUM_PROC = ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)


def editor_path() -> Path:
    """Where DIAScreen lives, from the .dpa shell association."""
    with winreg.OpenKey(winreg.HKEY_CLASSES_ROOT, r"dpafile\shell\open\command") as key:
        command, _ = winreg.QueryValueEx(key, None)
    return Path(command.split('"')[1])


def _windows() -> list[tuple[int, int, str, str]]:
    """Every visible top-level window as (hwnd, pid, class, title)."""
    found: list[tuple[int, int, str, str]] = []

    def collect(hwnd, _):
        if not user32.IsWindowVisible(hwnd):
            return True
        pid = wintypes.DWORD()
        user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
        title = ctypes.create_unicode_buffer(512)
        user32.GetWindowTextW(hwnd, title, 512)
        klass = ctypes.create_unicode_buffer(256)
        user32.GetClassNameW(hwnd, klass, 256)
        found.append((hwnd, pid.value, klass.value, title.value))
        return True

    user32.EnumWindows(_ENUM_PROC(collect), 0)
    return found


def find_document(path: str | Path) -> list[tuple[int, int, str]]:
    """DIAScreen windows showing this project, as (hwnd, pid, title).

    DIAScreen titles its window `DIAScreen - <project> - [1 - <screen>]`, so the
    file stem is what identifies the document.
    """
    stem = Path(path).stem.lower()
    return [
        (hwnd, pid, title)
        for hwnd, pid, klass, title in _windows()
        if klass.startswith("Afx:") and title.startswith("DIAScreen") and stem in title.lower()
    ]


def _dialogs(pid: int) -> list[str]:
    return [title for _, owner, klass, title in _windows() if owner == pid and klass == DIALOG_CLASS]


def reload_document(path: str | Path, timeout: float = 6.0) -> dict:
    """Close the window showing this project, then reopen it on the new bytes.

    Returns what happened. If DIAScreen puts up a dialog - which means the user
    has edits in the editor that closing would throw away - nothing is answered
    and nothing is reopened; the caller is told to go and look at the screen.
    """
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(path)

    open_windows = find_document(path)
    if not open_windows:
        subprocess.Popen([str(editor_path()), str(path)])
        return {"action": "opened", "detail": "no window had this project open"}

    hwnd, pid, title = open_windows[0]

    # Look BEFORE knocking. A close request cannot be taken back: once DIAScreen
    # raises its save prompt the user is holding a question they did not ask
    # for, and answering "save" writes the editor's older copy over the file
    # that was just written.
    standing = _dialogs(pid)
    if standing:
        return {
            "action": "refused",
            "detail": "DIAScreen has a dialog open - close it, then reload again",
            "dialog": standing,
            "window": title,
        }

    # There is no way to know whether the user has edits pending, and DIAScreen
    # only raises its save prompt after it has been asked to close. If that
    # prompt is answered "save", the editor writes its older copy over the file.
    # So keep a snapshot: a wrong click then costs nothing.
    snapshot = path.read_bytes()

    user32.PostMessageW(hwnd, WM_CLOSE, 0, 0)

    prompted = False
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        time.sleep(0.25)
        prompted = prompted or bool(_dialogs(pid))
        if find_document(path):
            continue

        restored = False
        if path.read_bytes() != snapshot:
            path.write_bytes(snapshot)
            restored = True
        subprocess.Popen([str(editor_path()), str(path)])
        return {
            "action": "reloaded",
            "window": title,
            "asked_to_save": prompted,
            "restored": restored,
            "detail": (
                "the editor saved its older copy on the way out; the file was put "
                "back the way it was written" if restored else ""
            ),
        }

    return {
        "action": "timed_out",
        "detail": (
            f"window still open after {timeout:g}s"
            + (" - a save prompt is waiting on screen; answer NO" if prompted else "")
        ),
        "asked_to_save": prompted,
        "window": title,
    }


IDYES = 6
BM_CLICK = 0x00F5


def close_document(path: str | Path, timeout: float = 15.0) -> dict:
    """Close DIAScreen's window on this project, keeping whatever the user typed.

    This is the step to run BEFORE rewriting the file, not after: if DIAScreen
    asks whether to save, the answer is Yes, so the user's edits land on disk
    and the rewrite then builds on top of them. Nothing is lost either way.

    A dialog that is already standing (a properties box, say) means the user is
    mid-edit, so the window is left alone.
    """
    path = Path(path)
    open_windows = find_document(path)
    if not open_windows:
        return {"action": "none", "detail": "no window had this project open"}
    hwnd, pid, title = open_windows[0]

    standing = _dialogs(pid)
    if standing:
        return {"action": "refused", "detail": "DIAScreen has a dialog open - the user is mid-edit", "dialog": standing}

    user32.PostMessageW(hwnd, WM_CLOSE, 0, 0)
    saved = False
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        time.sleep(0.25)
        if not find_document(path):
            return {"action": "closed", "window": title, "saved_user_edits": saved}
        for dialog, owner, klass, _ in _windows():
            if owner != pid or klass != DIALOG_CLASS:
                continue
            yes = user32.GetDlgItem(dialog, IDYES)
            if not yes:
                return {"action": "stuck", "detail": "a dialog without a Yes button is open - look at the screen"}
            user32.SendMessageW(yes, BM_CLICK, 0, 0)
            saved = True
    return {"action": "timed_out", "window": title, "saved_user_edits": saved}


def open_document(path: str | Path) -> dict:
    """Launch DIAScreen on the file, unless a window already shows it."""
    path = Path(path)
    if find_document(path):
        return {"action": "none", "detail": "already open"}
    subprocess.Popen([str(editor_path()), str(path)])
    return {"action": "opened"}
