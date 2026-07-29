import json
import urllib.error
import urllib.request
from collections.abc import Mapping
from typing import Any, Callable, Sequence
from urllib.parse import urlparse

from .model import Message, ModelClientError, ModelResponse, ToolCall
from .tools import ToolDefinition

Urlopen = Callable[..., Any]


class OpenAICompatibleModel:
    """Client for providers exposing the Chat Completions-compatible endpoint."""

    def __init__(
        self,
        base_url: str,
        api_key: str,
        model_name: str,
        *,
        timeout: int = 30,
        urlopen: Urlopen = urllib.request.urlopen,
    ) -> None:
        parsed_base_url = urlparse(base_url)
        if parsed_base_url.scheme not in {"http", "https"} or not parsed_base_url.netloc:
            raise ModelClientError("model base URL must be an HTTP(S) URL")
        self._endpoint = base_url.rstrip("/") + "/chat/completions"
        self._api_key = api_key
        self._model_name = model_name
        self._timeout = timeout
        self._urlopen = urlopen

    def complete(
        self,
        messages: Sequence[Message],
        *,
        tools: Sequence[ToolDefinition] = (),
    ) -> ModelResponse:
        payload: dict[str, Any] = {
            "model": self._model_name,
            "messages": [
                _serialize_message(message)
                for message in messages
            ],
        }
        if tools:
            payload["tools"] = [
                _serialize_tool_definition(tool)
                for tool in tools
            ]
        request = urllib.request.Request(
            self._endpoint,
            data=json.dumps(payload).encode("utf-8"),
            headers={
                "Authorization": f"Bearer {self._api_key}",
                "Content-Type": "application/json",
            },
            method="POST",
        )

        try:
            with self._urlopen(request, timeout=self._timeout) as response:
                status = getattr(response, "status", 200)
                if not 200 <= status < 300:
                    raise ModelClientError(
                        f"model request returned HTTP status {status}"
                    )
                response_body = response.read()
        except (
            urllib.error.HTTPError,
            urllib.error.URLError,
            OSError,
            TimeoutError,
        ) as exc:
            raise ModelClientError("model request failed") from exc

        try:
            data = json.loads(response_body)
            message = data["choices"][0]["message"]
            tool_calls = message.get("tool_calls", [])
        except (
            KeyError,
            IndexError,
            TypeError,
            UnicodeDecodeError,
            json.JSONDecodeError,
        ) as exc:
            raise ModelClientError("model response has an invalid shape") from exc

        if tool_calls:
            if not isinstance(tool_calls, list) or len(tool_calls) != 1:
                raise ModelClientError(
                    "model response must contain exactly one tool call"
                )

            try:
                raw_tool_call = tool_calls[0]
                function = raw_tool_call["function"]
                call_id = raw_tool_call.get("id")
                name = function["name"]
                arguments_text = function["arguments"]
            except (KeyError, TypeError) as exc:
                raise ModelClientError(
                    "model tool call has an invalid shape"
                ) from exc

            if (
                not isinstance(call_id, (str, type(None)))
                or not isinstance(name, str)
                or not isinstance(arguments_text, str)
            ):
                raise ModelClientError("model tool call has invalid fields")

            try:
                arguments = json.loads(arguments_text)
            except (TypeError, json.JSONDecodeError) as exc:
                raise ModelClientError(
                    "model tool call arguments are not valid JSON"
                ) from exc

            if not isinstance(arguments, Mapping):
                raise ModelClientError(
                    "model tool call arguments must be an object"
                )

            return ModelResponse(
                tool_call=ToolCall(
                    name=name,
                    arguments=arguments,
                    call_id=call_id,
                )
            )

        content = message.get("content")
        if not isinstance(content, str):
            raise ModelClientError("model response content must be text")
        return ModelResponse(content=content)


def _serialize_message(message: Message) -> dict[str, str]:
    payload = {"role": message.role, "content": message.content}
    if message.name is not None:
        payload["name"] = message.name
    if message.tool_call_id is not None:
        payload["tool_call_id"] = message.tool_call_id
    return payload


def _serialize_tool_definition(
    tool: ToolDefinition,
) -> dict[str, Any]:
    return {
        "type": "function",
        "function": {
            "name": tool.name,
            "description": tool.description,
            "parameters": tool.parameters,
        },
    }
