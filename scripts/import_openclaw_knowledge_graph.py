#!/usr/bin/env python3
"""
OpenClaw 专利知识图谱 → Athena 统一图谱 (优化版)

节点已导入（38,695个），本脚本只导入:
  - 关系 → Neo4j (40万条，用 CREATE + 索引加速)
  - 向量 → Qdrant (4万条)
"""

import pickle
import json
import time
import hashlib
import gc
import numpy as np
from pathlib import Path

WORKSPACE = Path.home() / ".openclaw" / "workspace" / "memory" / "patent-knowledge-graph"
GRAPH_FILE = WORKSPACE / "patent_knowledge_graph_updated.gpickle"
FRONTEND_DIR = WORKSPACE / "frontend"
VECTOR_FILE = FRONTEND_DIR / "search_index_full.npy"
NODE_MAP_FILE = FRONTEND_DIR / "node_id_map_full.json"

NEO4J_URI = "bolt://localhost:7687"
NEO4J_AUTH = ("neo4j", "athena_neo4j_2024")
QDRANT_URL = "http://localhost:6333"
QDRANT_COLLECTION = "legal_knowledge"

EDGE_BATCH = 5000
VEC_BATCH = 500

def log(msg: str):
    print(f"[{time.strftime('%H:%M:%S')}] {msg}", flush=True)


# ========== Step 1: 关系导入 ==========
def import_edges(g):
    from neo4j import GraphDatabase

    log("Step 1: 导入关系到 Neo4j (CREATE + 索引)")
    driver = GraphDatabase.driver(NEO4J_URI, auth=NEO4J_AUTH)

    # 按类型分组并去重
    edges_by_rel: dict[str, list] = {}
    seen: set[tuple[str, str, str]] = set()
    for u, v, ed in g.edges(data=True):
        rel = ed.get("relation", "RELATED_TO")
        key = (str(u), str(v), rel)
        if key in seen:
            continue
        seen.add(key)
        props = {k: val for k, val in ed.items()
                 if k != "relation" and isinstance(val, (str, int, float, bool))}
        edges_by_rel.setdefault(rel, []).append({"s": str(u), "t": str(v), "p": props})

    total = sum(len(v) for v in edges_by_rel.values())
    log(f"  共 {total} 条去重关系, {len(edges_by_rel)} 种类型")

    imported = 0
    t0 = time.time()

    with driver.session() as session:
        for rel_type, edges in edges_by_rel.items():
            log(f"  {rel_type}: {len(edges)} 条")
            for i in range(0, len(edges), EDGE_BATCH):
                batch = edges[i : i + EDGE_BATCH]
                session.run(
                    f"UNWIND $batch AS e "
                    f"MATCH (a:OpenClawNode {{id: e.s}}) "
                    f"MATCH (b:OpenClawNode {{id: e.t}}) "
                    f"CREATE (a)-[r:{rel_type}]->(b) "
                    f"SET r += e.p",
                    batch=batch,
                )
                imported += len(batch)
                elapsed = time.time() - t0
                speed = imported / elapsed if elapsed > 0 else 0
                remain = (total - imported) / speed if speed > 0 else 0
                log(f"    {imported}/{total} ({speed:.0f}/s, 剩余{remain:.0f}s)")

    driver.close()
    log(f"  ✅ 关系导入完成: {imported}")
    return imported


# ========== Step 2: 向量导入 ==========
def import_vectors(vectors, nmap):
    import requests

    log("Step 2: 导入向量到 Qdrant")

    # 检查已有
    r = requests.get(f"{QDRANT_URL}/collections/{QDRANT_COLLECTION}")
    existing = r.json()["result"]["points_count"] if r.status_code == 200 else 0
    if existing >= 40000:
        log(f"  ⏭️ 已有 {existing} 条，跳过")
        return existing

    total = vectors.shape[0]
    log(f"  共 {total} 条向量, 已有 {existing} 条")

    # 节点属性（用于 payload）
    with open(GRAPH_FILE, "rb") as f:
        g = pickle.load(f)
    node_data = {str(nid): {"nt": nd.get("node_type", ""), "t": nd.get("title", nd.get("name", ""))[:200]}
                 for nid, nd in g.nodes(data=True)}
    del g
    gc.collect()

    node_ids = list(nmap.keys())
    imported = 0
    t0 = time.time()

    for i in range(0, len(node_ids), VEC_BATCH):
        batch_ids = node_ids[i : i + VEC_BATCH]
        points = []
        for node_id in batch_ids:
            idx = nmap[node_id]
            if idx >= len(vectors):
                continue
            nd = node_data.get(node_id, {})
            pid = int(hashlib.md5(f"openclaw_{node_id}".encode()).hexdigest()[:16], 16)
            points.append({
                "id": pid,
                "vector": vectors[idx].tolist(),
                "payload": {"source": "openclaw", "node_id": node_id,
                            "node_type": nd.get("nt", ""), "title": nd.get("t", "")},
            })

        if points:
            requests.put(
                f"{QDRANT_URL}/collections/{QDRANT_COLLECTION}/points",
                json={"points": points}, timeout=120,
            )

        imported += len(points)
        elapsed = time.time() - t0
        if imported % 5000 == 0 or imported >= total:
            speed = imported / elapsed if elapsed > 0 else 0
            log(f"    {imported}/{total} ({speed:.0f}/s)")

    log(f"  ✅ 向量导入完成: {imported}")
    return imported


def main():
    log("🚀 OpenClaw → Athena 图谱导入 (关系+向量)")
    t0 = time.time()

    with open(GRAPH_FILE, "rb") as f:
        g = pickle.load(f)
    vectors = np.load(VECTOR_FILE)
    with open(NODE_MAP_FILE) as f:
        nmap = json.load(f)
    log(f"数据: {len(g.nodes)} 节点, {len(g.edges)} 关系, {vectors.shape} 向量")

    edge_count = import_edges(g)
    del g
    gc.collect()
    vec_count = import_vectors(vectors, nmap)

    elapsed = time.time() - t0
    log(f"\n✅ 完成! 关系={edge_count} 向量={vec_count} 耗时={elapsed:.0f}s")


if __name__ == "__main__":
    main()
