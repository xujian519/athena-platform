"""
法律提示词融合指标收集器（C4-Metrics）。

提供增强版 FusionMetrics 数据类与 PromptMetricsCollector 单例，
支持环形缓冲区、P50/P95/P99 分位计算及 Prometheus 纯文本格式导出。
"""

from __future__ import annotations

import json
import threading
from collections import deque
from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass
class FusionMetrics:
    """单次融合请求的完整指标快照（增强版）。

    字段覆盖延迟、证据分布、缓存命中、来源降级、错误、token 估算、
    预算使用率、回滚原因、Schema 校验等维度。
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
    token_count_input: int = 0
    token_count_output: int = 0
    evidence_relevance_score: float = 0.0
    budget_usage_ratio: float = 0.0
    rollback_reason: str | None = None
    schema_validated: bool = False
    # C1-BudgetIntegration: 记录 BudgetMetrics 快照
    budget_metrics: dict[str, Any] | None = None

    def to_dict(self) -> dict[str, Any]:
        """转换为普通字典，None 值保留为 null。"""
        return asdict(self)

    def to_json(self) -> str:
        """序列化为 JSON 字符串（确保中文不转义）。"""
        return json.dumps(self.to_dict(), ensure_ascii=False, separators=(",", ":"))


def _percentile(sorted_data: list[float], p: float) -> float:
    """计算有序数据的百分位值（线性插值）。"""
    if not sorted_data:
        return 0.0
    n = len(sorted_data)
    if n == 1:
        return sorted_data[0]
    k = (n - 1) * p / 100.0
    f = int(k)
    c = min(f + 1, n - 1)
    if f == c:
        return sorted_data[f]
    return sorted_data[f] * (c - k) + sorted_data[c] * (k - f)


class PromptMetricsCollector:
    """Prompt 系统指标收集器（单例）。

    使用环形缓冲区保留最近 1000 条 FusionMetrics，
    并提供 Prometheus 纯文本格式导出（前缀 ``athena_prompt_``）。
    """

    _instance: PromptMetricsCollector | None = None
    _lock = threading.Lock()

    def __new__(cls) -> PromptMetricsCollector:
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    obj = super().__new__(cls)
                    obj._metrics: deque[FusionMetrics] = deque(maxlen=1000)
                    cls._instance = obj
        return cls._instance

    def record(self, metrics: FusionMetrics) -> None:
        """记录一条指标到环形缓冲区。"""
        self._metrics.append(metrics)

    def get_recent_metrics(self, n: int = 1000) -> list[FusionMetrics]:
        """获取最近 n 条指标（默认全部）。"""
        return list(self._metrics)[-n:]

    def get_latency_percentiles(self) -> dict[str, float]:
        """计算已记录延迟的 P50/P95/P99（单位 ms）。"""
        latencies = sorted([m.latency_ms for m in self._metrics if m.latency_ms > 0])
        return {
            "p50": _percentile(latencies, 50),
            "p95": _percentile(latencies, 95),
            "p99": _percentile(latencies, 99),
        }

    def export_prometheus(self) -> str:
        """导出 Prometheus 文本格式（前缀 ``athena_prompt_``）。"""
        lines: list[str] = []
        metrics_list = list(self._metrics)

        # ---- fusion_requests_total ----
        total = len(metrics_list)
        lines.append(
            "# HELP athena_prompt_fusion_requests_total Total number of prompt fusion requests."
        )
        lines.append("# TYPE athena_prompt_fusion_requests_total counter")
        lines.append(f"athena_prompt_fusion_requests_total {total}")

        # ---- cache_hits_total ----
        cache_hits = sum(1 for m in metrics_list if m.cache_hit)
        lines.append("# HELP athena_prompt_cache_hits_total Total number of cache hits.")
        lines.append("# TYPE athena_prompt_cache_hits_total counter")
        lines.append(f"athena_prompt_cache_hits_total {cache_hits}")

        # ---- fusion_latency_ms summary ----
        latencies = [m.latency_ms for m in metrics_list if m.latency_ms > 0]
        if latencies:
            pcts = self.get_latency_percentiles()
            lines.append(
                "# HELP athena_prompt_fusion_latency_ms Fusion latency in milliseconds."
            )
            lines.append("# TYPE athena_prompt_fusion_latency_ms summary")
            for q, v in [("0.5", pcts["p50"]), ("0.95", pcts["p95"]), ("0.99", pcts["p99"])]:
                lines.append(f'athena_prompt_fusion_latency_ms{{quantile="{q}"}} {v:.3f}')
            lines.append(f"athena_prompt_fusion_latency_ms_count {len(latencies)}")
            lines.append(f"athena_prompt_fusion_latency_ms_sum {sum(latencies):.3f}")

        # ---- token counts ----
        total_input = sum(m.token_count_input for m in metrics_list)
        total_output = sum(m.token_count_output for m in metrics_list)
        lines.append("# HELP athena_prompt_token_count_input_total Total input tokens.")
        lines.append("# TYPE athena_prompt_token_count_input_total counter")
        lines.append(f"athena_prompt_token_count_input_total {total_input}")
        lines.append("# HELP athena_prompt_token_count_output_total Total output tokens.")
        lines.append("# TYPE athena_prompt_token_count_output_total counter")
        lines.append(f"athena_prompt_token_count_output_total {total_output}")

        # ---- evidence_relevance_score summary ----
        scores = [m.evidence_relevance_score for m in metrics_list if m.evidence_relevance_score > 0]
        if scores:
            sorted_scores = sorted(scores)
            lines.append(
                "# HELP athena_prompt_evidence_relevance_score Average evidence relevance score."
            )
            lines.append("# TYPE athena_prompt_evidence_relevance_score summary")
            for q, p in [("0.5", 50), ("0.95", 95), ("0.99", 99)]:
                v = _percentile(sorted_scores, p)
                lines.append(f'athena_prompt_evidence_relevance_score{{quantile="{q}"}} {v:.4f}')
            lines.append(f"athena_prompt_evidence_relevance_score_count {len(scores)}")
            lines.append(f"athena_prompt_evidence_relevance_score_sum {sum(scores):.4f}")

        # ---- budget_usage_ratio summary ----
        budgets = [m.budget_usage_ratio for m in metrics_list if m.budget_usage_ratio > 0]
        if budgets:
            sorted_budgets = sorted(budgets)
            lines.append("# HELP athena_prompt_budget_usage_ratio Budget usage ratio.")
            lines.append("# TYPE athena_prompt_budget_usage_ratio summary")
            for q, p in [("0.5", 50), ("0.95", 95), ("0.99", 99)]:
                v = _percentile(sorted_budgets, p)
                lines.append(f'athena_prompt_budget_usage_ratio{{quantile="{q}"}} {v:.4f}')
            lines.append(f"athena_prompt_budget_usage_ratio_count {len(budgets)}")
            lines.append(f"athena_prompt_budget_usage_ratio_sum {sum(budgets):.4f}")

        # ---- schema_validated_total ----
        schema_validated = sum(1 for m in metrics_list if m.schema_validated)
        lines.append(
            "# HELP athena_prompt_schema_validated_total Number of schema-validated requests."
        )
        lines.append("# TYPE athena_prompt_schema_validated_total counter")
        lines.append(f"athena_prompt_schema_validated_total {schema_validated}")

        # ---- rollback_total ----
        rollback_reasons: dict[str, int] = {}
        for m in metrics_list:
            if m.rollback_reason:
                rollback_reasons[m.rollback_reason] = rollback_reasons.get(m.rollback_reason, 0) + 1
        if rollback_reasons:
            lines.append("# HELP athena_prompt_rollback_total Number of rollbacks by reason.")
            lines.append("# TYPE athena_prompt_rollback_total counter")
            for reason, count in rollback_reasons.items():
                safe_reason = reason.replace('"', '\\"')
                lines.append(f'athena_prompt_rollback_total{{reason="{safe_reason}"}} {count}')

        # ---- source_degradation_total ----
        deg_counts: dict[str, int] = {}
        for m in metrics_list:
            for src in m.source_degradation:
                deg_counts[src] = deg_counts.get(src, 0) + 1
        if deg_counts:
            lines.append(
                "# HELP athena_prompt_source_degradation_total Number of source degradations."
            )
            lines.append("# TYPE athena_prompt_source_degradation_total counter")
            for src, count in deg_counts.items():
                safe_src = src.replace('"', '\\"')
                lines.append(f'athena_prompt_source_degradation_total{{source="{safe_src}"}} {count}')

        # ---- errors_total ----
        error_count = sum(1 for m in metrics_list if m.error)
        lines.append("# HELP athena_prompt_errors_total Number of fusion errors.")
        lines.append("# TYPE athena_prompt_errors_total counter")
        lines.append(f"athena_prompt_errors_total {error_count}")

        return "\n".join(lines) + "\n"


def get_prompt_metrics_collector() -> PromptMetricsCollector:
    """获取 PromptMetricsCollector 单例。"""
    return PromptMetricsCollector()
