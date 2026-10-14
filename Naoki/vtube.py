import asyncio
import os

import pyvts

from config import Base_dir

TOKEN_FILE = Base_dir / "vts_token.txt"

plugin_info = {
    "plugin_name": "Naoki",
    "developer": "Nishant",
    "authentication_token_path": TOKEN_FILE,
}


async def main():
    vts = pyvts.vts(plugin_info=plugin_info)
    await vts.connect()

    # First run: ask VTube Studio for a token (you click Allow in its popup).
    # Later runs: reuse the saved token so no popup is needed.
    if os.path.exists(TOKEN_FILE):
        await vts.read_token()
    else:
        await vts.request_authenticate_token()
        await vts.write_token()
    await vts.request_authenticate()

    # Ask which hotkeys the loaded model has.
    response = await vts.request(vts.vts_request.requestHotKeyList())
    hotkeys = response["data"]["availableHotkeys"]
    for h in hotkeys:
        print(h["name"], "->", h["hotkeyID"])

    # Trigger the first one as a test.
    if hotkeys:
        print("Triggering:", hotkeys[0]["name"])
        await vts.request(vts.vts_request.requestTriggerHotKey(hotkeys[0]["hotkeyID"]))
    else:
        print("This model has no hotkeys set up yet.")

    await vts.close()


asyncio.run(main())
