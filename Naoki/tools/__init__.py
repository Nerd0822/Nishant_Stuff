"""The toolbelt: every category module wrapped for LangChain.

Implementations live next to this file (filesystem, system, desktop, web,
downloads, botcan, apps, gmail) plus memory.py one level up. Each function is re-exported as a
LangChain StructuredTool -- its docstring becomes the schema the model
sees, which is why Args: lines describe when to call, not just types.
25 tools total: small enough for a 9B local model to choose between
reliably.
"""

import functools
import sys
from pathlib import Path

if str(Path(__file__).resolve().parent.parent) not in sys.path:
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import memory as _mem  # noqa: E402
from langchain_core.tools import tool as lc_tool  # noqa: E402
from tools.desktop import copy_to_clipboard as _copy_clip  # noqa: E402
from tools.desktop import launch_file as _launch  # noqa: E402
from tools.botcan import botcan_run_recipe as _bot_recipe  # noqa: E402
from tools.botcan import botcan_scrape as _bot_scrape  # noqa: E402
from tools.botcan import botcan_screenshot as _bot_shot  # noqa: E402
from tools.apps import launch_app as _open_app  # noqa: E402
from tools.apps import list_apps as _ls_apps  # noqa: E402
from tools.apps import quit_app as _quit_app  # noqa: E402
from tools.gmail import gmail_read as _g_read  # noqa: E402
from tools.gmail import gmail_send as _g_send  # noqa: E402
from tools.downloads import download_file as _download  # noqa: E402
from tools.downloads import download_media as _media  # noqa: E402
from tools.downloads import fetch_webpage as _fetch  # noqa: E402
from tools.downloads import list_downloads as _ls_dl  # noqa: E402
from tools.filesystem import inspect_path as _inspect  # noqa: E402
from tools.filesystem import read_file as _read  # noqa: E402
from tools.filesystem import save_file as _save  # noqa: E402
from tools.filesystem import search_files as _search_files  # noqa: E402
from tools.filesystem import transfer_file as _transfer  # noqa: E402
from tools.system import host_info as _host  # noqa: E402
from tools.system import run_shell as _run  # noqa: E402
from tools.system import take_screenshot as _shot  # noqa: E402
from tools.web import search_web as _search_web  # noqa: E402

def _guard(fn):
    """Run a tool so failures come back as advice, not crashes.

    Without this, an exception either kills the turn or reaches the model
    as a bare traceback it can't act on. The wrapper converts it into a
    result that says what broke and what to do instead -- inspect first,
    narrow the scope, pick another tool. functools.wraps keeps the name
    and docstring intact so the model-facing schema is unchanged.
    """

    @functools.wraps(fn)
    def inner(*args, **kwargs):
        try:
            return fn(*args, **kwargs)
        except Exception as exc:
            return (
                f"Tool '{fn.__name__}' failed "
                f"({type(exc).__name__}: {exc}). Do NOT repeat the same "
                f"call. Change approach: verify paths with inspect_path "
                f"first, narrow the scope, or use a different tool."
            )

    return inner


read_file = lc_tool(_guard(_read))
save_file = lc_tool(_guard(_save))
inspect_path = lc_tool(_guard(_inspect))
search_files = lc_tool(_guard(_search_files))
transfer_file = lc_tool(_guard(_transfer))
run_shell = lc_tool(_guard(_run))
host_info = lc_tool(_guard(_host))
take_screenshot = lc_tool(_guard(_shot))
launch_file = lc_tool(_guard(_launch))
copy_to_clipboard = lc_tool(_guard(_copy_clip))
download_file = lc_tool(_guard(_download))
fetch_webpage = lc_tool(_guard(_fetch))
list_downloads = lc_tool(_guard(_ls_dl))
download_media = lc_tool(_guard(_media))
botcan_scrape = lc_tool(_guard(_bot_scrape))
botcan_run_recipe = lc_tool(_guard(_bot_recipe))
botcan_screenshot = lc_tool(_guard(_bot_shot))
launch_app = lc_tool(_guard(_open_app))
list_apps = lc_tool(_guard(_ls_apps))
quit_app = lc_tool(_guard(_quit_app))
gmail_read = lc_tool(_guard(_g_read))
gmail_send = lc_tool(_guard(_g_send))
save_note = lc_tool(_guard(_mem.save_note))
search_web = lc_tool(_guard(_search_web))


@lc_tool
def remember_fact(info: str) -> str:
    """Store one durable fact about the user (name, setup, preferences).

    Call the moment a fact appears, before answering. One fact per call.
    Never secrets, small talk, or anything temporary.

    Args:
        info: One short sentence, e.g. "User's editor is Helix".
    """
    return _mem.add_fact(info)


TOOLS = [
    read_file,
    save_file,
    inspect_path,
    search_files,
    transfer_file,
    run_shell,
    host_info,
    take_screenshot,
    launch_file,
    copy_to_clipboard,
    download_file,
    fetch_webpage,
    list_downloads,
    download_media,
    botcan_scrape,
    botcan_run_recipe,
    botcan_screenshot,
    launch_app,
    list_apps,
    quit_app,
    gmail_read,
    gmail_send,
    save_note,
    search_web,
    remember_fact,
]

__all__ = ["TOOLS"]
