# Claude Code 最佳实践


## 本页内容

- 让 Claude 能够验证自己的工作
- 先探索，再规划，然后编码
- 在提示中提供具体上下文提供丰富内容
- 提供丰富内容
- 配置你的环境编写有效的 CLAUDE.md配置权限使用 CLI 工具连接 MCP 服务器设置钩子创建技能创建自定义子智能体安装插件
- 编写有效的 CLAUDE.md
- 配置权限
- 使用 CLI 工具
- 连接 MCP 服务器
- 设置钩子
- 创建技能
- 创建自定义子智能体
- 安装插件
- 有效沟通提出代码库相关问题让 Claude 访谈你
- 提出代码库相关问题
- 让 Claude 访谈你
- 管理你的会话尽早并频繁地修正方向积极管理上下文使用子智能体进行调查通过检查点回退恢复会话
- 尽早并频繁地修正方向
- 积极管理上下文
- 使用子智能体进行调查
- 通过检查点回退
- 恢复会话
- 自动化与规模化运行非交互模式运行多个 Claude 会话跨文件扇出执行使用自动模式自主运行添加对抗性审查步骤
- 运行非交互模式
- 运行多个 Claude 会话
- 跨文件扇出执行
- 使用自动模式自主运行
- 添加对抗性审查步骤
- 避免常见的失败模式
- 培养你的直觉
- 相关资源

# Claude Code 最佳实践

充分利用 Claude Code 的技巧和模式，从配置环境到跨并行会话进行规模化。

## 让 Claude 能够验证自己的工作

- 在单个提示中：要求 Claude 在同一条消息中运行检查并进行迭代，如上表所示。
- 跨会话：将检查设置为 /goal 条件。一个独立的评估器会在每轮对话后重新检查，Claude 会持续工作直到条件满足。
- 作为确定性门控：一个 Stop 钩子（Hook）将你的检查作为脚本运行，并阻止当前轮次结束直到检查通过。Claude Code 在连续 8 次阻止后会覆盖该钩子并结束轮次。
- 通过第二意见：一个验证子智能体（Subagent）或动态工作流来检查自身的发现，让一个全新的模型尝试反驳结果，这样执行工作的智能体不是评分的那个。

## 先探索，再规划，然后编码

探索

```
read /src/auth and understand how we handle sessions and login.also look at how we manage environment variables for secrets.
```

规划

```
I want to add Google OAuth. What files need to change?What's the session flow? Create a plan.
```

Ctrl+G
实现

```
implement the OAuth flow from your plan. write tests for thecallback handler, run the test suite and fix any failures.
```

提交

```
commit with a descriptive message and open a PR
```

## 在提示中提供具体上下文

"你会对这个文件做哪些改进？"

### 提供丰富内容

- 使用 @ 引用文件，而不是描述代码的位置。Claude 会在响应之前读取该文件。
- 直接粘贴图片。将图片复制/粘贴或拖放到提示中。
- 提供文档和 API 参考的 URL。使用 /permissions 将常用域名加入允许列表。
- 通过运行 cat error.log | claude 管道传入数据，直接发送文件内容。
- 让 Claude 获取所需内容。告诉 Claude 使用 Bash 命令、MCP 工具或读取文件来自行拉取上下文。

## 配置你的环境


### 编写有效的 CLAUDE.md

/init

```
# Code style-Use ES modules (import/export) syntax, not CommonJS (require)-Destructure imports when possible (eg. import { foo } from 'bar')# Workflow-Be sure to typecheck when you're done making a series of code changes-Prefer running single tests, and not the whole test suite, for performance
```

@path/to/import

```
See @README.md for project overview and @package.json for available npm commands.# Additional Instructions-Git workflow: @docs/git-instructions.md-Personal overrides: @~/.claude/my-project-instructions.md
```

- 主文件夹（~/.claude/CLAUDE.md）：适用于所有 Claude 会话
- 项目根目录（./CLAUDE.md）：提交到 git 以便与团队共享
- 项目根目录（./CLAUDE.local.md）：个人的项目专用笔记；将此文件添加到 .gitignore 中，避免与团队共享
- 父目录：适用于 monorepo，root/CLAUDE.md 和 root/foo/CLAUDE.md 都会被自动加载
- 子目录：当 Claude 读取子目录中的文件时，会按需加载子目录的 CLAUDE.md 文件

### 配置权限

/permissions

- 自动模式：一个独立的分类器模型审查命令，仅阻止看起来有风险的操作：权限范围升级、未知基础设施或恶意内容驱动的操作。当你信任任务的大致方向但不想逐步点击确认时，这是最佳选择
- 权限允许列表：允许你已知安全的特定工具，如 npm run lint 或 git commit
- 沙箱化：启用操作系统级别的隔离来限制文件系统和网络访问，允许 Claude 在定义的边界内更自由地工作

### 使用 CLI 工具

gh、aws、gcloud、sentry-cli 等工具都经过了优化。

使用 'foo-cli-tool --help' 来了解 foo 工具，然后用它来解决 A、B、C 问题。

### 连接 MCP 服务器

使用 claude mcp add 来连接 MCP 服务器。

### 设置钩子

在 .claude/settings.json 中配置 /hooks。

### 创建技能

技能（Skill）以 SKILL.md 文件的形式存在于 .claude/skills/ 目录中，可以通过 /skill-name 来调用。

```
---name:api-conventionsdescription:REST API design conventions for our services---# API Conventions-Use kebab-case for URL paths-Use camelCase for JSON properties-Always include pagination for list endpoints-Version APIs in the URL path (/v1/, /v2/)
```

```
---name:fix-issuedescription:Fix a GitHub issuedisable-model-invocation:true---Analyze and fix the GitHub issue: $ARGUMENTS.1.Use`gh issue view`to get the issue details2.Understand the problem described in the issue3.Search the codebase for relevant files4.Implement the necessary changes to fix the issue5.Write and run tests to verify the fix6.Ensure code passes linting and type checking7.Create a descriptive commit message8.Push and create a PR
```

你可以使用 /fix-issue 1234 来调用此技能。设置 disable-model-invocation: true 可以跳过模型调用，直接执行技能中的步骤。

### 创建自定义子智能体

子智能体（Subagent）定义在 .claude/agents/ 目录中。

```
---name:security-reviewerdescription:Reviews code for security vulnerabilitiestools:Read, Grep, Glob, Bashmodel:opus---You are a senior security engineer. Review code for:-Injection vulnerabilities (SQL, XSS, command injection)-Authentication and authorization flaws-Secrets or credentials in code-Insecure data handlingProvide specific line references and suggested fixes.
```

### 安装插件

使用 /plugin 来安装和管理插件。

## 有效沟通


### 提出代码库相关问题

- 日志系统是如何工作的？
- 如何创建一个新的 API 端点？
- foo.rs 第 134 行的 async move { ... } 是做什么的？
- CustomerOnboardingFlowImpl 处理了哪些边缘情况？
- 为什么这段代码在第 333 行调用 foo() 而不是 bar()？

### 让 Claude 访谈你

使用 AskUserQuestion 工具来让 Claude 对你进行深入访谈。

```
I want to build [brief description]. Interview me in detail using the AskUserQuestion tool.Ask about technical implementation, UI/UX, edge cases, concerns, and tradeoffs. Don't ask obvious questions, dig into the hard parts I might not have considered.Keep interviewing until we've covered everything, then write a complete spec to SPEC.md.
```

## 管理你的会话


### 尽早并频繁地修正方向

- Esc：在 Claude 执行过程中按 Esc 键停止。上下文会被保留，因此你可以重新引导方向。
- Esc + Esc 或 /rewind：按两次 Esc 或运行 /rewind 来打开回退菜单，恢复之前的对话和代码状态，或从选定消息开始总结。
- "撤销那个操作"：让 Claude 回退其更改。
- /clear：在不相关的任务之间重置上下文。包含不相关上下文的长会话可能会降低性能。

### 积极管理上下文

- 在任务之间频繁使用 /clear 来完全重置上下文窗口
- 当自动压缩触发时，Claude 会总结最重要的内容，包括代码模式、文件状态和关键决策
- 如需更多控制，运行 /compact <instructions>，例如 /compact Focus on the API changes
- 要仅压缩对话的一部分，使用 Esc + Esc 或 /rewind，选择一个消息检查点，然后选择"从此处总结"或"总结到此处"。前者压缩从该点之后的消息同时保留早期上下文不变；后者压缩早期消息同时完整保留最近的消息。请参阅"恢复与总结"。
- 在 CLAUDE.md 中自定义压缩行为，例如添加指令"压缩时，始终保留完整的已修改文件列表和所有测试命令"，以确保关键上下文在总结过程中得以保留
- 对于不需要保留在上下文中的快速问题，使用 /btw。答案会显示在可关闭的叠加层中，并且永远不会进入对话历史，因此你可以在不增加上下文的情况下查看细节。

### 使用子智能体进行调查

使用子智能体（Subagent）来调查问题。

```
Use subagents to investigate how our authentication system handles tokenrefresh, and whether we have any existing OAuth utilities I should reuse.
```

```
use a subagent to review this code for edge cases
```

### 通过检查点回退

按 Escape 键或使用 /rewind 命令来回退到之前的检查点。

### 恢复会话

使用 /rename 为会话命名，使用 claude --continue 继续最近的会话，使用 claude --resume 恢复特定会话（例如 claude --resume oauth-migration）。

## 自动化与规模化


### 运行非交互模式

使用 claude -p "prompt" 来运行非交互模式。可以配合 --output-format stream-json --verbose 使用。

```
# One-off queriesclaude-p"Explain what this project does"# Structured output for scriptsclaude-p"List all API endpoints"--output-formatjson# Streaming for real-time processingclaude-p"Analyze this log file"--output-formatstream-json--verbose
```

### 运行多个 Claude 会话

- 工作树（Worktree）：在隔离的 git 检出中运行独立的 CLI 会话，避免编辑冲突
- 桌面应用：可视化管理多个本地会话，每个会话在自己的工作树中
- Web 版 Claude Code：在 Anthropic 管理的云基础设施上的隔离虚拟机中运行会话
- 智能体团队（Agent Team）：多个会话的自动化协调，具有共享任务、消息传递和团队负责人

实现流程示例：
1. 智能体 A：为我们的 API 端点实现一个速率限制器
2. 智能体 B：审查 @src/middleware/rateLimiter.ts 中的速率限制器实现。查找边缘情况、竞态条件以及与现有中间件模式的一致性
3. 智能体 A：以下是审查反馈：[会话 B 输出]。解决这些问题

### 跨文件扇出执行

使用 claude -p 配合 --allowedTools 来跨多个文件扇出执行任务。

步骤：
1. 生成任务列表：列出所有需要迁移的 2,000 个 Python 文件
2. 编写脚本来循环处理列表

```
forfilein$(catfiles.txt);doclaude-p"Migrate$filefrom React to Vue. Return OK or FAIL."\--allowedTools"Edit,Bash(git commit *)"done
```

先在几个文件上测试，然后大规模运行。使用 --allowedTools 来限制可用工具。

```
claude-p"<your prompt>"--output-formatjson|your_command
```

使用 --verbose 获取详细输出。

### 使用自动模式自主运行

```
claude--permission-modeauto-p"fix all lint errors"
```

使用 -p 标志来指定提示。

### 添加对抗性审查步骤

使用 /code-review 或子智能体来添加对抗性审查。

```
Use a subagent to review the rate limiter diff against PLAN.md. Check thatevery requirement is implemented, the listed edge cases have tests, andnothing outside the task's scope changed. Report gaps, not style preferences.
```

## 避免常见的失败模式

- 大杂烩会话。你从一个任务开始，然后问 Claude 一些不相关的事情，再回到第一个任务。上下文中充满了不相关的信息。
  > 修复方法：在不相关的任务之间使用 /clear。

- 反复纠正。Claude 做错了某事，你纠正它，它仍然做错，你再次纠正。上下文被失败的方法污染了。
  > 修复方法：在两次失败的纠正后，使用 /clear 并根据你学到的经验编写一个更好的初始提示。

- 过度指定的 CLAUDE.md。如果你的 CLAUDE.md 太长，Claude 会忽略其中一半，因为重要的规则在噪音中丢失了。
  > 修复方法：果断精简。如果 Claude 在没有指令的情况下已经正确执行了某项操作，就删除它或将其转换为钩子。

- 信任后验证的差距。Claude 生成了一个看似合理的实现，但没有处理边缘情况。
  > 修复方法：始终提供验证（测试、脚本、截图）。如果你无法验证它，就不要发布它。

- 无限探索。你让 Claude "调查"某事但没有限定范围。Claude 读取了数百个文件，填满了上下文。
  > 修复方法：将调查范围缩小或使用子智能体，这样探索不会消耗你的主上下文。

## 培养你的直觉


## 相关资源

- Claude Code 的工作原理：智能体循环、工具和上下文管理
- 扩展 Claude Code：技能、钩子、MCP、子智能体和插件
- 常见工作流：调试、测试、PR 等的分步指南
- CLAUDE.md：存储项目约定和持久化上下文

本页是否对你有帮助？