# Agent 构建教学记录

## 项目约定

- 项目目录：`/Users/rm001/agent-course`
- 技术路线：Python + OpenAI 兼容 API + 离线 Mock 模式
- 教学方式：每节课先理解概念，再做一个小改动，并用测试或实验验证
- 当前阶段：第一课

## 第一课：模型调用与 Agent Runtime

### 本节目标

理解 LLM 和 Agent 的最小区别，并运行一个不依赖网络的 Agent。

### 核心概念

LLM 负责根据输入生成文本。Agent 则是一个由程序控制的运行时：它组织消息、调用模型、根据模型返回做下一步动作，并在边界内结束。第一课还没有工具调用，所以当前 Runtime 只有一次模型调用；这不是完整 Agent 的终点，而是后续循环的最小基线。

### 当前职责

| 组件 | 职责 |
|---|---|
| `Message` | 表示一条带角色的消息 |
| `ModelClient` | 定义模型客户端必须提供的 `complete` 能力 |
| `MockModel` | 离线返回确定性文本，便于测试和观察 |
| `OpenAICompatibleModel` | 发送 Chat Completions 请求并解析文本回答 |
| `AgentRuntime` | 把系统提示和用户输入交给模型，并返回回答 |
| `TraceRecorder` | 记录消息数量和回答长度，不保存密钥 |
| `CLI` | 读取环境变量和用户输入 |

### 实验命令

```bash
PYTHONPATH=src python3 -m unittest discover -s tests -v
PYTHONPATH=src python3 -m agent_course
```

### 当前验证结果

第一阶段测试覆盖：

- Runtime 传递系统消息和用户消息
- Mock 模式不依赖网络
- OpenAI 兼容客户端构造请求并解析回答
- 远程配置完整性检查

实际结果：`PYTHONPATH=src python3 -m unittest discover -s tests -v` 返回 `Ran 11 tests` 和 `OK`；离线 CLI 输入 `What is an agent?` 后返回 `Mock response to: What is an agent?`；`compileall` 检查通过。测试还验证了非法 URL、非 UTF-8 响应、非 2xx 状态和空配置会被拒绝。

### 容易混淆的地方

1. `ModelClient` 不是 Agent。它只负责一次模型请求。
2. `AgentRuntime` 目前只调用一次模型，因此还没有工具决策循环。
3. OpenAI 兼容只描述 HTTP 请求和响应格式，不代表所有供应商的能力完全相同。
4. 轨迹记录器只记录安全摘要，不能把原始请求日志当作默认安全的调试方式。

### 下一课问题

如果模型只能返回文字，程序如何知道它想调用哪个工具？下一课会引入工具 schema、工具注册表和第一版有界 Agent 循环。
