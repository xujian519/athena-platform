#!/usr/bin/env python3
"""
评估模块测试用例
Evaluation Module Tests

测试评估模块的核心功能，包括:
- 基础评估引擎
- 增强评估模块
- 质量评估器
- 反思系统
- 专利检索指标

作者: Athena AI系统
版本: v1.0.0
创建时间: 2026-01-30
"""

import asyncio
import pytest
from unittest.mock import AsyncMock, MagicMock

import sys
from pathlib import Path

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))


# =============================================================================
# === 基础评估引擎测试 ===
# =============================================================================

class TestEvaluationEngine:
    """基础评估引擎测试"""

    @pytest.fixture
    def engine(self):
        from core.evaluation import EvaluationEngine
        return EvaluationEngine(agent_id="test_agent", config={"test": True})

    def test_initialization(self, engine):
        """测试引擎初始化"""
        assert engine.agent_id == "test_agent"
        assert engine.config == {"test": True}
        assert engine.initialized is False

    @pytest.mark.asyncio
    async def test_initialize(self, engine):
        """测试引擎启动"""
        await engine.initialize()
        assert engine.initialized is True

    @pytest.mark.asyncio
    async def test_evaluate(self, engine):
        """测试评估功能"""
        await engine.initialize()
        result = await engine.evaluate({"test": "data"})
        assert "score" in result
        assert "feedback" in result

    def test_register_callback(self, engine):
        """测试注册回调函数"""
        callback = MagicMock()
        engine.register_callback("evaluation_complete", callback)
        assert "evaluation_complete" in engine._callbacks
        assert callback in engine._callbacks["evaluation_complete"]

    @pytest.mark.asyncio
    async def test_shutdown(self, engine):
        """测试引擎关闭"""
        await engine.initialize()
        await engine.shutdown()
        assert engine.initialized is False

    @pytest.mark.asyncio
    async def test_global_instance(self):
        """测试全局实例"""
        from core.evaluation import EvaluationEngine
        instance1 = await EvaluationEngine.initialize_global()
        instance2 = await EvaluationEngine.initialize_global()
        assert instance1 is instance2
        await EvaluationEngine.shutdown_global()


# =============================================================================
# === 增强评估模块测试 ===
# =============================================================================

class TestEnhancedEvaluationModule:
    """增强评估模块测试"""

    @pytest.fixture
    def enhanced_module_available(self):
        try:
            from core.evaluation import EnhancedEvaluationModule
            return True
        except ImportError:
            return False

    @pytest.mark.asyncio
    async def test_enhanced_module_initialization(self, enhanced_module_available):
        """测试增强模块初始化"""
        if not enhanced_module_available:
            pytest.skip("EnhancedEvaluationModule not available")
        from core.evaluation import EnhancedEvaluationModule
        module = EnhancedEvaluationModule(agent_id="test_agent")
        await module.initialize()
        assert module.initialized is True
        await module.shutdown()

    @pytest.mark.asyncio
    async def test_evaluation_task(self, enhanced_module_available):
        """测试评估任务"""
        if not enhanced_module_available:
            pytest.skip("EnhancedEvaluationModule not available")
        from core.evaluation import EnhancedEvaluationModule, EvaluationTask
        module = EnhancedEvaluationModule(agent_id="test_agent")
        await module.initialize()

        task = EvaluationTask(
            id="test_task_001",
            target_type="response",
            target_id="test_001",
            evaluation_type="quality",
            criteria=[
                {"dimension": "accuracy", "weight": 0.4},
                {"dimension": "completeness", "weight": 0.3},
                {"dimension": "relevance", "weight": 0.3}
            ]
        )

        result = await module.evaluate_task(task)
        assert result["success"] is True
        assert 0 <= result["score"] <= 1

        await module.shutdown()


# =============================================================================
# === 增强质量评估器测试 ===
# =============================================================================

class TestEnhancedQualityAssessor:
    """增强质量评估器测试"""

    @pytest.fixture
    def quality_assessor_available(self):
        try:
            from core.evaluation import EnhancedQualityAssessor
            return True
        except ImportError:
            return False

    def test_quality_assessor_import(self, quality_assessor_available):
        """测试质量评估器导入"""
        if not quality_assessor_available:
            pytest.skip("EnhancedQualityAssessor not available")
        from core.evaluation import (
            EnhancedQualityAssessor,
            AssessmentCriteria,
            AssessmentDimension,
            QualityMetrics,
            QualityReport,
        )
        assert EnhancedQualityAssessor is not None
        assert AssessmentCriteria is not None
        assert AssessmentDimension is not None
        assert QualityMetrics is not None
        assert QualityReport is not None

    @pytest.mark.asyncio
    async def test_quality_assessment(self, quality_assessor_available):
        """测试质量评估"""
        if not quality_assessor_available:
            pytest.skip("EnhancedQualityAssessor not available")
        from core.evaluation import EnhancedQualityAssessor
        assessor = EnhancedQualityAssessor()
        await assessor.initialize()

        # 测试内容质量评估
        result = await assessor.assess_content_quality(
            content="这是一个测试内容，用于评估质量。",
            context={"domain": "general"}
        )
        assert result is not None
        assert "overall_score" in result

        await assessor.shutdown()


# =============================================================================
# === 评估引擎子模块测试 ===
# =============================================================================

class TestEvaluationEngineSubmodules:
    """评估引擎子模块测试"""

    @pytest.fixture
    def submodules_available(self):
        try:
            from core.evaluation import BatchEvaluator, SequentialEvaluator
            return True
        except ImportError:
            return False

    def test_batch_evaluator(self, submodules_available):
        """测试批量评估器"""
        if not submodules_available:
            pytest.skip("EvaluationEngine submodules not available")
        from core.evaluation import BatchEvaluator
        assert BatchEvaluator is not None

    def test_sequential_evaluator(self, submodules_available):
        """测试顺序评估器"""
        if not submodules_available:
            pytest.skip("EvaluationEngine submodules not available")
        from core.evaluation import SequentialEvaluator
        assert SequentialEvaluator is not None

    def test_qa_checker(self, submodules_available):
        """测试QA检查器"""
        if not submodules_available:
            pytest.skip("EvaluationEngine submodules not available")
        from core.evaluation import QAChecker
        assert QAChecker is not None

    def test_reflection_types(self, submodules_available):
        """测试反思类型"""
        if not submodules_available:
            pytest.skip("EvaluationEngine submodules not available")
        from core.evaluation import ReflectionRecord, ReflectionType
        assert ReflectionRecord is not None
        assert ReflectionType is not None


# =============================================================================
# === 专利检索指标测试 ===
# =============================================================================

class TestPatentRetrievalMetrics:
    """专利检索指标测试"""

    @pytest.fixture
    def patent_metrics_available(self):
        try:
            from core.evaluation import PatentRetrievalMetrics
            return True
        except ImportError:
            return False

    def test_patent_metrics_import(self, patent_metrics_available):
        """测试专利指标导入"""
        if not patent_metrics_available:
            pytest.skip("PatentRetrievalMetrics not available")
        from core.evaluation import (
            PatentRetrievalMetrics,
            RetrievalQualityAssessor,
        )
        assert PatentRetrievalMetrics is not None
        assert RetrievalQualityAssessor is not None

    @pytest.mark.asyncio
    async def test_retrieval_quality_assessment(self, patent_metrics_available):
        """测试检索质量评估"""
        if not patent_metrics_available:
            pytest.skip("PatentRetrievalMetrics not available")
        from core.evaluation import RetrievalQualityAssessor
        assessor = RetrievalQualityAssessor()
        await assessor.initialize()

        # 模拟检索结果
        retrieved_docs = [
            {"id": "1", "relevance": 0.9},
            {"id": "2", "relevance": 0.7},
            {"id": "3", "relevance": 0.5},
        ]

        metrics = await assessor.assess_retrieval_quality(
            retrieved_docs=retrieved_docs,
            query="测试查询",
            total_retrieved=100
        )
        assert metrics is not None
        assert "precision" in metrics or "quality_score" in metrics

        await assessor.shutdown()


# =============================================================================
# === 反馈系统测试 ===
# =============================================================================

class TestFeedbackSystem:
    """反馈系统测试"""

    @pytest.fixture
    def feedback_system_available(self):
        try:
            from core.evaluation import XiaonuoFeedbackSystem
            return True
        except ImportError:
            return False

    def test_feedback_system_import(self, feedback_system_available):
        """测试反馈系统导入"""
        if not feedback_system_available:
            pytest.skip("XiaonuoFeedbackSystem not available")
        from core.evaluation import (
            XiaonuoFeedbackSystem,
            FeedbackCollector,
            FeedbackProcessor,
        )
        assert XiaonuoFeedbackSystem is not None
        assert FeedbackCollector is not None
        assert FeedbackProcessor is not None

    @pytest.mark.asyncio
    async def test_feedback_collection(self, feedback_system_available):
        """测试反馈收集"""
        if not feedback_system_available:
            pytest.skip("XiaonuoFeedbackSystem not available")
        from core.evaluation import FeedbackCollector
        collector = FeedbackCollector()
        await collector.initialize()

        # 收集反馈
        feedback = await collector.collect_feedback(
            task_id="test_task",
            user_id="test_user",
            rating=5,
            comment="很好用的功能"
        )
        assert feedback is not None

        await collector.shutdown()


# =============================================================================
# === 模块可用性测试 ===
# =============================================================================

class TestModuleCapabilities:
    """模块可用性测试"""

    def test_get_module_capabilities(self):
        """测试获取模块能力"""
        from core.evaluation import get_module_capabilities
        capabilities = get_module_capabilities()
        assert isinstance(capabilities, dict)
        assert "enhanced_evaluation" in capabilities
        assert "quality_assessor" in capabilities
        assert "full_engine" in capabilities
        assert "patent_metrics" in capabilities
        assert "feedback_system" in capabilities

    def test_get_available_features(self):
        """测试获取可用功能"""
        from core.evaluation import get_available_features
        features = get_available_features()
        assert isinstance(features, list)


# =============================================================================
# === 集成测试 ===
# =============================================================================

class TestEvaluationIntegration:
    """评估模块集成测试"""

    @pytest.mark.asyncio
    async def test_evaluation_pipeline(self):
        """测试完整评估流程"""
        from core.evaluation import EvaluationEngine
        engine = EvaluationEngine(agent_id="integration_test")

        # 初始化
        await engine.initialize()
        assert engine.initialized is True

        # 执行评估
        test_data = {
            "content": "这是一篇关于人工智能的技术文章。",
            "context": {"domain": "technology"}
        }
        result = await engine.evaluate(test_data)
        assert "score" in result

        # 关闭
        await engine.shutdown()
        assert engine.initialized is False


# =============================================================================
# === 性能测试 ===
# =============================================================================

class TestEvaluationPerformance:
    """评估模块性能测试"""

    @pytest.mark.asyncio
    @pytest.mark.benchmark(group="evaluation")
    async def test_evaluation_performance(self, benchmark):
        """测试评估性能"""
        from core.evaluation import EvaluationEngine
        engine = EvaluationEngine(agent_id="perf_test")
        await engine.initialize()

        async def evaluate_items():
            for i in range(100):
                await engine.evaluate({"item": i, "data": "test"})

        await benchmark(evaluate_items)
        await engine.shutdown()


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
