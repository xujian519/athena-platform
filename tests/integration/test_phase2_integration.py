"""
Phase 2 集成测试

测试目标:
1. 验证所有模块的导入和基本功能
2. 测试模块间的协作
3. 验证端到端工作流
"""


# 导入所有Phase 2模块
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from patents.core.ai_services.knowledge_diagnosis import (
    ActivationStrategy,
    DiagnosisResult,
    DiagnosisSeverity,
    ErrorType,
    KnowledgeActivationDiagnoser,
    diagnose_response,
)
from patents.core.ai_services.multimodal_retrieval import (
    FusionStrategy,
    ImageType,
    ImageVectorizer,
    MultimodalRetrievalSystem,
    SearchMode,
    hybrid_search,
)
from patents.core.ai_services.quality_assessment_enhanced import (
    AssessmentType,
    EnhancedQualityAssessment,
    EnhancedQualityAssessor,
    QualityDimension,
    QualityGrade,
    assess_patent_quality,
)
from patents.core.ai_services.task_classifier import (
    PatentTaskClassifier,
    PatentTaskType,
    TaskClassificationResult,
    TaskComplexity,
    WorkflowStage,
    classify_patent_task,
)

# ============================================================================
# 模块导入测试
# ============================================================================

class TestModuleImports:
    """测试所有模块是否正确导入"""

    def test_knowledge_diagnosis_imports(self):
        """测试知识诊断模块导入"""
        assert KnowledgeActivationDiagnoser is not None
        assert DiagnosisResult is not None
        assert ErrorType is not None
        assert len(ErrorType) == 6  # 6种错误类型（已优化）
        assert len(DiagnosisSeverity) == 4
        assert len(ActivationStrategy) == 5

    def test_task_classifier_imports(self):
        """测试任务分类模块导入"""
        assert PatentTaskClassifier is not None
        assert TaskClassificationResult is not None
        assert PatentTaskType is not None
        assert len(PatentTaskType) == 21  # 21种任务类型（已扩展）
        assert len(TaskComplexity) == 4
        assert len(WorkflowStage) == 5

    def test_quality_assessment_imports(self):
        """测试质量评估模块导入"""
        assert EnhancedQualityAssessor is not None
        assert EnhancedQualityAssessment is not None
        assert QualityDimension is not None
        assert len(QualityDimension) == 8  # 8个维度
        assert len(QualityGrade) == 8
        assert len(AssessmentType) == 6

    def test_multimodal_retrieval_imports(self):
        """测试多模态检索模块导入"""
        assert MultimodalRetrievalSystem is not None
        assert ImageVectorizer is not None
        assert SearchMode is not None
        assert len(SearchMode) == 5  # 5种检索模式
        assert len(ImageType) == 8
        assert len(FusionStrategy) == 5


# ============================================================================
# 模块功能测试
# ============================================================================

class TestModuleFunctions:
    """测试各模块核心功能"""

    @pytest.fixture
    def sample_patent_data(self):
        """样本专利数据"""
        return {
            "patent_number": "CN123456789A",
            "title": "基于深度学习的图像识别方法及系统",
            "abstract": "本发明公开了一种基于深度学习的图像识别方法",
            "technical_features": [
                "特征1：卷积神经网络特征提取",
                "特征2：注意力机制融合",
                "特征3：多尺度检测",
                "特征4：端到端训练",
                "特征5：实时推理优化"
            ],
            "technical_field": "人工智能深度学习",
            "embodiments": [
                "实施例1：图像分类应用",
                "实施例2：目标检测应用",
                "实施例3：语义分割应用"
            ],
            "claims": [
                {"type": "independent", "text": "一种基于深度学习的图像识别方法，包括：步骤A，提取图像特征；步骤B，融合多模态特征；步骤C，输出识别结果"},
                {"type": "dependent", "text": "根据权利要求1的方法，其中步骤B使用注意力机制"},
                {"type": "dependent", "text": "根据权利要求1的方法，其中步骤A使用卷积神经网络"},
                {"type": "independent", "text": "一种图像识别系统，包括：图像处理模块，融合模块， 输出模块"}
            ],
            "description": "详细说明书内容" * 300,
            "figures": ["图1：系统架构", "图2：流程图", "图3：网络结构", "图4：实验结果"],
            "keywords": ["深度学习", "图像识别", "注意力机制", "实时推理"],
            "filing_date": "2024-06-15"
        }

    @pytest.mark.asyncio
    async def test_knowledge_diagnosis_function(self, sample_patent_data):
        """测试知识诊断功能"""
        query = "这个专利的技术方案是什么？"
        response = "该专利使用深度学习进行图像识别。"

        result = await diagnose_response(
            query=query,
            response=response
        )

        assert result is not None
        assert result.error_type is not None
        assert result.severity is not None

    @pytest.mark.asyncio
    async def test_task_classifier_function(self):
        """测试任务分类功能"""
        query = "请帮我检索关于光伏充电的现有技术"

        result = await classify_patent_task(query)

        assert result is not None
        assert result.primary_task_type is not None
        assert result.detected_intent is not None

    @pytest.mark.asyncio
    async def test_quality_assessment_function(self, sample_patent_data):
        """测试质量评估功能"""
        result = await assess_patent_quality(
            patent_number=sample_patent_data["patent_number"],
            patent_data=sample_patent_data,
            assessment_type=AssessmentType.QUICK
        )

        assert result is not None
        assert 0 <= result.overall_score <= 100
        assert result.overall_grade is not None

    @pytest.mark.asyncio
    async def test_multimodal_retrieval_function(self):
        """测试多模态检索功能"""
        result = await hybrid_search(
            query="图像识别技术",
            mode=SearchMode.TEXT_ONLY,
            top_k=5
        )

        assert result is not None
        assert result.query == "图像识别技术"


# ============================================================================
# 模块协作测试
# ============================================================================

class TestModuleIntegration:
    """测试模块间的协作"""

    @pytest.fixture
    def integrated_system(self):
        """集成系统实例"""
        return {
            "diagnoser": KnowledgeActivationDiagnoser(),
            "classifier": PatentTaskClassifier(),
            "assessor": EnhancedQualityAssessor(),
            "retriever": MultimodalRetrievalSystem()
        }

    @pytest.mark.asyncio
    async def test_task_classification_to_diagnosis_flow(self, integrated_system):
        """测试任务分类到知识诊断的流程"""
        query = "分析这个专利的创新点"

        # 1. 分类任务
        task_result = await classify_patent_task(query)
        assert task_result.primary_task_type in [
            PatentTaskType.INVENTIVENESS_ANALYSIS,
            PatentTaskType.CLAIM_ANALYSIS,
            PatentTaskType.PATENT_QA
        ]

        # 2. 根据任务类型进行诊断
        if task_result.primary_task_type == PatentTaskType.INVENTIVENESS_ANALYSIS:
            diagnosis = await diagnose_response(
                query=query,
                response="需要分析创新性"
            )
            assert diagnosis is not None

    @pytest.mark.asyncio
    async def test_quality_assessment_with_retrieval(self, integrated_system):
        """测试质量评估与检索的协作"""
        # 1. 质量评估
        patent_data = {
            "technical_features": ["特征1", "特征2"],
            "claims": [{"type": "independent", "text": "权利要求"}],
            "description": "说明书" * 100
        }

        quality = await assess_patent_quality(
            patent_number="CN999999A",
            patent_data=patent_data,
            assessment_type=AssessmentType.QUICK
        )

        # 2. 如果质量分数低，可能需要检索对比
        if quality.overall_score < 70:
            retrieval = await hybrid_search(
                query="相关技术",
                mode=SearchMode.HYBRID,
                top_k=5
            )
            assert retrieval is not None


# ============================================================================
# 端到端工作流测试
# ============================================================================

class TestEndToEndWorkflow:
    """端到端工作流测试"""

    @pytest.fixture
    def complete_patent_data(self):
        """完整专利数据"""
        return {
            "patent_number": "CN202410000000A",
            "title": "一种智能图像处理系统",
            "abstract": "本发明涉及一种智能图像处理系统",
            "technical_features": [
                "多模态特征提取",
                "注意力融合机制",
                "端到端优化",
                "实时推理加速"
            ],
            "technical_field": "人工智能",
            "embodiments": ["实施例1", "实施例2", "实施例3"],
            "claims": [
                {"type": "independent", "text": "一种智能图像处理系统，包括特征提取模块、融合模块和处理模块"},
                {"type": "dependent", "text": "根据权利要求1的系统，特征提取模块使用卷积神经网络"},
                {"type": "dependent", "text": "根据权利要求1的系统，融合模块使用注意力机制"}
            ],
            "description": "详细说明书" * 400,
            "figures": ["图1", "图2", "图3"],
            "keywords": ["智能处理", "图像识别", "深度学习"],
            "filing_date": "2024-01-01",
            "applications": ["安防监控", "自动驾驶", "医疗影像"],
            "family_members": ["US专利", "EP专利"]
        }

    @pytest.mark.asyncio
    async def test_complete_analysis_workflow(self, complete_patent_data):
        """测试完整分析工作流"""
        query = "分析专利CN202410000000A的技术创新点和质量"

        # Step 1: 任务分类
        task_result = await classify_patent_task(query)
        assert task_result is not None
        print(f"任务类型: {task_result.primary_task_type.value}")

        # Step 2: 知识诊断
        diagnosis = await diagnose_response(
            query=query,
            response="该专利涉及智能图像处理"
        )
        assert diagnosis is not None
        print(f"诊断类型: {diagnosis.error_type.value}")

        # Step 3: 质量评估
        quality = await assess_patent_quality(
            patent_number=complete_patent_data["patent_number"],
            patent_data=complete_patent_data,
            assessment_type=AssessmentType.TECHNICAL
        )
        assert quality is not None
        print(f"质量得分: {quality.overall_score:.1f}")
        print(f"质量等级: {quality.overall_grade.value}")

        # Step 4: 相关技术检索
        retrieval = await hybrid_search(
            query="智能图像处理 深度学习",
            mode=SearchMode.HYBRID,
            top_k=5
        )
        assert retrieval is not None
        print(f"检索结果: {len(retrieval.fused_results)} 条")

        # 汇总结果
        workflow_result = {
            "task_classification": {
                "type": task_result.primary_task_type.value,
                "complexity": task_result.complexity.value
            },
            "knowledge_diagnosis": {
                "error_type": diagnosis.error_type.value,
                "severity": diagnosis.severity.value
            },
            "quality_assessment": {
                "score": quality.overall_score,
                "grade": quality.overall_grade.value,
                "risks": len(quality.risks),
                "improvements": len(quality.improvements)
            },
            "retrieval": {
                "mode": retrieval.mode.value,
                "results": len(retrieval.fused_results),
                "time": retrieval.total_time
            }
        }

        # 验证工作流完整性
        assert workflow_result["task_classification"]["type"] is not None
        assert workflow_result["quality_assessment"]["score"] >= 0
        assert workflow_result["retrieval"]["results"] >= 0

        return workflow_result

    @pytest.mark.asyncio
    async def test_error_recovery_workflow(self):
        """测试错误恢复工作流"""
        # 测试空数据处理
        empty_data = {}

        try:
            result = await classify_patent_task("")
            assert result is not None  # 应该有默认处理
        except Exception as e:
            pytest.fail(f"空查询应该被优雅处理: {e}")

        try:
            result = await assess_patent_quality(
                patent_number="",
                patent_data=empty_data,
                assessment_type=AssessmentType.QUICK
            )
            assert result is not None
        except Exception as e:
            pytest.fail(f"空数据应该被优雅处理: {e}")


# ============================================================================
# 性能测试
# ============================================================================

class TestPerformance:
    """性能基准测试"""

    @pytest.mark.asyncio
    async def test_classification_performance(self):
        """测试分类性能"""
        import time

        start = time.time()
        for _ in range(10):
            await classify_patent_task("测试查询")
        elapsed = time.time() - start

        avg_time = elapsed / 10
        assert avg_time < 1.0, f"平均分类时间应小于1秒，实际: {avg_time:.3f}s"
        print(f"平均分类时间: {avg_time*1000:.1f}ms")

    @pytest.mark.asyncio
    async def test_assessment_performance(self):
        """测试评估性能"""
        import time

        patent_data = {
            "technical_features": ["特征1"],
            "claims": [{"type": "independent", "text": "权利要求"}],
            "description": "说明书" * 100
        }

        start = time.time()
        await assess_patent_quality(
            patent_number="CN_TEST",
            patent_data=patent_data,
            assessment_type=AssessmentType.QUICK
        )
        elapsed = time.time() - start

        assert elapsed < 5.0, f"评估时间应小于5秒，实际: {elapsed:.3f}s"
        print(f"评估时间: {elapsed*1000:.1f}ms")


# ============================================================================
# 运行测试
# ============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s", "--tb=short"])
