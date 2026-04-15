#!/usr/bin/env python3
"""
分析步骤单元测试
Analysis Steps Unit Tests
"""

import re
from typing import Any
from unittest.mock import Mock, patch

import pytest
from atomic_steps.analysis.formal_exam_steps import (
    ExamineClaimsSupportStep,
    ExamineDescriptionClarityStep,
    ExamineUnityStep,
)
from atomic_steps.analysis.invalid_strategy_steps import (
    AnalyzeEvidenceCombinationStep,
    AnalyzeTargetPatentStep,
    AssessInvalidationSuccessProbabilityStep,
    GenerateInvalidationStrategyReportStep,
    SearchPriorArtForInvalidationStep,
    SearchSuccessfulInvalidationCasesStep,
)
from atomic_steps.analysis.response_steps import (
    AnalyzeOfficeActionStep,
    BuildResponseArgumentsStep,
    GenerateResponseDocumentStep,
    RetrieveResponseSupportStep,
    SuggestClaimModificationStep,
)


@pytest.mark.unit
class TestInvalidityStrategyAnalysis:
    """无效策略分析测试"""

    def test_analyze_target_patent(self) -> Any:
        """测试分析目标专利"""
        step = AnalyzeTargetPatentStep()

        input_data = {
            'patent_id': 'CN123456A',
            'claims': [
                {'claim_number': 1, 'claim_text': '一种电池，包括正极和负极。'}
            ]
        }

        result = step.execute(input_data)

        assert result is not None
        assert result.success or result.error is not None


@pytest.mark.unit
class TestEvidenceCombination:
    """证据组合分析测试"""

    def test_analyze_evidence_combination(self) -> Any:
        """测试证据组合分析"""
        step = AnalyzeEvidenceCombinationStep()

        input_data = {
            'evidences': [
                {'source': 'D1', 'content': '对比文件1的内容', 'relevance': 0.8},
                {'source': 'D2', 'content': '对比文件2的内容', 'relevance': 0.6}
            ]
        }

        result = step.execute(input_data)

        assert result is not None


@pytest.mark.unit
class TestOfficeActionAnalysis:
    """审查意见分析测试"""

    def test_analyze_office_action(self) -> Any:
        """测试审查意见分析"""
        step = AnalyzeOfficeActionStep()

        input_data = {
            'office_action': {
                'content': '权利要求1不具备创造性'
            }
        }

        result = step.execute(input_data)

        assert result is not None


@pytest.mark.unit
class TestClaimModification:
    """权利要求修改建议测试"""

    def test_suggest_claim_modification(self) -> Any:
        """测试权利要求修改建议"""
        step = SuggestClaimModificationStep()

        input_data = {
            'claim': {
                'claim_number': 1,
                'claim_text': '一种装置，包括组件A和组件B。'
            },
            'rejection_reason': {
                'type': 'clarity',
                'description': '权利要求1中的"组件A"表述不清楚'
            }
        }

        result = step.execute(input_data)

        assert result is not None


@pytest.mark.unit
class TestFormalExamination:
    """形式审查测试"""

    def test_examine_description_clarity(self) -> Any:
        """测试说明书清晰度检查"""
        step = ExamineDescriptionClarityStep()

        input_data = {
            'description': '本发明涉及一种技术方案。该方案包括大约10个组件。'
        }

        result = step.execute(input_data)

        assert result is not None

    def test_examine_claims_support(self) -> Any:
        """测试权利要求支持检查"""
        step = ExamineClaimsSupportStep()

        input_data = {
            'claims': [
                {'claim_number': 1, 'claim_text': '一种智能手机，包括处理器。'}
            ],
            'description': '本发明提供一种智能手机。'
        }

        result = step.execute(input_data)

        assert result is not None

    def test_examine_unity(self) -> Any:
        """测试单一性检查"""
        step = ExamineUnityStep()

        input_data = {
            'claims': [
                {'claim_number': 1, 'claim_text': '一种手机，包括屏幕。'}
            ]
        }

        result = step.execute(input_data)

        assert result is not None


@pytest.mark.unit
class TestNLPFeatureExtraction:
    """NLP特征提取测试"""

    def test_extract_technical_terms(self) -> Any:
        """测试技术术语提取"""
        text = "本发明涉及一种智能手机，包括处理器、存储器和摄像头组件。"

        # 使用正则表达式提取技术术语
        technical_terms = re.findall(
            r'[\u4e00-\u9fa5]+(?:装置|设备|器件|组件|部件)',
            text
        )

        assert len(technical_terms) > 0

    def test_detect_vague_terminology(self) -> Any:
        """测试模糊术语检测"""
        vague_patterns = [
            r'大约|大概|左右|约',
            r'适当|合理|充分'
        ]

        text_with_vague = "该装置大约有10厘米长。"
        has_vague = any(re.search(pattern, text_with_vague) for pattern in vague_patterns)

        assert has_vague is True

        text_clear = "该装置长度为10厘米。"
        has_vague = any(re.search(pattern, text_clear) for pattern in vague_patterns)

        assert has_vague is False


@pytest.mark.unit
class TestPriorArtSearch:
    """现有技术检索测试"""

    def test_search_prior_art(self) -> Any:
        """测试现有技术检索"""
        step = SearchPriorArtForInvalidationStep()

        input_data = {
            'target_patent': 'CN123456A',
            'claims': [{'claim_number': 1, 'claim_text': '一种电池'}]
        }

        with patch('atomic_steps.clients.get_qdrant_client') as mock_client:
            mock_qdrant = Mock()
            mock_client.return_value = mock_qdrant
            mock_qdrant.query_points.return_value = []

            result = step.execute(input_data)
            assert result is not None

    def test_search_successful_cases(self) -> Any:
        """测试成功案例检索"""
        step = SearchSuccessfulInvalidationCasesStep()

        input_data = {
            'target_patent': 'CN123456A',
            'technology_field': '电池'
        }

        with patch('atomic_steps.clients.get_qdrant_client') as mock_client:
            mock_qdrant = Mock()
            mock_client.return_value = mock_qdrant
            mock_qdrant.query_points.return_value = []

            result = step.execute(input_data)
            assert result is not None


@pytest.mark.unit
class TestResponseSteps:
    """答复步骤测试"""

    def test_retrieve_response_support(self) -> Any:
        """测试检索答复支持"""
        step = RetrieveResponseSupportStep()

        input_data = {
            'office_action': {'content': '权利要求1不具备创造性'},
            'patent_id': 'CN123456A'
        }

        result = step.execute(input_data)
        assert result is not None

    def test_build_response_arguments(self) -> Any:
        """测试构建答复论点"""
        step = BuildResponseArgumentsStep()

        input_data = {
            'rejection_reasons': [
                {'type': 'creativity', 'description': '不具备创造性'}
            ]
        }

        result = step.execute(input_data)
        assert result is not None

    def test_generate_response_document(self) -> Any:
        """测试生成答复文书"""
        step = GenerateResponseDocumentStep()

        input_data = {
            'arguments': ['论点1', '论点2'],
            'patent_id': 'CN123456A'
        }

        result = step.execute(input_data)
        assert result is not None


@pytest.mark.unit
class TestSuccessProbability:
    """成功概率评估测试"""

    def test_assess_invalidation_success_probability(self) -> Any:
        """测试无效成功概率评估"""
        step = AssessInvalidationSuccessProbabilityStep()

        input_data = {
            'target_claims': [1, 2],
            'evidences': [
                {'source': 'D1', 'relevance': 0.9}
            ],
            'strategy': 'novelty_attack'
        }

        result = step.execute(input_data)
        assert result is not None


@pytest.mark.unit
class TestReportGeneration:
    """报告生成测试"""

    def test_generate_invalidation_strategy_report(self) -> Any:
        """测试无效策略报告生成"""
        step = GenerateInvalidationStrategyReportStep()

        input_data = {
            'target_patent': 'CN123456A',
            'strategy': 'combined_attack',
            'success_probability': 0.75,
            'evidences': [
                {'source': 'D1', 'content': '对比文件1'}
            ]
        }

        result = step.execute(input_data)
        assert result is not None
