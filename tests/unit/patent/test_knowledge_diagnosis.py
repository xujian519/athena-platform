"""
知识激活诊断系统单元测试
Unit tests for Knowledge Activation Diagnosis System

基于论文 "Missing vs. Unused Knowledge in Large Language Models" (2025)
"""

import sys
from pathlib import Path

import pytest

# 添加项目根目录到sys.path
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from unittest.mock import MagicMock

from core.patents.ai_services.knowledge_diagnosis import (
    ActivationSession,
    ActivationStrategy,
    ClarificationQuestion,
    DiagnosisResult,
    DiagnosisSeverity,
    ErrorType,
    KnowledgeActivationDiagnoser,
    OptimizationRecommendation,
    activate_and_improve,
    diagnose_response,
    format_diagnosis_report,
)

# ==================== 枚举测试 ====================

class TestEnums:
    """枚举类型测试"""

    def test_error_type_values(self):
        """测试错误类型枚举"""
        assert ErrorType.KNOWLEDGE_MISSING.value == "knowledge_missing"
        assert ErrorType.KNOWLEDGE_UNUSED.value == "knowledge_unused"
        assert ErrorType.KNOWLEDGE_MISAPPLIED.value == "knowledge_misapplied"
        assert ErrorType.REASONING_ERROR.value == "reasoning_error"
        assert ErrorType.AMBIGUITY.value == "ambiguity"

    def test_diagnosis_severity_values(self):
        """测试诊断严重程度枚举"""
        assert DiagnosisSeverity.CRITICAL.value == "critical"
        assert DiagnosisSeverity.HIGH.value == "high"
        assert DiagnosisSeverity.MEDIUM.value == "medium"
        assert DiagnosisSeverity.LOW.value == "low"

    def test_activation_strategy_values(self):
        """测试激活策略枚举"""
        assert ActivationStrategy.CLARIFICATION.value == "clarification"
        assert ActivationStrategy.SELF_ANSWERING.value == "self_answering"
        assert ActivationStrategy.DECOMPOSITION.value == "decomposition"
        assert ActivationStrategy.CHAIN_OF_THOUGHT.value == "chain_of_thought"


# ==================== 数据结构测试 ====================

class TestClarificationQuestion:
    """ClarificationQuestion 数据结构测试"""

    def test_question_creation(self):
        """测试澄清问题创建"""
        question = ClarificationQuestion(
            question_id="Q1",
            question="您指的是哪种类型的专利？",
            purpose="确定专利类型",
            expected_info="专利类型信息",
            priority=1
        )
        assert question.question_id == "Q1"
        assert question.priority == 1

    def test_question_to_dict(self):
        """测试澄清问题序列化"""
        question = ClarificationQuestion(
            question_id="Q2",
            question="请提供更多上下文",
            purpose="获取背景信息",
            expected_info="背景信息"
        )
        result = question.to_dict()
        assert result["question_id"] == "Q2"
        assert result["priority"] == 1  # 默认值


class TestOptimizationRecommendation:
    """OptimizationRecommendation 数据结构测试"""

    def test_recommendation_creation(self):
        """测试优化建议创建"""
        recommendation = OptimizationRecommendation(
            recommendation_id="R1",
            strategy=ActivationStrategy.CLARIFICATION,
            description="添加澄清问题",
            implementation="在回答前先问问题",
            expected_improvement="提高准确性",
            priority=DiagnosisSeverity.HIGH
        )
        assert recommendation.strategy == ActivationStrategy.CLARIFICATION
        assert recommendation.priority == DiagnosisSeverity.HIGH

    def test_recommendation_to_dict(self):
        """测试优化建议序列化"""
        recommendation = OptimizationRecommendation(
            recommendation_id="R2",
            strategy=ActivationStrategy.CHAIN_OF_THOUGHT,
            description="使用思维链",
            implementation="逐步推理",
            expected_improvement="提高推理质量",
            priority=DiagnosisSeverity.MEDIUM
        )
        result = recommendation.to_dict()
        assert result["strategy"] == "chain_of_thought"
        assert result["priority"] == "medium"


class TestDiagnosisResult:
    """DiagnosisResult 数据结构测试"""

    def test_result_creation(self):
        """测试诊断结果创建"""
        result = DiagnosisResult(
            diagnosis_id="diag_001",
            error_type=ErrorType.KNOWLEDGE_UNUSED,
            severity=DiagnosisSeverity.HIGH,
            error_description="模型知道但未正确使用知识",
            evidence=["回答包含模糊表述"],
            confidence=0.85
        )
        assert result.diagnosis_id == "diag_001"
        assert result.error_type == ErrorType.KNOWLEDGE_UNUSED
        assert len(result.evidence) == 1

    def test_result_to_dict(self):
        """测试诊断结果序列化"""
        result = DiagnosisResult(
            diagnosis_id="diag_002",
            error_type=ErrorType.AMBIGUITY,
            severity=DiagnosisSeverity.MEDIUM,
            error_description="问题有歧义",
            evidence=["有多种解释"],
            clarification_questions=[
                ClarificationQuestion("Q1", "问题1", "目的1", "信息1")
            ],
            recommendations=[
                OptimizationRecommendation(
                    "R1",
                    ActivationStrategy.REPHRASING,
                    "重新表述",
                    "用更清晰的方式表述",
                    "消除歧义",
                    DiagnosisSeverity.LOW
                )
            ]
        )
        data = result.to_dict()
        assert data["diagnosis_id"] == "diag_002"
        assert data["error_type"] == "ambiguity"
        assert len(data["clarification_questions"]) == 1
        assert len(data["recommendations"]) == 1


class TestActivationSession:
    """ActivationSession 数据结构测试"""

    def test_session_creation(self):
        """测试激活会话创建"""
        session = ActivationSession(
            session_id="session_001",
            original_query="什么是专利？",
            original_response="我不知道"
        )
        assert session.session_id == "session_001"
        assert session.diagnosis is None

    def test_session_with_diagnosis(self):
        """测试带诊断的会话"""
        diagnosis = DiagnosisResult(
            diagnosis_id="diag_001",
            error_type=ErrorType.KNOWLEDGE_MISSING,
            severity=DiagnosisSeverity.CRITICAL,
            error_description="知识缺失",
            evidence=["模型明确表示不知道"]
        )
        session = ActivationSession(
            session_id="session_002",
            original_query="测试问题",
            original_response="我不知道",
            diagnosis=diagnosis,
            improved_response="专利是一种..."
        )
        assert session.diagnosis is not None
        assert session.improved_response != ""

    def test_session_to_dict(self):
        """测试会话序列化"""
        session = ActivationSession(
            session_id="session_003",
            original_query="问题",
            original_response="回答",
            improved_response="改进回答",
            improvement_score=0.8
        )
        data = session.to_dict()
        assert data["session_id"] == "session_003"
        assert data["improvement_score"] == 0.8


# ==================== KnowledgeActivationDiagnoser 测试 ====================

class TestKnowledgeActivationDiagnoser:
    """KnowledgeActivationDiagnoser 核心测试"""

    def test_diagnoser_initialization(self):
        """测试诊断器初始化"""
        diagnoser = KnowledgeActivationDiagnoser()
        assert diagnoser.llm_manager is None
        assert hasattr(diagnoser, 'diagnosis_prompt')
        assert hasattr(diagnoser, 'ERROR_INDICATORS')

    def test_diagnoser_with_llm_manager(self):
        """测试带LLM管理器的初始化"""
        mock_llm = MagicMock()
        diagnoser = KnowledgeActivationDiagnoser(llm_manager=mock_llm)
        assert diagnoser.llm_manager == mock_llm

    def test_quick_error_classification_missing(self):
        """测试快速错误分类 - 知识缺失"""
        diagnoser = KnowledgeActivationDiagnoser()
        response = "我不知道这个问题的答案"
        error_type = diagnoser._quick_error_classification(response)
        assert error_type == ErrorType.KNOWLEDGE_MISSING

    def test_quick_error_classification_unused(self):
        """测试快速错误分类 - 知识未激活"""
        diagnoser = KnowledgeActivationDiagnoser()
        response = "可能是这样，也许..."
        error_type = diagnoser._quick_error_classification(response)
        assert error_type == ErrorType.KNOWLEDGE_UNUSED

    def test_quick_error_classification_ambiguity(self):
        """测试快速错误分类 - 歧义"""
        diagnoser = KnowledgeActivationDiagnoser()
        response = "你是指什么？需要更多信息"
        error_type = diagnoser._quick_error_classification(response)
        assert error_type == ErrorType.AMBIGUITY

    def test_quick_error_classification_unknown(self):
        """测试快速错误分类 - 未知"""
        diagnoser = KnowledgeActivationDiagnoser()
        response = "这是一个关于专利的回答"
        error_type = diagnoser._quick_error_classification(response)
        assert error_type == ErrorType.UNKNOWN

    def test_select_activation_strategy(self):
        """测试激活策略选择"""
        diagnoser = KnowledgeActivationDiagnoser()

        # 知识缺失 -> 分解
        diagnosis = DiagnosisResult(
            diagnosis_id="test",
            error_type=ErrorType.KNOWLEDGE_MISSING,
            severity=DiagnosisSeverity.HIGH,
            error_description="test",
            evidence=["测试证据"]
        )
        strategy = diagnoser._select_activation_strategy(diagnosis)
        assert strategy == ActivationStrategy.DECOMPOSITION

        # 知识未激活 -> 澄清
        diagnosis.error_type = ErrorType.KNOWLEDGE_UNUSED
        strategy = diagnoser._select_activation_strategy(diagnosis)
        assert strategy == ActivationStrategy.CLARIFICATION

        # 推理错误 -> 思维链
        diagnosis.error_type = ErrorType.REASONING_ERROR
        strategy = diagnoser._select_activation_strategy(diagnosis)
        assert strategy == ActivationStrategy.CHAIN_OF_THOUGHT

    def test_heuristic_clarification_questions(self):
        """测试启发式澄清问题生成"""
        diagnoser = KnowledgeActivationDiagnoser()
        questions = diagnoser._heuristic_clarification_questions(
            "专利申请流程是什么？",
            "我不确定"
        )
        assert len(questions) > 0
        assert all(isinstance(q, ClarificationQuestion) for q in questions)

    def test_heuristic_clarification_questions_patent(self):
        """测试专利相关澄清问题"""
        diagnoser = KnowledgeActivationDiagnoser()
        questions = diagnoser._heuristic_clarification_questions(
            "发明专利的权利要求怎么写？",
            "可能是这样"
        )
        # 应该包含专利类型相关的澄清问题
        assert len(questions) > 0

    def test_generate_recommendations(self):
        """测试优化建议生成"""
        diagnoser = KnowledgeActivationDiagnoser()

        recommendations = diagnoser._generate_recommendations(
            ErrorType.KNOWLEDGE_MISSING,
            DiagnosisSeverity.HIGH
        )
        assert len(recommendations) > 0
        assert all(isinstance(r, OptimizationRecommendation) for r in recommendations)

    def test_calculate_improvement(self):
        """测试改进分数计算"""
        diagnoser = KnowledgeActivationDiagnoser()

        # 有标准答案的情况
        score = diagnoser._calculate_improvement(
            original="这是一个关于专利的回答",
            improved="这是一个关于发明专利的详细回答",
            ground_truth="发明专利是..."
        )
        assert 0.0 <= score <= 1.0

        # 无标准答案的情况
        score = diagnoser._calculate_improvement(
            original="短回答",
            improved="这是一个更长的详细回答",
            ground_truth=None
        )
        assert 0.0 <= score <= 1.0


# ==================== 异步方法测试 ====================

@pytest.mark.asyncio
class TestAsyncMethods:
    """异步方法测试"""

    async def test_diagnose_no_llm(self):
        """测试无LLM时的诊断"""
        diagnoser = KnowledgeActivationDiagnoser()
        result = await diagnoser.diagnose(
            query="什么是专利？",
            response="我不知道",
            ground_truth=None
        )
        assert isinstance(result, DiagnosisResult)
        assert result.error_type == ErrorType.KNOWLEDGE_MISSING

    async def test_generate_clarification_questions_no_llm(self):
        """测试无LLM时的澄清问题生成"""
        diagnoser = KnowledgeActivationDiagnoser()
        questions = await diagnoser.generate_clarification_questions(
            query="专利申请",
            response="可能需要"
        )
        assert len(questions) > 0
        assert all(isinstance(q, ClarificationQuestion) for q in questions)

    async def test_activate_knowledge_no_llm(self):
        """测试无LLM时的知识激活"""
        diagnoser = KnowledgeActivationDiagnoser()
        diagnosis = DiagnosisResult(
            diagnosis_id="test",
            error_type=ErrorType.KNOWLEDGE_UNUSED,
            severity=DiagnosisSeverity.MEDIUM,
            error_description="测试",
            evidence=["测试证据"]
        )
        improved = await diagnoser.activate_knowledge(
            query="问题",
            response="回答",
            diagnosis=diagnosis
        )
        assert isinstance(improved, str)
        assert len(improved) > 0


# ==================== 便捷函数测试 ====================

class TestConvenienceFunctions:
    """便捷函数测试"""

    @pytest.mark.asyncio
    async def test_diagnose_response(self):
        """测试便捷诊断函数"""
        result = await diagnose_response(
            query="什么是专利？",
            response="我不知道",
            ground_truth=None,
            llm_manager=None
        )
        assert isinstance(result, DiagnosisResult)

    @pytest.mark.asyncio
    async def test_activate_and_improve(self):
        """测试便捷激活函数"""
        session = await activate_and_improve(
            query="问题",
            response="回答",
            llm_manager=None
        )
        assert isinstance(session, ActivationSession)
        assert session.diagnosis is not None

    def test_format_diagnosis_report(self):
        """测试格式化诊断报告"""
        result = DiagnosisResult(
            diagnosis_id="diag_001",
            error_type=ErrorType.KNOWLEDGE_UNUSED,
            severity=DiagnosisSeverity.HIGH,
            error_description="模型知道但未正确使用知识",
            evidence=["回答包含模糊表述", "可能"],
            clarification_questions=[
                ClarificationQuestion("Q1", "澄清问题", "目的", "期望信息")
            ],
            recommendations=[
                OptimizationRecommendation(
                    "R1",
                    ActivationStrategy.CLARIFICATION,
                    "添加澄清问题",
                    "实施方法",
                    "预期改进",
                    DiagnosisSeverity.HIGH
                )
            ],
            confidence=0.85
        )
        report = format_diagnosis_report(result)
        assert "知识激活诊断报告" in report
        assert "knowledge_unused" in report
        assert "澄清问题" in report


# ==================== 边界条件测试 ====================

class TestEdgeCases:
    """边界条件测试"""

    def test_empty_response(self):
        """测试空响应"""
        diagnoser = KnowledgeActivationDiagnoser()
        error_type = diagnoser._quick_error_classification("")
        assert error_type == ErrorType.UNKNOWN

    def test_long_response(self):
        """测试长响应"""
        diagnoser = KnowledgeActivationDiagnoser()
        long_response = "这是一个很长的回答。" * 1000
        error_type = diagnoser._quick_error_classification(long_response)
        assert isinstance(error_type, ErrorType)

    def test_multiple_error_indicators(self):
        """测试多个错误指示器"""
        diagnoser = KnowledgeActivationDiagnoser()
        response = "我不知道，可能不确定，你是指什么？"
        error_type = diagnoser._quick_error_classification(response)
        # 应该返回第一个匹配的类型
        assert error_type in [ErrorType.KNOWLEDGE_MISSING, ErrorType.KNOWLEDGE_UNUSED, ErrorType.AMBIGUITY]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
