# 长时间运行智能体的有效运行框架

随着 AI 智能体（Agent）能力的不断增强，开发者越来越倾向于让它们承担跨越数小时甚至数天的复杂任务。然而，如何让智能体在多个上下文窗口之间保持持续稳定的进展，仍然是一个尚未解决的问题。

长时间运行智能体的核心挑战在于，它们必须在离散的会话中工作，而每个新会话开始时对之前发生的事情毫无记忆。想象一下，一个软件项目由轮班制的工程师负责，每位新到岗的工程师对上一班次的工作内容完全没有记忆。由于上下文窗口是有限的，而大多数复杂项目无法在单个窗口内完成，因此智能体需要一种方式来弥合编码会话之间的鸿沟。

我们开发了一套双重解决方案，使 Claude Agent SDK 能够在多个上下文窗口中高效工作：一个初始化智能体（Initializer Agent）在首次运行时搭建环境，以及一个编码智能体（Coding Agent）负责在每个会话中取得增量进展，同时为下一个会话留下清晰的工作产物。你可以在配套的快速入门指南中找到代码示例。

## 长时间运行智能体的问题

Claude Agent SDK 是一个功能强大的通用智能体运行框架，擅长编码以及其他需要模型使用工具来收集上下文、规划和执行的任务。它具备上下文管理能力，例如压缩（Compaction），使智能体能够在不耗尽上下文窗口的情况下持续工作。理论上，在这种配置下，智能体应该能够在任意长的时间内继续执行有用的工作。

然而，仅靠压缩是不够的。开箱即用的情况下，即使是像 Opus 4.5 这样的前沿编码模型，在 Claude Agent SDK 上跨多个上下文窗口循环运行，如果只给出一个高层级的提示（例如"构建一个 claude.ai 的克隆版本"），也无法构建出生产级质量的 Web 应用。

Claude 的失败表现为两种模式。首先，智能体倾向于试图一次完成过多工作——本质上是试图一次性构建整个应用。这通常导致模型在实现过程中耗尽上下文，留下一个半成品且无文档记录的功能给下一个会话。然后智能体不得不猜测之前发生了什么，并花费大量时间尝试让基本应用重新运行起来。即使有压缩机制也会出现这种情况，因为它并不总能向下一位智能体传递完全清晰的指令。

第二种失败模式通常出现在项目的后期阶段。当某些功能已经构建完成后，后续的智能体实例会查看周围环境，发现已经取得了一些进展，然后就宣布任务完成。

这将问题分解为两个部分。首先，我们需要搭建一个初始环境，为给定提示所要求的全部功能奠定基础，使智能体能够按步骤、逐功能地工作。其次，我们应当提示每个智能体向目标取得增量进展，同时在会话结束时保持环境处于整洁状态。所谓"整洁状态"，是指适合合并到主分支的代码：没有重大缺陷，代码有序且文档完善，总体而言，开发者能够轻松开始新功能的开发，而无需先清理无关的遗留问题。

在内部实验中，我们使用两部分方案来解决这些问题：

- **初始化智能体**：第一个智能体会话使用专门的提示，要求模型搭建初始环境：一个 `init.sh` 脚本、一个 `claude-progress.txt` 文件用于记录智能体的工作日志，以及一个初始 git 提交来记录添加了哪些文件。
- **编码智能体**：每个后续会话要求模型取得增量进展，然后留下结构化的更新记录。^1

这里的关键洞见是找到一种方式，让智能体在以全新上下文窗口启动时能够快速了解工作状态，这通过 `claude-progress.txt` 文件配合 git 历史记录来实现。这些做法的灵感来自于了解高效软件工程师每天的工作方式。

## 环境管理

在更新版的 Claude 4 提示指南中，我们分享了一些跨上下文窗口工作流的最佳实践，包括一种为"第一个上下文窗口使用不同提示"的运行框架结构。这个"不同的提示"要求初始化智能体搭建一个包含所有必要上下文的环境，使未来的编码智能体能够高效工作。以下我们深入介绍该环境的一些关键组件。

### 功能清单

为了解决智能体一次性构建应用或过早认为项目已完成的问题，我们提示初始化智能体编写一份全面的功能需求文件，对用户的初始提示进行扩展。在 claude.ai 克隆示例中，这意味着超过 200 项功能，例如"用户可以打开新对话、输入查询、按回车键并看到 AI 响应"。这些功能最初都标记为"失败"，以便后续编码智能体清楚了解完整功能的全貌。

```json
{
    "category": "functional",
    "description": "New chat button creates a fresh conversation",
    "steps": [
      "Navigate to main interface",
      "Click the 'New Chat' button",
      "Verify a new conversation is created",
      "Check that chat area shows welcome state",
      "Verify conversation appears in sidebar"
    ],
    "passes": false
  }
```

我们提示编码智能体仅通过更改 `passes` 字段的状态来编辑此文件，并使用措辞强烈的指令，例如"删除或修改测试是不可接受的，因为这可能导致功能缺失或存在缺陷。"经过一些实验后，我们决定使用 JSON 格式，因为与 Markdown 文件相比，模型不太可能不当修改或覆盖 JSON 文件。

### 增量进展

有了这个初始环境脚手架后，下一个编码智能体被要求每次只处理一个功能。事实证明，这种增量方式对于解决智能体一次性做太多事情的倾向至关重要。

一旦采用增量方式工作，模型在代码更改后保持环境整洁仍然至关重要。在我们的实验中，我们发现引导这种行为的最佳方式是要求模型将其进展提交到 git 并附上描述性的提交信息，同时在进度文件中撰写进展摘要。这使得模型能够使用 git 来回退不良的代码更改并恢复代码库的可用状态。

这些方法还提高了效率，因为它们消除了智能体猜测之前发生了什么以及花费时间尝试让基本应用重新运行的需要。

### 测试

我们观察到的最后一个主要失败模式是 Claude 在未进行适当测试的情况下就将功能标记为完成。在没有明确提示的情况下，Claude 倾向于进行代码更改，甚至使用单元测试或 `curl` 命令对开发服务器进行测试，但无法识别该功能在端到端场景中是否真正有效。

在构建 Web 应用的情况下，一旦明确提示 Claude 使用浏览器自动化工具并像真实用户一样进行所有测试，它在端到端验证功能方面表现良好。

为 Claude 提供这类测试工具显著提升了性能，因为智能体能够识别和修复仅从代码层面难以发现的缺陷。

一些问题仍然存在，例如 Claude 视觉能力和浏览器自动化工具的局限性使得识别每种缺陷变得困难。例如，Claude 无法通过 Puppeteer MCP 看到浏览器原生的警告弹窗，依赖这些弹窗的功能往往因此存在更多缺陷。

## 快速上手

在以上所有配置就位后，每个编码智能体会被提示执行一系列步骤来了解当前状况，其中一些相当基础但仍然有用：

- 运行 `pwd` 查看当前工作目录。你只能编辑此目录中的文件。
- 阅读 git 日志和进度文件，了解最近的工作内容。
- 阅读功能清单文件，选择优先级最高且尚未完成的功能来处理。

这种方法为 Claude 在每个会话中节省了一些 token，因为它无需自行摸索如何测试代码。同时，让初始化智能体编写一个 `init.sh` 脚本来运行开发服务器，然后在实现新功能之前先执行基本的端到端测试，也会很有帮助。

在 claude.ai 克隆的案例中，这意味着智能体始终先启动本地开发服务器，然后使用 Puppeteer MCP 创建新对话、发送消息并接收响应。这确保了 Claude 能够快速识别应用是否处于损坏状态，并立即修复任何已有缺陷。如果智能体转而直接开始实现新功能，很可能会使问题更加严重。

基于以上所有配置，一个典型的会话从以下助手消息开始：

```
[Assistant] I'll start by getting my bearings and understanding the current state of the project.
[Tool Use] <bash - pwd>
[Tool Use] <read - claude-progress.txt>
[Tool Use] <read - feature_list.json>
[Assistant] Let me check the git log to see recent work.
[Tool Use] <bash - git log --oneline -20>
[Assistant] Now let me check if there's an init.sh script to restart the servers.
<Starts the development server>
[Assistant] Excellent! Now let me navigate to the application and verify that some fundamental features are still working.
<Tests basic functionality>
[Assistant] Based on my verification testing, I can see that the fundamental functionality is working well. The core chat features, theme switching, conversation loading, and error handling are all functioning correctly. Now let me review the tests.json file more comprehensively to understand what needs to be implemented next.
<Starts work on a new feature>
```

## 未来工作

本研究展示了长时间运行智能体运行框架中一组可行的解决方案，使模型能够在多个上下文窗口之间取得增量进展。然而，仍有一些待解决的问题。

最值得注意的是，目前仍不清楚单一的通用编码智能体是否在跨上下文场景中表现最佳，还是通过多智能体架构可以实现更好的性能。专门化的智能体，如测试智能体、质量保证智能体或代码清理智能体，似乎有理由在软件开发生命周期的子任务中做得更好。

此外，本演示针对全栈 Web 应用开发进行了优化。未来的一个方向是将这些发现推广到其他领域。这些经验中的部分或全部很可能可以应用于其他类型的长时间运行智能体任务，例如科学研究或金融建模。

### 致谢

由 Justin Young 撰写。特别感谢 David Hershey、Prithvi Rajasakeran、Jeremy Hadfield、Naia Bouscal、Michael Tingley、Jesse Mu、Jake Eaton、Marius Buleandara、Maggie Vo、Pedram Navid、Nadine Yasser 和 Alex Notov 的贡献。

这项工作反映了 Anthropic 内部多个团队的集体努力，使 Claude 能够安全地进行长周期自主软件工程，特别是代码强化学习和 Claude Code 团队。有意向的候选人欢迎在 anthropic.com/careers 申请加入。

### 脚注

^1 我们在此处将它们称为不同的智能体，仅因为它们使用不同的初始用户提示。系统提示、工具集和整体智能体运行框架在其他方面完全相同。