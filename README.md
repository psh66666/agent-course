# Agent Course

这是一个从零开始构建 Agent 的教学项目。代码刻意保持小而直接，每次课程只引入一个新的核心概念。

## 第一课：模型调用与 Agent Runtime

第一课展示：

- `Message` 表示对话消息
- `ModelClient` 隔离模型供应商
- `AgentRuntime` 组织系统提示和用户输入
- `TraceRecorder` 记录不含敏感内容的执行摘要
- `MockModel` 让项目无需网络即可运行
- `OpenAICompatibleModel` 调用 `/v1/chat/completions`

## 第二课：工具契约与注册表

第二课新增：

- `ToolDefinition` 描述工具名称、用途、参数和执行器
- `ToolRegistry` 管理工具白名单、参数校验和执行结果
- 当前参数 schema 只接受顶层 `object` 和属性 `string`、`number`、`boolean`
- `lookup_topic` 提供一个完全离线的课程知识查询工具

当前可以直接运行工具实验：

```bash
PYTHONPATH=src python3 -c 'from agent_course.course_tools import build_course_registry; print(build_course_registry().execute("lookup_topic", {"topic": "Agent"}))'
```

本地 Mock 已支持结构化工具调用循环；真实模型的供应商工具协议将在后续课程接入。

运行测试：

```bash
PYTHONPATH=src python3 -m unittest discover -s tests -v
```

离线运行：

```bash
PYTHONPATH=src python3 -m agent_course
```

使用远程模型时，在启动前设置 `MODEL_BASE_URL`、`MODEL_API_KEY` 和 `MODEL_NAME`。三个变量必须同时存在；不要把真实密钥写入文件。

教学过程记录在 [`docs/teaching-log.md`](docs/teaching-log.md)。
