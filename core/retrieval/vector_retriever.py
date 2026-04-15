#!/usr/bin/env python3
from __future__ import annotations
"""
向量检索器
Vector Retriever for Athena Platform

整合BGE嵌入和向量数据库,提供完整的向量检索功能
"""

import os
from typing import Any

import numpy as np

from core.embedding.bge_embedding_service import (
    get_bge_service,
)
from core.logging_config import setup_logging

logger = setup_logging()


class VectorRetrieverConfig:
    """向量检索器配置"""

    # 默认配置
    DEFAULT_MODEL = "BAAI/bge-m3"
    DEFAULT_TOP_K = 10
    DEFAULT_SCORE_THRESHOLD = 0.6

    # Qdrant配置
    QDRANT_URL = os.getenv("QDRANT_URL", "http://localhost:6333")
    QDRANT_API_KEY = os.getenv("QDRANT_API_KEY", None)

    # 集合配置
    COLLECTION_PREFIX = "athena"

    # 集合命名映射
    COLLECTIONS = {
        "general": f"{COLLECTION_PREFIX}_general",
        "patent": f"{COLLECTION_PREFIX}_patent",
        "legal": f"{COLLECTION_PREFIX}_legal",
        "technical": f"{COLLECTION_PREFIX}_technical",
    }


class VectorRetriever:
    """向量检索器"""

    def __init__(
        self,
        model_name: str = VectorRetrieverConfig.DEFAULT_MODEL,
        collection_name: str = "general",
        top_k: int = VectorRetrieverConfig.DEFAULT_TOP_K,
        score_threshold: float = VectorRetrieverConfig.DEFAULT_SCORE_THRESHOLD,
        device: str = "cpu",
    ):
        """
        初始化向量检索器

        Args:
            model_name: BGE模型名称
            collection_name: 向量集合名称
            top_k: 返回结果数量
            score_threshold: 相似度阈值
            device: 运行设备
        """
        self.model_name = model_name
        self.collection_name = collection_name
        self.top_k = top_k
        self.score_threshold = score_threshold
        self.device = device

        # 初始化BGE嵌入服务
        self.embedding_service = get_bge_service(model_name, device)
        self.dimension = self.embedding_service.dimension

        # 向量存储(内存中,可扩展为Qdrant)
        self._vectors: dict[str, np.ndarray] = {}
        self._payloads: dict[str, dict[str, Any]] = {}

        # 统计信息
        self._stats = {"total_vectors": 0, "total_searches": 0, "cache_hits": 0}

    def add(
        self,
        texts: str | list[str],
        payloads: list[dict[str, Any]] | None = None,
        ids: list[str] | None = None,
    ) -> list[str]:
        """
        添加文本向量到存储

        Args:
            texts: 文本或文本列表
            payloads: 有效载荷数据列表
            ids: 自定义ID列表

        Returns:
            向量ID列表
        """
        if isinstance(texts, str):
            texts = [texts]

        # 编码文本
        embeddings = self.embedding_service.encode(texts, normalize=True)

        # 生成ID
        if ids is None:
            ids = [f"{i:07d}" for i in range(len(texts))]

        # 准备payload
        if payloads is None:
            payloads = [{"text": text} for text in texts]
        else:
            for i, payload in enumerate(payloads):
                if "text" not in payload:
                    payload["text"] = texts[i]

        # 存储向量和payload
        for vec_id, embedding, payload in zip(ids, embeddings, payloads, strict=False):
            self._vectors[vec_id] = embedding
            self._payloads[vec_id] = payload
            self._stats["total_vectors"] += 1

        logger.info(f"添加 {len(ids)} 个向量到集合 '{self.collection_name}'")
        return ids

    def search(
        self,
        query: str,
        top_k: int | None = None,
        score_threshold: float | None = None,
        filters: dict[str, Any] | None = None,
    ) -> list[dict[str, Any]]:
        """
        向量检索

        Args:
            query: 查询文本
            top_k: 返回结果数量
            score_threshold: 相似度阈值
            filters: 过滤条件

        Returns:
            检索结果列表
        """
        top_k = top_k or self.top_k
        score_threshold = score_threshold or self.score_threshold

        self._stats["total_searches"] += 1

        # 编码查询
        query_embedding = self.embedding_service.encode(query, normalize=True)

        # 计算相似度
        results = []
        for vec_id, vector in self._vectors.items():
            # 计算余弦相似度
            score = float(np.dot(query_embedding[0], vector))

            # 应用阈值
            if score >= score_threshold:
                # 应用过滤器
                payload = self._payloads[vec_id]
                if self._match_filters(payload, filters):
                    results.append({"id": vec_id, "score": score, "payload": payload})

        # 按分数排序并取top-k
        results.sort(key=lambda x: x["score"], reverse=True)
        results = results[:top_k]

        return results

    def _match_filters(self, payload: dict[str, Any], filters: dict[str, Any]) -> bool:
        """检查payload是否匹配过滤条件"""
        if not filters:
            return True

        for key, value in filters.items():
            if key not in payload:
                return False
            if payload[key] != value:
                return False

        return True

    def delete(self, ids: list[str]) -> int:
        """
        删除向量

        Args:
            ids: 向量ID列表

        Returns:
            删除数量
        """
        count = 0
        for vec_id in ids:
            if vec_id in self._vectors:
                del self._vectors[vec_id]
                del self._payloads[vec_id]
                count += 1
                self._stats["total_vectors"] -= 1

        logger.info(f"从集合 '{self.collection_name}' 删除 {count} 个向量")
        return count

    def get_stats(self) -> dict[str, Any]:
        """获取检索器统计信息"""
        return {
            "collection_name": self.collection_name,
            "model_name": self.model_name,
            "dimension": self.dimension,
            "total_vectors": self._stats["total_vectors"],
            "total_searches": self._stats["total_searches"],
            "cache_stats": self.embedding_service.get_cache_stats(),
        }

    def clear(self) -> Any:
        """清空所有向量"""
        count = len(self._vectors)
        self._vectors.clear()
        self._payloads.clear()
        self._stats["total_vectors"] = 0
        logger.info(f"清空集合 '{self.collection_name}',删除 {count} 个向量")


class PatentVectorRetriever(VectorRetriever):
    """专利向量检索器(专用)"""

    def __init__(self, model_name: str = "BAAI/bge-m3", **kwargs):
        super().__init__(model_name=model_name, collection_name="patent", **kwargs)

    def add_patents(self, patents: list[dict[str, Any]], text_field: str = "abstract") -> list[str]:
        """
        添加专利文档

        Args:
            patents: 专利列表
            text_field: 用作嵌入的文本字段

        Returns:
            向量ID列表
        """
        texts = []
        payloads = []

        for patent in patents:
            text = patent.get(text_field, patent.get("title", ""))
            texts.append(text)
            payloads.append({**patent, "_text_field": text_field})

        return self.add(texts, payloads=payloads)

    def search_patents(
        self, query: str, top_k: int = 10, score_threshold: float = 0.5
    ) -> list[dict[str, Any]]:
        """
        检索专利

        Args:
            query: 查询文本
            top_k: 返回数量
            score_threshold: 相似度阈值

        Returns:
            专利结果列表
        """
        results = self.search(query, top_k=top_k, score_threshold=score_threshold)

        # 移除内部字段
        clean_results = []
        for result in results:
            payload = result["payload"].copy()
            payload.pop("_text_field", None)
            clean_results.append({"id": result["id"], "score": result["score"], "payload": payload})

        return clean_results


# =============================================================================
# 便捷函数
# =============================================================================


def create_retriever(
    collection_name: str = "general", model_name: str = "BAAI/bge-m3"
) -> VectorRetriever:
    """创建向量检索器(便捷函数)"""
    return VectorRetriever(model_name=model_name, collection_name=collection_name)


def create_patent_retriever(model_name: str = "BAAI/bge-m3") -> PatentVectorRetriever:
    """创建专利向量检索器(便捷函数)"""
    return PatentVectorRetriever(model_name=model_name)


# =============================================================================
# 主程序
# =============================================================================

if __name__ == "__main__":
    import sys

    # setup_logging()  # 日志配置已移至模块导入

    print("=" * 60)
    print("向量检索器测试")
    print("=" * 60)

    try:
        # 创建检索器
        retriever = create_retriever("general")

        # 添加测试文档
        documents = [
            "专利是保护发明创造的重要法律制度",
            "商标用于区分商品或服务的来源",
            "版权保护原创作品的著作权",
            "专利检索可以帮助查找相关技术",
        ]

        print("\n1. 添加文档...")
        retriever.add(documents)

        # 检索
        print("\n2. 向量检索...")
        query = "如何查找专利技术"
        results = retriever.search(query, top_k=3)

        print(f"查询: {query}")
        print("结果:")
        for i, result in enumerate(results, 1):
            print(f"  {i}. [{result['score']:.4f}] {result['payload']['text']}")

        # 统计
        print("\n3. 统计信息...")
        stats = retriever.get_stats()
        for key, value in stats.items():
            if key != "cache_stats":
                print(f"  {key}: {value}")

        print("\n✅ 测试完成!")

    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)
