#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试：感知模块接口定义
Test: Perception Module Interface Definitions
"""

import pytest
import sys
from pathlib import Path
from abc import ABC
from datetime import datetime

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from core.perception.interfaces import (
    IProcessor,
    IStreamProcessor,
    IPerceptionEngine,
    ICache,
    IMonitor,
    IProcessorFactory,
)
from core.perception.types import (
    InputType,
    PerceptionResult,
    ProcessingMode,
    StreamConfig,
)


class TestIProcessor:
    """测试IProcessor接口"""

    def test_iprocessor_is_abstract(self):
        """测试IProcessor是抽象基类"""
        assert issubclass(IProcessor, ABC)

    def test_iprocessor_has_required_methods(self):
        """测试IProcessor有必需的方法"""
        assert hasattr(IProcessor, "initialize")
        assert hasattr(IProcessor, "process")
        assert hasattr(IProcessor, "cleanup")
        assert hasattr(IProcessor, "health_check")
        assert hasattr(IProcessor, "get_processor_info")

    def test_cannot_instantiate_iprocessor(self):
        """测试不能直接实例化IProcessor"""
        with pytest.raises(TypeError):
            IProcessor()


class TestIStreamProcessor:
    """测试IStreamProcessor接口"""

    def test_istreamprocessor_is_abstract(self):
        """测试IStreamProcessor是抽象基类"""
        assert issubclass(IStreamProcessor, ABC)

    def test_istreamprocessor_has_required_methods(self):
        """测试IStreamProcessor有必需的方法"""
        assert hasattr(IStreamProcessor, "stream_process")
        assert hasattr(IStreamProcessor, "process_batch")

    def test_cannot_instantiate_istreamprocessor(self):
        """测试不能直接实例化IStreamProcessor"""
        with pytest.raises(TypeError):
            IStreamProcessor()


class TestIPerceptionEngine:
    """测试IPerceptionEngine接口"""

    def test_iperceptionengine_is_abstract(self):
        """测试IPerceptionEngine是抽象基类"""
        assert issubclass(IPerceptionEngine, ABC)

    def test_iperceptionengine_has_required_methods(self):
        """测试IPerceptionEngine有必需的方法"""
        assert hasattr(IPerceptionEngine, "perceive")
        assert hasattr(IPerceptionEngine, "stream_perceive")
        assert hasattr(IPerceptionEngine, "health_check")
        assert hasattr(IPerceptionEngine, "shutdown")
        assert hasattr(IPerceptionEngine, "get_metrics")
        assert hasattr(IPerceptionEngine, "get_status")

    def test_cannot_instantiate_iperceptionengine(self):
        """测试不能直接实例化IPerceptionEngine"""
        with pytest.raises(TypeError):
            IPerceptionEngine()


class TestICache:
    """测试ICache接口"""

    def test_icache_is_abstract(self):
        """测试ICache是抽象基类"""
        assert issubclass(ICache, ABC)

    def test_icache_has_required_methods(self):
        """测试ICache有必需的方法"""
        assert hasattr(ICache, "get")
        assert hasattr(ICache, "set")
        assert hasattr(ICache, "delete")
        assert hasattr(ICache, "clear")
        assert hasattr(ICache, "exists")
        assert hasattr(ICache, "get_stats")

    def test_cannot_instantiate_icache(self):
        """测试不能直接实例化ICache"""
        with pytest.raises(TypeError):
            ICache()


class TestIMonitor:
    """测试IMonitor接口"""

    def test_imonitor_is_abstract(self):
        """测试IMonitor是抽象基类"""
        assert issubclass(IMonitor, ABC)

    def test_imonitor_has_required_methods(self):
        """测试IMonitor有必需的方法"""
        assert hasattr(IMonitor, "start_monitoring")
        assert hasattr(IMonitor, "stop_monitoring")
        assert hasattr(IMonitor, "record_request")
        assert hasattr(IMonitor, "get_metrics")
        assert hasattr(IMonitor, "get_performance_report")

    def test_cannot_instantiate_imonitor(self):
        """测试不能直接实例化IMonitor"""
        with pytest.raises(TypeError):
            IMonitor()


class TestIProcessorFactory:
    """测试IProcessorFactory接口"""

    def test_iprocessorfactory_is_abstract(self):
        """测试IProcessorFactory是抽象基类"""
        assert issubclass(IProcessorFactory, ABC)

    def test_iprocessorfactory_has_required_methods(self):
        """测试IProcessorFactory有必需的方法"""
        assert hasattr(IProcessorFactory, "create_processor")
        assert hasattr(IProcessorFactory, "register_processor")
        assert hasattr(IProcessorFactory, "get_supported_types")

    def test_cannot_instantiate_iprocessorfactory(self):
        """测试不能直接实例化IProcessorFactory"""
        with pytest.raises(TypeError):
            IProcessorFactory()


class TestInterfaceImplementation:
    """测试接口实现示例"""

    def test_concrete_processor_implementation(self):
        """测试具体的处理器实现"""

        class ConcreteProcessor(IProcessor):
            def __init__(self):
                self.initialized = False

            async def initialize(self) -> bool:
                self.initialized = True
                return True

            async def process(self, data, input_type, mode=ProcessingMode.STANDARD, **kwargs):
                return PerceptionResult(
                    input_type=input_type,
                    raw_content=data,
                    processed_content=f"processed: {data}",
                    features={"length": len(str(data))},
                    confidence=0.95,
                    metadata={},
                    timestamp=datetime.now()
                )

            async def cleanup(self) -> bool:
                self.initialized = False
                return True

            def health_check(self) -> bool:
                return self.initialized

        processor = ConcreteProcessor()
        assert isinstance(processor, IProcessor)
        assert hasattr(processor, "initialize")
        assert hasattr(processor, "process")
        assert hasattr(processor, "cleanup")
        assert hasattr(processor, "health_check")

    def test_concrete_stream_processor_implementation(self):
        """测试具体的流处理器实现"""
        from collections.abc import AsyncIterator

        class ConcreteStreamProcessor(IStreamProcessor):
            def __init__(self):
                self.initialized = False

            async def initialize(self) -> bool:
                self.initialized = True
                return True

            async def process(self, data, input_type, mode=ProcessingMode.STANDARD, **kwargs):
                return PerceptionResult(
                    input_type=input_type,
                    raw_content=data,
                    processed_content=f"processed: {data}",
                    features={},
                    confidence=1.0,
                    metadata={},
                    timestamp=datetime.now()
                )

            async def stream_process(self, data_stream, input_type, config=None):
                for data in data_stream:
                    yield PerceptionResult(
                        input_type=input_type,
                        raw_content=data,
                        processed_content=f"streamed: {data}",
                        features={},
                        confidence=1.0,
                        metadata={},
                        timestamp=datetime.now()
                    )

            async def process_batch(self, data_list, input_type, **kwargs):
                return [
                    PerceptionResult(
                        input_type=input_type,
                        raw_content=data,
                        processed_content=f"batch: {data}",
                        features={},
                        confidence=1.0,
                        metadata={},
                        timestamp=datetime.now()
                    )
                    for data in data_list
                ]

            async def cleanup(self) -> bool:
                self.initialized = False
                return True

            def health_check(self) -> bool:
                return self.initialized

        processor = ConcreteStreamProcessor()
        assert isinstance(processor, IStreamProcessor)
        assert isinstance(processor, IProcessor)

    def test_concrete_cache_implementation(self):
        """测试具体的缓存实现"""

        class ConcreteCache(ICache):
            def __init__(self):
                self._cache = {}

            async def get(self, key):
                return self._cache.get(key)

            async def set(self, key, value, ttl=None):
                self._cache[key] = value
                return True

            async def delete(self, key):
                return self._cache.pop(key, None) is not None

            async def clear(self):
                self._cache.clear()
                return True

            async def exists(self, key):
                return key in self._cache

            async def get_stats(self):
                return {"size": len(self._cache)}

        cache = ConcreteCache()
        assert isinstance(cache, ICache)

    def test_concrete_monitor_implementation(self):
        """测试具体的监控实现"""

        class ConcreteMonitor(IMonitor):
            def __init__(self):
                self.monitoring = False
                self._metrics = []

            async def start_monitoring(self):
                self.monitoring = True

            async def stop_monitoring(self):
                self.monitoring = False

            def record_request(self, latency, success, metadata=None):
                self._metrics.append({
                    "latency": latency,
                    "success": success,
                    "metadata": metadata or {}
                })

            def get_metrics(self):
                return {"request_count": len(self._metrics)}

            def get_performance_report(self):
                return {
                    "total_requests": len(self._metrics),
                    "avg_latency": sum(m["latency"] for m in self._metrics) / len(self._metrics) if self._metrics else 0
                }

        monitor = ConcreteMonitor()
        assert isinstance(monitor, IMonitor)


class TestInterfaceInheritance:
    """测试接口继承"""

    def test_istreamprocessor_inherits_iprocessor(self):
        """测试IStreamProcessor继承IProcessor"""
        # IStreamProcessor继承自IProcessor
        assert issubclass(IStreamProcessor, IProcessor)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
