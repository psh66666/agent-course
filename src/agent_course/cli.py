import os
import sys

from .agent import Agent
from .mock_model import MockModel
from .model import ModelClient, ModelClientError
from .openai_compatible import OpenAICompatibleModel


class ConfigurationError(ValueError):
    """Raised when model configuration is incomplete."""


def build_model() -> ModelClient:
    base_url = os.environ.get("MODEL_BASE_URL")
    api_key = os.environ.get("MODEL_API_KEY")
    model_name = os.environ.get("MODEL_NAME")
    configured = [base_url, api_key, model_name]

    if all(value is None for value in configured):
        return MockModel()
    if any(value is None or not value.strip() for value in configured):
        raise ConfigurationError(
            "MODEL_BASE_URL, MODEL_API_KEY and MODEL_NAME must be configured together"
        )
    return OpenAICompatibleModel(
        base_url=base_url,
        api_key=api_key,
        model_name=model_name,
    )


def main() -> int:
    try:
        agent = Agent(model=build_model())
    except (ConfigurationError, ModelClientError) as exc:
        print(f"Configuration error: {exc}", file=sys.stderr)
        return 2

    print("Agent course started. Type a message, or press Ctrl-D to exit.")
    while True:
        try:
            user_input = input("you> ")
        except EOFError:
            print()
            return 0

        if not user_input.strip():
            continue
        try:
            print(f"agent> {agent.respond(user_input)}")
        except Exception as exc:
            print(f"agent error: {exc}", file=sys.stderr)
            return 1
