#!/usr/bin/env python3
from __future__ import annotations
"""
认知与决策模块监控指标导出器
Metrics Exporter for Cognitive & Decision Module

将认知与决策模块的关键指标导出到Prometheus

作者: Athena Platform Team
版本: v1.0
"""

import logging
import time
from collections.abc import Callable
from datetime import datetime
from functools import wraps

from prometheus_client import Counter, Gauge, Histogram, Info, start_http_server
from prometheus_client.core import CollectorRegistry

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ============== 认知模块指标 ==============

# 认知处理延迟
cognitive_processing_duration = Histogram(
    'cognitive_processing_duration_seconds',
    'Cognitive processing duration in seconds',
    ['mode', 'query_type'],
    buckets=[0.1, 0.5, 1.0, 2.0, 5.0, 10.0, 30.0, 60.0]
)

# 认知请求总数
cognitive_requests_total = Counter(
    'cognitive_requests_total',
    'Total cognitive requests',
    ['mode', 'status']
)

# 认知错误总数
cognitive_errors_total = Counter(
    'cognitive_errors_total',
    'Total cognitive errors',
    ['mode', 'error_type']
)

# 认知置信度分布
cognitive_confidence = Gauge(
    'cognitive_confidence',
    'Cognitive result confidence score',
    ['mode']
)

# ============== 决策模块指标 ==============

# 决策处理延迟
decision_processing_duration = Histogram(
    'decision_processing_duration_seconds',
    'Decision processing duration in seconds',
    ['decision_type', 'priority'],
    buckets=[0.1, 0.5, 1.0, 2.0, 5.0, 10.0]
)

# 决策请求总数
decision_requests_total = Counter(
    'decision_requests_total',
    'Total decision requests',
    ['decision_type', 'status']
)

# 决策错误总数
decision_errors_total = Counter(
    'decision_errors_total',
    'Total decision errors',
    ['decision_type', 'error_type']
)

# 决策队列长度
decision_queue_length = Gauge(
    'decision_queue_length',
    'Current decision queue length',
    ['priority']
)

# ============== 超级推理引擎指标 ==============

# 超级推理延迟
super_reasoning_duration = Histogram(
    'super_reasoning_duration_seconds',
    'Super reasoning engine duration',
    ['reasoning_mode', 'depth_level'],
    buckets=[1.0, 5.0, 10.0, 30.0, 60.0, 120.0, 300.0]
)

# 超级推理内存使用
super_reasoning_memory = Gauge(
    'super_reasoning_memory_bytes',
    'Super reasoning engine memory usage in bytes',
    ['reasoning_mode']
)

# 超级推理步骤数
super_reasoning_steps_total = Counter(
    'super_reasoning_steps_total',
    'Total super reasoning steps executed',
    ['reasoning_mode', 'step_type']
)

# ============== 意图识别指标 ==============

# 意图识别请求
intent_classification_total = Counter(
    'intent_classification_total',
    'Total intent classification requests',
    ['intent_detected']
)

# 意图识别失败
intent_classification_failures = Counter(
    'intent_classification_failures_total',
    'Total intent classification failures',
    ['error_type']
)

# 意图识别置信度
intent_confidence = Gauge(
    'intent_confidence_score',
    'Intent classification confidence score',
    ['intent_type']
)

# ============== LLM集成指标 ==============

# LLM请求延迟
llm_request_duration = Histogram(
    'llm_request_duration_seconds',
    'LLM API request duration',
    ['model', 'operation'],
    buckets=[0.5, 1.0, 2.0, 5.0, 10.0, 30.0, 60.0]
)

# LLM请求总数
llm_requests_total = Counter(
    'llm_requests_total',
    'Total LLM requests',
    ['model', 'status']
)

# LLM请求失败
llm_request_errors = Counter(
    'llm_request_errors_total',
    'Total LLM request errors',
    ['model', 'error_type']
)

# Token使用量
llm_tokens_total = Counter(
    'llm_tokens_total',
    'Total LLM tokens used',
    ['model', 'token_type']
)

# ============== Agent协作指标 ==============

# Agent任务总数
agent_tasks_total = Counter(
    'agent_tasks_total',
    'Total agent tasks',
    ['agent_type', 'status']
)

# Agent任务失败
agent_task_failures = Counter(
    'agent_task_failures_total',
    'Total agent task failures',
    ['agent_type', 'failure_reason']
)

# Agent超时
agent_timeouts = Counter(
    'agent_timeouts_total',
    'Total agent timeouts',
    ['agent_type']
)

# Agent任务队列
agent_task_queue = Gauge(
    'agent_task_queue_length',
    'Current agent task queue length',
    ['agent_type', 'priority']
)

# ============== 记忆系统指标 ==============

# 记忆缓存命中
memory_cache_hits = Counter(
    'memory_cache_hits_total',
    'Total memory cache hits',
    ['memory_type', 'cache_level']
)

# 记忆缓存未命中
memory_cache_misses = Counter(
    'memory_cache_misses_total',
    'Total memory cache misses',
    ['memory_type', 'cache_level']
)

# 向量搜索延迟
vector_search_duration = Histogram(
    'vector_search_duration_seconds',
    'Vector search duration',
    ['index_type', 'search_method'],
    buckets=[0.01, 0.05, 0.1, 0.5, 1.0, 2.0, 5.0]
)

# ============== 质量门禁指标 ==============

# 技术债务计数
technical_debt_count = Gauge(
    'technical_debt_count',
    'Current technical debt items',
    ['severity', 'category']
)

# 代码覆盖率
code_coverage = Gauge(
    'code_coverage_percent',
    'Code coverage percentage',
    ['module']
)

# 语法错误计数
syntax_error_count = Gauge(
    'syntax_error_count',
    'Current syntax errors',
    ['module']
)

# 模块信息
module_info = Info(
    'cognitive_decision_module',
    'Cognitive and Decision module information'
)


def track_cognitive(mode: str = 'basic'):
    """装饰器：追踪认知处理指标"""
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            start_time = time.time()
            query_type = kwargs.get('query_type', 'unknown')

            try:
                result = await func(*args, **kwargs)

                # 记录成功指标
                duration = time.time() - start_time
                cognitive_processing_duration.labels(
                    mode=mode,
                    query_type=query_type
                ).observe(duration)
                cognitive_requests_total.labels(
                    mode=mode,
                    status='success'
                ).inc()

                # 记录置信度
                if 'confidence' in result:
                    cognitive_confidence.labels(mode=mode).set(result['confidence'])

                return result

            except Exception as e:
                # 记录错误指标
                cognitive_errors_total.labels(
                    mode=mode,
                    error_type=type(e).__name__
                ).inc()
                cognitive_requests_total.labels(
                    mode=mode,
                    status='error'
                ).inc()
                raise

        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            start_time = time.time()
            query_type = kwargs.get('query_type', 'unknown')

            try:
                result = func(*args, **kwargs)

                # 记录成功指标
                duration = time.time() - start_time
                cognitive_processing_duration.labels(
                    mode=mode,
                    query_type=query_type
                ).observe(duration)
                cognitive_requests_total.labels(
                    mode=mode,
                    status='success'
                ).inc()

                return result

            except Exception as e:
                # 记录错误指标
                cognitive_errors_total.labels(
                    mode=mode,
                    error_type=type(e).__name__
                ).inc()
                cognitive_requests_total.labels(
                    mode=mode,
                    status='error'
                ).inc()
                raise

        # 根据函数类型返回对应的包装器
        import asyncio
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        return sync_wrapper

    return decorator


def track_decision(decision_type: str = 'general', priority: str = 'normal'):
    """装饰器：追踪决策处理指标"""
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            start_time = time.time()

            try:
                result = await func(*args, **kwargs)

                duration = time.time() - start_time
                decision_processing_duration.labels(
                    decision_type=decision_type,
                    priority=priority
                ).observe(duration)
                decision_requests_total.labels(
                    decision_type=decision_type,
                    status='success'
                ).inc()

                return result

            except Exception as e:
                decision_errors_total.labels(
                    decision_type=decision_type,
                    error_type=type(e).__name__
                ).inc()
                decision_requests_total.labels(
                    decision_type=decision_type,
                    status='error'
                ).inc()
                raise

        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            start_time = time.time()

            try:
                result = func(*args, **kwargs)

                duration = time.time() - start_time
                decision_processing_duration.labels(
                    decision_type=decision_type,
                    priority=priority
                ).observe(duration)
                decision_requests_total.labels(
                    decision_type=decision_type,
                    status='success'
                ).inc()

                return result

            except Exception as e:
                decision_errors_total.labels(
                    decision_type=decision_type,
                    error_type=type(e).__name__
                ).inc()
                raise

        import asyncio
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        return sync_wrapper

    return decorator


def track_llm_call(model: str, operation: str = 'completion'):
    """装饰器：追踪LLM调用指标"""
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            start_time = time.time()

            try:
                result = await func(*args, **kwargs)

                duration = time.time() - start_time
                llm_request_duration.labels(model=model, operation=operation).observe(duration)
                llm_requests_total.labels(model=model, status='success').inc()

                # 记录token使用（如果结果中包含）
                if isinstance(result, dict):
                    if 'prompt_tokens' in result:
                        llm_tokens_total.labels(model=model, token_type='prompt').inc(result['prompt_tokens'])
                    if 'completion_tokens' in result:
                        llm_tokens_total.labels(model=model, token_type='completion').inc(result['completion_tokens'])

                return result

            except Exception as e:
                llm_request_errors.labels(model=model, error_type=type(e).__name__).inc()
                llm_requests_total.labels(model=model, status='error').inc()
                raise

        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            start_time = time.time()

            try:
                result = func(*args, **kwargs)

                duration = time.time() - start_time
                llm_request_duration.labels(model=model, operation=operation).observe(duration)
                llm_requests_total.labels(model=model, status='success').inc()

                return result

            except Exception as e:
                llm_request_errors.labels(model=model, error_type=type(e).__name__).inc()
                llm_requests_total.labels(model=model, status='error').inc()
                raise

        import asyncio
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        return sync_wrapper

    return decorator


class CognitiveMetricsCollector:
    """认知与决策模块指标收集器"""

    def __init__(self, port: int = 9100):
        self.port = port
        self.registry = CollectorRegistry()

    def start(self):
        """启动指标导出服务器"""
        start_http_server(self.port)
        logger.info(f"📊 认知决策模块指标导出器已启动，端口: {self.port}")

        # 设置模块信息
        module_info.info({
            'version': '1.0.0',
            'build_date': datetime.now().isoformat(),
            'python_version': '3.14+',
            'description': 'Athena Cognitive & Decision Module'
        })

    def update_quality_gates(self, tech_debt: dict[str, int], coverage: dict[str, float], syntax_errors: dict[str, int]):
        """更新质量门禁指标"""
        # 技术债务
        for severity, count in tech_debt.items():
            technical_debt_count.labels(severity=severity, category='all').set(count)

        # 代码覆盖率
        for module, cov in coverage.items():
            code_coverage.labels(module=module).set(cov)

        # 语法错误
        for module, count in syntax_errors.items():
            syntax_error_count.labels(module=module).set(count)

    def record_super_reasoning(self, mode: str, depth: int, duration: float, memory_bytes: int, steps: int):
        """记录超级推理指标"""
        super_reasoning_duration.labels(reasoning_mode=mode, depth_level=str(depth)).observe(duration)
        super_reasoning_memory.labels(reasoning_mode=mode).set(memory_bytes)
        super_reasoning_steps_total.labels(reasoning_mode=mode, step_type='total').inc(steps)

    def record_intent_classification(self, intent: str, confidence: float, success: bool):
        """记录意图识别指标"""
        intent_classification_total.labels(intent_detected=intent).inc()
        intent_confidence.labels(intent_type=intent).set(confidence)
        if not success:
            intent_classification_failures.labels(error_type='classification_failed').inc()

    def record_memory_cache(self, memory_type: str, cache_level: str, hit: bool):
        """记录记忆缓存指标"""
        if hit:
            memory_cache_hits.labels(memory_type=memory_type, cache_level=cache_level).inc()
        else:
            memory_cache_misses.labels(memory_type=memory_type, cache_level=cache_level).inc()

    def record_vector_search(self, index_type: str, method: str, duration: float):
        """记录向量搜索指标"""
        vector_search_duration.labels(index_type=index_type, search_method=method).observe(duration)


# 全局指标收集器实例
metrics_collector = CognitiveMetricsCollector()


# 便捷函数
def start_metrics_exporter(port: int = 9100):
    """启动指标导出器"""
    global metrics_collector
    metrics_collector = CognitiveMetricsCollector(port)
    metrics_collector.start()
    return metrics_collector


def update_quality_metrics(tech_debt: dict[str, int], coverage: dict[str, float], syntax_errors: dict[str, int]):
    """更新质量指标"""
    metrics_collector.update_quality_gates(tech_debt, coverage, syntax_errors)


if __name__ == "__main__":
    # 启动指标导出器（用于测试）
    collector = start_metrics_exporter(9100)

    # 模拟一些指标
    import asyncio

    async def simulate_metrics():
        while True:
            # 更新质量门禁
            update_quality_metrics(
                tech_debt={'critical': 5, 'high': 15, 'medium': 30},
                coverage={'cognition': 85.5, 'decision': 78.2},
                syntax_errors={'cognition': 2, 'decision': 0}
            )

            # 记录超级推理
            collector.record_super_reasoning('super', 5, 45.2, 1024*1024*100, 15)

            # 记录意图识别
            collector.record_intent_classification('patent_analysis', 0.92, True)

            # 记录记忆缓存
            collector.record_memory_cache('episodic', 'l1', True)

            # 记录向量搜索
            collector.record_vector_search('qdrant', 'hnsw', 0.15)

            await asyncio.sleep(5)

    logger.info("📊 指标导出器运行中，访问 http://localhost:9100 查看指标")
    asyncio.run(simulate_metrics())
