#!/usr/bin/env python3
"""
混合搜索引擎
Hybrid Search Engine

结合向量搜索、文本搜索和知识图谱的智能法律搜索引擎

作者: Athena平台团队
创建时间: 2025-12-20
版本: v1.0.0
"""

from __future__ import annotations
import json
import logging
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

import numpy as np
import requests

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class SearchResult:
    """搜索结果"""
    id: str
    title: str
    content: str
    score: float
    source: str  # vector, text, kg
    metadata: dict

class HybridSearchEngine:
    """混合搜索引擎"""

    def __init__(self):
        self.qdrant_url = "http://localhost:6333"
        self.weights = {
            "vector": 0.5,      # 向量搜索权重
            "text": 0.3,        # 文本搜索权重
            "knowledge_graph": 0.2  # 知识图谱权重
        }

    def generate_query_vector(self, query: str) -> list[float]:
        """生成查询向量"""
        # 使用与增强相同的逻辑
        legal_domains = {
            "民法基础": {"keywords": ["民法典", "民事", "合同", "侵权"], "range": (0, 100)},
            "刑法规定": {"keywords": ["刑法", "犯罪", "刑罚"], "range": (100, 200)},
            "行政程序": {"keywords": ["行政", "处罚", "许可"], "range": (200, 300)},
            "宪法权利": {"keywords": ["宪法", "公民", "权利"], "range": (300, 400)},
            "诉讼程序": {"keywords": ["诉讼", "审判", "证据"], "range": (400, 500)},
            "知识产权": {"keywords": ["专利", "商标", "版权"], "range": (500, 600)},
        }

        vector = np.zeros(1024, dtype=np.float32)

        # 基于法律领域
        for _domain, config in legal_domains.items():
            for kw in config["keywords"]:
                if kw in query:
                    start, end = config["range"]
                    vector[start:end] += 1.0

        # 基于词汇
        words = query.split()
        for word in words:
            hash_val = abs(hash(word)) % 1024
            vector[hash_val] += 1.0

        # 归一化
        norm = np.linalg.norm(vector)
        if norm > 0:
            vector = vector / norm

        return vector.tolist()

    def vector_search(self, query: str, collection: str, limit: int = 10) -> list[SearchResult]:
        """向量搜索"""
        query_vector = self.generate_query_vector(query)

        response = requests.post(
            f"{self.qdrant_url}/collections/{collection}/points/search",
            json={
                "vector": query_vector,
                "limit": limit,
                "with_payload": True,
                "score_threshold": 0.2
            }
        )

        results = []
        if response.status_code == 200:
            data = response.json().get('result', [])
            for item in data:
                payload = item.get('payload', {})
                results.append(SearchResult(
                    id=item.get('id'),
                    title=payload.get('title', ''),
                    content=payload.get('title', ''),  # 简化，实际应读取文件
                    score=item.get('score', 0) * self.weights['vector'],
                    source='vector',
                    metadata=payload
                ))

        return results

    def text_search(self, query: str, collection: str, limit: int = 10) -> list[SearchResult]:
        """文本搜索（基于payload）"""
        # 获取所有文档进行文本匹配
        response = requests.post(
            f"{self.qdrant_url}/collections/{collection}/points/scroll",
            json={
                "limit": 1000,  # 获取足够多的文档
                "with_payload": True,
                "with_vector": False
            }
        )

        results = []
        if response.status_code == 200:
            data = response.json().get('result', {}).get('points', [])

            # 计算文本相似度
            query_words = set(query.lower().split())
            for item in data:
                payload = item.get('payload', {})
                title = payload.get('title', '').lower()

                # 简单的文本匹配
                title_words = set(title.split())
                match_count = len(query_words & title_words)
                similarity = match_count / max(len(query_words), len(title_words), 1)

                if similarity > 0.1:  # 最低匹配阈值
                    results.append(SearchResult(
                        id=item.get('id'),
                        title=payload.get('title', ''),
                        content=payload.get('title', ''),
                        score=similarity * self.weights['text'],
                        source='text',
                        metadata=payload
                    ))

        # 按分数排序并限制数量
        results.sort(key=lambda x: x.score, reverse=True)
        return results[:limit]

    def knowledge_graph_search(self, query: str, limit: int = 10) -> list[SearchResult]:
        """知识图谱搜索"""
        # 简化的知识图谱搜索（实际应查询NebulaGraph）
        # 这里模拟知识图谱返回相关文档

        # 从知识图谱摘要中获取相关实体
        kg_summary_path = Path("/Users/xujian/Athena工作平台/production/data/metadata/kg_summary.json")
        results = []

        if kg_summary_path.exists():
            with open(kg_summary_path, encoding='utf-8') as f:
                kg_data = json.load(f)

            # 模拟基于知识图谱的推荐
            if kg_data.get('statistics', {}).get('total_entities', 0) > 0:
                # 这里应该查询图数据库获取相关实体
                # 简化处理，返回固定结果
                results.append(SearchResult(
                    id="kg_001",
                    title="知识图谱相关文档",
                    content="通过知识图谱关联的文档",
                    score=0.6 * self.weights['knowledge_graph'],
                    source='knowledge_graph',
                    metadata={"type": "knowledge_graph", "relations": ["REFERENCES", "AMENDS"]}
                ))

        return results

    def merge_and_rank_results(self, vector_results: list[SearchResult],
                              text_results: list[SearchResult],
                              kg_results: list[SearchResult]) -> list[SearchResult]:
        """合并和重排结果"""
        # 合并所有结果
        all_results = vector_results + text_results + kg_results

        # 去重（基于ID）
        unique_results = {}
        for result in all_results:
            if result.id not in unique_results:
                unique_results[result.id] = result
            else:
                # 合并分数
                existing = unique_results[result.id]
                existing.score = max(existing.score, result.score)
                # 记录多个来源
                if result.source not in existing.metadata.get('sources', []):
                    existing.metadata.setdefault('sources', []).append(result.source)

        # 按分数排序
        sorted_results = sorted(unique_results.values(), key=lambda x: x.score, reverse=True)

        return sorted_results[:20]  # 返回前20个结果

    def search(self, query: str, collections: list[str] | None = None) -> dict:
        """执行混合搜索"""
        if collections is None:
            collections = ["legal_articles_1024", "legal_judgments_1024"]

        logger.info(f"\n🔍 执行混合搜索: {query}")

        # 1. 向量搜索
        vector_results = []
        for collection in collections:
            vector_results.extend(self.vector_search(query, collection, limit=10))
        logger.info(f"  向量搜索: {len(vector_results)} 个结果")

        # 2. 文本搜索
        text_results = []
        for collection in collections:
            text_results.extend(self.text_search(query, collection, limit=10))
        logger.info(f"  文本搜索: {len(text_results)} 个结果")

        # 3. 知识图谱搜索
        kg_results = self.knowledge_graph_search(query, limit=5)
        logger.info(f"  知识图谱: {len(kg_results)} 个结果")

        # 4. 合并和重排
        final_results = self.merge_and_rank_results(vector_results, text_results, kg_results)

        # 5. 分析结果分布
        source_distribution = {}
        for result in final_results:
            source = result.source
            source_distribution[source] = source_distribution.get(source, 0) + 1

        # 构建响应
        response = {
            "query": query,
            "timestamp": datetime.now().isoformat(),
            "total_results": len(final_results),
            "source_distribution": source_distribution,
            "weights": self.weights,
            "reports/reports/results": []
        }

        for result in final_results:
            response["reports/reports/results"].append({
                "id": result.id,
                "title": result.title,
                "score": round(result.score, 4),
                "source": result.source,
                "metadata": result.metadata
            })

        # 保存搜索日志
        self.save_search_log(response)

        return response

    def save_search_log(self, response: dict) -> None:
        """保存搜索日志"""
        log_path = Path("/Users/xujian/Athena工作平台/production/data/metadata") / \
                  f"search_log_{datetime.now().strftime('%Y%m%d')}.json"

        logs = []
        if log_path.exists():
            with open(log_path, encoding='utf-8') as f:
                logs = json.load(f)

        # 添加新日志
        log_entry = {
            "query": response["query"],
            "timestamp": response["timestamp"],
            "result_count": response["total_results"],
            "sources": response["source_distribution"]
        }
        logs.append(log_entry)

        # 只保留最近100条
        logs = logs[-100:]

        with open(log_path, 'w', encoding='utf-8') as f:
            json.dump(logs, f, ensure_ascii=False, indent=2)

def main() -> None:
    """主函数 - 演示混合搜索"""
    print("="*100)
    print("🔍 混合搜索引擎演示 🔍")
    print("="*100)

    engine = HybridSearchEngine()

    # 测试查询
    test_queries = [
        "民法典物权编",
        "刑法正当防卫",
        "合同纠纷处理",
        "行政复议程序",
        "专利侵权责任"
    ]

    for query in test_queries:
        print(f"\n{'='*80}")
        print(f"查询: {query}")
        print('='*80)

        results = engine.search(query)

        print("\n📊 搜索统计:")
        print(f"  总结果数: {results['total_results']}")
        print(f"  来源分布: {results['source_distribution']}")

        print("\n📋 前5个结果:")
        for i, result in enumerate(results["reports/reports/results"][:5]):
            print(f"\n{i+1}. {result['title'][:60]}...")
            print(f"   相似度: {result['score']}")
            print(f"   来源: {result['source']}")

        # 保存详细结果
        result_path = Path("/Users/xujian/Athena工作平台/production/output/reports") / \
                     f"hybrid_search_{query.replace(' ', '_')[:10]}_{datetime.now().strftime('%H%M%S')}.json"
        result_path.parent.mkdir(parents=True, exist_ok=True)

        with open(result_path, 'w', encoding='utf-8') as f:
            json.dump(results, f, ensure_ascii=False, indent=2)

    print("\n✅ 混合搜索演示完成！")

if __name__ == "__main__":
    main()
