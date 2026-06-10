#!/usr/bin/env python3
"""Build bilingual Chinese/English mirror site — warm editorial design."""
import os
import json
import re
import html as html_mod

TRANSLATED_DIR = "/Users/craig/anthropic-engineering-cn/articles-cn"
ARTICLES_DIR = "/Users/craig/anthropic-engineering-cn/articles"
SITE_DIR = "/Users/craig/anthropic-engineering-cn/site"

ARTICLES_META = [
    {"slug": "how-we-contain-claude", "date": "2026"},
    {"slug": "april-23-postmortem", "date": "2026-04-23"},
    {"slug": "managed-agents", "date": "2026-04-08"},
    {"slug": "claude-code-auto-mode", "date": "2026-03-25"},
    {"slug": "harness-design-long-running-apps", "date": "2026-03-24"},
    {"slug": "eval-awareness-browsecomp", "date": "2026-03-06"},
    {"slug": "infrastructure-noise", "date": "2026-02-05"},
    {"slug": "building-c-compiler", "date": "2026-02-05"},
    {"slug": "AI-resistant-technical-evaluations", "date": "2026-01-21"},
    {"slug": "demystifying-evals-for-ai-agents", "date": "2026-01-09"},
    {"slug": "effective-harnesses-for-long-running-agents", "date": "2025-11-26"},
    {"slug": "advanced-tool-use", "date": "2025-11-24"},
    {"slug": "code-execution-with-mcp", "date": "2025-11-04"},
    {"slug": "claude-code-sandboxing", "date": "2025-10-20"},
    {"slug": "equipping-agents-for-the-real-world-with-agent-skills", "date": "2025-10-16"},
    {"slug": "effective-context-engineering-for-ai-agents", "date": "2025-09-29"},
    {"slug": "a-postmortem-of-three-recent-issues", "date": "2025-09-17"},
    {"slug": "writing-tools-for-agents", "date": "2025-09-11"},
    {"slug": "desktop-extensions", "date": "2025-06-26"},
    {"slug": "multi-agent-research-system", "date": "2025-06-13"},
    {"slug": "claude-code-best-practices", "date": "2025-04-18"},
    {"slug": "claude-think-tool", "date": "2025-03-20"},
    {"slug": "swe-bench-sonnet", "date": "2025-01-06"},
    {"slug": "building-effective-agents", "date": "2024-12-19"},
    {"slug": "contextual-retrieval", "date": "2024-09-19"},
]


# ─── Markdown parser ──────────────────────────────────────────────────

def md_to_html_blocks(md_text):
    lines = md_text.split('\n')
    blocks = []
    current_block = []
    in_code = False
    code_lang = ""

    def flush():
        nonlocal current_block
        text = '\n'.join(current_block).strip()
        if text:
            blocks.append(('p', inline_format(html_mod.escape(text))))
        current_block = []

    for line in lines:
        stripped = line.strip()
        if stripped.startswith('```'):
            if in_code:
                blocks.append(('pre', f'<code class="language-{html_mod.escape(code_lang)}">{html_mod.escape(chr(10).join(current_block))}</code>'))
                current_block = []
                in_code = False
            else:
                flush()
                code_lang = stripped[3:].strip()
                in_code = True
            continue
        if in_code:
            current_block.append(line)
            continue
        if stripped.startswith('#### '):
            flush(); blocks.append(('h4', html_mod.escape(stripped[5:])))
        elif stripped.startswith('### '):
            flush(); blocks.append(('h3', html_mod.escape(stripped[4:])))
        elif stripped.startswith('## '):
            flush(); blocks.append(('h2', html_mod.escape(stripped[3:])))
        elif stripped.startswith('# '):
            flush(); blocks.append(('h1', html_mod.escape(stripped[2:])))
        elif stripped.startswith('> '):
            flush(); blocks.append(('blockquote', html_mod.escape(stripped[2:])))
        elif stripped.startswith(('- ', '* ')):
            flush(); blocks.append(('li', inline_format(html_mod.escape(stripped[2:]))))
        elif re.match(r'^\d+\.', stripped):
            flush()
            text = re.sub(r'^\d+\.\s*', '', stripped)
            blocks.append(('oli', inline_format(html_mod.escape(text))))
        elif stripped:
            if current_block and current_block[-1] == '':
                flush()
            current_block.append(line)
        else:
            flush()
            current_block.append('')
    flush()
    return blocks


def inline_format(text):
    text = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', text)
    text = re.sub(r'\*(.+?)\*', r'<em>\1</em>', text)
    text = re.sub(r'`(.+?)`', r'<code class="inline">\1</code>', text)
    text = re.sub(r'\[(.+?)\]\((.+?)\)', r'<a href="\2" target="_blank">\1</a>', text)
    return text


def blocks_to_html(blocks):
    parts = []
    in_list = False
    list_type = None
    for tag, content in blocks:
        if tag == 'li':
            if not in_list or list_type != 'ul':
                if in_list: parts.append(f'</{list_type}>')
                parts.append('<ul>')
                in_list = True
                list_type = 'ul'
            parts.append(f'<li>{content}</li>')
        elif tag == 'oli':
            if not in_list or list_type != 'ol':
                if in_list: parts.append(f'</{list_type}>')
                parts.append('<ol>')
                in_list = True
                list_type = 'ol'
            parts.append(f'<li>{content}</li>')
        else:
            if in_list:
                parts.append(f'</{list_type}>')
                in_list = False
            if tag in ('h1', 'h2', 'h3', 'h4', 'p'):
                parts.append(f'<{tag}>{content}</{tag}>')
            elif tag == 'pre':
                parts.append(f'<pre>{content}</pre>')
            elif tag == 'blockquote':
                parts.append(f'<blockquote><p>{content}</p></blockquote>')
    if in_list:
        parts.append(f'</{list_type}>')
    return '\n'.join(parts)


def blocks_to_paired_html(blocks_cn, blocks_en, toc_cn=None):
    def tag_of(b): return b[0]
    def content_of(b): return b[1]

    # Build anchor map from toc_cn: heading text -> anchor id
    toc_anchors = {}
    if toc_cn:
        for tag, text, anchor in toc_cn:
            toc_anchors[text] = anchor

    def group_blocks(blocks):
        groups = []
        current = []
        current_type = None
        for b in blocks:
            t = tag_of(b)
            if t in ('li', 'oli'):
                if current_type == t:
                    current.append(b)
                else:
                    if current: groups.append((current_type, current))
                    current = [b]; current_type = t
            else:
                if current: groups.append((current_type, current)); current = []; current_type = None
                groups.append((t, [b]))
        if current: groups.append((current_type, current))
        return groups

    cn_heading_counter = [0]
    def render_group(t, items, is_cn=False):
        if t == 'li':
            return '<ul>' + ''.join(f'<li>{content_of(it)}</li>' for it in items) + '</ul>'
        elif t == 'oli':
            return '<ol>' + ''.join(f'<li>{content_of(it)}</li>' for it in items) + '</ol>'
        else:
            c = content_of(items[0])
            if t == 'pre': return f'<pre>{c}</pre>'
            elif t == 'blockquote': return f'<blockquote><p>{c}</p></blockquote>'
            elif t in ('h2','h3','h4'):
                if is_cn and toc_anchors:
                    plain = re.sub(r'<[^>]+>', '', c)
                    anchor = toc_anchors.get(plain)
                    if anchor:
                        return f'<{t} id="{anchor}">{c}</{t}>'
                return f'<{t}>{c}</{t}>'
            elif t == 'h1': return f'<h1>{c}</h1>'
            else: return f'<p>{c}</p>'

    groups_cn = group_blocks(blocks_cn)
    groups_en = group_blocks(blocks_en)
    max_len = max(len(groups_cn), len(groups_en))
    parts = []

    for i in range(max_len):
        if i < len(groups_en) and i < len(groups_cn):
            t_en, items_en = groups_en[i]
            t_cn, items_cn = groups_cn[i]
            en_html = render_group(t_en, items_en, is_cn=False)
            cn_html = render_group(t_cn, items_cn, is_cn=True)
            if t_en == 'pre':
                parts.append(f'<div class="bilingual-pair bilingual-code">{en_html}</div>')
            else:
                parts.append(f'<div class="bilingual-pair"><div class="lang-en-block">{en_html}</div><div class="lang-cn-block">{cn_html}</div></div>')
        elif i < len(groups_en):
            for it in groups_en[i][1]:
                tag, c = tag_of(it), content_of(it)
                if tag == 'pre': parts.append(f'<div class="lang-en-block"><pre>{c}</pre></div>')
                elif tag in ('h1','h2','h3','h4'): parts.append(f'<div class="lang-en-block"><{tag}>{c}</{tag}></div>')
                elif tag == 'li': parts.append(f'<div class="lang-en-block"><ul><li>{c}</li></ul></div>')
                elif tag == 'oli': parts.append(f'<div class="lang-en-block"><ol><li>{c}</li></ol></div>')
                else: parts.append(f'<div class="lang-en-block"><p>{c}</p></div>')
        elif i < len(groups_cn):
            for it in groups_cn[i][1]:
                tag, c = tag_of(it), content_of(it)
                if tag == 'pre': parts.append(f'<div class="lang-cn-block"><pre>{c}</pre></div>')
                elif tag in ('h1','h2','h3','h4'):
                    plain = re.sub(r'<[^>]+>', '', c)
                    anchor = toc_anchors.get(plain) if toc_anchors else None
                    if anchor:
                        parts.append(f'<div class="lang-cn-block"><{tag} id="{anchor}">{c}</{tag}></div>')
                    else:
                        parts.append(f'<div class="lang-cn-block"><{tag}>{c}</{tag}></div>')
                elif tag == 'li': parts.append(f'<div class="lang-cn-block"><ul><li>{c}</li></ul></div>')
                elif tag == 'oli': parts.append(f'<div class="lang-cn-block"><ol><li>{c}</li></ol></div>')
                else: parts.append(f'<div class="lang-cn-block"><p>{c}</p></div>')

    return '\n'.join(parts)


def extract_title(md_text):
    for line in md_text.split('\n'):
        line = line.strip()
        if line.startswith('# '):
            return line[2:]
    return "Untitled"


def extract_toc(blocks):
    toc = []
    counter = 0
    for tag, content in blocks:
        if tag in ('h2', 'h3'):
            counter += 1
            anchor = f"heading-{counter}"
            plain = re.sub(r'<[^>]+>', '', content)
            toc.append((tag, plain, anchor))
    return toc


def render_toc_html(toc):
    if not toc:
        return ''
    items = []
    for tag, text, anchor in toc:
        cls = 'toc-h3' if tag == 'h3' else 'toc-h2'
        items.append(f'<a class="{cls}" href="#{anchor}">{text}</a>')
    return '\n'.join(items)


def inject_anchors(html_content, toc):
    counter = [0]
    def replacer(m):
        counter[0] += 1
        tag = m.group(1)
        rest = m.group(2) or ''
        return f'<{tag} id="heading-{counter[0]}"{rest}>'
    return re.sub(r'<(h[23])((?:\s[^>]*)?)>', replacer, html_content)


# ─── Shared CSS ───────────────────────────────────────────────────────

def CSS_COMMON(has_dark=True):
    dark_toggle = """
        /* ── Dark mode ──────────────────────────────────────── */
        [data-theme="dark"] {
            --bg: #1a1a1a;
            --text: #e5e2dd;
            --text-secondary: #a09890;
            --border: #333;
            --accent: #f59e0b;
            --accent-hover: #d97706;
            --input-bg: #252525;
        }
        [data-theme="dark"] .site-header {
            background: rgba(26, 26, 26, 0.85);
        }
        [data-theme="dark"] .content pre {
            background: #111;
            color: #e5e2dd;
        }
        [data-theme="dark"] .mode-btn.active {
            background: var(--accent);
            color: #1a1a1a;
            border-color: var(--accent);
        }
        [data-theme="dark"] .controls button:hover {
            border-color: var(--accent);
        }
        [data-theme="dark"] .theme-toggle {
            color: var(--text-secondary);
            background: #333;
        }
        [data-theme="dark"] .theme-toggle:hover {
            color: var(--accent);
            background: #444;
        }
    """ if has_dark else ""

    return """
        :root {
            --bg: #faf9f7;
            --text: #1a1a1a;
            --text-secondary: #6b6560;
            --border: #e5e2dd;
            --accent: #d97706;
            --accent-hover: #b45309;
            --input-bg: #f5f3ef;
        }
        * { margin: 0; padding: 0; box-sizing: border-box; }
        html { scroll-behavior: smooth; }
        body {
            font-family: 'Georgia', 'Noto Serif SC', 'Source Han Serif SC', 'Songti SC', serif;
            background: var(--bg);
            color: var(--text);
            line-height: 1.9;
            -webkit-font-smoothing: antialiased;
            transition: background 0.3s, color 0.3s;
        }
        """ + dark_toggle


def build_article_page(slug, title_cn, title_en, content_cn_html, content_en_html, paired_html, toc_blocks_cn, toc_blocks_en, toc_cn, date):
    toc_en = extract_toc(toc_blocks_en)
    toc_html_cn = render_toc_html(toc_cn)
    toc_html_en = render_toc_html(toc_en)

    # paired_html already has anchors injected by blocks_to_paired_html
    # single-view content doesn't need anchors — TOC uses text matching

    return f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{html_mod.escape(title_cn)} - Anthropic 工程博客 中英双语</title>
    <style>
{CSS_COMMON()}
        /* ── Header ─────────────────────────────────────────── */
        .site-header {{
            position: sticky;
            top: 0;
            z-index: 999;
            background: rgba(250, 249, 247, 0.85);
            backdrop-filter: blur(12px);
            -webkit-backdrop-filter: blur(12px);
            border-bottom: 1px solid var(--border);
            padding: 1.2rem 2.5rem;
            display: flex;
            align-items: center;
            gap: 2rem;
            transition: background 0.3s, border-color 0.3s;
        }}
        .site-header .logo {{
            color: var(--accent);
            text-decoration: none;
            font-weight: 600;
            font-size: 1.15rem;
            letter-spacing: 2px;
        }}
        .controls {{
            margin-left: auto;
            display: flex;
            gap: 0.6rem;
            align-items: center;
        }}
        .controls button {{
            background: transparent;
            border: 1px solid var(--border);
            color: var(--text-secondary);
            padding: 0.5rem 1.1rem;
            border-radius: 0;
            cursor: pointer;
            font-size: 0.88rem;
            font-family: inherit;
            letter-spacing: 1px;
            transition: all 0.15s;
        }}
        .controls button:hover {{
            border-color: var(--accent);
            color: var(--text);
        }}
        .controls button.active {{
            background: var(--accent);
            color: #fff;
            border-color: var(--accent);
        }}
        .theme-toggle {{
            background: var(--border);
            border: none;
            cursor: pointer;
            font-size: 1.1rem;
            color: var(--text-secondary);
            width: 36px;
            height: 36px;
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            transition: background 0.2s, color 0.15s;
            line-height: 1;
        }}
        .theme-toggle:hover {{ color: var(--accent); background: var(--input-bg); }}

        /* ── Layout with sidebar ────────────────────────────── */
        .page-layout {{
            display: flex;
            max-width: 1280px;
            margin: 0 auto;
            padding: 2.5rem 2.5rem 5rem;
            gap: 3.5rem;
        }}

        /* ── TOC sidebar ────────────────────────────────────── */
        .toc-sidebar {{
            width: 240px;
            flex-shrink: 0;
            position: sticky;
            top: 90px;
            align-self: flex-start;
            max-height: calc(100vh - 110px);
            overflow-y: auto;
            padding-right: 1.2rem;
        }}
        .toc-sidebar .toc-label {{
            font-size: 0.8rem;
            text-transform: uppercase;
            letter-spacing: 3px;
            color: var(--text-secondary);
            margin-bottom: 1.2rem;
            padding-bottom: 0.6rem;
            border-bottom: 1px solid var(--border);
        }}
        .toc-sidebar a {{
            display: block;
            color: var(--text-secondary);
            text-decoration: none;
            font-size: 0.88rem;
            line-height: 1.6;
            padding: 0.3rem 0;
            transition: color 0.15s;
            border-left: 2px solid transparent;
            padding-left: 0.9rem;
        }}
        .toc-sidebar a:hover {{ color: var(--accent); }}
        .toc-sidebar a.active {{
            color: var(--accent);
            border-left-color: var(--accent);
        }}
        .toc-sidebar .toc-h3 {{
            padding-left: 1.8rem;
            font-size: 0.82rem;
        }}

        /* ── Main content ───────────────────────────────────── */
        .main-content {{
            flex: 1;
            min-width: 0;
            max-width: 860px;
        }}
        .back-link {{
            display: inline-block;
            color: var(--accent);
            text-decoration: none;
            margin-bottom: 1.8rem;
            font-size: 0.95rem;
            letter-spacing: 1px;
        }}
        .back-link:hover {{ color: var(--accent-hover); }}
        .meta {{
            color: var(--text-secondary);
            font-size: 0.92rem;
            margin-bottom: 0.4rem;
        }}
        .title-block {{
            margin-bottom: 2.5rem;
            padding-bottom: 2rem;
            border-bottom: 1px solid var(--border);
        }}
        .title-block h1 {{
            font-size: 2.3rem;
            line-height: 1.35;
            font-weight: 400;
            letter-spacing: 2px;
        }}
        .title-block .en-title {{
            color: var(--text-secondary);
            font-size: 1.1rem;
            margin-top: 0.5rem;
            font-style: italic;
        }}

        /* ── Bilingual pair (EN above, CN below) ───────────── */
        .bilingual-pair {{
            margin: 2rem 0;
        }}
        .lang-en-block {{
            color: var(--text-secondary);
            font-size: 1rem;
            line-height: 1.8;
            padding-bottom: 0.4rem;
            border-bottom: 1px dashed var(--border);
            margin-bottom: 0.6rem;
        }}
        .lang-cn-block {{
            color: var(--text);
            font-size: 1.08rem;
            line-height: 1.9;
        }}
        .bilingual-pair.bilingual-code {{
            border-bottom: none;
        }}
        .bilingual-pair.bilingual-code .lang-en-block {{
            border-bottom: none;
            padding-bottom: 0;
        }}

        /* ── Single language mode ───────────────────────────── */
        .single-view {{ display: none; }}
        .single-view .lang-zh,
        .single-view .lang-en {{ display: none; }}
        body.mode-zh .single-view {{ display: block; }}
        body.mode-zh .single-view .lang-zh {{ display: block; }}
        body.mode-en .single-view {{ display: block; }}
        body.mode-en .single-view .lang-en {{ display: block; }}
        body.mode-zh .bilingual-view,
        body.mode-en .bilingual-view {{ display: none; }}
        body.mode-zh .title-block .en-title {{ display: none; }}
        body.mode-en .title-block h1.cn {{ display: none; }}
        body.mode-en .title-block h1.en {{ display: block; }}
        .title-block h1.en {{ display: none; }}

        /* ── TOC visibility per mode ────────────────────────── */
        .toc-cn, .toc-en {{ display: none; }}
        body.mode-zh .toc-cn {{ display: block; }}
        body.mode-en .toc-en {{ display: block; }}
        body.mode-bi .toc-cn {{ display: block; }}

        /* ── Content typography ─────────────────────────────── */
        .content h2 {{
            font-size: 1.55rem;
            margin: 2.5rem 0 1rem;
            padding-bottom: 0.4rem;
            border-bottom: 2px solid var(--accent);
            letter-spacing: 2px;
            font-weight: 400;
            color: var(--accent);
            scroll-margin-top: 80px;
        }}
        .content h3 {{
            font-size: 1.28rem;
            margin: 2rem 0 0.8rem;
            font-weight: 400;
            letter-spacing: 1px;
            color: var(--accent);
            scroll-margin-top: 80px;
        }}
        .content h4 {{
            font-size: 1.1rem;
            margin: 1.5rem 0 0.6rem;
            font-weight: 400;
        }}
        .content p {{
            margin: 0.9rem 0;
        }}
        .content a {{
            color: var(--accent);
            text-decoration: none;
        }}
        .content a:hover {{
            color: var(--accent-hover);
            text-decoration: underline;
        }}
        .content pre {{
            background: #1a1a1a;
            color: #e5e2dd;
            border-radius: 0;
            padding: 1.2rem 1.4rem;
            overflow-x: auto;
            margin: 1.2rem 0;
            font-size: 0.9rem;
            line-height: 1.65;
            border-left: 3px solid var(--accent);
        }}
        .content code {{
            font-family: 'SF Mono', 'Fira Code', monospace;
            font-size: 0.88em;
        }}
        .content code.inline {{
            background: var(--input-bg);
            padding: 0.15em 0.4em;
            border-radius: 0;
        }}
        .content blockquote {{
            border-left: 3px solid var(--accent);
            padding: 0.5rem 1.2rem;
            margin: 1.2rem 0;
            color: var(--text-secondary);
        }}
        .content blockquote p {{ margin: 0; }}
        .content ul, .content ol {{
            margin: 0.8rem 0;
            padding-left: 2rem;
        }}
        .content li {{ margin: 0.35rem 0; }}
        .content strong {{ font-weight: 600; }}

        /* ── Footer ─────────────────────────────────────────── */
        .site-footer {{
            text-align: center;
            padding: 2.5rem;
            color: var(--text-secondary);
            font-size: 0.88rem;
            border-top: 1px solid var(--border);
            margin-top: 2.5rem;
        }}
        .site-footer a {{ color: var(--accent); }}
        kbd {{
            background: var(--input-bg);
            border: 1px solid var(--border);
            border-radius: 3px;
            padding: 0.1em 0.5em;
            font-size: 0.8rem;
            color: var(--text-secondary);
            font-family: inherit;
        }}

        /* ── Responsive ─────────────────────────────────────── */
        @media (max-width: 960px) {{
            .toc-sidebar {{ display: none; }}
            .page-layout {{ padding: 2rem 1.5rem 4rem; }}
        }}
        @media (max-width: 768px) {{
            .site-header {{ padding: 1rem 1.2rem; }}
            .page-layout {{ padding: 1.2rem; }}
            .title-block h1 {{ font-size: 1.7rem; }}
            .content h2 {{ font-size: 1.3rem; }}
            .controls button {{ padding: 0.35rem 0.7rem; font-size: 0.8rem; }}
        }}
    </style>
</head>
<body class="mode-bi">
    <nav class="site-header">
        <a class="logo" href="index.html">Anthropic 工程博客</a>
        <div class="controls">
            <button onclick="setMode('zh')" id="btn-zh">中文</button>
            <button onclick="setMode('en')" id="btn-en">English</button>
            <button onclick="setMode('bi')" id="btn-bi" class="active">对照</button>
            <button class="theme-toggle" onclick="toggleTheme()" id="theme-btn" title="切换暗色模式">☀</button>
        </div>
    </nav>

    <div class="page-layout">
        <aside class="toc-sidebar">
            <div class="toc-label">目录</div>
            <div class="toc-cn">{toc_html_cn}</div>
            <div class="toc-en">{toc_html_en}</div>
        </aside>

        <div class="main-content">
            <a href="index.html" class="back-link">← 返回文章列表</a>
            <div class="meta">{date}</div>
            <div class="title-block">
                <h1 class="cn">{html_mod.escape(title_cn)}</h1>
                <h1 class="en">{html_mod.escape(title_en)}</h1>
                <div class="en-title">{html_mod.escape(title_en)}</div>
            </div>

            <div class="bilingual-view content">
                {paired_html}
            </div>
            <div class="single-view content">
                <div class="lang-zh">{content_cn_html}</div>
                <div class="lang-en">{content_en_html}</div>
            </div>
        </div>
    </div>

    <div class="site-footer">
        原文来自 <a href="https://www.anthropic.com/engineering/{slug}" target="_blank">Anthropic Engineering</a>
        · 由 mimo-v2.5-pro 翻译
        · 快捷键: <kbd>Z</kbd> 中文 <kbd>E</kbd> English <kbd>B</kbd> 对照
    </div>

    <script>
    function setMode(m) {{
        document.body.className = 'mode-' + m;
        document.querySelectorAll('.controls button:not(.theme-toggle)').forEach(b => b.classList.remove('active'));
        document.getElementById('btn-' + m).classList.add('active');
        localStorage.setItem('lang-mode', m);
    }}
    function toggleTheme() {{
        const isDark = document.documentElement.getAttribute('data-theme') === 'dark';
        if (isDark) {{
            document.documentElement.removeAttribute('data-theme');
            document.getElementById('theme-btn').textContent = '☀';
            localStorage.setItem('theme', 'light');
        }} else {{
            document.documentElement.setAttribute('data-theme', 'dark');
            document.getElementById('theme-btn').textContent = '☾';
            localStorage.setItem('theme', 'dark');
        }}
    }}
    // Restore theme
    const savedTheme = localStorage.getItem('theme');
    if (savedTheme === 'dark') {{
        document.documentElement.setAttribute('data-theme', 'dark');
        document.getElementById('theme-btn').textContent = '☾';
    }}
    // Restore lang mode
    const saved = localStorage.getItem('lang-mode');
    if (saved) setMode(saved);
    document.addEventListener('keydown', e => {{
        if (e.target.tagName === 'INPUT' || e.target.tagName === 'TEXTAREA') return;
        if (e.key === 'z' || e.key === 'Z') setMode('zh');
        if (e.key === 'e' || e.key === 'E') setMode('en');
        if (e.key === 'b' || e.key === 'B') setMode('bi');
    }});

    // TOC click: scroll to heading in the active view
    document.querySelectorAll('.toc-sidebar a[href^="#"]').forEach(link => {{
        link.addEventListener('click', function(e) {{
            e.preventDefault();
            const headingText = this.textContent.trim();
            const mode = document.body.className;
            let container;
            if (mode === 'mode-zh') {{
                container = document.querySelector('.single-view .lang-zh');
            }} else if (mode === 'mode-en') {{
                container = document.querySelector('.single-view .lang-en');
            }} else {{
                container = document.querySelector('.bilingual-view');
            }}
            if (!container) return;
            const headings = container.querySelectorAll('h2, h3');
            for (const h of headings) {{
                if (h.textContent.trim() === headingText) {{
                    h.scrollIntoView({{ behavior: 'smooth', block: 'start' }});
                    break;
                }}
            }}
        }});
    }});

    // TOC scroll spy
    (function() {{
        const tocLinks = document.querySelectorAll('.toc-sidebar a');
        if (!tocLinks.length) return;
        const observer = new IntersectionObserver(entries => {{
            entries.forEach(entry => {{
                if (entry.isIntersecting) {{
                    const text = entry.target.textContent.trim();
                    tocLinks.forEach(l => l.classList.remove('active'));
                    for (const l of tocLinks) {{
                        if (l.textContent.trim() === text) {{
                            l.classList.add('active');
                            break;
                        }}
                    }}
                }}
            }});
        }}, {{ rootMargin: '-90px 0px -70% 0px' }});
        // Observe all visible headings
        function observeHeadings() {{
            const mode = document.body.className;
            let container;
            if (mode === 'mode-zh') container = document.querySelector('.single-view .lang-zh');
            else if (mode === 'mode-en') container = document.querySelector('.single-view .lang-en');
            else container = document.querySelector('.bilingual-view');
            if (!container) return;
            container.querySelectorAll('h2, h3').forEach(h => observer.observe(h));
        }}
        observeHeadings();
        // Re-observe when mode changes
        const origSetMode = window.setMode;
        window.setMode = function(m) {{
            observer.disconnect();
            origSetMode(m);
            observeHeadings();
        }};
    }})();
    </script>
</body>
</html>"""


def build_index(articles):
    cards = ""
    for a in articles:
        cards += f"""
        <a href="{a['slug']}.html" class="card">
            <div class="date">{a['date']}</div>
            <h2>{html_mod.escape(a['title_cn'])}</h2>
            <p class="en-title">{html_mod.escape(a['title_en'])}</p>
        </a>"""

    return f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Anthropic 工程博客 - 中英双语</title>
    <style>
{CSS_COMMON()}
        /* ── Header ─────────────────────────────────────────── */
        .site-header {{
            position: sticky;
            top: 0;
            z-index: 999;
            background: rgba(250, 249, 247, 0.85);
            backdrop-filter: blur(12px);
            -webkit-backdrop-filter: blur(12px);
            border-bottom: 1px solid var(--border);
            padding: 1.2rem 2.5rem;
            display: flex;
            align-items: center;
            gap: 2rem;
            transition: background 0.3s, border-color 0.3s;
        }}
        .site-header .logo {{
            color: var(--accent);
            text-decoration: none;
            font-weight: 600;
            font-size: 1.15rem;
            letter-spacing: 2px;
        }}
        .header-right {{
            margin-left: auto;
            display: flex;
            align-items: center;
            gap: 0.6rem;
        }}
        .theme-toggle {{
            background: var(--border);
            border: none;
            cursor: pointer;
            font-size: 1.1rem;
            color: var(--text-secondary);
            width: 36px;
            height: 36px;
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            transition: background 0.2s, color 0.15s;
            line-height: 1;
        }}
        .theme-toggle:hover {{ color: var(--accent); background: var(--input-bg); }}

        /* ── Hero ────────────────────────────────────────────── */
        .hero {{
            text-align: center;
            padding: 4rem 2rem 2rem;
            max-width: 960px;
            margin: 0 auto;
        }}
        .hero h1 {{
            font-size: 2.6rem;
            font-weight: 400;
            letter-spacing: 3px;
            margin-bottom: 0.6rem;
        }}
        .hero p {{
            color: var(--text-secondary);
            font-size: 1.1rem;
        }}
        .hero-divider {{
            max-width: 960px;
            margin: 0 auto;
            padding: 0 2rem;
        }}
        .hero-divider hr {{
            border: none;
            border-top: 1px solid var(--border);
        }}

        /* ── Article list ───────────────────────────────────── */
        .grid {{
            max-width: 960px;
            margin: 0 auto;
            padding: 1.2rem 2rem;
        }}
        .card {{
            display: block;
            text-decoration: none;
            color: var(--text);
            padding: 1.5rem 0;
            border-bottom: 1px solid var(--border);
            transition: padding-left 0.15s ease;
        }}
        .card:first-child {{ border-top: 1px solid var(--border); }}
        .card:hover {{ padding-left: 0.6rem; color: var(--accent); }}
        .card:hover .en-title {{ color: var(--accent); }}
        .card h2 {{
            font-size: 1.2rem;
            margin-bottom: 0.3rem;
            line-height: 1.45;
            font-weight: 400;
            letter-spacing: 1px;
        }}
        .card .date {{
            color: var(--text-secondary);
            font-size: 0.85rem;
            margin-bottom: 0.25rem;
        }}
        .card .en-title {{
            color: var(--text-secondary);
            font-size: 0.92rem;
            font-style: italic;
        }}

        /* ── Footer ─────────────────────────────────────────── */
        .site-footer {{
            text-align: center;
            padding: 2.5rem;
            color: var(--text-secondary);
            font-size: 0.88rem;
            border-top: 1px solid var(--border);
            margin-top: 2.5rem;
        }}
        .site-footer a {{ color: var(--accent); }}

        /* ── Responsive ─────────────────────────────────────── */
        @media (max-width: 768px) {{
            .site-header {{ padding: 1rem 1.2rem; }}
            .hero {{ padding: 2.5rem 1.2rem 1.2rem; }}
            .hero h1 {{ font-size: 1.8rem; }}
            .grid {{ padding: 1.2rem; }}
        }}
    </style>
</head>
<body>
    <nav class="site-header">
        <a class="logo" href="index.html">Anthropic 工程博客</a>
        <div class="header-right">
            <button class="theme-toggle" onclick="toggleTheme()" id="theme-btn" title="切换暗色模式">☀</button>
        </div>
    </nav>
    <div class="hero">
        <h1>Anthropic 工程博客</h1>
        <p>中英双语 · 共 {len(articles)} 篇文章 · 支持对照阅读</p>
    </div>
    <div class="hero-divider"><hr></div>
    <div class="grid">
        {cards}
    </div>
    <div class="site-footer">
        原文来自 <a href="https://www.anthropic.com/engineering" target="_blank">Anthropic Engineering</a>
        · 由 mimo-v2.5-pro 翻译
    </div>
    <script>
    function toggleTheme() {{
        const isDark = document.documentElement.getAttribute('data-theme') === 'dark';
        if (isDark) {{
            document.documentElement.removeAttribute('data-theme');
            document.getElementById('theme-btn').textContent = '☀';
            localStorage.setItem('theme', 'light');
        }} else {{
            document.documentElement.setAttribute('data-theme', 'dark');
            document.getElementById('theme-btn').textContent = '☾';
            localStorage.setItem('theme', 'dark');
        }}
    }}
    const savedTheme = localStorage.getItem('theme');
    if (savedTheme === 'dark') {{
        document.documentElement.setAttribute('data-theme', 'dark');
        document.getElementById('theme-btn').textContent = '☾';
    }}
    </script>
</body>
</html>"""


if __name__ == "__main__":
    os.makedirs(SITE_DIR, exist_ok=True)

    translated_files = set(os.listdir(TRANSLATED_DIR)) if os.path.exists(TRANSLATED_DIR) else set()
    articles_files = set(os.listdir(ARTICLES_DIR)) if os.path.exists(ARTICLES_DIR) else set()

    articles_for_index = []
    built = 0

    for meta in ARTICLES_META:
        slug = meta['slug']
        fname = f"{slug}.md"

        if fname not in translated_files or fname not in articles_files:
            print(f"  SKIP {slug}: missing file")
            continue

        with open(os.path.join(ARTICLES_DIR, fname), 'r') as f:
            md_en = f.read()
        with open(os.path.join(TRANSLATED_DIR, fname), 'r') as f:
            md_cn = f.read()

        title_en = extract_title(md_en)
        title_cn = extract_title(md_cn)

        blocks_cn = md_to_html_blocks(md_cn)
        blocks_en = md_to_html_blocks(md_en)

        # Strip leading h1 to avoid duplicating the title-block
        if blocks_cn and blocks_cn[0][0] == 'h1': blocks_cn = blocks_cn[1:]
        if blocks_en and blocks_en[0][0] == 'h1': blocks_en = blocks_en[1:]

        toc_cn = extract_toc(blocks_cn)
        content_cn_html = blocks_to_html(blocks_cn)
        content_en_html = blocks_to_html(blocks_en)
        paired_html = blocks_to_paired_html(blocks_cn, blocks_en, toc_cn)

        page = build_article_page(slug, title_cn, title_en, content_cn_html, content_en_html, paired_html, blocks_cn, blocks_en, toc_cn, meta['date'])

        with open(os.path.join(SITE_DIR, f"{slug}.html"), 'w') as f:
            f.write(page)

        articles_for_index.append({
            'slug': slug,
            'title_cn': title_cn,
            'title_en': title_en,
            'date': meta['date'],
        })
        built += 1

    index_html = build_index(articles_for_index)
    with open(os.path.join(SITE_DIR, "index.html"), 'w') as f:
        f.write(index_html)

    print(f"Built {built} bilingual article pages + index.html")
    print(f"Site at: {SITE_DIR}/")
