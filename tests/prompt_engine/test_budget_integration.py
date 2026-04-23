"""
Context Budget Manager 集成测试

验证 Budget Manager 在主链路中的裁剪、回滚和降级行为。
"""

from unittest.mock import MagicMock, patch

import pytest

from core.prompt_engine.budget.manager import ContextBudgetManager
from core.prompt_engine.budget.rollback import RollbackReason
from core.prompt_engine.budget.truncation import EvidenceItem


class TestBudgetIntegration:
    def test_budget_truncate_excess_evidence(self):
        """证据过多时自动裁剪至 budget 内。"""
        manager = ContextBudgetManager(total_budget=512, min_core_evidence=1)
        evidence = [
            EvidenceItem(content="A" * 200, relevance_score=0.9, source="postgres"),
            EvidenceItem(content="B" * 200, relevance_score=0.8, source="neo4j"),
            EvidenceItem(content="C" * 200, relevance_score=0.7, source="wiki"),
        ]
        result = manager.build_context(
            system_prompt="system",
            user_query="query",
            evidence_list=evidence,
        )
        assert len(result["evidence"]) < len(evidence)
        assert result["metrics"].evidence_count_before == 3
        assert result["metrics"].evidence_count_after < 3
        assert result["metrics"].evidence_dropped_count > 0

    def test_budget_rollback_on_token_overflow(self):
        """即使裁剪后仍超限时触发回滚降级。"""
        manager = ContextBudgetManager(total_budget=256, min_core_evidence=1)
        evidence = [
            EvidenceItem(content="X" * 500, relevance_score=0.9, source="postgres"),
        ]
        result = manager.build_context(
            system_prompt="S" * 200,
            user_query="Q" * 200,
            evidence_list=evidence,
        )
        assert result["rollback"].should_rollback is True
        assert result["rollback"].reason in (
            RollbackReason.TOKEN_OVERFLOW,
            RollbackReason.INSUFFICIENT_EVIDENCE,
        )
        assert result["target_mode"] == "single_source"

    def test_budget_timeout_rollback(self):
        """超时触发最高优先级回滚。"""
        manager = ContextBudgetManager(total_budget=8192, timeout_ms=10.0)
        evidence = [EvidenceItem(content="test", relevance_score=0.5, source="wiki")]
        result = manager.build_context(
            system_prompt="sys",
            user_query="query",
            evidence_list=evidence,
            elapsed_ms=50.0,  # 超过 10ms 阈值
        )
        assert result["rollback"].should_rollback is True
        assert result["rollback"].reason == RollbackReason.TIMEOUT
        assert result["target_mode"] == "single_source"

    def test_budget_no_rollback_when_healthy(self):
        """正常情况不触发回滚。"""
        manager = ContextBudgetManager(total_budget=8192, min_core_evidence=1)
        evidence = [
            EvidenceItem(content="short", relevance_score=0.9, source="postgres"),
        ]
        result = manager.build_context(
            system_prompt="sys",
            user_query="query",
            evidence_list=evidence,
        )
        assert result["rollback"].should_rollback is False
        assert result["rollback"].reason == RollbackReason.NONE
        assert result["target_mode"] == "multi_source"

    def test_budget_metrics_populated(self):
        """metrics 字段完整填充。"""
        manager = ContextBudgetManager(total_budget=1024)
        evidence = [EvidenceItem(content="E" * 100, relevance_score=0.8, source="wiki")]
        result = manager.build_context(
            system_prompt="sys",
            user_query="query",
            evidence_list=evidence,
            elapsed_ms=15.0,
        )
        metrics = result["metrics"]
        assert metrics.budget_total == 1024
        assert metrics.budget_used > 0
        assert 0.0 <= metrics.budget_usage_ratio <= 1.0
        assert metrics.evidence_count_before == 1
        assert metrics.elapsed_ms == 15.0
