import json
import urllib.error
import urllib.request
from typing import Any, Callable, Sequence
from urllib.parse import urlparse

from .model import Message, ModelClientError, ModelResponse


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

    def complete(self, messages: Sequence[Message]) -> ModelResponse:
        payload = {
            "model": self._model_name,
            "messages": [
                {"role": message.role, "content": message.content}
                for message in messages
            ],
        }
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
        except (urllib.error.HTTPError, urllib.error.URLError, OSError, TimeoutError) as exc:
            raise ModelClientError("model request failed") from exc

        try:
            data = json.loads(response_body)
            content = data["choices"][0]["message"]["content"]
        except (
            KeyError,
            IndexError,
            TypeError,
            UnicodeDecodeError,
            json.JSONDecodeError,
        ) as exc:
            raise ModelClientError("model response has an invalid shape") from exc

        if not isinstance(content, str):
            raise ModelClientError("model response content must be text")
        return ModelResponse(content=content)
