#!/usr/bin/env python3
"""
向量库导入模块
Vector Database Importer

将处理好的法律文档导入到Qdrant向量数据库

作者: Athena AI系统
创建时间: 2025-01-06
版本: 1.0.0
"""

import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

# 向量数据库
from qdrant_client import QdrantClient
from qdrant_client.models import (
    Distance,
    FieldCondition,
    Filter,
    MatchValue,
    PointStruct,
    VectorParams,
)


# 向量化服务
from core.embedding.bge_embedding_service import BGEEmbeddingService

logger = logging.getLogger(__name__)


class VectorDBImporter:
    """向量库导入器"""

    def __init__(self, config: dict[str, Any] | None = None):
        """
        初始化导入器

        Args:
            config: 配置字典,包含:
                - qdrant_host: Qdrant主机地址
                - qdrant_port: Qdrant端口
                - collection_name: 集合名称
                - vector_size: 向量维度(768=bge-base-zh, 1024=bge-large-zh)
                - batch_size: 批量导入大小(默认100)
                - embedding_model: 嵌入模型名称(默认bge-large-zh)
        """
        self.config = config or {}
        self.qdrant_host = self.config.get("qdrant_host", "localhost")
        self.qdrant_port = self.config.get("qdrant_port", 6333)
        self.collection_name = self.config.get("collection_name", "legal_books_yianshuofa")
        self.vector_size = self.config.get("vector_size", 1024)  # 默认使用1024维
        self.batch_size = self.config.get("batch_size", 100)
        self.embedding_model = self.config.get("embedding_model", "bge-large-zh")

        # 初始化Qdrant客户端
        self.qdrant_client = QdrantClient(host=self.qdrant_host, port=self.qdrant_port)

        # 初始化向量化服务(支持自定义模型)
        self.embedding_service = BGEEmbeddingService(
            model_name=self.embedding_model, device=self.config.get("device", "cpu")  # 支持MPS/CUDA
        )

        logger.info(
            f"🔢 向量库导入器初始化完成 (模型: {self.embedding_model}, 维度: {self.vector_size})"
        )

    async def import_documents(self, vector_docs: list[dict[str, Any]]) -> dict[str, Any]:
        """
        导入文档到向量库

        Args:
            vector_docs: 向量化文档列表

        Returns:
            导入结果
        """
        logger.info(f"📥 开始导入 {len(vector_docs)} 个文档到向量库")

        # 确保集合存在
        await self._ensure_collection_exists()

        # 批量导入
        success_count = 0
        failed_count = 0
        errors = []

        for i in range(0, len(vector_docs), self.batch_size):
            batch = vector_docs[i : i + self.batch_size]

            try:
                # 生成向量
                vectors = await self._generate_vectors(batch)

                # 准备Qdrant点数据
                points = []
                for j, doc in enumerate(batch):
                    # 使用整数ID(全局计数器)
                    point_id = success_count + j
                    points.append(
                        PointStruct(
                            id=point_id,
                            vector=vectors[j],
                            payload={"text": doc["text"], **doc["metadata"]},
                        )
                    )

                # 上传到Qdrant
                self.qdrant_client.upsert(collection_name=self.collection_name, points=points)

                success_count += len(batch)
                logger.info(f"✅ 已导入 {success_count}/{len(vector_docs)} 个文档")

            except Exception as e:
                failed_count += len(batch)
                error_msg = f"批次 {i//self.batch_size + 1} 导入失败: {e!s}"
                errors.append(error_msg)
                logger.error(error_msg)

        logger.info(f"📊 导入完成: 成功 {success_count}, 失败 {failed_count}")

        return {
            "status": "completed",
            "success_count": success_count,
            "failed_count": failed_count,
            "errors": errors,
            "collection_name": self.collection_name,
        }

    async def _ensure_collection_exists(self):
        """确保集合存在,不存在则创建"""
        collections = self.qdrant_client.get_collections().collections
        collection_names = [c.name for c in collections]

        if self.collection_name not in collection_names:
            logger.info(f"📦 创建新集合: {self.collection_name}")

            self.qdrant_client.create_collection(
                collection_name=self.collection_name,
                vectors_config=VectorParams(size=self.vector_size, distance=Distance.COSINE),
            )

            # 创建索引
            self.qdrant_client.create_payload_index(
                collection_name=self.collection_name,
                field_name="metadata.type",
                field_schema="keyword",
            )

            logger.info(f"✅ 集合 {self.collection_name} 创建成功")
        else:
            logger.info(f"📦 集合 {self.collection_name} 已存在")

    async def _generate_vectors(self, docs: list[dict[str, Any]]) -> list[list[float]]:
        """
        生成文档向量

        Args:
            docs: 文档列表

        Returns:
            向量列表
        """
        texts = [doc["text"] for doc in docs]

        # 使用BGE模型的encode方法生成向量
        vectors = self.embedding_service.encode(texts)

        # 转换为列表格式
        return vectors.tolist()

    def _generate_point_id(self, doc_id: str) -> str:
        """
        生成Qdrant点ID

        Args:
            doc_id: 文档ID

        Returns:
            点ID(使用文档ID本身)
        """
        return doc_id

    async def search_similar(
        self, query: str, limit: int = 10, filter_type: str | None = None
    ) -> list[dict[str, Any]]:
        """
        搜索相似文档

        Args:
            query: 查询文本
            limit: 返回数量
            filter_type: 文档类型过滤(text_chunk/case_story/legal_rule)

        Returns:
            相似文档列表
        """
        # 生成查询向量
        query_vector = self.embedding_service.encode(query).tolist()

        # 构建过滤条件
        query_filter = None
        if filter_type:
            query_filter = Filter(
                must=[FieldCondition(key="metadata.type", match=MatchValue(value=filter_type))]
            )

        # 搜索
        search_result = self.qdrant_client.search(
            collection_name=self.collection_name,
            query_vector=query_vector,
            query_filter=query_filter,
            limit=limit,
            score_threshold=0.5,
        )

        # 格式化结果
        results = []
        for hit in search_result:
            results.append(
                {
                    "id": hit.id,
                    "score": hit.score,
                    "text": hit.payload.get("text", ""),
                    "metadata": hit.payload.get("metadata", {}),
                }
            )

        return results

    async def get_collection_stats(self) -> dict[str, Any]:
        """获取集合统计信息"""
        collection_info = self.qdrant_client.get_collection(self.collection_name)

        return {
            "collection_name": self.collection_name,
            "points_count": collection_info.points_count,
            "vector_size": collection_info.config.params.vectors.size,
            "status": collection_info.status,
        }


async def main():
    """测试向量库导入"""
    # 读取之前生成的向量文档
    vector_docs_file = Path("./data/legal_books/yianshuofa/vector_docs_20250106_xxxxxx.json")

    if not vector_docs_file.exists():
        print("❌ 向量文档文件不存在,请先运行 legal_book_pipeline.py")
        return

    with open(vector_docs_file, encoding="utf-8") as f:
        vector_docs = json.load(f)

    # 配置导入器
    config = {
        "qdrant_host": "localhost",
        "qdrant_port": 6333,
        "collection_name": "legal_books_yianshuofa",
        "vector_size": 768,
        "batch_size": 100,
    }

    # 创建并执行导入
    importer = VectorDBImporter(config)
    result = await importer.import_documents(vector_docs)

    print("\n" + "=" * 50)
    print("📊 向量库导入完成!")
    print("=" * 50)
    print(json.dumps(result, ensure_ascii=False, indent=2))

    # 获取统计信息
    stats = await importer.get_collection_stats()
    print("\n📈 集合统计:")
    print(json.dumps(stats, ensure_ascii=False, indent=2))


# 入口点: @async_main装饰器已添加到main函数
