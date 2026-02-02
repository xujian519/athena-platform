#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试：感知模块工厂模式
Test: Perception Module Factory Pattern
"""

import pytest
import sys
from pathlib import Path

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from core.perception.factory import (
    ProcessorFactory,
    PerceptionEngineFactory,
    StreamProcessorFactory,
    PerceptionBuilder,
)
from core.perception.types import InputType, PerceptionConfig


class TestProcessorFactoryClass:
    """测试处理器工厂类"""

    def test_factory_class_exists(self):
        """测试工厂类存在"""
        # ProcessorFactory是类级别工厂，不需要实例化
        assert hasattr(ProcessorFactory, "create_processor")
        assert hasattr(ProcessorFactory, "register_processor")
        assert hasattr(ProcessorFactory, "get_registered_processors")

    def test_factory_register_and_get_processors(self):
        """测试注册和获取处理器"""
        # 创建一个模拟处理器类
        class MockProcessor:
            def __init__(self, processor_type, config):
                self.processor_type = processor_type
                self.config = config

        # 注册处理器
        ProcessorFactory.register_processor(InputType.TEXT, MockProcessor)

        # 验证注册成功
        registered = ProcessorFactory.get_registered_processors()
        assert InputType.TEXT in registered

        # 创建处理器
        processor = ProcessorFactory.create_processor(InputType.TEXT, {"test": "config"})
        assert processor is not None
        assert processor.processor_type == "text"

        # 清理
        ProcessorFactory.unregister_processor(InputType.TEXT)

    def test_factory_unsupported_type(self):
        """测试不支持的输入类型"""
        # 尝试创建未注册的处理器应该抛出ValueError
        with pytest.raises(ValueError, match="不支持的输入类型"):
            ProcessorFactory.create_processor(InputType.AUDIO)


class TestPerceptionEngineFactory:
    """测试感知引擎工厂类"""

    def test_engine_factory_exists(self):
        """测试引擎工厂类存在"""
        assert hasattr(PerceptionEngineFactory, "create_engine")
        assert hasattr(PerceptionEngineFactory, "register_engine")
        assert hasattr(PerceptionEngineFactory, "get_engine_types")

    def test_engine_factory_register_and_get(self):
        """测试注册和获取引擎"""
        # 创建一个模拟引擎类
        class MockEngine:
            def __init__(self, agent_id, config):
                self.agent_id = agent_id
                self.config = config

        # 注册引擎
        PerceptionEngineFactory.register_engine("mock", MockEngine)

        # 验证注册成功
        engine_types = PerceptionEngineFactory.get_engine_types()
        assert "mock" in engine_types

        # 创建引擎 - 使用正确的配置参数
        engine = PerceptionEngineFactory.create_engine(
            agent_id="test_agent",
            engine_type="mock",
            config=PerceptionConfig(enable_multimodal=True)
        )
        assert engine is not None
        assert engine.agent_id == "test_agent"

        # 清理
        PerceptionEngineFactory._engines.pop("mock", None)

    def test_engine_factory_unsupported_type(self):
        """测试不支持的引擎类型"""
        with pytest.raises(ValueError, match="不支持的引擎类型"):
            PerceptionEngineFactory.create_engine(
                agent_id="test",
                engine_type="nonexistent"
            )


class TestStreamProcessorFactory:
    """测试流处理器工厂类"""

    def test_stream_factory_exists(self):
        """测试流工厂类存在"""
        assert hasattr(StreamProcessorFactory, "create_processor")
        assert hasattr(StreamProcessorFactory, "register_processor")

    def test_stream_factory_register_and_create(self):
        """测试注册和创建流处理器"""
        from core.perception.types import StreamType, StreamConfig

        # 创建一个模拟流处理器类
        class MockStreamProcessor:
            def __init__(self, config):
                self.config = config

        # 注册流处理器
        StreamProcessorFactory.register_processor(StreamType.TEXT, MockStreamProcessor)

        # 创建流处理器
        config = StreamConfig(chunk_size=2048)
        processor = StreamProcessorFactory.create_processor(StreamType.TEXT, config)
        assert processor is not None
        assert processor.config.chunk_size == 2048

        # 清理
        StreamProcessorFactory._processors.pop(StreamType.TEXT, None)


class TestPerceptionBuilder:
    """测试感知构建器"""

    def test_builder_creation(self):
        """测试创建构建器"""
        builder = PerceptionBuilder(agent_id="test_agent")
        assert builder.agent_id == "test_agent"
        assert isinstance(builder.config, PerceptionConfig)
        assert builder._processors == []
        assert builder._middleware == []
        assert builder._extensions == []

    def test_builder_with_config(self):
        """测试设置配置"""
        builder = PerceptionBuilder(agent_id="test_agent")
        config = PerceptionConfig(enable_multimodal=False)
        result = builder.with_config(config)
        # 支持链式调用
        assert result is builder
        assert builder.config.enable_multimodal is False

    def test_builder_with_processor(self):
        """测试添加处理器"""
        builder = PerceptionBuilder(agent_id="test_agent")
        result = builder.with_processor(InputType.TEXT, {"max_length": 1000})
        # 支持链式调用
        assert result is builder
        assert len(builder._processors) == 1
        assert builder._processors[0] == (InputType.TEXT, {"max_length": 1000})

    def test_builder_with_middleware(self):
        """测试添加中间件"""
        builder = PerceptionBuilder(agent_id="test_agent")
        middleware = {"name": "test_middleware"}
        result = builder.with_middleware(middleware)
        assert result is builder
        assert len(builder._middleware) == 1

    def test_builder_with_extension(self):
        """测试添加扩展"""
        builder = PerceptionBuilder(agent_id="test_agent")
        extension = {"name": "test_extension"}
        result = builder.with_extension(extension)
        assert result is builder
        assert len(builder._extensions) == 1

    def test_builder_chain_calls(self):
        """测试链式调用"""
        builder = (PerceptionBuilder(agent_id="test_agent")
                   .with_config({"enable_multimodal": True})
                   .with_processor(InputType.TEXT)
                   .with_processor(InputType.IMAGE))

        assert len(builder._processors) == 2
        assert builder.config.enable_multimodal is True


class TestFactoryErrorHandling:
    """测试工厂错误处理"""

    def test_create_processor_without_registration(self):
        """测试创建未注册的处理器"""
        # 确保VIDEO类型未注册
        ProcessorFactory._processors.pop(InputType.VIDEO, None)

        with pytest.raises(ValueError, match="不支持的输入类型"):
            ProcessorFactory.create_processor(InputType.VIDEO)

    def test_create_engine_without_registration(self):
        """测试创建未注册的引擎"""
        # 确保nonexistent类型未注册
        PerceptionEngineFactory._engines.pop("nonexistent", None)

        with pytest.raises(ValueError, match="不支持的引擎类型"):
            PerceptionEngineFactory.create_engine(
                agent_id="test",
                engine_type="nonexistent"
            )


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
