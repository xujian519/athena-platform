#!/usr/bin/env python3
from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from core.api.prompt_system_routes import (
    PromptGenerateRequest,
    generate_prompt,
)
from core.legal_prompt_fusion.rollout_config import FusionRolloutConfig


@pytest.fixture(autouse=True)
def reset_rollout_config():
    """每个测试前重置灰度配置单例。"""
    import core.api.prompt_system_routes as routes

    routes._rollout_config = None
    yield
    routes._rollout_config = None


@pytest.fixture
def mock_rule():
    """模拟规则对象。"""
    rule = MagicMock()
    rule.rule_id = "rule_001"
    rule.domain = "patent"
    rule.task_type = "office_action"
    rule.phase = "draft"
    rule.capability_invocations = []
    rule.substitute_variables.return_value = ("system_prompt", "user_prompt")
    return rule


@pytest.fixture
def mock_context():
    """模拟场景识别上下文。"""
    ctx = MagicMock()
    ctx.domain.value = "patent"
    ctx.task_type.value = "office_action"
    ctx.phase.value = "draft"
    ctx.confidence = 0.95
    ctx.extracted_variables = {"key": "value"}
    return ctx


@pytest.fixture
def mock_prompt_cache():
    """模拟提示词缓存。"""
    cache = MagicMock()
    cache.get.return_value = None  # 默认缓存未命中
    return cache


class TestGeneratePromptRollout:
    """generate_prompt 灰度开关与埋点测试。"""

    @pytest.mark.asyncio
    async def test_backward_compat_env_var_enabled(
        self, mock_rule, mock_context, mock_prompt_cache
    ):
        """原有 LEGAL_PROMPT_FUSION_ENABLED=true 行为不变（融合应启用）。"""
        with patch(
            "core.legal_world_model.scenario_identifier_optimized.ScenarioIdentifierOptimized"
        ) as MockIdentifier:
            identifier = MockIdentifier.return_value
            identifier.identify_scenario.return_value = mock_context

            with patch(
                "core.legal_world_model.scenario_rule_retriever_optimized.ScenarioRuleRetrieverOptimized"
            ) as MockRetriever:
                retriever = MockRetriever.return_value
                retriever.retrieve_rule.return_value = mock_rule

                with patch(
                    "core.capabilities.prompt_template_cache.get_prompt_cache",
                    return_value=mock_prompt_cache,
                ):
                    with patch(
                        "core.legal_prompt_fusion.prompt_context_builder.LegalPromptContextBuilder"
                    ) as MockBuilder:
                        builder = MockBuilder.return_value
                        fusion_result = MagicMock()
                        fusion_result.system_prompt = "fused_system"
                        fusion_result.user_prompt = "fused_user"
                        fusion_result.context.evidence = []
                        fusion_result.context.legal_articles = []
                        fusion_result.context.graph_relations = []
                        fusion_result.context.wiki_background = []
                        fusion_result.context.freshness.get.return_value = "rev_1"
                        fusion_result.template_version = "v1"
                        builder.build.return_value = fusion_result

                        with patch(
                            "core.legal_prompt_fusion.metrics._send_metrics_async",
                            new_callable=AsyncMock,
                        ) as mock_send:
                            # 直接 patch _get_rollout_config 返回全开启配置（模拟向后兼容）
                            with patch(
                                "core.api.prompt_system_routes._get_rollout_config",
                                return_value=FusionRolloutConfig(
                                    global_enabled=True, traffic_percentage=100
                                ),
                            ):
                                request = PromptGenerateRequest(
                                    user_input="test query",
                                    additional_context={},
                                )
                                response = await generate_prompt(request)

                                # 验证融合 builder 被调用（向后兼容行为）
                                assert builder.build.called
                                assert response.system_prompt == "fused_system"
                                assert response.user_prompt == "fused_user"
                                # 验证指标被发送
                                assert mock_send.called

    @pytest.mark.asyncio
    async def test_config_overrides_env_var(
        self, mock_rule, mock_context, mock_prompt_cache
    ):
        """灰度配置文件可覆盖环境变量（模拟配置 global_enabled=false）。"""
        with patch(
            "core.legal_world_model.scenario_identifier_optimized.ScenarioIdentifierOptimized"
        ) as MockIdentifier:
            identifier = MockIdentifier.return_value
            identifier.identify_scenario.return_value = mock_context

            with patch(
                "core.legal_world_model.scenario_rule_retriever_optimized.ScenarioRuleRetrieverOptimized"
            ) as MockRetriever:
                retriever = MockRetriever.return_value
                retriever.retrieve_rule.return_value = mock_rule

                with patch(
                    "core.capabilities.prompt_template_cache.get_prompt_cache",
                    return_value=mock_prompt_cache,
                ):
                    with patch(
                        "core.legal_prompt_fusion.prompt_context_builder.LegalPromptContextBuilder"
                    ) as MockBuilder:
                        builder = MockBuilder.return_value

                        with patch(
                            "core.legal_prompt_fusion.metrics._send_metrics_async",
                            new_callable=AsyncMock,
                        ) as mock_send:
                            # 模拟配置覆盖：global_enabled=false
                            with patch(
                                "core.api.prompt_system_routes._get_rollout_config",
                                return_value=FusionRolloutConfig(
                                    global_enabled=False, traffic_percentage=0
                                ),
                            ):
                                request = PromptGenerateRequest(
                                    user_input="test query",
                                    additional_context={},
                                )
                                response = await generate_prompt(request)

                                # 配置文件 global_enabled=false，融合不应被调用
                                assert not builder.build.called
                                assert response.system_prompt == "system_prompt"
                                assert response.user_prompt == "user_prompt"
                                # 验证基线指标被发送
                                assert mock_send.called
                                # 确认 fusion_enabled=false
                                call_args = mock_send.call_args[0][0]
                                assert call_args.fusion_enabled is False

    @pytest.mark.asyncio
    async def test_fusion_enabled_produces_metrics(
        self, mock_rule, mock_context, mock_prompt_cache
    ):
        """融合开启请求 100% 产生指标记录。"""
        with patch(
            "core.legal_world_model.scenario_identifier_optimized.ScenarioIdentifierOptimized"
        ) as MockIdentifier:
            identifier = MockIdentifier.return_value
            identifier.identify_scenario.return_value = mock_context

            with patch(
                "core.legal_world_model.scenario_rule_retriever_optimized.ScenarioRuleRetrieverOptimized"
            ) as MockRetriever:
                retriever = MockRetriever.return_value
                retriever.retrieve_rule.return_value = mock_rule

                with patch(
                    "core.capabilities.prompt_template_cache.get_prompt_cache",
                    return_value=mock_prompt_cache,
                ):
                    with patch(
                        "core.legal_prompt_fusion.prompt_context_builder.LegalPromptContextBuilder"
                    ) as MockBuilder:
                        builder = MockBuilder.return_value
                        fusion_result = MagicMock()
                        fusion_result.system_prompt = "fused_system"
                        fusion_result.user_prompt = "fused_user"
                        fusion_result.context.evidence = [MagicMock(), MagicMock()]
                        fusion_result.context.legal_articles = [MagicMock()]
                        fusion_result.context.graph_relations = [MagicMock()]
                        fusion_result.context.wiki_background = []
                        fusion_result.context.freshness.get.return_value = "rev_2"
                        fusion_result.template_version = "v2"
                        builder.build.return_value = fusion_result

                        with patch(
                            "core.legal_prompt_fusion.metrics._send_metrics_async",
                            new_callable=AsyncMock,
                        ) as mock_send:
                            with patch(
                                "core.api.prompt_system_routes._get_rollout_config",
                                return_value=FusionRolloutConfig(
                                    global_enabled=True, traffic_percentage=100
                                ),
                            ):
                                request = PromptGenerateRequest(
                                    user_input="test query",
                                    additional_context={},
                                )
                                response = await generate_prompt(request)

                                assert response.system_prompt == "fused_system"
                                assert mock_send.called
                                metrics = mock_send.call_args[0][0]
                                assert metrics.fusion_enabled is True
                                assert metrics.evidence_count == 2
                                assert metrics.evidence_by_source == {
                                    "postgres": 1,
                                    "neo4j": 1,
                                    "wiki": 0,
                                }
                                assert metrics.cache_hit is False
                                assert metrics.latency_ms > 0
                                assert metrics.wiki_revision == "rev_2"
                                assert metrics.template_version == "v2"

    @pytest.mark.asyncio
    async def test_fusion_disabled_produces_baseline_metrics(
        self, mock_rule, mock_context, mock_prompt_cache
    ):
        """融合关闭请求产生基线记录。"""
        with patch(
            "core.legal_world_model.scenario_identifier_optimized.ScenarioIdentifierOptimized"
        ) as MockIdentifier:
            identifier = MockIdentifier.return_value
            identifier.identify_scenario.return_value = mock_context

            with patch(
                "core.legal_world_model.scenario_rule_retriever_optimized.ScenarioRuleRetrieverOptimized"
            ) as MockRetriever:
                retriever = MockRetriever.return_value
                retriever.retrieve_rule.return_value = mock_rule

                with patch(
                    "core.capabilities.prompt_template_cache.get_prompt_cache",
                    return_value=mock_prompt_cache,
                ):
                    with patch(
                        "core.legal_prompt_fusion.metrics._send_metrics_async",
                        new_callable=AsyncMock,
                    ) as mock_send:
                        with patch(
                            "core.api.prompt_system_routes._get_rollout_config",
                            return_value=FusionRolloutConfig(
                                global_enabled=False, traffic_percentage=0
                            ),
                        ):
                            request = PromptGenerateRequest(
                                user_input="test query",
                                additional_context={},
                            )
                            response = await generate_prompt(request)

                            assert response.system_prompt == "system_prompt"
                            assert mock_send.called
                            metrics = mock_send.call_args[0][0]
                            assert metrics.fusion_enabled is False
                            assert metrics.latency_ms == 0.0
                            assert metrics.evidence_count == 0
                            assert metrics.cache_hit is False

    @pytest.mark.asyncio
    async def test_metrics_send_failure_non_blocking(
        self, mock_rule, mock_context, mock_prompt_cache
    ):
        """指标发送失败不阻断主链路。"""
        with patch(
            "core.legal_world_model.scenario_identifier_optimized.ScenarioIdentifierOptimized"
        ) as MockIdentifier:
            identifier = MockIdentifier.return_value
            identifier.identify_scenario.return_value = mock_context

            with patch(
                "core.legal_world_model.scenario_rule_retriever_optimized.ScenarioRuleRetrieverOptimized"
            ) as MockRetriever:
                retriever = MockRetriever.return_value
                retriever.retrieve_rule.return_value = mock_rule

                with patch(
                    "core.capabilities.prompt_template_cache.get_prompt_cache",
                    return_value=mock_prompt_cache,
                ):
                    with patch(
                        "core.legal_prompt_fusion.metrics._send_metrics_async",
                        side_effect=RuntimeError("metrics sender failed"),
                    ) as mock_send:
                        with patch(
                            "core.api.prompt_system_routes._get_rollout_config",
                            return_value=FusionRolloutConfig(
                                global_enabled=False, traffic_percentage=0
                            ),
                        ):
                            request = PromptGenerateRequest(
                                user_input="test query",
                                additional_context={},
                            )
                            # 不应抛出异常
                            response = await generate_prompt(request)
                            assert response.system_prompt == "system_prompt"
                            assert mock_send.called

    @pytest.mark.asyncio
    async def test_fusion_failure_fallback(
        self, mock_rule, mock_context, mock_prompt_cache
    ):
        """融合 builder 异常时回退到原逻辑，并记录 error。"""
        with patch(
            "core.legal_world_model.scenario_identifier_optimized.ScenarioIdentifierOptimized"
        ) as MockIdentifier:
            identifier = MockIdentifier.return_value
            identifier.identify_scenario.return_value = mock_context

            with patch(
                "core.legal_world_model.scenario_rule_retriever_optimized.ScenarioRuleRetrieverOptimized"
            ) as MockRetriever:
                retriever = MockRetriever.return_value
                retriever.retrieve_rule.return_value = mock_rule

                with patch(
                    "core.capabilities.prompt_template_cache.get_prompt_cache",
                    return_value=mock_prompt_cache,
                ):
                    with patch(
                        "core.legal_prompt_fusion.prompt_context_builder.LegalPromptContextBuilder"
                    ) as MockBuilder:
                        builder = MockBuilder.return_value
                        builder.build.side_effect = RuntimeError("fusion failed")

                        with patch(
                            "core.legal_prompt_fusion.metrics._send_metrics_async",
                            new_callable=AsyncMock,
                        ) as mock_send:
                            with patch(
                                "core.api.prompt_system_routes._get_rollout_config",
                                return_value=FusionRolloutConfig(
                                    global_enabled=True, traffic_percentage=100
                                ),
                            ):
                                request = PromptGenerateRequest(
                                    user_input="test query",
                                    additional_context={},
                                )
                                response = await generate_prompt(request)

                                # 回退到规则变量替换
                                assert response.system_prompt == "system_prompt"
                                assert response.user_prompt == "user_prompt"
                                assert mock_send.called
                                metrics = mock_send.call_args[0][0]
                                assert metrics.fusion_enabled is True
                                assert metrics.error == "fusion failed"
                                assert metrics.latency_ms > 0

    @pytest.mark.asyncio
    async def test_cache_hit_sends_baseline_metrics(
        self, mock_rule, mock_context
    ):
        """缓存命中时也发送基线指标。"""
        cache = MagicMock()
        cache.get.return_value = ("cached_system", "cached_user")

        with patch(
            "core.legal_world_model.scenario_identifier_optimized.ScenarioIdentifierOptimized"
        ) as MockIdentifier:
            identifier = MockIdentifier.return_value
            identifier.identify_scenario.return_value = mock_context

            with patch(
                "core.legal_world_model.scenario_rule_retriever_optimized.ScenarioRuleRetrieverOptimized"
            ) as MockRetriever:
                retriever = MockRetriever.return_value
                retriever.retrieve_rule.return_value = mock_rule

                with patch(
                    "core.capabilities.prompt_template_cache.get_prompt_cache",
                    return_value=cache,
                ):
                    with patch(
                        "core.legal_prompt_fusion.metrics._send_metrics_async",
                        new_callable=AsyncMock,
                    ) as mock_send:
                        with patch(
                            "core.api.prompt_system_routes._get_rollout_config",
                            return_value=FusionRolloutConfig(
                                global_enabled=True, traffic_percentage=100
                            ),
                        ):
                            request = PromptGenerateRequest(
                                user_input="test query",
                                additional_context={},
                            )
                            response = await generate_prompt(request)

                            assert response.system_prompt == "cached_system"
                            assert response.cached is True
                            assert mock_send.called
                            metrics = mock_send.call_args[0][0]
                            assert metrics.cache_hit is True
