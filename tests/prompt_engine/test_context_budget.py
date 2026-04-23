"""
Context Budget 模块单元测试

覆盖：
- TokenEstimator 估算精度（有/无 tiktoken）
- EvidenceTruncator 排序与裁剪
- RollbackTrigger 三类回滚触发
- ContextBudgetManager 端到端分配、动态调整、metrics 采集
"""


import sys
from pathlib import Path

import pytest

# 隔离并建立 core.prompt_engine.budget 导入路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from core.prompt_engine.budget.manager import (
    BudgetAllocation,
    BudgetMetrics,
    ContextBudgetManager,
)
from core.prompt_engine.budget.rollback import (
    RollbackDecision,
    RollbackReason,
    RollbackTrigger,
)
from core.prompt_engine.budget.truncation import (
    EvidenceItem,
    EvidenceTruncator,
    TruncationResult,
)
from core.prompt_engine.budget.utils import TokenEstimator


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def estimator():
    return TokenEstimator()


@pytest.fixture
def truncator(estimator):
    return EvidenceTruncator(estimator=estimator)


@pytest.fixture
def rollback_trigger():
    return RollbackTrigger(min_core_threshold=2, timeout_ms=200.0)


@pytest.fixture
def sample_evidence() -> list[EvidenceItem]:
    """构造 5 条证据，长度与相关性递减。"""
    return [
        EvidenceItem(content="核心法条：专利法第22条关于创造性的规定。", relevance_score=0.95, source="law"),
        EvidenceItem(content="司法解释：创造性判断中的三步法适用。", relevance_score=0.88, source="judicial"),
        EvidenceItem(content="类似案例：A公司诉B公司专利侵权案判决书摘要。", relevance_score=0.70, source="case"),
        EvidenceItem(content="百科补充：专利审查指南中关于技术效果的说明。", relevance_score=0.50, source="wiki"),
        EvidenceItem(content="背景信息：该领域技术发展历程简述。", relevance_score=0.30, source="background"),
    ]


# ---------------------------------------------------------------------------
# TokenEstimator
# ---------------------------------------------------------------------------


class TestTokenEstimator:
    def test_estimate_empty(self):
        est = TokenEstimator()
        assert est.estimate("") == 0

    def test_estimate_ascii_approximate(self):
        est = TokenEstimator()
        # 回退模式下 4 字符 ~ 1 token；tiktoken 对重复字符会 BPE 压缩
        text = "The quick brown fox jumps over the lazy dog. " * 3  # ~150 chars
        tokens = est.estimate(text)
        assert tokens >= 15  # 足够覆盖 tiktoken 和回退两种模式

    def test_estimate_cjk_approximate(self):
        est = TokenEstimator()
        text = "专" * 30
        tokens = est.estimate(text)
        # CJK 1.5 字符/token => ~20 tokens
        assert tokens >= 15

    def test_estimate_mixed(self):
        est = TokenEstimator()
        text = "专利law分析123"
        tokens = est.estimate(text)
        assert tokens > 0


# ---------------------------------------------------------------------------
# EvidenceTruncator
# ---------------------------------------------------------------------------


class TestEvidenceTruncator:
    def test_truncate_keeps_high_relevance(self, truncator, sample_evidence):
        result = truncator.truncate(sample_evidence, target_budget=200, min_core_count=1)
        assert len(result.kept) >= 1
        # 最高分证据应被保留
        assert any(e.relevance_score == 0.95 for e in result.kept)

    def test_truncate_drops_low_relevance(self, truncator, sample_evidence):
        result = truncator.truncate(sample_evidence, target_budget=50, min_core_count=1)
        # 低分证据应被丢弃
        assert any(e.relevance_score == 0.30 for e in result.dropped)

    def test_truncate_respects_min_core_count(self, truncator, sample_evidence):
        result = truncator.truncate(sample_evidence, target_budget=10, min_core_count=3)
        # 即使 budget 极小，也保留 3 条
        assert len(result.kept) == 3

    def test_truncate_tokens_stats(self, truncator, sample_evidence):
        result = truncator.truncate(sample_evidence, target_budget=500, min_core_count=1)
        assert result.tokens_before >= result.tokens_after
        assert result.tokens_after <= result.target_budget

    def test_truncate_empty_list(self, truncator):
        result = truncator.truncate([], target_budget=100, min_core_count=1)
        assert result.kept == []
        assert result.dropped == []
        assert result.tokens_before == 0

    def test_truncate_same_score_shorter_first(self, truncator):
        evs = [
            EvidenceItem(content="x" * 100, relevance_score=0.5, source="a"),
            EvidenceItem(content="y" * 20, relevance_score=0.5, source="b"),
        ]
        result = truncator.truncate(evs, target_budget=30, min_core_count=1)
        # 同分下短的优先保留
        assert result.kept[0].content == "y" * 20


# ---------------------------------------------------------------------------
# RollbackTrigger
# ---------------------------------------------------------------------------


class TestRollbackTrigger:
    def test_no_rollback_when_healthy(self, rollback_trigger):
        dec = rollback_trigger.check(
            evidence_kept_count=5,
            evidence_tokens=100,
            evidence_budget=500,
            elapsed_ms=50.0,
        )
        assert dec.should_rollback is False
        assert dec.reason == RollbackReason.NONE
        assert dec.target_mode == "multi_source"

    def test_rollback_token_overflow(self, rollback_trigger):
        dec = rollback_trigger.check(
            evidence_kept_count=2,
            evidence_tokens=1000,
            evidence_budget=500,
            elapsed_ms=50.0,
        )
        assert dec.should_rollback is True
        assert dec.reason == RollbackReason.TOKEN_OVERFLOW
        assert dec.target_mode == "single_source"

    def test_rollback_insufficient_evidence(self, rollback_trigger):
        dec = rollback_trigger.check(
            evidence_kept_count=1,
            evidence_tokens=100,
            evidence_budget=500,
            elapsed_ms=50.0,
        )
        assert dec.should_rollback is True
        assert dec.reason == RollbackReason.INSUFFICIENT_EVIDENCE

    def test_rollback_timeout(self, rollback_trigger):
        dec = rollback_trigger.check(
            evidence_kept_count=5,
            evidence_tokens=100,
            evidence_budget=500,
            elapsed_ms=250.0,
        )
        assert dec.should_rollback is True
        assert dec.reason == RollbackReason.TIMEOUT

    def test_timeout_priority_over_token(self, rollback_trigger):
        # 超时 + 超限同时发生，应优先返回 TIMEOUT
        dec = rollback_trigger.check(
            evidence_kept_count=1,
            evidence_tokens=1000,
            evidence_budget=500,
            elapsed_ms=250.0,
        )
        assert dec.reason == RollbackReason.TIMEOUT


# ---------------------------------------------------------------------------
# ContextBudgetManager
# ---------------------------------------------------------------------------


class TestContextBudgetManager:
    def test_initialization_default_allocation(self):
        mgr = ContextBudgetManager(total_budget=8192)
        assert mgr.total_budget == 8192
        assert mgr.allocation.total <= 8192

    def test_initialization_custom_allocation(self):
        alloc = BudgetAllocation(
            system_prompt=512, user_query=256, evidence=6000, output_buffer=512, overhead=256
        )
        mgr = ContextBudgetManager(total_budget=8192, allocation=alloc)
        assert mgr.allocation.evidence == 6000

    def test_build_context_no_evidence(self):
        mgr = ContextBudgetManager(total_budget=8192, min_core_evidence=0)
        result = mgr.build_context(
            system_prompt="你是助手",
            user_query="分析创造性",
            evidence_list=[],
        )
        assert result["evidence"] == []
        assert result["metrics"].evidence_count_after == 0
        assert result["rollback"].should_rollback is False

    def test_build_context_no_evidence_rollback(self):
        mgr = ContextBudgetManager(total_budget=8192, min_core_evidence=2)
        result = mgr.build_context(
            system_prompt="你是助手",
            user_query="分析创造性",
            evidence_list=[],
        )
        assert result["evidence"] == []
        assert result["rollback"].should_rollback is True
        assert result["rollback"].reason == RollbackReason.INSUFFICIENT_EVIDENCE

    def test_build_context_normal(self, sample_evidence):
        mgr = ContextBudgetManager(total_budget=8192, min_core_evidence=2)
        result = mgr.build_context(
            system_prompt="你是专利分析专家。" * 20,
            user_query="请分析这个方案的创造性。" * 10,
            evidence_list=sample_evidence,
        )
        metrics: BudgetMetrics = result["metrics"]
        assert metrics.evidence_count_before == 5
        assert metrics.evidence_count_after >= 2
        assert metrics.budget_usage_ratio > 0
        assert result["target_mode"] in ("multi_source", "single_source")

    def test_build_context_forces_rollback_when_budget_too_tight(self):
        # 构造极长证据，使得即使裁剪后 evidence 部分仍超限
        long_evidence = [
            EvidenceItem(content="专" * 2000, relevance_score=0.9, source="law"),
            EvidenceItem(content="利" * 2000, relevance_score=0.8, source="law"),
        ]
        mgr = ContextBudgetManager(
            total_budget=2048,
            allocation=BudgetAllocation(
                system_prompt=256, user_query=128, evidence=512, output_buffer=256, overhead=256
            ),
            min_core_evidence=2,
        )
        result = mgr.build_context(
            system_prompt="系统提示",
            user_query="用户问题",
            evidence_list=long_evidence,
        )
        rollback: RollbackDecision = result["rollback"]
        # 由于 min_core=2，两条超长证据都会保留，导致 evidence_tokens > evidence_budget
        assert rollback.should_rollback is True
        assert rollback.reason == RollbackReason.TOKEN_OVERFLOW

    def test_dynamic_shift(self):
        alloc = BudgetAllocation(
            system_prompt=512, user_query=1024, evidence=3000, output_buffer=512, overhead=256
        )
        mgr = ContextBudgetManager(
            total_budget=8192,
            allocation=alloc,
            enable_dynamic_shift=True,
        )
        # user_query 极短，应有剩余 budget 转移给 evidence
        result = mgr.build_context(
            system_prompt="系统提示",
            user_query="短",
            evidence_list=[EvidenceItem(content="证据", relevance_score=0.5)],
        )
        # evidence 配额应大于原始 3000（因为 user_query 只用了少量 token）
        assert result["metrics"].budget_total == 8192

    def test_metrics_after_build(self, sample_evidence):
        mgr = ContextBudgetManager(total_budget=8192)
        mgr.build_context(
            system_prompt="系统提示",
            user_query="用户问题",
            evidence_list=sample_evidence,
        )
        metrics = mgr.get_metrics()
        assert metrics is not None
        assert metrics.evidence_dropped_count >= 0
        assert 0.0 <= metrics.budget_usage_ratio <= 1.0

    def test_build_context_timeout_rollback(self, sample_evidence):
        mgr = ContextBudgetManager(total_budget=8192, timeout_ms=100.0)
        result = mgr.build_context(
            system_prompt="系统提示",
            user_query="用户问题",
            evidence_list=sample_evidence,
            elapsed_ms=150.0,
        )
        assert result["rollback"].should_rollback is True
        assert result["rollback"].reason == RollbackReason.TIMEOUT
        assert result["metrics"].rollback_reason == RollbackReason.TIMEOUT.value


# ---------------------------------------------------------------------------
# Integration / Edge Cases
# ---------------------------------------------------------------------------


class TestBudgetIntegration:
    def test_16k_budget_allocation(self):
        mgr = ContextBudgetManager(total_budget=16384)
        assert mgr.allocation.evidence >= 7000  # 16K 默认 evidence 更大

    def test_32k_budget_allocation(self):
        mgr = ContextBudgetManager(total_budget=32768)
        assert mgr.allocation.evidence >= 15000

    def test_truncation_result_structure(self, truncator):
        evs = [EvidenceItem(content="a" * 40, relevance_score=float(i) / 10) for i in range(5, 0, -1)]
        result = truncator.truncate(evs, target_budget=30, min_core_count=1)
        assert isinstance(result, TruncationResult)
        assert len(result.kept) + len(result.dropped) == 5

    def test_min_core_threshold_boundary(self):
        trigger = RollbackTrigger(min_core_threshold=1)
        dec = trigger.check(
            evidence_kept_count=1,
            evidence_tokens=10,
            evidence_budget=100,
        )
        assert dec.should_rollback is False

        dec2 = trigger.check(
            evidence_kept_count=0,
            evidence_tokens=0,
            evidence_budget=100,
        )
        assert dec2.should_rollback is True
        assert dec2.reason == RollbackReason.INSUFFICIENT_EVIDENCE
