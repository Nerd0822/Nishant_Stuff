"""Live Ollama pre-deploy check: proves the model is up and replying.

Unit tests never touch the network, so a green suite alone cannot tell you
the assistant will actually answer in production. Run this gate explicitly
before deploying:

    RAAHI_LIVE_TESTS=1 python manage.py test home.test_ollama_live

It fails (instead of skipping) on connection errors — a down Ollama must
block the deploy.
"""

import os
import unittest

import httpx
from django.test import SimpleTestCase

import home.helper as helper
from home.helper import ask_ollama_sync

RUN_LIVE = os.environ.get("RAAHI_LIVE_TESTS") == "1"


@unittest.skipUnless(
    RUN_LIVE,
    "Set RAAHI_LIVE_TESTS=1 to run the live Ollama pre-deploy check.",
)
class OllamaLiveTests(SimpleTestCase):
    def test_model_is_reachable_and_replies(self):
        helper.OLLAMA_TIMEOUT = 120
        try:
            reply = ask_ollama_sync("Reply with exactly this word: OK")
        except httpx.HTTPError as exc:
            # HTTPError is the parent of ConnectError, TimeoutException,
            # RemoteProtocolError, ... — any transport failure must fail
            # the gate with a clear message, not an ERROR traceback.
            self.fail(
                f"Ollama request to {helper.OLLAMA_BASE_URL} failed: {exc}. "
                "Start Ollama (and pull the model) before deploying."
            )
        self.assertTrue(reply.strip(), "Ollama returned an empty reply.")
        self.assertIn(
            "ok", reply.lower(), f"Model did not follow instructions: {reply!r}"
        )
