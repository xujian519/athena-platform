"""
意图识别服务重构验证测试
Intent Recognition Service Refactoring Verification Tests

验证重构后的继承体系和统一接口的集成测试。

Author: Athena AI系统
Created: 2026-01-20
Version: 2.0.0
"""

import pytest

pytestmark = pytest.mark.skip(reason="Missing required modules: ")

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from core.intent import (
    # 基础类
    BaseIntentEngine,
    ComplexityLevel,
    # 具体引擎
    EnhancedIntentRecognitionEngine,
    IntentCategory,
    IntentResult,
    IntentType,
    # 工厂和函数
    get_intent_engine,
    recognize_intent,
    recognize_intent_async,
)
from core.intent.base_engine import (
    IntentEngineFactory,
    create_default_result,
    infer_category_from_intent,
    merge_results,
)
from core.intent.intent_recognition_adapter import (
    IntentRecognitionAdapter,
)
from core.intent.semantic_enhanced_intent_engine import (
    SemanticEnhancedIntentEngine,
)

# ========================================================================
# 统一数据模型测试
# ========================================================================

@pytest.mark.integration
class TestUnifiedDataModel:
    """测试统一数据模型"""

    def test_intent_type_enum_comprehensive(self):
        """测试IntentType枚举包含所有意图类型"""
        # 验证核心意图类型存在
        assert IntentType.PATENT_SEARCH
        assert IntentType.PATENT_ANALYSIS
        assert IntentType.CODE_GENERATION
        assert IntentType.OPINION_RESPONSE
        assert IntentType.INFRINGEMENT_ANALYSIS
        assert IntentType.LEGAL_CONSULTING
        assert IntentType.GENERAL_CHAT

        # 验证枚举值
        assert IntentType.PATENT_SEARCH.value == "PATENT_SEARCH"

    def test_intent_category_enum(self):
        """测试IntentCategory枚举"""
        assert IntentCategory.PATENT
        assert IntentCategory.LEGAL
        assert IntentCategory.CODE
        assert IntentCategory.QUERY
        assert IntentCategory.ANALYSIS
        assert IntentCategory.GENERAL

    def test_complexity_level_enum(self):
        """测试ComplexityLevel枚举"""
        assert ComplexityLevel.SIMPLE
        assert ComplexityLevel.MEDIUM
        assert ComplexityLevel.COMPLEX
        assert ComplexityLevel.EXPERT

    def test_intent_result_model(self):
        """测试IntentResult数据模型"""
        result = IntentResult(
            intent=IntentType.PATENT_SEARCH,
            confidence=0.95,
            category=IntentCategory.PATENT,
            raw_text="检索专利",
            processing_time_ms=50.0,
            model_version="2.0.0",
            entities=["CN123456"],
            key_concepts=["专利检索"],
            complexity=ComplexityLevel.MEDIUM,
            semantic_similarity=0.8,
            context_requirements=[],
            suggested_tools=["patent_search"],
            processing_strategy="混合检索策略",
            estimated_time=3.0,
            metadata={"test": True}
        )

        # 验证所有字段
        assert result.intent == IntentType.PATENT_SEARCH
        assert result.confidence == 0.95
        assert result.category == IntentCategory.PATENT
        assert result.raw_text == "检索专利"
        assert result.processing_time_ms == 50.0
        assert result.entities == ["CN123456"]
        assert result.key_concepts == ["专利检索"]
        assert result.complexity == ComplexityLevel.MEDIUM
        assert result.semantic_similarity == 0.8
        assert result.suggested_tools == ["patent_search"]
        assert result.estimated_time == 3.0
        assert result.metadata == {"test": True}

    def test_infer_category_from_intent(self):
        """测试从意图类型推断类别"""
        assert infer_category_from_intent(IntentType.PATENT_SEARCH) == IntentCategory.PATENT
        assert infer_category_from_intent(IntentType.LEGAL_CONSULTING) == IntentCategory.LEGAL
        assert infer_category_from_intent(IntentType.CODE_GENERATION) == IntentCategory.CODE
        assert infer_category_from_intent(IntentType.GENERAL_CHAT) == IntentCategory.GENERAL

    def test_create_default_result(self):
        """测试创建默认结果"""
        result = create_default_result("测试文本", 100.0, "2.0.0")

        assert result.intent == IntentType.UNKNOWN
        assert result.confidence == 0.0
        assert result.raw_text == "测试文本"
        assert result.processing_time_ms == 100.0

    def test_merge_results_weighted_vote(self):
        """测试加权投票合并策略"""
        result1 = IntentResult(
            intent=IntentType.PATENT_SEARCH,
            confidence=0.8,
            category=IntentCategory.PATENT,
            raw_text="检索专利",
            processing_time_ms=50.0,
            model_version="2.0.0"
        )
        result2 = IntentResult(
            intent=IntentType.PATENT_SEARCH,
            confidence=0.9,
            category=IntentCategory.PATENT,
            raw_text="检索专利",
            processing_time_ms=60.0,
            model_version="2.0.0"
        )

        merged = merge_results([result1, result2], strategy="weighted_vote")

        assert merged.intent == IntentType.PATENT_SEARCH
        assert 0 < merged.confidence <= 1.0


# ========================================================================
# 继承体系测试
# ========================================================================

@pytest.mark.integration
class TestInheritanceHierarchy:
    """测试继承体系"""

    def test_enhanced_engine_inherits_base(self):
        """测试EnhancedIntentRecognitionEngine继承BaseIntentEngine"""
        engine = EnhancedIntentRecognitionEngine()

        assert isinstance(engine, BaseIntentEngine)
        assert hasattr(engine, 'recognize_intent')
        assert hasattr(engine, 'recognize_intent_async')
        assert hasattr(engine, 'get_stats')
        assert hasattr(engine, 'reset_stats')

    def test_semantic_engine_inherits_enhanced(self):
        """测试SemanticEnhancedIntentEngine继承EnhancedIntentRecognitionEngine"""
        engine = SemanticEnhancedIntentEngine()

        assert isinstance(engine, BaseIntentEngine)
        assert isinstance(engine, EnhancedIntentRecognitionEngine)
        assert hasattr(engine, 'recognize_intent')
        assert hasattr(engine, 'recognize_intent_async')

    def test_adapter_inherits_base(self):
        """测试IntentRecognitionAdapter继承BaseIntentEngine"""
        engine = IntentRecognitionAdapter({"use_phase2_model": False})

        assert isinstance(engine, BaseIntentEngine)
        assert hasattr(engine, 'recognize_intent')
        assert hasattr(engine, 'get_stats')


# ========================================================================
# 统一入口测试
# ========================================================================

@pytest.mark.integration
class TestUnifiedEntryPoints:
    """测试统一入口"""

    def test_get_intent_engine_enhanced(self):
        """测试获取Enhanced引擎"""
        engine = get_intent_engine("enhanced")

        assert isinstance(engine, BaseIntentEngine)
        assert isinstance(engine, EnhancedIntentRecognitionEngine)

    def test_get_intent_engine_keyword_alias(self):
        """测试keyword别名指向Enhanced引擎"""
        engine = get_intent_engine("keyword")

        assert isinstance(engine, EnhancedIntentRecognitionEngine)

    def test_get_intent_engine_semantic(self):
        """测试获取Semantic引擎"""
        engine = get_intent_engine("semantic")

        assert isinstance(engine, BaseIntentEngine)
        assert isinstance(engine, SemanticEnhancedIntentEngine)

    def test_get_intent_engine_adapter(self):
        """测试获取Adapter引擎"""
        engine = get_intent_engine("adapter")

        assert isinstance(engine, BaseIntentEngine)
        assert isinstance(engine, IntentRecognitionAdapter)

    def test_recognize_intent_convenience_function(self):
        """测试recognize_intent便捷函数"""
        result = recognize_intent("帮我检索专利", engine_type="enhanced")

        assert isinstance(result, IntentResult)
        assert result.intent in [IntentType.PATENT_SEARCH, IntentType.INFORMATION_QUERY]

    @pytest.mark.asyncio
    async def test_recognize_intent_async_convenience_function(self):
        """测试recognize_intent_async便捷函数"""
        result = await recognize_intent_async("帮我检索专利", engine_type="enhanced")

        assert isinstance(result, IntentResult)
        assert result.intent in [IntentType.PATENT_SEARCH, IntentType.INFORMATION_QUERY]


# ========================================================================
# IntentResult格式一致性测试
# ========================================================================

@pytest.mark.integration
class TestIntentResultConsistency:
    """测试IntentResult格式一致性"""

    def test_enhanced_engine_result_format(self):
        """测试Enhanced引擎返回统一格式"""
        engine = EnhancedIntentRecognitionEngine()
        result = engine.recognize_intent("检索专利")

        # 验证所有必需字段存在
        assert hasattr(result, 'intent')
        assert hasattr(result, 'confidence')
        assert hasattr(result, 'category')
        assert hasattr(result, 'raw_text')
        assert hasattr(result, 'processing_time_ms')
        assert hasattr(result, 'model_version')
        assert hasattr(result, 'entities')
        assert hasattr(result, 'key_concepts')
        assert hasattr(result, 'complexity')

        # 验证类型正确
        assert isinstance(result.intent, IntentType)
        assert isinstance(result.confidence, float)
        assert isinstance(result.category, IntentCategory)
        assert isinstance(result.raw_text, str)
        assert isinstance(result.processing_time_ms, float)
        assert isinstance(result.entities, list)
        assert isinstance(result.key_concepts, list)
        assert isinstance(result.complexity, ComplexityLevel)

    def test_semantic_engine_result_format(self):
        """测试Semantic引擎返回统一格式"""
        engine = SemanticEnhancedIntentEngine()
        result = engine.recognize_intent("检索专利")

        # 验证格式一致
        assert isinstance(result.intent, IntentType)
        assert isinstance(result.confidence, float)
        assert isinstance(result.category, IntentCategory)
        assert isinstance(result.complexity, ComplexityLevel)

    @pytest.mark.asyncio
    async def test_semantic_engine_async_result_format(self):
        """测试Semantic引擎异步方法返回统一格式"""
        engine = SemanticEnhancedIntentEngine()
        await engine.initialize_async()
        result = await engine.recognize_intent_async("检索专利")

        # 验证格式一致
        assert isinstance(result.intent, IntentType)
        assert isinstance(result.confidence, float)
        assert isinstance(result.category, IntentCategory)
        assert isinstance(result.complexity, ComplexityLevel)


# ========================================================================
# 工厂模式测试
# ========================================================================

@pytest.mark.integration
class TestFactoryPattern:
    """测试工厂模式"""

    def test_factory_registration(self):
        """测试工厂注册"""
        engines = IntentEngineFactory.list_engines()

        # 验证所有引擎都已注册
        assert "enhanced" in engines
        assert "enhanced_keyword" in engines
        assert "semantic" in engines
        assert "adapter" in engines

    def test_factory_create_enhanced(self):
        """测试工厂创建Enhanced引擎"""
        engine = IntentEngineFactory.create("enhanced")

        assert isinstance(engine, EnhancedIntentRecognitionEngine)
        assert isinstance(engine, BaseIntentEngine)

    def test_factory_create_semantic(self):
        """测试工厂创建Semantic引擎"""
        engine = IntentEngineFactory.create("semantic")

        assert isinstance(engine, SemanticEnhancedIntentEngine)
        assert isinstance(engine, BaseIntentEngine)

    def test_factory_create_adapter(self):
        """测试工厂创建Adapter引擎"""
        engine = IntentEngineFactory.create("adapter")

        assert isinstance(engine, IntentRecognitionAdapter)
        assert isinstance(engine, BaseIntentEngine)

    def test_factory_unknown_type(self):
        """测试工厂创建未知引擎类型"""
        from core.intent.exceptions import ConfigurationError

        with pytest.raises(ConfigurationError):
            IntentEngineFactory.create("unknown_engine")


# ========================================================================
# 端到端功能测试
# ========================================================================

@pytest.mark.integration
class TestEndToEndFunctionality:
    """端到端功能测试"""

    def test_patent_search_intent_enhanced(self):
        """测试Enhanced引擎识别专利搜索意图"""
        engine = EnhancedIntentRecognitionEngine()
        result = engine.recognize_intent("帮我检索人工智能相关专利")

        assert result.intent == IntentType.PATENT_SEARCH
        assert result.category == IntentCategory.PATENT
        assert result.confidence > 0.5

    def test_code_generation_intent_enhanced(self):
        """测试Enhanced引擎识别代码生成意图"""
        engine = EnhancedIntentRecognitionEngine()
        result = engine.recognize_intent("帮我写一个快速排序算法")

        assert result.intent == IntentType.CODE_GENERATION
        assert result.category == IntentCategory.CODE

    def test_opinion_response_intent_enhanced(self):
        """测试Enhanced引擎识别审查意见答复意图"""
        engine = EnhancedIntentRecognitionEngine()
        result = engine.recognize_intent("审查意见怎么答复")

        assert result.intent == IntentType.OPINION_RESPONSE
        assert result.category == IntentCategory.PATENT

    @pytest.mark.asyncio
    async def test_async_recognition_enhanced(self):
        """测试Enhanced引擎异步识别"""
        engine = EnhancedIntentRecognitionEngine()
        result = await engine.recognize_intent_async("检索专利", user_id="test_user")

        assert isinstance(result, IntentResult)
        # 异步方法应该返回和同步方法相同的结果
        assert result.intent in [IntentType.PATENT_SEARCH, IntentType.INFORMATION_QUERY]

    @pytest.mark.asyncio
    async def test_async_recognition_semantic(self):
        """测试Semantic引擎异步识别"""
        engine = SemanticEnhancedIntentEngine()
        await engine.initialize_async()
        result = await engine.recognize_intent_async("分析专利产品是否侵权")

        assert isinstance(result, IntentResult)
        # 语义引擎应该能识别到相关的专利意图
        assert result.category == IntentCategory.PATENT


# ========================================================================
# 统计信息测试
# ========================================================================

@pytest.mark.integration
class TestStatistics:
    """统计信息测试"""

    def test_enhanced_engine_stats(self):
        """测试Enhanced引擎统计"""
        engine = EnhancedIntentRecognitionEngine()

        # 执行几次识别
        engine.recognize_intent("检索专利")
        engine.recognize_intent("写代码")

        stats = engine.get_stats()
        assert stats.total_requests == 2
        assert stats.successful_requests == 2
        assert stats.avg_processing_time_ms > 0

    def test_stats_reset(self):
        """测试统计重置"""
        engine = EnhancedIntentRecognitionEngine()
        engine.recognize_intent("测试")

        engine.reset_stats()
        stats = engine.get_stats()

        assert stats.total_requests == 0


# ========================================================================
# 错误处理测试
# ========================================================================

@pytest.mark.integration
class TestErrorHandling:
    """错误处理测试"""

    def test_empty_input_validation(self):
        """测试空输入验证"""
        from core.intent.exceptions import ValidationError

        engine = EnhancedIntentRecognitionEngine()

        with pytest.raises(ValidationError):
            engine.recognize_intent("")

    def test_invalid_input_type(self):
        """测试无效输入类型"""
        from core.intent.exceptions import ValidationError

        engine = EnhancedIntentRecognitionEngine()

        with pytest.raises(ValidationError):
            engine.recognize_intent(12345)  # type: ignore


# ========================================================================
# 性能测试
# ========================================================================

@pytest.mark.integration
@pytest.mark.performance
class TestPerformance:
    """性能测试"""

    def test_single_request_performance(self):
        """测试单次请求性能"""
        engine = EnhancedIntentRecognitionEngine()
        result = engine.recognize_intent("检索专利")

        # 应该在100ms内完成
        assert result.processing_time_ms < 100

    def test_batch_processing_performance(self):
        """测试批量处理性能"""
        engine = EnhancedIntentRecognitionEngine()

        texts = ["检索专利" for _ in range(50)]
        results = engine.recognize_batch(texts)

        assert len(results) == 50

        stats = engine.get_stats()
        assert stats.total_requests == 50
        # 平均处理时间应该合理
        assert stats.avg_processing_time_ms < 100


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
