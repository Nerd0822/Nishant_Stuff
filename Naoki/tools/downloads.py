"""Download anything from the web: files, pages, and online media.

Jarvis-equivalent fetch suite. All network I/O is stdlib urllib except
download_media, which shells out to yt-dlp when it is installed. Every
function takes plain strings and returns a short human-readable summary
the model can act on -- no exceptions escape (tools/__init__.py's guard
turns them into retry advice anyway).
"""

import html
import os
import re
import shutil
import subprocess
import time
import urllib.parse
import urllib.request
from datetime import datetime
from pathlib import Path

from config import DOWNLOAD_DIR, DOWNLOAD_MAX_BYTES, DOWNLOAD_TIMEOUT

from ._common import _truncate

_HEADERS = {"User-Agent": "NaokiAssistant/0.1 (local desktop assistant)"}
_CHUNK = 64 * 1024

# Fallback extension when the URL has no filename and the server gives no
# Content-Disposition. Covers the common Jarvis cases (docs, images, zips).
_CONTENT_EXT = {
    "application/pdf": ".pdf",
    "application/zip": ".zip",
    "application/x-tar": ".tar",
    "application/gzip": ".gz",
    "application/json": ".json",
    "application/octet-stream": "",
    "text/plain": ".txt",
    "text/html": ".html",
    "text/csv": ".csv",
    "image/jpeg": ".jpg",
    "image/png": ".png",
    "image/gif": ".gif",
    "image/webp": ".webp",
    "image/svg+xml": ".svg",
    "audio/mpeg": ".mp3",
    "audio/ogg": ".ogg",
    "video/mp4": ".mp4",
}


def _human_size(n: int) -> str:
    if n < 1024:
        return f"{n} B"
    for unit in ("KB", "MB", "GB"):
        n /= 1024.0
        if n < 1024:
            return f"{n:.1f} {unit}"
    return f"{n:.1f} TB"


def _check_url(url: str) -> urllib.parse.ParseResult:
    parts = urllib.parse.urlparse(url.strip())
    if parts.scheme not in ("http", "https") or not parts.netloc:
        raise ValueError(
            f"only http(s) URLs can be downloaded, got '{url}' -- "
            "paste the full link starting with http:// or https://"
        )
    return parts


def _safe_filename(name: str) -> str:
    name = os.path.basename(name.strip().replace("\\", "/"))
    name = re.sub(r"[^A-Za-z0-9._\-+() \[\]]+", "_", name).strip("._ ")
    return name[:150] or "download"


def _filename_from_response(url: str, response) -> str:
    # 1. Server-declared name wins (handles ?download=1 style links).
    disposition = response.headers.get("Content-Disposition", "")
    match = re.search(r"filename\*\s*=\s*UTF-8''([^;]+)", disposition, re.I)
    if not match:
        match = re.search(r'filename\s*=\s*"([^"]+)"', disposition)
    if not match:
        match = re.search(r"filename\s*=\s*([^;\s]+)", disposition)
    if match:
        candidate = _safe_filename(urllib.parse.unquote(match.group(1)))
        if candidate:
            return candidate
    # 2. Last URL path segment.
    candidate = _safe_filename(
        urllib.parse.unquote(urllib.parse.urlparse(url).path.rsplit("/", 1)[-1])
    )
    if candidate and "." in candidate:
        return candidate
    # 3. Synthesize from content type + timestamp.
    content_type = (response.headers.get("Content-Type", "").split(";")[0].strip().lower())
    ext = _CONTENT_EXT.get(content_type, "")
    if candidate:
        return candidate + ext if ext and not candidate.endswith(ext) else candidate
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    host = _safe_filename(urllib.parse.urlparse(url).netloc.replace(":", "_"))
    return f"download-{host}-{stamp}{ext}"


def _unique_path(directory: Path, filename: str) -> Path:
    dest = directory / filename
    if not dest.exists():
        return dest
    stem, suffix = dest.stem, dest.suffix
    counter = 1
    while True:
        counter += 1
        candidate = directory / f"{stem} ({counter}){suffix}"
        if not candidate.exists():
            return candidate


def download_file(
    url: str, filename: str = "", directory: str = ""
) -> str:
    """Download a file from the web to this machine. The Jarvis download.

    Use for direct links to documents, images, PDFs, ZIPs, installers --
    anything search_web finds that the user wants saved. Streams to disk
    (no memory blowups), infers a filename when none is given, and never
    overwrites: clashes become "name (2).ext". Returns the saved path --
    pass it to launch_file to open it for the user.

    Args:
        url: Full http(s) link to the file.
        filename: Optional name to save as, e.g. "report.pdf". Empty
            means infer from the server or URL.
        directory: Optional absolute folder to save into. Empty means
            the standard downloads folder (~/Downloads/naoki).
    """
    parts = _check_url(url)
    _ = parts
    dest_dir = Path(directory) if directory else DOWNLOAD_DIR
    dest_dir.mkdir(parents=True, exist_ok=True)
    if not dest_dir.is_dir():
        raise NotADirectoryError(f"not a directory: {dest_dir}")

    request = urllib.request.Request(url, headers=_HEADERS)
    with urllib.request.urlopen(request, timeout=DOWNLOAD_TIMEOUT) as response:
        declared = int(response.headers.get("Content-Length", "0") or 0)
        if declared and declared > DOWNLOAD_MAX_BYTES:
            raise ValueError(
                f"file is {_human_size(declared)} -- over the "
                f"{_human_size(DOWNLOAD_MAX_BYTES)} limit, refusing"
            )
        name = _safe_filename(filename) if filename else _filename_from_response(url, response)
        dest = _unique_path(dest_dir, name)
        content_type = response.headers.get("Content-Type", "").split(";")[0].strip()

        total = 0
        with open(dest, "wb") as f:
            while True:
                chunk = response.read(_CHUNK)
                if not chunk:
                    break
                total += len(chunk)
                if total > DOWNLOAD_MAX_BYTES:
                    f.close()
                    dest.unlink(missing_ok=True)
                    raise ValueError(
                        f"download exceeded {_human_size(DOWNLOAD_MAX_BYTES)} "
                        "limit, partial file deleted"
                    )
                f.write(chunk)

    detail = f"downloaded {_human_size(total)} to {dest}"
    if content_type:
        detail += f" ({content_type})"
    return detail + ". Open it with launch_file to show the user."


def fetch_webpage(url: str) -> str:
    """Read a web page as plain text: title plus visible content.

    Use after search_web to actually read a hit, or whenever the user
    pastes a link and asks what's on it. Strips navigation/scripts to
    article text. If the link is a file (PDF/ZIP/image), says so --
    call download_file for those instead.

    Args:
        url: Full http(s) link of the page to read.
    """
    _check_url(url)
    request = urllib.request.Request(url, headers=_HEADERS)
    with urllib.request.urlopen(request, timeout=30) as response:
        content_type = response.headers.get("Content-Type", "").split(";")[0].strip().lower()
        if content_type and not (
            content_type.startswith("text/") or "html" in content_type or "xml" in content_type
        ):
            return (
                f"{url} is a {content_type or 'non-text'} file, not a page -- "
                "use download_file to save it instead"
            )
        raw = response.read(2 * 1024 * 1024)  # 2 MB cap: pages never need more
        charset = response.headers.get_content_charset() or "utf-8"
        page = raw.decode(charset, "replace")

    title_match = re.search(r"<title[^>]*>(.*?)</title>", page, re.DOTALL | re.I)
    title = ""
    if title_match:
        title = html.unescape(re.sub(r"\s+", " ", re.sub(r"<[^>]+>", "", title_match.group(1)))).strip()
    text = re.sub(r"(?is)<(script|style|nav|footer|noscript)[^>]*>.*?</\1>", " ", page)
    text = re.sub(r"<[^>]+>", " ", text)
    text = html.unescape(text)
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n\s*\n+", "\n\n", text).strip()
    if not text:
        return f"{url} has no readable text (empty page or image-only)"
    head = f"{title}\nSource: {url}\n\n" if title else f"Source: {url}\n\n"
    return _truncate(head + text, 8000)


def list_downloads() -> str:
    """List files Naoki has downloaded (newest first, with sizes).

    No arguments. Call when the user asks "where is my file" or "what
    did you download" -- then open their pick with launch_file.
    """
    DOWNLOAD_DIR.mkdir(parents=True, exist_ok=True)
    entries = sorted(
        (p for p in DOWNLOAD_DIR.iterdir() if p.is_file()),
        key=lambda p: p.stat().st_mtime,
        reverse=True,
    )
    if not entries:
        return f"no downloads yet -- they land in {DOWNLOAD_DIR}"
    lines = []
    for entry in entries[:50]:
        stat = entry.stat()
        modified = datetime.fromtimestamp(stat.st_mtime).strftime("%Y-%m-%d %H:%M")
        lines.append(f"{entry.name} -- {_human_size(stat.st_size)}, {modified}\n  {entry}")
    if len(entries) > 50:
        lines.append(f"... and {len(entries) - 50} more in {DOWNLOAD_DIR}")
    return _truncate("\n".join(lines))


def download_media(url: str, kind: str = "audio", account: bool = False) -> str:
    """Download a YouTube (or SoundCloud/Vimeo/etc) track or video.

    Needs the free yt-dlp tool on this machine; if it is missing the
    result says exactly how to install it. Audio saves as MP3, video as
    MP4, both into the downloads folder. Never overwrites existing files.

    Args:
        url: Full http(s) link to the video/track/page.
        kind: "audio" for MP3 sound, "video" for MP4 picture+sound.
        account: True when the link is personal -- Watch Later, private
            playlists, "my subscriptions". Reads the login cookies from
            ~/.config/naoki/youtube-cookies.txt (export once with a
            "cookies.txt" browser addon, chmod 600). Without that file
            it says how to create it. Public links leave this False.
    """
    if kind not in ("audio", "video"):
        raise ValueError(f"kind must be 'audio' or 'video', got '{kind}'")
    _check_url(url)
    DOWNLOAD_DIR.mkdir(parents=True, exist_ok=True)

    import importlib.util

    has_module = importlib.util.find_spec("yt_dlp") is not None
    binary = shutil.which("yt-dlp") or shutil.which("yt_dlp")
    if not has_module and not binary:
        return (
            "yt-dlp is not installed, so media downloads are unavailable. "
            "Install it once with: uv pip install yt-dlp  "
            "(or: pip install yt-dlp), then ask again."
        )

    template = str(DOWNLOAD_DIR / "%(title)s [%(id)s].%(ext)s")
    before = {p.name for p in DOWNLOAD_DIR.iterdir()}
    cookie_note = ""
    cookie_file = Path.home() / ".config" / "naoki" / "youtube-cookies.txt"
    use_cookies = False
    if account:
        if not cookie_file.is_file():
            return (
                "account downloads need your YouTube login cookies once: in "
                "Firefox install the 'Get cookies.txt LOCALLY' addon, export "
                "cookies for youtube.com, save as "
                f"{cookie_file} (then `chmod 600 {cookie_file}`), and ask again. "
                "Public links don't need this -- retry with account=False."
            )
        use_cookies = True
        cookie_note = " (using your YouTube login)"

    if binary:
        command = [binary, "-o", template, "--no-playlist", "--no-warnings"]
        if use_cookies:
            command += ["--cookies", str(cookie_file)]
        command += (
            ["-x", "--audio-format", "mp3"] if kind == "audio"
            else ["-f", "bv*+ba/b", "--merge-output-format", "mp4"]
        )
        command.append(url)
        try:
            result = subprocess.run(
                command, capture_output=True, text=True, timeout=600
            )
        except subprocess.TimeoutExpired:
            return "media download timed out after 10 minutes -- try a shorter video"
        if result.returncode != 0:
            tail = (result.stderr or result.stdout).strip().splitlines()
            reason = " ".join(tail[-3:])[:500] if tail else "unknown error"
            return f"Tool 'download_media' failed (yt-dlp: {reason}). Do NOT repeat the same call."
    else:
        import yt_dlp  # type: ignore

        options: dict = {
            "outtmpl": template,
            "noplaylist": True,
            "quiet": True,
            "no_warnings": True,
        }
        if use_cookies:
            options["cookiefile"] = str(cookie_file)
            cookie_note = " (using your YouTube login)"
        if kind == "audio":
            options.update(
                {
                    "format": "bestaudio/best",
                    "postprocessors": [
                        {"key": "FFmpegExtractAudio", "preferredcodec": "mp3"}
                    ],
                }
            )
        else:
            options.update({"format": "bv*+ba/b", "merge_output_format": "mp4"})
        started = time.monotonic()
        try:
            with yt_dlp.YoutubeDL(options) as ydl:
                ydl.download([url])
        except Exception as exc:
            return (
                f"Tool 'download_media' failed ({type(exc).__name__}: {exc}). "
                "Do NOT repeat the same call."
            )
        _ = started

    after = sorted(
        (DOWNLOAD_DIR / name for name in ({p.name for p in DOWNLOAD_DIR.iterdir()} - before)),
        key=lambda p: p.stat().st_size if p.is_file() else 0,
        reverse=True,
    )
    media = [p for p in after if p.is_file()]
    if not media:
        return f"yt-dlp finished but no new file appeared in {DOWNLOAD_DIR}"
    biggest = max(media, key=lambda p: p.stat().st_size)
    return (
        f"downloaded {kind}{cookie_note} {_human_size(biggest.stat().st_size)} "
        f"to {biggest}. Open it with launch_file to show the user."
    )
