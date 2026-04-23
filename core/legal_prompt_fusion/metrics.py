
"""
法律提示词融合核心指标结构。

定义 FusionMetrics 数据类，用于在融合链路中收集和传递观测数据，
支持字典与 JSON 序列化，便于接入 ELK / Loki / Prometheus 等观测系统。

.. note::
    FusionMetrics 已迁移至 ``metrics_collector.py``，本模块保留向后兼容的
    重新导出与异步发送逻辑。
"""

import logging

logger = logging.getLogger(__name__)

# 从独立模块导入增强版 FusionMetrics
from core.legal_prompt_fusion.metrics_collector import (  # noqa: F401
    FusionMetrics,
    get_prompt_metrics_collector,
)


async def _send_metrics_async(metrics: FusionMetrics) -> None:
    """异步发送融合指标。失败不阻断主链路，仅记录 warning 日志。"""
    try:
        # 0. 写入本地环形缓冲区（C4-Metrics）
        try:
            collector = get_prompt_metrics_collector()
            collector.record(metrics)
        except Exception:
            pass

        # 1. 结构化 JSON 日志输出（接入 ELK / Loki）
        logger.info("fusion_metrics %s", metrics.to_json())

        # 2. 若全局指标收集器可用，也写入 Prometheus 指标
        try:
            from core.monitoring.metrics_collector import get_metrics_collector

            collector = get_metrics_collector()
            labels = {"domain": metrics.domain, "task_type": metrics.task_type}

            collector.inc_counter(
                "fusion_requests_total",
                1.0,
                {**labels, "fusion_enabled": str(metrics.fusion_enabled).lower()},
            )

            if metrics.fusion_enabled:
                collector.observe_histogram(
                    "fusion_latency_seconds",
                    metrics.latency_ms / 1000.0,
                    labels,
                )
                collector.observe_histogram(
                    "fusion_evidence_count",
                    float(metrics.evidence_count),
                    {**labels, "source_type": "total"},
                )
                for source_type, count in (metrics.evidence_by_source or {}).items():
                    collector.observe_histogram(
                        "fusion_evidence_count",
                        float(count),
                        {**labels, "source_type": source_type},
                    )

            if metrics.cache_hit:
                collector.inc_counter("fusion_cache_hits_total", 1.0, {"domain": metrics.domain})

            for degraded_source in metrics.source_degradation:
                collector.inc_counter(
                    "fusion_source_degradations_total",
                    1.0,
                    {"source_type": degraded_source},
                )

            # B5-PerfObs / C4-Metrics 新增指标
            collector.observe_histogram(
                "fusion_token_count",
                float(metrics.token_count_input),
                {**labels, "direction": "input"},
            )
            collector.observe_histogram(
                "fusion_token_count",
                float(metrics.token_count_output),
                {**labels, "direction": "output"},
            )
            collector.observe_histogram(
                "fusion_evidence_relevance_score",
                metrics.evidence_relevance_score,
                labels,
            )
            collector.observe_histogram(
                "fusion_budget_usage_ratio",
                metrics.budget_usage_ratio,
                labels,
            )
        except Exception:
            # Prometheus 指标发送失败不影响主链路
            pass

    except Exception as exc:
        logger.warning("融合指标发送失败（非阻断）: %s", exc)
