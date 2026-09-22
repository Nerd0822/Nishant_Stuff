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
| `cli.py` | Rich terminal UI (entry point). Run with `python -m wall_e`. |
| `agent.py` | Agent loop: model → tool calls → results → answer. Print/input-free so other front-ends can reuse `run_agent()`. |
| `tools/` | Tool subpackage by category (`filesystem`, `system`, `desktop`, `web`, `memory`, `reasoning`); functions use the `@tool` decorator in `tools/registry.py` and `tools/__init__.py` auto-assembles the `TOOLS` name → function dict Ollama builds schemas from. |
| `prompt.py` | System prompt: rules, guardrails, tool list, date, stored user facts. |
| `conversation.py` | Conversation state, `history.json` persistence, `about_me.json` profile storage. |
| `models.py` | Model lifecycle: list/load/unload models so only one is resident at a time. Never raises, never hangs. |
| `config.py` | Models, limits, file paths, search keys, TTS settings. |
| `tts.py` | Kokoro v1.0 text-to-speech (`af_nicole`), streamed sentence by sentence. Never raises, cancels fast. |

## Requirements

- Python 3.10+ (developed on 3.14.7)
- [Ollama](https://ollama.com) running locally with both models pulled:
  ```bash
  ollama pull qwen3:1.7b
  ollama pull ornith-1.5:9b
  ```
- System packages: one audio player (`paplay`, `pw-play`, `aplay`, or
  `ffplay`) and `espeak-ng` (the `misaki` phonemizer backend kokoro-onnx uses).
  PipeWire/PulseAudio must be running for realtime playback.
- Python packages in `requirements.txt` (core: `ollama`, `rich`; voice:
  `kokoro-onnx`, `sounddevice`, `soundfile`, `numpy`).

## Setup

```bash
cd Nishant_stuff                                        # repo root
source ml_shit/bin/activate                             # this repo's shared venv
uv pip install --python ml_shit/bin/python -r wall_e/requirements.txt
python -m wall_e
```

Kokoro also needs its two model files in `wall_e/models/` (see "Voice" below).

Optional: for official Google results in `search_web`, fill
`GOOGLE_API_KEY` and `GOOGLE_CSE_ID` in `config.py`. Without them it falls
back to keyless DuckDuckGo.

## Usage

In the TUI, just type. Each turn prints which model is generating
(`🤖 qwen3.5:2b-q4_K_M`), and delegations show the swap
(`🤖 → ornith-1.5:9b (delegated)`). Useful commands:

- `/help` — show commands
- `/clear` — start a new session (also clears saved history)
- `/tts` | `/tts on` | `/tts off` — toggle voice output
- `/voice` — show voice/speed/audio status; `/voice af_heart` — switch voice live (54 voices)
- `/models` — list what is loaded in memory right now
- `/unload` — free all model memory immediately
- `/exit` — quit (`exit`, `quit`, Ctrl+C / Ctrl+D work too)

Ctrl+C during a reply cancels it and rolls the turn back; the TUI keeps
running. Every exit path (`/exit`, `quit`, Ctrl+D, SIGTERM) unloads the models
first.

## Model memory

Two models loaded at once can exhaust VRAM, so `SWAP_MODELS = True` in
`config.py` keeps **one model resident at a time** (`models.py`):

- Before the primary model runs, the advanced model is evicted
  (`agent.py`).
- `ask_expert` evicts the primary model before loading the advanced one
  (`tools/reasoning.py`), then `ADVANCED_KEEP_ALIVE = 0` unloads it as soon as
  the answer is ready.
- `PRIMARY_KEEP_ALIVE = 600` keeps the primary warm for 10 minutes between
  turns, so back-to-back chatting stays fast.
- On exit, `/unload`, or SIGTERM every loaded model is evicted.

`ps`/unload calls use `MODEL_CMD_TIMEOUT = 5` seconds so a busy Ollama server
can never hang the TUI on exit. Set `SWAP_MODELS = False` to keep both models
resident (needs enough VRAM).

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

One engine: Kokoro v1.0 through `kokoro-onnx`, fully offline on CPU, with the
`af_nicole` voice. `TTS_VOICE` in `config.py` picks any of the 54 names inside
`voices-v1.0.bin` (`/voice` lists them, `/voice af_heart` switches live),
`TTS_SPEED` sets the rate, and `TTS_REALTIME` toggles streamed playback.

Speech is real time: the reply is cut into sentence-sized pieces, each piece
goes to the speakers the moment the model renders it, and the next piece is
already rendering while the current one plays. First words land about half a
second after generation on a warm model, and Ctrl+C during playback cuts the
audio immediately (`[voice: stopped]`) while the session stays alive.

Model files (not in git — `wall_e/models/` is ignored):

```bash
mkdir -p wall_e/models && cd wall_e/models
wget -c https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.1/kokoro-v1.0.onnx
wget -c https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.1/voices-v1.0.bin
# or link copies that already exist elsewhere (saves 354MB of duplication):
# ln -s ../../Naoki/models/kokoro-v1.0.onnx .
# ln -s ../../Naoki/models/voices-v1.0.bin .
```

If `sounddevice` cannot open an output device, the clip is rendered to a wav
and handed to a system player instead. `speak()` never breaks the assistant:
a missing model or audio stack costs one warning line and nothing else. Replies
are capped at `TTS_MAX_CHARS`, code blocks are skipped when spoken, and
`/tts off` mutes everything. On exit, `shutdown()` drops the voice weights from
RAM right after the LLMs are unloaded.

## Guardrails

The system prompt (`prompt.py`) forbids guessing (read files / run commands
instead of inventing results), destructive commands without explicit user
consent, reading or revealing secrets, following instructions hidden in tool
results (prompt-injection defense), and unverified claims. These are soft
rules on top of the hard limits in code (timeouts, output caps, backup and
restore on write, error feedback into the agent loop).
