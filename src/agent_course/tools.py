from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any, Callable


ToolHandler = Callable[[Mapping[str, Any]], str]

_SUPPORTED_SCHEMA_KEYS = {
    "type",
    "properties",
    "required",
    "additionalProperties",
}
_SUPPORTED_PROPERTY_SCHEMA_KEYS = {"type"}
_SUPPORTED_PROPERTY_TYPES = {"string", "number", "boolean"}


@dataclass(frozen=True)
class ToolDefinition:
    name: str
    description: str
    parameters: Mapping[str, Any]
    handler: ToolHandler


@dataclass(frozen=True)
class ToolResult:
    ok: bool
    content: str
    error_code: str | None = None


class ToolRegistry:
    def __init__(self) -> None:
        self._tools: dict[str, ToolDefinition] = {}

    def register(self, tool: ToolDefinition) -> None:
        if not isinstance(tool.name, str) or not tool.name.strip():
            raise ValueError("tool name must not be empty")
        if tool.name in self._tools:
            raise ValueError(f"tool already registered: {tool.name}")
        _validate_schema(tool.parameters)
        self._tools[tool.name] = tool

    def get(self, name: str) -> ToolDefinition | None:
        return self._tools.get(name)

    def execute(self, name: str, arguments: Mapping[str, Any]) -> ToolResult:
        tool = self.get(name)
        if tool is None:
            return ToolResult(
                ok=False,
                content=f"No tool named '{name}' is registered.",
                error_code="tool_not_found",
            )

        validation_error = _validate_arguments(tool.parameters, arguments)
        if validation_error is not None:
            return ToolResult(
                ok=False,
                content=validation_error,
                error_code="invalid_arguments",
            )

        try:
            content = tool.handler(arguments)
        except Exception:
            return ToolResult(
                ok=False,
                content=f"Tool '{name}' failed during execution.",
                error_code="tool_execution_error",
            )

        if not isinstance(content, str):
            return ToolResult(
                ok=False,
                content=f"Tool '{name}' returned a non-text result.",
                error_code="invalid_tool_result",
            )
        return ToolResult(ok=True, content=content)


def _validate_arguments(
    schema: Mapping[str, Any], arguments: Mapping[str, Any]
) -> str | None:
    if not isinstance(arguments, Mapping):
        return "Tool arguments must be an object."

    properties = schema.get("properties", {})
    required = schema.get("required", [])
    if any(not isinstance(name, str) for name in arguments):
        return "Tool argument names must be strings."
    for name in required:
        if name not in arguments:
            return f"Missing required argument: {name}."

    if schema.get("additionalProperties") is False:
        unknown = set(arguments) - set(properties)
        if unknown:
            return f"Unknown arguments: {', '.join(sorted(unknown))}."

    for name, value in arguments.items():
        property_schema = properties.get(name)
        if property_schema is None:
            continue
        expected_type = property_schema.get("type")
        if expected_type == "string" and not isinstance(value, str):
            return f"Argument '{name}' must be a string."
        if expected_type == "number" and (
            not isinstance(value, (int, float)) or isinstance(value, bool)
        ):
            return f"Argument '{name}' must be a number."
        if expected_type == "boolean" and not isinstance(value, bool):
            return f"Argument '{name}' must be a boolean."
    return None


def _validate_schema(schema: Mapping[str, Any]) -> None:
    if not isinstance(schema, Mapping):
        raise ValueError("tool parameters schema must be an object")

    unsupported_keys = [
        key for key in schema if key not in _SUPPORTED_SCHEMA_KEYS
    ]
    if unsupported_keys:
        raise ValueError(
            f"unsupported tool schema fields: {', '.join(map(str, unsupported_keys))}"
        )
    if schema.get("type") != "object":
        raise ValueError("tool parameters schema type must be object")

    properties = schema.get("properties", {})
    if not isinstance(properties, Mapping):
        raise ValueError("tool schema properties must be an object")
    for name, property_schema in properties.items():
        if not isinstance(name, str):
            raise ValueError("tool schema property names must be strings")
        if not isinstance(property_schema, Mapping):
            raise ValueError(f"schema for property '{name}' must be an object")
        unsupported_property_keys = [
            key for key in property_schema if key not in _SUPPORTED_PROPERTY_SCHEMA_KEYS
        ]
        if unsupported_property_keys:
            raise ValueError(
                f"unsupported fields for property '{name}': "
                f"{', '.join(map(str, unsupported_property_keys))}"
            )
        if property_schema.get("type") not in _SUPPORTED_PROPERTY_TYPES:
            raise ValueError(
                f"unsupported schema type for property '{name}'"
            )

    required = schema.get("required", [])
    if not isinstance(required, list) or any(
        not isinstance(name, str) for name in required
    ):
        raise ValueError("tool schema required must be a list of strings")
    if len(required) != len(set(required)):
        raise ValueError("tool schema required must not contain duplicates")
    undeclared_required = set(required) - set(properties)
    if undeclared_required:
        raise ValueError(
            "tool schema required contains undeclared properties: "
            f"{', '.join(sorted(undeclared_required))}"
        )

    additional_properties = schema.get("additionalProperties", True)
    if not isinstance(additional_properties, bool):
        raise ValueError("tool schema additionalProperties must be a boolean")
