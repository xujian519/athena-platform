#!/usr/bin/env python3
from __future__ import annotations
"""
BGE重排序引擎 - 修复版
BGE Reranker Engine - Fixed Version

完整实现BGE-Reranker模型的加载和重排序功能
作者: Athena AI Team
创建时间: 2026-01-09
版本: v2.0.0 "完整实现"
"""

import asyncio
import logging
import os
import threading
import time
from dataclasses import dataclass
from enum import Enum
from typing import Any

import numpy as np

logger = logging.getLogger(__name__)


class RerankMode(Enum):
    """重排序模式"""

    FULL_RERANK = "full_rerank"  # 全量重排序
    TOP_K_RERANK = "top_k_rerank"  # Top-K重排序
    THRESHOLD_RERANK = "threshold_rerank"  # 阈值重排序
    ADAPTIVE_RERANK = "adaptive_rerank"  # 自适应重排序


@dataclass
class RerankConfig:
    """重排序配置"""

    mode: RerankMode = RerankMode.TOP_K_RERANK
    top_k: int = 100  # 重排序前的Top-K数量(增加)
    final_top_k: int = 10  # 最终返回的Top-K数量(减少)
    threshold: float = 0.2  # 重排序阈值(降低)
    batch_size: int = 16  # 批处理大小(增加)
    use_cache: bool = True  # 是否使用缓存
    cache_ttl: int = 300  # 缓存时间(秒)


@dataclass
class RerankResult:
    """重排序结果"""

    query: str
    items: list[dict[str, Any]]
    scores: list[float]
    reranked_items: list[dict[str, Any]]
    reranked_scores: list[float]
    rerank_time: float
    mode: RerankMode


class BGEReranker:
    """BGE重排序引擎 - 完整实现"""

    def __init__(self, model_path: Optional[str] = None, config: RerankConfig | None = None):
        """
        初始化BGE重排序引擎

        Args:
            model_path: BGE-Reranker模型路径
            config: 重排序配置
        """
        self.config = config or RerankConfig()
        self.name = "BGE重排序引擎"
        self.version = "2.0.0"
        self._initialized = False
        self.logger = logging.getLogger(self.name)

        # 模型路径
        if model_path is None:
            model_path = "/Users/xujian/Athena工作平台/models/converted/bge-reranker-large"

        self.model_path = model_path

        # 重排序模型
        self.model = None
        self.model_lock = threading.Lock()

        # 缓存
        self.cache = {}
        self.cache_stats = {"hits": 0, "misses": 0}

        # 统计信息
        self.stats = {"total_reranks": 0, "total_time": 0.0, "avg_time": 0.0}

        self.logger.info(f"📦 {self.name} v{self.version} 初始化")
        self.logger.info(f"   模型路径: {self.model_path}")

        # 检查模型文件
        if not os.path.exists(model_path):
            self.logger.error(f"❌ 模型文件不存在: {model_path}")
        else:
            self.logger.info(
                f"✅ 模型文件存在,大小: {os.path.getsize(model_path) / 1024 / 1024:.1f} MB"
            )

    def initialize(self) -> bool:
        """
        初始化重排序引擎(同步版本)

        Returns:
            bool: 是否初始化成功
        """
        try:
            with self.model_lock:
                if self._initialized:
                    return True

                self.logger.info("🔄 开始初始化BGE重排序引擎...")

                # 加载模型
                self.model = self._load_rerank_model()

                if self.model is None:
                    self.logger.error("❌ 模型加载失败")
                    return False

                # 测试模型
                test_scores = self.model.predict([["测试查询", "测试文档"]])
                self.logger.info(f"✅ 模型测试通过,测试分数: {test_scores}")

                self._initialized = True
                self.logger.info("✅ BGEReranker 初始化完成")
                return True

        except Exception as e:
            self.logger.error(f"❌ BGEReranker 初始化失败: {e}")
            import traceback

            self.logger.error(traceback.format_exc())
            return False

    def _load_rerank_model(self) -> Any:
        """加载BGE-Reranker模型"""
        try:
            from sentence_transformers import CrossEncoder

            self.logger.info(f"📦 加载BGE-Reranker模型: {self.model_path}")

            # 加载CrossEncoder模型
            model = CrossEncoder(self.model_path, device="mps")  # 使用MPS加速

            self.logger.info("✅ BGE-Reranker模型加载完成")
            return model

        except Exception as e:
            self.logger.error(f"❌ 模型加载失败: {e}")
            return None

    async def initialize_async(self) -> bool:
        """异步初始化"""
        # 在线程池中执行同步初始化
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self.initialize)

    def rerank(
        self, query: str, items: list[dict[str, Any]], config: RerankConfig | None = None
    ) -> RerankResult:
        """
        重排序项目列表(同步版本)

        Args:
            query: 查询文本
            items: 待重排序的项目列表
            config: 重排序配置

        Returns:
            RerankResult: 重排序结果
        """
        start_time = time.time()

        # 使用提供的配置或默认配置
        rerank_config = config or self.config

        if not self._initialized:
            # 尝试自动初始化
            if not self.initialize():
                self.logger.error("❌ 重排序引擎未初始化")
                return self._create_empty_result(query, items, start_time)

        try:
            # 1. 提取内容和原始分数
            contents = [
                item.get("content", item.get("description", item.get("title", "")))
                for item in items
            ]
            original_scores = [item.get("score", 0.0) for item in items]

            self.logger.debug(f"🔄 开始重排序: {len(items)}个项目")
            self.logger.debug(f"   查询: {query[:50]}...")
            self.logger.debug(f"   模式: {rerank_config.mode.value}")

            # 2. 检查缓存
            if rerank_config.use_cache:
                cache_key = self._generate_cache_key(query, contents)
                cached_result = self._get_from_cache(cache_key)
                if cached_result is not None:
                    self.cache_stats["hits"] += 1
                    return self._create_cached_result(query, items, cached_result, start_time)
                else:
                    self.cache_stats["misses"] += 1

            # 3. 根据模式选择重排序策略
            if rerank_config.mode == RerankMode.FULL_RERANK:
                reranked_items, reranked_scores = self._full_rerank(query, items, contents)
            elif rerank_config.mode == RerankMode.TOP_K_RERANK:
                reranked_items, reranked_scores = self._top_k_rerank(
                    query, items, contents, rerank_config
                )
            elif rerank_config.mode == RerankMode.THRESHOLD_RERANK:
                reranked_items, reranked_scores = self._threshold_rerank(
                    query, items, contents, rerank_config
                )
            else:  # ADAPTIVE_RERANK
                reranked_items, reranked_scores = self._adaptive_rerank(
                    query, items, contents, rerank_config
                )

            # 4. 缓存结果
            if rerank_config.use_cache:
                cache_key = self._generate_cache_key(query, contents)
                self._save_to_cache(cache_key, reranked_scores)

            end_time = time.time()
            rerank_time = end_time - start_time

            # 5. 创建结果
            result = RerankResult(
                query=query,
                items=items,
                scores=original_scores,
                reranked_items=reranked_items,
                reranked_scores=reranked_scores,
                rerank_time=rerank_time,
                mode=rerank_config.mode,
            )

            # 更新统计
            self.stats["total_reranks"] += 1
            self.stats["total_time"] += rerank_time
            self.stats["avg_time"] = self.stats["total_time"] / self.stats["total_reranks"]

            self.logger.info(
                f"✅ 重排序完成: {len(items)} -> {len(reranked_items)} 项 ({rerank_time:.3f}s)"
            )
            self.logger.debug(f'   原始Top-3分数: {[f"{s:.3f}" for s in original_scores[:3]]}')
            self.logger.debug(f'   重排Top-3分数: {[f"{s:.3f}" for s in reranked_scores[:3]]}')

            return result

        except Exception as e:
            self.logger.error(f"❌ 重排序失败: {e}")
            import traceback

            self.logger.error(traceback.format_exc())
            return self._create_empty_result(query, items, start_time)

    def _full_rerank(
        self, query: str, items: list[dict[str, Any]], contents: list[str]
    ) -> tuple[list[dict[str, Any]], list[float]]:
        """全量重排序"""
        self.logger.debug("🔄 执行全量重排序")

        # 批量计算重排序分数
        scores = self._batch_rerank_scores(query, contents)

        # 按分数排序
        scored_items = list(zip(items, scores, strict=False))
        scored_items.sort(key=lambda x: x[1], reverse=True)

        # 分离结果
        reranked_items = [item for item, _ in scored_items]
        reranked_scores = [score for _, score in scored_items]

        return reranked_items, reranked_scores

    def _top_k_rerank(
        self, query: str, items: list[dict[str, Any]], contents: list[str], config: RerankConfig
    ) -> tuple[list[dict[str, Any]], list[float]]:
        """Top-K重排序(推荐)"""
        self.logger.debug(
            f"🔄 执行Top-K重排序: top_k={config.top_k}, final_top_k={config.final_top_k}"
        )

        # 批量计算重排序分数
        scores = self._batch_rerank_scores(query, contents)

        # 更新分数
        for i, item in enumerate(items):
            item["rerank_score"] = float(scores[i])

        # 按新分数排序
        scored_items = list(zip(items, scores, strict=False))
        scored_items.sort(key=lambda x: x[1], reverse=True)

        # 返回Top-K
        top_k_items = scored_items[: config.final_top_k]
        reranked_items = [item for item, _ in top_k_items]
        reranked_scores = [score for _, score in top_k_items]

        return reranked_items, reranked_scores

    def _threshold_rerank(
        self, query: str, items: list[dict[str, Any]], contents: list[str], config: RerankConfig
    ) -> tuple[list[dict[str, Any]], list[float]]:
        """阈值重排序"""
        self.logger.debug(f"🔄 执行阈值重排序: threshold={config.threshold}")

        # 批量计算重排序分数
        scores = self._batch_rerank_scores(query, contents)

        # 过滤低于阈值的结果
        filtered_items = [
            (item, score) for item, score in zip(items, scores, strict=False) if score >= config.threshold
        ]

        if not filtered_items:
            self.logger.warning(f"⚠️ 所有结果都低于阈值 {config.threshold},返回原始结果")
            return items, scores

        # 排序
        filtered_items.sort(key=lambda x: x[1], reverse=True)

        reranked_items = [item for item, _ in filtered_items]
        reranked_scores = [score for _, score in filtered_items]

        return reranked_items, reranked_scores

    def _adaptive_rerank(
        self, query: str, items: list[dict[str, Any]], contents: list[str], config: RerankConfig
    ) -> tuple[list[dict[str, Any]], list[float]]:
        """自适应重排序"""
        self.logger.debug("🔄 执行自适应重排序")

        # 分析查询复杂度
        query_length = len(query)
        content_diversity = len(set(" ".join(contents).split()))

        # 根据复杂度选择策略
        if query_length < 20 and content_diversity < 10:
            # 简单查询:使用Top-K
            return self._top_k_rerank(query, items, contents, config)
        elif query_length > 50 or content_diversity > 20:
            # 复杂查询:使用全量重排序
            return self._full_rerank(query, items, contents)
        else:
            # 中等查询:使用阈值重排序
            return self._threshold_rerank(query, items, contents, config)

    def _batch_rerank_scores(self, query: str, contents: list[str]) -> list[float]:
        """批量计算重排序分数"""
        try:
            # 准备查询-文档对
            pairs = [[query, content] for content in contents]

            self.logger.debug(f"   计算 {len(pairs)} 个查询-文档对的分数...")

            # 批量预测
            scores = self.model.predict(pairs, convert_to_numpy=True, show_progress_bar=False)

            # 归一化分数到0-1范围
            scores = self._normalize_scores(scores)

            self.logger.debug(f"   分数范围: {np.min(scores):.3f} - {np.max(scores):.3f}")

            return scores.tolist()

        except Exception as e:
            self.logger.error(f"❌ 重排序分数计算失败: {e}")
            # 返回原始分数
            return [0.0] * len(contents)

    def _normalize_scores(self, scores: np.ndarray) -> np.ndarray:
        """归一化分数到0-1范围"""
        if len(scores) == 0:
            return scores

        min_score = np.min(scores)
        max_score = np.max(scores)

        if max_score == min_score:
            # 所有分数相同
            return np.ones_like(scores) * 0.5

        # Min-Max归一化
        normalized = (scores - min_score) / (max_score - min_score)
        return normalized

    def _generate_cache_key(self, query: str, contents: list[str]) -> str:
        """生成缓存键"""
        import hashlib

        key_data = f"{query}|{'|'.join(contents[:5])}"  # 只使用前5个内容生成键
        return hashlib.md5(key_data.encode('utf-8'), usedforsecurity=False).hexdigest()

    def _get_from_cache(self, cache_key: str) -> Optional[list[float]]:
        """从缓存获取"""
        return self.cache.get(cache_key)

    def _save_to_cache(self, cache_key: str, scores: list[float]) -> Any:
        """保存到缓存"""
        self.cache[cache_key] = scores

        # 清理过期缓存(简单实现)
        if len(self.cache) > 1000:
            self.cache.clear()

    def _create_empty_result(
        self, query: str, items: list[dict[str, Any]], start_time: float
    ) -> RerankResult:
        """创建空结果"""
        return RerankResult(
            query=query,
            items=items,
            scores=[item.get("score", 0.0) for item in items],
            reranked_items=items,
            reranked_scores=[item.get("score", 0.0) for item in items],
            rerank_time=time.time() - start_time,
            mode=self.config.mode,
        )

    def _create_cached_result(
        self, query: str, items: list[dict[str, Any]], cached_scores: list[float], start_time: float
    ) -> RerankResult:
        """创建缓存结果"""
        # 根据缓存分数排序
        scored_items = list(zip(items, cached_scores, strict=False))
        scored_items.sort(key=lambda x: x[1], reverse=True)

        reranked_items = [item for item, _ in scored_items]
        reranked_scores = [score for _, score in scored_items]

        return RerankResult(
            query=query,
            items=items,
            scores=[item.get("score", 0.0) for item in items],
            reranked_items=reranked_items,
            reranked_scores=reranked_scores,
            rerank_time=time.time() - start_time,
            mode=self.config.mode,
        )

    def get_stats(self) -> dict:
        """获取统计信息"""
        cache_hit_rate = (
            self.cache_stats["hits"] / (self.cache_stats["hits"] + self.cache_stats["misses"])
            if (self.cache_stats["hits"] + self.cache_stats["misses"]) > 0
            else 0
        )

        return {
            "initialized": self._initialized,
            "total_reranks": self.stats["total_reranks"],
            "avg_time": self.stats["avg_time"],
            "cache_hit_rate": cache_hit_rate,
            "cache_stats": self.cache_stats,
        }

    def clear_cache(self) -> None:
        """清理缓存"""
        self.cache.clear()
        self.cache_stats = {"hits": 0, "misses": 0}
        self.logger.info("✅ 缓存已清理")


# 全局单例
_reranker_instance: BGEReranker | None = None
_reranker_lock = threading.Lock()


def get_bge_reranker(
    model_path: Optional[str] = None,
    config: RerankConfig | None = None,
    auto_initialize: bool = True,
) -> BGEReranker:
    """
    获取BGE重排序引擎单例

    Args:
        model_path: 模型路径
        config: 配置
        auto_initialize: 是否自动初始化

    Returns:
        BGEReranker: 重排序引擎实例
    """
    global _reranker_instance

    with _reranker_lock:
        if _reranker_instance is None:
            _reranker_instance = BGEReranker(model_path, config)

            # 自动初始化
            if auto_initialize:
                _reranker_instance.initialize()

        return _reranker_instance


# 示例使用
if __name__ == "__main__":
    print("=" * 80)
    print("🧪 BGE重排序引擎测试")
    print("=" * 80)
    print()

    # 获取Reranker实例
    reranker = get_bge_reranker()

    # 测试数据
    query = "专利侵权"
    items = [
        {"id": "1", "content": "专利侵权是指侵犯专利权的行为", "score": 0.8},
        {"id": "2", "content": "商标注册流程", "score": 0.6},
        {"id": "3", "content": "著作权保护", "score": 0.7},
        {"id": "4", "content": "专利权的保护期", "score": 0.5},
    ]

    print(f"查询: {query}")
    print(f"项目数: {len(items)}")
    print()

    # 执行重排序
    print("执行重排序...")
    result = reranker.rerank(query, items)

    print()
    print("原始排序:")
    for i, (item, score) in enumerate(zip(result.items, result.scores, strict=False), 1):
        print(f"  {i}. [{item['id']}] {item['content'][:40]}... (分数: {score:.3f})")

    print()
    print("重排序后:")
    for i, (item, score) in enumerate(zip(result.reranked_items, result.reranked_scores, strict=False), 1):
        print(f"  {i}. [{item['id']}] {item['content'][:40]}... (分数: {score:.3f})")

    print()
    print(f"重排序耗时: {result.rerank_time:.3f}秒")
    print(f"缓存命中率: {reranker.get_stats()['cache_hit_rate']:.1%}")

    print()
    print("=" * 80)
