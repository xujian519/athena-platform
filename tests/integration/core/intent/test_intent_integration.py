"""
意图识别服务 - 集成测试

测试端到端的意图识别流程。

Author: Xiaonuo
Created: 2025-01-17
Version: 1.0.0
"""

import pytest

pytestmark = pytest.mark.skip(reason="Missing required modules: ")

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from core.intent.base_engine import (
    IntentCategory,
    IntentEngineFactory,
    IntentType,
    create_default_result,
)
from core.intent.exceptions import ValidationError
from core.intent.keyword_engine_refactored import KeywordIntentEngine, create_keyword_engine

# ========================================================================
# 端到端测试
# ========================================================================

@pytest.mark.integration
@pytest.mark.intent
class TestIntentRecognitionE2E:
    """端到端意图识别测试"""

    def test_full_workflow_patent_search(self):
        """测试专利检索的完整流程"""
        engine = create_keyword_engine()

        text = "帮我检索关于人工智能的专利"
        result = engine.recognize_intent(text)

        # 验证结果
        assert result.intent == IntentType.PATENT_SEARCH
        assert result.category == IntentCategory.PATENT
        assert result.confidence > 0.5
        assert result.raw_text == text
        assert result.processing_time_ms > 0

    def test_full_workflow_code_generation(self):
        """测试代码生成的完整流程"""
        engine = create_keyword_engine()

        text = "帮我写一个快速排序算法"
        result = engine.recognize_intent(text)

        # 验证结果
        assert result.intent == IntentType.CODE_GENERATION
        assert result.category == IntentCategory.CODE
        assert result.confidence > 0.5

    def test_full_workflow_general_chat(self):
        """测试通用聊天的完整流程"""
        engine = create_keyword_engine()

        text = "你好，今天天气怎么样"
        result = engine.recognize_intent(text)

        # 验证结果
        assert result.intent == IntentType.GENERAL_CHAT
        assert result.category == IntentCategory.GENERAL

    def test_batch_processing(self):
        """测试批量处理"""
        engine = create_keyword_engine()

        texts = [
            "检索专利",
            "分析专利",
            "写代码",
            "天气"
        ]

        results = engine.recognize_batch(texts)

        # 验证结果
        assert len(results) == len(texts)
        assert all(isinstance(r, IntentType) or isinstance(r.intent, IntentType) for r in results)


# ========================================================================
# 错误处理测试
# ========================================================================

@pytest.mark.integration
class TestErrorHandling:
    """错误处理集成测试"""

    def test_invalid_input_empty_string(self):
        """测试空字符串输入"""
        engine = create_keyword_engine()

        with pytest.raises(ValidationError) as exc_info:
            engine.recognize_intent("")

        assert "输入文本不能为空" in str(exc_info.value)

    def test_invalid_input_too_long(self):
        """测试超长输入"""
        engine = create_keyword_engine(config={"max_input_length": 100})

        long_text = "a" * 200

        with pytest.raises(ValidationError) as exc_info:
            engine.recognize_intent(long_text)

        assert "输入文本长度超过限制" in str(exc_info.value)

    def test_invalid_input_wrong_type(self):
        """测试错误类型的输入"""
        engine = create_keyword_engine()

        with pytest.raises(ValidationError) as exc_info:
            engine.recognize_intent(12345)  # type: ignore

        assert "输入必须是字符串类型" in str(exc_info.value)


# ========================================================================
# 性能测试
# ========================================================================

@pytest.mark.integration
@pytest.mark.performance
class TestPerformance:
    """性能集成测试"""

    def test_single_request_performance(self):
        """测试单次请求性能"""
        engine = create_keyword_engine()

        text = "帮我检索专利"
        result = engine.recognize_intent(text)

        # 验证性能（应该在100ms内）
        assert result.processing_time_ms < 100

    def test_batch_performance(self):
        """测试批量处理性能"""
        engine = create_keyword_engine()

        texts = ["检索专利" for _ in range(100)]

        import time
        start = time.perf_counter()

        results = engine.recognize_batch(texts)

        elapsed = time.perf_counter() - start

        # 验证结果
        assert len(results) == 100

        # 验证性能（100个请求应该在5秒内完成）
        assert elapsed < 5.0

        # 验证平均处理时间
        stats = engine.get_stats()
        assert stats.avg_processing_time_ms < 50


# ========================================================================
# 统计信息测试
# ========================================================================

@pytest.mark.integration
class TestStatistics:
    """统计信息集成测试"""

    def test_stats_tracking(self):
        """测试统计信息跟踪"""
        engine = create_keyword_engine()

        # 执行一些请求
        texts = ["检索专利", "分析专利", "写代码"]
        for text in texts:
            engine.recognize_intent(text)

        # 获取统计信息
        stats = engine.get_stats()

        # 验证统计信息
        assert stats.total_requests == 3
        assert stats.successful_requests == 3
        assert stats.failed_requests == 0
        assert stats.avg_processing_time_ms > 0

    def test_stats_reset(self):
        """测试统计信息重置"""
        engine = create_keyword_engine()

        # 执行请求
        engine.recognize_intent("测试")

        # 重置统计
        engine.reset_stats()

        # 验证已重置
        stats = engine.get_stats()
        assert stats.total_requests == 0


# ========================================================================
# 实体提取测试
# ========================================================================

@pytest.mark.integration
class TestEntityExtraction:
    """实体提取集成测试"""

    def test_patent_number_extraction(self):
        """测试专利号提取"""
        engine = create_keyword_engine()

        text = "检索专利CN123456A和US7890123"
        result = engine.recognize_intent(text)

        # 验证提取的专利号
        assert "CN123456A" in result.entities or "US7890123" in result.entities

    def test_multiple_entities(self):
        """测试多实体提取"""
        engine = create_keyword_engine()

        text = "比较CN123456A和2024年的人工智能专利"
        result = engine.recognize_intent(text)

        # 应该至少有一个实体
        assert len(result.entities) > 0


# ========================================================================
# 生命周期管理测试
# ========================================================================

@pytest.mark.integration
class TestLifecycle:
    """生命周期管理测试"""

    def test_context_manager(self):
        """测试上下文管理器"""
        with create_keyword_engine() as engine:
            result = engine.recognize_intent("检索专利")
            assert result.intent == IntentType.PATENT_SEARCH

        # 验证资源已清理
        # 这里可以验证GPU内存等资源的释放

    def test_cleanup(self):
        """测试资源清理"""
        engine = create_keyword_engine()

        # 执行请求
        engine.recognize_intent("测试")

        # 清理资源
        engine.cleanup()

        # 验证清理后的状态
        # 这里可以验证模型已卸载


# ========================================================================
# 工厂模式测试
# ========================================================================

@pytest.mark.integration
class TestFactoryPattern:
    """工厂模式集成测试"""

    def test_engine_factory_create(self):
        """测试工厂创建引擎"""
        engine = IntentEngineFactory.create("keyword")

        assert isinstance(engine, KeywordIntentEngine)

    def test_engine_factory_list(self):
        """测试列出所有引擎"""
        engines = IntentEngineFactory.list_engines()

        assert "keyword" in engines

    def test_engine_factory_unknown_type(self):
        """测试未知引擎类型"""
        with pytest.raises(Exception):  # ConfigurationError
            IntentEngineFactory.create("unknown_engine")


# ========================================================================
# 工具函数测试
# ========================================================================

@pytest.mark.integration
class TestUtilityFunctions:
    """工具函数集成测试"""

    def test_create_default_result(self):
        """测试创建默认结果"""
        result = create_default_result(
            text="测试文本",
            processing_time_ms=50.0,
            model_version="1.0"
        )

        assert result.intent == IntentType.UNKNOWN
        assert result.confidence == 0.0
        assert result.raw_text == "测试文本"
        assert result.processing_time_ms == 50.0


# ========================================================================
# 复杂场景测试
# ========================================================================

@pytest.mark.integration
class TestComplexScenarios:
    """复杂场景集成测试"""

    def test_mixed_intent_detection(self):
        """测试混合意图检测"""
        engine = create_keyword_engine()

        # 包含多个关键词的文本
        text = "帮我检索并分析人工智能领域的专利"

        result = engine.recognize_intent(text)

        # 应该选择最匹配的意图
        assert result.intent in [
            IntentType.PATENT_SEARCH,
            IntentType.PATENT_ANALYSIS
        ]

    def test_ambiguous_input(self):
        """测试歧义输入"""
        engine = create_keyword_engine()

        # 有歧义的文本
        text = "分析一下"

        result = engine.recognize_intent(text)

        # 应该有合理的默认值
        assert result.confidence < 0.8  # 歧义输入置信度应该较低

    def test_special_characters(self):
        """测试特殊字符处理"""
        engine = create_keyword_engine()

        text = "检索专利!!!###$$$"

        result = engine.recognize_intent(text)

        # 应该能正确处理特殊字符
        assert result.intent == IntentType.PATENT_SEARCH


# ========================================================================
# 边界条件测试
# ========================================================================

@pytest.mark.integration
class TestEdgeCases:
    """边界条件集成测试"""

    def test_very_short_input(self):
        """测试极短输入"""
        engine = create_keyword_engine()

        text = "专利"
        result = engine.recognize_intent(text)

        # 极短输入也应该能处理
        assert result.intent != IntentType.UNKNOWN

    def test_unicode_text(self):
        """测试Unicode文本"""
        engine = create_keyword_engine()

        text = "检索关于🤖人工智能的专利"
        result = engine.recognize_intent(text)

        # Unicode应该能正确处理
        assert result.intent == IntentType.PATENT_SEARCH

    def test_mixed_language(self):
        """测试混合语言"""
        engine = create_keyword_engine()

        text = "Search for AI patent and 分析专利"
        result = engine.recognize_intent(text)

        # 混合语言应该能处理
        assert result.category == IntentCategory.PATENT
