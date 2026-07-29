from dataclasses import dataclass
from collections.abc import Mapping
from typing import Any, Protocol, Sequence


@dataclass(frozen=True)
class Message:
    role: str
    content: str
    name: str | None = None
    tool_call_id: str | None = None


@dataclass(frozen=True)
class ToolCall:
    name: str
    arguments: Mapping[str, Any]
    call_id: str | None = None


@dataclass(frozen=True)
class ModelResponse:
    content: str | None = None
    tool_call: ToolCall | None = None

    def __post_init__(self) -> None:
        if (self.content is None) == (self.tool_call is None):
            raise ValueError("model response must contain content or a tool call")


class ModelClientError(RuntimeError):
    """Raised when a model request or response cannot be used."""


class ModelClient(Protocol):
    def complete(self, messages: Sequence[Message]) -> ModelResponse:
        """Generate one assistant response for the supplied conversation."""
