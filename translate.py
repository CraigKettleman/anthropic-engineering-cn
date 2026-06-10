#!/usr/bin/env python3
"""Translate articles using hermes CLI with mimo-v2.5-pro model."""
import subprocess
import os
import time
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed

ARTICLES_DIR = "/Users/craig/anthropic-engineering-cn/articles"
TRANSLATED_DIR = "/Users/craig/anthropic-engineering-cn/articles-cn"
MODEL = "mimo-v2.5-pro"
PROVIDER = "mimo"
MAX_WORKERS = 3

SYSTEM_PROMPT = """请将以下英文技术文档翻译成中文。翻译规则：
1. 忠实翻译所有内容，保持技术准确性
2. 代码块、URL、API名称、工具名称、变量名等保持英文原文
3. 标题、解释、描述翻译成自然流畅的中文
4. 保持Markdown格式不变
5. 专业术语首次出现时可附英文原文，如：智能体（Agent）
6. 直接输出翻译结果，不要添加任何解释或前缀

---

"""

os.makedirs(TRANSLATED_DIR, exist_ok=True)

all_articles = sorted([f for f in os.listdir(ARTICLES_DIR) if f.endswith('.md')])
already_done = set(os.listdir(TRANSLATED_DIR))
todo = [f for f in all_articles if f not in already_done]

print(f"Total: {len(all_articles)}, Done: {len(already_done)}, Remaining: {len(todo)}")
print(f"Workers: {MAX_WORKERS}\n")

lock = threading.Lock()

def translate_one(fname):
    slug = fname.replace('.md', '')
    src = os.path.join(ARTICLES_DIR, fname)
    dst = os.path.join(TRANSLATED_DIR, fname)
    
    with open(src, 'r') as f:
        content = f.read()
    
    if len(content) < 100:
        return slug, "SKIP", 0
    
    # Write combined prompt to temp file
    prompt_file = f"/tmp/prompt_{slug}.txt"
    with open(prompt_file, 'w') as f:
        f.write(SYSTEM_PROMPT + content)
    
    start = time.time()
    try:
        # Use hermes chat -q with file content via $(cat)
        cmd = f'export PATH="/Users/craig/.local/bin:/opt/homebrew/bin:$PATH" && hermes chat -q "$(cat {prompt_file})" -m {MODEL} --provider {PROVIDER} -Q --max-turns 1'
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=600)
        
        translated = result.stdout.strip()
        # Strip session_id line if present
        if translated.startswith("session_id:"):
            translated = translated.split("\n", 1)[1].strip()
        
        if translated and len(translated) > 200:
            with open(dst, 'w') as f:
                f.write(translated)
            elapsed = time.time() - start
            return slug, "OK", elapsed
        else:
            stderr_hint = result.stderr[:200] if result.stderr else ""
            return slug, f"SHORT({len(translated)} chars, stderr: {stderr_hint[:80]})", time.time() - start
    except subprocess.TimeoutExpired:
        return slug, "TIMEOUT", 600
    except Exception as e:
        return slug, f"ERROR:{e}", time.time() - start
    finally:
        try: os.remove(prompt_file)
        except: pass

with ThreadPoolExecutor(max_workers=MAX_WORKERS) as pool:
    futures = {pool.submit(translate_one, f): f for f in todo}
    for future in as_completed(futures):
        slug, status, elapsed = future.result()
        with lock:
            done_count = len(os.listdir(TRANSLATED_DIR))
            print(f"[{done_count}/{len(all_articles)}] {slug}: {status} ({elapsed:.0f}s)", flush=True)

final = len(os.listdir(TRANSLATED_DIR))
print(f"\n=== Done: {final}/{len(all_articles)} ===")
if final < len(all_articles):
    missing = set(all_articles) - set(os.listdir(TRANSLATED_DIR))
    print(f"Missing: {missing}")
