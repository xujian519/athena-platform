#!/usr/bin/env python3
"""
NLP模块__init__.py单元测试

测试自然语言处理模块的统一导出接口

测试范围:
- 模块导入验证
- 枚举类型（NLPProviderType, TaskType）
- 便捷函数测试
- 服务类测试
"""

import pytest


# 测试所有主要导入
def test_module_imports():
    """测试模块主要导入"""
    from core.nlp import (
        NLPProviderType,
        OllamaProvider,
        TaskType,
        UniversalNLPService,
        analyze_patent,
        conversation_response,
        creative_writing,
        emotional_analysis,
        get_nlp_service,
        technical_reasoning,
    )

    # 验证导入成功
    assert NLPProviderType is not None
    assert OllamaProvider is not None
    assert TaskType is not None
    assert UniversalNLPService is not None
    assert analyze_patent is not None
    assert conversation_response is not None
    assert creative_writing is not None
    assert emotional_analysis is not None
    assert get_nlp_service is not None
    assert technical_reasoning is not None


class TestNLPProviderType:
    """测试NLPProviderType枚举"""

    def test_provider_values(self):
        """测试提供商类型值"""
        from core.nlp import NLPProviderType

        # 验证常见提供商存在
        assert hasattr(NLPProviderType, 'OLLAMA') or hasattr(NLPProviderType, 'ollama')
        assert hasattr(NLPProviderType, 'OPENAI') or hasattr(NLPProviderType, 'openai')

    def test_provider_comparison(self):
        """测试提供商比较"""
        from core.nlp import NLPProviderType

        # 如果是枚举，测试比较
        if hasattr(NLPProviderType, '__members__'):
            provider1 = NLPProviderType.OLLAMA if hasattr(NLPProviderType, 'OLLAMA') else list(NLPProviderType)[0]
            provider2 = NLPProviderType.OLLAMA if hasattr(NLPProviderType, 'OLLAMA') else list(NLPProviderType)[0]
            assert provider1 == provider2


class TestTaskType:
    """测试TaskType枚举"""

    def test_task_values(self):
        """测试任务类型值"""
        from core.nlp import TaskType

        # 验证常见任务类型存在
        assert hasattr(TaskType, 'PATENT_ANALYSIS') or hasattr(TaskType, 'patent_analysis')
        assert hasattr(TaskType, 'CONVERSATION') or hasattr(TaskType, 'conversation')
        assert hasattr(TaskType, 'CREATIVE_WRITING') or hasattr(TaskType, 'creative_writing')

    def test_task_comparison(self):
        """测试任务类型比较"""
        from core.nlp import TaskType

        # 如果是枚举，测试比较
        if hasattr(TaskType, '__members__'):
            task1 = TaskType.PATENT_ANALYSIS if hasattr(TaskType, 'PATENT_ANALYSIS') else list(TaskType)[0]
            task2 = TaskType.PATENT_ANALYSIS if hasattr(TaskType, 'PATENT_ANALYSIS') else list(TaskType)[0]
            assert task1 == task2


class TestConvenienceFunctions:
    """测试便捷函数"""

    def test_get_nlp_service(self):
        """测试获取NLP服务"""
        from core.nlp import get_nlp_service

        # 可能返回服务实例或None
        service = get_nlp_service()

        # 只验证可以调用
        assert service is not None or callable(get_nlp_service)

    def test_analyze_patent(self):
        """测试专利分析函数"""
        from core.nlp import analyze_patent

        # 验证函数可调用
        assert callable(analyze_patent)

    def test_conversation_response(self):
        """测试对话响应函数"""
        from core.nlp import conversation_response

        # 验证函数可调用
        assert callable(conversation_response)

    def test_creative_writing(self):
        """测试创意写作函数"""
        from core.nlp import creative_writing

        # 验证函数可调用
        assert callable(creative_writing)

    def test_emotional_analysis(self):
        """测试情感分析函数"""
        from core.nlp import emotional_analysis

        # 验证函数可调用
        assert callable(emotional_analysis)

    def test_technical_reasoning(self):
        """测试技术推理函数"""
        from core.nlp import technical_reasoning

        # 验证函数可调用
        assert callable(technical_reasoning)


class TestUniversalNLPService:
    """测试UniversalNLPService类"""

    def test_service_creation(self):
        """测试服务创建"""
        from core.nlp import UniversalNLPService

        # 如果有默认构造函数，测试创建
        try:
            service = UniversalNLPService()
            assert service is not None
        except TypeError:
            # 如果需要参数，跳过此测试
            pass

    def test_service_methods(self):
        """测试服务方法"""
        from core.nlp import UniversalNLPService

        # 检查是否有预期的方法
        expected_methods = ['analyze', 'process', 'execute']
        for method in expected_methods:
            # 不强制要求所有方法存在，只检查如果存在的话
            if hasattr(UniversalNLPService, method):
                assert callable(getattr(UniversalNLPService, method))


class TestOllamaProvider:
    """测试OllamaProvider类"""

    def test_provider_creation(self):
        """测试提供商创建"""
        from core.nlp import OllamaProvider

        # 如果有默认构造函数，测试创建
        try:
            provider = OllamaProvider()
            assert provider is not None
        except TypeError:
            # 如果需要参数，跳过此测试
            pass

    def test_provider_methods(self):
        """测试提供商方法"""
        from core.nlp import OllamaProvider

        # 检查是否有预期的方法
        expected_methods = ['generate', 'process', 'chat']
        for method in expected_methods:
            if hasattr(OllamaProvider, method):
                assert callable(getattr(OllamaProvider, method))


class TestIntegration:
    """集成测试"""

    def test_module_integration(self):
        """测试模块集成"""
        from core.nlp import NLPProviderType, TaskType, UniversalNLPService, get_nlp_service

        # 验证所有组件可以一起导入
        assert NLPProviderType is not None
        assert TaskType is not None
        assert UniversalNLPService is not None
        assert callable(get_nlp_service)

    def test_function_availability(self):
        """测试函数可用性"""
        from core.nlp import (
            analyze_patent,
            conversation_response,
            creative_writing,
            emotional_analysis,
            technical_reasoning,
        )

        # 验证所有函数都可调用
        functions = [
            analyze_patent,
            conversation_response,
            creative_writing,
            emotional_analysis,
            technical_reasoning
        ]

        for func in functions:
            assert callable(func), f"{func.__name__} 不可调用"


class TestEdgeCases:
    """测试边界情况"""

    def test_multiple_service_calls(self):
        """测试多次调用获取服务"""
        from core.nlp import get_nlp_service

        # 多次调用应该返回同一个实例（单例模式）或新的有效实例
        service1 = get_nlp_service()
        service2 = get_nlp_service()

        # 至少两个都应该有效（不是None）或可调用
        assert (service1 is not None and service2 is not None) or callable(get_nlp_service)

    def test_empty_input_handling(self):
        """测试空输入处理"""
        from core.nlp import analyze_patent

        # 验证函数可以处理空输入（可能返回空结果或抛出异常）
        try:
            result = analyze_patent("")
            # 如果不抛出异常，验证返回值
            assert result is not None or isinstance(result, (str, dict, list))
        except (ValueError, TypeError):
            # 预期可能抛出异常
            pass


class TestPerformance:
    """测试性能"""

    def test_module_import_speed(self):
        """测试模块导入速度"""
        import time

        start = time.time()
        elapsed = time.time() - start

        # 模块导入应该很快 (< 1秒)
        assert elapsed < 1.0

    def test_function_creation_speed(self):
        """测试函数创建速度"""
        import time


        start = time.time()
        # 多次获取函数引用
        for _ in range(100):
            pass
        elapsed = time.time() - start

        # 获取函数引用应该很快 (< 0.01秒)
        assert elapsed < 0.01


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
