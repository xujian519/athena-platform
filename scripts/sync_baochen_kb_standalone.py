#!/usr/bin/env python3
"""
宝宸知识库全量导入脚本（轻量独立版）
使用本地 BGE-M3 嵌入服务 (localhost:7866)，不依赖 Athena 重量级模块。

用法:
    python3 scripts/sync_baochen_kb_standalone.py
    python3 scripts/sync_baochen_kb_standalone.py --wiki /path/to/Wiki
    python3 scripts/sync_baochen_kb_standalone.py --batch-size 16
"""

import argparse
import gc
import hashlib
import json
import re
import sys
import time
import uuid
from pathlib import Path

import numpy as np
import requests

# ============ 配置 ============

DEFAULT_WIKI_PATH = "/Users/xujian/projects/宝宸知识库/Wiki"
DEFAULT_QDRANT_URL = "http://localhost:6333"
DEFAULT_EMBED_URL = "http://localhost:8766/v1"
COLLECTION_NAME = "baochen_wiki"
VECTOR_SIZE = 1024
EMBED_BATCH_SIZE = 8       # 小批次嵌入，降低内存峰值
EMBED_STRIDE = 80          # 每轮处理 80 个 chunk（= 10 个嵌入批次）
UPSERT_BATCH_SIZE = 40     # Qdrant 写入批次

SKIP_FILE_NAMES = {"CLAUDE.md", "log.md", "index.md"}
WIKI_LINK_PATTERN = re.compile(r"\[\[([^\]|]+?)(?:\|[^\]]+?)?\]\]")


# ============ 分块处理 ============

def collect_files(wiki_root: Path) -> list[tuple[Path, str]]:
    """收集所有 .md 文件"""
    files = []
    for md_file in sorted(wiki_root.rglob("*.md")):
        if md_file.name in SKIP_FILE_NAMES:
            continue
        rel = md_file.relative_to(wiki_root)
        kb_name = rel.parts[0] if len(rel.parts) > 1 else "根目录"
        files.append((md_file, kb_name))
    return files


def split_into_chunks(content: str, rel_path: str, kb_name: str,
                      chunk_size: int = 2000) -> list[dict]:
    """按 ## 标题分块"""
    lines = content.split("\n")
    title = ""
    for line in lines:
        if line.startswith("# ") and not line.startswith("## "):
            title = line.lstrip("# ").strip()
            break

    # 按 ## 标题分割
    sections = []
    cur_title = "摘要"
    cur_lines = []
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

    # 分块
    parts = Path(rel_path).parts
    kb_sub = parts[1] if len(parts) > 2 else ""
    source_book, source_prefix = infer_source(rel_path, kb_name)

    chunks = []
    chunk_idx = 0
    for sec_title, sec_text in sections:
        if not sec_text.strip():
            continue
        if len(sec_text) <= chunk_size:
            chunks.append(make_chunk(sec_text.strip(), rel_path, kb_name, kb_sub,
                                     title, sec_title, chunk_idx, source_book, source_prefix))
            chunk_idx += 1
        else:
            for sub in split_by_paragraphs(sec_text, chunk_size):
                chunks.append(make_chunk(sub.strip(), rel_path, kb_name, kb_sub,
                                         title, sec_title, chunk_idx, source_book, source_prefix))
                chunk_idx += 1
    return chunks


def split_by_paragraphs(text: str, max_size: int) -> list[str]:
    paras = text.split("\n\n")
    result, cur = [], ""
    for p in paras:
        if len(cur) + len(p) + 2 > max_size and cur:
            result.append(cur.strip())
            cur = p
        else:
            cur = cur + "\n\n" + p if cur else p
    if cur.strip():
        result.append(cur.strip())
    return result


def make_chunk(text, source_file, kb_cat, kb_sub, page_title, sec_title,
               idx, source_book, source_prefix) -> dict:
    wiki_links = list(set(WIKI_LINK_PATTERN.findall(text)))
    h = hashlib.sha256(text.encode("utf-8")).hexdigest()[:16]
    return {
        "text": text,
        "source_file": source_file,
        "kb_category": kb_cat,
        "kb_subcategory": kb_sub,
        "page_title": page_title,
        "section_title": sec_title,
        "chunk_index": idx,
        "char_count": len(text),
        "wiki_links": wiki_links,
        "source_book": source_book,
        "source_prefix": source_prefix,
        "content_hash": f"sha256:{h}",
    }


def infer_source(rel_path: str, kb_cat: str) -> tuple[str | None, str | None]:
    if kb_cat != "专利实务":
        return {"审查指南": "审查指南(2023版)", "专利侵权": "北高院侵权判定指南",
                "专利判决": "法院判决汇编", "复审无效": "复审无效决定汇编",
                "法律法规": "法律法规汇编", "书籍": "参考书籍"}.get(kb_cat), None
    fname = Path(rel_path).stem
    parts = fname.split("-", 2)
    if len(parts) >= 2:
        if parts[1] == "原理":
            return "崔国斌《专利法》", "原理-"
        if parts[1] == "法条":
            return "尹新天《中国专利法详解》", "法条-"
    return "《以案说法》", None


# ============ 嵌入 ============

def embed_texts(texts: list[str], embed_url: str, model: str = "bge-m3",
                batch_size: int = EMBED_BATCH_SIZE) -> np.ndarray:
    """调用本地 BGE-M3 OpenAI 兼容接口"""
    all_embeddings = []
    total = len(texts)

    for i in range(0, total, batch_size):
        batch = texts[i:i + batch_size]
        try:
            resp = requests.post(
                f"{embed_url}/embeddings",
                json={"model": model, "input": batch},
                timeout=120,
            )
            resp.raise_for_status()
            data = resp.json()
            sorted_data = sorted(data["data"], key=lambda x: x["index"])
            for item in sorted_data:
                all_embeddings.append(item["embedding"])
        except Exception as e:
            print(f"  ❌ 嵌入失败 (batch {i // batch_size + 1}/{(total-1)//batch_size+1}): {e}")
            for _ in batch:
                all_embeddings.append([0.0] * VECTOR_SIZE)

        done = min(i + batch_size, total)
        pct = done * 100 // total
        print(f"  📊 嵌入进度: {done}/{total} ({pct}%)", end="\r")

        if i + batch_size < total:
            time.sleep(0.05)

    print()
    return np.array(all_embeddings, dtype=np.float32)


# ============ Qdrant 操作 ============

def ensure_collection(qdrant_url: str) -> None:
    """确保 collection 存在"""
    url = f"{qdrant_url}/collections/{COLLECTION_NAME}"
    resp = requests.get(url, timeout=5)
    if resp.status_code == 200:
        print(f"✅ 集合 {COLLECTION_NAME} 已存在")
        return

    config = {
        "vectors": {"size": VECTOR_SIZE, "distance": "Cosine"},
        "optimizers_config": {"default_segment_number": 2, "indexing_threshold": 20000},
        "hnsw_config": {"m": 16, "ef_construct": 100},
    }
    resp = requests.put(url, json=config, timeout=30)
    if resp.status_code == 200:
        print(f"✅ 创建集合 {COLLECTION_NAME}")
    else:
        raise RuntimeError(f"创建集合失败: {resp.text}")


def clear_collection(qdrant_url: str) -> None:
    """清空 collection"""
    url = f"{qdrant_url}/collections/{COLLECTION_NAME}/points/delete"
    requests.post(url, json={"filter": {"must": []}}, timeout=30)
    print("🗑️  已清空现有数据")


def upsert_batch(qdrant_url: str, chunks: list[dict], embeddings: np.ndarray,
                 sync_version: int = 1) -> int:
    """批量写入 Qdrant"""
    points = []
    for chunk, emb in zip(chunks, embeddings):
        pid = str(uuid.uuid5(uuid.NAMESPACE_URL, f"{chunk['source_file']}#{chunk['chunk_index']}"))
        points.append({
            "id": pid,
            "vector": emb.tolist(),
            "payload": {
                "source_file": chunk["source_file"],
                "kb_category": chunk["kb_category"],
                "kb_subcategory": chunk["kb_subcategory"],
                "page_title": chunk["page_title"],
                "section_title": chunk["section_title"],
                "chunk_index": chunk["chunk_index"],
                "chunk_text": chunk["text"],
                "char_count": chunk["char_count"],
                "wiki_links": chunk["wiki_links"],
                "source_book": chunk["source_book"],
                "source_prefix": chunk["source_prefix"],
                "content_hash": chunk["content_hash"],
                "sync_version": sync_version,
                "ingested_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            },
        })

    url = f"{qdrant_url}/collections/{COLLECTION_NAME}/points"
    resp = requests.put(url, json={"points": points}, timeout=120)
    return len(points) if resp.status_code == 200 else 0


def save_sync_state(state: dict, state_path: Path) -> None:
    state_path.parent.mkdir(parents=True, exist_ok=True)
    with open(state_path, "w", encoding="utf-8") as f:
        json.dump(state, f, ensure_ascii=False, indent=2)


# ============ 主流程 ============

def main():
    parser = argparse.ArgumentParser(description="宝宸知识库全量导入（独立版）")
    parser.add_argument("--wiki", default=DEFAULT_WIKI_PATH, help="Wiki 目录路径")
    parser.add_argument("--qdrant", default=DEFAULT_QDRANT_URL, help="Qdrant 地址")
    parser.add_argument("--embed", default=DEFAULT_EMBED_URL, help="嵌入服务地址")
    parser.add_argument("--embed-model", default="bge-m3", help="嵌入模型名")
    parser.add_argument("--batch-size", type=int, default=EMBED_BATCH_SIZE, help="嵌入批次大小")
    args = parser.parse_args()

    wiki_path = Path(args.wiki)
    start = time.time()

    print("=" * 60)
    print("宝宸知识库全量导入")
    print(f"  Wiki:   {wiki_path}")
    print(f"  Qdrant: {args.qdrant}")
    print(f"  Embed:  {args.embed} ({args.embed_model})")
    print("=" * 60)

    if not wiki_path.is_dir():
        print(f"❌ Wiki 目录不存在: {wiki_path}")
        sys.exit(1)

    # 1. 收集文件
    print("\n📂 扫描文件...")
    files = collect_files(wiki_path)
    print(f"   找到 {len(files)} 个 .md 文件")

    # 2. 分块
    print("\n✂️  分块处理...")
    all_chunks = []
    for md_file, kb_name in files:
        try:
            content = md_file.read_text(encoding="utf-8")
        except Exception as e:
            print(f"   ⚠️ 跳过 {md_file.name}: {e}")
            continue
        rel = str(md_file.relative_to(wiki_path))
        chunks = split_into_chunks(content, rel, kb_name)
        all_chunks.extend(chunks)

    kb_counts = {}
    for c in all_chunks:
        kb_counts[c["kb_category"]] = kb_counts.get(c["kb_category"], 0) + 1

    print(f"   共 {len(all_chunks)} 个分块:")
    for kb, cnt in sorted(kb_counts.items(), key=lambda x: -x[1]):
        print(f"     {kb}: {cnt}")

    # 3. 准备 Qdrant
    print("\n🔧 准备 Qdrant...")
    ensure_collection(args.qdrant)
    clear_collection(args.qdrant)

    # 4. 分批嵌入 + 写入（小步进，低内存）
    print(f"\n🧠 开始嵌入（批次 {args.batch_size}，步进 {EMBED_STRIDE}）...")
    total_written = 0
    stride = EMBED_STRIDE

    for i in range(0, len(all_chunks), stride):
        batch_chunks = all_chunks[i:i + stride]
        texts = [c["text"] for c in batch_chunks]

        # 嵌入（内部按 embed_batch_size 分小批）
        embeddings = embed_texts(texts, args.embed, args.embed_model, args.batch_size)

        # 归一化
        norms = np.linalg.norm(embeddings, axis=1, keepdims=True)
        norms[norms == 0] = 1
        embeddings = embeddings / norms

        # 写入 Qdrant
        for j in range(0, len(batch_chunks), UPSERT_BATCH_SIZE):
            written = upsert_batch(
                args.qdrant,
                batch_chunks[j:j + UPSERT_BATCH_SIZE],
                embeddings[j:j + UPSERT_BATCH_SIZE],
            )
            total_written += written

        # 释放本轮内存
        del texts, embeddings, batch_chunks
        gc.collect()

        done = min(i + stride, len(all_chunks))
        elapsed_now = time.time() - start
        rate = done / elapsed_now if elapsed_now > 0 else 0
        eta = (len(all_chunks) - done) / rate if rate > 0 else 0
        print(f"  ✅ {done}/{len(all_chunks)} ({done*100//len(all_chunks)}%) | "
              f"{rate:.0f} chunk/s | ETA {eta:.0f}s")

    # 5. 保存状态
    elapsed = time.time() - start
    state_path = Path(__file__).parent.parent / "data" / "baochen_sync_state.json"
    save_sync_state({
        "last_sync": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "sync_type": "full_rebuild",
        "total_files": len(files),
        "total_chunks": len(all_chunks),
        "total_written": total_written,
        "elapsed_seconds": round(elapsed, 1),
        "kb_counts": kb_counts,
        "embed_model": args.embed_model,
        "embed_url": args.embed,
    }, state_path)

    print("\n" + "=" * 60)
    print(f"🎉 全量导入完成!")
    print(f"   文件数:   {len(files)}")
    print(f"   分块数:   {len(all_chunks)}")
    print(f"   写入数:   {total_written}")
    print(f"   耗时:     {elapsed:.1f}s")
    print(f"   状态文件: {state_path}")
    print("=" * 60)


if __name__ == "__main__":
    main()
