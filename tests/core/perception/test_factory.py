#!/usr/bin/env python3
"""
工厂模式单元测试
Factory Pattern Unit Tests
"""

import sys
from pathlib import Path
from unittest.mock import MagicMock

import pytest

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent.parent))

from core.perception import TextProcessor
from core.perception.factory import (
    PerceptionBuilder,
    PerceptionEngineFactory,
    ProcessorFactory,
    create_audio_processor,
    create_image_processor,
    create_multimodal_processor,
    create_perception_engine,
    create_text_processor,
    create_video_processor,
)
from core.perception.types import (
    InputType,
    PerceptionConfig,
)


@pytest.mark.unit
class TestProcessorFactory:
    """处理器工厂测试类"""

    def test_register_processor(self):
        """测试注册处理器"""
        # 清理之前的注册
        if InputType.TEXT in ProcessorFactory._processors:
            del ProcessorFactory._processors[InputType.TEXT]

        ProcessorFactory.register_processor(InputType.TEXT, TextProcessor)

        assert InputType.TEXT in ProcessorFactory._processors
        assert ProcessorFactory._processors[InputType.TEXT] == TextProcessor

    def test_unregister_processor(self):
        """测试注销处理器"""
        # 先注册
        ProcessorFactory.register_processor(InputType.TEXT, TextProcessor)

        # 注销
        ProcessorFactory.unregister_processor(InputType.TEXT)

        assert InputType.TEXT not in ProcessorFactory._processors

    def test_create_processor(self):
        """测试创建处理器"""
        ProcessorFactory.register_processor(InputType.TEXT, TextProcessor)

        processor = ProcessorFactory.create_processor(
            InputType.TEXT, config={"max_text_length": 1000}
        )

        assert processor is not None
        assert hasattr(processor, "processor_id")
        assert hasattr(processor, "initialize")

    def test_create_processor_singleton(self):
        """测试创建单例处理器"""
        ProcessorFactory.register_processor(InputType.TEXT, TextProcessor)

        processor1 = ProcessorFactory.create_processor(InputType.TEXT, singleton=True)
        processor2 = ProcessorFactory.create_processor(InputType.TEXT, singleton=True)

        # 应该是同一个实例
        assert processor1 is processor2

    def test_create_processor_not_singleton(self):
        """测试创建非单例处理器"""
        ProcessorFactory.register_processor(InputType.TEXT, TextProcessor)

        processor1 = ProcessorFactory.create_processor(InputType.TEXT, singleton=False)
        processor2 = ProcessorFactory.create_processor(InputType.TEXT, singleton=False)

        # 应该是不同实例
        assert processor1 is not processor2

    def test_create_processor_unsupported_type(self):
        """测试创建不支持的处理器类型"""
        with pytest.raises(ValueError, match="不支持的输入类型"):
            ProcessorFactory.create_processor(InputType.UNKNOWN)

    def test_get_registered_processors(self):
        """测试获取已注册的处理器"""
        ProcessorFactory.register_processor(InputType.TEXT, TextProcessor)

        registered = ProcessorFactory.get_registered_processors()

        assert isinstance(registered, list)
        assert InputType.TEXT in registered


@pytest.mark.unit
class TestPerceptionEngineFactory:
    """感知引擎工厂测试类"""

    def test_register_engine(self):
        """测试注册引擎"""
        # 使用PerceptionEngine作为测试引擎
        from core.perception import PerceptionEngine

        PerceptionEngineFactory.register_engine("standard", PerceptionEngine)

        assert "standard" in PerceptionEngineFactory._engines
        assert PerceptionEngineFactory._engines["standard"] == PerceptionEngine

    def test_create_engine_with_dict_config(self):
        """测试使用字典配置创建引擎"""
        from core.perception import PerceptionEngine

        PerceptionEngineFactory.register_engine("standard", PerceptionEngine)

        engine = PerceptionEngineFactory.create_engine(
            agent_id="test_agent", engine_type="standard", config={"max_file_size": 1000000}
        )

        assert engine is not None
        assert engine.agent_id == "test_agent"

    def test_create_engine_with_config_object(self):
        """测试使用配置对象创建引擎"""
        from core.perception import PerceptionEngine

        PerceptionEngineFactory.register_engine("standard", PerceptionEngine)

        config = PerceptionConfig(max_file_size=5000000)
        engine = PerceptionEngineFactory.create_engine(
            agent_id="test_agent", engine_type="standard", config=config
        )

        assert engine is not None
        assert engine.agent_id == "test_agent"

    def test_create_engine_default_config(self):
        """测试使用默认配置创建引擎"""
        from core.perception import PerceptionEngine

        PerceptionEngineFactory.register_engine("standard", PerceptionEngine)

        engine = PerceptionEngineFactory.create_engine(
            agent_id="test_agent", engine_type="standard"
        )

        assert engine is not None
        assert engine.agent_id == "test_agent"

    def test_create_engine_singleton(self):
        """测试创建单例引擎"""
        from core.perception import PerceptionEngine

        PerceptionEngineFactory.register_engine("standard", PerceptionEngine)

        engine1 = PerceptionEngineFactory.create_engine(
            agent_id="test_agent", engine_type="standard", singleton=True
        )
        engine2 = PerceptionEngineFactory.create_engine(
            agent_id="test_agent", engine_type="standard", singleton=True
        )

        # 应该是同一个实例
        assert engine1 is engine2

    def test_create_engine_unsupported_type(self):
        """测试创建不支持的引擎类型"""
        with pytest.raises(ValueError, match="不支持的引擎类型"):
            PerceptionEngineFactory.create_engine(agent_id="test_agent", engine_type="unknown_type")

    def test_get_engine_types(self):
        """测试获取已注册的引擎类型"""
        from core.perception import PerceptionEngine

        PerceptionEngineFactory.register_engine("standard", PerceptionEngine)

        types = PerceptionEngineFactory.get_engine_types()

        assert isinstance(types, list)
        assert "standard" in types


@pytest.mark.asyncio
@pytest.mark.unit
class TestPerceptionBuilder:
    """感知模块构建器测试类"""

    def test_initialization(self):
        """测试初始化"""
        builder = PerceptionBuilder("test_agent")

        assert builder.agent_id == "test_agent"
        assert isinstance(builder.config, PerceptionConfig)
        assert builder._processors == []
        assert builder._middleware == []
        assert builder._extensions == []

    def test_with_config_dict(self):
        """测试设置配置（字典）"""
        builder = PerceptionBuilder("test_agent")
        config = {"max_file_size": 1000000}

        result = builder.with_config(config)

        # 支持链式调用
        assert result is builder
        assert builder.config.max_file_size == 1000000

    def test_with_config_object(self):
        """测试设置配置（对象）"""
        builder = PerceptionBuilder("test_agent")
        config = PerceptionConfig(max_file_size=5000000)

        result = builder.with_config(config)

        assert result is builder
        assert builder.config.max_file_size == 5000000

    def test_with_processor(self):
        """测试添加处理器"""
        builder = PerceptionBuilder("test_agent")

        result = builder.with_processor(InputType.TEXT, {"max_length": 1000})

        assert result is builder
        assert len(builder._processors) == 1
        assert builder._processors[0][0] == InputType.TEXT
        assert builder._processors[0][1] == {"max_length": 1000}

    def test_with_middleware(self):
        """测试添加中间件"""
        builder = PerceptionBuilder("test_agent")
        middleware = MagicMock()

        result = builder.with_middleware(middleware)

        assert result is builder
        assert len(builder._middleware) == 1
        assert builder._middleware[0] == middleware

    def test_with_extension(self):
        """测试添加扩展"""
        builder = PerceptionBuilder("test_agent")
        extension = MagicMock()

        result = builder.with_extension(extension)

        assert result is builder
        assert len(builder._extensions) == 1
        assert builder._extensions[0] == extension

    async def test_build(self):
        """测试构建引擎"""
        from core.perception import PerceptionEngine

        # 注册引擎
        PerceptionEngineFactory.register_engine("standard", PerceptionEngine)

        builder = (
            PerceptionBuilder("test_agent")
            .with_config({"max_file_size": 1000000})
            .with_processor(InputType.TEXT)
        )

        engine = await builder.build("standard")

        assert engine is not None
        assert engine.agent_id == "test_agent"
        assert engine.initialized


@pytest.mark.asyncio
@pytest.mark.unit
class TestConvenienceFunctions:
    """便捷函数测试类"""

    async def test_create_perception_engine(self):
        """测试创建感知引擎便捷函数"""
        from core.perception import PerceptionEngine

        PerceptionEngineFactory.register_engine("standard", PerceptionEngine)
        ProcessorFactory.register_processor(InputType.TEXT, TextProcessor)

        engine = await create_perception_engine(
            agent_id="test_agent", engine_type="standard", config={"max_file_size": 1000000}
        )

        assert engine is not None
        assert engine.agent_id == "test_agent"
        assert engine.initialized

        # 清理
        await engine.shutdown()

    def test_create_text_processor(self):
        """测试创建文本处理器便捷函数"""
        ProcessorFactory.register_processor(InputType.TEXT, TextProcessor)

        processor = create_text_processor({"max_text_length": 1000})

        assert processor is not None
        assert processor.processor_id == "text"

    def test_create_image_processor(self):
        """测试创建图像处理器便捷函数"""
        # 如果未注册图像处理器，应该抛出错误
        with pytest.raises(ValueError):
            create_image_processor()

    def test_create_audio_processor(self):
        """测试创建音频处理器便捷函数"""
        # 如果未注册音频处理器，应该抛出错误
        with pytest.raises(ValueError):
            create_audio_processor()

    def test_create_video_processor(self):
        """测试创建视频处理器便捷函数"""
        # 如果未注册视频处理器，应该抛出错误
        with pytest.raises(ValueError):
            create_video_processor()

    def test_create_multimodal_processor(self):
        """测试创建多模态处理器便捷函数"""
        # 如果未注册多模态处理器，应该抛出错误
        with pytest.raises(ValueError):
            create_multimodal_processor()


@pytest.mark.unit
class TestFactoryIntegration:
    """工厂模式集成测试"""

    def test_full_factory_workflow(self):
        """测试完整的工厂工作流"""
        # 1. 注册处理器
        ProcessorFactory.register_processor(InputType.TEXT, TextProcessor)

        # 2. 创建处理器实例
        processor1 = ProcessorFactory.create_processor(
            InputType.TEXT, config={"max_text_length": 5000}
        )
        processor2 = ProcessorFactory.create_processor(InputType.TEXT, singleton=True)

        # 3. 验证
        assert processor1 is not None
        assert processor2 is not None
        assert processor1 is not processor2  # 非单例

        # 4. 使用便捷函数
        processor3 = create_text_processor()

        assert processor3 is not None

    @pytest.mark.asyncio
    async def test_builder_pattern_workflow(self):
        """测试构建器模式工作流"""
        from core.perception import PerceptionEngine

        # 注册引擎和处理器
        PerceptionEngineFactory.register_engine("standard", PerceptionEngine)
        ProcessorFactory.register_processor(InputType.TEXT, TextProcessor)

        # 使用构建器创建引擎
        engine = await (
            PerceptionBuilder("test_agent")
            .with_config(
                {
                    "max_file_size": 10000000,
                    "enable_incremental_ocr": True,
                    "ocr_languages": ["chi_sim", "eng"],
                }
            )
            .with_processor(InputType.TEXT, {"max_text_length": 5000})
            .build("standard")
        )

        # 验证
        assert engine is not None
        assert engine.agent_id == "test_agent"
        assert engine.initialized

        # 清理
        await engine.shutdown()


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
