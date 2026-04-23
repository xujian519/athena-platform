
"""
法律提示词融合核心指标结构。

定义 FusionMetrics 数据类，用于在融合链路中收集和传递观测数据，
支持字典与 JSON 序列化，便于接入 ELK / Loki / Prometheus 等观测系统。
"""


import json
import logging
from dataclasses import asdict, dataclass, field
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class FusionMetrics:
    """单次融合请求的完整指标快照。

    字段覆盖延迟、证据分布、缓存命中、来源降级、错误等维度，
    可直接通过 to_json() 输出为结构化日志。
    """

    request_id: str
    domain: str
    task_type: str
    fusion_enabled: bool = False
    latency_ms: float = 0.0
    evidence_count: int = 0
    evidence_by_source: dict[str, int] = field(default_factory=dict)
    cache_hit: bool = False
    wiki_revision: str = "unknown"
    template_version: str = ""
    source_degradation: list[str] = field(default_factory=list)
    error: str | None = None
    # B5-PerfObs 新增维度
    token_count_input: int = 0
    token_count_output: int = 0
    evidence_relevance_score: float = 0.0
    budget_usage: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        """转换为普通字典，None 值保留为 null。"""
        return asdict(self)

    def to_json(self) -> str:
        """序列化为 JSON 字符串（确保中文不转义）。"""
        return json.dumps(self.to_dict(), ensure_ascii=False, separators=(",", ":"))


async def _send_metrics_async(metrics: FusionMetrics) -> None:
    """异步发送融合指标。失败不阻断主链路，仅记录 warning 日志。"""
    try:
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

            # B5-PerfObs 新增指标
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
                metrics.budget_usage,
                labels,
            )
        except Exception:
            # Prometheus 指标发送失败不影响主链路
            pass

    except Exception as exc:
        logger.warning("融合指标发送失败（非阻断）: %s", exc)
