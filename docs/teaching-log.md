# Agent 构建教学记录

## 项目约定

- 项目目录：`/Users/rm001/agent-course`
- 技术路线：Python + OpenAI 兼容 API + 离线 Mock 模式
- 教学方式：每节课先理解概念，再做一个小改动，并用测试或实验验证
- 提交方式：课堂过程先保存在本地，一节课结束后再统一提交并推送 GitHub
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

## 第一课完整课堂过程

### 过程 1：建立最小心智模型

#### 教师讲解

LLM 可以暂时看成一个函数：

```text
answer = model(messages)
```

它根据消息生成文本，但通常不知道程序有哪些工具、工具是否执行成功、是否需要继续下一步，以及什么时候应该停止。

Agent 是围绕模型构建的程序运行时：

```text
用户输入
  -> 程序组织消息
  -> 调用模型
  -> 程序判断下一步
  -> 继续调用模型、执行工具或结束
```

因此，Agent 不是模型本身，而是模型、运行时、状态、工具和控制规则的组合。

第一阶段故意只实现一次模型调用。它是完整 Agent 的最小骨架，还没有工具决策循环。

#### 学生需要掌握

- LLM 负责生成文本或决策候选。
- Runtime 负责控制程序流程。
- 只有模型调用时，系统还不能执行外部动作。
- “程序能够运行”和“答案一定正确”是两个不同问题。

### 过程 2：为什么抽象 `ModelClient`

#### 教师讲解

项目把模型访问抽象成 `ModelClient`：

```text
AgentRuntime -> ModelClient -> MockModel
                         -> OpenAICompatibleModel
                         -> 未来的其他模型客户端
```

Runtime 只依赖 `complete(messages)`，不依赖 HTTP、URL、请求头或某个供应商的 SDK。这样可以切换模型，也可以在测试中使用不联网的替身。

#### 学生回答

“HTTP 的请求也需要可以替换；对于 Agent 来说，只是工具，不是一定需要完成的流程。”

#### 教师纠正

前半句正确：HTTP 访问应该可以替换，`ModelClient` 就是模型供应商适配层。

后半句需要区分：`ModelClient` 不是工具。工具是 Agent 可以调用的外部能力，例如查询数据库、搜索网页或创建订单。HTTP 只是实现模型访问的一种方式，也可能是实现某个工具的一种方式，但两者在架构职责上不同。

简单问答可以没有工具；需要执行任务时，Runtime 才会让模型决定是否调用工具，并执行有边界的循环。

### 过程 3：当前 Agent 架构

#### 整体分层

```text
用户
  |
  v
CLI / API 入口
  |
  v
AgentRuntime  <---- TraceRecorder
  |
  +---- ModelClient ----> MockModel
  |                    -> OpenAICompatibleModel
  |
  +---- 下一阶段加入 ToolRegistry
                         |
                         +-> 具体工具函数
```

#### 模块职责

| 模块 | 当前职责 | 未来扩展 |
|---|---|---|
| `cli.py` | 读取配置、接收用户输入、输出回答 | Web/API 入口、会话管理 |
| `agent.py` | 暴露 `Agent` 这个公共名称 | 面向使用者的 Agent 配置 |
| `runtime.py` | 组织消息、调用模型、记录安全摘要 | 主循环、工具调用、停止条件、错误恢复 |
| `model.py` | 定义消息和模型客户端协议 | 工具调用、流式响应、结构化输出 |
| `mock_model.py` | 提供离线确定性模型 | 模拟工具决策和异常场景 |
| `openai_compatible.py` | 调用兼容 Chat Completions 的 API | 重试、流式输出、供应商差异适配 |
| `TraceRecorder` | 记录消息数量和响应长度 | 调试轨迹、指标和评估数据 |
| `tests/` | 验证模块边界和错误处理 | Agent 场景测试、回归测试 |

### 过程 4：`AgentRuntime` 是不是 Agent 的主循环

#### 当前答案

它是 Agent 的核心控制器，也是未来主循环的承载位置，但当前代码还没有真正的循环。现在的流程只有：

```python
messages = [system_message, user_message]
response = model.complete(messages)
return response.content
```

所以当前 `AgentRuntime` 更准确的名称是“单步 Runtime”。

#### 完整 Agent Runtime 的未来形态

```text
while not finished:
    response = model.complete(messages)

    if response is final answer:
        return answer

    if response requests a tool:
        validate tool name and arguments
        result = execute tool
        append tool result to messages
```

这个循环不能完全交给模型。模型可以提出调用建议，但程序必须负责工具白名单、参数校验、权限、最大步数、超时和错误处理。

### 过程 5：模型是否只是“查答案的函数”

#### 学生回答

“模型只是 Agent 用来查答案的函数，不会影响查答案的过程，哪怕答案是错的 Agent 也可以运行。”

#### 教师纠正

对于第一阶段的单步 Runtime，这个理解基本成立：模型只生成文本，Runtime 不验证事实正确性；即使回答错误，程序仍可能正常结束。

但在完整 Agent 中，模型不只是查答案。它还可能决定：

- 是否调用工具
- 调用哪个工具
- 传入什么参数
- 工具失败后是否重试
- 是否认为任务已经完成

因此模型会影响 Agent 的执行路径。模型答错和程序崩溃是不同的故障：前者是质量问题，后者是运行时问题。生产 Agent 必须通过工具白名单、参数校验、最大循环次数和人工审批等机制降低模型错误造成的风险。

### 当前阶段结论

你现在需要形成的核心判断是：

```text
模型负责提出文本或动作建议
Runtime 负责决定程序如何安全地执行
工具负责提供外部能力
```

下一步会用一个最简单的本地工具，把“模型提出工具调用”和“程序执行工具”这两个动作连接起来。

### 课堂问答：执行删除文件前需要检查什么

#### 教师问题

如果模型返回“请执行删除文件工具”，Runtime 在真正执行之前，必须检查哪些内容？

#### 学生回答

“确认文件是否存在，确认当前用户允许删除文件。”

#### 教师补充

回答正确地覆盖了目标有效性和权限边界。完整检查还应包括：

- 工具是否在允许调用的白名单中
- 参数是否符合 schema，例如路径是不是字符串
- 路径是否落在允许操作的目录内，是否包含路径穿越
- 当前进程是否真的拥有操作系统权限
- 删除是否属于需要用户二次确认的高风险动作
- 是否记录审计信息，并设置超时和失败处理

文件不存在时可以选择返回明确的“文件不存在”，也可以把删除设计成幂等操作；这属于工具契约，而不是简单地交给模型决定。

由此得到工具执行原则：模型只能提出调用请求，Runtime 和工具实现必须在执行前完成验证，不能因为模型要求了某个动作就直接执行。

### 课堂问答：为什么需要工具白名单和参数校验

#### 教师问题

为什么不能只依赖操作系统权限，而还需要 Agent 自己的工具白名单和参数校验？

#### 学生回答

“工具白名单保证了能力边界，防止安全问题；参数校验确保工具可以正确使用。”

#### 教师确认

回答完整。操作系统权限只能说明进程在技术上能不能执行某个动作，不能说明产品是否允许 Agent 具备这个能力，也不能保证模型传入的参数符合业务规则。工具白名单解决“允许调用哪些能力”，参数校验解决“这次调用是否合理”，二者共同构成 Runtime 的第一层安全边界。

### 第一课阶段性结论

第一课已经建立了四个基础判断：

1. LLM 是生成文本或动作建议的组件，不等于 Agent。
2. `AgentRuntime` 是 Agent 控制流程的核心；当前版本还是单步 Runtime。
3. `ModelClient` 是模型适配层，不是工具。
4. 模型提出工具请求后，Runtime 必须通过白名单、参数、权限和确认机制控制执行。

下一课将在当前项目中实现第一个本地工具和工具注册表，把这些概念变成可运行的代码。

## 第二课：工具契约与工具注册表

### 本节目标

理解工具不是一段随意执行的函数，而是一个拥有名称、描述、参数契约、执行器和结果边界的受控能力。

### 过程 1：工具是什么

工具是 Agent 可以请求程序执行的外部能力。一个工具至少需要描述：

```text
name        工具名称
description 工具用途
parameters  参数 schema
handler     实际执行函数
result      标准化结果或错误
```

例如课程项目可以提供一个本地 `lookup_topic` 工具：

```json
{
  "name": "lookup_topic",
  "description": "Look up a known concept from the course notes.",
  "parameters": {
    "type": "object",
    "properties": {
      "topic": {"type": "string"}
    },
    "required": ["topic"]
  }
}
```

这里的 JSON 描述是工具契约。它告诉模型“可以请求什么”和“参数长什么样”，但不会让模型直接执行 Python 函数。

### 过程 2：模型和工具的边界

模型可能返回一个抽象的工具请求：

```json
{
  "type": "tool_call",
  "name": "lookup_topic",
  "arguments": {"topic": "Agent"}
}
```

这个请求是不可信输入。Runtime 必须先检查工具名称、参数 schema 和权限，再交给对应 handler。模型永远不应该直接获得 Python 函数、Shell 或文件系统的执行权。

### 过程 3：工具注册表

工具注册表可以看作受控映射：

```text
"lookup_topic" -> ToolDefinition -> lookup_topic handler
```

它集中负责注册工具、查询工具、拒绝未知工具和调用已验证的 handler。这样 Runtime 不需要把每个工具写死在主循环里，也能保持工具白名单清晰可见。

### 当前问题

为什么工具需要参数 schema，而不能只给模型一个工具名称和一段自然语言描述？

### 课堂问答：为什么需要参数 schema

#### 学生回答

“因为工具想要能正确调用，给出的参数格式都要匹配；但是自然语言描述的工具会导致模型输出存在问题，导致工具不能被正常使用。”

#### 教师确认

回答正确。自然语言适合解释工具用途，但不适合作为唯一的机器可验证契约。参数 schema 将调用要求结构化，使 Runtime 能检查必填字段、类型和基本形状。

还要注意：schema 只能约束格式，不能保证模型选择了正确工具，也不能保证参数符合所有业务规则。即使 JSON 结构合法，Runtime 仍需要检查工具白名单、权限和业务约束；必要时可以拒绝、重试或请求用户确认。

当前项目的 OpenAI 兼容客户端还没有把工具 schema 发送给模型，下一步会先实现本地 `ToolDefinition` 和 `ToolRegistry`，再把工具调用接入模型循环。

### 课堂问答：模型请求未知工具时如何处理

#### 教师问题

如果模型传来的参数格式完全合法，但工具名称是系统中不存在的工具，Runtime 应该怎么处理？

#### 学生回答

“需要给出找不到对应工具的回答，要求模型重新选择工具。”

#### 教师补充

方向正确，但错误处理应该分两层：Runtime 先生成结构化的 `tool_not_found` 错误，并把错误结果返回给模型，让模型在上下文中重新选择；Runtime 同时递增重试次数并设置上限。如果模型反复请求未知工具，程序应该停止循环并返回明确错误，或升级给用户/人工处理，不能无限重试。

```text
未知工具
  -> Runtime 拒绝执行
  -> 返回结构化错误给模型
  -> 有界重试
  -> 仍失败则结束或升级
```

### 课堂问答：为什么需要 `ToolRegistry`

#### 教师问题

为什么要设计 `ToolRegistry`，而不是直接在 `AgentRuntime` 里写很多个 `if tool_name == ...`？

#### 学生回答

“这样会导致添加新的工具困难，同时还需要在主循环里不断判断是否调用了每个工具。”

#### 教师确认

回答正确。把工具判断全部写进主循环会让编排逻辑和业务能力耦合，工具越多，主循环越难阅读、测试和修改。注册表把工具名称映射到工具定义和 handler，Runtime 只负责统一的查找、校验、执行和错误处理。

这体现了一个重要架构原则：新增一个工具应该主要新增工具定义和注册动作，而不是修改已经稳定的主循环。

## 第二课设计：第一个本地工具

### 选择的工具

实现一个无网络的 `lookup_topic` 工具，从固定的课程知识字典中查询概念。它没有文件写入、Shell 或外部网络能力，适合第一次学习工具调用。

### 计划中的组件

```text
ToolDefinition
  - name
  - description
  - parameters schema
  - handler

ToolRegistry
  - register
  - get
  - execute
```

### 第一条实现边界

先实现工具定义、注册、未知工具错误和参数校验，不立即接入真实模型。先让 Python 测试直接验证工具契约，再把它接入 Agent Runtime 循环。

### 过程 4：TDD 实现结果

#### 红灯阶段

先添加 `tests/test_tools.py`，测试正常调用、未知工具、缺少参数、错误类型和重复注册。生产模块尚不存在时，测试因无法导入 `course_tools` 而失败，确认测试确实覆盖了待实现能力。

#### 绿灯阶段

新增：

- `tools.py`：定义 `ToolDefinition`、`ToolResult` 和 `ToolRegistry`
- `course_tools.py`：定义课程知识字典、`lookup_topic` handler 和默认注册表

`ToolRegistry.execute()` 统一返回 `ToolResult`。未知工具和非法参数不会直接让程序崩溃，而是返回错误码和可交给模型的错误内容。

#### 实验结果

```text
ToolResult(ok=True, content='Agent 是由模型、Runtime、状态、工具和控制规则组成的系统。', error_code=None)
ToolResult(ok=False, content="No tool named 'unknown' is registered.", error_code='tool_not_found')
ToolResult(ok=False, content='Missing required argument: topic.', error_code='invalid_arguments')
```

`PYTHONPATH=src python3 -m unittest discover -s tests -v` 当前返回 `Ran 23 tests` 和 `OK`。本节新增的 12 个测试只验证工具层，尚未把模型输出接入工具循环。

### 过程 5：当前代码边界

当前可以由 Python 程序直接调用：

```python
registry.execute("lookup_topic", {"topic": "Agent"})
```

但用户对话还不能让模型自动触发这个工具，因为 `AgentRuntime` 目前只解析文本回答，`OpenAICompatibleModel` 也还没有发送工具 schema。下一步要解决的是：模型如何表达工具调用，以及 Runtime 如何在模型响应和工具结果之间循环。

### 过程 6：注册边界与执行错误修复

回归审查发现，`ToolRegistry.register()` 之前只检查工具名称和重复注册，非法 schema 会被保存下来，直到执行时才可能因为 `properties` 不是对象而抛异常；未实现的 schema 类型也会被静默接受。

修复后，注册阶段明确限制当前实现支持的 schema 子集：顶层必须是 `object`，属性类型只允许 `string`、`number` 和 `boolean`，并拒绝未实现的 schema 字段。执行阶段继续把额外参数、handler 异常和非文本返回值转换为结构化错误结果。

新增回归测试覆盖非法顶层 schema、非法属性 schema、空工具名称、额外参数、handler 异常和非文本结果。工具注册失败发生在进入白名单之前，因此坏工具不会污染注册表。

用户理解：HTTP 请求需要可以替换，而且不是每个 Agent 流程都必须依赖工具。

教师补充：前半句正确。`ModelClient` 把模型供应商和 HTTP 细节隔离出来，方便切换真实模型、Mock 模型和测试替身。后半句需要区分：工具不是 HTTP 请求本身，而是 Agent 可以调用的外部能力，例如查询订单或读取数据库。简单问答可以没有工具，但需要工具执行任务时，Runtime 才会进入模型决策和程序执行之间的循环。
