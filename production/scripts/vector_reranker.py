#!/usr/bin/env python3
"""
向量重排序器
Vector Reranker

对检索结果进行重排序，提升检索精度

作者: Athena平台团队
创建时间: 2025-12-20
版本: v2.0.0
"""

from __future__ import annotations
import hashlib
import json
import logging
import re
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

import numpy as np

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class RerankResult:
    """重排序结果"""
    chunk_id: str
    original_score: float
    rerank_score: float
    content: str
    metadata: dict
    rank_reasons: list[str]

class VectorReranker:
    """向量重排序器"""

    def __init__(self):
        # 重排序权重配置
        self.weights = {
            "vector_similarity": 0.4,      # 向量相似度权重
            "text_match": 0.3,            # 文本匹配权重
            "legal_relevance": 0.2,       # 法律相关性权重
            "structural_importance": 0.1  # 结构重要性权重
        }

        # 法律关键词列表
        self.legal_keywords = [
            "法律", "法规", "条例", "规定", "办法", "细则",
            "第", "条", "款", "项", "章", "节", "编",
            "应当", "必须", "可以", "有权", "义务", "责任",
            "处罚", "罚款", "没收", "责令", "禁止", "违反",
            "国务院", "最高人民法院", "最高人民检察院"
        ]

        # 结构重要性等级
        self.structure_hierarchy = {
            "H1": 10, "CHAPTER": 9, "PART": 8,
            "H2": 7, "SECTION": 6,
            "H3": 5, "ARTICLE": 4,
            "H4": 3, "H5": 2, "H6": 1,
            "PARAGRAPH": 0.5, "unknown": 0
        }

    def calculate_text_similarity(self, query: str, content: str) -> float:
        """计算文本相似度"""
        # 分词（简单实现）
        query_words = set(re.findall(r'[\u4e00-\u9fff]+|[a-z_a-Z]+', query.lower()))
        content_words = set(re.findall(r'[\u4e00-\u9fff]+|[a-z_a-Z]+', content.lower()))

        if not query_words:
            return 0.0

        # Jaccard相似度
        intersection = query_words.intersection(content_words)
        union = query_words.union(content_words)

        return len(intersection) / len(union) if union else 0.0

    def calculate_legal_relevance(self, query: str, content: str, metadata: dict) -> float:
        """计算法律相关性"""
        score = 0.0

        # 检查法律关键词匹配
        legal_words_in_query = [word for word in self.legal_keywords if word in query]
        legal_words_in_content = [word for word in self.legal_keywords if word in content]

        if legal_words_in_query:
            # 如果查询包含法律关键词，检查内容的匹配度
            matched_keywords = set(legal_words_in_query).intersection(set(legal_words_in_content))
            score += len(matched_keywords) / len(legal_words_in_query) * 0.5

        # 检查条款编号匹配
        article_pattern = r'第([一二三四五六七八九十百千万\d]+)条'
        query_articles = re.findall(article_pattern, query)
        content_articles = re.findall(article_pattern, content)

        if query_articles and content_articles:
            if any(article in content_articles for article in query_articles):
                score += 0.3

        # 检查法律引用
        law_refs = re.findall(r'《([^》]+(?:法|条例|规定|办法|细则|解释))》', content)
        if law_refs:
            score += 0.2 * min(len(law_refs), 3) / 3  # 最多3个引用

        # 检查文档类型
        doc_type = metadata.get("document_type", "")
        if doc_type in ["法律", "行政法规", "部门规章", "司法解释"]:
            score += 0.1

        return min(score, 1.0)

    def calculate_structural_importance(self, metadata: dict) -> float:
        """计算结构重要性"""
        structural_info = metadata.get("structural_info", {})
        level = structural_info.get("level", "unknown")

        # 获取重要性等级
        importance = self.structure_hierarchy.get(level, 0)

        # 归一化到[0,1]
        max_importance = max(self.structure_hierarchy.values())
        return importance / max_importance if max_importance > 0 else 0.0

    def generate_vector_embedding(self, text: str, dim: int = 1024) -> list[float]:
        """生成文本向量嵌入（使用哈希方法）"""
        # 使用文本哈希生成固定维度的向量
        text_hash = hashlib.sha256(text.encode('utf-8')).hexdigest()

        # 将哈希值转换为向量
        vector = []
        for i in range(0, len(text_hash), 2):
            hex_pair = text_hash[i:i+2]
            val = int(hex_pair, 16) / 255.0
            vector.append(val)

        # 扩展或截断到指定维度
        while len(vector) < dim:
            # 循环使用现有值
            vector.extend(vector[:dim - len(vector)])

        return vector[:dim]

    def calculate_vector_similarity(self, query_vector: list[float], content_vector: list[float]) -> float:
        """计算向量相似度（余弦相似度）"""
        if len(query_vector) != len(content_vector):
            return 0.0

        # 转换为numpy数组
        query_arr = np.array(query_vector)
        content_arr = np.array(content_vector)

        # 计算余弦相似度
        dot_product = np.dot(query_arr, content_arr)
        norm_query = np.linalg.norm(query_arr)
        norm_content = np.linalg.norm(content_arr)

        if norm_query == 0 or norm_content == 0:
            return 0.0

        return dot_product / (norm_query * norm_content)

    def rerank(self, query: str, candidates: list[dict], top_k: int = 10) -> list[RerankResult]:
        """对候选结果进行重排序"""
        logger.info(f"开始重排序，候选文档数: {len(candidates)}")

        # 生成查询向量
        query_vector = self.generate_vector_embedding(query)

        rerank_results = []

        for idx, candidate in enumerate(candidates):
            content = candidate.get("content", "")
            metadata = candidate.get("metadata", {})
            original_score = candidate.get("score", 0.5)  # 默认分数

            # 计算各项分数
            vector_sim = self.calculate_vector_similarity(
                query_vector,
                candidate.get("embedding", self.generate_vector_embedding(content))
            )

            text_sim = self.calculate_text_similarity(query, content)
            legal_rel = self.calculate_legal_relevance(query, content, metadata)
            struct_imp = self.calculate_structural_importance(metadata)

            # 加权计算总分
            rerank_score = (
                vector_sim * self.weights["vector_similarity"] +
                text_sim * self.weights["text_match"] +
                legal_rel * self.weights["legal_relevance"] +
                struct_imp * self.weights["structural_importance"]
            )

            # 记录排序原因
            reasons = []
            if vector_sim > 0.7:
                reasons.append(f"向量相似度高({vector_sim:.3f})")
            if text_sim > 0.5:
                reasons.append(f"文本匹配度高({text_sim:.3f})")
            if legal_rel > 0.5:
                reasons.append(f"法律相关性强({legal_rel:.3f})")
            if struct_imp > 0.5:
                reasons.append(f"结构重要性高({struct_imp:.3f})")

            result = RerankResult(
                chunk_id=candidate.get("chunk_id", f"chunk_{idx}"),
                original_score=original_score,
                rerank_score=rerank_score,
                content=content[:200] + "..." if len(content) > 200 else content,
                metadata=metadata,
                rank_reasons=reasons
            )
            rerank_results.append(result)

        # 按重排序分数排序
        rerank_results.sort(key=lambda x: x.rerank_score, reverse=True)

        # 返回top_k结果
        return rerank_results[:top_k]

    def test_reranker(self) -> Any:
        """测试重排序器"""
        logger.info("\n🧪 测试向量重排序器")

        # 测试查询
        query = "劳动合同的解除条件有哪些？"

        # 模拟候选文档
        candidates = [
            {
                "chunk_id": "chunk_001",
                "content": "第四章 劳动合同的解除和终止\n第三十六条 用人单位与劳动者协商一致，可以解除劳动合同。",
                "metadata": {
                    "structural_info": {"level": "H2"},
                    "document_type": "法律"
                },
                "score": 0.7
            },
            {
                "chunk_id": "chunk_002",
                "content": "第三十九条 劳动者有下列情形之一的，用人单位可以解除劳动合同：（一）在试用期间被证明不符合录用条件的；",
                "metadata": {
                    "structural_info": {"level": "ARTICLE"},
                    "document_type": "法律"
                },
                "score": 0.8
            },
            {
                "chunk_id": "chunk_003",
                "content": "第五章 特别规定\n第一节 集体合同",
                "metadata": {
                    "structural_info": {"level": "H2"},
                    "document_type": "法律"
                },
                "score": 0.4
            }
        ]

        # 执行重排序
        results = self.rerank(query, candidates)

        # 输出结果
        logger.info(f"\n📊 重排序结果 (查询: {query})")
        for i, result in enumerate(results):
            logger.info(f"\n{i+1}. 排名: {i+1}")
            logger.info(f"   ID: {result.chunk_id}")
            logger.info(f"   原始分数: {result.original_score:.3f}")
            logger.info(f"   重排序分数: {result.rerank_score:.3f}")
            logger.info(f"   内容: {result.content}")
            logger.info(f"   排序原因: {', '.join(result.rank_reasons) if result.rank_reasons else '无'}")

        return results

    def save_rerank_config(self) -> None:
        """保存重排序配置"""
        config = {
            "version": "2.0.0",
            "created_at": datetime.now().isoformat(),
            "weights": self.weights,
            "legal_keywords_count": len(self.legal_keywords),
            "structure_hierarchy": self.structure_hierarchy
        }

        config_path = Path("/Users/xujian/Athena工作平台/production/config/reranker_config.json")
        config_path.parent.mkdir(parents=True, exist_ok=True)

        with open(config_path, 'w', encoding='utf-8') as f:
            json.dump(config, f, ensure_ascii=False, indent=2)

        logger.info(f"✅ 重排序配置已保存: {config_path}")

def main() -> None:
    """主函数"""
    print("="*100)
    print("🔄 向量重排序器 🔄")
    print("="*100)

    # 初始化重排序器
    reranker = VectorReranker()

    # 保存配置
    reranker.save_rerank_config()

    # 运行测试
    reranker.test_reranker()

    # 说明使用方法
    print("\n📖 使用说明:")
    print("1. VectorReranker用于对检索结果进行重排序")
    print("2. 结合了向量相似度、文本匹配、法律相关性和结构重要性")
    print("3. 可通过调整weights配置各项权重")
    print("4. 在Hybrid RAG系统中，用于提升最终检索结果的准确性")

if __name__ == "__main__":
    main()
