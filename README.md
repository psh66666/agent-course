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
