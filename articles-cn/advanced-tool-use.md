# Claude 开发者平台推出高级工具使用功能

AI 智能体（Agent）的未来是模型能够无缝地在数百甚至数千个工具之间协同工作。一个 IDE 助手可以集成 git 操作、文件处理、包管理器、测试框架和部署流水线。一个运营协调器可以同时连接 Slack、GitHub、Google Drive、Jira、公司数据库以及数十个 MCP 服务器。

要构建有效的智能体，它们需要能够使用无限的工具库，而无需将所有工具定义预先塞入上下文。我们关于在 MCP 中使用代码执行的博文中讨论了工具结果和定义有时会消耗 50,000+ 个 token，而这发生在智能体读取请求之前。智能体应该按需发现和加载工具，只保留与当前任务相关的工具。

智能体还需要具备从代码中调用工具的能力。使用自然语言工具调用时，每次调用都需要一次完整的推理过程，而无论中间结果是否有用，它们都会堆积在上下文中。代码天然适合编排逻辑，如循环、条件判断和数据转换。智能体需要灵活地根据当前任务选择使用代码执行还是推理。

智能体还需要通过示例学习正确的工具使用方式，而不仅仅是模式定义。JSON Schema 定义了什么在结构上是有效的，但无法表达使用模式：何时包含可选参数、哪些组合是有意义的，或者你的 API 期望遵循什么约定。

今天，我们发布了三个功能来实现这些目标：

- **Tool Search Tool**，允许 Claude 使用搜索工具来访问数千个工具，而不会消耗其上下文窗口
- **Programmatic Tool Calling（编程式工具调用）**，允许 Claude 在代码执行环境中调用工具，减少对模型上下文窗口的影响
- **Tool Use Examples（工具使用示例）**，提供一个通用标准来演示如何有效使用给定工具

在内部测试中，我们发现这些功能帮助我们构建了传统工具使用模式不可能实现的产品。例如，Claude for Excel 使用编程式工具调用来读取和修改包含数千行的电子表格，而不会使模型的上下文窗口过载。

根据我们的经验，我们相信这些功能为使用 Claude 构建产品开辟了新的可能性。

## Tool Search Tool

### 挑战

MCP 工具定义提供了重要的上下文，但随着更多服务器的连接，这些 token 会不断累积。考虑一个五服务器的配置：

- GitHub：35 个工具（约 26K token）
- Slack：11 个工具（约 21K token）
- Sentry：5 个工具（约 3K token）
- Grafana：5 个工具（约 3K token）
- Splunk：2 个工具（约 2K token）

这 58 个工具在对话开始之前就消耗了大约 55K token。再添加更多服务器，如 Jira（仅此一项就使用约 17K token），你很快就会达到 100K+ 的 token 开销。在 Anthropic，我们曾见过工具定义在优化前消耗了 134K token。

但 token 成本并不是唯一的问题。最常见的故障是工具选择错误和参数不正确，尤其是当工具名称相似时，如 `notification-send-user` 和 `notification-send-channel`。

### 我们的解决方案

Tool Search Tool 不是预先加载所有工具定义，而是按需发现工具。Claude 只看到它当前任务实际需要的工具。

传统方式：

- 所有工具定义预先加载（50+ 个 MCP 工具约 72K token）
- 对话历史和系统提示争夺剩余空间
- 总上下文消耗：在任何工作开始之前约 77K token

使用 Tool Search Tool：

- 仅预先加载 Tool Search Tool（约 500 token）
- 按需发现工具（3-5 个相关工具，约 3K token）
- 总上下文消耗：约 8.7K token，保留 95% 的上下文窗口

这意味着 token 使用量减少了 85%，同时保持对完整工具库的访问。内部测试显示，在处理大型工具库时，MCP 评估的准确性有显著提高。启用 Tool Search Tool 后，Opus 4 从 49% 提升到 74%，Opus 4.5 从 79.5% 提升到 88.1%。

### Tool Search Tool 的工作原理

Tool Search Tool 让 Claude 能够动态发现工具，而不是预先加载所有定义。你将所有工具定义提供给 API，但使用 `defer_loading: true` 标记工具使其可按需发现。延迟加载的工具最初不会被加载到 Claude 的上下文中。Claude 只能看到 Tool Search Tool 本身以及 `defer_loading: false` 的工具（你最关键的、最常用的工具）。

当 Claude 需要特定功能时，它会搜索相关工具。Tool Search Tool 返回匹配工具的引用，这些引用会在 Claude 的上下文中展开为完整定义。

例如，如果 Claude 需要与 GitHub 交互，它会搜索 "github"，此时只有 `github.createPullRequest` 和 `github.listIssues` 会被加载——而不是你来自 Slack、Jira 和 Google Drive 的其他 50+ 个工具。

这样，Claude 可以访问你的完整工具库，但只需为它实际需要的工具支付 token 成本。

**提示缓存说明：** Tool Search Tool 不会破坏提示缓存，因为延迟加载的工具完全从初始提示中排除。它们只在 Claude 搜索后才被添加到上下文中，因此你的系统提示和核心工具定义仍然可以被缓存。

实现方式：

```json
{
  "tools": [
    // Include a tool search tool (regex, BM25, or custom)
    {"type": "tool_search_tool_regex_20251119", "name": "tool_search_tool_regex"},

    // Mark tools for on-demand discovery
    {
      "name": "github.createPullRequest",
      "description": "Create a pull request",
      "input_schema": {...},
      "defer_loading": true
    }
    // ... hundreds more deferred tools with defer_loading: true
  ]
}
```

对于 MCP 服务器，你可以延迟加载整个服务器，同时保持特定的高频使用工具处于加载状态：

```json
{
  "type": "mcp_toolset",
  "mcp_server_name": "google-drive",
  "default_config": {"defer_loading": true}, # defer loading the entire server
  "configs": {
    "search_files": {
"defer_loading": false
    }  // Keep most used tool loaded
  }
}
```

Claude Developer Platform 提供开箱即用的基于正则表达式和基于 BM25 的搜索工具，但你也可以使用嵌入向量（Embedding）或其他策略实现自定义搜索工具。

### 何时使用 Tool Search Tool

与任何架构决策一样，启用 Tool Search Tool 涉及权衡。该功能在工具调用前增加了一个搜索步骤，因此当上下文节省和准确性提升超过额外延迟时，它的投资回报率最高。

**适合使用的场景：**

- 工具定义消耗超过 10K token
- 遇到工具选择准确性问题
- 构建多服务器的 MCP 驱动系统
- 可用工具超过 10 个

**收益较小的场景：**

- 工具库较小（少于 10 个工具）
- 所有工具在每次会话中都被频繁使用
- 工具定义本身很紧凑

## Programmatic Tool Calling（编程式工具调用）

### 挑战

随着工作流变得越来越复杂，传统工具调用会产生两个根本性问题：

- **中间结果导致的上下文污染：** 当 Claude 分析一个 10MB 日志文件以查找错误模式时，整个文件会进入其上下文窗口，即使 Claude 只需要错误频率的摘要。当跨多个表获取客户数据时，每条记录无论是否相关都会累积在上下文中。这些中间结果消耗大量 token 预算，并可能将重要信息完全挤出上下文窗口。
- **推理开销和手动综合：** 每次工具调用都需要一次完整的模型推理过程。收到结果后，Claude 必须"用眼扫视"数据以提取相关信息，推理各部分之间的关系，并决定下一步做什么——所有这些都通过自然语言处理完成。一个包含五次工具调用的工作流意味着五次推理过程，加上 Claude 解析每个结果、比较数值和综合结论。这既缓慢又容易出错。

### 我们的解决方案

编程式工具调用使 Claude 能够通过代码来编排工具，而不是通过单个 API 往返调用。Claude 不再逐个请求工具并将每个结果返回到其上下文，而是编写代码来调用多个工具、处理它们的输出，并控制哪些信息实际进入其上下文窗口。

Claude 擅长编写代码，让它用 Python 而非自然语言工具调用来表达编排逻辑，你可以获得更可靠、更精确的控制流。循环、条件判断、数据转换和错误处理在代码中都是显式的，而不是隐含在 Claude 的推理中。

#### 示例：预算合规检查

考虑一个常见的业务任务："哪些团队成员超出了他们的第三季度差旅预算？"

你有三个可用工具：

- `get_team_members(department)` - 返回团队成员列表，包含 ID 和级别
- `get_expenses(user_id, quarter)` - 返回用户的费用明细
- `get_budget_by_level(level)` - 返回某个员工级别的预算限额

**传统方式：**

- 获取团队成员 → 20 人
- 为每个人获取其第三季度费用 → 20 次工具调用，每次返回 50-100 个明细项（航班、酒店、餐饮、收据）
- 按员工级别获取预算限额
- 所有这些都进入 Claude 的上下文：2,000+ 个费用明细项（50 KB+）
- Claude 手动计算每个人的费用，查询其预算，将费用与预算限额进行比较
- 更多模型往返调用，大量上下文消耗

**使用编程式工具调用：**

每个工具结果不再返回给 Claude，Claude 会编写一个 Python 脚本来编排整个工作流。该脚本在 Code Execution 工具（沙箱环境）中运行，在需要你的工具结果时暂停。当你通过 API 返回工具结果时，它们由脚本处理而不是被模型消费。脚本继续执行，Claude 只看到最终输出。

以下是 Claude 为预算合规任务编写的编排代码：

```python
team = await get_team_members("engineering")

# Fetch budgets for each unique level
levels = list(set(m["level"] for m in team))
budget_results = await asyncio.gather(*[
    get_budget_by_level(level) for level in levels
])

# Create a lookup dictionary: {"junior": budget1, "senior": budget2, ...}
budgets = {level: budget for level, budget in zip(levels, budget_results)}

# Fetch all expenses in parallel
expenses = await asyncio.gather(*[
    get_expenses(m["id"], "Q3") for m in team
])

# Find employees who exceeded their travel budget
exceeded = []
for member, exp in zip(team, expenses):
    budget = budgets[member["level"]]
    total = sum(e["amount"] for e in exp)
    if total > budget["travel_limit"]:
        exceeded.append({
            "name": member["name"],
            "spent": total,
            "limit": budget["travel_limit"]
        })

print(json.dumps(exceeded))
```

Claude 的上下文只接收最终结果：超出预算的两三个人。2,000+ 个明细项、中间求和以及预算查询都不会影响 Claude 的上下文，将消耗从 200KB 的原始费用数据减少到仅 1KB 的结果。

效率提升非常显著：

- **Token 节省：** 通过将中间结果保持在 Claude 的上下文之外，PTC 大幅降低了 token 消耗。在复杂研究任务中，平均使用量从 43,588 降至 27,297 个 token，减少了 37%。
- **延迟降低：** 每次 API 往返都需要模型推理（数百毫秒到数秒）。当 Claude 在单个代码块中编排 20+ 次工具调用时，你可以省去 19+ 次推理过程。API 处理工具执行而无需每次都返回模型。
- **准确性提升：** 通过编写显式的编排逻辑，Claude 犯的错误比在自然语言中处理多个工具结果时更少。内部知识检索从 25.6% 提升到 28.5%；GIA 基准测试从 46.5% 提升到 51.2%。

生产工作流涉及杂乱的数据、条件逻辑和需要规模化的操作。编程式工具调用让 Claude 以编程方式处理这些复杂性，同时将其注意力集中在可操作的结果上，而不是原始数据处理。

### 编程式工具调用的工作原理

#### 1. 标记工具为可从代码调用

将 `code_execution` 添加到 tools 中，并设置 `allowed_callers` 以将工具纳入编程式调用：

```json
{
  "tools": [
    {
      "type": "code_execution_20250825",
      "name": "code_execution"
    },
    {
      "name": "get_team_members",
      "description": "Get all members of a department...",
      "input_schema": {...},
      "allowed_callers": ["code_execution_20250825"] # opt-in to programmatic tool calling
    },
    {
      "name": "get_expenses",
 	...
    },
    {
      "name": "get_budget_by_level",
	...
    }
  ]
}
```

API 会将这些工具定义转换为 Claude 可以调用的 Python 函数。

#### 2. Claude 编写编排代码

Claude 不再逐个请求工具，而是生成 Python 代码：

```json
{
  "type": "server_tool_use",
  "id": "srvtoolu_abc",
  "name": "code_execution",
  "input": {
    "code": "team = get_team_members('engineering')\n..." # the code example above
  }
}
```

#### 3. 工具执行而不进入 Claude 的上下文

当代码调用 `get_expenses()` 时，你会收到一个带有 caller 字段的工具请求：

```json
{
  "type": "tool_use",
  "id": "toolu_xyz",
  "name": "get_expenses",
  "input": {"user_id": "emp_123", "quarter": "Q3"},
  "caller": {
    "type": "code_execution_20250825",
    "tool_id": "srvtoolu_abc"
  }
}
```

你提供结果，该结果在 Code Execution 环境中处理，而不是在 Claude 的上下文中。这个请求-响应循环针对代码中的每个工具调用重复执行。

#### 4. 只有最终输出进入上下文

当代码运行完成后，只有代码的结果会返回给 Claude：

```json
{
  "type": "code_execution_tool_result",
  "tool_use_id": "srvtoolu_abc",
  "content": {
    "stdout": "[{\"name\": \"Alice\", \"spent\": 12500, \"limit\": 10000}...]"
  }
}
```

这就是 Claude 看到的全部内容，而不是处理过程中产生的 2000+ 个费用明细项。

### 何时使用编程式工具调用

编程式工具调用为你的工作流增加了一个代码执行步骤。当 token 节省、延迟改善和准确性提升足够显著时，这个额外开销是值得的。

**最适合使用的场景：**

- 处理大型数据集，只需要聚合或摘要
- 运行包含三个或更多依赖工具调用的多步骤工作流
- 在 Claude 看到工具结果之前进行过滤、排序或转换
- 处理中间数据不应影响 Claude 推理的任务
- 对多个项目运行并行操作（例如检查 50 个端点）

**收益较小的场景：**

- 简单的单工具调用
- Claude 应该看到并推理所有中间结果的任务
- 响应较小的快速查询

## Tool Use Examples（工具使用示例）

### 挑战

JSON Schema 擅长定义结构——类型、必填字段、允许的枚举值——但它无法表达使用模式：何时包含可选参数、哪些组合是有意义的，或者你的 API 期望遵循什么约定。

考虑一个工单 API：

```json
{
  "name": "create_ticket",
  "input_schema": {
    "properties": {
      "title": {"type": "string"},
      "priority": {"enum": ["low", "medium", "high", "critical"]},
      "labels": {"type": "array", "items": {"type": "string"}},
      "reporter": {
        "type": "object",
        "properties": {
          "id": {"type": "string"},
          "name": {"type": "string"},
          "contact": {
            "type": "object",
            "properties": {
              "email": {"type": "string"},
              "phone": {"type": "string"}
            }
          }
        }
      },
      "due_date": {"type": "string"},
      "escalation": {
        "type": "object",
        "properties": {
          "level": {"type": "integer"},
          "notify_manager": {"type": "boolean"},
          "sla_hours": {"type": "integer"}
        }
      }
    },
    "required": ["title"]
  }
}
```

该 Schema 定义了什么是有效的，但留下了一些关键问题未解答：

- **格式歧义：** `due_date` 应该使用 "2024-11-06"、"Nov 6, 2024" 还是 "2024-11-06T00:00:00Z"？
- **ID 约定：** `reporter.id` 是 UUID、"USR-12345" 还是只是 "12345"？
- **嵌套结构使用：** Claude 何时应该填充 `reporter.contact`？
- **参数关联：** `escalation.level` 和 `escalation.sla_hours` 与优先级有什么关系？

这些歧义可能导致格式错误的工具调用和不一致的参数使用。

### 我们的解决方案

Tool Use Examples 让你直接在工具定义中提供示例工具调用。你不再仅依赖 Schema，而是向 Claude 展示具体的使用模式：

```json
{
    "name": "create_ticket",
    "input_schema": { /* same schema as above */ },
    "input_examples": [
      {
        "title": "Login page returns 500 error",
        "priority": "critical",
        "labels": ["bug", "authentication", "production"],
        "reporter": {
          "id": "USR-12345",
          "name": "Jane Smith",
          "contact": {
            "email": "jane@acme.com",
            "phone": "+1-555-0123"
          }
        },
        "due_date": "2024-11-06",
        "escalation": {
          "level": 2,
          "notify_manager": true,
          "sla_hours": 4
        }
      },
      {
        "title": "Add dark mode support",
        "labels": ["feature-request", "ui"],
        "reporter": {
          "id": "USR-67890",
          "name": "Alex Chen"
        }
      },
      {
        "title": "Update API documentation"
      }
    ]
  }
```

从这三个示例中，Claude 学习到：

- **格式约定：** 日期使用 YYYY-MM-DD，用户 ID 遵循 USR-XXXXX 格式，标签使用 kebab-case
- **嵌套结构模式：** 如何构建带有嵌套 contact 对象的 reporter 对象
- **可选参数关联：** 严重错误有完整的联系信息 + 带有严格 SLA 的升级处理；功能请求有 reporter 但没有 contact/escalation；内部任务只有 title

在我们自己的内部测试中，工具使用示例将复杂参数处理的准确性从 72% 提升到 90%。

### 何时使用工具使用示例

工具使用示例会增加工具定义中的 token，因此当准确性提升超过额外成本时，它们最有价值。

**最适合使用的场景：**

- 复杂嵌套结构中，有效的 JSON 不意味着正确的用法
- 具有许多可选参数且包含模式很重要的工具
- 具有 Schema 中未捕获的领域特定约定的 API
- 相似工具中，示例能明确使用哪个（例如 `create_ticket` 和 `create_incident`）

**收益较小的场景：**

- 用法显而易见的简单单参数工具
- Claude 已经理解的标准格式，如 URL 或电子邮件
- 更适合通过 JSON Schema 约束处理的验证问题

## 最佳实践

构建执行真实世界操作的智能体意味着同时处理规模、复杂性和精度。这三个功能协同工作，解决工具使用工作流中的不同瓶颈。以下是如何有效组合它们的方法。

### 分层策略性地组合功能

并非每个智能体对给定任务都需要使用所有三个功能。从你最大的瓶颈开始：

- 工具定义导致的上下文膨胀 → Tool Search Tool
- 大量中间结果污染上下文 → Programmatic Tool Calling
- 参数错误和格式错误的调用 → Tool Use Examples

这种聚焦的方式让你能够针对限制智能体性能的具体约束进行优化，而不是预先增加复杂性。

然后根据需要叠加额外功能。它们是互补的：Tool Search Tool 确保找到正确的工具，Programmatic Tool Calling 确保高效执行，Tool Use Examples 确保正确调用。

### 设置 Tool Search Tool 以获得更好的发现效果

工具搜索匹配名称和描述，因此清晰、描述性的定义能提高发现准确性。

```json
// Good
{
    "name": "search_customer_orders",
    "description": "Search for customer orders by date range, status, or total amount. Returns order details including items, shipping, and payment info."
}

// Bad
{
    "name": "query_db_orders",
    "description": "Execute order query"
}
```

添加系统提示指导，让 Claude 知道有哪些可用工具：

```
You have access to tools for Slack messaging, Google Drive file management, 
Jira ticket tracking, and GitHub repository operations. Use the tool search 
to find specific capabilities.
```

保持你最常用的三到五个工具始终加载，延迟加载其余工具。这在常见操作的即时访问和所有其他工具的按需发现之间取得了平衡。

### 设置编程式工具调用以获得正确的执行

由于 Claude 编写代码来解析工具输出，请清晰地记录返回格式。这有助于 Claude 编写正确的解析逻辑：

```json
{
    "name": "get_orders",
    "description": "Retrieve orders for a customer.
Returns:
    List of order objects, each containing:
    - id (str): Order identifier
    - total (float): Order total in USD
    - status (str): One of 'pending', 'shipped', 'delivered'
    - items (list): Array of {sku, quantity, price}
    - created_at (str): ISO 8601 timestamp"
}
```

以下是适合编程式编排的候选工具：

- 可以并行运行的工具（独立操作）
- 可安全重试的操作（幂等操作）

### 设置工具使用示例以提高参数准确性

为行为清晰性精心设计示例：

- 使用真实数据（真实的城市名称、合理的价格，而不是 "string" 或 "value"）
- 展示最小、部分和完整规范的多样性
- 保持简洁：每个工具 1-5 个示例
- 聚焦于歧义（仅在 Schema 无法明确正确用法时添加示例）

## 入门指南

这些功能目前处于 Beta 阶段可用。要启用它们，添加 Beta 头信息并包含你需要的工具：

```python
client.beta.messages.create(
    betas=["advanced-tool-use-2025-11-20"],
    model="claude-sonnet-4-5-20250929",
    max_tokens=4096,
    tools=[
        {"type": "tool_search_tool_regex_20251119", "name": "tool_search_tool_regex"},
        {"type": "code_execution_20250825", "name": "code_execution"},
        # Your tools with defer_loading, allowed_callers, and input_examples
    ]
)
```

有关详细的 API 文档和 SDK 示例，请参阅我们的：

- Tool Search Tool 的文档和 Cookbook
- Programmatic Tool Calling 的文档和 Cookbook
- Tool Use Examples 的文档

这些功能将工具使用从简单的函数调用推向智能编排。随着智能体处理跨越数十个工具和大型数据集的更复杂工作流，动态发现、高效执行和可靠调用成为基础能力。

我们期待看到你的构建成果。

## 致谢

由 Bin Wu 撰写，Adam Jones、Artur Renault、Henry Tay、Jake Noble、Noah Picard、Sam Jiang 和 Claude Developer Platform 团队参与贡献。这项工作建立在 Chris Gorgolewski、Daniel Jiang、Jeremy Fox 和 Mike Lambert 的基础研究之上。我们还从 AI 生态系统中汲取了灵感，包括 Joel Pobar 的 LLMVM、Cloudflare 的 Code Mode 和 Code Execution as MCP。特别感谢 Andy Schumeister、Hamish Kerr、Keir Bradwell、Matt Bleifer 和 Molly Vorwerck 的支持。