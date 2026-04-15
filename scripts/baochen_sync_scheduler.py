#!/usr/bin/env python3
"""
宝宸知识库定时增量同步服务
Scheduled Sync Service for Bao Chen Knowledge Base

独立运行，不依赖 Athena 重量级模块。
使用 APScheduler 定时触发增量同步。

用法:
    python3 scripts/baochen_sync_scheduler.py start          # 启动调度服务
    python3 scripts/baochen_sync_scheduler.py status          # 查看调度状态
    python3 scripts/baochen_sync_scheduler.py trigger         # 手动触发一次同步
    python3 scripts/baochen_sync_scheduler.py install-cron    # 安装 cron 定时任务
    python3 scripts/baochen_sync_scheduler.py remove-cron     # 移除 cron 定时任务
"""

import argparse
import hashlib
import json
import os
import re
import subprocess
import sys
import time
import uuid
from datetime import datetime
from pathlib import Path

import numpy as np
import requests

# ============ 配置 ============

PROJECT_ROOT = Path(__file__).parent.parent
DEFAULT_WIKI_PATH = "/Users/xujian/projects/宝宸知识库/Wiki"
DEFAULT_QDRANT_URL = "http://localhost:6333"
DEFAULT_EMBED_URL = "http://localhost:8766/v1"
COLLECTION_NAME = "baochen_wiki"
VECTOR_SIZE = 1024
EMBED_BATCH_SIZE = 8
UPSERT_BATCH_SIZE = 40
STATE_FILE = PROJECT_ROOT / "data" / "baochen_sync_state.json"
SCHEDULE_LOG = PROJECT_ROOT / "logs" / "baochen_sync.log"
PID_FILE = PROJECT_ROOT / "data" / "baochen_scheduler.pid"

SKIP_FILE_NAMES = {"CLAUDE.md", "log.md", "index.md"}
WIKI_LINK_PATTERN = re.compile(r"\[\[([^\]|]+?)(?:\|[^\]]+?)?\]\]")

# 每周一(1)、周五(5) 上午 9:17 运行
CRON_SCHEDULE = "17 9 * * 1,5"
CRON_COMMAND = f"cd {PROJECT_ROOT} && /opt/homebrew/bin/python3.11 scripts/baochen_sync_scheduler.py trigger >> {SCHEDULE_LOG} 2>&1"


# ============ 分块（与 standalone 一致） ============

def collect_files(wiki_root: Path) -> list[tuple[Path, str]]:
    files = []
    for md_file in sorted(wiki_root.rglob("*.md")):
        if md_file.name in SKIP_FILE_NAMES:
            continue
        rel = md_file.relative_to(wiki_root)
        files.append((md_file, rel.parts[0] if len(rel.parts) > 1 else "根目录"))
    return files


def split_into_chunks(content: str, rel_path: str, kb_name: str,
                      chunk_size: int = 2000) -> list[dict]:
    lines = content.split("\n")
    title = ""
    for line in lines:
        if line.startswith("# ") and not line.startswith("## "):
            title = line.lstrip("# ").strip()
            break
    sections, cur_title, cur_lines = [], "摘要", []
    for line in lines:
        if line.startswith("## ") and not line.startswith("### "):
            if cur_lines:
                sections.append((cur_title, "\n".join(cur_lines)))
            cur_title = line.lstrip("# ").strip()
            cur_lines = [line]
        else:
            cur_lines.append(line)
    if cur_lines:
        sections.append((cur_title, "\n".join(cur_lines)))
    parts = Path(rel_path).parts
    kb_sub = parts[1] if len(parts) > 2 else ""
    source_book, source_prefix = infer_source(rel_path, kb_name)
    chunks, idx = [], 0
    for sec_title, sec_text in sections:
        if not sec_text.strip():
            continue
        if len(sec_text) <= chunk_size:
            chunks.append(_mkchunk(sec_text.strip(), rel_path, kb_name, kb_sub,
                                   title, sec_title, idx, source_book, source_prefix))
            idx += 1
        else:
            for sub in _split_paras(sec_text, chunk_size):
                if sub.strip():
                    chunks.append(_mkchunk(sub.strip(), rel_path, kb_name, kb_sub,
                                           title, sec_title, idx, source_book, source_prefix))
                    idx += 1
    return chunks


def _split_paras(text, max_size):
    paras, result, cur = text.split("\n\n"), [], ""
    for p in paras:
        if len(cur) + len(p) + 2 > max_size and cur:
            result.append(cur.strip())
            cur = p
        else:
            cur = cur + "\n\n" + p if cur else p
    if cur.strip():
        result.append(cur.strip())
    return result


def _mkchunk(text, sf, kc, ks, pt, st, idx, sb, sp):
    return {"text": text, "source_file": sf, "kb_category": kc, "kb_subcategory": ks,
            "page_title": pt, "section_title": st, "chunk_index": idx, "char_count": len(text),
            "wiki_links": list(set(WIKI_LINK_PATTERN.findall(text))),
            "source_book": sb, "source_prefix": sp,
            "content_hash": f"sha256:{hashlib.sha256(text.encode()).hexdigest()[:16]}"}


def infer_source(rel_path, kb_cat):
    if kb_cat != "专利实务":
        return {"审查指南": "审查指南(2023版)", "专利侵权": "北高院侵权判定指南",
                "专利判决": "法院判决汇编", "复审无效": "复审无效决定汇编",
                "法律法规": "法律法规汇编", "书籍": "参考书籍"}.get(kb_cat), None
    parts = Path(rel_path).stem.split("-", 2)
    if len(parts) >= 2:
        if parts[1] == "原理": return "崔国斌《专利法》", "原理-"
        if parts[1] == "法条": return "尹新天《中国专利法详解》", "法条-"
    return "《以案说法》", None


# ============ 嵌入 & Qdrant ============

def embed_texts(texts, embed_url, model="bge-m3", batch_size=EMBED_BATCH_SIZE):
    all_embs = []
    for i in range(0, len(texts), batch_size):
        batch = texts[i:i + batch_size]
        try:
            resp = requests.post(f"{embed_url}/embeddings",
                                 json={"model": model, "input": batch}, timeout=120)
            resp.raise_for_status()
            for item in sorted(resp.json()["data"], key=lambda x: x["index"]):
                all_embs.append(item["embedding"])
        except Exception as e:
            print(f"  ❌ 嵌入失败 batch {i // batch_size + 1}: {e}")
            all_embs.extend([[0.0] * VECTOR_SIZE] * len(batch))
        if i + batch_size < len(texts):
            time.sleep(0.05)
    return np.array(all_embs, dtype=np.float32)


def upsert_batch(qdrant_url, chunks, embeddings, sync_version):
    points = []
    for c, e in zip(chunks, embeddings):
        points.append({"id": str(uuid.uuid5(uuid.NAMESPACE_URL, f"{c['source_file']}#{c['chunk_index']}")),
                        "vector": e.tolist(),
                        "payload": {k: c[k] for k in ("source_file", "kb_category", "kb_subcategory",
                        "page_title", "section_title", "chunk_index", "text",
                        "char_count", "wiki_links", "source_book", "source_prefix", "content_hash")}
                        | {"sync_version": sync_version,
                           "ingested_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())}})
    resp = requests.put(f"{qdrant_url}/collections/{COLLECTION_NAME}/points",
                        json={"points": points}, timeout=120)
    return len(points) if resp.status_code == 200 else 0


def delete_by_source(qdrant_url, source_file):
    requests.post(f"{qdrant_url}/collections/{COLLECTION_NAME}/points/delete",
                  json={"filter": {"must": [{"key": "source_file", "match": {"value": source_file}}]}},
                  timeout=30)


# ============ 增量同步核心 ============

def load_state() -> dict:
    if STATE_FILE.exists():
        try:
            with open(STATE_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {}


def save_state(state: dict):
    STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(STATE_FILE, "w", encoding="utf-8") as f:
        json.dump(state, f, ensure_ascii=False, indent=2)


def file_hash(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def run_incremental_sync(wiki_path: str = DEFAULT_WIKI_PATH,
                         qdrant_url: str = DEFAULT_QDRANT_URL,
                         embed_url: str = DEFAULT_EMBED_URL) -> dict:
    """执行一次增量同步"""
    start = time.time()
    wiki = Path(wiki_path)

    if not wiki.is_dir():
        return {"status": "error", "message": f"Wiki 不可用: {wiki}"}

    old_state = load_state()
    old_files = old_state.get("files", {})

    # 收集当前文件
    current_files = {}
    for md_file, kb_name in collect_files(wiki):
        rel = str(md_file.relative_to(wiki))
        current_files[rel] = md_file

    # 检测变更
    added = set(current_files) - set(old_files)
    deleted = set(old_files) - set(current_files)
    modified = set()
    for rel in set(current_files) & set(old_files):
        if file_hash(current_files[rel]) != old_files[rel].get("content_hash", ""):
            modified.add(rel)

    if not added and not modified and not deleted:
        elapsed = time.time() - start
        return {"status": "no_changes", "message": "无变更", "elapsed": round(elapsed, 1)}

    print(f"[{datetime.now():%Y-%m-%d %H:%M:%S}] 增量同步: +{len(added)} ~{len(modified)} -{len(deleted)}")

    # 处理删除
    for rel in deleted:
        delete_by_source(qdrant_url, rel)

    # 处理新增和修改
    changed = added | modified
    all_chunks = []
    for rel in changed:
        chunks = split_into_chunks(current_files[rel].read_text("utf-8"), rel, "")
        # 补充 kb_category
        kb = Path(rel).parts[0] if len(Path(rel).parts) > 1 else "根目录"
        for c in chunks:
            c["kb_category"] = kb
        all_chunks.extend(chunks)

    # 删除修改文件的旧数据
    for rel in modified:
        delete_by_source(qdrant_url, rel)

    # 嵌入并写入
    total_written = 0
    sync_version = old_state.get("sync_version", 1) + 1
    gc = __import__("gc")

    for i in range(0, len(all_chunks), 80):
        batch = all_chunks[i:i + 80]
        texts = [c["text"] for c in batch]
        embs = embed_texts(texts, embed_url)
        norms = np.linalg.norm(embs, axis=1, keepdims=True)
        norms[norms == 0] = 1
        embs = embs / norms
        for j in range(0, len(batch), UPSERT_BATCH_SIZE):
            total_written += upsert_batch(qdrant_url, batch[j:j + UPSERT_BATCH_SIZE],
                                          embs[j:j + UPSERT_BATCH_SIZE], sync_version)
        del texts, embs, batch
        gc.collect()

    # 更新状态
    new_file_state = dict(old_files)
    for rel in deleted:
        new_file_state.pop(rel, None)
    for rel in changed:
        new_file_state[rel] = {
            "content_hash": file_hash(current_files[rel]),
            "chunk_count": sum(1 for c in all_chunks if c["source_file"] == rel),
            "byte_size": current_files[rel].stat().st_size,
        }

    elapsed = time.time() - start
    new_state = {
        "last_sync": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "sync_type": "incremental",
        "sync_version": sync_version,
        "total_files": len(current_files),
        "added": len(added),
        "modified": len(modified),
        "deleted": len(deleted),
        "total_written": total_written,
        "elapsed_seconds": round(elapsed, 1),
        "files": new_file_state,
        "embed_model": "bge-m3",
        "embed_url": embed_url,
    }
    save_state(new_state)

    print(f"[{datetime.now():%Y-%m-%d %H:%M:%S}] 同步完成: {total_written} chunks, {elapsed:.1f}s")
    return new_state


# ============ Cron 管理 ============

def get_cron_jobs() -> list[str]:
    """获取当前用户的 crontab 中与宝宸同步相关的条目"""
    try:
        result = subprocess.run(["crontab", "-l"], capture_output=True, text=True, timeout=5)
        if result.returncode != 0:
            return []
        return [line for line in result.stdout.strip().split("\n")
                if "baochen_sync_scheduler" in line and not line.startswith("#")]
    except Exception:
        return []


def install_cron():
    """安装 cron 定时任务"""
    existing = get_cron_jobs()
    if existing:
        print(f"⚠️  已存在 cron 条目:")
        for line in existing:
            print(f"   {line}")
        return

    # 获取当前 crontab
    try:
        result = subprocess.run(["crontab", "-l"], capture_output=True, text=True, timeout=5)
        current = result.stdout if result.returncode == 0 else ""
    except Exception:
        current = ""

    # 追加新条目
    new_entry = f"\n# 宝宸知识库定时同步（每周一、周五 09:17）\n{CRON_SCHEDULE} {CRON_COMMAND}\n"
    full = current.rstrip("\n") + new_entry

    # 写入
    proc = subprocess.run(["crontab", "-"], input=full, capture_output=True, text=True, timeout=10)
    if proc.returncode == 0:
        print(f"✅ Cron 已安装: {CRON_SCHEDULE}")
        print(f"   命令: {CRON_COMMAND}")
    else:
        print(f"❌ 安装失败: {proc.stderr}")


def remove_cron():
    """移除 cron 定时任务"""
    try:
        result = subprocess.run(["crontab", "-l"], capture_output=True, text=True, timeout=5)
        if result.returncode != 0:
            print("无 crontab 条目")
            return
        lines = result.stdout.split("\n")
        # 过滤掉相关行和紧跟的注释行
        filtered = []
        skip_next = False
        for line in lines:
            if "baochen_sync_scheduler" in line:
                # 也移除上一行如果是注释
                if filtered and filtered[-1].startswith("#") and "宝宸" in filtered[-1]:
                    filtered.pop()
                continue
            filtered.append(line)

        full = "\n".join(filtered)
        proc = subprocess.run(["crontab", "-"], input=full, capture_output=True, text=True, timeout=10)
        if proc.returncode == 0:
            print("✅ Cron 已移除")
        else:
            print(f"❌ 移除失败: {proc.stderr}")
    except Exception as e:
        print(f"❌ 操作失败: {e}")


def show_status():
    """显示调度状态"""
    print("\n" + "=" * 60)
    print("宝宸知识库同步调度状态")
    print("=" * 60)

    # Cron 状态
    cron_jobs = get_cron_jobs()
    print(f"\n📅 Cron 定时任务:")
    if cron_jobs:
        for line in cron_jobs:
            print(f"   {line}")
        print(f"   → 每周一、周五 09:17 运行")
    else:
        print("   未安装（运行 install-cron 安装）")

    # 上次同步状态
    state = load_state()
    if state:
        print(f"\n📊 上次同步:")
        print(f"   时间:   {state.get('last_sync', '未知')}")
        print(f"   类型:   {state.get('sync_type', '未知')}")
        print(f"   版本:   v{state.get('sync_version', '?')}")
        print(f"   文件数: {state.get('total_files', 0)}")
        if state.get("added") or state.get("modified") or state.get("deleted"):
            print(f"   +{state.get('added', 0)} ~{state.get('modified', 0)} -{state.get('deleted', 0)}")
        print(f"   写入:   {state.get('total_written', '?')} chunks")
        print(f"   耗时:   {state.get('elapsed_seconds', '?')}s")
    else:
        print("\n📊 无同步记录")

    # Qdrant 状态
    try:
        resp = requests.get(f"{DEFAULT_QDRANT_URL}/collections/{COLLECTION_NAME}", timeout=5)
        if resp.status_code == 200:
            info = resp.json()["result"]
            print(f"\n🗄️  Qdrant:")
            print(f"   集合:   {COLLECTION_NAME}")
            print(f"   向量数: {info['points_count']}")
    except Exception:
        print("\n🗄️  Qdrant: 不可达")

    # Wiki 状态
    wiki = Path(DEFAULT_WIKI_PATH)
    print(f"\n📂 Wiki: {'可用' if wiki.is_dir() else '不可用'} ({DEFAULT_WIKI_PATH})")

    print("=" * 60)


# ============ 主入口 ============

def main():
    parser = argparse.ArgumentParser(description="宝宸知识库定时同步服务")
    sub = parser.add_subparsers(dest="command")
    sub.add_parser("status", help="查看调度状态")
    sub.add_parser("trigger", help="手动触发一次增量同步")
    sub.add_parser("install-cron", help="安装 cron 定时任务（每周一/五 09:17）")
    sub.add_parser("remove-cron", help="移除 cron 定时任务")

    args = parser.parse_args()

    if args.command == "status":
        show_status()
    elif args.command == "trigger":
        run_incremental_sync()
    elif args.command == "install-cron":
        install_cron()
    elif args.command == "remove-cron":
        remove_cron()
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
