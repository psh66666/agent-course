# Agent 构建教学记录

## 项目约定

- 项目目录：`/Users/rm001/agent-course`
- 技术路线：Python + OpenAI 兼容 API + 离线 Mock 模式
- 教学方式：每节课先理解概念，再做一个小改动，并用测试或实验验证
- 提交方式：课堂过程先保存在本地，一节课结束后再统一提交并推送 GitHub
- 当前阶段：第三课

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

## 第二课结束复盘

第二课完成了第一个本地工具和工具注册表。当前代码可以由程序直接调用 `lookup_topic`，但模型还不能自动请求工具；这正是下一课要解决的边界。

第二课最终实现了：

- `ToolDefinition`：描述工具契约和 handler
- `ToolRegistry`：管理白名单、schema 校验、执行和结构化错误
- `lookup_topic`：完全离线的课程知识查询工具
- 注册阶段的 schema 边界：顶层 `object`，属性只允许 `string`、`number`、`boolean`

第二课共通过 23 个测试，提交 `2977b78` 已推送到公开仓库。当前仍未把工具 schema 发送给模型，也未把工具结果接回模型消息。

## 第三课：工具调用循环

### 本节目标

让模型能够用结构化结果表达“我要调用哪个工具、参数是什么”，让 Runtime 执行工具后把结果放回消息，再决定结束还是继续调用模型。

### 当前代码缺口

现在的 `ModelResponse` 只有一个文本字段：

```python
ModelResponse(content: str)
```

它能表示最终回答，却不能可靠地区分下面两种情况：

```text
这是给用户的最终回答
请调用 lookup_topic，参数是 Agent
```

如果 Runtime 依赖字符串解析来判断第二种情况，就会把自然语言、格式错误和真正的工具请求混在一起。第三课首先要设计一个明确的模型响应协议。

### 目标流程

```text
用户问题
  -> Runtime 请求模型
  -> 模型返回 final answer 或 tool call
  -> Runtime 校验并执行 ToolRegistry
  -> 把 tool result 追加到消息
  -> 再次请求模型
  -> final answer 或达到最大步数后结束
```

循环的控制权仍然属于 Runtime。模型只能提出工具请求，不能直接获得 Python 函数；Runtime 必须设置最大步数，并处理未知工具、非法参数和工具执行失败。

### 第一个问题

如果模型只返回一段文本：`请调用 lookup_topic，参数是 Agent`，为什么 Runtime 不应该直接用字符串解析来决定是否执行工具？

### 课堂问答：为什么不能直接解析模型文本

#### 学生回答

“只解析字符串会不会出现误判？而且这样的方式让模型的输出毫无约束，会导致很多工程问题；同时也没法保证可以正确调用工具。”

#### 教师确认

回答正确。字符串解析至少有四类风险：

1. **语义误判**：模型可能是在解释“如何调用工具”，而不是请求 Runtime 真正执行工具；也可能在普通回答中偶然出现工具名称。
2. **格式不稳定**：同一个请求可能被写成自然语言、JSON、Markdown 代码块或带额外解释的混合文本，解析器会越来越复杂。
3. **契约不明确**：没有稳定字段来区分工具名称、参数、最终回答和错误信息，Runtime 很难可靠地决定下一步。
4. **工程边界变差**：无法稳定做 schema 校验、错误恢复、日志记录和重试控制，模型输出的微小变化都可能破坏执行流程。

结构化响应可以明确表达：

```text
final answer
或
tool call:
  name: lookup_topic
  arguments: {topic: Agent}
```

但还要注意：结构化格式只能解决“如何表达请求”，不能保证模型一定选择了正确工具，也不能保证参数符合业务规则。后两项仍然必须由 Runtime 和 ToolRegistry 校验。

#### 当前结论

```text
自然语言文本 -> 适合给用户阅读
结构化 ToolCall -> 适合给程序执行
ToolRegistry -> 决定请求是否真的允许执行
```

### 第三课下一个问题

如果要设计一个结构化的 `ToolCall`，你认为它至少需要包含哪些字段？

### 课堂问答：`ToolCall` 应该包含什么

#### 学生回答

“包含工具名称、工具说明、工具调用规范、工具权限要求。”

#### 教师纠正

回答里包含了两个不同层次的对象。工具说明、调用规范和权限要求主要属于注册阶段的 `ToolDefinition`，而不是模型每次请求时生成的 `ToolCall`。

可以这样区分：

```text
ToolDefinition（系统注册）
  - name
  - description
  - parameters schema
  - permission policy
  - handler

ToolCall（模型请求）
  - name
  - arguments
  - call_id（可选，但便于关联请求和结果）
```

`ToolDefinition` 是系统预先建立的可信契约，决定工具是什么、参数应该怎样写、是否允许执行以及实际调用哪个 handler。模型可以看到其中适合用于决策的名称、描述和参数 schema，但不能通过请求自行声明权限或替换 handler。

`ToolCall` 是模型针对某一次任务提出的请求。它只需要说明“想调用哪个已注册工具”和“这次传入什么参数”。Runtime 收到后，仍然要根据注册表中的 `ToolDefinition` 重新检查 schema、白名单、权限和业务规则。

因此不能把权限要求放在模型请求里当作可信信息：模型可以声称“我有权限”，但这不等于系统真的授予了权限。

#### 当前结论

```text
ToolDefinition = 系统定义的能力和约束
ToolCall       = 模型提出的一次调用请求
ToolResult     = 程序执行后返回的标准化结果
```

### 第三课下一个问题

如果模型在 `ToolCall` 中请求了一个未注册的工具，Runtime 应该相信模型提供的工具说明和权限要求，还是只相信本地 `ToolRegistry`？为什么？

### 课堂问答：谁是工具能力的事实来源

#### 学生回答

“只能相信 `ToolRegistry`，因为这才是用户决定和要求的；模型的请求可以拒绝。”

#### 教师确认

回答正确。`ToolCall` 是模型生成的不可信输入，不能因为模型在请求中附带了工具说明、权限声明或新的工具名称，就扩大系统实际拥有的能力。

Runtime 应该只根据本地 `ToolRegistry` 判断：

- 工具名称是否在白名单中
- 参数是否符合注册时的 schema
- 当前调用是否满足权限和业务规则
- 是否需要用户确认

未知工具应被拒绝，并返回结构化的 `tool_not_found` 结果。Runtime 可以把这个错误反馈给模型，让模型重新选择，但必须设置最大重试次数；模型不能通过反复请求未知工具来改变白名单。

#### 当前结论

```text
模型：提出请求
Registry：定义能力边界
Runtime：执行安全检查并决定是否执行
用户/业务规则：决定高风险动作是否需要额外确认
```

### 第三课下一个问题

如果工具 handler 执行时抛出异常，Runtime 应该让异常直接传给上层，还是转换成结构化的 `ToolResult`？为什么？

### 课堂问答：工具异常如何返回

#### 学生回答

“肯定需要 `ToolResult`，这样可以看到工具运行的具体错误。”

#### 教师确认与补充

回答正确。工具异常不应该直接穿过 Runtime，因为那会让一次可预期的工具失败变成整个 Agent 流程的崩溃，也无法让模型在上下文中判断应该重试、换工具还是向用户说明失败。

结构化结果至少应该表达：

```text
ok: false
error_code: tool_execution_error
content: 安全、可供模型理解的错误消息
```

但“具体错误”需要分层处理。异常原文可能包含文件路径、内部模块名、凭据或其他敏感信息，不能未经筛选直接返回给模型或用户。Runtime 可以把异常原文和堆栈写入受控日志，同时向模型返回稳定的错误码和安全消息。

例如：

```text
内部日志：PermissionError('/private/secret.txt')
ToolResult：ok=False, error_code='tool_execution_error'
            content='The tool could not complete the requested operation.'
```

#### 当前结论

```text
handler 异常
  -> Runtime 捕获
  -> 记录受控诊断信息
  -> 返回结构化、安全的 ToolResult
  -> 模型决定重试、换工具或结束
```

### 第三课下一个问题

如果你来设计 `ToolResult`，除了 `ok` 和错误消息之外，你认为还应该有哪些字段？

### 课堂问答：`ToolResult` 是否需要工具调用结果

#### 学生回答

“还需要具体工具调用结果？”

#### 教师确认

是的，这是 `ToolResult` 的核心字段之一。只有 `ok=True` 而没有实际结果，模型无法根据工具执行结果继续工作；只有错误消息而没有结果，也无法表示成功调用返回的数据。

当前项目把这个字段统一命名为 `content`，类型暂时是字符串：

```python
ToolResult(
    ok=True,
    content="Agent 是由模型、Runtime、状态、工具和控制规则组成的系统。",
)
```

一个完整的工具结果通常可以分为：

```text
ok          是否执行成功
content     成功时的实际结果，失败时的安全错误消息
error_code  失败时的稳定错误分类
call_id     可选，用于关联某次 ToolCall 和 ToolResult
```

`tool_name` 也可以放在调用外层的消息中，用来说明结果属于哪个工具。当前课程先保持最小设计，只使用 `ok`、`content` 和可选的 `error_code`；等接入模型循环时，再讨论 `call_id` 和结构化结果格式。

#### 当前结论

```text
ToolCall   -> 请求调用
ToolResult -> 返回执行结果或安全错误
```

### 第三课下一个问题

当前 `ToolResult.content` 只能是字符串。你认为工具返回字符串有什么优点和限制？

### 课堂问答：工具结果为什么暂时使用字符串

#### 学生回答

“优点是格式明确，返回的信息确定；但是如果错误没有定义或者出现其他特殊情况，返回的信息不够灵活，会导致模型无法判断问题。”

#### 教师确认与补充

判断正确。字符串结果的优点是接口简单、容易打印和记录，也容易直接放进模型上下文；对于 `lookup_topic` 这种只返回一段课程说明的工具，字符串足够清楚。

限制也很明显：

- 程序无法可靠区分多个字段，例如数据、状态、来源和分页信息
- 数字、布尔值、列表等类型会被压成文本，后续代码还要重新解析
- 只有自然语言错误时，Runtime 很难稳定判断是权限失败、参数失败还是临时失败
- 工具返回特殊情况时，模型可能只能依靠猜测文本含义

`error_code` 可以补足一部分错误分类，但它不能替代成功结果的结构。更成熟的设计通常让工具返回结构化数据，再由 Runtime 序列化成模型可读的消息，同时保留机器可判断的字段。

例如：

```json
{
  "ok": true,
  "data": {
    "topic": "agent",
    "content": "Agent 是由模型、Runtime、状态、工具和控制规则组成的系统。"
  },
  "error_code": null
}
```

当前课程保留字符串，是为了先学习最小契约和调用循环；并不代表所有生产工具都应该只返回字符串。

### 第三课下一个问题

对于当前的 `lookup_topic`，你会选择继续返回字符串，还是改成包含 `topic` 和 `content` 的结构化对象？为什么？

### 教学方式调整：理论、集中问题与实践

#### 学生反馈

学生询问 `lookup_topic` 的含义，并指出当前提问过于频繁。期望的教学顺序是：先完整讲解基础理论，再集中提出多个问题由学生一次回答，最后进入代码实践。

#### 教师调整

后续每个主题采用三个阶段：

1. **理论讲解**：先建立完整的概念、职责边界和流程图。
2. **集中检查**：一次提出一组由浅入深的问题，学生可以一起回答，教师统一纠正和总结。
3. **代码实践**：理论和问题确认后，再通过 TDD 修改项目并验证结果。

不再在每个小问题后立即中断讲解。课堂记录仍然保留完整的讲解、学生回答、教师反馈和实验结果。

### `lookup_topic` 的含义

`lookup_topic` 是第二课选择的第一个本地工具，名字可以理解为“查询课程主题”。它不访问网络、不读写文件，也不执行 Shell，只从 `course_tools.py` 中固定的 `COURSE_TOPICS` 字典查找课程概念。

调用方式是：

```python
registry.execute("lookup_topic", {"topic": "Agent"})
```

执行路径是：

```text
调用方
  -> ToolRegistry 根据名称找到 lookup_topic
  -> 校验 topic 必须存在且是字符串
  -> lookup_topic 查询 COURSE_TOPICS
  -> 返回 ToolResult
```

例如 `topic` 为 `Agent` 时，工具返回关于 Agent 的课程说明；如果主题不存在，则返回没有找到课程笔记的文本。它的教学价值不是功能复杂，而是用最小风险展示完整工具契约：名称、描述、参数 schema、handler 和结果。

### 集中检查结果：第三课理论

#### 学生回答

学生回答：`lookup_topic` 是工具定义；`ToolCall` 是模型调用工具的请求，`ToolDefinition` 是提前给工具的定义；`ToolResult` 帮助模型判断工具调用是否完成并提供调用结果；Runtime 必须设置最大循环步数，避免工具调用失败后模型不断请求而形成循环。

#### 教师反馈

后三个判断正确。需要精确区分 `lookup_topic` 这个名字在不同语境中的含义：

```text
"lookup_topic" 注册名 -> ToolDefinition.name
lookup_topic 函数     -> 实际 handler / 工具执行器
整个 ToolDefinition   -> 名称、描述、schema、权限和 handler 的完整定义
```

`ToolCall` 是模型针对一次任务提出的请求；`ToolDefinition` 是系统预先注册的可信契约；`ToolResult` 把成功数据或安全错误交回上下文；最大步数则是 Runtime 防止死循环的控制边界。

#### 理论阶段结论

第三课已经完成理论讲解和集中检查，下一步进入代码实践。实践仍然只使用离线 Mock 和本地工具，不接入真实网络模型。

### 第三课代码实践设计

#### 目标

让 Runtime 能处理两种模型响应：最终文本回答，或者结构化工具调用。

#### 计划改动

1. 在模型协议层增加结构化的 `ToolCall`。
2. 让 `ModelResponse` 能表达 final answer 或 tool call。
3. 给 `AgentRuntime` 注入可选的 `ToolRegistry`，执行有最大步数的循环。
4. 用可控的 Fake/Mock 模型测试：最终回答、成功工具调用、未知工具、非法参数、handler 失败和达到最大步数。
5. 保持 `OpenAICompatibleModel` 的网络适配范围清晰，先不假设真实供应商的工具调用格式已经统一。

#### TDD 顺序

```text
先写失败测试
  -> 定义最小响应协议
  -> 实现一次工具调用循环
  -> 补齐错误和最大步数边界
  -> 全量验证
```

### 第三课代码实践：TDD 过程

#### 红灯阶段

先在 `tests/test_agent.py` 增加结构化工具调用测试。第一次运行时，测试因为 `ToolCall` 尚不存在而无法导入；补上响应类型后，测试继续因为 `AgentRuntime` 不接受 `tool_registry` 而失败。两次失败都对应真实的生产代码缺口，而不是测试环境问题。

#### 绿灯阶段

本轮实现了四个部分：

1. **模型响应协议**：`ToolCall` 保存工具名称、参数和可选 `call_id`；`ModelResponse` 现在必须二选一地包含最终文本或工具调用，不能两者都没有或同时存在。
2. **消息元数据**：`Message` 增加可选的 `name` 和 `tool_call_id`，工具结果可以标记来源并和请求关联。
3. **有界 Runtime 循环**：`AgentRuntime` 每一步请求模型；遇到 final content 就返回，遇到 tool call 就调用 `ToolRegistry`，把 JSON 序列化的 `ToolResult` 作为 `role="tool"` 消息加入上下文，然后继续请求模型。
4. **安全停止**：`max_steps` 必须为正数；模型持续请求工具时达到上限后返回明确停止信息。没有 Registry 时不会执行工具，而是生成 `tools_unavailable` 结果。

#### 测试结果

新增测试覆盖成功工具调用、未知工具结果回传和最大步数停止。完整测试从第二课的 23 个增加到 26 个，`PYTHONPATH=src python3 -m unittest discover -s tests -v` 返回 `Ran 26 tests` 和 `OK`。

#### 当前边界

本轮只完成本地结构化响应和离线 Runtime 循环。`OpenAICompatibleModel` 现在可以保留 tool 消息的元数据，但仍只解析文本型供应商响应，还没有把工具 schema 发送给真实模型，也没有解析真实供应商的 `tool_calls` 字段；这些属于后续的供应商协议适配课题。

### 代码阅读重点

可以按这个顺序阅读本轮实现：

```text
model.py: ToolCall / ModelResponse
  -> runtime.py: AgentRuntime.respond
  -> tools.py: ToolRegistry.execute
  -> runtime.py: _serialize_tool_result
  -> Message(role="tool") 返回模型上下文
```

### 教学纠偏：代码实现必须被完整讲解

#### 学生反馈

学生指出：代码已经被修改和提交，但教师只给了实现摘要，没有逐段讲解代码，也没有真正带着学生完成实践。

#### 教师调整

这次反馈成立。代码实践不等于代码已经写完；教学还必须包括：

- 按模块解释新增代码和数据流
- 运行一个可观察的完整实验
- 说明测试如何验证每个边界
- 给学生一个可以独立修改和验证的练习

后续先完成这四步，再进入下一课或提交新的代码。

### 实验结果：错误参数被模型处理

实践示例把 `topic` 改为整数 `123` 后，输出为：

```text
ToolResult: ok=false, error_code=invalid_arguments
最终回答：工具参数错误，topic 必须是字符串。
```

这证明参数错误没有直接抛出，而是经过 `ToolRegistry`、Runtime 和 `role="tool"` 消息回到模型，再由示例模型生成最终回答。期间还通过调整缩进修复了 `UnboundLocalError`：读取 `tool_result` 的代码必须位于 `role == "tool"` 分支内部。

### 分步实践步骤：使用通用成功标志

当前示例根据具体错误码判断：

```python
if tool_result["error_code"] == "invalid_arguments":
```

下一步练习是改为根据通用状态判断：

```python
if not tool_result["ok"]:
```

这样同一段逻辑也能处理未来的 `tool_not_found`、`tool_execution_error` 等失败类型。

学生完成了这一行代码的泛化修改，运行输出保持不变。教师说明：输入仍然产生 `ok=False`，所以行为不应改变；变化在于错误判断不再绑定单一 `error_code`。

学生随后将 `topic` 改回字符串 `"Agent"`，验证成功分支：`ToolResult.ok=True`，结果内容包含 Agent 课程说明，且不会进入错误处理。

### 分步实践步骤：让模型读取成功结果

当前示例的第二次模型响应仍然是预先写死的：

```python
ModelResponse(content="这是模型根据工具结果生成的最终回答。")
```

下一步让 `DemoModel.complete()` 在 `role="tool"` 分支中读取成功结果：错误时返回错误说明，成功时返回：

```python
return ModelResponse(
    content=f"查询结果：{tool_result['content']}"
)
```

这样可以证明模型确实消费了工具结果，而不是只完成了 Runtime 的消息传递。

### 第三课结课

学生完成了本地工具循环的完整实践：正常工具调用、参数错误、结构化错误回传和成功结果消费。完整测试达到 27 个，正式改动提交为 `26400a9` 并推送到 GitHub。`examples/` 是学生亲手创建的本地实践目录，暂不纳入正式提交。

## 第四课：真实模型的工具协议

### 本节目标

理解本地 `ToolCall` 如何与真实模型供应商的 JSON 协议连接起来，并明确 Provider Adapter、Runtime 和 ToolRegistry 的职责边界。

### 第三课留下的边界

第三课的 `ScriptedModel` 可以直接构造 Python 对象：

```python
ModelResponse(
    tool_call=ToolCall(
        name="lookup_topic",
        arguments={"topic": "Agent"},
    )
)
```

真实模型不会直接返回 Python 对象，而是通过 HTTP 返回 JSON。模型供应商通常会在响应中表达类似的信息：

```json
{
  "message": {
    "content": null,
    "tool_calls": [
      {
        "id": "call-1",
        "function": {
          "name": "lookup_topic",
          "arguments": "{\"topic\": \"Agent\"}"
        }
      }
    ]
  }
}
```

这里的 `arguments` 甚至可能是 JSON 字符串，而不是已经解析好的对象。Provider Adapter 需要把供应商格式转换成内部 `ToolCall`；Runtime 不应该知道供应商字段名和 HTTP 响应细节。

### 四层职责

```text
OpenAICompatibleModel
  -> 发送工具定义，解析供应商 JSON
  -> 转换为内部 ModelResponse / ToolCall

AgentRuntime
  -> 控制模型、工具和结果之间的有界循环

ToolRegistry
  -> 校验工具名称、参数 schema 和执行边界

具体 handler
  -> 执行实际业务能力
```

### 重要安全边界

真实模型返回的 `tool_calls` 仍然是不可信输入。Adapter 负责解析格式，不能因为 JSON 能解析就认为请求合法；Runtime 和 Registry 仍然必须执行白名单、schema、权限、确认和最大步数检查。

### 集中检查问题

1. 为什么不能让 `OpenAICompatibleModel` 直接调用 `ToolRegistry`，而要把工具调用交给 Runtime？
2. 如果供应商返回的 `arguments` 不是合法 JSON，应该在哪一层处理？应该如何反馈？
3. 为什么“供应商 JSON 解析成功”仍然不代表工具可以执行？

### 集中检查结果：真实模型协议的职责边界

#### 学生回答

1. “因为 `OpenAICompatibleModel` 本质上还是模型返回的内容，不可信。”
2. “应该在 `ToolRegistry` 处理。”
3. “还是需要判断权限问题。”

#### 教师反馈

第 3 点正确，但还需要补充白名单、schema、业务规则和用户确认。第 1、2 点需要区分“谁不可信”和“哪一层负责什么”：

- 模型返回的 tool-call 数据是不可信输入，但 `OpenAICompatibleModel` 是供应商协议适配器，不是模型本身。
- `OpenAICompatibleModel` 负责 HTTP、供应商 JSON 解析和内部 `ToolCall` 转换，不应该直接调用 `ToolRegistry`。
- `ToolRegistry` 接收已经解析出的工具名称和参数对象，再负责白名单、schema 和执行边界。
- 如果 `arguments` 不是合法 JSON，首先应由适配层发现并转换成结构化的无效工具请求；Runtime 决定是否把错误反馈给模型或结束流程。

正确的数据流是：

```text
供应商 JSON
  -> Adapter 解析和归一化
  -> 内部 ToolCall
  -> Runtime 编排
  -> ToolRegistry 校验和执行
```

#### 理论阶段结论

供应商协议解析、Runtime 编排和工具安全校验是三个不同职责，不能因为它们都处理“工具调用”就合并到一个模块。

### 第四课代码实践：第一步

先增加一个测试，固定供应商返回 `tool_calls` 时，客户端应该转换出内部 `ToolCall`。当前生产代码只支持文本响应，因此这个测试应先红灯；下一步再实现最小解析逻辑。

### 第四课代码实践：解析供应商 tool call

#### 红灯与实现

学生先增加了供应商返回 `tool_calls` 的测试。原实现只接受文本 `content`，在 `content=None` 时抛出 `ModelClientError`，确认适配能力缺失。

随后学生在 `OpenAICompatibleModel` 中补上：

```text
读取 HTTP response_body
  -> 解析 choices[0].message
  -> 检查 tool_calls
  -> 解析 function.arguments JSON 字符串
  -> 转换为内部 ToolCall
```

适配器当前明确限制一次响应只能包含一个 tool call，因为内部 `ModelResponse` 目前只有单个 `tool_call` 字段；遇到多个调用或错误形状会返回受控的 `ModelClientError`，不会静默丢弃调用。

#### 错误边界测试

学生增加了 `arguments="not-json"` 的测试。非法 arguments 在 Provider Adapter 层被拒绝，确认坏 JSON 不会继续传给 `ToolRegistry`。

#### 验证

完整测试返回 `Ran 29 tests` 和 `OK`，同时通过 `compileall` 与 `git diff --check`。过程中的缩进和缺失 `response_body` 问题属于手写实现时的结构错误，已通过错误信息定位并修复。

### 第四课下一阶段：把工具定义发送给模型

现在客户端能够解析模型发来的 tool call，但请求 payload 仍然没有工具清单。真实模型不知道 `lookup_topic` 的名称、描述和参数 schema，也就没有可靠依据主动调用它。

请求方向需要公开工具的可调用部分：

```json
{
  "type": "function",
  "function": {
    "name": "lookup_topic",
    "description": "Look up a known concept from the course notes.",
    "parameters": {"type": "object"}
  }
}
```

`handler`、权限策略和其他内部实现不能发送给模型。它们只保留在本地 Registry，继续构成执行安全边界。

### 集中检查问题：请求方向

1. 为什么 HTTP 请求中的工具定义只应发送名称、描述和参数 schema，而不能发送 handler？
2. Runtime 应该从哪里取得要发送给模型的工具清单，为什么不能让模型自行声明？
3. 如果 Registry 没有任何工具，HTTP payload 应该包含空 `tools` 数组，还是省略 `tools` 字段？请说明你的选择和理由。

### 集中检查结果：工具定义发送边界

#### 学生回答

1. “把 handler 发送进去模型就可以绕过审查直接调用工具了。”
2. “Runtime 应该去工具定义里找。”
3. “发送空 tools 数组，告诉模型没有工具可以调用。”

#### 教师反馈

第 2 点正确：Runtime 应从本地 `ToolRegistry` 的已注册工具中取得清单，模型不能声明新工具，否则模型可以尝试扩大系统能力。

第 1 点需要补充：handler 是本地 Python 可执行对象，既不能序列化成供应商 JSON，也不应向模型暴露内部实现、权限规则或可执行入口。即使模型知道工具名称，它仍只能提出请求；Runtime 和 Registry 才能调用 handler。

第 3 点的“告诉模型没有工具”意图正确，但当前课程选择在没有工具时省略 `tools` 字段。原因是没有工具协议时不需要发送该字段，且不同 OpenAI 兼容供应商对空数组的行为未必一致。模型仍可根据缺少工具定义得知本次请求没有可调用工具。

#### 理论阶段结论

HTTP 中只发送工具的公开契约：名称、描述和参数 schema。本地 Registry 是工具能力的唯一事实来源；handler、权限和业务规则永不离开本地进程。

### 第四课代码实践：请求 payload 测试

下一步先为“有 Registry 时发送 `tools`，无 Registry 时省略 `tools`”写测试，再修改 ModelClient/Runtime/Provider Adapter 的参数传递。

### 第四课代码实践：发送工具定义

学生先增加 Provider Adapter 的请求测试，确认有工具时 payload 包含公开的 `tools` schema，已有文本请求测试同时断言无工具时省略该字段。测试先因 `complete()` 不接受 `tools` 参数而红灯。

学生随后扩展 `OpenAICompatibleModel.complete()`：接受可选 tools，只有工具非空时才在 payload 加入序列化的公开工具定义。序列化只包含 `name`、`description` 和 `parameters`，不包含 handler。

完整测试达到 30 个且全部通过。当前完成的是 Adapter 的发送能力；Runtime 还没有把本地 Registry 的工具列表传给模型，这是下一步要连接的边界。

### 第四课下一步：Runtime 传递工具清单

下一条测试将验证：Agent 持有 Registry 时，模型客户端能收到 Registry 的已注册工具；没有 Registry 时，模型客户端应收到空清单，最终由 Adapter 省略 `tools` 字段。

### 第四课代码实践：Runtime 传递工具清单

学生先写入 Runtime 传递工具清单的测试。测试使用 `ToolRecordingModel` 记录 `complete()` 的 `tools` 参数；初始结果为空列表，确认 Runtime 尚未从 Registry 提取工具定义。

随后完成接口传播：

```text
ToolRegistry.definitions
  -> AgentRuntime.respond
  -> ModelClient.complete(..., tools=...)
  -> OpenAICompatibleModel.complete
  -> HTTP payload.tools
```

`ToolRegistry.definitions` 返回注册工具的只读元组。Runtime 有 Registry 时传入该元组，没有 Registry 时传入空元组；Adapter 继续负责在空清单时省略 HTTP `tools` 字段。Mock 和测试替身也接受相同的可选参数，保证协议替换和离线测试不受影响。

### 第四课结课

本课实现了真实模型工具协议的双向适配：请求时发送公开工具契约，响应时解析供应商 `tool_calls` 并转换成内部 `ToolCall`。模型永远不获得 handler；Runtime 负责编排，Registry 保持执行安全边界。

完整验证达到 31 个测试。学生的 `examples/` 实践目录保留在本地，不自动纳入课程提交。

### 分步实践约定

学生进一步明确：实践任务不能一次布置一个大目标，而应由教师逐步带领；每一步都要提供具体代码、运行验证和解释，确认当前步骤后再进入下一步。

#### 实践步骤 1：补充非法参数回传测试

新增 `test_invalid_arguments_result_is_returned_to_model`：让脚本模型先请求 `lookup_topic`，但传入数字类型的 `topic`，再返回最终文本。测试检查第二次模型看到的 `role="tool"` 消息包含 `invalid_arguments`。

该测试直接通过，原因是当前生产代码已经由 `ToolRegistry` 生成结构化错误，并由 Runtime 回传给模型。这一步的价值是把已有行为固定成回归测试，没有新增生产逻辑。

### 代码实践讲解与可观察实验

教师补充讲解了本轮代码，而不是只报告实现结果。

#### 实验模型

使用离线 `DemoModel` 固定返回两次响应：第一次返回 `ToolCall("lookup_topic", {"topic": "Agent"})`，第二次返回最终文本。实验结果：

```text
answer: 这是最终回答。
call_1: system -> user
call_2: system -> user -> tool(lookup_topic)
```

这说明 Runtime 没有把工具请求当成用户答案，而是执行工具并把结果加入下一次模型上下文。

#### 实验中发现的观察问题

最初的 `ScriptedModel` 直接保存传入的 `messages` 列表。Runtime 后续向同一个列表追加 `tool` 消息，导致测试回看第一次调用时也看到了第二次的消息。根因是可变列表引用别名，不是 Runtime 的调用顺序错误。

先增加回归断言，要求第一次调用最后一条消息必须是 `user`；测试随后失败。最小修复是记录 `list(messages)` 快照。修复后实验准确显示两次调用的消息差异，完整 Runtime 行为没有改变。

这说明测试替身也必须尊重调用边界：如果测试需要观察历史输入，就应该保存快照，而不是保存会被后续流程修改的对象引用。
