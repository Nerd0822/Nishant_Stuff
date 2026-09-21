"""Launch and list desktop apps by friendly name.

Linux scatters apps across /usr/share/applications and
~/.local/share/applications as .desktop files with cryptic binary names
(firefox, org.kde.dolphin...). These tools let the model work the way the
user talks ("open Spotify", "is VLC installed") instead of guessing
binaries. Launching is detached: the app outlives the tool call, exactly
like clicking its icon. This only OPENS apps -- driving clicks and typing
inside them needs a Wayland automation daemon this box doesn't have.
"""

import configparser
import difflib
import os
import shutil
import signal
import subprocess
from pathlib import Path

_APP_DIRS = [
    Path.home() / ".local" / "share" / "applications",
    Path("/usr/share/applications"),
]

_LAUNCHERS = ("gtk-launch", "gio")


def _read_desktop(path: Path) -> dict | None:
    """Parse one .desktop file; None when it isn't a launchable app."""
    parser = configparser.ConfigParser(interpolation=None)
    try:
        parser.read(path, encoding="utf-8")
        entry = parser["Desktop Entry"]
    except Exception:
        return None
    if entry.get("Type", "Application") != "Application":
        return None
    if entry.get("NoDisplay", "false").lower() == "true":
        return None
    if entry.get("Hidden", "false").lower() == "true":
        return None
    if entry.get("Terminal", "false").lower() == "true":
        return None  # TUI assistant: terminal apps would hijack nothing useful
    name = entry.get("Name", "").strip()
    if not name or not entry.get("Exec", "").strip():
        return None
    return {
        "id": path.stem,  # what gtk-launch wants
        "name": name,
        "comment": entry.get("Comment", "").strip(),
        "exec": entry.get("Exec", "").split()[0],
    }


def _all_apps() -> list[dict]:
    """Every launchable app, local overrides winning over system ones."""
    apps: dict[str, dict] = {}
    for directory in reversed(_APP_DIRS):  # system first, local overwrites
        if not directory.is_dir():
            continue
        for path in directory.glob("*.desktop"):
            info = _read_desktop(path)
            if info:
                apps[info["id"]] = info
    return sorted(apps.values(), key=lambda a: a["name"].lower())


def _match(apps: list[dict], name: str) -> tuple[dict | None, list[str]]:
    """Best app for `name`, plus suggestions when nothing matches."""
    want = name.strip().lower()
    for app in apps:
        if app["id"].lower() == want or app["name"].lower() == want:
            return app, []
    containing = [a for a in apps if want in a["name"].lower()]
    if len(containing) == 1:
        return containing[0], []
    if containing:
        picks = sorted({a["name"] for a in containing})[:6]
        return None, [f"several match '{name}': {', '.join(picks)} -- be specific"]
    close = difflib.get_close_matches(
        name, [a["name"] for a in apps], n=3, cutoff=0.6
    )
    hint = f" -- did you mean: {', '.join(close)}?" if close else ""
    return None, [f"no app named '{name}'{hint} -- use list_apps to browse"]


def _launcher() -> str | None:
    return next((b for b in _LAUNCHERS if shutil.which(b)), None)


def list_apps(query: str = "") -> str:
    """List installed graphical apps, optionally filtered by name.

    Use when the user says "open X" and you're unsure of the exact name,
    or asks what's installed ("do I have VLC?"). Returns friendly names
    with their launch IDs -- pass the name to launch_app.

    Args:
        query: Filter text, e.g. "music" or "vlc". Empty lists everything
            (long -- prefer a query).
    """
    from ._common import _truncate

    apps = _all_apps()
    if not apps:
        return "no applications found in ~/.local/share/applications or /usr/share/applications"
    want = query.strip().lower()
    if want:
        apps = [
            a
            for a in apps
            if want in a["name"].lower()
            or want in a["id"].lower()
            or want in a["comment"].lower()
        ]
        if not apps:
            return f"no installed app matches '{query}'"
    lines = [f"{a['name']}  (id: {a['id']})" for a in apps[:60]]
    if len(apps) > 60:
        lines.append(f"... and {len(apps) - 60} more -- narrow with a query")
    summary = f"{len(apps)} installed apps"
    if want:
        summary += f" matching '{query}'"
    return _truncate(summary + ":\n" + "\n".join(lines))


def launch_app(name: str) -> str:
    """Open a desktop app by its friendly name, e.g. "Firefox".

    Use whenever the user says "open/launch/start X". The app opens
    detached (like clicking its icon) and the tool returns at once --
    it does NOT report what the app shows; call take_screenshot to see
    it. Files still go through launch_file, which picks the right app
    for a document.

    Args:
        name: App name as the user said it, e.g. "calculator", "Spotify".
    """
    apps = _all_apps()
    app, hints = _match(apps, name)
    if app is None:
        return hints[0]
    tool = _launcher()
    if tool is None:
        return "no launcher found (need gtk-launch or gio) -- cannot open apps"
    try:
        if tool == "gtk-launch":
            subprocess.Popen(
                ["gtk-launch", app["id"]],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                start_new_session=True,
                env={**os.environ, "DISPLAY": os.environ.get("DISPLAY", ":0")},
            )
        else:
            desktop_file = next(
                (
                    d / f"{app['id']}.desktop"
                    for d in _APP_DIRS
                    if (d / f"{app['id']}.desktop").is_file()
                ),
                None,
            )
            subprocess.Popen(
                ["gio", "open", str(desktop_file)],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                start_new_session=True,
            )
    except OSError as exc:
        return f"could not start {app['name']} ({exc})"
    return (
        f"opened {app['name']}. To see what it shows, call take_screenshot; "
        "to open a document in it instead, use launch_file with the file path."
    )


def quit_app(name: str) -> str:
    """Quit a running app by name (asks it to close, never force-kills).

    Use only when the user explicitly says "close/quit X". Sends SIGTERM
    to the app's main binary -- unsaved work may prompt, which Naoki
    cannot answer, so prefer asking the user to close things themselves
    unless they clearly said to do it.

    Args:
        name: App name, e.g. "Firefox". Matched against running processes
            via the app's own binary from its .desktop entry.
    """
    apps = _all_apps()
    app, hints = _match(apps, name)
    if app is None:
        return hints[0]
    binary = Path(app["exec"]).name
    result = subprocess.run(
        ["pgrep", "-x", binary], capture_output=True, text=True, timeout=10
    )
    pids = result.stdout.split()
    if not pids:
        return f"{app['name']} is not running (no '{binary}' process)"
    killed = 0
    for pid in pids:
        try:
            os.kill(int(pid), signal.SIGTERM)
            killed += 1
        except (OSError, ValueError):
            pass
    return f"asked {app['name']} to quit ({killed} process{'es' if killed != 1 else ''} signalled)"
