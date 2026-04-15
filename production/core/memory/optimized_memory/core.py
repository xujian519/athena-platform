#!/usr/bin/env python3
"""
优化记忆系统 - 核心模块
Optimized Memory System - Core Module

主系统类，整合所有组件

作者: Athena AI系统
创建时间: 2025-12-11
重构时间: 2026-01-26
版本: 2.1.0
"""

from __future__ import annotations
import asyncio
import json
import logging
import pickle
import time
import uuid
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from typing import Any

import numpy as np

from core.base_module import BaseModule
from core.logging_config import setup_logging
from core.memory.optimized_memory.tier_coordinator import IntelligentTierManager
from core.memory.optimized_memory.types import (
    DataAccessPattern,
    MemoryData,
    MemoryTier,
    VectorIndexConfig,
)
from core.memory.optimized_memory.vector_index import OptimizedVectorIndex

# 尝试导入现有的记忆系统
try:
    from core.memory.enhanced_memory_system import EnhancedMemorySystem

    MEMORY_SYSTEM_AVAILABLE = True
except ImportError:
    logging.warning("无法导入现有记忆系统")
    MEMORY_SYSTEM_AVAILABLE = False

logger = setup_logging()


class OptimizedMemorySystem(BaseModule):
    """优化版记忆系统 - 智能分层存储 + 向量索引优化"""

    def __init__(self, agent_id: str, config: dict[str, Any] | None = None):
        super().__init__(agent_id, config)

        # 优化配置
        self.optimization_config = {
            "intelligent_tiering": True,
            "vector_index_optimization": True,
            "parallel_processing": True,
            "smart_caching": True,
            "auto_compaction": True,
            "max_concurrent_operations": 10,
            **self.config,
        }

        # 初始化优化组件
        if self.optimization_config["intelligent_tiering"]:
            self.tier_manager = IntelligentTierManager(self.optimization_config)

        if self.optimization_config["vector_index_optimization"]:
            vector_config = VectorIndexConfig(
                index_type=self.optimization_config.get("vector_index_type", "hnsw"),
                dimension=self.optimization_config.get("embedding_dimension", 1024),
                ef_construction=self.optimization_config.get("ef_construction", 200),
                ef_search=self.optimization_config.get("ef_search", 50),
            )
            self.vector_index = OptimizedVectorIndex(vector_config)

        # 现有记忆系统集成
        self.enhanced_memory_system = None
        self.fallback_enabled = True

        if MEMORY_SYSTEM_AVAILABLE:
            try:
                self.enhanced_memory_system = EnhancedMemorySystem(self.agent_id)
                logger.info("✅ 现有记忆系统集成成功")
            except Exception as e:
                logger.warning(f"现有记忆系统集成失败: {e}")

        # 线程池
        self.executor = ThreadPoolExecutor(
            max_workers=self.optimization_config["max_concurrent_operations"]
        )

        # 统计信息
        self.optimization_stats: dict[str, Any] = {
            "total_stored_items": 0,
            "total_retrieved_items": 0,
            "tier_migrations": 0,
            "cache_hits": 0,
            "cache_misses": 0,
            "vector_searches": 0,
            "average_storage_time": 0.0,
            "average_retrieval_time": 0.0,
            "memory_efficiency": 0.0,
        }

        logger.info("🧠 优化版记忆系统初始化完成")

    async def _on_initialize(self) -> bool:
        """初始化优化记忆系统"""
        try:
            logger.info("🧠 初始化优化记忆系统...")

            # 初始化向量索引
            if hasattr(self, "vector_index") and self.optimization_config.get(
                "prebuild_index", True
            ):
                logger.info("🔧 预构建向量索引...")
                # 这里可以添加预构建逻辑

            logger.info("✅ 优化记忆系统初始化成功")
            return True

        except Exception as e:
            logger.error(f"❌ 优化记忆系统初始化失败: {e!s}")
            return False

    async def _on_start(self) -> bool:
        """启动优化记忆系统"""
        try:
            logger.info("🚀 启动优化记忆系统")

            # 启动后台任务
            if self.optimization_config.get("auto_compaction", True):
                asyncio.create_task(self._auto_compaction_loop())

            logger.info("✅ 优化记忆系统启动成功")
            return True

        except Exception as e:
            logger.error(f"❌ 优化记忆系统启动失败: {e!s}")
            return False

    async def _on_stop(self) -> bool:
        """停止优化记忆系统"""
        try:
            logger.info("⏹️ 停止优化记忆系统")
            logger.info("✅ 优化记忆系统停止成功")
            return True

        except Exception as e:
            logger.error(f"❌ 优化记忆系统停止失败: {e!s}")
            return False

    async def _on_shutdown(self) -> bool:
        """关闭优化记忆系统"""
        try:
            logger.info("🔚 关闭优化记忆系统")

            # 关闭线程池
            self.executor.shutdown(wait=True)

            # 生成优化报告
            self._generate_optimization_report()

            logger.info("✅ 优化记忆系统关闭成功")
            return True

        except Exception as e:
            logger.error(f"❌ 优化记忆系统关闭失败: {e!s}")
            return False

    async def _on_health_check(self) -> bool:
        """健康检查"""
        try:
            checks = {
                "tier_manager_available": hasattr(self, "tier_manager")
                or not self.optimization_config["intelligent_tiering"],
                "vector_index_available": hasattr(self, "vector_index")
                or not self.optimization_config["vector_index_optimization"],
                "enhanced_memory_available": self.enhanced_memory_system is not None
                or self.fallback_enabled,
                "parallel_processing_enabled": self.optimization_config["parallel_processing"],
                "memory_usage_ok": self._check_memory_usage(),
                "storage_space_ok": self._check_storage_space(),
            }

            overall_healthy = (
                checks["tier_manager_available"]
                and checks["vector_index_available"]
                and checks["enhanced_memory_available"]
                and checks["memory_usage_ok"]
                and checks["storage_space_ok"]
            )

            # 存储健康检查详情
            self._health_check_details = {  # type: ignore
                "tier_manager_status": "available" if checks["tier_manager_available"] else "unavailable",
                "vector_index_status": "available" if checks["vector_index_available"] else "unavailable",
                "enhanced_memory_status": "available" if checks["enhanced_memory_available"] else "unavailable",
                "optimization_stats": self.optimization_stats,
                "overall_healthy": overall_healthy,
            }

            return overall_healthy

        except Exception as e:
            logger.error(f"健康检查失败: {e!s}")
            return False

    def _check_memory_usage(self) -> bool:
        """检查内存使用"""
        try:
            import psutil

            process = psutil.Process()
            memory_mb = process.memory_info().rss / 1024 / 1024
            return memory_mb < self.optimization_config.get("max_memory_mb", 1024)  # 默认1GB
        except ImportError:
            return True  # 如果没有psutil，假设内存使用正常

    def _check_storage_space(self) -> bool:
        """检查存储空间"""
        try:
            import shutil

            _total, _used, free = shutil.disk_usage("/")
            free_gb = free / (1024**3)
            return free_gb > 1  # 至少1GB可用空间
        except Exception:
            return True

    async def store_optimized(
        self,
        data_id: str,
        content: Any,
        metadata: dict[str, Any] | None = None,
        vector_embedding: np.ndarray | None = None,
    ) -> bool:
        """优化存储"""
        start_time = time.time()

        try:
            # 创建内存数据对象
            memory_data = MemoryData(
                data_id=data_id,
                content=content,
                metadata=metadata or {},
                access_pattern=self._detect_access_pattern(data_id, content),
                size_bytes=self._calculate_size(content),
                vector_embedding=vector_embedding,
            )

            # 智能分层
            if hasattr(self, "tier_manager"):
                target_tier = self.tier_manager.evaluate_data_placement(memory_data)
                memory_data.tier = target_tier

                # 执行层级迁移
                if memory_data.tier != MemoryTier.COLD:
                    await self.tier_manager.execute_tier_migration(
                        memory_data, memory_data.tier
                    )

            # 向量索引
            if vector_embedding is not None and hasattr(self, "vector_index"):
                self.vector_index.add_vector(vector_embedding, metadata)
                if self.vector_index.build_time is None:
                    self.vector_index.build_index()

            # 并行存储到各个层级
            storage_tasks = []

            if memory_data.tier == MemoryTier.HOT and hasattr(self, "tier_manager"):
                storage_tasks.append(
                    self.tier_manager.tier_managers[MemoryTier.HOT].store(memory_data)
                )

            if memory_data.tier == MemoryTier.WARM and hasattr(self, "tier_manager"):
                storage_tasks.append(
                    self.tier_manager.tier_managers[MemoryTier.WARM].store(memory_data)
                )

            if memory_data.tier == MemoryTier.COLD and hasattr(self, "tier_manager"):
                storage_tasks.append(
                    self.tier_manager.tier_managers[MemoryTier.COLD].store(memory_data)
                )

            if storage_tasks and self.optimization_config["parallel_processing"]:
                await asyncio.gather(*storage_tasks, return_exceptions=True)

            # 更新统计信息
            processing_time = time.time() - start_time
            self._update_storage_stats(processing_time)

            logger.debug(f"✅ 优化存储完成: {data_id} ({processing_time:.3f}s)")
            return True

        except Exception as e:
            logger.error(f"❌ 优化存储失败 {data_id}: {e}")
            return False

    async def retrieve_optimized(self, data_id: str) -> Any | None:
        """优化检索"""
        start_time = time.time()

        try:
            # 按层级顺序检索（热→温→冷→归档）

            if hasattr(self, "tier_manager"):
                # 先检查热层
                hot_result = await self.tier_manager.tier_managers[MemoryTier.HOT].retrieve(
                    data_id
                )
                if hot_result:
                    self._update_retrieval_stats(start_time, cache_hit=True)
                    return hot_result.content

                # 检查温层
                warm_result = await self.tier_manager.tier_managers[MemoryTier.WARM].retrieve(
                    data_id
                )
                if warm_result:
                    # 提升到热层
                    await self.tier_manager.tier_managers[MemoryTier.HOT].store(warm_result)
                    self._update_retrieval_stats(start_time, cache_hit=True)
                    return warm_result.content

                # 检查冷层
                cold_result = await self.tier_manager.tier_managers[MemoryTier.COLD].retrieve(
                    data_id
                )
                if cold_result:
                    # 根据访问模式决定是否提升
                    target_tier = self.tier_manager.evaluate_data_placement(cold_result)
                    if target_tier in [MemoryTier.HOT, MemoryTier.WARM]:
                        await self.tier_manager.execute_tier_migration(cold_result, target_tier)
                    self._update_retrieval_stats(start_time, cache_hit=True)
                    return cold_result.content

            # 如果所有层级都没有，使用现有系统
            if self.enhanced_memory_system:
                result = await self._fallback_retrieve(data_id)
                if result is not None:
                    self._update_retrieval_stats(start_time, cache_hit=False)
                    return result

            self._update_retrieval_stats(start_time, cache_hit=False)
            return None

        except Exception as e:
            logger.error(f"❌ 优化检索失败 {data_id}: {e}")
            return None

    async def vector_search_optimized(
        self,
        query_vector: np.ndarray,
        k: int = 10,
        filters: dict[str, Any] | None = None,
    ) -> list[dict[str, Any]]:
        """优化向量搜索"""
        time.time()

        try:
            self.optimization_stats["vector_searches"] += 1

            # 使用优化索引搜索
            if hasattr(self, "vector_index"):
                search_results = await self.vector_index.search(query_vector, k)

                # 转换为详细结果
                detailed_results = []
                for vector_id, distance in search_results:
                    # 检索对应的内存数据
                    content = await self.retrieve_optimized(vector_id)
                    if content is not None:
                        metadata = self.vector_index.index_metadata.get(vector_id, {})
                        detailed_results.append({
                            "data_id": vector_id,
                            "content": content,
                            "similarity": 1.0 / (1.0 + distance),  # 转换为相似度
                            "distance": distance,
                            "metadata": metadata,
                        })

                return detailed_results

            # 回退到现有系统
            if self.enhanced_memory_system:
                return await self._fallback_vector_search(query_vector, k, filters)

            return []

        except Exception as e:
            logger.error(f"❌ 优化向量搜索失败: {e}")
            return []

    async def _fallback_retrieve(self, data_id: str) -> Any | None:
        """回退检索机制"""
        try:
            # 这里实现回退到现有记忆系统的逻辑
            # 简化实现
            return None
        except Exception as e:
            logger.error(f"回退检索失败: {e}")
            return None

    async def _fallback_vector_search(
        self, query_vector: np.ndarray, k: int, filters: dict[str, Any]
    ) -> list[dict[str, Any]]:
        """回退向量搜索机制"""
        try:
            # 这里实现回退到现有记忆系统的向量搜索逻辑
            # 简化实现
            return []
        except Exception as e:
            logger.error(f"回退向量搜索失败: {e}")
            return []

    def _detect_access_pattern(self, data_id: str, content: Any) -> DataAccessPattern:
        """检测访问模式"""
        # 简化的模式检测逻辑
        if isinstance(content, str) and len(content) > 10000:
            return DataAccessPattern.SEQUENTIAL
        elif isinstance(content, list) and len(content) > 100:
            return DataAccessPattern.RANDOM
        else:
            return DataAccessPattern.FREQUENT

    def _calculate_size(self, content: Any) -> int:
        """计算内容大小"""
        try:
            if isinstance(content, str):
                return len(content.encode("utf-8"))
            elif isinstance(content, (list, tuple)):
                return sum(self._calculate_size(item) for item in content)
            elif isinstance(content, dict):
                return sum(self._calculate_size(v) for v in content.values())
            else:
                return len(pickle.dumps(content))
        except Exception:
            return 0

    def _update_storage_stats(self, processing_time: float):
        """更新存储统计"""
        self.optimization_stats["total_stored_items"] += 1

        total_items = self.optimization_stats["total_stored_items"]
        current_avg = self.optimization_stats["average_storage_time"]
        new_avg = (current_avg * (total_items - 1) + processing_time) / total_items
        self.optimization_stats["average_storage_time"] = new_avg

    def _update_retrieval_stats(self, start_time: float, cache_hit: bool):
        """更新检索统计"""
        processing_time = time.time() - start_time

        self.optimization_stats["total_retrieved_items"] += 1

        if cache_hit:
            self.optimization_stats["cache_hits"] += 1
        else:
            self.optimization_stats["cache_misses"] += 1

        total_items = self.optimization_stats["total_retrieved_items"]
        current_avg = self.optimization_stats["average_retrieval_time"]
        new_avg = (current_avg * (total_items - 1) + processing_time) / total_items
        self.optimization_stats["average_retrieval_time"] = new_avg

        # 计算内存效率
        total_retrievals = (
            self.optimization_stats["cache_hits"] + self.optimization_stats["cache_misses"]
        )
        if total_retrievals > 0:
            self.optimization_stats["memory_efficiency"] = (
                self.optimization_stats["cache_hits"] / total_retrievals
            )

    async def _auto_compaction_loop(self):
        """自动压缩循环"""
        logger.info("🔄 启动自动压缩循环")

        while True:
            try:
                # 每小时执行一次压缩
                await asyncio.sleep(3600)

                # 清理过期数据
                await self._cleanup_expired_data()

                # 优化存储布局
                await self._optimize_storage_layout()

                # 重建索引（如果需要）
                if hasattr(self, "vector_index"):
                    await self._rebuild_vector_index_if_needed()

            except Exception as e:
                logger.error(f"自动压缩循环异常: {e}")
                await asyncio.sleep(60)  # 出错后短暂等待

    async def _cleanup_expired_data(self):
        """清理过期数据"""
        # 这里实现过期数据清理逻辑
        pass

    async def _optimize_storage_layout(self):
        """优化存储布局"""
        # 这里实现存储布局优化逻辑
        pass

    async def _rebuild_vector_index_if_needed(self):
        """在需要时重建向量索引"""
        # 检查索引是否需要重建
        if self.vector_index.stats["index_size"] > self.optimization_config.get(
            "index_rebuild_threshold", 10000
        ):
            logger.info("🔧 重建向量索引...")
            self.vector_index.build_index()

    def _generate_optimization_report(self) -> dict[str, Any]:
        """生成优化报告"""
        try:
            report: dict[str, Any] = {
                "optimization_summary": {
                    "total_stored_items": self.optimization_stats["total_stored_items"],
                    "total_retrieved_items": self.optimization_stats["total_retrieved_items"],
                    "average_storage_time": self.optimization_stats["average_storage_time"],
                    "average_retrieval_time": self.optimization_stats["average_retrieval_time"],
                    "memory_efficiency": self.optimization_stats["memory_efficiency"],
                    "vector_searches": self.optimization_stats["vector_searches"],
                },
                "tier_statistics": {},
                "vector_index_stats": {},
                "configuration": self.optimization_config,
            }

            if hasattr(self, "tier_manager"):
                report["tier_statistics"] = self.tier_manager.get_tier_statistics()

            if hasattr(self, "vector_index"):
                report["vector_index_stats"] = self.vector_index.get_stats()

            # 保存报告
            report_path = (
                f"memory_optimization_report_{self.agent_id}_"
                f"{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            )
            with open(report_path, "w", encoding="utf-8") as f:
                json.dump(report, f, indent=2, ensure_ascii=False, default=str)

            logger.info(f"📊 记忆系统优化报告已生成: {report_path}")
            return report

        except Exception as e:
            logger.error(f"生成优化报告失败: {e}")
            return {}

    async def process(self, data: dict[str, Any]) -> dict[str, Any]:
        """标准处理接口"""
        operation = data.get("operation", "store")

        if operation == "store":
            data_id = data.get("data_id", str(uuid.uuid4()))
            content = data.get("content")
            metadata = data.get("metadata")
            vector_embedding = data.get("vector_embedding")

            success = await self.store_optimized(data_id, content, metadata, vector_embedding)
            return {"success": success, "data_id": data_id}

        elif operation == "retrieve":
            data_id = data.get("data_id")
            result = await self.retrieve_optimized(data_id)
            return {"success": result is not None, "data_id": data_id, "content": result}

        elif operation == "vector_search":
            query_vector = data.get("query_vector")
            k = data.get("k", 10)
            filters = data.get("filters")

            if query_vector is not None:
                results = await self.vector_search_optimized(query_vector, k, filters)
                return {"success": True, "results": results, "count": len(results)}

        # 其他操作的默认处理
        return await super().process(data)

    def get_optimization_stats(self) -> dict[str, Any]:
        """获取优化统计信息"""
        stats: dict[str, Any] = {
            "module_stats": self.optimization_stats,
            "configuration": self.optimization_config,
        }

        if hasattr(self, "tier_manager"):
            stats["tier_statistics"] = self.tier_manager.get_tier_statistics()

        if hasattr(self, "vector_index"):
            stats["vector_index_stats"] = self.vector_index.get_stats()

        return stats
