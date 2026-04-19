#!/usr/bin/env python3
"""
Hybrid RAG系统
Hybrid RAG System

结合向量检索和知识图谱的混合检索系统

作者: Athena平台团队
创建时间: 2025-12-20
版本: v2.0.0
"""

from __future__ import annotations
import asyncio
import hashlib
import json
import logging
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path

# 使用安全哈希函数替代不安全的MD5/SHA1
from production.utils.security_helpers import short_hash

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class RetrievalResult:
    """检索结果"""
    content: str
    source: str  # "vector" 或 "graph"
    score: float
    metadata: dict
    explanation: str

@dataclass
class HybridResult:
    """混合检索结果"""
    query: str
    vector_results: list[RetrievalResult]
    graph_results: list[RetrievalResult]
    hybrid_results: list[RetrievalResult]
    processing_time: float
    query_analysis: dict

class HybridRAGSystem:
    """混合RAG系统"""

    def __init__(self):
        # 服务配置
        self.qdrant_url = "http://localhost:6333"
        self.nebula_url = "http://localhost:9669"
        self.nlp_url = "http://localhost:8001"

        # 检索配置
        self.vector_weight = 0.4
        self.graph_weight = 0.3
        self.rerank_weight = 0.3
        self.top_k_vector = 10
        self.top_k_graph = 10
        self.final_top_k = 5

        # Qdrant集合名
        self.collection_name = "legal_knowledge"

        # 初始化向量检索器
        self.vector_retriever = VectorRetriever(self.qdrant_url)
        self.graph_retriever = GraphRetriever(self.nebula_url)
        self.reranker = VectorReranker()

    async def search(self, query: str) -> HybridResult:
        """执行混合检索"""
        logger.info(f"\n🔍 执行混合检索: {query}")
        start_time = asyncio.get_event_loop().time()

        # 1. 查询分析
        query_analysis = self._analyze_query(query)
        logger.info(f"查询分析: {query_analysis}")

        # 2. 并行检索
        tasks = [
            self.vector_retriever.search(query, self.top_k_vector),
            self.graph_retriever.search(query, self.top_k_graph)
        ]
        vector_results, graph_results = await asyncio.gather(*tasks)

        # 3. 结果融合
        hybrid_results = self._merge_results(
            vector_results, graph_results, query
        )

        # 4. 重排序
        if hybrid_results:
            hybrid_results = self._rerank_results(query, hybrid_results)

        processing_time = asyncio.get_event_loop().time() - start_time

        # 构建结果
        result = HybridResult(
            query=query,
            vector_results=vector_results,
            graph_results=graph_results,
            hybrid_results=hybrid_results,
            processing_time=processing_time,
            query_analysis=query_analysis
        )

        logger.info(f"✅ 检索完成，耗时: {processing_time:.2f}秒")
        logger.info(f"  向量结果: {len(vector_results)}条")
        logger.info(f"  图谱结果: {len(graph_results)}条")
        logger.info(f"  最终结果: {len(hybrid_results)}条")

        return result

    def _analyze_query(self, query: str) -> dict:
        """分析查询"""
        analysis = {
            "query_type": "general",
            "entities": [],
            "intent": "search",
            "legal_keywords": []
        }

        # 识别法律关键词
        legal_keywords = [
            "法", "条例", "规定", "办法", "细则",
            "第", "条", "款", "义务", "权利", "责任",
            "处罚", "罚款", "禁止", "应当", "可以"
        ]

        found_keywords = [kw for kw in legal_keywords if kw in query]
        if found_keywords:
            analysis["legal_keywords"] = found_keywords
            analysis["query_type"] = "legal"

        # 识别查询意图
        if any(word in query for word in ["什么是", "定义", "概念"]):
            analysis["intent"] = "definition"
        elif any(word in query for word in ["如何", "怎么办", "流程"]):
            analysis["intent"] = "procedure"
        elif any(word in query for word in ["条件", "要求", "资格"]):
            analysis["intent"] = "requirement"
        elif any(word in query for word in ["处罚", "罚款", "责任"]):
            analysis["intent"] = "penalty"

        return analysis

    def _merge_results(self, vector_results: list[RetrievalResult],
                      graph_results: list[RetrievalResult],
                      query: str) -> list[RetrievalResult]:
        """合并检索结果"""
        # 创建结果字典，基于内容去重
        result_dict = {}

        # 添加向量检索结果
        for result in vector_results:
            key = short_hash(result.content.encode())
            if key not in result_dict:
                result_dict[key] = {
                    "content": result.content,
                    "metadata": result.metadata,
                    "sources": [],
                    "scores": []
                }
            result_dict[key]["sources"].append("vector")
            result_dict[key]["scores"].append(result.score * self.vector_weight)

        # 添加图谱检索结果
        for result in graph_results:
            key = short_hash(result.content.encode())
            if key not in result_dict:
                result_dict[key] = {
                    "content": result.content,
                    "metadata": result.metadata,
                    "sources": [],
                    "scores": []
                }
            result_dict[key]["sources"].append("graph")
            result_dict[key]["scores"].append(result.score * self.graph_weight)

        # 计算综合分数
        merged_results = []
        for key, data in result_dict.items():
            # 加权平均分数
            combined_score = sum(data["scores"])

            # 创建解释
            explanation = f"来源: {', '.join(data['sources'])}"
            if len(data["sources"]) == 2:
                explanation += " (双路匹配)"

            result = RetrievalResult(
                content=data["content"],
                source="hybrid",
                score=combined_score,
                metadata=data["metadata"],
                explanation=explanation
            )
            merged_results.append(result)

        # 按分数排序
        merged_results.sort(key=lambda x: x.score, reverse=True)

        return merged_results[:self.final_top_k]

    def _rerank_results(self, query: str, results: list[RetrievalResult]) -> list[RetrievalResult]:
        """重排序结果"""
        # 转换为reranker需要的格式
        candidates = []
        for result in results:
            candidates.append({
                "content": result.content,
                "score": result.score,
                "metadata": result.metadata
            })

        # 执行重排序
        rerank_results = self.reranker.rerank(query, candidates, self.final_top_k)

        # 转换回RetrievalResult格式
        final_results = []
        for i, rerank_result in enumerate(rerank_results):
            result = RetrievalResult(
                content=rerank_result.content,
                source="hybrid_reranked",
                score=rerank_result.rerank_score,
                metadata=rerank_result.metadata,
                explanation=f"重排序第{i+1}名: {', '.join(rerank_result.rank_reasons)}"
            )
            final_results.append(result)

        return final_results

    def generate_answer(self, hybrid_result: HybridResult) -> str:
        """生成答案"""
        if not hybrid_result.hybrid_results:
            return "抱歉，没有找到相关信息。"

        # 构建上下文
        contexts = []
        for i, result in enumerate(hybrid_result.hybrid_results[:3]):
            contexts.append(f"参考{i+1}: {result.content}")

        context = "\n\n".join(contexts)

        # 生成答案（简化版）
        answer = f"""
基于法律数据库的检索结果，针对您的问题"{hybrid_result.query}"，提供以下信息：

{context}

以上信息来源于：
- 向量检索: {len(hybrid_result.vector_results)}条相关内容
- 知识图谱: {len(hybrid_result.graph_results)}条相关内容
- 综合评分: 已通过重排序优化

查询类型: {hybrid_result.query_analysis.get('query_type', '一般查询')}
检索耗时: {hybrid_result.processing_time:.2f}秒

请注意：以上信息仅供参考，具体法律适用请咨询专业律师。
"""

        return answer

    def save_results(self, hybrid_result: HybridResult) -> None:
        """保存检索结果"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')

        # 保存完整结果
        result_file = Path(f"/Users/xujian/Athena工作平台/production/data/retrieval_reports/results/hybrid_search_{timestamp}.json")
        result_file.parent.mkdir(parents=True, exist_ok=True)

        result_data = {
            "query": hybrid_result.query,
            "timestamp": datetime.now().isoformat(),
            "processing_time": hybrid_result.processing_time,
            "query_analysis": hybrid_result.query_analysis,
            "vector_results": [asdict(r) for r in hybrid_result.vector_results],
            "graph_results": [asdict(r) for r in hybrid_result.graph_results],
            "hybrid_results": [asdict(r) for r in hybrid_result.hybrid_results],
            "answer": self.generate_answer(hybrid_result)
        }

        with open(result_file, 'w', encoding='utf-8') as f:
            json.dump(result_data, f, ensure_ascii=False, indent=2)

        logger.info(f"✅ 检索结果已保存: {result_file}")

        return result_file


class VectorRetriever:
    """向量检索器"""

    def __init__(self, qdrant_url: str):
        self.qdrant_url = qdrant_url
        self.collection_name = "legal_knowledge"

    async def search(self, query: str, top_k: int) -> list[RetrievalResult]:
        """向量检索"""
        try:
            # 生成查询向量（简化版，使用哈希）
            query_vector = self._generate_query_vector(query)

            # 模拟检索结果
            results = []
            for i in range(top_k):
                result = RetrievalResult(
                    content=f"这是向量检索的第{i+1}个相关内容片段，与查询'{query}'相关。",
                    source="vector",
                    score=0.9 - i * 0.05,
                    metadata={"source": "qdrant", "vector_id": f"vec_{i}"},
                    explanation=f"向量相似度: {0.9 - i * 0.05:.3f}"
                )
                results.append(result)

            logger.info(f"向量检索返回 {len(results)} 个结果")
            return results

        except Exception as e:
            logger.error(f"向量检索失败: {e}")
            return []

    def _generate_query_vector(self, query: str, dim: int = 1024) -> list[float]:
        """生成查询向量"""
        # 使用查询文本的哈希值生成向量
        text_hash = hashlib.sha256(query.encode('utf-8')).hexdigest()
        vector = []
        for i in range(0, len(text_hash), 2):
            hex_pair = text_hash[i:i+2]
            val = int(hex_pair, 16) / 255.0
            vector.append(val)
        # 扩展到指定维度
        while len(vector) < dim:
            vector.extend(vector[:dim - len(vector)])
        return vector[:dim]


class GraphRetriever:
    """图谱检索器"""

    def __init__(self, nebula_url: str):
        self.nebula_url = nebula_url
        self.space_name = "legal_knowledge"

    async def search(self, query: str, top_k: int) -> list[RetrievalResult]:
        """图谱检索"""
        try:
            # 模拟图谱检索结果
            results = []
            for i in range(top_k):
                result = RetrievalResult(
                    content=f"这是图谱检索的第{i+1}个相关内容，展示了法律实体间的关系。",
                    source="graph",
                    score=0.85 - i * 0.04,
                    metadata={"source": "nebula", "path": f"path_{i}"},
                    explanation=f"图谱路径相似度: {0.85 - i * 0.04:.3f}"
                )
                results.append(result)

            logger.info(f"图谱检索返回 {len(results)} 个结果")
            return results

        except Exception as e:
            logger.error(f"图谱检索失败: {e}")
            return []


# 引用之前的VectorReranker类（简化版）
class VectorReranker:
    """向量重排序器"""

    def __init__(self):
        self.weights = {
            "vector_similarity": 0.4,
            "text_match": 0.3,
            "legal_relevance": 0.2,
            "structural_importance": 0.1
        }

    def rerank(self, query: str, candidates: list[dict], top_k: int) -> list[any]:
        """重排序候选结果"""
        # 创建简单的重排序结果类
        @dataclass
        class RerankResult:
            content: str
            metadata: dict
            rerank_score: float
            rank_reasons: list[str]

        results = []
        for i, candidate in enumerate(candidates):
            score = candidate.get("score", 0.5)
            # 简单的分数调整
            rerank_score = score * 0.9 + (top_k - i) * 0.01

            reasons = []
            if score > 0.8:
                reasons.append("高分匹配")
            if i < 3:
                reasons.append("排名靠前")

            result = RerankResult(
                content=candidate.get("content", ""),
                metadata=candidate.get("metadata", {}),
                rerank_score=rerank_score,
                rank_reasons=reasons
            )
            results.append(result)

        return results[:top_k]


async def main():
    """主函数"""
    print("="*100)
    print("🔄 Hybrid RAG混合检索系统 🔄")
    print("="*100)

    # 初始化系统
    rag = HybridRAGSystem()

    # 测试查询列表
    test_queries = [
        "劳动合同的解除条件有哪些？",
        "什么是不可抗力？",
        "公司破产的条件是什么？",
        "如何申请行政复议？",
        "环境保护的法律责任有哪些？"
    ]

    # 执行检索
    for query in test_queries:
        print(f"\n{'='*80}")
        print(f"查询: {query}")
        print(f"{'='*80}")

        # 执行混合检索
        result = await rag.search(query)

        # 生成答案
        answer = rag.generate_answer(result)
        print(answer)

        # 保存结果
        result_file = rag.save_results(result)
        print(f"\n📄 结果已保存到: {result_file}")

    print("\n✅ 所有测试查询完成！")


if __name__ == "__main__":
    asyncio.run(main())
