from django.test import SimpleTestCase

from home.helper import _strip_thinking


class StripThinkingTests(SimpleTestCase):
    def test_removes_closed_block(self):
        self.assertEqual(
            _strip_thinking("<thinking>hmm</thinking>The answer."),
            "The answer.",
        )

    def test_removes_truncated_block(self):
        self.assertEqual(
            _strip_thinking("Partial answer <thinking>still thinking..."),
            "Partial answer",
        )

    def test_plain_text_untouched(self):
        self.assertEqual(_strip_thinking("Just a reply."), "Just a reply.")
