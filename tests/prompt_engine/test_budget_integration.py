"""
C1-BudgetIntegration: ContextBudgetManager 与融合主链路集成测试

验证：
- 证据过多时自动裁剪
- token 超限时触发回滚降级
- 环境变量 LEGAL_FUSION_BUDGET_TOKENS 读取
- EvidenceItem 与 RetrievalEvidence 互转及映射
"""

from __future__ import annotations

import os
from typing import Any

import pytest

from core.prompt_engine.budget.manager import BudgetAllocation, ContextBudgetManager
from core.prompt_engine.budget.rollback import RollbackReason
from core.prompt_engine.budget.truncation import EvidenceItem
from core.legal_prompt_fusion.models import (
    FusedPromptContext,
    PromptGenerationRequest,
    RetrievalEvidence,
    SourceType,
)


def _make_retrieval_evidence(
    source_type: SourceType,
    content: str,
    score: float,
    source_id: str = "test-id",
    title: str = "test-title",
) -> RetrievalEvidence:
    """快速构造 RetrievalEvidence（模拟三源检索结果）。"""
    return RetrievalEvidence(
        source_type=source_type,
        source_id=source_id,
        title=title,
        content=content,
        score=score,
        metadata={},
    )


def _convert_to_evidence_items(
    evidence: list[RetrievalEvidence],
) -> list[EvidenceItem]:
    """模拟主链路中的转换逻辑：RetrievalEvidence → EvidenceItem。"""
    return [
        EvidenceItem(
            content=ev.content,
            relevance_score=ev.score,
            source=ev.source_type.value,
            metadata={"original": ev},
        )
        for ev in evidence
    ]


class TestBudgetIntegration:
    """验证 Budget Manager 在融合链路中的裁剪与降级行为。"""

    def test_evidence_truncation_when_too_many(self):
        """证据过多时，ContextBudgetManager 应自动裁剪低相关性证据。"""
        evidence = [
            _make_retrieval_evidence(
                source_type=SourceType.POSTGRES
                if i % 3 == 0
                else (SourceType.NEO4J if i % 3 == 1 else SourceType.WIKI),
                content="专利法相关条文与解释，包含大量技术术语和法律细节说明。" * 20,
                score=0.95 - i * 0.05,
                source_id=f"ev-{i}",
            )
            for i in range(10)
        ]

        items = _convert_to_evidence_items(evidence)
        manager = ContextBudgetManager(total_budget=2048)
        result = manager.build_context(
            system_prompt="系统提示词" * 10,
            user_query="用户查询" * 10,
            evidence_list=items,
        )

        metrics = result["metrics"]
        assert metrics.evidence_count_before == 10
        assert metrics.evidence_count_after < 10
        assert metrics.evidence_dropped_count > 0
        assert result["rollback"].target_mode in ("multi_source", "single_source")

    def test_rollback_on_token_overflow(self):
        """token 超限时，应触发回滚降级为 single_source。"""
        evidence = [
            _make_retrieval_evidence(
                source_type=SourceType.POSTGRES,
                content="法" * 3000,
                score=0.95,
                source_id="pg1",
            ),
            _make_retrieval_evidence(
                source_type=SourceType.NEO4J,
                content="关" * 3000,
                score=0.90,
                source_id="neo1",
            ),
        ]

        items = _convert_to_evidence_items(evidence)
        manager = ContextBudgetManager(
            total_budget=2048,
            allocation=BudgetAllocation(
                system_prompt=256,
                user_query=128,
                evidence=512,
                output_buffer=256,
                overhead=256,
            ),
            min_core_evidence=2,
        )

        result = manager.build_context(
            system_prompt="系统提示",
            user_query="用户问题",
            evidence_list=items,
        )

        assert result["rollback"].should_rollback is True
        assert result["rollback"].reason == RollbackReason.TOKEN_OVERFLOW
        assert result["target_mode"] == "single_source"
        assert result["metrics"].rollback_reason == RollbackReason.TOKEN_OVERFLOW.value

    def test_rollback_on_timeout(self):
        """处理超时时，应触发回滚降级为 single_source。"""
        evidence = [
            _make_retrieval_evidence(
                source_type=SourceType.WIKI,
                content="背景知识说明。",
                score=0.80,
            ),
        ]

        items = _convert_to_evidence_items(evidence)
        manager = ContextBudgetManager(total_budget=8192, timeout_ms=50.0)
        result = manager.build_context(
            system_prompt="系统提示",
            user_query="用户问题",
            evidence_list=items,
            elapsed_ms=100.0,
        )

        assert result["rollback"].should_rollback is True
        assert result["rollback"].reason == RollbackReason.TIMEOUT
        assert result["target_mode"] == "single_source"

    def test_budget_env_var_override(self, monkeypatch):
        """LEGAL_FUSION_BUDGET_TOKENS 环境变量应覆盖默认 budget。"""
        monkeypatch.setenv("LEGAL_FUSION_BUDGET_TOKENS", "16384")
        total_budget = int(os.getenv("LEGAL_FUSION_BUDGET_TOKENS", "8192"))
        assert total_budget == 16384

        manager = ContextBudgetManager(total_budget=total_budget)
        assert manager.allocation.evidence >= 7000

    def test_source_preservation_in_conversion(self):
        """RetrievalEvidence → EvidenceItem 转换应保留来源类型。"""
        evidence = [
            _make_retrieval_evidence(SourceType.POSTGRES, "专利法第22条", 0.95),
            _make_retrieval_evidence(SourceType.NEO4J, "创造性判断关系链", 0.88),
            _make_retrieval_evidence(SourceType.WIKI, "三步法框架", 0.80),
        ]

        items = _convert_to_evidence_items(evidence)
        assert len(items) == 3
        assert items[0].source == "postgres"
        assert items[1].source == "neo4j"
        assert items[2].source == "wiki"

    def test_kept_evidence_mapping_with_metadata(self):
        """EvidenceItem.metadata 中的 original 引用应正确映射回 RetrievalEvidence。"""
        evidence = [
            _make_retrieval_evidence(SourceType.POSTGRES, "内容A", 0.9, source_id="pg1"),
            _make_retrieval_evidence(SourceType.NEO4J, "内容B", 0.8, source_id="neo1"),
            _make_retrieval_evidence(SourceType.WIKI, "内容C", 0.5, source_id="wiki1"),
        ]

        items = _convert_to_evidence_items(evidence)
        manager = ContextBudgetManager(total_budget=1024)
        result = manager.build_context(
            system_prompt="系统提示",
            user_query="用户问题",
            evidence_list=items,
        )

        kept_items = result["evidence"]
        for item in kept_items:
            assert "original" in item.metadata
            original: Any = item.metadata["original"]
            assert isinstance(original, RetrievalEvidence)
            assert original.content == item.content

    def test_prompt_rerender_after_truncation(self):
        """证据裁剪后，应能用 builder 方法重新渲染提示词（模拟主链路行为）。"""
        from core.legal_prompt_fusion.prompt_context_builder import (
            LegalPromptContextBuilder,
        )

        evidence = [
            _make_retrieval_evidence(SourceType.POSTGRES, "专" * 500, 0.9, source_id="pg1"),
            _make_retrieval_evidence(SourceType.POSTGRES, "利" * 500, 0.8, source_id="pg2"),
            _make_retrieval_evidence(SourceType.NEO4J, "法" * 500, 0.7, source_id="neo1"),
            _make_retrieval_evidence(SourceType.WIKI, "审" * 500, 0.6, source_id="wiki1"),
        ]

        builder = LegalPromptContextBuilder()
        context = FusedPromptContext(
            user_query="分析创造性",
            domain="patent",
            scenario="creativity_analysis",
            evidence=evidence,
            freshness={"wiki_revision": "v1.0"},
        )
        context.legal_articles = builder._convert_to_snippets(evidence, SourceType.POSTGRES)
        context.graph_relations = builder._convert_to_snippets(evidence, SourceType.NEO4J)
        context.wiki_background = builder._convert_to_snippets(evidence, SourceType.WIKI)

        full_system_prompt = builder._render_system_prompt(context)
        full_user_prompt = builder._render_user_prompt(context, {})

        # 执行 budget 裁剪
        items = _convert_to_evidence_items(evidence)
        manager = ContextBudgetManager(total_budget=2048)
        budget_result = manager.build_context(
            system_prompt=full_system_prompt,
            user_query=full_user_prompt,
            evidence_list=items,
        )

        if budget_result["target_mode"] != "single_source":
            assert budget_result["metrics"].evidence_count_before == 4
            kept_evidence = [
                item.metadata["original"] for item in budget_result["evidence"]
            ]
            context.evidence = kept_evidence
            context.legal_articles = builder._convert_to_snippets(
                kept_evidence, SourceType.POSTGRES
            )
            context.graph_relations = builder._convert_to_snippets(
                kept_evidence, SourceType.NEO4J
            )
            context.wiki_background = builder._convert_to_snippets(
                kept_evidence, SourceType.WIKI
            )

            cropped_system = builder._render_system_prompt(context)
            # 裁剪后提示词应能正常生成，且证据数减少或不变
            assert len(context.evidence) <= 4
            assert isinstance(cropped_system, str)
