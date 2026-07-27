# Agent 教学项目设计规格

## 目标

建立一个从零开始学习 Agent 的本地项目。项目既要能离线运行，也要能通过环境变量切换到 OpenAI 兼容 API。每一轮教学都通过一个可观察、可测试的小改动推进，并把原理、实验和结论记录在教学文档中。

## 学习范围

项目按以下顺序演进：

1. 模型调用、消息和 Agent 循环
2. 工具 schema、工具注册和工具执行
3. 有界循环、错误处理和执行轨迹
4. 对话状态与记忆边界
5. OpenAI 兼容 API 适配
6. MCP 工具和资源
7. 多 Agent 委派与结果汇总
8. 安全策略、评估和可靠性

第一阶段只覆盖第 1 项，并为第 2、3 项保留清晰的扩展边界。

## 技术选择

- Python 3.13+
- Python 标准库实现核心运行时和 HTTP 请求
- `unittest` 实现第一阶段测试，避免初学者先学习测试框架配置
- OpenAI 兼容 Chat Completions 协议作为真实模型接口
- Mock 模型作为默认离线实现
- 环境变量提供 `MODEL_BASE_URL`、`MODEL_API_KEY` 和 `MODEL_NAME`
- 不在代码、Git 历史或教学文档中保存密钥

## 架构

```text
CLI
 |
 v
AgentRuntime -----> ModelClient
 |
 v
TraceRecorder
```

第一阶段的 `AgentRuntime` 负责接收用户输入、构造消息、调用模型并返回最终文本。模型客户端通过协议隔离，真实客户端和 Mock 客户端可以互换。运行轨迹只记录消息数量和模型响应长度，便于教学观察，但不记录原始输入、响应内容或 API 密钥。

工具执行属于下一阶段，不在第一阶段伪装成已经完成的能力。这样可以先把“模型调用”和“Agent 控制循环”讲清楚，再引入模型驱动的工具调用。

## 目录边界

```text
agent-course/
├── src/agent_course/
│   ├── agent.py
│   ├── model.py
│   ├── mock_model.py
│   ├── openai_compatible.py
│   ├── runtime.py
│   └── cli.py
├── tests/
├── docs/teaching-log.md
├── .env.example
├── README.md
└── pyproject.toml
```

## 第一阶段成功标准

- `python -m unittest discover -s tests -v` 通过。
- 不配置 API 密钥时，CLI 使用 Mock 模式并能返回确定性回答。
- 配置 OpenAI 兼容 API 环境变量后，CLI 将消息发送到 `/v1/chat/completions`，并解析标准文本回答。
- Agent Runtime 和模型客户端都可以在测试中替换，不依赖网络。
- 教学记录说明“LLM、Agent、Runtime、ModelClient”各自的职责，并包含一次真实的测试输出。

## 安全和可靠性边界

- API 密钥只从进程环境读取。
- HTTP 请求设置明确的超时时间。
- 远程响应必须是合法 JSON，并检查必要字段。
- 第一阶段不提供文件读写、Shell、网络搜索等高权限工具。
- 运行时对单次模型调用失败返回可理解的错误，不泄露请求头内容。

## 教学交互约定

每节课维护以下内容：概念、当前代码、一个实验、测试结果、容易混淆的地方和下一步问题。实现时优先保持代码短小，让每个类和函数都能对应到一个明确的概念。
