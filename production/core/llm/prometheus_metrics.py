from __future__ import annotations
"""
统一LLM层 - Prometheus监控指标导出
提供标准化的metrics导出接口,支持Prometheus监控

作者: Claude Code
日期: 2026-01-23
"""

import logging
import time

from prometheus_client import (
    CONTENT_TYPE_LATEST,
    Gauge,
    Histogram,
    Info,
    generate_latest,
)
from prometheus_client import (
    Counter as PromCounter,
)

logger = logging.getLogger(__name__)


class LLMetrics:
    """
    LLM统一监控指标

    功能:
    1. 请求计数
    2. 延迟分布
    3. 成本追踪
    4. 模型使用统计
    5. 缓存命中率
    """

    def __init__(self, enabled: bool = True):
        """
        初始化监控指标

        Args:
            enabled: 是否启用metrics收集
        """
        self.enabled = enabled

        if not enabled:
            logger.info("⏭️ Prometheus metrics已禁用")
            return

        # 请求计数器
        self.request_total = PromCounter(
            "llm_requests_total",
            "LLM请求总数",
            ["model_id", "task_type", "status"],  # status: success, failure, cached
        )

        # 延迟分布
        self.request_duration = Histogram(
            "llm_request_duration_seconds",
            "LLM请求耗时",
            ["model_id", "task_type"],
            buckets=(0.1, 0.5, 1.0, 2.0, 5.0, 10.0, 30.0, 60.0, 120.0),
        )

        # Token计数器
        self.tokens_total = PromCounter(
            "llm_tokens_total",
            "LLM Token使用总数",
            ["model_id", "task_type", "token_type"],  # token_type: prompt, completion
        )

        # 成本追踪
        self.cost_total = PromCounter("llm_cost_yuan", "LLM总成本(元)", ["model_id", "task_type"])

        # 模型健康状态
        self.model_health = Gauge(
            "llm_model_health", "模型健康状态(1=健康,0=不健康)", ["model_id"]
        )

        # 模型质量评分
        self.model_quality_score = Gauge("llm_model_quality_score", "模型质量评分", ["model_id"])

        # 缓存统计
        self.cache_hits = PromCounter("llm_cache_hits_total", "缓存命中总数", ["task_type"])

        self.cache_misses = PromCounter("llm_cache_misses_total", "缓存未命中总数", ["task_type"])

        # 预算使用率
        self.budget_utilization = Gauge(
            "llm_budget_utilization",
            "预算使用率(0-1)",
            ["budget_type"],  # budget_type: daily, alert_threshold
        )

        # 系统信息
        self.llm_info = Info("llm_build_info", "LLM系统构建信息")
        self.llm_info.info(
            {"version": "1.0.0", "author": "Claude Code", "description": "Athena统一LLM层"}
        )

        logger.info("✅ Prometheus metrics已启用")

    def record_request(
        self,
        model_id: str,
        task_type: str,
        status: str,
        duration: float,
        tokens: int = 0,
        cost: float = 0.0,
        cached: bool = False,
    ) -> None:
        """
        记录请求指标

        Args:
            model_id: 模型ID
            task_type: 任务类型
            status: 请求状态 (success, failure, cached)
            duration: 请求耗时(秒)
            tokens: 使用token数
            cost: 成本(元)
            cached: 是否来自缓存
        """
        if not self.enabled:
            return

        try:
            # 记录请求计数
            cache_label = "cached" if cached else status
            self.request_total.labels(
                model_id=model_id, task_type=task_type, status=cache_label
            ).inc()

            # 记录延迟
            self.request_duration.labels(model_id=model_id, task_type=task_type).observe(duration)

            # 记录token使用
            if tokens > 0:
                self.tokens_total.labels(
                    model_id=model_id, task_type=task_type, token_type="total"
                ).inc(tokens)

            # 记录成本
            if cost > 0:
                self.cost_total.labels(model_id=model_id, task_type=task_type).inc(cost)

        except Exception as e:
            logger.warning(f"⚠️ 记录metrics失败: {e}")

    def record_cache_hit(self, task_type: str) -> None:
        """
        记录缓存命中

        Args:
            task_type: 任务类型
        """
        if not self.enabled:
            return

        try:
            self.cache_hits.labels(task_type=task_type).inc()
        except Exception as e:
            logger.warning(f"⚠️ 记录缓存命中失败: {e}")

    def record_cache_miss(self, task_type: str) -> None:
        """
        记录缓存未命中

        Args:
            task_type: 任务类型
        """
        if not self.enabled:
            return

        try:
            self.cache_misses.labels(task_type=task_type).inc()
        except Exception as e:
            logger.warning(f"⚠️ 记录缓存未命中失败: {e}")

    def update_model_health(self, model_id: str, healthy: bool) -> None:
        """
        更新模型健康状态

        Args:
            model_id: 模型ID
            healthy: 是否健康
        """
        if not self.enabled:
            return

        try:
            self.model_health.labels(model_id=model_id).set(1 if healthy else 0)
        except Exception as e:
            logger.warning(f"⚠️ 更新模型健康状态失败: {e}")

    def update_model_quality(self, model_id: str, score: float) -> None:
        """
        更新模型质量评分

        Args:
            model_id: 模型ID
            score: 质量评分 (0-1)
        """
        if not self.enabled:
            return

        try:
            self.model_quality_score.labels(model_id=model_id).set(score)
        except Exception as e:
            logger.warning(f"⚠️ 更新模型质量评分失败: {e}")

    def update_budget_utilization(
        self, daily_utilization: float, threshold_utilization: float
    ) -> None:
        """
        更新预算使用率

        Args:
            daily_utilization: 日预算使用率 (0-1)
            threshold_utilization: 告警阈值使用率 (0-1)
        """
        if not self.enabled:
            return

        try:
            self.budget_utilization.labels(budget_type="daily").set(daily_utilization)
            self.budget_utilization.labels(budget_type="alert_threshold").set(threshold_utilization)
        except Exception as e:
            logger.warning(f"⚠️ 更新预算使用率失败: {e}")

    def export_metrics(self) -> bytes:
        """
        导出Prometheus格式的metrics

        Returns:
            bytes: Prometheus格式的metrics数据
        """
        if not self.enabled:
            return b""

        try:
            return generate_latest()
        except Exception as e:
            logger.error(f"❌ 导出metrics失败: {e}")
            return b""

    def get_content_type(self) -> str:
        """
        获取metrics的Content-Type

        Returns:
            str: Content-Type header value
        """
        return CONTENT_TYPE_LATEST

    def get_summary(self) -> dict[str, any]:
        """
        获取metrics摘要

        Returns:
            Dict: metrics摘要信息
        """
        return {
            "enabled": self.enabled,
            "metrics_count": 9 if self.enabled else 0,
            "metrics_list": (
                [
                    "llm_requests_total",
                    "llm_request_duration_seconds",
                    "llm_tokens_total",
                    "llm_cost_yuan",
                    "llm_model_health",
                    "llm_model_quality_score",
                    "llm_cache_hits_total",
                    "llm_cache_misses_total",
                    "llm_budget_utilization",
                ]
                if self.enabled
                else []
            ),
        }


# 单例
_metrics_instance: LLMetrics | None = None


def get_metrics(enabled: bool = True) -> LLMetrics:
    """
    获取metrics单例

    Args:
        enabled: 是否启用metrics收集

    Returns:
        LLMetrics: metrics实例
    """
    global _metrics_instance
    if _metrics_instance is None:
        _metrics_instance = LLMetrics(enabled=enabled)
    return _metrics_instance


def reset_metrics():
    """重置单例(用于测试)"""
    global _metrics_instance
    _metrics_instance = None


class MetricsContext:
    """
    Metrics上下文管理器

    用于自动记录请求耗时

    用法:
        async with MetricsContext(model_id, task_type) as ctx:
            # 执行LLM调用
            response = await llm_generate(...)
            ctx.set_success(tokens=100, cost=0.01)
    """

    def __init__(self, metrics: LLMetrics, model_id: str, task_type: str):
        self.metrics = metrics
        self.model_id = model_id
        self.task_type = task_type
        self.start_time = None
        self.tokens = 0
        self.cost = 0.0
        self.cached = False

    def __enter__(self):
        self.start_time = time.time()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        duration = time.time() - self.start_time if self.start_time else 0

        status = "success" if exc_type is None else "failure"
        self.metrics.record_request(
            model_id=self.model_id,
            task_type=self.task_type,
            status=status,
            duration=duration,
            tokens=self.tokens,
            cost=self.cost,
            cached=self.cached,
        )

    async def __aenter__(self):
        self.start_time = time.time()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        duration = time.time() - self.start_time if self.start_time else 0

        status = "success" if exc_type is None else "failure"
        self.metrics.record_request(
            model_id=self.model_id,
            task_type=self.task_type,
            status=status,
            duration=duration,
            tokens=self.tokens,
            cost=self.cost,
            cached=self.cached,
        )

    def set_success(self, tokens: int = 0, cost: float = 0.0) -> None:
        """设置成功结果"""
        self.tokens = tokens
        self.cost = cost

    def set_cached(self) -> None:
        """标记为缓存命中"""
        self.cached = True
