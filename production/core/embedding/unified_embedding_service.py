#!/usr/bin/env python3
from __future__ import annotations
"""
统一嵌入服务
Unified Embedding Service for Athena Platform

为整个平台提供统一的BGE嵌入服务,支持多模块配置优化

作者: 小诺·双鱼座
创建时间: 2025-12-16
"""

import asyncio
import logging
from dataclasses import dataclass
from enum import Enum
from typing import Any

from ..nlp.bge_embedding_service import get_bge_service

logger = logging.getLogger(__name__)


class ModuleType(Enum):
    """模块类型枚举"""

    KNOWLEDGE_GRAPH = "knowledge_graph"
    MEMORY = "memory"
    DOCUMENT_PROCESSING = "document_processing"
    COGNITION = "cognition"
    LEARNING = "learning"
    COMMUNICATION = "communication"
    PATENT_SEARCH = "patent_search"
    LEGAL_ANALYSIS = "legal_analysis"
    DEFAULT = "default"


@dataclass
class ModuleConfig:
    """模块配置"""

    task_type: str = "default"
    temperature: float | None = None
    max_length: int | None = None
    batch_size: int = 32
    cache_ttl: int = 3600  # 缓存时间(秒)
    priority: int = 1  # 优先级


class UnifiedEmbeddingService:
    """统一嵌入服务"""

    def __init__(self):
        self.name = "统一嵌入服务"
        self.version = "1.0.0"
        self.logger = logging.getLogger(self.name)

        # BGE服务实例
        self.bge_service = None

        # 各模块配置
        self.module_configs = self._init_module_configs()

        # 使用统计
        self.module_stats = {
            module: {"total_requests": 0, "total_texts": 0, "total_time": 0.0}
            for module in ModuleType
        }

        # 预热标记
        self._prewarmed = False

    def _init_module_configs(self) -> dict[ModuleType, ModuleConfig]:
        """初始化各模块配置"""
        return {
            ModuleType.KNOWLEDGE_GRAPH: ModuleConfig(
                task_type="entity_extraction", batch_size=64, cache_ttl=7200  # 知识图谱缓存更久
            ),
            ModuleType.MEMORY: ModuleConfig(
                task_type="memory_encoding", batch_size=16, cache_ttl=86400  # 记忆缓存最久
            ),
            ModuleType.DOCUMENT_PROCESSING: ModuleConfig(
                task_type="document_analysis", batch_size=32, max_length=512
            ),
            ModuleType.COGNITION: ModuleConfig(
                task_type="decision_support", batch_size=8, priority=2
            ),
            ModuleType.LEARNING: ModuleConfig(
                task_type="knowledge_encoding", batch_size=32, cache_ttl=3600
            ),
            ModuleType.COMMUNICATION: ModuleConfig(
                task_type="conversation", batch_size=8, priority=3
            ),
            ModuleType.PATENT_SEARCH: ModuleConfig(
                task_type="patent_search", batch_size=16, priority=1
            ),
            ModuleType.LEGAL_ANALYSIS: ModuleConfig(
                task_type="legal_analysis", batch_size=16, priority=1
            ),
            ModuleType.DEFAULT: ModuleConfig(task_type="default", batch_size=32),
        }

    async def initialize(self):
        """异步初始化"""
        if self.bge_service is None:
            self.bge_service = await get_bge_service()
            self.logger.info("统一嵌入服务初始化完成")

    async def preheat(self):
        """预热服务"""
        if self._prewarmed:
            return

        await self.initialize()

        # 预热各模块
        preheat_texts = {
            ModuleType.KNOWLEDGE_GRAPH: ["实体关系抽取测试"],
            ModuleType.MEMORY: ["记忆编码测试"],
            ModuleType.DOCUMENT_PROCESSING: ["文档分析测试"],
            ModuleType.COGNITION: ["决策支持测试"],
            ModuleType.LEARNING: ["知识编码测试"],
            ModuleType.COMMUNICATION: ["对话理解测试"],
        }

        print("🔥 开始预热各模块...")
        for module_type, texts in preheat_texts.items():
            try:
                await self.encode(texts[0], module_type)
                print(f"   ✅ {module_type.value} 预热完成")
            except Exception as e:
                print(f"   ⚠️ {module_type.value} 预热失败: {e}")

        self._prewarmed = True
        print("🎉 所有模块预热完成!")

    async def encode(
        self,
        texts: str | list[str],
        module_type: ModuleType = ModuleType.DEFAULT,
        custom_config: ModuleConfig | None = None,
    ) -> dict[str, Any]:
        """
        获取嵌入向量

        Args:
            texts: 文本或文本列表
            module_type: 模块类型
            custom_config: 自定义配置

        Returns:
            嵌入结果
        """
        await self.initialize()

        # 标准化输入
        if isinstance(texts, str):
            texts = [texts]
            single_text = True
        else:
            single_text = False

        # 获取配置
        config = custom_config or self.module_configs.get(
            module_type, self.module_configs[ModuleType.DEFAULT]
        )

        # 更新统计
        self.module_stats[module_type]["total_requests"] += 1
        self.module_stats[module_type]["total_texts"] += len(texts)

        start_time = asyncio.get_event_loop().time()

        try:
            # 调用BGE服务
            result = await self.bge_service.encode(
                texts, task_type=config.task_type, batch_size=config.batch_size
            )

            # 计算处理时间
            processing_time = asyncio.get_event_loop().time() - start_time
            self.module_stats[module_type]["total_time"] += processing_time

            # 构建返回结果
            return {
                "embeddings": result.embeddings[0] if single_text else result.embeddings,
                "dimension": result.dimension,
                "module_type": module_type.value,
                "task_type": config.task_type,
                "processing_time": processing_time,
                "batch_size": len(texts),
                "model_name": result.model_name,
                "metadata": {
                    **result.metadata,
                    "module_config": {
                        "task_type": config.task_type,
                        "batch_size": config.batch_size,
                        "priority": config.priority,
                    },
                },
            }

        except Exception as e:
            self.logger.error(f"嵌入编码失败 [{module_type.value}]: {e}")
            raise e

    async def batch_encode_by_module(
        self,
        module_batches: dict[ModuleType, list[str]],
    ) -> dict[ModuleType, list[list[float]]]:
        """
        按模块批量编码

        Args:
            module_batches: 模块到文本列表的映射

        Returns:
            各模块的嵌入向量
        """
        results = {}

        # 按优先级排序
        sorted_modules = sorted(
            module_batches.items(), key=lambda x: self.module_configs[x[0]].priority
        )

        for module_type, texts in sorted_modules:
            if texts:
                try:
                    result = await self.encode(texts, module_type)
                    embeddings = result["embeddings"]
                    if isinstance(embeddings[0], list):
                        results[module_type] = embeddings
                    else:
                        results[module_type] = [embeddings]
                except Exception as e:
                    self.logger.error(f"批量编码失败 [{module_type.value}]: {e}")
                    results[module_type] = []

        return results

    def get_module_stats(self, module_type: ModuleType | None = None) -> dict[str, Any]:
        """获取模块使用统计"""
        if module_type:
            stats = self.module_stats[module_type]
            total_time = stats["total_time"]
            total_texts = stats["total_texts"]
            return {
                "module": module_type.value,
                "total_requests": stats["total_requests"],
                "total_texts": total_texts,
                "total_time": total_time,
                "avg_time_per_request": total_time / max(stats["total_requests"], 1),
                "avg_time_per_text": total_time / max(total_texts, 1),
                "throughput": total_texts / (total_time + 0.001),
            }
        else:
            return {module.value: self.get_module_stats(module) for module in ModuleType}

    def get_service_info(self) -> dict[str, Any]:
        """获取服务信息"""
        return {
            "name": self.name,
            "version": self.version,
            "bge_loaded": self.bge_service is not None,
            "prewarmed": self._prewarmed,
            "supported_modules": [module.value for module in ModuleType],
            "module_count": len(ModuleType),
        }

    async def health_check(self) -> dict[str, Any]:
        """健康检查"""
        health = {
            "status": "healthy",
            "service_loaded": self.bge_service is not None,
            "prewarmed": self._prewarmed,
            "modules": {},
        }

        # 检查各模块
        for module_type in ModuleType:
            try:
                test_text = f"{module_type.value}_health_check"
                await self.encode(test_text, module_type)
                health["modules"][module_type.value] = "healthy"
            except Exception as e:
                health["modules"][module_type.value] = f"unhealthy: {e}"
                health["status"] = "degraded"

        return health

    def update_module_config(self, module_type: ModuleType, config: ModuleConfig) -> None:
        """更新模块配置"""
        self.module_configs[module_type] = config
        self.logger.info(f"更新模块配置: {module_type.value}")


# 全局实例
_unified_service = None


async def get_unified_embedding_service() -> UnifiedEmbeddingService:
    """获取统一嵌入服务实例"""
    global _unified_service
    if _unified_service is None:
        _unified_service = UnifiedEmbeddingService()
        await _unified_service.initialize()
    return _unified_service


# 便捷函数
async def encode_for_knowledge_graph(texts: str | list[str]) -> dict[str, Any]:
    """知识图谱模块嵌入"""
    service = await get_unified_embedding_service()
    return await service.encode(texts, ModuleType.KNOWLEDGE_GRAPH)


async def encode_for_memory(texts: str | list[str]) -> dict[str, Any]:
    """记忆模块嵌入"""
    service = await get_unified_embedding_service()
    return await service.encode(texts, ModuleType.MEMORY)


async def encode_for_document(texts: str | list[str]) -> dict[str, Any]:
    """文档处理模块嵌入"""
    service = await get_unified_embedding_service()
    return await service.encode(texts, ModuleType.DOCUMENT_PROCESSING)


async def encode_for_cognition(texts: str | list[str]) -> dict[str, Any]:
    """认知决策模块嵌入"""
    service = await get_unified_embedding_service()
    return await service.encode(texts, ModuleType.COGNITION)


# 导出
__all__ = [
    "ModuleConfig",
    "ModuleType",
    "UnifiedEmbeddingService",
    "encode_for_cognition",
    "encode_for_document",
    "encode_for_knowledge_graph",
    "encode_for_memory",
    "get_unified_embedding_service",
]
