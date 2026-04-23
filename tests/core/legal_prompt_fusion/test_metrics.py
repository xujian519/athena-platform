#!/usr/bin/env python3
from __future__ import annotations

import json
import logging

import pytest

from core.legal_prompt_fusion.metrics import FusionMetrics, _send_metrics_async


class TestFusionMetrics:
    """FusionMetrics 数据模型测试。"""

    def test_to_dict(self):
        metrics = FusionMetrics(
            request_id="req_123",
            domain="patent",
            task_type="office_action",
            fusion_enabled=True,
            latency_ms=123.456,
            evidence_count=5,
            evidence_by_source={"postgres": 2, "neo4j": 2, "wiki": 1},
            cache_hit=False,
            wiki_revision="abc123",
            template_version="v1.2.3",
            source_degradation=["postgres"],
            error=None,
        )
        d = metrics.to_dict()
        assert d["request_id"] == "req_123"
        assert d["domain"] == "patent"
        assert d["evidence_by_source"] == {"postgres": 2, "neo4j": 2, "wiki": 1}
        assert d["error"] is None

    def test_to_json(self):
        metrics = FusionMetrics(
            request_id="req_456",
            domain="patent",
            task_type="office_action",
        )
        raw = metrics.to_json()
        parsed = json.loads(raw)
        assert parsed["request_id"] == "req_456"
        assert parsed["fusion_enabled"] is False

    def test_default_values(self):
        metrics = FusionMetrics(request_id="req_789", domain="patent", task_type="novelty_analysis")
        assert metrics.latency_ms == 0.0
        assert metrics.evidence_count == 0
        assert metrics.evidence_by_source == {}
        assert metrics.cache_hit is False
        assert metrics.wiki_revision == "unknown"
        assert metrics.source_degradation == []
        assert metrics.error is None


class TestSendMetricsAsync:
    """异步指标发送测试。"""

    @pytest.mark.asyncio
    async def test_send_metrics_does_not_raise(self, caplog):
        """指标发送失败不应抛出异常。"""
        caplog.set_level(logging.INFO)
        metrics = FusionMetrics(
            request_id="req_001",
            domain="patent",
            task_type="office_action",
            fusion_enabled=True,
            latency_ms=50.0,
            evidence_count=3,
        )
        # 正常执行不应抛异常
        await _send_metrics_async(metrics)
        # 验证日志中包含结构化 JSON
        assert "fusion_metrics" in caplog.text

    @pytest.mark.asyncio
    async def test_baseline_metrics_for_disabled_fusion(self, caplog):
        """融合关闭时也应产生基线记录。"""
        caplog.set_level(logging.INFO)
        metrics = FusionMetrics(
            request_id="req_002",
            domain="patent",
            task_type="office_action",
            fusion_enabled=False,
            latency_ms=0.0,
            evidence_count=0,
        )
        await _send_metrics_async(metrics)
        assert "fusion_metrics" in caplog.text
        # 验证 JSON 中包含 fusion_enabled=false
        log_line = [r for r in caplog.records if "fusion_metrics" in r.message][0]
        assert '"fusion_enabled":false' in log_line.message
