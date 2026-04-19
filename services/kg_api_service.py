#!/usr/bin/env python3
"""
Athena知识图谱API服务
提供统一的REST API接口访问Neo4j知识图谱
"""

from flask import Flask, jsonify, request
from flask_cors import CORS
from neo4j import GraphDatabase
import os

app = Flask(__name__)
CORS(app)

# Neo4j连接配置
NEO4J_URI = os.getenv("NEO4J_URI", "bolt://localhost:7687")
NEO4J_USER = os.getenv("NEO4J_USER", "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "athena_neo4j_2024")

# 初始化Neo4j驱动
driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))


@app.route("/health", methods=["GET"])
def health_check():
    """健康检查"""
    try:
        driver.verify_connectivity()
        return jsonify({
            "status": "healthy",
            "service": "knowledge-graph-api",
            "neo4j": "connected"
        }), 200
    except Exception as e:
        return jsonify({
            "status": "unhealthy",
            "error": str(e)
        }), 503


@app.route("/api/v1/kg/query", methods=["POST"])
def query_knowledge_graph():
    """知识图谱查询接口"""
    try:
        data = request.get_json()
        query = data.get("query", "")

        if not query:
            return jsonify({"error": "缺少查询参数"}), 400

        # 简单查询示例
        with driver.session() as session:
            # 这里应该是真正的查询逻辑
            # 暂时返回示例响应
            result = {
                "success": True,
                "query": query,
                "results": [],
                "message": "知识图谱查询功能需要实现具体查询逻辑"
            }

            return jsonify(result), 200

    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@app.route("/api/v1/kg/search", methods=["POST"])
def search_knowledge_graph():
    """知识图谱搜索接口"""
    try:
        data = request.get_json()
        search_term = data.get("term", "")

        with driver.session() as session:
            # Cypher查询示例
            cypher = """
                MATCH (n)
                WHERE any(prop IN keys(n) WHERE toString(n[prop]) CONTAINS $term)
                RETURN n LIMIT 10
            """
            result = session.run(cypher, term=search_term)

            nodes = []
            for record in result:
                node = record["n"]
                nodes.append({
                    "id": element_id(node),
                    "labels": list(node.labels),
                    "properties": dict(node)
                })

            return jsonify({
                "success": True,
                "count": len(nodes),
                "nodes": nodes
            }), 200

    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@app.route("/api/v1/kg/stats", methods=["GET"])
def get_stats():
    """获取知识图谱统计信息"""
    try:
        with driver.session() as session:
            # 统计节点数量
            node_count_result = session.run("MATCH (n) RETURN count(n) as count")
            node_count = node_count_result.single()["count"]

            # 统计关系数量
            rel_count_result = session.run("MATCH ()-[r]->() RETURN count(r) as count")
            rel_count = rel_count_result.single()["count"]

            return jsonify({
                "success": True,
                "stats": {
                    "node_count": node_count,
                    "relationship_count": rel_count
                }
            }), 200

    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@app.route("/", methods=["GET"])
def index():
    """根路径"""
    return jsonify({
        "service": "Athena Knowledge Graph API",
        "version": "1.0.0",
        "endpoints": [
            "/health",
            "/api/v1/kg/query",
            "/api/v1/kg/search",
            "/api/v1/kg/stats"
        ]
    }), 200


if __name__ == "__main__":
    port = int(os.getenv("PORT", 8100))
    debug = os.getenv("DEBUG", "False").lower() == "true"

    print(f"🚀 启动知识图谱API服务 (端口{port})...")
    print(f"   Neo4j: {NEO4J_URI}")

    app.run(host="0.0.0.0", port=port, debug=debug)
