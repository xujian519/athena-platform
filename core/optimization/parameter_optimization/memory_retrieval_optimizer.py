#!/usr/bin/env python3
from __future__ import annotations
"""
记忆检索参数优化器
Memory Retrieval Parameter Optimizer

优化记忆系统的检索参数:
- vector_top_k (向量检索Top-K)
- vector_threshold (向量相似度阈值)
- kg_top_k (知识图谱Top-K)
- kg_depth (知识图谱深度)
- 混合检索权重 (vector_weight, kg_weight, keyword_weight)

借鉴Heretic的多目标优化思路:
- 优化目标: 召回率 + 精确度 + 延迟

作者: Athena平台团队
创建时间: 2025-01-04
"""

import logging
from typing import Any

from .base_optimizer import BaseParameterOptimizer, OptimizationConfig
from .evaluation_metrics import EvaluationMetrics

logger = logging.getLogger(__name__)


class MemoryRetrievalOptimizer(BaseParameterOptimizer):
    """
    记忆检索参数优化器

    应用场景:
    1. 优化记忆系统的检索参数
    2. 平衡召回率、精确度和性能
    3. 针对不同查询类型的优化

    示例:
    ```python
    optimizer = MemoryRetrievalOptimizer(
        name="memory_retrieval",
        eval_dataset=eval_queries
    )
    result = await optimizer.optimize(n_trials=50)
    ```
    """

    def __init__(
        self,
        name: str = "memory_retrieval_optimization",
        config: OptimizationConfig | None = None,
        eval_dataset: list[dict] | None = None,
        memory_system: Any | None = None,
    ):
        """
        初始化记忆检索优化器

        Args:
            name: 优化器名称
            config: 优化配置
            eval_dataset: 评估数据集
                格式: [{
                    'query': '查询文本',
                    'relevant_ids': ['id1', 'id2', ...],
                    'category': '查询类型(可选)'
                }]
            memory_system: 可选的记忆系统实例
        """
        super().__init__(name, config, eval_dataset)
        self.memory_system = memory_system
        self.evaluator = EvaluationMetrics()

        logger.info(f"🧠 初始化记忆检索优化器: {name}")

    def define_search_space(self, trial) -> dict[str, Any]:
        """
        定义记忆检索参数搜索空间

        借鉴Heretic的权重曲线思想:
        - Heretic: 层间消融权重曲线
        - 我们: 检索模态间的权重分配
        """
        params = {
            # 向量检索参数
            "vector_top_k": trial.suggest_int("vector_top_k", 5, 50),
            "vector_threshold": trial.suggest_float("vector_threshold", 0.5, 0.99),
            # 知识图谱检索参数
            "kg_top_k": trial.suggest_int("kg_top_k", 3, 20),
            "kg_depth": trial.suggest_int("kg_depth", 1, 5),
            # 混合检索权重(类似Heretic的层间权重)
            "vector_weight": trial.suggest_float("vector_weight", 0.0, 1.0),
            "kg_weight": trial.suggest_float("kg_weight", 0.0, 1.0),
            "keyword_weight": trial.suggest_float("keyword_weight", 0.0, 1.0),
            # 性能相关
            "cache_enabled": trial.suggest_categorical("cache_enabled", [True, False]),
            "parallel_search": trial.suggest_categorical("parallel_search", [True, False]),
        }

        return params

    async def evaluate(self, params: dict[str, Any]) -> float:
        """
        评估记忆检索参数配置

        多目标优化(类似Heretic):
        - Heretic: minimize(拒绝率, KL散度)
        - 我们: maximize(召回率, 精确度), minimize(延迟)

        Args:
            params: 检索参数

        Returns:
            综合评分(0-1)
        """
        if not self.eval_dataset:
            logger.warning("没有评估数据集,返回默认分数")
            return 0.5

        metrics_list = []

        for example in self.eval_dataset:
            # 执行检索
            retrieved = await self._retrieve(example["query"], params)

            # 计算检索指标
            retrieved_ids = [item.get("id", "") for item in retrieved]
            relevant_ids = example.get("relevant_ids", [])

            metrics = self.evaluator.compute_retrieval_metrics(
                retrieved_ids=retrieved_ids, relevant_ids=relevant_ids
            )

            metrics_list.append(metrics)

        # 计算平均指标
        avg_metrics = {}
        for key in metrics_list[0]:
            avg_metrics[key] = sum(m[key] for m in metrics_list) / len(metrics_list)

        # 多目标综合评分
        # 权重: Recall@5 (40%) + MAP (30%) + MRR (20%) + 效率 (10%)
        score = (
            avg_metrics.get("recall@5", 0) * 0.40
            + avg_metrics.get("map", 0) * 0.30
            + avg_metrics.get("mrr", 0) * 0.20
            + self._compute_efficiency_score(params) * 0.10
        )

        return score

    async def _retrieve(self, query: str, params: dict[str, Any]) -> list[dict[str, Any]]:
        """
        执行检索

        如果有memory_system则使用,否则模拟
        """
        if self.memory_system:
            return await self._retrieve_with_system(query, params)
        else:
            return self._simulate_retrieval(query, params)

    async def _retrieve_with_system(
        self, query: str, params: dict[str, Any]
    ) -> list[dict[str, Any]]:
        """使用实际记忆系统检索"""
        try:
            # 调用记忆系统的search方法
            results = await self.memory_system.search(
                query,
                top_k=params["vector_top_k"],
                threshold=params["vector_threshold"],
                # ... 其他参数
            )
            return results
        except Exception as e:
            logger.error(f"记忆系统检索失败: {e}")
            return []

    def _simulate_retrieval(self, query: str, params: dict[str, Any]) -> list[dict[str, Any]]:
        """
        模拟检索(用于测试)

        根据参数模拟检索结果质量
        """
        vector_top_k = params["vector_top_k"]
        vector_threshold = params["vector_threshold"]

        # 模拟: 较小的top_k和较高的阈值通常返回更少但更相关的结果
        num_results = int(vector_top_k * vector_threshold)

        # 模拟返回结果
        results = []
        for i in range(num_results):
            results.append(
                {
                    "id": f"doc_{i}",
                    "score": vector_threshold - (i * 0.01),
                    "content": f"模拟检索结果 {i}",
                }
            )

        return results

    def _compute_efficiency_score(self, params: dict[str, Any]) -> float:
        """
        计算效率分数

        基于参数估计检索效率
        """
        score = 1.0

        # 较小的top_k更快
        vector_top_k = params["vector_top_k"]
        score *= (50 / max(vector_top_k, 1)) ** 0.3

        # 缓存提升效率
        if params.get("cache_enabled", True):
            score *= 1.2

        # 并行搜索提升效率
        if params.get("parallel_search"):
            score *= 1.1

        # 较浅的KG深度更快
        kg_depth = params.get("kg_depth", 3)
        score *= (3 / max(kg_depth, 1)) ** 0.2

        return min(score, 1.0)

    async def optimize_for_query_type(self, query_type: str, n_trials: int = 50) -> dict[str, Any]:
        """
        针对特定查询类型优化

        查询类型:
        - 'factual': 事实查询(需要精确匹配)
        - 'semantic': 语义查询(需要理解意图)
        - 'relational': 关系查询(需要KG推理)
        - 'mixed': 混合查询(需要综合检索)

        Args:
            query_type: 查询类型
            n_trials: 优化试验次数

        Returns:
            优化结果
        """
        # 过滤数据集
        filtered_dataset = [
            ex for ex in self.eval_dataset if ex.get("category") == query_type
        ] or self.eval_dataset

        # 临时替换数据集
        original_dataset = self.eval_dataset
        self.eval_dataset = filtered_dataset

        try:
            # 执行优化
            result = await self.optimize(n_trials=n_trials)
            result.metadata["query_type"] = query_type

            return result
        finally:
            # 恢复原始数据集
            self.eval_dataset = original_dataset

    def get_recommended_params(self, query_type: str = "mixed") -> dict[str, Any]:
        """
        获取推荐的检索参数

        基于经验或历史优化结果
        """
        recommended = {
            "factual": {
                "vector_top_k": 10,
                "vector_threshold": 0.85,
                "kg_top_k": 5,
                "kg_depth": 2,
                "vector_weight": 0.7,
                "kg_weight": 0.2,
                "keyword_weight": 0.1,
                "cache_enabled": True,
                "parallel_search": False,
            },
            "semantic": {
                "vector_top_k": 20,
                "vector_threshold": 0.75,
                "kg_top_k": 8,
                "kg_depth": 3,
                "vector_weight": 0.6,
                "kg_weight": 0.3,
                "keyword_weight": 0.1,
                "cache_enabled": True,
                "parallel_search": True,
            },
            "relational": {
                "vector_top_k": 15,
                "vector_threshold": 0.70,
                "kg_top_k": 15,
                "kg_depth": 4,
                "vector_weight": 0.3,
                "kg_weight": 0.6,
                "keyword_weight": 0.1,
                "cache_enabled": True,
                "parallel_search": True,
            },
            "mixed": {
                "vector_top_k": 20,
                "vector_threshold": 0.78,
                "kg_top_k": 10,
                "kg_depth": 3,
                "vector_weight": 0.5,
                "kg_weight": 0.3,
                "keyword_weight": 0.2,
                "cache_enabled": True,
                "parallel_search": True,
            },
        }

        return recommended.get(query_type, recommended["mixed"])
