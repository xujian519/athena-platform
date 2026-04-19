#!/usr/bin/env python3
"""
OpenClaw专利知识图谱节点导入脚本
Import OpenClaw Patent Knowledge Graph Nodes to Neo4j
"""

import pickle
import json
import time
from pathlib import Path

WORKSPACE = Path.home() / ".openclaw" / "workspace" / "memory" / "patent-knowledge-graph"
GRAPH_FILE = WORKSPACE / "patent_knowledge_graph_updated.gpickle"

NEO4J_URI = "bolt://localhost:7687"
NEO4J_AUTH = ("neo4j", "athena_neo4j_2024")

BATCH_SIZE = 1000

def log(msg: str):
    print(f"[{time.strftime('%H:%M:%S')}] {msg}", flush=True)


def import_nodes():
    """导入OpenClaw节点到Neo4j"""
    from neo4j import GraphDatabase

    log("🚀 开始导入OpenClaw节点到Neo4j")
    t0 = time.time()

    # 加载图谱数据
    log(f"加载图谱文件: {GRAPH_FILE}")
    with open(GRAPH_FILE, "rb") as f:
        import networkx as nx
        g = pickle.load(f)

    total_nodes = g.number_of_nodes()
    log(f"节点总数: {total_nodes:,}")

    driver = GraphDatabase.driver(NEO4J_URI, auth=NEO4J_AUTH)

    try:
        with driver.session() as session:
            # 创建约束
            log("创建约束...")
            try:
                session.run("CREATE CONSTRAINT IF NOT EXISTS FOR (n:OpenClawNode) REQUIRE n.id IS UNIQUE")
                log("  ✅ OpenClawNode.id 约束已创建")
            except Exception as e:
                log(f"  ⚠️  约束创建警告: {e}")

            # 准备节点数据
            log("准备节点数据...")
            nodes_data = []
            for node_id, node_attrs in g.nodes(data=True):
                # 构建属性
                props = {
                    "id": str(node_id),
                    "node_type": node_attrs.get("node_type", ""),
                }

                # 添加其他属性
                if "title" in node_attrs:
                    props["title"] = str(node_attrs["title"])[:500]
                if "name" in node_attrs:
                    props["name"] = str(node_attrs["name"])[:500]
                if "description" in node_attrs:
                    props["description"] = str(node_attrs["description"])[:2000]
                if "content" in node_attrs:
                    props["content"] = str(node_attrs["content"])[:5000]

                # 添加数值属性
                for key, value in node_attrs.items():
                    if key not in ["node_type", "title", "name", "description", "content"]:
                        if isinstance(value, (str, int, float, bool)):
                            props[key] = value

                nodes_data.append(props)

            # 批量导入节点
            log(f"开始批量导入节点（批次大小: {BATCH_SIZE}）...")
            imported = 0
            for i in range(0, len(nodes_data), BATCH_SIZE):
                batch = nodes_data[i:i + BATCH_SIZE]

                # 使用UNWIND批量创建
                session.run("""
                    UNWIND $batch AS node
                    CREATE (n:OpenClawNode)
                    SET n = node
                """, batch=batch)

                imported += len(batch)
                elapsed = time.time() - t0
                speed = imported / elapsed if elapsed > 0 else 0
                remain = (total_nodes - imported) / speed if speed > 0 else 0

                if imported % 5000 == 0 or imported >= total_nodes:
                    log(f"  进度: {imported}/{total_nodes} ({speed:.0f}/s, 剩余{remain:.0f}s)")

            log(f"  ✅ 节点导入完成: {imported:,}")

            # 验证导入
            result = session.run("MATCH (n:OpenClawNode) RETURN count(n) as count")
            count = result.single()["count"]
            log(f"  验证: Neo4j中有 {count:,} 个OpenClawNode节点")

    finally:
        driver.close()

    elapsed = time.time() - t0
    log(f"\n✅ 节点导入完成! 耗时: {elapsed:.1f}秒")

    return imported


if __name__ == "__main__":
    import_nodes()
