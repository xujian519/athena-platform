#!/usr/bin/env python3
from __future__ import annotations
"""
Athena工作平台业务指标
Business Metrics for Athena Platform

定义所有业务相关的Prometheus指标

Created by Athena AI系统
Date: 2025-12-14
Version: 1.0.0
"""


from shared.observability.metrics.prometheus_exporter import (
    PrometheusCounter,
    PrometheusGauge,
    PrometheusHistogram,
)

# =============================================================================
# 业务指标注册表
# =============================================================================

class BusinessMetrics:
    """
    业务指标注册表

    集中管理所有业务相关的Prometheus指标

    使用示例：
        metrics = BusinessMetrics()

        # 专利分析指标
        metrics.patent_analysis_started(labels={"type": "novelty"})
        metrics.patent_analysis_duration.labels(type="novelty").observe(5.2)
    """

    def __init__(self):
        """初始化所有业务指标"""

        # =====================================================================
        # 专利执行指标
        # =====================================================================

        # 专利分析总数
        self.patent_analysis_total = PrometheusCounter(
            "patent_analysis_total",
            "Total patent analysis operations",
            labelnames=("type", "status")  # type: novelty|inventiveness|comprehensive, status: started|completed|failed
        )

        # 专利分析延迟
        self.patent_analysis_duration_seconds = PrometheusHistogram(
            "patent_analysis_duration_seconds",
            "Patent analysis duration in seconds",
            labelnames=("type",),
            buckets=(1.0, 2.0, 5.0, 10.0, 30.0, 60.0, 120.0, 300.0)
        )

        # 专利分析成本（元）
        self.patent_analysis_cost_yuan = PrometheusGauge(
            "patent_analysis_cost_yuan",
            "Patent analysis cost in yuan"
        )

        # 专利分析成功率
        self.patent_analysis_success_rate = PrometheusGauge(
            "patent_analysis_success_rate",
            "Patent analysis success rate (0-1)"
        )

        # =====================================================================
        # LLM调用指标
        # =====================================================================

        # LLM请求总数
        self.llm_requests_total = PrometheusCounter(
            "llm_requests_total",
            "Total LLM requests",
            labelnames=("model", "operation", "status")  # model: glm-4-plus|deepseek-chat, operation: analysis|generation, status: success|failure
        )

        # LLM响应延迟
        self.llm_response_time_seconds = PrometheusHistogram(
            "llm_response_time_seconds",
            "LLM response time in seconds",
            labelnames=("model",),
            buckets=(0.5, 1.0, 2.0, 5.0, 10.0, 20.0, 30.0)
        )

        # LLM Token使用量
        self.llm_tokens_total = PrometheusCounter(
            "llm_tokens_total",
            "Total LLM tokens consumed",
            labelnames=("model", "token_type")  # token_type: input|output
        )

        # LLM成本（元）
        self.llm_cost_yuan = PrometheusGauge(
            "llm_cost_yuan",
            "LLM cost in yuan",
            labelnames=("model",)
        )

        # =====================================================================
        # 缓存指标
        # =====================================================================

        # 缓存命中总数
        self.cache_hits_total = PrometheusCounter(
            "cache_hits_total",
            "Total cache hits",
            labelnames=("cache", "operation")  # cache: redis|memory, operation: get|set
        )

        # 缓存未命中总数
        self.cache_misses_total = PrometheusCounter(
            "cache_misses_total",
            "Total cache misses",
            labelnames=("cache", "operation")
        )

        # 缓存命中率
        self.cache_hit_rate = PrometheusGauge(
            "cache_hit_rate",
            "Cache hit rate (0-1)",
            labelnames=("cache",)
        )

        # 缓存延迟
        self.cache_operation_duration_seconds = PrometheusHistogram(
            "cache_operation_duration_seconds",
            "Cache operation duration in seconds",
            labelnames=("cache", "operation"),
            buckets=(0.001, 0.005, 0.01, 0.05, 0.1, 0.5, 1.0)
        )

        # =====================================================================
        # 数据库指标
        # =====================================================================

        # 数据库查询总数
        self.db_queries_total = PrometheusCounter(
            "db_queries_total",
            "Total database queries",
            labelnames=("database", "operation", "status")  # database: postgresql|redis, operation: select|insert|update|delete, status: success|failure
        )

        # 数据库连接池大小
        self.db_connections_active = PrometheusGauge(
            "db_connections_active",
            "Active database connections",
            labelnames=("database",)
        )

        # 数据库查询延迟
        self.db_query_duration_seconds = PrometheusHistogram(
            "db_query_duration_seconds",
            "Database query duration in seconds",
            labelnames=("database", "operation"),
            buckets=(0.001, 0.005, 0.01, 0.05, 0.1, 0.5, 1.0, 2.0)
        )

        # =====================================================================
        # 爬虫指标
        # =====================================================================

        # 爬虫请求总数
        self.crawler_requests_total = PrometheusCounter(
            "crawler_requests_total",
            "Total crawler requests",
            labelnames=("source", "status")  # source: pqai|google_patents, status: success|failure|blocked
        )

        # 爬虫延迟
        self.crawler_duration_seconds = PrometheusHistogram(
            "crawler_duration_seconds",
            "Crawler request duration in seconds",
            labelnames=("source",),
            buckets=(1.0, 2.0, 5.0, 10.0, 20.0, 30.0, 60.0)
        )

        # 爬虫队列大小
        self.crawler_queue_size = PrometheusGauge(
            "crawler_queue_size",
            "Crawler queue size",
            labelnames=("source",)
        )

        # =====================================================================
        # 并发和性能指标
        # =====================================================================

        # 并发任务数
        self.concurrent_tasks = PrometheusGauge(
            "concurrent_tasks",
            "Number of concurrent tasks",
            labelnames=("task_type",)
        )

        # 任务队列大小
        self.task_queue_size = PrometheusGauge(
            "task_queue_size",
            "Task queue size",
            labelnames=("queue_name",)
        )

        # 系统吞吐量（每秒请求数）
        self.system_throughput = PrometheusGauge(
            "system_throughput",
            "System throughput (requests per second)"
        )

        # =====================================================================
        # 可靠性指标
        # =====================================================================

        # 重试次数
        self.retry_total = PrometheusCounter(
            "retry_total",
            "Total retry attempts",
            labelnames=("operation", "status")  # status: success|failure|exhausted
        )

        # 熔断器状态
        self.circuit_breaker_state = PrometheusGauge(
            "circuit_breaker_state",
            "Circuit breaker state (0=closed, 1=open, 2=half_open)",
            labelnames=("breaker_name",)
        )

        # 熔断器触发次数
        self.circuit_breaker_trips_total = PrometheusCounter(
            "circuit_breaker_trips_total",
            "Total circuit breaker trips",
            labelnames=("breaker_name",)
        )

        # 死信队列大小
        self.dead_letter_queue_size = PrometheusGauge(
            "dead_letter_queue_size",
            "Dead letter queue size",
            labelnames=("queue_name",)
        )

        # =====================================================================
        # 资源使用指标
        # =====================================================================

        # 内存使用量（字节）
        self.memory_usage_bytes = PrometheusGauge(
            "memory_usage_bytes",
            "Memory usage in bytes",
            labelnames=("type",)  # type: rss|vms|heap
        )

        # 对象池大小
        self.object_pool_size = PrometheusGauge(
            "object_pool_size",
            "Object pool size",
            labelnames=("pool_type",)  # pool_type: dict|list|bytearray
        )

        # 对象池利用率
        self.object_pool_utilization = PrometheusGauge(
            "object_pool_utilization",
            "Object pool utilization (0-1)",
            labelnames=("pool_type",)
        )

        # =====================================================================
        # 业务价值指标
        # =====================================================================

        # 日处理专利数
        self.daily_patents_processed = PrometheusGauge(
            "daily_patents_processed",
            "Number of patents processed today"
        )

        # 累计处理专利数
        self.total_patents_processed = PrometheusCounter(
            "total_patents_processed",
            "Total patents processed since start"
        )

        # 用户满意度评分
        self.user_satisfaction_score = PrometheusGauge(
            "user_satisfaction_score",
            "User satisfaction score (0-100)"
        )

        # 人工审核率
        def human_review_rate(self):
            """人工审核率 (0-1)"""
            return PrometheusGauge(
                "human_review_rate",
                "Human review rate (0-1)"
            )


# =============================================================================
# 单例实例
# =============================================================================

_global_business_metrics: BusinessMetrics | None = None


def get_business_metrics() -> BusinessMetrics:
    """
    获取业务指标实例（单例）

    Returns:
        BusinessMetrics实例
    """
    global _global_business_metrics

    if _global_business_metrics is None:
        _global_business_metrics = BusinessMetrics()

    return _global_business_metrics


# =============================================================================
# 辅助函数
# =============================================================================

def update_analysis_metrics(metrics: BusinessMetrics,
                           analysis_type: str,
                           duration: float,
                           success: bool,
                           cost: float = 0.0):
    """
    更新专利分析指标

    Args:
        metrics: 业务指标实例
        analysis_type: 分析类型 (novelty|inventiveness|comprehensive)
        duration: 分析耗时（秒）
        success: 是否成功
        cost: 分析成本（元）
    """
    # 记录分析总数
    status = "completed" if success else "failed"
    metrics.patent_analysis_total.labels(type=analysis_type, status=status).inc()

    # 记录延迟
    if success:
        metrics.patent_analysis_duration_seconds.labels(type=analysis_type).observe(duration)

    # 记录成本
    if cost > 0:
        metrics.patent_analysis_cost_yuan.set(cost)


def update_llm_metrics(metrics: BusinessMetrics,
                      model: str,
                      operation: str,
                      duration: float,
                      success: bool,
                      input_tokens: int = 0,
                      output_tokens: int = 0,
                      cost: float = 0.0):
    """
    更新LLM调用指标

    Args:
        metrics: 业务指标实例
        model: 模型名称
        operation: 操作类型
        duration: 响应时间（秒）
        success: 是否成功
        input_tokens: 输入token数
        output_tokens: 输出token数
        cost: 成本（元）
    """
    # 记录请求数
    status = "success" if success else "failure"
    metrics.llm_requests_total.labels(model=model, operation=operation, status=status).inc()

    # 记录延迟
    if success:
        metrics.llm_response_time_seconds.labels(model=model).observe(duration)

    # 记录token使用
    if input_tokens > 0:
        metrics.llm_tokens_total.labels(model=model, token_type="input").inc(input_tokens)
    if output_tokens > 0:
        metrics.llm_tokens_total.labels(model=model, token_type="output").inc(output_tokens)

    # 记录成本
    if cost > 0:
        metrics.llm_cost_yuan.labels(model=model).set(cost)


def update_cache_metrics(metrics: BusinessMetrics,
                        cache_type: str,
                        operation: str,
                        hit: bool,
                        duration: float):
    """
    更新缓存指标

    Args:
        metrics: 业务指标实例
        cache_type: 缓存类型 (redis|memory)
        operation: 操作类型 (get|set)
        hit: 是否命中
        duration: 操作耗时（秒）
    """
    if hit:
        metrics.cache_hits_total.labels(cache=cache_type, operation=operation).inc()
    else:
        metrics.cache_misses_total.labels(cache=cache_type, operation=operation).inc()

    # 记录延迟
    metrics.cache_operation_duration_seconds.labels(cache=cache_type, operation=operation).observe(duration)


# =============================================================================
# 测试代码
# =============================================================================

async def test_business_metrics():
    """测试业务指标"""
    from shared.observability.metrics.prometheus_exporter import generate_metrics

    # 获取业务指标
    metrics = get_business_metrics()

    # 测试专利分析指标
    update_analysis_metrics(metrics, "novelty", duration=5.2, success=True, cost=9.05)
    update_analysis_metrics(metrics, "inventiveness", duration=3.8, success=True, cost=7.50)
    update_analysis_metrics(metrics, "comprehensive", duration=12.5, success=False, cost=0.0)

    # 测试LLM指标
    update_llm_metrics(metrics, "glm-4-plus", "analysis", duration=2.3, success=True,
                       input_tokens=1500, output_tokens=800, cost=0.12)
    update_llm_metrics(metrics, "deepseek-chat", "generation", duration=1.8, success=True,
                       input_tokens=1000, output_tokens=500, cost=0.05)

    # 测试缓存指标
    update_cache_metrics(metrics, "redis", "get", hit=True, duration=0.002)
    update_cache_metrics(metrics, "redis", "get", hit=False, duration=0.005)
    update_cache_metrics(metrics, "memory", "get", hit=True, duration=0.0001)

    # 生成指标
    metrics_data = generate_metrics()
    print("\n" + "="*60)
    print("业务指标:")
    print("="*60)
    print(metrics_data.decode('utf-8'))
    print("="*60)


if __name__ == '__main__':
    import asyncio
    import logging

    logging.basicConfig(level=logging.INFO)
    asyncio.run(test_business_metrics())
