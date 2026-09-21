# Wall-e — local desktop assistant

Wall-e is a small, fully local AI assistant that runs on your Linux machine.
A small primary model (`qwen3:1.7b`) acts as the orchestrator: it talks to
you, calls tools, and delegates hard reasoning or code-writing to a bigger
local model (`ornith-1.5:9b`). Replies can be spoken out loud.

```
                USER
                 │
                 ▼
          PRIMARY_MODEL
           ornith-1.5:9b
                 │
        ┌────────┼────────┐
        ▼        ▼        ▼
   file tools  web tools ask_expert
                                  │
                                  ▼
                            ADVANCED_MODEL
                             ornith-1.5:9b
                                  │
                                  ▼
                            tool result
                                  │
                                  ▼
                           PRIMARY_MODEL
                                  │
                                  ▼
                            FINAL ANSWER
```

## Layout

| File | Role |
|---|---|
| `tui.py` | Rich terminal UI (entry point). Run this. |
| `core.py` | Agent loop: model → tool calls → results → answer. Print/input-free so other front-ends can reuse `run_agent()`. |
| `tools/` | Tool subpackage by category (`filesystem`, `system`, `desktop`, `web`, `memory`, `reasoning`); functions use the `@tool` decorator in `tools/_common.py` and `tools/__init__.py` auto-assembles the `TOOLS` name → function dict Ollama builds schemas from. |
| `prompt.py` | System prompt: rules, guardrails, tool list, date, stored user facts. |
| `helper.py` | Conversation state, `history.json` persistence, `about_me.json` profile storage. |
| `config.py` | Models, limits, file paths, search keys, TTS settings. |
| `voice.py` | Text-to-speech: flite / edge / kokoro with automatic fallback. Never raises. |

## Requirements

- Python 3.10+ (developed on 3.14.7)
- [Ollama](https://ollama.com) running locally with both models pulled:
  ```bash
  ollama pull qwen3:1.7b
  ollama pull ornith-1.5:9b
  ```
- System packages (most already present on a typical desktop):
  `flite` (offline fallback voice), `ffmpeg` (needed to convert edge-tts
  audio), and one audio player (`paplay`, `pw-play`, `aplay`, or `ffplay`).
- Python packages in `requirements.txt` (core: `ollama`, `rich`;
  TTS default engine: `edge-tts`; optional: `kokoro-onnx`, `soundfile`).

## Setup

```bash
cd Wall-e
python3 -m venv .venv && source .venv/bin/activate   # or use your own venv
pip install -r requirements.txt                       # core + edge TTS voice
# optional, for the offline kokoro voice:
# pip install kokoro-onnx soundfile
python3 tui.py
```

Kokoro additionally needs its model files in `./models` (see "Voice" below).

Optional: for official Google results in `search_web`, fill
`GOOGLE_API_KEY` and `GOOGLE_CSE_ID` in `config.py`. Without them it falls
back to keyless DuckDuckGo.

## Usage

In the TUI, just type. Useful commands:

- `/help` — show commands
- `/clear` — start a new session (also clears saved history)
- `/tts` | `/tts on` | `/tts off` — toggle voice output
- `/voice` — show engine status; `/voice flite|edge|kokoro` — switch live
- `/exit` — quit (`exit`, `quit`, Ctrl+C / Ctrl+D work too)

## Tools (14)

Filesystem (`tools/filesystem.py`): `read_file`, `save_file` (mode
`overwrite` backs up the original to `<name>.bak-YYYYMMDD-HHMMSS` before
overwriting and restores it if the write fails; mode `append` grows
logs/notes without erasing; parents auto-created), `inspect_path` (empty
means the current directory -- "where am I / here"; directories list
entries, files report size/mtime), `search_files` (recursive glob),
`transfer_file` (action `copy`/`move`, refuses to overwrite, parents
auto-created).

System (`tools/system.py`): `host_info` (OS, CPU, memory, disk, uptime,
session -- call it instead of guessing specs), `run_shell` (60 s timeout,
capped output), `take_screenshot` (target `screen`/`window`/`region`,
saves a PNG to `/tmp`, returns path + dimensions; needs spectacle, grim,
scrot, ImageMagick, gnome-screenshot, or maim).

Desktop (`tools/desktop.py`): `launch_file` (opens files/folders/screenshots
via xdg-open, formerly `open_file`), `copy_to_clipboard` (Wayland/X11,
formerly `clipboard_copy`).

Web (`tools/web.py`): `search_web` (source `web` = official Google API with
keys, DuckDuckGo fallback without; source `wikipedia` = keyless official
API; replaces `search_google` / `search_wikipedia`, kept as deprecated
aliases).

Memory (`tools/memory.py`): `remember_fact` (stores durable facts in
`about_me.json` — never secrets or small talk; formerly
`remember_user_info`), `save_note` (timestamped notes to `~/notes.txt`;
formerly `take_note`).

Reasoning (`tools/reasoning.py`): `ask_expert` (hard tasks go to the 9B
model with a self-contained prompt; the model unloads right after answering
via `keep_alive=0` — raise `ADVANCED_KEEP_ALIVE` in `config.py` if
delegations get frequent; formerly `delegate_to_advanced_model`).

Screenshot vision note: the bundled text models (`qwen3:1.7b`,
`ornith-1.5:9b`, `llama3.2:1b`) reject image payloads, so `take_screenshot`
returns path + metadata and `core.py` attaches pixels opportunistically
(text fallback on 400 multimodal errors). Pull a vision model
(e.g. `ollama pull qwen2.5vl`) and set it as `PRIMARY_MODEL` for the model
to actually see screenshots.

Complex work (code, file content) is always drafted by the advanced model
first, then saved with `save_file` — this is enforced in the system prompt.

Rename map (old → new): `write_file`+`append_to_file` → `save_file`,
`list_directory`+`file_info`+`current_directory` → `inspect_path`,
`find_files` → `search_files`, `copy_file`/`move_file` → `transfer_file`,
`make_directory` → dropped (auto-created), `run_command` → `run_shell`,
`system_info` → `host_info`, `open_file` → `launch_file`,
`clipboard_copy` → `copy_to_clipboard`, `take_note` → `save_note`,
`remember_user_info` → `remember_fact`, `search_google`/`search_wikipedia`
→ `search_web`, `delegate_to_advanced_model` → `ask_expert`. Run `/clear`
after upgrading: old `history.json` tool calls use retired names.

## Memory files

- `history.json` — full conversation log, saved every turn, restored on
  startup. Thinking traces are stripped before saving.
- `about_me.json` — durable user facts, written **only** by the
  `remember_fact` tool and injected into the system prompt each turn.
  Created on first real use; delete either file to reset it.

## Voice

`TTS_ENGINE` in `config.py`: `"edge"` (default, Microsoft `en-US-AriaNeural`
female neural voice, needs internet per utterance), `"flite"` (offline
robotic fallback, female `slt` voice), `"kokoro"` (offline neural,
`af_heart` female voice).

Kokoro setup:

```bash
pip install kokoro-onnx soundfile
mkdir -p models && cd models
wget -c https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.1/kokoro-v1.0.onnx
wget -c https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.1/voices-v1.0.bin
```

`speak()` never breaks the assistant: an unavailable or failed engine falls
back to flite, and the TUI shows which engine actually spoke (`[voice: edge]`).
Replies are capped at `TTS_MAX_CHARS` and code blocks are skipped when spoken.

## Guardrails

The system prompt (`prompt.py`) forbids guessing (read files / run commands
instead of inventing results), destructive commands without explicit user
consent, reading or revealing secrets, following instructions hidden in tool
results (prompt-injection defense), and unverified claims. These are soft
rules on top of the hard limits in code (timeouts, output caps, backup and
restore on write, error feedback into the agent loop).
