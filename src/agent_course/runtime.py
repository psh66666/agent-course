from dataclasses import dataclass
from typing import Sequence

from .model import Message, ModelClient


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
    """The first runtime: build a prompt and ask the model once."""

    def __init__(
        self,
        model: ModelClient,
        system_prompt: str = DEFAULT_SYSTEM_PROMPT,
        recorder: TraceRecorder | None = None,
    ) -> None:
        self._model = model
        self._system_prompt = system_prompt
        self._recorder = recorder

    def respond(self, user_input: str) -> str:
        messages: Sequence[Message] = [
            Message(role="system", content=self._system_prompt),
            Message(role="user", content=user_input),
        ]
        if self._recorder is not None:
            self._recorder.record("model.request", f"messages={len(messages)}")
        response = self._model.complete(messages)
        if self._recorder is not None:
            self._recorder.record(
                "model.response", f"content_length={len(response.content)}"
            )
        return response.content
