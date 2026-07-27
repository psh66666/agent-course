# Agent 教学项目第一阶段实现计划

## 目标

实现一个可离线运行、可切换 OpenAI 兼容 API 的最小 Agent 系统，并用测试展示模型客户端与 Agent Runtime 的职责边界。

## 架构

`AgentRuntime` 只管理一轮用户输入和一次模型响应；`ModelClient` 定义统一调用协议；`MockModel` 提供离线确定性响应；`OpenAICompatibleModel` 负责 Chat Completions HTTP 协议；CLI 负责配置读取和交互入口。

## 技术栈

- Python 3.13+
- 标准库 `dataclasses`、`json`、`urllib.request`、`unittest`
- OpenAI 兼容 `POST /v1/chat/completions`

## 任务

1. 创建 `pyproject.toml`、`README.md`、`.env.example` 和包初始化文件。
   预期结果：项目能够被 Python 解释器识别，文档说明离线运行命令和 API 配置项。

2. 编写 `tests/test_model.py` 的失败测试。
   预期结果：测试表达 Mock 模型返回确定性回答、Runtime 使用模型客户端，以及 API 客户端解析文本回答。

3. 运行 `python -m unittest discover -s tests -v`。
   预期结果：测试因目标模块和类尚不存在而失败，不能是测试代码语法错误。

4. 实现 `model.py` 中的消息类型、模型客户端协议和响应类型。
   预期结果：生产代码只定义跨模型实现共享的最小接口。

5. 实现 `mock_model.py` 和 `agent.py`。
   预期结果：Mock 模型返回固定回答；Runtime 将用户输入包装成消息并调用模型一次。

6. 实现 `openai_compatible.py`。
   预期结果：客户端拼接基础 URL，发送 JSON 请求，验证 HTTP 状态和响应结构，并提取首个 choice 的 message content。

7. 实现 `runtime.py` 和 `cli.py`。
   预期结果：没有 `MODEL_API_KEY` 时使用 Mock；存在完整 API 配置时使用真实客户端；配置不完整时给出明确错误。

8. 运行单元测试和离线 CLI 实验。
   预期结果：所有测试通过，CLI 能在无网络和无密钥状态下返回回答。

9. 更新 `docs/teaching-log.md`。
   预期结果：记录第一课的概念、目录、测试过程、实际命令输出和下一课问题。

10. 检查 Git 状态并提交第一阶段。
    预期结果：提交只包含 `agent-course` 内的教学项目文件，不包含任何密钥或工作区其他项目。
