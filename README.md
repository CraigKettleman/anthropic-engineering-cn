# Anthropic Engineering 文章[中文版]

我将 [Anthropic Engineering](https://www.anthropic.com/engineering/) 的全部文章爬取并翻译为中文，做成了比较美观网页，支持中英对照阅读，如果对你有帮助，***非常感谢您给的star🤠***。

> **在线阅读** 👉 [GitHub Pages](https://CraigKettleman.github.io/anthropic-engineering-cn/)
<img width="735" height="478" alt="截屏2026-06-10 22 52 44" src="https://github.com/user-attachments/assets/597a65a2-ee16-4da2-846d-803bd72c97c8" />


## 1.文章简介


> 如何把大模型从“会聊天”变成“能长期稳定干活的软件工程师”。


Anthropic Engineering 收录了 Anthropic 工程团队在构建 Claude、Claude Code 和 AI Agent 过程中的实践经验与技术思考。文章关注如何通过上下文管理、工具使用、记忆机制和工程化设计，让 AI 真正成为能够长期协作、解决复杂问题的伙伴。对于想理解现代 AI 编程工具背后设计理念的朋友来说，相信这份资料能拨开你内心的谜团。

```bash
Prompt Engineering
↓
Context Engineering
↓
Harness Engineering
↓
Agent Engineering
↓
wait for you!

```


## 2.快速开始（读者）

**方式一：在线访问**（推荐）

直接访问上方链接即可，无需下载。

**方式二：下载离线阅读**

前往 [Releases](https://github.com/CraigKettleman/anthropic-engineering-cn/releases/latest) 下载最新 zip 包，解压后双击 `index.html` 即可。

**方式三：Clone 仓库**

```bash
git clone https://github.com/CraigKettleman/anthropic-engineering-cn.git
cd anthropic-engineering-cn/site
open index.html    # macOS，其他系统用浏览器打开
```

## 3.功能特性

- **三种阅读模式** — 中文 / English / 中英对照（英文在上、中文在下逐段对照）
- **暗色模式** — 一键切换，偏好自动保存
- **侧边栏目录** — 根据文章标题自动生成，支持页面内平滑跳转
- **键盘快捷键** — `Z` 中文、`E` English、`B` 对照
- **纯静态站点** — 无后端依赖，任何浏览器直接打开



## 4.自行构建（开发者/维护者）

如果你想自己抓取、翻译或修改站点，请按以下步骤操作。

### 开发依赖

- Python 3.10+
- `requests`、`beautifulsoup4`（抓取用）
- `hermes` CLI（翻译用，需配置 mimo-v2.5-pro 模型）

```bash
pip install requests beautifulsoup4
```

### 构建流程

```bash
# 1. 抓取文章
python scrape_articles.py

# 2. 翻译为中文（使用 mimo-v2.5-pro）
python translate.py

# 3. 构建静态站点
python build_site.py
```

生成的站点在 `site/` 目录下。

### 添加新文章

1. 在 `ARTICLES_META` 列表（`build_site.py` 顶部）中添加条目
2. 运行 `python scrape_articles.py` 抓取（会跳过已存在的文件）
3. 运行 `python translate.py` 翻译
4. 运行 `python build_site.py` 重新构建

## 5.目录结构

```
├── scrape_articles.py    # 文章抓取脚本
├── translate.py          # LLM 翻译脚本
├── build_site.py         # 静态站点生成器
├── articles/             # 英文原文（.md）
├── articles-cn/          # 中文翻译（.md）
└── site/                 # ← 读者只需关注这个目录
    ├── index.html        # 首页
    └── *.html            # 文章页
```

## 6.技术实现

- **抓取**：`requests` + `BeautifulSoup`，礼貌间隔 1 秒
- **翻译**：通过 `hermes` CLI 调用 mimo-v2.5-pro，3 并发 worker
- **构建**：纯 Python f-string 模板生成 HTML，自研 markdown 解析器，无第三方框架
- **样式**：CSS 内联，暖色系衬线字体设计，CSS 变量驱动明暗主题
  
## 7.后续

未来会翻译更多优质教程和文章，可能会合并到我的个人博客中，敬请期待🐣......

## License

原文版权归 [Anthropic](https://www.anthropic.com/) 所有。本项目仅供学习交流。
