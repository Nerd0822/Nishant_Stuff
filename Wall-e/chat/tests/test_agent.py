"""Tests for the chat agent module.

The agent module (chat/agent.py) exposes:
  - _build_ollama_options() -> dict
  - get_response(user_message, prev_messages, on_tool_event=None) -> str

All tests mock `ollama.chat` so no real LLM runs.
"""
from unittest.mock import MagicMock, patch

from chat.agent import get_response


# ── helpers ──────────────────────────────────────────────────────────
def _flush(content="resp", tool_calls=None):
    """A MagicMock stream whose .message looks like a parsed Ollama reply."""
    tc = tool_calls or []
    msg = MagicMock()
    msg.content = content
    msg.tool_calls = tc
    stream = MagicMock()
    stream.message = msg
    return stream


def _tool_call(name, arguments=None):
    """A MagicMock that looks like one element of assistant_msg.tool_calls.
    `arguments` must be a dict (Ollama returns parsed JSON, never a string).
    """
    if arguments is None:
        arguments = {}
    fn = MagicMock()
    fn.name = name
    fn.arguments = arguments
    tc = MagicMock()
    tc.function = fn
    tc.index = 0
    tc.type = "tool_call"
    tc.id = "c1"
    return tc


# ── options / message-building tests (no tool calls) ──────────────
class OptionsAndMessagesTest:
    def test_model_kwarg_is_primary_model(self):
        with patch("chat.agent.ollama") as m:
            m.chat.return_value = _flush(content="ok", tool_calls=[])
            get_response("hi", [])
        assert m.chat.call_args.kwargs["model"] == "ornith-1.5:9b"

    def test_system_message_is_first(self):
        with patch("chat.agent.ollama") as m:
            m.chat.return_value = _flush(content="ok", tool_calls=[])
            get_response("hi", [])
        msgs = m.chat.call_args.kwargs["messages"]
        assert msgs[0]["role"] == "system"
        assert msgs[-1]["role"] == "user"
        assert msgs[-1]["content"] == "hi"

    def test_user_message_is_last_entry(self):
        with patch("chat.agent.ollama") as m:
            m.chat.return_value = _flush(content="ok", tool_calls=[])
            get_response("hello world", [])
        msgs = m.chat.call_args.kwargs["messages"]
        assert msgs[-1]["content"] == "hello world"

    def test_empty_history_still_has_system_and_user(self):
        with patch("chat.agent.ollama") as m:
            m.chat.return_value = _flush(content="ok", tool_calls=[])
            get_response("hi", [])
        msgs = m.chat.call_args.kwargs["messages"]
        assert len(msgs) == 2  # system + user

    def test_history_appended_between_system_and_user(self):
        hist = [{"role": "user", "content": "previous"}]
        with patch("chat.agent.ollama") as m:
            m.chat.return_value = _flush(content="ok", tool_calls=[])
            get_response("hi", hist)
        msgs = m.chat.call_args.kwargs["messages"]
        assert msgs[1]["content"] == "previous"
        assert msgs[-1]["content"] == "hi"


# ── direct (no tool_calls) response tests ───────────────────────────
class DirectResponseTest:
    def test_returns_content_string(self):
        with patch("chat.agent.ollama") as m:
            m.chat.return_value = _flush(content="hello back", tool_calls=[])
            result = get_response("hi", [])
        assert result == "hello back"

    def test_empty_content_returns_empty_string(self):
        with patch("chat.agent.ollama") as m:
            m.chat.return_value = _flush(content="", tool_calls=[])
            result = get_response("hi", [])
        assert result == ""

    def test_none_content_returns_empty_string(self):
        with patch("chat.agent.ollama") as m:
            m.chat.return_value = _flush(content=None, tool_calls=[])
            result = get_response("hi", [])
        assert result == ""

    def test_tool_calls_empty_list_returns_content(self):
        with patch("chat.agent.ollama") as m:
            m.chat.return_value = _flush(content="final", tool_calls=[])
            result = get_response("hi", [])
        assert result == "final"


# ── tool-call tests ──────────────────────────────────────────────────
class ToolCallTest:
    """Tests where the model requests one or more tools.

    Every test uses ``side_effect`` with *two* responses so the agent loop
    terminates on the second turn with a real final answer instead of running
    until MAX_TURNS and returning the ``"stopped after ..."`` string.
    """

    def _with_known_tool(self, tool_name="echo", arguments=None, result_str="tool ok"):
        if arguments is None:
            arguments = {}
        tool_fn = MagicMock(return_value=result_str)
        with patch("chat.agent.ollama") as m, \
             patch("chat.agent.TOOLS", {tool_name: tool_fn}):
            tc = _tool_call(tool_name, arguments)
            m.chat.side_effect = [
                _flush(content="", tool_calls=[tc]),
                _flush(content=result_str, tool_calls=[]),
            ]
            resp = get_response("hi", [])
        return resp, tool_fn

    def test_known_tool_called_with_parsed_args(self):
        resp, fn = self._with_known_tool("echo", {"msg": "hello"})
        fn.assert_called_once_with(msg="hello")
        assert resp == "tool ok"

    def test_known_tool_with_empty_args(self):
        resp, fn = self._with_known_tool("echo", {})
        fn.assert_called_once_with()
        assert resp == "tool ok"

    def test_unknown_tool_returns_error_text(self):
        tc = _tool_call("no_such_tool", {"a": 1})
        with patch("chat.agent.ollama") as m:
            m.chat.side_effect = [
                _flush(content="", tool_calls=[tc]),
                _flush(content="done", tool_calls=[]),
            ]
            get_response("hi", [])
        second_call = m.chat.call_args_list[1]
        msgs = second_call.kwargs["messages"]
        tool_msgs = [mm for mm in msgs if mm.get("role") == "tool"]
        assert tool_msgs, "expected a tool-role message carrying the error"
        assert "no_such_tool" in tool_msgs[0]["content"]

    def test_tool_exception_caught_and_returned(self):
        tool_fn = MagicMock(side_effect=RuntimeError("boom"))
        tc = _tool_call("echo", {"x": 1})
        with patch("chat.agent.ollama") as m, \
             patch("chat.agent.TOOLS", {"echo": tool_fn}):
            m.chat.side_effect = [
                _flush(content="", tool_calls=[tc]),
                _flush(content="done", tool_calls=[]),
            ]
            get_response("hi", [])
        second_call = m.chat.call_args_list[1]
        msgs = second_call.kwargs["messages"]
        tool_msgs = [mm for mm in msgs if mm.get("role") == "tool"]
        assert tool_msgs, "expected a tool-role message carrying the error"
        assert "RuntimeError" in tool_msgs[0]["content"]
        assert "boom" in tool_msgs[0]["content"]

    def test_tool_result_feeds_back_as_tool_role_message(self):
        """A tool-result message must be appended into the history."""
        tool_fn = MagicMock(return_value="ok")
        with patch("chat.agent.ollama") as m, \
             patch("chat.agent.TOOLS", {"echo": tool_fn}):
            tc = _tool_call("echo", {"x": 1})
            call_count = [0]

            def side(*a, **kw):
                call_count[0] += 1
                if call_count[0] == 1:
                    return _flush(content="", tool_calls=[tc])
                return _flush(content="done", tool_calls=[])

            m.chat.side_effect = side
            resp = get_response("hi", [])
        assert resp == "done"
        first = m.chat.call_args_list[0]
        msgs = first.kwargs.get("messages", first[1].get("messages"))
        tool_msgs = [mm for mm in msgs if mm.get("role") == "tool"]
        assert tool_msgs, "expected a tool-role message after first turn"

    def test_multiple_tool_calls_in_one_response(self):
        tool_a = MagicMock(return_value="A")
        tool_b = MagicMock(return_value="B")
        tca = _tool_call("a", {"k": 1})
        tcb = _tool_call("b", {"k": 2})
        with patch("chat.agent.ollama") as m, \
             patch("chat.agent.TOOLS", {"a": tool_a, "b": tool_b}):
            m.chat.side_effect = [
                _flush(content="", tool_calls=[tca, tcb]),
                _flush(content="done", tool_calls=[]),
            ]
            resp = get_response("hi", [])
        assert resp == "done"
        first_call = m.chat.call_args_list[0]
        msgs = first_call.kwargs["messages"]
        assistant_msgs = [mm for mm in msgs if mm.get("role") == "assistant"]
        assert len(assistant_msgs) == 1
        assert len(assistant_msgs[0].tool_calls) == 2
        tool_msgs = [mm for mm in msgs if mm.get("role") == "tool"]
        assert len(tool_msgs) == 2


# ── on_tool_event callback tests ─────────────────────────────────────
class OnToolEventTest:
    def test_callback_called_for_known_tool(self):
        events = []

        def recorder(kind, *rest, **kw):
            events.append(kind)

        tool_fn = MagicMock(return_value="ok")
        with patch("chat.agent.ollama") as m, \
             patch("chat.agent.TOOLS", {"echo": tool_fn}):
            tc = _tool_call("echo", {"a": 1})
            m.chat.return_value = _flush(content="", tool_calls=[tc])
            get_response("hi", [], on_tool_event=recorder)
        assert "call" in events

    def test_callback_called_for_result(self):
        events = []

        def recorder(kind, *rest, **kw):
            events.append(kind)

        tool_fn = MagicMock(return_value="ok")
        with patch("chat.agent.ollama") as m, \
             patch("chat.agent.TOOLS", {"echo": tool_fn}):
            tc = _tool_call("echo", {"a": 1})
            m.chat.return_value = _flush(content="", tool_calls=[tc])
            get_response("hi", [], on_tool_event=recorder)
        assert "result" in events

    def test_callback_not_called_when_none_provided(self):
        tool_fn = MagicMock(return_value="ok")
        with patch("chat.agent.ollama") as m, \
             patch("chat.agent.TOOLS", {"echo": tool_fn}):
            tc = _tool_call("echo", {"a": 1})
            m.chat.return_value = _flush(content="", tool_calls=[tc])
            get_response("hi", [], on_tool_event=None)
        assert True  # just confirms no crash


# ── loop / edge-case tests ───────────────────────────────────────────
class LoopEdgeCaseTest:
    def test_max_turns_does_not_loop_forever(self):
        import config
        orig = config.MAX_TURNS
        try:
            config.MAX_TURNS = 1
            n = [0]

            def side(*a, **kw):
                n[0] += 1
                return _flush(content=f"turn {n[0]}", tool_calls=[])

            with patch("chat.agent.ollama") as m:
                m.chat.side_effect = side
                resp = get_response("hi", [])
            assert resp == "turn 1"
            assert n[0] == 1
        finally:
            config.MAX_TURNS = orig

    def test_loop_stops_on_none_content(self):
        with patch("chat.agent.ollama") as m:
            m.chat.return_value = _flush(content=None, tool_calls=[])
            resp = get_response("hi", [])
        assert resp == ""

    def test_loop_stops_on_empty_content(self):
        with patch("chat.agent.ollama") as m:
            m.chat.return_value = _flush(content="", tool_calls=[])
            resp = get_response("hi", [])
        assert resp == ""

    def test_history_is_list_of_dicts_passed_to_ollama(self):
        with patch("chat.agent.ollama") as m:
            m.chat.return_value = _flush(content="ok", tool_calls=[])
            get_response("hi", [{"role": "user", "content": "hist"}])
        msgs = m.chat.call_args.kwargs["messages"]
        assert all(isinstance(mm, dict) for mm in msgs)

    def test_stop_message_when_exhausting_max_turns(self):
        """When MAX_TURNS is exhausted without a final answer, the stop
        message is returned and the loop counter matches MAX_TURNS."""
        import config
        orig = config.MAX_TURNS
        try:
            config.MAX_TURNS = 2
            n = [0]

            def side(*a, **kw):
                n[0] += 1
                return _flush(
                    content="", tool_calls=[_tool_call("echo", {"x": 1})]
                )

            tool_fn = MagicMock(return_value="ok")
            with patch("chat.agent.ollama") as m, \
                 patch("chat.agent.TOOLS", {"echo": tool_fn}):
                m.chat.side_effect = side
                resp = get_response("hi", [])
            assert "stopped after" in resp
            assert n[0] == 2
        finally:
            config.MAX_TURNS = orig


def test_module_imports_correctly():
    import chat.agent
    assert hasattr(chat.agent, "get_response")
    assert hasattr(chat.agent, "_build_ollama_options")
