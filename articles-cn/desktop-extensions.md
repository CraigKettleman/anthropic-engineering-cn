# 桌面扩展（Desktop Extensions）：Claude Desktop 一键安装 MCP 服务器

- 文件扩展名更新Sep 11, 2025Claude 桌面扩展现在使用 .mcpb（MCP Bundle）文件扩展名代替 .dxt。现有的 .dxt 扩展将继续工作，但我们建议开发者今后使用 .mcpb 创建新扩展。所有功能保持不变——这纯粹是命名约定的更新。
文件扩展名更新
Sep 11, 2025
Claude 桌面扩展现在使用 .mcpb（MCP Bundle）文件扩展名代替 .dxt。现有的 .dxt 扩展将继续工作，但我们建议开发者今后使用 .mcpb 创建新扩展。所有功能保持不变——这纯粹是命名约定的更新。
—
去年我们发布模型上下文协议（Model Context Protocol，MCP）时，看到开发者构建了出色的本地服务器，让 Claude 能够访问从文件系统到数据库的一切资源。但我们不断收到相同的反馈：安装过程太复杂了。用户需要开发者工具，必须手动编辑配置文件，而且经常在依赖问题上卡住。

今天，我们推出桌面扩展（Desktop Extensions）——一种全新的打包格式，让安装 MCP 服务器变得像点击按钮一样简单。

### 解决 MCP 安装难题

本地 MCP 服务器为 Claude Desktop 用户解锁了强大的功能。它们可以与本地应用程序交互、访问私有数据，并与开发工具集成——同时数据始终保留在用户自己的机器上。然而，当前的安装过程存在显著障碍：
- 需要开发者工具：用户需要安装 Node.js、Python 或其他运行时
- 手动配置：每个服务器都需要编辑 JSON 配置文件
- 依赖管理：用户必须解决包冲突和版本不匹配问题
- 缺少发现机制：查找有用的 MCP 服务器需要在 GitHub 上搜索
- 更新复杂：保持服务器最新意味着需要手动重新安装

这些摩擦点意味着，尽管 MCP 服务器功能强大，但对非技术用户来说基本上无法使用。

### 桌面扩展介绍

桌面扩展（.mcpb 文件）通过将整个 MCP 服务器——包括所有依赖项——打包到一个可安装的包中来解决这些问题。以下是用户体验的变化：

安装前：

```
# 首先安装 Node.js
npm install -g @example/mcp-server
# 手动编辑 ~/.claude/claude_desktop_config.json
# 重启 Claude Desktop
# 祈祷它能正常工作
```

安装后：
- 下载一个 .mcpb 文件
- 双击用 Claude Desktop 打开
- 点击"安装"

就这么简单。无需终端、无需配置文件、无依赖冲突。

## 架构概述

桌面扩展是一个 ZIP 压缩包，包含本地 MCP 服务器以及一个 manifest.json 文件，该文件描述了 Claude Desktop 和其他支持桌面扩展的应用程序需要了解的所有信息。

```
extension.mcpb (ZIP 压缩包)
├── manifest.json         # 扩展元数据和配置
├── server/               # MCP 服务器实现
│   └── [服务器文件]
├── dependencies/         # 所有必需的包/库
└── icon.png             # 可选：扩展图标

# 示例：Node.js 扩展
extension.mcpb
├── manifest.json         # 必需：扩展元数据和配置
├── server/               # 服务器文件
│   └── index.js          # 主入口文件
├── node_modules/         # 捆绑的依赖项
├── package.json          # 可选：NPM 包定义
└── icon.png              # 可选：扩展图标

# 示例：Python 扩展
extension.mcpb (ZIP 文件)
├── manifest.json         # 必需：扩展元数据和配置
├── server/               # 服务器文件
│   ├── main.py           # 主入口文件
│   └── utils.py          # 附加模块
├── lib/                  # 捆绑的 Python 包
├── requirements.txt      # 可选：Python 依赖列表
└── icon.png              # 可选：扩展图标
```

桌面扩展中唯一必需的文件是 manifest.json。Claude Desktop 处理了所有复杂性：
- 内置运行时：我们在 Claude Desktop 中内置了 Node.js，消除了外部依赖
- 自动更新：扩展在新版本可用时自动更新
- 安全的密钥管理：敏感配置（如 API 密钥）存储在操作系统密钥链中

该清单包含人类可读的信息（如名称、描述、作者）、功能声明（工具、提示词）、用户配置和运行时要求。大多数字段是可选的，因此最简版本相当短，但实际中，我们期望所有三种支持的扩展类型（Node.js、Python 和经典二进制文件/可执行文件）都包含以下文件：

```json
{
  "mcpb_version": "0.1",                    // 此清单遵循的 MCPB 规范版本
  "name": "my-extension",                   // 机器可读名称（用于 CLI、API）
  "version": "1.0.0",                       // 扩展的语义化版本号
  "description": "A simple MCP extension",  // 扩展功能的简要描述
  "author": {                               // 作者信息（必需）
    "name": "Extension Author"              // 作者姓名（必填字段）
  },
  "server": {                               // 服务器配置（必需）
    "type": "node",                         // 服务器类型："node"、"python" 或 "binary"
    "entry_point": "server/index.js",       // 主服务器文件的路径
    "mcp_config": {                         // MCP 服务器配置
      "command": "node",                    // 运行服务器的命令
      "args": [                             // 传递给命令的参数
        "${__dirname}/server/index.js"      // ${__dirname} 会被替换为扩展的目录路径
      ]
    }
  }
}
```

清单规范中提供了许多便利选项，旨在简化本地 MCP 服务器的安装和配置。服务器配置对象可以定义为既支持以模板字面量形式的用户自定义配置，也支持平台特定的覆盖。扩展开发者可以详细定义他们希望从用户那里收集的配置类型。

让我们看一个具体的例子，了解清单如何辅助配置。在下面的清单中，开发者声明用户需要提供一个 api_key。Claude 在用户提供该值之前不会启用扩展，自动将其保存在操作系统的安全存储中，并在启动服务器时透明地将 ${user_config.api_key} 替换为用户提供的值。类似地，${__dirname} 将被替换为扩展解压目录的完整路径。

```json
{
  "mcpb_version": "0.1",
  "name": "my-extension",
  "version": "1.0.0",
  "description": "A simple MCP extension",
  "author": {
    "name": "Extension Author"
  },
  "server": {
    "type": "node",
    "entry_point": "server/index.js",
    "mcp_config": {
      "command": "node",
      "args": ["${__dirname}/server/index.js"],
      "env": {
        "API_KEY": "${user_config.api_key}"
      }
    }
  },
  "user_config": {
    "api_key": {
      "type": "string",
      "title": "API Key",
      "description": "Your API key for authentication",
      "sensitive": true,
      "required": true
    }
  }
}
```

一个包含大多数可选字段的完整 manifest.json 可能如下所示：

```json
{
  "mcpb_version": "0.1",
  "name": "My MCP Extension",
  "display_name": "My Awesome MCP Extension",
  "version": "1.0.0",
  "description": "A brief description of what this extension does",
  "long_description": "A detailed description that can include multiple paragraphs explaining the extension's functionality, use cases, and features. It supports basic markdown.",
  "author": {
    "name": "Your Name",
    "email": "yourname@example.com",
    "url": "https://your-website.com"
  },
  "repository": {
    "type": "git",
    "url": "https://github.com/your-username/my-mcp-extension"
  },
  "homepage": "https://example.com/my-extension",
  "documentation": "https://docs.example.com/my-extension",
  "support": "https://github.com/your-username/my-extension/issues",
  "icon": "icon.png",
  "screenshots": [
    "assets/screenshots/screenshot1.png",
    "assets/screenshots/screenshot2.png"
  ],
  "server": {
    "type": "node",
    "entry_point": "server/index.js",
    "mcp_config": {
      "command": "node",
      "args": ["${__dirname}/server/index.js"],
      "env": {
        "ALLOWED_DIRECTORIES": "${user_config.allowed_directories}"
      }
    }
  },
  "tools": [
    {
      "name": "search_files",
      "description": "Search for files in a directory"
    }
  ],
  "prompts": [
    {
      "name": "poetry",
      "description": "Have the LLM write poetry",
      "arguments": ["topic"],
      "text": "Write a creative poem about the following topic: ${arguments.topic}"
    }
  ],
  "tools_generated": true,
  "keywords": ["api", "automation", "productivity"],
  "license": "MIT",
  "compatibility": {
    "claude_desktop": ">=1.0.0",
    "platforms": ["darwin", "win32", "linux"],
    "runtimes": {
      "node": ">=16.0.0"
    }
  },
  "user_config": {
    "allowed_directories": {
      "type": "directory",
      "title": "Allowed Directories",
      "description": "Directories the server can access",
      "multiple": true,
      "required": true,
      "default": ["${HOME}/Desktop"]
    },
    "api_key": {
      "type": "string",
      "title": "API Key",
      "description": "Your API key for authentication",
      "sensitive": true,
      "required": false
    },
    "max_file_size": {
      "type": "number",
      "title": "Maximum File Size (MB)",
      "description": "Maximum file size to process",
      "default": 10,
      "min": 1,
      "max": 100
    }
  }
}
```

要查看扩展和清单示例，请参阅 MCPB 仓库中的示例。
manifest.json 中所有必需和可选字段的完整规范可作为我们开源工具链的一部分找到。

### 构建你的第一个扩展

让我们通过一个示例，逐步将现有 MCP 服务器打包为桌面扩展。我们将使用一个简单的文件系统服务器作为示例。

#### 第一步：创建清单

首先，为你的服务器初始化一个清单：

```
npx @anthropic-ai/mcpb init
```

这个交互式工具会询问你的服务器信息，并生成完整的 manifest.json。如果你想快速生成最基本的 manifest.json，可以使用 --yes 参数运行该命令。

#### 第二步：处理用户配置

如果你的服务器需要用户输入（如 API 密钥或允许的目录），在清单中声明它：

```json
"user_config": {
  "allowed_directories": {
    "type": "directory",
    "title": "Allowed Directories",
    "description": "Directories the server can access",
    "multiple": true,
    "required": true,
    "default": ["${HOME}/Documents"]
  }
}
```

Claude Desktop 将：
- 显示用户友好的配置界面
- 在启用扩展之前验证输入
- 安全存储敏感值
- 根据开发者配置，将配置作为参数或环境变量传递给你的服务器

在下面的示例中，我们将用户配置作为环境变量传递，但也可以作为参数传递。

```json
"server": {
   "type": "node",
   "entry_point": "server/index.js",
   "mcp_config": {
   "command": "node",
   "args": ["${__dirname}/server/index.js"],
   "env": {
      "ALLOWED_DIRECTORIES": "${user_config.allowed_directories}"
   }
   }
}
```

#### 第三步：打包扩展

将所有内容打包为 .mcpb 文件：

```
npx @anthropic-ai/mcpb pack
```

此命令：
- 验证你的清单
- 生成 .mcpb 压缩包

#### 第四步：本地测试

将你的 .mcpb 文件拖入 Claude Desktop 的设置窗口。你将看到：
- 扩展的人类可读信息
- 所需权限和配置
- 一个简单的"安装"按钮

### 高级功能

#### 跨平台支持

扩展可以适配不同的操作系统：

```json
"server": {
  "type": "node",
  "entry_point": "server/index.js",
  "mcp_config": {
    "command": "node",
    "args": ["${__dirname}/server/index.js"],
    "platforms": {
      "win32": {
        "command": "node.exe",
        "env": {
          "TEMP_DIR": "${TEMP}"
        }
      },
      "darwin": {
        "env": {
          "TEMP_DIR": "${TMPDIR}"
        }
      }
    }
  }
}
```

#### 动态配置

使用模板字面量获取运行时值：
- ${__dirname}：扩展的安装目录
- ${user_config.key}：用户提供的配置
- ${HOME}、${TEMP}：系统环境变量

#### 功能声明

帮助用户提前了解功能：

```json
"tools": [
  {
    "name": "read_file",
    "description": "Read contents of a file"
  }
],
"prompts": [
  {
    "name": "code_review",
    "description": "Review code for best practices",
    "arguments": ["file_path"]
  }
]
```

### 扩展目录

我们推出时在 Claude Desktop 中内置了一个精选的扩展目录。用户可以浏览、搜索并一键安装——无需在 GitHub 上搜索或审查代码。

虽然我们预计桌面扩展规范和 Claude 在 macOS 及 Windows 上的实现会随时间演变，但我们期待看到扩展能以各种创意方式扩展 Claude 的功能。

提交你的扩展：
- 确保遵循提交表单中的指南
- 在 Windows 和 macOS 上进行测试
- 提交你的扩展
- 我们的团队将审核质量和安全性

### 构建开放生态系统

我们致力于围绕 MCP 服务器构建开放生态系统，并相信其被多个应用程序和服务普遍采用的能力已经惠及社区。秉承这一承诺，我们将桌面扩展规范、工具链以及 Claude 在 macOS 和 Windows 上实现桌面扩展支持所使用的架构和关键功能开源。我们希望 MCPB 格式不仅能让本地 MCP 服务器对 Claude 更具可移植性，也能为其他 AI 桌面应用程序所用。

我们开源的内容：
- 完整的 MCPB 规范
- 打包和验证工具
- 参考实现代码
- TypeScript 类型和架构定义

这意味着：
- 对于 MCP 服务器开发者：一次打包，即可在任何支持 MCPB 的平台上运行
- 对于应用开发者：无需从零开始即可添加扩展支持
- 对于用户：在所有支持 MCP 的应用程序中获得一致的体验

规范和工具链特意以 0.1 版本发布，因为我们期待与更广泛的社区合作来发展和改进该格式。我们期待听到你的反馈。

### 安全性和企业考量

我们理解扩展引入了新的安全考量，特别是对企业用户而言。我们在桌面扩展的预览版本中内置了多项安全保障：

#### 面向用户

- 敏感数据保存在操作系统密钥链中
- 自动更新
- 审查已安装扩展的能力

#### 面向企业

- 组策略（Windows）和 MDM（macOS）支持
- 预安装已批准扩展的能力
- 封禁特定扩展或发布者
- 完全禁用扩展目录
- 部署私有扩展目录

有关如何在组织中管理扩展的更多信息，请参阅我们的文档。

### 开始使用

准备好构建你自己的扩展了吗？以下是入门方法：

对于 MCP 服务器开发者：查阅我们的开发者文档——或者直接在本地 MCP 服务器目录中运行以下命令开始：

```
npm install -g @anthropic-ai/mcpb
mcpb init
mcpb pack
```

对于 Claude Desktop 用户：更新到最新版本，并在设置中查找"扩展"部分

对于企业用户：查阅我们的企业文档了解部署选项

### 使用 Claude Code 构建

在 Anthropic 内部，我们发现 Claude 能够在极少干预的情况下出色地构建扩展。如果你也想使用 Claude Code，我们建议你简要说明你希望扩展做什么，然后将以下上下文添加到提示词中：

```
I want to build this as a Desktop Extension, abbreviated as "MCPB". Please follow these steps:

1. **Read the specifications thoroughly:**
   - https://github.com/anthropics/mcpb/blob/main/README.md - MCPB architecture overview, capabilities, and integration patterns
   - https://github.com/anthropics/mcpb/blob/main/MANIFEST.md - Complete extension manifest structure and field definitions
   - https://github.com/anthropics/mcpb/tree/main/examples - Reference implementations including a "Hello World" example

2. **Create a proper extension structure:**
   - Generate a valid manifest.json following the MANIFEST.md spec
   - Implement an MCP server using @modelcontextprotocol/sdk with proper tool definitions
   - Include proper error handling and timeout management

3. **Follow best development practices:**
   - Implement proper MCP protocol communication via stdio transport
   - Structure tools with clear schemas, validation, and consistent JSON responses
   - Make use of the fact that this extension will be running locally
   - Add appropriate logging and debugging capabilities
   - Include proper documentation and setup instructions

4. **Test considerations:**
   - Validate that all tool calls return properly structured responses
   - Verify manifest loads correctly and host integration works

Generate complete, production-ready code that can be immediately tested. Focus on defensive programming, clear error messages, and following the exact
MCPB specifications to ensure compatibility with the ecosystem.
```

### 结语

桌面扩展代表了用户与本地 AI 工具交互方式的根本性转变。通过消除安装摩擦，我们将强大的 MCP 服务器变得人人可用——而不仅仅是开发者。

在内部，我们使用桌面扩展来分享高度实验性的 MCP 服务器——有些很有趣，有些很实用。一个团队尝试将模型直接连接到 GameBoy 看看能走多远，类似于我们的"Claude 玩宝可梦"研究。我们使用桌面扩展打包了一个单独的扩展，打开了流行的 PyBoy GameBoy 模拟器并让 Claude 接管控制。我们相信，将模型的能力与用户本地机器上已有的工具、数据和应用程序连接起来，存在着无数的机会。

我们迫不及待地想看到你的作品。那些为我们带来数千个 MCP 服务器的创造力，现在只需一次点击就能触达数百万用户。准备好分享你的 MCP 服务器了吗？提交你的扩展以供审核。

### 想了解更多？