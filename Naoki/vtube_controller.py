"""Small sync-friendly bridge between Naoki and VTube Studio.

VTube Studio is async-only (pyvts), the agent's REPL is sync. We keep one
short-lived connection per trigger: auth (token once), list hotkeys, fire the
one whose name matches the emotion, close. Cost ~1s per turn -- fine for v1;
swap in a long-lived async worker later if it gets annoying.

Emotion is detected from the reply text with a tiny keyword classifier so we
do not have to change the LLM's system prompt at all.
"""

import asyncio

from config import Base_dir
import pyvts

TOKEN_FILE = Base_dir / "vts_token.txt"

PLUGIN_INFO = {
    "plugin_name": "Naoki",
    "developer": "Nishant",
    "authentication_token_path": TOKEN_FILE,
}

# keyword -> emotion -> matched against hotkey NAME substrings. Authors must
# name their VTube Studio hotkeys to contain one of these words, e.g.
# "expression_happy", "nod", "thinking".
EMOTION_KEYWORDS = {
    "happy": ["happy", "smile", "smiling", "laugh", "joy", "great", "glad", "yay"],
    "sad": ["sad", "sorry", "unhappy", "down", "upset", "cry", "bummer"],
    "angry": ["angry", "mad", "annoyed", "frustrated", "furious"],
    "surprised": ["surprise", "surprised", "wow", "unexpected", "shock"],
    "nod": ["nod", "yes", "agree", "sure", "right"],
    "thinking": ["think", "thinking", "hmm", "consider", "interesting"],
}


def _classify(text):
    low = (text or "").lower()
    for emotion, keys in EMOTION_KEYWORDS.items():
        if any(k in low for k in keys):
            return emotion
    return None


async def _trigger(emotion):
    vts = pyvts.vts(plugin_info=PLUGIN_INFO)
    await vts.connect()
    try:
        if TOKEN_FILE.exists():
            await vts.read_token()
        else:
            await vts.request_authenticate_token()
            await vts.write_token()
        await vts.request_authenticate()

        resp = await vts.request(vts.vts_request.requestHotKeyList())
        hotkeys = (resp or {}).get("data", {}).get("availableHotkeys", [])

        candidate = None
        for hotkey in hotkeys:
            if emotion in hotkey.get("name", "").lower():
                candidate = hotkey
                break
        if candidate is None and hotkeys:
            candidate = hotkeys[0]

        if candidate:
            await vts.request(vts.vts_request.requestTriggerHotKey(candidate["hotkeyID"]))
        return candidate.get("name") if candidate else ""
    finally:
        await vts.close()


def fire_for_reply(text):
    """Return (did_fire, detail_or_none). Never raises."""
    emotion = _classify(text)
    if emotion is None:
        return False, "no emotion matched"
    try:
        name = asyncio.run(_trigger(emotion))
        return True, f"{emotion} -> {name or 'first hotkey'}"
    except Exception as e:
        return False, f"VTS error: {type(e).__name__}: {e}"


def _list_hotkeys():
    async def run():
        vts = pyvts.vts(plugin_info=PLUGIN_INFO)
        await vts.connect()
        if TOKEN_FILE.exists():
            await vts.read_token()
        else:
            await vts.request_authenticate_token()
            await vts.write_token()
        await vts.request_authenticate()
        resp = await vts.request(vts.vts_request.requestHotKeyList())
        hotkeys = (resp or {}).get("data", {}).get("availableHotkeys", [])
        for h in hotkeys:
            print(f"  {h.get('name')!r} -> {h.get('hotkeyID')}")
        await vts.close()
    asyncio.run(run())


if __name__ == "__main__":
    import sys

    word = (sys.argv[1] if len(sys.argv) > 1 else "cycle").lower()

    # A word optionally passed on the CLI: map it to an emotion and fire one
    # hotkey so you can test a single target directly.
    if word not in ("cycle", "list", "all"):
        ok, detail = fire_for_reply(word)
        print("did_fire:", ok, "| detail:", detail)
        sys.exit(0)

    # list/cycle/all: print every available hotkey, trigger each one with a
    # pause, so you can watch which animation you can actually see on the model.
    async def run_cycle():
        vts = pyvts.vts(plugin_info=PLUGIN_INFO)
        await vts.connect()
        if TOKEN_FILE.exists():
            await vts.read_token()
        else:
            await vts.request_authenticate_token()
            await vts.write_token()
        await vts.request_authenticate()
        resp = await vts.request(vts.vts_request.requestHotKeyList())
        hotkeys = (resp or {}).get("data", {}).get("availableHotkeys", [])
        print("Available hotkeys:")
        for h in hotkeys:
            print(f"  {h.get('name')!r} -> {h.get('hotkeyID')}")
        print()
        for i, h in enumerate(hotkeys, 1):
            print(f"[{i}/{len(hotkeys)}] Firing {h.get('name')!r} ...")
            try:
                await vts.request(vts.vts_request.requestTriggerHotKey(h["hotkeyID"]))
                print("   -> VTS replied OK; watch the model for 2s")
            except Exception as e:
                print("   -> ERROR:", type(e).__name__, e)
            await asyncio.sleep(2)
        await vts.close()
        print("done")

    asyncio.run(run_cycle())
