"""Memory tools: durable facts about the user (about_me.json)."""

from helper import append_user_info


def remember_user_info(info: str) -> str:
    """Save a durable fact about the user the moment they share one.

    Call this proactively, BEFORE answering. Example: if the user says their
    name is Nishant, call remember_user_info with that fact right away. One
    fact per call -- a message with three facts needs three calls. The user
    never needs to ask you to remember. Skip secrets, small talk, and
    temporary details.

    Args:
        info: One short sentence describing the fact to remember.
    """
    if append_user_info(info):
        return f"remembered: {info}"
    return f"already known or empty, nothing stored: {info}"
