#!/usr/bin/env python3
from __future__ import annotations

"""
动态提示词Prometheus监控指标
Dynamic Prompt Performance Metrics for Prometheus

监控动态提示词系统的性能和效果

指标:
- 生成次数
- 生成耗时
- 置信度分布
- 缓存命中率
- 数据源使用频率

作者: 小诺·双鱼公主
创建时间: 2026-01-26
版本: v0.1.0
"""

import time
from typing import Any

from prometheus_client import Counter, Gauge, Histogram

from core.logging_config import setup_logging

logger = setup_logging()


class DynamicPromptMetrics:
    """
    动态提示词性能指标收集器

    监控指标:
    1. 生成指标：次数、耗时
    2. 质量指标：置信度、数据源数量
    3. 缓存指标：命中率、未命中次数
    4. 数据源指标：各数据源使用频率
    """

    def __init__(self):
        """初始化指标收集器"""
        self._setup_metrics()

        # 统计数据
        self.cache_hits = 0
        self.cache_misses = 0

    def _setup_metrics(self):
        """设置Prometheus指标"""

        # ===== 生成指标 =====

        # 动态提示词生成总次数
        self.prompt_generation_total = Counter(
            "dynamic_prompt_generation_total",
            "动态提示词生成总次数",
            ["success"],  # success: "true" or "false"
        )

        # 动态提示词生成耗时（直方图）
        self.prompt_generation_duration = Histogram(
            "dynamic_prompt_generation_duration_seconds",
            "动态提示词生成耗时（秒）",
            buckets=[0.001, 0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0],
        )

        # ===== 质量指标 =====

        # 动态提示词置信度（仪表盘）
        self.prompt_confidence = Gauge(
            "dynamic_prompt_confidence",
            "动态提示词置信度",
            ["oa_id"],  # 按审查意见ID分组
        )

        # 置信度分布（直方图）
        self.prompt_confidence_distribution = Histogram(
            "dynamic_prompt_confidence_distribution",
            "动态提示词置信度分布",
            buckets=[0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0],
        )

        # 数据源数量（直方图）
        self.prompt_sources_count = Histogram(
            "dynamic_prompt_sources_count",
            "动态提示词使用的数据源数量",
            buckets=[1, 2, 3, 4, 5, 6, 7, 8, 9, 10],
        )

        # 各维度提示词生成状态
        self.prompt_dimension_generated = Counter(
            "dynamic_prompt_dimension_generated_total",
            "各维度提示词生成总次数",
            ["dimension", "has_content"],  # dimension: system_prompt, context_prompt等; has_content: "true" or "false"
        )

        # ===== 缓存指标 =====

        # 缓存命中率（仪表盘）
        self.prompt_cache_hit_rate = Gauge(
            "dynamic_prompt_cache_hit_rate",
            "动态提示词缓存命中率（0-1）",
        )

        # 缓存命中次数
        self.prompt_cache_hits_total = Counter(
            "dynamic_prompt_cache_hits_total",
            "动态提示词缓存命中总次数",
        )

        # 缓存未命中次数
        self.prompt_cache_misses_total = Counter(
            "dynamic_prompt_cache_misses_total",
            "动态提示词缓存未命中总次数",
        )

        # ===== 数据源指标 =====

        # 各数据源使用频率
        self.prompt_data_source_usage = Counter(
            "dynamic_prompt_data_source_usage_total",
            "各数据源使用总次数",
            ["source_type"],  # patent_rules, ai_terminology, knowledge_graph等
        )

        # 数据源返回项数（直方图）
        self.prompt_data_source_items = Histogram(
            "dynamic_prompt_data_source_items",
            "数据源返回的项数",
            ["source_type"],
            buckets=[1, 5, 10, 20, 50, 100, 200, 500, 1000],
        )

        # ===== 业务指标 =====

        # 按驳回类型统计生成次数
        self.prompt_generation_by_rejection = Counter(
            "dynamic_prompt_generation_by_rejection_total",
            "按驳回类型统计的生成次数",
            ["rejection_type"],  # novelty, inventiveness, utility等
        )

        # 按技术领域统计生成次数
        self.prompt_generation_by_field = Counter(
            "dynamic_prompt_generation_by_field_total",
            "按技术领域统计的生成次数",
            ["tech_field"],  # 计算机视觉, 自然语言处理等
        )

        # 提示词效果评估分数
        self.prompt_effectiveness_score = Gauge(
            "dynamic_prompt_effectiveness_score",
            "提示词效果评估分数（0-1）",
            ["plan_id"],
        )

        logger.info("✅ 动态提示词Prometheus指标初始化完成")

    # ===== 记录方法 =====

    def record_generation(
        self,
        success: bool,
        duration: float,
        oa_id: str,
        rejection_type: str,
        tech_field: str,
        confidence: float,
        sources: list[dict[str, Any],    ):
        """
        记录动态提示词生成

        Args:
            success: 是否成功生成
            duration: 生成耗时（秒）
            oa_id: 审查意见ID
            rejection_type: 驳回类型
            tech_field: 技术领域
            confidence: 置信度分数
            sources: 数据源列表
        """
        # 记录生成次数
        self.prompt_generation_total.labels(success=str(success).lower()).inc()

        # 记录耗时
        if success:
            self.prompt_generation_duration.observe(duration)

        # 记录置信度
        self.prompt_confidence.labels(oa_id=oa_id).set(confidence)
        self.prompt_confidence_distribution.observe(confidence)

        # 记录数据源数量
        self.prompt_sources_count.observe(len(sources))

        # 记录驳回类型
        self.prompt_generation_by_rejection.labels(rejection_type=rejection_type).inc()

        # 记录技术领域
        self.prompt_generation_by_field.labels(tech_field=tech_field).inc()

        # 记录数据源使用情况
        for source in sources:
            source_type = source.get("type", "unknown")
            count = source.get("count", 0)

            self.prompt_data_source_usage.labels(source_type=source_type).inc()
            self.prompt_data_source_items.labels(source_type=source_type).observe(count)

    def record_cache_hit(self):
        """记录缓存命中"""
        self.cache_hits += 1
        self.prompt_cache_hits_total.inc()
        self._update_cache_hit_rate()

    def record_cache_miss(self):
        """记录缓存未命中"""
        self.cache_misses += 1
        self.prompt_cache_misses_total.inc()
        self._update_cache_hit_rate()

    def _update_cache_hit_rate(self):
        """更新缓存命中率"""
        total = self.cache_hits + self.cache_misses
        if total > 0:
            hit_rate = self.cache_hits / total
            self.prompt_cache_hit_rate.set(hit_rate)

    def record_prompt_dimensions(self, dynamic_prompt_data: dict[str, Any]):
        """
        记录各维度提示词生成情况

        Args:
            dynamic_prompt_data: 动态提示词数据
        """
        dimensions = [
            "system_prompt",
            "context_prompt",
            "patent_rules_prompt",
            "technical_terms_prompt",
            "knowledge_prompt",
            "sqlite_knowledge_prompt",
            "action_prompt",
            "search_strategy_prompt",
        ]

        for dimension in dimensions:
            has_content = dimension in dynamic_prompt_data and bool(
                dynamic_prompt_data.get(dimension)
            )
            self.prompt_dimension_generated.labels(
                dimension=dimension, has_content=str(has_content).lower()
            ).inc()

    def record_effectiveness(self, plan_id: str, effectiveness_score: float):
        """
        记录提示词效果评估分数

        Args:
            plan_id: 方案ID
            effectiveness_score: 效果分数（0-1）
        """
        self.prompt_effectiveness_score.labels(plan_id=plan_id).set(
            effectiveness_score
        )

    def get_metrics_summary(self) -> dict[str, Any]:
        """
        获取指标摘要

        Returns:
            指标摘要字典
        """
        total_requests = self.cache_hits + self.cache_misses
        hit_rate = self.cache_hits / total_requests if total_requests > 0 else 0.0

        return {
            "cache_statistics": {
                "hits": self.cache_hits,
                "misses": self.cache_misses,
                "total_requests": total_requests,
                "hit_rate": hit_rate,
            },
            "generation_total": int(
                self.prompt_generation_total.labels(success="true")._value.get()
            )
            + int(self.prompt_generation_total.labels(success="false")._value.get()),
        }


# ===== 上下文管理器用于计时 =====

class PromptGenerationTimer:
    """提示词生成计时器上下文管理器"""

    def __init__(self, metrics: DynamicPromptMetrics):
        """
        初始化计时器

        Args:
            metrics: 指标收集器
        """
        self.metrics = metrics
        self.start_time = None
        self.duration = None

    def __enter__(self):
        """开始计时"""
        self.start_time = time.time()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """结束计时"""
        if self.start_time is not None:
            self.duration = time.time() - self.start_time


# ===== 全局单例 =====

_metrics_instance: DynamicPromptMetrics | None = None


def get_dynamic_prompt_metrics() -> DynamicPromptMetrics:
    """获取动态提示词指标收集器单例"""
    global _metrics_instance
    if _metrics_instance is None:
        _metrics_instance = DynamicPromptMetrics()
    return _metrics_instance
