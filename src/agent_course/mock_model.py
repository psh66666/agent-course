from collections.abc import Sequence

from .model import Message, ModelResponse
from .tools import ToolDefinition


class MockModel:
    def complete(
        self,
        messages: Sequence[Message],
        *,
        tools: Sequence[ToolDefinition] = (),
    ) -> ModelResponse:
        user_message = next(
            message for message in reversed(messages) if message.role == "user"
        )
        return ModelResponse(content=f"Mock response to: {user_message.content}")
