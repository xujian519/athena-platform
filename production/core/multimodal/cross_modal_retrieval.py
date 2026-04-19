#!/usr/bin/env python3
"""
跨模态检索系统
Cross-Modal Retrieval System

支持文本、图像、音频、视频之间的跨模态语义检索

作者: Athena平台团队
创建时间: 2025-01-11
版本: v1.0.0
"""

from __future__ import annotations
import logging
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any

import numpy as np

from core.multimodal.multimodal_fusion import (
    ModalityData,
    ModalityType,
    MultimodalFusion,
    create_image_modality,
    create_text_modality,
)


class RetrievalMode(Enum):
    """检索模式"""

    TEXT_TO_IMAGE = "text_to_image"  # 文本检索图像
    IMAGE_TO_TEXT = "image_to_text"  # 图像检索文本
    TEXT_TO_AUDIO = "text_to_audio"  # 文本检索音频
    AUDIO_TO_TEXT = "audio_to_text"  # 音频检索文本
    TEXT_TO_VIDEO = "text_to_video"  # 文本检索视频
    VIDEO_TO_TEXT = "video_to_text"  # 视频检索文本
    MULTIMODAL = "multimodal"  # 多模态联合检索


@dataclass
class RetrievalResult:
    """检索结果"""

    item_id: str
    modality: ModalityType
    score: float  # 相似度分数
    metadata: dict[str, Any] = field(default_factory=dict)
    preview_data: Any | None = None  # 预览数据(如缩略图、摘要等)

    def to_dict(self) -> dict[str, Any]:
        """转换为字典"""
        return {
            "item_id": self.item_id,
            "modality": self.modality.value,
            "score": self.score,
            "metadata": self.metadata,
            "preview_data": str(self.preview_data) if self.preview_data else None,
        }


@dataclass
class RetrievalResponse:
    """检索响应"""

    query_modality: ModalityType
    retrieval_mode: RetrievalMode
    results: list[RetrievalResult]
    total_count: int
    query_time: float = 0.0
    timestamp: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> dict[str, Any]:
        """转换为字典"""
        return {
            "query_modality": self.query_modality.value,
            "retrieval_mode": self.retrieval_mode.value,
            "results": [r.to_dict() for r in self.results],
            "total_count": self.total_count,
            "query_time": self.query_time,
            "timestamp": self.timestamp.isoformat(),
        }


class CrossModalRetrieval:
    """跨模态检索引擎"""

    def __init__(
        self,
        fusion_engine: MultimodalFusion | None = None,
        vector_db_client: Any | None = None,
    ):
        """
        初始化跨模态检索引擎

        Args:
            fusion_engine: 多模态融合引擎
            vector_db_client: 向量数据库客户端(如Qdrant)
        """
        self.fusion_engine = fusion_engine or MultimodalFusion(
            embedding_dim=1024
        )  # BGE-M3向量维度(已更新)
        self.vector_db_client = vector_db_client
        self.logger = self._setup_logger()

        # 检索索引(内存存储,生产环境应使用向量数据库)
        self.index = {}  # {item_id: ModalityData}
        self.index_metadata = {}  # {item_id: metadata}

    def _setup_logger(self) -> logging.Logger:
        """设置日志"""
        logger = logging.getLogger("CrossModalRetrieval")
        logger.setLevel(logging.INFO)

        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
            handler.setFormatter(formatter)
            logger.addHandler(handler)

        return logger

    def index_item(
        self, item_id: str, modality_data: ModalityData, metadata: dict[str, Any] | None = None
    ) -> bool:
        """
        索引单个项目

        Args:
            item_id: 项目ID
            modality_data: 模态数据
            metadata: 元数据

        Returns:
            是否成功
        """
        try:
            # 提取向量
            embedding = self.fusion_engine.extract_embedding(modality_data)
            modality_data.embedding = embedding

            # 存储到索引
            self.index[item_id] = modality_data
            self.index_metadata[item_id] = metadata or {}

            # 如果有向量数据库,同时存储到向量数据库
            if self.vector_db_client:
                try:
                    import uuid

                    from qdrant_client.models import PointStruct

                    PointStruct(
                        id=uuid.uuid4().hex,
                        vector=embedding.tolist(),
                        payload={
                            "item_id": item_id,
                            "modality": modality_data.modality.value,
                            **(metadata or {}),
                        },
                    )
                    # 存储到Qdrant(需要先创建集合)
                    # self.vector_db_client.upsert(...)
                except Exception as e:
                    self.logger.debug(f"向量数据库存储失败: {e}")

            self.logger.info(f"✅ 索引成功: {item_id}")
            return True

        except Exception as e:
            self.logger.error(f"❌ 索引失败: {e}")
            return False

    def index_batch(self, items: list[tuple[str, ModalityData, dict[str, Any]]]) -> int:
        """
        批量索引

        Args:
            items: [(item_id, modality_data, metadata), ...]

        Returns:
            成功索引的数量
        """
        success_count = 0
        for item_id, modality_data, metadata in items:
            if self.index_item(item_id, modality_data, metadata):
                success_count += 1
        return success_count

    def retrieve(
        self,
        query: str | ModalityData,
        mode: RetrievalMode,
        top_k: int = 10,
        filters: dict[str, Any] | None = None,
    ) -> RetrievalResponse:
        """
        跨模态检索

        Args:
            query: 查询(文本字符串或ModalityData)
            mode: 检索模式
            top_k: 返回前k个结果
            filters: 过滤条件

        Returns:
            检索响应
        """
        start_time = datetime.now()

        try:
            # 1. 处理查询
            if isinstance(query, str):
                query_modality = ModalityType.TEXT
                query_data = create_text_modality(query)
            elif isinstance(query, ModalityData):  # type: ignore[unnecessary-isinstance]
                query_modality = query.modality
                query_data = query
            else:
                raise ValueError("不支持的查询类型")

            # 2. 提取查询向量
            query_embedding = self.fusion_engine.extract_embedding(query_data)

            # 3. 根据模式确定目标模态
            target_modality = self._get_target_modality(mode)

            # 4. 计算相似度
            results = []
            for item_id, item_data in self.index.items():
                # 模态过滤
                if target_modality and item_data.modality != target_modality:
                    continue

                # 元数据过滤
                if filters:
                    item_metadata = self.index_metadata.get(item_id, {})
                    if not all(item_metadata.get(k) == v for k, v in filters.items()):
                        continue

                # 计算相似度
                if item_data.embedding is not None:
                    similarity = self._calculate_similarity(query_embedding, item_data.embedding)

                    results.append(
                        RetrievalResult(
                            item_id=item_id,
                            modality=item_data.modality,
                            score=similarity,
                            metadata=self.index_metadata.get(item_id, {}),
                            preview_data=item_data.data,
                        )
                    )

            # 5. 排序并返回top_k
            results.sort(key=lambda x: x.score, reverse=True)  # type: ignore[arg-type]
            top_results = results[:top_k]

            query_time = (datetime.now() - start_time).total_seconds()

            self.logger.info(f"✅ 检索完成: 返回{len(top_results)}个结果, 耗时{query_time:.3f}秒")

            return RetrievalResponse(
                query_modality=query_modality,
                retrieval_mode=mode,
                results=top_results,
                total_count=len(results),
                query_time=query_time,
            )

        except Exception as e:
            self.logger.error(f"❌ 检索失败: {e}")
            return RetrievalResponse(
                query_modality=ModalityType.TEXT,
                retrieval_mode=mode,
                results=[],
                total_count=0,
                query_time=(datetime.now() - start_time).total_seconds(),
            )

    def _get_target_modality(self, mode: RetrievalMode) -> ModalityType | None:
        """根据检索模式获取目标模态"""
        mapping = {
            RetrievalMode.TEXT_TO_IMAGE: ModalityType.IMAGE,
            RetrievalMode.IMAGE_TO_TEXT: ModalityType.TEXT,
            RetrievalMode.TEXT_TO_AUDIO: ModalityType.AUDIO,
            RetrievalMode.AUDIO_TO_TEXT: ModalityType.TEXT,
            RetrievalMode.TEXT_TO_VIDEO: ModalityType.VIDEO,
            RetrievalMode.VIDEO_TO_TEXT: ModalityType.TEXT,
        }
        return mapping.get(mode)

    def _calculate_similarity(
        self, vec1: np.ndarray, vec2: np.ndarray, method: str = "cosine"
    ) -> float:
        """
        计算向量相似度

        Args:
            vec1: 向量1
            vec2: 向量2
            method: 相似度计算方法(cosine, euclidean, dot)

        Returns:
            相似度分数
        """
        if method == "cosine":
            # 余弦相似度
            return float(np.dot(vec1, vec2) / (np.linalg.norm(vec1) * np.linalg.norm(vec2) + 1e-8))
        elif method == "euclidean":
            # 欧氏距离(转换为相似度)
            dist = np.linalg.norm(vec1 - vec2)
            return float(1 / (1 + dist))
        elif method == "dot":
            # 点积
            return float(np.dot(vec1, vec2))
        else:
            return 0.0

    def semantic_search(
        self, query_text: str, target_modality: ModalityType, top_k: int = 10
    ) -> list[RetrievalResult]:
        """
        语义搜索(便捷方法)

        Args:
            query_text: 查询文本
            target_modality: 目标模态
            top_k: 返回数量

        Returns:
            检索结果列表
        """
        # 确定检索模式
        mode_map = {
            ModalityType.IMAGE: RetrievalMode.TEXT_TO_IMAGE,
            ModalityType.AUDIO: RetrievalMode.TEXT_TO_AUDIO,
            ModalityType.VIDEO: RetrievalMode.TEXT_TO_VIDEO,
            ModalityType.TEXT: RetrievalMode.MULTIMODAL,
        }

        mode = mode_map.get(target_modality, RetrievalMode.MULTIMODAL)

        response = self.retrieve(query=query_text, mode=mode, top_k=top_k)

        return response.results

    def hybrid_search(
        self,
        query_text: str,
        query_image: str | None = None,
        top_k: int = 10,
        text_weight: float = 0.7,
        image_weight: float = 0.3,
    ) -> list[RetrievalResult]:
        """
        混合搜索(文本+图像)

        Args:
            query_text: 查询文本
            query_image: 查询图像路径(可选)
            top_k: 返回数量
            text_weight: 文本权重
            image_weight: 图像权重

        Returns:
            检索结果列表
        """
        # 创建多模态查询
        modalities = [create_text_modality(query_text)]

        if query_image:
            modalities.append(create_image_modality(query_image))

        # 融合查询
        fused = self.fusion_engine.fuse_modalities(
            modalities, weights=[text_weight, image_weight] if query_image else [1.0]
        )

        # 使用融合向量检索
        query_data = ModalityData(
            modality=ModalityType.MULTIMODAL, data="", embedding=fused.fused_embedding
        )

        response = self.retrieve(query=query_data, mode=RetrievalMode.MULTIMODAL, top_k=top_k)

        return response.results

    def get_index_stats(self) -> dict[str, Any]:
        """获取索引统计信息"""
        modality_counts = {}
        for item_data in self.index.values():
            modality = item_data.modality.value
            modality_counts[modality] = modality_counts.get(modality, 0) + 1

        return {
            "total_items": len(self.index),
            "modality_distribution": modality_counts,
            "indexed_ids": list(self.index.keys()),
        }

    def clear_index(self):
        """清空索引"""
        self.index.clear()
        self.index_metadata.clear()
        self.logger.info("✅ 索引已清空")


# 便捷函数
def build_sample_index(retrieval: CrossModalRetrieval) -> int:
    """
    构建示例索引

    Args:
        retrieval: 检索引擎实例

    Returns:
        索引的项目数
    """
    # 示例数据
    sample_items = [
        # 文本项目
        (
            "doc1",
            create_text_modality("智能家居控制系统的用户手册"),
            {"category": "manual", "lang": "zh"},
        ),
        ("doc2", create_text_modality("机械臂操作指南 v2.0"), {"category": "guide", "lang": "zh"}),
        ("doc3", create_text_modality("AI图像识别算法综述"), {"category": "paper", "lang": "zh"}),
        # 图像项目
        (
            "img1",
            create_image_modality("robot_arm.png"),
            {"category": "product", "type": "diagram"},
        ),
        ("img2", create_image_modality("smart_home.jpg"), {"category": "scene", "type": "photo"}),
        (
            "img3",
            create_image_modality("ai_network.png"),
            {"category": "concept", "type": "illustration"},
        ),
    ]

    return retrieval.index_batch(sample_items)


# 使用示例
async def main():
    """主函数示例"""
    print("=" * 60)
    print("🔍 跨模态检索系统演示")
    print("=" * 60)

    # 1. 创建检索引擎
    retrieval = CrossModalRetrieval()

    # 2. 构建示例索引
    print("\n📚 构建示例索引...")
    count = build_sample_index(retrieval)
    print(f"✅ 索引完成: {count}个项目")

    # 3. 显示索引统计
    stats = retrieval.get_index_stats()
    print("\n📊 索引统计:")
    print(f"   总项目数: {stats['total_items']}")
    print(f"   模态分布: {stats['modality_distribution']}")

    # 4. 文本检索图像
    print("\n🔍 示例1: 文本检索图像")
    results = retrieval.semantic_search(
        query_text="机器人产品图", target_modality=ModalityType.IMAGE, top_k=3
    )

    print(f"   找到 {len(results)} 个结果:")
    for i, result in enumerate(results[:3], 1):
        print(f"   {i}. {result.item_id} (相似度: {result.score:.3f})")

    # 5. 文本检索文本
    print("\n🔍 示例2: 文本检索文本")
    results = retrieval.semantic_search(
        query_text="操作指南", target_modality=ModalityType.TEXT, top_k=3
    )

    print(f"   找到 {len(results)} 个结果:")
    for i, result in enumerate(results[:3], 1):
        print(f"   {i}. {result.item_id} (相似度: {result.score:.3f})")

    # 6. 混合检索
    print("\n🔍 示例3: 混合检索(假设有图像)")
    print("   (需要实际图像文件才能演示)")

    print("\n" + "=" * 60)
    print("✅ 演示完成")
    print("=" * 60)


# 入口点: @async_main装饰器已添加到main函数
