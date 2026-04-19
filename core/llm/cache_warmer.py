from __future__ import annotations
"""
统一LLM层 - 缓存预热器
在系统启动时预加载常用数据,提升首次请求性能

作者: Claude Code
日期: 2026-01-23
"""

import logging
from datetime import datetime

from core.llm.model_registry import ModelCapabilityRegistry
from core.llm.response_cache import ResponseCache

logger = logging.getLogger(__name__)


class CacheWarmer:
    """
    缓存预热器

    功能:
    1. 预加载模型能力定义
    2. 预加载常用提示词
    3. 预热响应缓存(可选)
    """

    def __init__(
        self, registry: ModelCapabilityRegistry, response_cache: ResponseCache, enabled: bool = True
    ):
        """
        初始化缓存预热器

        Args:
            registry: 模型能力注册表
            response_cache: 响应缓存
            enabled: 是否启用预热
        """
        self.registry = registry
        self.response_cache = response_cache
        self.enabled = enabled

        # 预热配置
        self.warmup_queries = [
            # 简单查询,用于触发缓存初始化
            ("你好", "simple_chat"),
            ("test", "simple_qa"),
        ]

        # 需要预热的任务类型
        self.warmup_task_types = {"simple_chat", "simple_qa", "general_chat"}

        logger.info(f"✅ 缓存预热器初始化完成 (启用: {enabled})")

    async def warmup(
        self, warmup_models: bool = True, warmup_cache: bool = False
    ) -> dict[str, any]:
        """
        执行缓存预热

        Args:
            warmup_models: 是否预热模型加载
            warmup_cache: 是否预热响应缓存

        Returns:
            Dict: 预热结果统计
        """
        if not self.enabled:
            logger.info("⏭️ 缓存预热已禁用,跳过")
            return {"enabled": False, "timestamp": datetime.now().isoformat()}

        start_time = datetime.now()
        logger.info("🔥 开始缓存预热...")

        results = {
            "enabled": True,
            "start_time": start_time.isoformat(),
            "models_warmed": 0,
            "cache_entries_warmed": 0,
            "warmup_duration_ms": 0,
            "errors": [],
        }

        # 1. 预热模型能力注册表
        if warmup_models:
            try:
                model_results = await self._warmup_models()
                results["models_warmed"] = model_results["count"]
                results["model_list"] = model_results["models"]
            except Exception as e:
                logger.error(f"❌ 模型预热失败: {e}", exc_info=True)
                results["errors"].append(f"模型预热失败: {e}")

        # 2. 预热响应缓存(可选)
        if warmup_cache:
            try:
                cache_results = await self._warmup_cache()
                results["cache_entries_warmed"] = cache_results["count"]
            except Exception as e:
                logger.error(f"❌ 缓存预热失败: {e}", exc_info=True)
                results["errors"].append(f"缓存预热失败: {e}")

        # 计算预热耗时
        end_time = datetime.now()
        results["warmup_duration_ms"] = (end_time - start_time).total_seconds() * 1000
        results["end_time"] = end_time.isoformat()

        logger.info(
            f"✅ 缓存预热完成 "
            f"(模型: {results['models_warmed']}, "
            f"缓存: {results['cache_entries_warmed']}, "
            f"耗时: {results['warmup_duration_ms']:.1f}ms)"
        )

        return results

    async def _warmup_models(self) -> dict[str, any]:
        """
        预热模型能力定义

        Returns:
            Dict: 预热结果
        """
        logger.info("🔥 预热模型能力定义...")

        models = self.registry.list_all_models()
        warmed_models = []

        for model_id in models:
            try:
                # 获取模型能力定义(触发缓存)
                capability = self.registry.get_capability(model_id)
                if capability:
                    warmed_models.append(
                        {
                            "model_id": model_id,
                            "model_type": capability.model_type.value,
                            "deployment": capability.deployment.value,
                            "quality_score": capability.quality_score,
                        }
                    )
            except Exception as e:
                logger.warning(f"⚠️ 预热模型 {model_id} 失败: {e}")

        logger.info(f"✅ 预热了 {len(warmed_models)} 个模型能力定义")

        return {"count": len(warmed_models), "models": warmed_models}

    async def _warmup_cache(self) -> dict[str, any]:
        """
        预热响应缓存

        注意: 这只是为了演示缓存预热功能。
        实际使用时,您可能需要根据业务场景选择合适的预热数据。

        Returns:
            Dict: 预热结果
        """
        logger.info("🔥 预热响应缓存...")

        warmed_count = 0

        # 预热一些简单的查询(模拟)
        # 注意: 这些只是占位符,实际不会调用LLM
        # 实际使用时,您可能需要:
        # 1. 从历史日志中提取常见查询
        # 2. 预加载知识库
        # 3. 预计算常用结果

        for query, task_type in self.warmup_queries:
            try:
                # 这里只是触发缓存初始化,实际不存储内容
                # 因为真实的数据需要LLM调用才能生成
                self.response_cache.get(query, task_type)
                warmed_count += 1
            except Exception as e:
                logger.warning(f"⚠️ 预热缓存查询失败: {e}")

        logger.info(f"✅ 预热了 {warmed_count} 个缓存查询")

        return {"count": warmed_count}

    def configure_warmup_queries(self, queries: list[tuple], task_types: set[str] | None = None) -> None:
        """
        配置预热查询

        Args:
            queries: 预热查询列表 [(message, task_type), ...]
            task_types: 需要预热的任务类型集合
        """
        self.warmup_queries = queries
        if task_types:
            self.warmup_task_types = task_types

        logger.info(f"✅ 配置了 {len(queries)} 个预热查询")

    def get_warmup_config(self) -> dict[str, any]:
        """
        获取当前预热配置

        Returns:
            Dict: 预热配置
        """
        return {
            "enabled": self.enabled,
            "warmup_queries_count": len(self.warmup_queries),
            "warmup_task_types": list(self.warmup_task_types),
            "available_models": len(self.registry.list_all_models()) if self.registry else 0,
        }


# 单例
_cache_warmer: CacheWarmer | None = None


def get_cache_warmer(
    registry: ModelCapabilityRegistry = None,
    response_cache: ResponseCache = None,
    enabled: bool = True,
) -> CacheWarmer:
    """
    获取缓存预热器单例

    Args:
        registry: 模型能力注册表
        response_cache: 响应缓存
        enabled: 是否启用预热

    Returns:
        CacheWarmer: 缓存预热器实例
    """
    global _cache_warmer
    if _cache_warmer is None:
        _cache_warmer = CacheWarmer(
            registry=registry, response_cache=response_cache, enabled=enabled
        )
    return _cache_warmer


def reset_cache_warmer():
    """重置单例(用于测试)"""
    global _cache_warmer
    _cache_warmer = None
