import json
from dataclasses import dataclass

from .model import Message, ModelClient
from .tools import ToolRegistry, ToolResult


DEFAULT_SYSTEM_PROMPT = (
    "You are a concise teaching assistant. Explain concepts with small examples."
)


@dataclass(frozen=True)
class TraceEvent:
    kind: str
    detail: str


class TraceRecorder:
    def __init__(self) -> None:
        self._events: list[TraceEvent] = []

    @property
    def events(self) -> tuple[TraceEvent, ...]:
        return tuple(self._events)

    def record(self, kind: str, detail: str) -> None:
        self._events.append(TraceEvent(kind=kind, detail=detail))


class AgentRuntime:
    """A bounded runtime that can execute structured tool calls."""

    def __init__(
        self,
        model: ModelClient,
        system_prompt: str = DEFAULT_SYSTEM_PROMPT,
        recorder: TraceRecorder | None = None,
        tool_registry: ToolRegistry | None = None,
        max_steps: int = 8,
    ) -> None:
        if max_steps < 1:
            raise ValueError("max_steps must be positive")
        self._model = model
        self._system_prompt = system_prompt
        self._recorder = recorder
        self._tool_registry = tool_registry
        self._max_steps = max_steps

    def respond(self, user_input: str) -> str:
        messages: list[Message] = [
            Message(role="system", content=self._system_prompt),
            Message(role="user", content=user_input),
        ]
        for _step in range(self._max_steps):
            if self._recorder is not None:
                self._recorder.record("model.request", f"messages={len(messages)}")
            response = self._model.complete(messages)

            if response.content is not None:
                if self._recorder is not None:
                    self._recorder.record(
                        "model.response", f"content_length={len(response.content)}"
                    )
                return response.content

            tool_call = response.tool_call
            if self._recorder is not None:
                self._recorder.record("model.tool_call", f"name={tool_call.name}")
            if self._tool_registry is None:
                result = ToolResult(
                    ok=False,
                    content="No tool registry is configured for this agent.",
                    error_code="tools_unavailable",
                )
            else:
                result = self._tool_registry.execute(
                    tool_call.name, tool_call.arguments
                )
            if self._recorder is not None:
                self._recorder.record(
                    "tool.result", f"ok={result.ok},error_code={result.error_code}"
                )
            messages.append(
                Message(
                    role="tool",
                    content=_serialize_tool_result(result),
                    name=tool_call.name,
                    tool_call_id=tool_call.call_id,
                )
            )

        return "Agent stopped after reaching the maximum tool steps."


def _serialize_tool_result(result: ToolResult) -> str:
    return json.dumps(
        {
            "ok": result.ok,
            "content": result.content,
            "error_code": result.error_code,
        },
        ensure_ascii=False,
    )
