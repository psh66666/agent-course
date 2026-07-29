import json
import unittest
from typing import Any

from agent_course.agent import Agent
from agent_course.course_tools import build_course_registry
from agent_course.mock_model import MockModel
from agent_course.model import (
    Message,
    ModelClientError,
    ModelResponse,
    ToolCall,
)
from agent_course.openai_compatible import OpenAICompatibleModel
from agent_course.runtime import TraceEvent, TraceRecorder


class RecordingModel:
    def __init__(self) -> None:
        self.messages: list[Message] = []

    def complete(self, messages: list[Message]) -> ModelResponse:
        self.messages = messages
        return ModelResponse(content="recorded answer")


class ScriptedModel:
    def __init__(self, *responses: ModelResponse) -> None:
        self._responses = list(responses)
        self.calls: list[list[Message]] = []

    def complete(self, messages: list[Message]) -> ModelResponse:
        self.calls.append(messages)
        return self._responses.pop(0)


class FakeResponse:
    def __init__(self, payload: dict[str, Any], status: int = 200) -> None:
        self._body = json.dumps(payload).encode("utf-8")
        self.status = status

    def read(self) -> bytes:
        return self._body

    def __enter__(self) -> "FakeResponse":
        return self

    def __exit__(self, *_args: object) -> None:
        return None


class RawFakeResponse:
    def __init__(self, body: bytes, status: int = 200) -> None:
        self._body = body
        self.status = status

    def read(self) -> bytes:
        return self._body

    def __enter__(self) -> "RawFakeResponse":
        return self

    def __exit__(self, *_args: object) -> None:
        return None


class OpenAICompatibleClientTests(unittest.TestCase):
    def test_complete_sends_messages_and_returns_text(self) -> None:
        requests: list[tuple[str, dict[str, str], dict[str, Any], int]] = []

        def fake_urlopen(request: Any, timeout: int) -> FakeResponse:
            requests.append(
                (
                    request.full_url,
                    dict(request.headers),
                    json.loads(request.data.decode("utf-8")),
                    timeout,
                )
            )
            return FakeResponse(
                {"choices": [{"message": {"content": "remote answer"}}]}
            )

        client = OpenAICompatibleModel(
            base_url="https://example.test/v1/",
            api_key="test-key",
            model_name="demo-model",
            urlopen=fake_urlopen,
            timeout=7,
        )

        response = client.complete([Message(role="user", content="hello")])

        self.assertEqual(response.content, "remote answer")
        self.assertEqual(len(requests), 1)
        url, headers, payload, timeout = requests[0]
        self.assertEqual(url, "https://example.test/v1/chat/completions")
        self.assertEqual(headers["Authorization"], "Bearer test-key")
        self.assertEqual(payload["model"], "demo-model")
        self.assertEqual(payload["messages"], [{"role": "user", "content": "hello"}])
        self.assertEqual(timeout, 7)

    def test_non_success_status_is_rejected(self) -> None:
        def fake_urlopen(_request: Any, timeout: int) -> FakeResponse:
            return FakeResponse(
                {"choices": [{"message": {"content": "should not be used"}}]},
                status=500,
            )

        client = OpenAICompatibleModel(
            base_url="https://example.test/v1",
            api_key="test-key",
            model_name="demo-model",
            urlopen=fake_urlopen,
        )

        with self.assertRaises(ModelClientError):
            client.complete([Message(role="user", content="hello")])

    def test_invalid_base_url_is_rejected(self) -> None:
        with self.assertRaises(ModelClientError):
            OpenAICompatibleModel(
                base_url="not-a-url",
                api_key="test-key",
                model_name="demo-model",
            )

    def test_non_utf8_response_is_rejected(self) -> None:
        def fake_urlopen(_request: Any, timeout: int) -> RawFakeResponse:
            return RawFakeResponse(b"\xff")

        client = OpenAICompatibleModel(
            base_url="https://example.test/v1",
            api_key="test-key",
            model_name="demo-model",
            urlopen=fake_urlopen,
        )

        with self.assertRaises(ModelClientError):
            client.complete([Message(role="user", content="hello")])


class AgentTests(unittest.TestCase):
    def test_runtime_passes_system_and_user_messages_to_model(self) -> None:
        model = RecordingModel()
        agent = Agent(model=model, system_prompt="You are a teacher.")

        answer = agent.respond("Explain an agent.")

        self.assertEqual(answer, "recorded answer")
        self.assertEqual(
            model.messages,
            [
                Message(role="system", content="You are a teacher."),
                Message(role="user", content="Explain an agent."),
            ],
        )

    def test_mock_model_works_without_network(self) -> None:
        agent = Agent(model=MockModel())

        answer = agent.respond("hello")

        self.assertEqual(answer, "Mock response to: hello")

    def test_runtime_records_safe_execution_summaries(self) -> None:
        recorder = TraceRecorder()
        agent = Agent(model=RecordingModel(), recorder=recorder)

        agent.respond("hello")

        self.assertEqual(
            recorder.events,
            (
                TraceEvent(kind="model.request", detail="messages=2"),
                TraceEvent(kind="model.response", detail="content_length=15"),
            ),
        )

    def test_runtime_executes_tool_and_returns_follow_up_answer(self) -> None:
        model = ScriptedModel(
            ModelResponse(
                tool_call=ToolCall(
                    name="lookup_topic",
                    arguments={"topic": "Agent"},
                    call_id="call-1",
                )
            ),
            ModelResponse(content="Here is the course explanation."),
        )
        agent = Agent(model=model, tool_registry=build_course_registry())

        answer = agent.respond("What is an agent?")

        self.assertEqual(answer, "Here is the course explanation.")
        self.assertEqual(len(model.calls), 2)
        tool_message = model.calls[1][-1]
        self.assertEqual(tool_message.role, "tool")
        self.assertEqual(tool_message.name, "lookup_topic")
        self.assertEqual(tool_message.tool_call_id, "call-1")
        self.assertIn("Agent 是由模型", tool_message.content)

    def test_unknown_tool_result_is_returned_to_model(self) -> None:
        model = ScriptedModel(
            ModelResponse(
                tool_call=ToolCall(name="missing", arguments={}, call_id="call-1")
            ),
            ModelResponse(content="I cannot use that tool."),
        )
        agent = Agent(model=model, tool_registry=build_course_registry())

        answer = agent.respond("Do something")

        self.assertEqual(answer, "I cannot use that tool.")
        self.assertIn("tool_not_found", model.calls[1][-1].content)

    def test_runtime_stops_after_maximum_tool_steps(self) -> None:
        model = ScriptedModel(
            ModelResponse(tool_call=ToolCall(name="missing", arguments={})),
            ModelResponse(tool_call=ToolCall(name="missing", arguments={})),
        )
        agent = Agent(
            model=model,
            tool_registry=build_course_registry(),
            max_steps=2,
        )

        answer = agent.respond("Do something")

        self.assertIn("maximum tool steps", answer)
        self.assertEqual(len(model.calls), 2)


if __name__ == "__main__":
    unittest.main()
