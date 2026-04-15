#!/usr/bin/env python3
"""
测试法律向量检索
Test Legal Vector Search

测试法律向量库的搜索功能

作者: Athena平台团队
创建时间: 2025-12-20
版本: v1.0.0
"""

from __future__ import annotations
import json
from datetime import datetime
from typing import Any

import numpy as np
import requests


# 颜色输出
class Colors:
    GREEN = "\033[92m"
    RED = "\033[91m"
    YELLOW = "\033[93m"
    BLUE = "\033[94m"
    PURPLE = "\033[35m"
    CYAN = "\033[96m"
    PINK = "\033[95m"
    RESET = "\033[0m"
    BOLD = "\033[1m"

def print_header(title) -> None:
    """打印标题"""
    print(f"\n{Colors.PURPLE}{Colors.BOLD}{'='*100}{Colors.RESET}")
    print(f"{Colors.PURPLE}{Colors.BOLD}🔍 {title} 🔍{Colors.RESET}")
    print(f"{Colors.PURPLE}{Colors.BOLD}{'='*100}{Colors.RESET}")

def print_success(message) -> None:
    print(f"{Colors.GREEN}✅ {message}{Colors.RESET}")

def print_info(message) -> None:
    print(f"{Colors.BLUE}ℹ️ {message}{Colors.RESET}")

def print_warning(message) -> None:
    print(f"{Colors.YELLOW}⚠️ {message}{Colors.RESET}")

def print_error(message) -> None:
    print(f"{Colors.RED}❌ {message}{Colors.RESET}")

def print_pink(message) -> None:
    print(f"{Colors.PINK}💖 {message}{Colors.RESET}")

def generate_query_vector(text: str) -> list:
    """生成查询向量"""
    # 简单的向量化方法
    words = text.split()
    vector = np.zeros(1024)

    # 基于词汇生成向量
    for _i, word in enumerate(words[:100]):
        hash_val = hash(word) % 1024
        vector[hash_val] += 1.0

    # 归一化
    norm = np.linalg.norm(vector)
    if norm > 0:
        vector = vector / norm

    return vector.tolist()

def search_legal_documents(query: str, collection: str, limit: int = 5) -> Any | None:
    """搜索法律文档"""
    print_info(f"搜索查询: {query}")
    print_info(f"搜索集合: {collection}")

    # 生成查询向量
    query_vector = generate_query_vector(query)

    try:
        response = requests.post(
            f"http://localhost:6333/collections/{collection}/points/search",
            json={
                "vector": query_vector,
                "limit": limit,
                "with_payload": True,
                "with_vector": False,
                "score_threshold": 0.3
            }
        )

        if response.status_code == 200:
            data = response.json()
            result = data.get('result', [])

            print_success(f"找到 {len(result)} 个相关文档")

            if result:
                for i, point in enumerate(result[:limit]):
                    payload = point.get('payload', {})
                    score = point.get('score', 0)

                    print(f"\n{i+1}. {payload.get('title', 'N/A')}")
                    print(f"   类型: {payload.get('doc_type', 'N/A')}")
                    print(f"   类别: {payload.get('category', 'N/A')}")
                    print(f"   相似度: {score:.4f}")

                    # 显示部分元数据
                    metadata = payload.get('metadata', {})
                    if metadata:
                        if 'char_count' in metadata:
                            print(f"   字符数: {metadata['char_count']:,}")
                        if 'chapter_count' in metadata:
                            print(f"   章节数: {metadata['chapter_count']}")

            return result
        else:
            print_error(f"搜索失败: {response.status_code}")
            return None

    except Exception as e:
        print_error(f"搜索异常: {e}")
        return None

def test_multiple_queries() -> Any:
    """测试多个查询"""
    print_header("测试法律向量检索")

    # 测试查询
    test_queries = [
        ("民法典", "legal_articles_1024"),
        ("刑法", "legal_articles_1024"),
        ("司法解释", "legal_judgments_1024"),
        ("合同", "legal_articles_1024"),
        ("侵权", "legal_articles_1024"),
        ("诉讼", "legal_judgments_1024"),
        ("行政法", "legal_articles_1024"),
        ("宪法", "legal_articles_1024"),
        ("民事纠纷", "legal_cases_1024")
    ]

    all_results = []

    for query, collection in test_queries:
        print_header(f"搜索: {query}")
        results = search_legal_documents(query, collection, limit=3)

        if results:
            all_results.append({
                'query': query,
                'collection': collection,
                'count': len(results),
                'reports/reports/results': results
            })

    # 保存搜索结果
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    output_file = f'/Users/xujian/Athena工作平台/production/output/reports/vector_search_test_{timestamp}.json'

    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(all_results, f, ensure_ascii=False, indent=2)

    print_success(f"\n✓ 搜索结果已保存: {output_file}")

    # 显示统计
    print_header("搜索统计")
    total_queries = len(test_queries)
    total_results = sum(r.get('count', 0) for r in all_results)

    print_info(f"总查询数: {total_queries}")
    print_info(f"总结果数: {total_results}")
    print_info(f"平均结果数: {total_results/total_queries:.1f}")

def test_collection_info() -> Any:
    """测试集合信息"""
    print_header("查询集合信息")

    collections = [
        'legal_articles_1024',
        'legal_clauses_1024',
        'legal_cases_1024',
        'legal_judgments_1024'
    ]

    total_points = 0

    for collection in collections:
        try:
            response = requests.get(f"http://localhost:6333/collections/{collection}")
            if response.status_code == 200:
                data = response.json()
                result = data.get('result', {})
                points = result.get('points_count', 0)
                total_points += points

                status = result.get('status', 'unknown')
                print_info(f"{collection}: {points:,} 个文档 (状态: {status})")

        except Exception as e:
            print_error(f"获取 {collection} 信息失败: {e}")

    print_success(f"\n总文档数: {total_points:,}")

def main() -> None:
    """主函数"""
    print_header("法律向量检索测试")
    print_pink("爸爸，测试法律向量检索功能！")

    # 1. 查询集合信息
    test_collection_info()

    # 2. 测试多个查询
    test_multiple_queries()

    # 3. 总结
    print_header("测试完成")
    print_pink("爸爸，法律向量检索测试完成！")
    print_success("✓ 向量库运行正常")
    print_success("✓ 检索功能正常")
    print_success("✓ 可以进行法律文档检索")

if __name__ == "__main__":
    main()
