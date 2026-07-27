from typing import Sequence

from .model import Message, ModelResponse


class MockModel:
    """Deterministic model used for local lessons and tests."""

    def complete(self, messages: Sequence[Message]) -> ModelResponse:
        user_message = next(
            message for message in reversed(messages) if message.role == "user"
        )
        return ModelResponse(content=f"Mock response to: {user_message.content}")
