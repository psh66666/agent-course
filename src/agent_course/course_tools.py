from typing import Any, Mapping

from .tools import ToolDefinition, ToolRegistry


COURSE_TOPICS = {
    "agent": "Agent 是由模型、Runtime、状态、工具和控制规则组成的系统。",
    "llm": "LLM 根据输入消息生成文本或动作建议，但不会自动执行外部工具。",
    "modelclient": "ModelClient 隔离模型供应商和 HTTP 细节，让模型实现可以被替换。",
    "toolregistry": "ToolRegistry 管理工具白名单、参数契约和 handler 的映射。",
}


def lookup_topic(arguments: Mapping[str, Any]) -> str:
    topic = arguments["topic"].strip().lower()
    return COURSE_TOPICS.get(topic, f"No course note found for topic: {topic}")


def build_course_registry() -> ToolRegistry:
    registry = ToolRegistry()
    registry.register(
        ToolDefinition(
            name="lookup_topic",
            description="Look up a known concept from the course notes.",
            parameters={
                "type": "object",
                "properties": {"topic": {"type": "string"}},
                "required": ["topic"],
                "additionalProperties": False,
            },
            handler=lookup_topic,
        )
    )
    return registry
