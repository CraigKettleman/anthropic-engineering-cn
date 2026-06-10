#!/usr/bin/env python3
"""Scrape all Anthropic engineering articles and save as JSON."""
import json
import time
import requests
from bs4 import BeautifulSoup

ARTICLES = [
    {"slug": "how-we-contain-claude", "title": "How we contain Claude across products"},
    {"slug": "april-23-postmortem", "title": "An update on recent Claude Code quality reports"},
    {"slug": "managed-agents", "title": "Scaling Managed Agents: Decoupling the brain from the hands"},
    {"slug": "claude-code-auto-mode", "title": "How we built Claude Code auto mode: a safer way to skip permissions"},
    {"slug": "harness-design-long-running-apps", "title": "Harness design for long-running application development"},
    {"slug": "eval-awareness-browsecomp", "title": "Eval awareness in Claude Opus 4.6's BrowseComp performance"},
    {"slug": "infrastructure-noise", "title": "Quantifying infrastructure noise in agentic coding evals"},
    {"slug": "building-c-compiler", "title": "Building a C compiler with a team of parallel Claudes"},
    {"slug": "AI-resistant-technical-evaluations", "title": "Designing AI-resistant technical evaluations"},
    {"slug": "demystifying-evals-for-ai-agents", "title": "Demystifying evals for AI agents"},
    {"slug": "effective-harnesses-for-long-running-agents", "title": "Effective harnesses for long-running agents"},
    {"slug": "advanced-tool-use", "title": "Introducing advanced tool use on the Claude Developer Platform"},
    {"slug": "code-execution-with-mcp", "title": "Code execution with MCP: Building more efficient agents"},
    {"slug": "claude-code-sandboxing", "title": "Beyond permission prompts: making Claude Code more secure and autonomous"},
    {"slug": "equipping-agents-for-the-real-world-with-agent-skills", "title": "Equipping agents for the real world with Agent Skills"},
    {"slug": "effective-context-engineering-for-ai-agents", "title": "Effective context engineering for AI agents"},
    {"slug": "a-postmortem-of-three-recent-issues", "title": "A postmortem of three recent issues"},
    {"slug": "writing-tools-for-agents", "title": "Writing effective tools for agents — with agents"},
    {"slug": "desktop-extensions", "title": "Desktop Extensions: One-click MCP server installation for Claude Desktop"},
    {"slug": "multi-agent-research-system", "title": "How we built our multi-agent research system"},
    {"slug": "claude-code-best-practices", "title": "Claude Code: Best practices for agentic coding"},
    {"slug": "claude-think-tool", "title": 'The "think" tool: Enabling Claude to stop and think in complex tool use situations'},
    {"slug": "swe-bench-sonnet", "title": "Raising the bar on SWE-bench Verified with Claude 3.5 Sonnet"},
    {"slug": "building-effective-agents", "title": "Building effective agents"},
    {"slug": "contextual-retrieval", "title": "Introducing Contextual Retrieval"},
]

BASE = "https://www.anthropic.com/engineering/"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

def scrape_article(slug):
    url = BASE + slug
    try:
        resp = requests.get(url, headers=HEADERS, timeout=30)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "html.parser")
        
        # Try to find the main article content
        article = soup.find("article") or soup.find("main") or soup.find("body")
        
        # Extract text content, preserving some structure
        content_parts = []
        for elem in article.find_all(["h1", "h2", "h3", "h4", "p", "li", "pre", "code", "blockquote"]):
            tag = elem.name
            text = elem.get_text(strip=True)
            if not text:
                continue
            if tag in ("h1",):
                content_parts.append(f"\n# {text}\n")
            elif tag in ("h2",):
                content_parts.append(f"\n## {text}\n")
            elif tag in ("h3",):
                content_parts.append(f"\n### {text}\n")
            elif tag in ("h4",):
                content_parts.append(f"\n#### {text}\n")
            elif tag == "blockquote":
                content_parts.append(f"\n> {text}\n")
            elif tag == "pre":
                content_parts.append(f"\n```\n{text}\n```\n")
            elif tag == "li":
                content_parts.append(f"- {text}")
            else:
                content_parts.append(text)
        
        content = "\n".join(content_parts)
        
        # Get the raw HTML too for the mirror
        # Find the main content area HTML
        main_html = str(article)
        
        return {
            "slug": slug,
            "url": url,
            "title": soup.find("h1") or soup.find("h2"),
            "content_md": content,
            "raw_html": main_html,
            "success": True
        }
    except Exception as e:
        return {"slug": slug, "url": url, "error": str(e), "success": False}

# Fix title extraction
def fix_title(result):
    if result.get("title"):
        result["title"] = result["title"].get_text(strip=True)
    return result

if __name__ == "__main__":
    results = []
    for i, art in enumerate(ARTICLES):
        print(f"[{i+1}/{len(ARTICLES)}] Scraping {art['slug']}...")
        r = scrape_article(art["slug"])
        r = fix_title(r)
        if not r.get("title"):
            r["title"] = art["title"]
        results.append(r)
        time.sleep(1)  # polite delay
    
    with open("/Users/craig/anthropic-engineering-cn/articles_raw.json", "w") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    
    ok = sum(1 for r in results if r["success"])
    print(f"\nDone: {ok}/{len(results)} articles scraped successfully")
    
    # Print any failures
    for r in results:
        if not r["success"]:
            print(f"  FAILED: {r['slug']} - {r.get('error')}")
