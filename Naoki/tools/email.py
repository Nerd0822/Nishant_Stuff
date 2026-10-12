"""Email tools. Read and search only -- nothing here can send.

Plain IMAP over stdlib imaplib, so there is no dependency to install. Needs
gmail_user and gmail_pass (a Google app password, not the account password) in
.env. Every error is left to propagate: a wrong password raises
imaplib.IMAP4.error with the server's real complaint attached.
"""

import email
import imaplib
import os
from email import policy

from langchain_core.tools import tool

from config import Base_dir  # noqa: F401  (loads .env via config import side effect)


def _connect() -> tuple[imaplib.IMAP4_SSL, str]:
    """Log into IMAP, select INBOX, return the connection."""
    user = os.environ.get("gmail_user")
    password = os.environ.get("gmail_pass")
    if not user or not password:
        raise ValueError("gmail_user and gmail_pass must be set in .env")

    conn = imaplib.IMAP4_SSL(os.environ.get("imap_host", "imap.gmail.com"))
    conn.login(user, password)
    conn.select("INBOX")
    return conn, user


def _fmt(msg: email.message.Message) -> str:
    """Render one message as From / Subject / Date / body."""
    body = ""
    if msg.is_multipart():
        for part in msg.walk():
            if part.get_content_type() == "text/plain":
                body = part.get_content()
                break
    else:
        body = msg.get_content()
    return "\n".join(
        [
            f"From: {msg['from']}",
            f"Subject: {msg['subject']}",
            f"Date: {msg['date']}",
            "---",
            body.strip(),
        ]
    )


@tool
def read_email(index: int = 0) -> str:
    """Read the most recent email, newest first. Args: index (0 is newest)."""
    conn, _ = _connect()
    try:
        ids = conn.search(None, "ALL")[1][0].split()
        if not ids:
            return "(inbox empty)"
        return _fmt(email.message_from_bytes(conn.fetch(ids[-1 - index], "(RFC822)")[1][0][1], policy=policy.default))
    finally:
        conn.logout()


@tool
def search_emails(query: str, limit: int = 5) -> str:
    """Search email. query is IMAP syntax: 'UNSEEN', 'FROM someone', 'SUBJECT x'. Args: query, limit."""
    conn, _ = _connect()
    try:
        ids = conn.search(None, query)[1][0].split()[-limit:]
        if not ids:
            return f"no matches for: {query}"
        return "\n\n".join(
            _fmt(email.message_from_bytes(conn.fetch(i, "(RFC822)")[1][0][1], policy=policy.default))
            for i in reversed(ids)
        )
    finally:
        conn.logout()