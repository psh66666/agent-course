import unittest

from agent_course.course_tools import build_course_registry
from agent_course.tools import ToolDefinition, ToolRegistry


class ToolRegistryTests(unittest.TestCase):
    def test_lookup_topic_returns_course_content(self) -> None:
        registry = build_course_registry()

        result = registry.execute("lookup_topic", {"topic": "Agent"})

        self.assertTrue(result.ok)
        self.assertIn("模型", result.content)
        self.assertIsNone(result.error_code)

    def test_unknown_tool_returns_structured_error(self) -> None:
        registry = build_course_registry()

        result = registry.execute("delete_file", {"path": "/tmp/example"})

        self.assertFalse(result.ok)
        self.assertEqual(result.error_code, "tool_not_found")
        self.assertIn("delete_file", result.content)

    def test_missing_required_argument_is_rejected(self) -> None:
        registry = build_course_registry()

        result = registry.execute("lookup_topic", {})

        self.assertFalse(result.ok)
        self.assertEqual(result.error_code, "invalid_arguments")

    def test_wrong_argument_type_is_rejected(self) -> None:
        registry = build_course_registry()

        result = registry.execute("lookup_topic", {"topic": 123})

        self.assertFalse(result.ok)
        self.assertEqual(result.error_code, "invalid_arguments")

    def test_duplicate_tool_registration_is_rejected(self) -> None:
        registry = ToolRegistry()
        tool = ToolDefinition(
            name="example",
            description="An example tool.",
            parameters={"type": "object"},
            handler=lambda _arguments: "ok",
        )
        registry.register(tool)

        with self.assertRaises(ValueError):
            registry.register(tool)

    def test_invalid_schema_is_rejected_at_registration(self) -> None:
        registry = ToolRegistry()
        tool = ToolDefinition(
            name="invalid",
            description="Invalid schema.",
            parameters={"type": "object", "properties": None},
            handler=lambda _arguments: "ok",
        )

        with self.assertRaises(ValueError):
            registry.register(tool)

    def test_unsupported_schema_type_is_rejected(self) -> None:
        registry = ToolRegistry()
        tool = ToolDefinition(
            name="invalid",
            description="Unsupported schema.",
            parameters={"type": "array"},
            handler=lambda _arguments: "ok",
        )

        with self.assertRaises(ValueError):
            registry.register(tool)

    def test_unsupported_property_schema_type_is_rejected(self) -> None:
        registry = ToolRegistry()
        tool = ToolDefinition(
            name="invalid",
            description="Unsupported property schema.",
            parameters={
                "type": "object",
                "properties": {"items": {"type": "array"}},
            },
            handler=lambda _arguments: "ok",
        )

        with self.assertRaises(ValueError):
            registry.register(tool)

    def test_empty_tool_name_is_rejected(self) -> None:
        registry = ToolRegistry()
        tool = ToolDefinition(
            name=" ",
            description="Unnamed tool.",
            parameters={"type": "object"},
            handler=lambda _arguments: "ok",
        )

        with self.assertRaises(ValueError):
            registry.register(tool)

    def test_unexpected_argument_is_rejected(self) -> None:
        registry = build_course_registry()

        result = registry.execute(
            "lookup_topic", {"topic": "Agent", "extra": "value"}
        )

        self.assertFalse(result.ok)
        self.assertEqual(result.error_code, "invalid_arguments")

    def test_handler_failure_returns_structured_error(self) -> None:
        registry = ToolRegistry()
        registry.register(
            ToolDefinition(
                name="fails",
                description="A failing tool.",
                parameters={"type": "object"},
                handler=lambda _arguments: (_ for _ in ()).throw(RuntimeError()),
            )
        )

        result = registry.execute("fails", {})

        self.assertFalse(result.ok)
        self.assertEqual(result.error_code, "tool_execution_error")

    def test_non_text_handler_result_returns_structured_error(self) -> None:
        registry = ToolRegistry()
        registry.register(
            ToolDefinition(
                name="number",
                description="Returns a number.",
                parameters={"type": "object"},
                handler=lambda _arguments: 123,  # type: ignore[return-value]
            )
        )

        result = registry.execute("number", {})

        self.assertFalse(result.ok)
        self.assertEqual(result.error_code, "invalid_tool_result")


if __name__ == "__main__":
    unittest.main()
