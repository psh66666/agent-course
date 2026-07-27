from dataclasses import dataclass
from typing import Protocol, Sequence


@dataclass(frozen=True)
class Message:
    role: str
    content: str


@dataclass(frozen=True)
class ModelResponse:
    content: str


class ModelClientError(RuntimeError):
    """Raised when a model request or response cannot be used."""


class ModelClient(Protocol):
    def complete(self, messages: Sequence[Message]) -> ModelResponse:
        """Generate one assistant response for the supplied conversation."""
