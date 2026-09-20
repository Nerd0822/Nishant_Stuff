# Naoki — local desktop assistant

Naoki is a small, fully local AI assistant that runs on your Linux machine.
A small primary model (`qwen3:1.7b`) acts as the orchestrator: it talks to
you, calls tools, and delegates hard reasoning or code-writing to a bigger
local model (`ornith-1.5:9b`). Replies can be spoken out loud.

```
                USER
                 │
                 ▼
          PRIMARY_MODEL
           qwen3:1.7b
                 │
        ┌────────┼────────┐
        ▼        ▼        ▼
   file tools  web tools delegate_to_advanced_model
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
| `tools/` | Tool subpackage by category (`files`, `shell`, `web`, `memory`, `desktop`, `models`); `tools/__init__.py` assembles the `TOOLS` name → function dict Ollama builds schemas from. |
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
cd Naoki
python3 -m venv .venv && source .venv/bin/activate   # or use your own venv
pip install -r requirements.txt                       # core + edge TTS voice
# optional, for the offline kokoro voice:
# pip install kokoro-onnx soundfile
python3 tui.py
```

Kokoro additionally needs its model files in `./models` (see "Voice" below).

Optional: for official Google results in `search_google`, fill
`GOOGLE_API_KEY` and `GOOGLE_CSE_ID` in `config.py`. Without them it falls
back to keyless DuckDuckGo.

## Usage

In the TUI, just type. Useful commands:

- `/help` — show commands
- `/clear` — start a new session (also clears saved history)
- `/tts` | `/tts on` | `/tts off` — toggle voice output
- `/voice` — show engine status; `/voice flite|edge|kokoro` — switch live
- `/exit` — quit (`exit`, `quit`, Ctrl+C / Ctrl+D work too)

## Tools (19)

File: `read_file`, `write_file` (backs up the original to
`<name>.bak-YYYYMMDD-HHMMSS` before overwriting, restores it if the write
fails), `append_to_file` (grows logs/notes without erasing), `list_directory`,
`current_directory` ("where am I / here"), `find_files`, `file_info`,
`copy_file` / `move_file` (both refuse to overwrite existing files),
`make_directory`, `open_file` (opens files/folders via xdg-open).

Desktop: `system_info` (OS, CPU, memory, disk, uptime, session -- call it
instead of guessing specs), `clipboard_copy` (Wayland/X11), `take_note`
(timestamped notes to `~/notes.txt`), `run_command` (60 s timeout,
capped output).

Web: `search_wikipedia` (keyless official API), `search_google` (official
Google API with keys, DuckDuckGo fallback without).

Memory/reasoning: `remember_user_info` (stores durable facts in
`about_me.json` — never secrets or small talk), `delegate_to_advanced_model`
(hard tasks go to the 9B model with a self-contained prompt; the model
unloads right after answering via `keep_alive=0` — raise
`ADVANCED_KEEP_ALIVE` in `config.py` if delegations get frequent).

Complex work (code, file content) is always drafted by the advanced model
first, then saved with `write_file` — this is enforced in the system prompt.

## Memory files

- `history.json` — full conversation log, saved every turn, restored on
  startup. Thinking traces are stripped before saving.
- `about_me.json` — durable user facts, written **only** by the
  `remember_user_info` tool and injected into the system prompt each turn.
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
