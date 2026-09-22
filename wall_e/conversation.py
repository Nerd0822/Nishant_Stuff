"""Conversation state, history persistence, and user profile."""

import json

from .config import ABOUT_ME_FILE, HISTORY_FILE

# Shared conversation state. All modules import this list object and mutate it
# in place, so everything stays in sync.
conversation: list[dict] = []


def create_user_message(user_input: str) -> dict:
    return {"role": "user", "content": user_input}


def _message_to_dict(message) -> dict:
    if hasattr(message, "model_dump"):
        data = message.model_dump(exclude_none=True)
        data.pop("thinking", None)
        data.pop("images", None)
        return data
    data = dict(message)
    data.pop("images", None)
    return data


def save_history() -> None:
    """Write the current conversation to HISTORY_FILE."""
    try:
        data = [_message_to_dict(m) for m in conversation]
        HISTORY_FILE.write_text(
            json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8"
        )
    except OSError as exc:
        print(f"[history] could not save: {exc}")


def load_history() -> None:
    """Restore HISTORY_FILE into the shared conversation list."""
    if not HISTORY_FILE.exists():
        return
    try:
        data = json.loads(HISTORY_FILE.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        print(f"[history] ignoring unreadable {HISTORY_FILE.name}: {exc}")
        return
    if isinstance(data, list):
        conversation.clear()
        conversation.extend(data)


def load_user_info() -> list[str]:
    """Return stored user facts from about_me.json."""
    if not ABOUT_ME_FILE.exists():
        return []
    try:
        data = json.loads(ABOUT_ME_FILE.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return []
    if isinstance(data, list):
        return [str(item) for item in data]
    return []


def append_user_info(info: str) -> bool:
    """Store one fact. Returns False when it is empty or already known."""
    info = " ".join(str(info).split())
    if not info:
        return False
    facts = load_user_info()
    if info in facts:
        return False
    facts.append(info)
    try:
        ABOUT_ME_FILE.write_text(
            json.dumps(facts, indent=2, ensure_ascii=False), encoding="utf-8"
        )
    except OSError as exc:
        print(f"[memory] could not save: {exc}")
        return False
    return True