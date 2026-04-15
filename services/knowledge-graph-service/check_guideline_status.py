#!/usr/bin/env python3
"""
检查审查指南集成状态
"""

import json

import requests


def check_qdrant() -> bool:
    """检查Qdrant服务"""
    try:
        response = requests.get("http://localhost:6333/collections/patent_guideline")
        if response.status_code == 200:
            data = response.json()
            points = data.get("result", {}).get("points_count", 0)
            print(f"✅ Qdrant: patent_guideline集合, {points}个向量")
            return True
    except (json.JSONDecodeError, TypeError, ValueError):
        print("❌ Qdrant服务不可用")
    return False

def check_graph_data() -> bool:
    """检查知识图谱数据"""
    try:
        with open("/Users/xujian/Athena工作平台/data/guideline_graph/patent_guideline_graph.json") as f:
            data = json.load(f)
            nodes = len(data.get("nodes", []))
            rels = len(data.get("relationships", []))
            print(f"✅ 知识图谱: {nodes}个节点, {rels}条关系")
            return True
    except (json.JSONDecodeError, TypeError, ValueError):
        print("❌ 知识图谱数据文件不存在")
    return False

def check_api() -> bool:
    """检查API服务"""
    try:
        response = requests.get("http://localhost:8080/health")
        if response.status_code == 200:
            print("✅ API服务运行正常")
            return True
    except (ConnectionError, OSError, TimeoutError):
        print("❌ API服务不可用")
    return False

def main() -> None:
    print("检查审查指南集成状态...\n")

    all_ok = True

    if not check_qdrant():
        all_ok = False

    if not check_graph_data():
        all_ok = False

    if not check_api():
        all_ok = False

    print("\n" + "="*50)
    if all_ok:
        print("✅ 所有组件运行正常")
        print("\n可用的API端点:")
        print("- GET  /api/v2/guidelines/search?query=<text>")
        print("- GET  /api/v2/guidelines/structure")
        print("- POST /api/v2/guidelines/prompt")
        print("- GET  /api/v2/guidelines/extract-rules?topic=<text>")
    else:
        print("⚠️ 部分组件存在问题")
    print("="*50)

if __name__ == "__main__":
    main()
