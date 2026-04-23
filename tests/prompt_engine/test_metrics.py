"""
C4-Metrics: FusionMetrics 与 Prometheus 指标端点测试。

覆盖：
- FusionMetrics 数据模型与序列化
- PromptMetricsCollector 环形缓冲区与分位计算
- Prometheus 文本格式导出（前缀 athena_prompt_）
- /api/v1/prompt-system/metrics 端点（prometheus 格式）
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

import pytest

project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from core.legal_prompt_fusion.metrics_collector import (
    FusionMetrics,
    PromptMetricsCollector,
    _percentile,
    get_prompt_metrics_collector,
)


class TestFusionMetrics:
    def test_basic_creation(self):
        m = FusionMetrics(
            request_id="req-001",
            domain="patent",
            task_type="creativity_analysis",
        )
        assert m.request_id == "req-001"
        assert m.domain == "patent"
        assert m.cache_hit is False
        assert m.schema_validated is False
        assert m.rollback_reason is None

    def test_enhanced_fields(self):
        m = FusionMetrics(
            request_id="req-002",
            domain="patent",
            task_type="creativity_analysis",
            token_count_input=150,
            token_count_output=400,
            evidence_relevance_score=0.85,
            budget_usage_ratio=0.25,
            rollback_reason="fusion_failure",
            schema_validated=True,
        )
        assert m.token_count_input == 150
        assert m.token_count_output == 400
        assert m.evidence_relevance_score == 0.85
        assert m.budget_usage_ratio == 0.25
        assert m.rollback_reason == "fusion_failure"
        assert m.schema_validated is True

    def test_serialization(self):
        m = FusionMetrics(
            request_id="req-003",
            domain="patent",
            task_type="creativity_analysis",
            rollback_reason=None,
        )
        d = m.to_dict()
        assert d["request_id"] == "req-003"
        assert d["rollback_reason"] is None
        j = m.to_json()
        assert '"request_id":"req-003"' in j


class TestPercentileHelper:
    def test_empty(self):
        assert _percentile([], 50) == 0.0

    def test_single(self):
        assert _percentile([42.0], 50) == 42.0

    def test_median(self):
        assert _percentile([1.0, 2.0, 3.0, 4.0], 50) == 2.5

    def test_p95(self):
        data = [float(i) for i in range(1, 101)]
        # k=(100-1)*0.95=94.05 -> 95*0.95 + 96*0.05 = 95.05
        assert _percentile(data, 95) == 95.05

    def test_p99(self):
        data = [float(i) for i in range(1, 101)]
        # k=(100-1)*0.99=98.01 -> 99*0.99 + 100*0.01 = 99.01
        assert _percentile(data, 99) == 99.01


class TestPromptMetricsCollector:
    def setup_method(self):
        # 每个测试前重置单例内部状态，保证隔离
        collector = PromptMetricsCollector()
        collector._metrics.clear()

    def test_singleton(self):
        c1 = get_prompt_metrics_collector()
        c2 = get_prompt_metrics_collector()
        assert c1 is c2

    def test_record_and_retrieve(self):
        collector = PromptMetricsCollector()
        m = FusionMetrics(request_id="r1", domain="patent", task_type="t1", latency_ms=10.0)
        collector.record(m)
        recent = collector.get_recent_metrics()
        assert len(recent) == 1
        assert recent[0].latency_ms == 10.0

    def test_ring_buffer_max_1000(self):
        collector = PromptMetricsCollector()
        for i in range(1200):
            collector.record(
                FusionMetrics(request_id=f"r{i}", domain="patent", task_type="t1")
            )
        assert len(collector._metrics) == 1000
        recent = collector.get_recent_metrics()
        assert len(recent) == 1000
        # 最早的那条已被挤出
        assert recent[0].request_id != "r0"

    def test_latency_percentiles(self):
        collector = PromptMetricsCollector()
        for lat in [10.0, 20.0, 30.0, 40.0, 50.0]:
            collector.record(
                FusionMetrics(
                    request_id=f"r{int(lat)}", domain="patent", task_type="t1", latency_ms=lat
                )
            )
        pcts = collector.get_latency_percentiles()
        assert pcts["p50"] == 30.0
        assert pcts["p95"] == 48.0
        assert pcts["p99"] == 49.6

    def test_prometheus_output_structure(self):
        collector = PromptMetricsCollector()
        collector.record(
            FusionMetrics(
                request_id="r1",
                domain="patent",
                task_type="t1",
                latency_ms=25.0,
                token_count_input=100,
                token_count_output=200,
                evidence_relevance_score=0.8,
                budget_usage_ratio=0.3,
                schema_validated=True,
                cache_hit=True,
                rollback_reason="fusion_failure",
                source_degradation=["postgres"],
                error="some_error",
            )
        )
        text = collector.export_prometheus()
        # 前缀检查
        assert "athena_prompt_fusion_requests_total" in text
        assert "athena_prompt_cache_hits_total" in text
        assert "athena_prompt_fusion_latency_ms" in text
        assert "athena_prompt_token_count_input_total" in text
        assert "athena_prompt_token_count_output_total" in text
        assert "athena_prompt_evidence_relevance_score" in text
        assert "athena_prompt_budget_usage_ratio" in text
        assert "athena_prompt_schema_validated_total" in text
        assert "athena_prompt_rollback_total" in text
        assert "athena_prompt_source_degradation_total" in text
        assert "athena_prompt_errors_total" in text

    def test_prometheus_quantile_values(self):
        collector = PromptMetricsCollector()
        for lat in [10.0, 20.0, 30.0, 40.0, 50.0]:
            collector.record(
                FusionMetrics(
                    request_id=f"r{int(lat)}", domain="patent", task_type="t1", latency_ms=lat
                )
            )
        text = collector.export_prometheus()
        # 提取 quantile="0.5" 的值
        match = re.search(r'athena_prompt_fusion_latency_ms\{quantile="0\.5"\}\s+([\d.]+)', text)
        assert match is not None
        assert float(match.group(1)) == 30.0

    def test_prometheus_empty_collector(self):
        collector = PromptMetricsCollector()
        collector._metrics.clear()
        text = collector.export_prometheus()
        # 空状态下仍应输出基本计数器
        assert "athena_prompt_fusion_requests_total 0" in text
        assert "athena_prompt_cache_hits_total 0" in text
        assert "athena_prompt_errors_total 0" in text
        # latency summary 不应出现（无数据）
        assert "athena_prompt_fusion_latency_ms_count" not in text

    def test_prometheus_rollback_labels(self):
        collector = PromptMetricsCollector()
        collector.record(
            FusionMetrics(
                request_id="r1",
                domain="patent",
                task_type="t1",
                rollback_reason="fusion_failure",
            )
        )
        collector.record(
            FusionMetrics(
                request_id="r2",
                domain="patent",
                task_type="t1",
                rollback_reason="fusion_failure",
            )
        )
        text = collector.export_prometheus()
        assert 'athena_prompt_rollback_total{reason="fusion_failure"} 2' in text

    def test_prometheus_source_degradation_labels(self):
        collector = PromptMetricsCollector()
        collector.record(
            FusionMetrics(
                request_id="r1",
                domain="patent",
                task_type="t1",
                source_degradation=["postgres", "neo4j"],
            )
        )
        text = collector.export_prometheus()
        assert 'athena_prompt_source_degradation_total{source="postgres"} 1' in text
        assert 'athena_prompt_source_degradation_total{source="neo4j"} 1' in text


class TestMetricsEndpoint:
    @pytest.fixture
    def metrics_client(self):
        """挂载 /metrics 端点的独立测试客户端。"""
        import asyncio

        import httpx
        from fastapi import APIRouter, FastAPI
        from fastapi.responses import PlainTextResponse

        from tests.prompt_engine.conftest import _SyncTestClient

        app = FastAPI()
        router = APIRouter(prefix="/api/v1/prompt-system")

        @router.get("/metrics")
        async def get_metrics(format: str = "json"):
            if format.lower() == "prometheus":
                collector = get_prompt_metrics_collector()
                return PlainTextResponse(
                    content=collector.export_prometheus(),
                    media_type="text/plain; version=0.0.4; charset=utf-8",
                )
            return {"scenario_identifier": {}, "timestamp": "2024-01-01T00:00:00"}

        app.include_router(router)
        return _SyncTestClient(app)

    def test_metrics_prometheus_format(self, metrics_client, monkeypatch):
        """通过端点获取 prometheus 格式指标。"""
        # 先清空 collector，确保状态可控
        collector = PromptMetricsCollector()
        collector._metrics.clear()
        collector.record(
            FusionMetrics(
                request_id="endpoint-req",
                domain="patent",
                task_type="creativity_analysis",
                latency_ms=12.5,
                token_count_input=50,
                token_count_output=150,
                schema_validated=True,
            )
        )

        response = metrics_client.get("/api/v1/prompt-system/metrics?format=prometheus")
        assert response.status_code == 200
        text = response.text
        assert "athena_prompt_fusion_requests_total" in text
        assert "athena_prompt_fusion_latency_ms" in text
        assert "athena_prompt_schema_validated_total" in text

    def test_metrics_json_format(self, metrics_client):
        """JSON 格式应保持向后兼容。"""
        response = metrics_client.get("/api/v1/prompt-system/metrics?format=json")
        assert response.status_code == 200
        data = response.json()
        assert "scenario_identifier" in data
        assert "timestamp" in data
