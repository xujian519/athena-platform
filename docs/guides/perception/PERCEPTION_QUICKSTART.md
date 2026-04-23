# Athena感知模块 - 快速入门指南

## 概述

Athena感知模块 (Perception Module) 是一个企业级的多模态数据处理系统，提供文本、图像、音频、视频等多种输入类型的智能处理能力。

### 核心特性

- 🔄 **多模态支持**: 文本、图像、音频、视频统一处理
- ⚡ **高性能**: 内置缓存、批处理、异步优化
- 📊 **性能监控**: 实时监控处理性能和系统资源
- 🔌 **流式处理**: 支持大规模数据流的实时处理
- 🎯 **智能缓存**: 多级缓存策略，显著提升响应速度

## 快速开始

### 1. 环境准备

```bash
# 确保Python版本 >= 3.14
python --version

# 安装依赖
poetry install

# 或使用pip
pip install -e .
```

### 2. 基础使用

#### 文本处理

```python
from core.perception import TextProcessor

# 创建处理器
processor = TextProcessor("my_text_processor", {})
await processor.initialize()

# 处理文本
text = "这是一段需要处理的中文文本"
result = await processor.process(text, "text")

# 查看结果
print(f"输入类型: {result.input_type}")
print(f"置信度: {result.confidence}")
print(f"处理内容: {result.processed_content}")
print(f"特征: {result.features}")

# 清理资源
await processor.cleanup()
```

#### 图像处理

```python
from core.perception import ImageProcessor

# 创建图像处理器
processor = ImageProcessor("my_image_processor", {})
await processor.initialize()

# 处理图像
with open("image.jpg", "rb") as f:
    image_data = f.read()

result = await processor.process(image_data, "image")

# 清理资源
await processor.cleanup()
```

### 3. 使用感知引擎 (推荐)

感知引擎提供了统一的接口来处理多种输入类型：

```python
from core.perception import PerceptionEngine

# 创建感知引擎
engine = PerceptionEngine("my_engine", {
    "text": {
        "enable_sentiment_analysis": True,
        "enable_entity_extraction": True
    },
    "image": {
        "max_size": 10 * 1024 * 1024  # 10MB
    }
})

await engine.initialize()

# 处理不同类型的输入
text_result = await engine.process("处理这段文本", "text")
image_result = await engine.process(image_bytes, "image")

# 关闭引擎
await engine.shutdown()
```

### 4. 性能优化

#### 启用缓存

```python
from core.perception import PerceptionEngine
from core.perception.types import CacheConfig
from datetime import timedelta

# 创建带缓存的引擎
engine = PerceptionEngine("cached_engine", {},
    cache_config=CacheConfig(
        result_cache_ttl=timedelta(hours=1)
    )
)

await engine.initialize()

# 重复处理会自动命中缓存
result1 = await engine.process("测试文本", "text")
result2 = await engine.process("测试文本", "text")  # 从缓存返回

await engine.shutdown()
```

#### 使用性能优化器

```python
from core.perception.performance_optimizer import PerformanceOptimizer
from core.perception import TextProcessor

optimizer = PerformanceOptimizer({
    "enable_cache": True,
    "enable_batch_processing": True,
    "max_batch_size": 10
})

processor = TextProcessor("optimized_processor", {})
await processor.initialize()

# 批量处理
items = [{"data": f"文本 {i}", "input_type": "text"} for i in range(20)]
results = await optimizer.batch_process(processor, items)

await processor.cleanup()
```

### 5. 流式处理

对于大规模数据流，使用流式处理器：

```python
from core.perception.streaming_perception_processor import (
    StreamingPerceptionEngine,
    StreamConfig,
    StreamType
)

# 配置流式引擎
config = StreamConfig(
    buffer_size=1000,
    max_queue_size=5000,
    enable_backpressure=True
)

engine = StreamingPerceptionEngine(config)
await engine.initialize()

# 启动数据流
stream_id = "my_stream"
await engine.start_streaming(stream_id, StreamType.TEXT)

# 发送数据块
for chunk in ["数据块1", "数据块2", "数据块3"]:
    await engine.put_chunk(stream_id, chunk)

# 结束流
await engine.end_stream(stream_id)
```

### 6. 性能监控

```python
from core.perception.monitoring import PerformanceMonitor

# 创建性能监控器
monitor = PerformanceMonitor(
    window_size=1000,
    enable_alerts=True
)

# 记录处理事件
monitor.record_request(
    latency=0.123,  # 处理延迟(秒)
    success=True,
    confidence=0.95
)

# 获取性能指标
metrics = monitor.get_metrics()
print(f"总请求数: {metrics['total_requests']}")
print(f"成功率: {metrics['success_rate']}")
print(f"平均延迟: {metrics['latency']['avg']}")

# 获取性能报告
report = monitor.get_performance_report()
```

## 高级功能

### 自定义处理器

```python
from core.perception import BaseProcessor, InputType, PerceptionResult
from core.perception.types import ProcessorConfig

class CustomProcessor(BaseProcessor):
    def __init__(self, processor_id: str, config: ProcessorConfig):
        super().__init__(processor_id, config)
        # 初始化自定义资源

    async def initialize(self):
        # 自定义初始化逻辑
        pass

    async def process(self, data: str, input_type: InputType) -> PerceptionResult:
        # 自定义处理逻辑
        return PerceptionResult(
            input_type=input_type,
            raw_content=data,
            processed_content=data.upper(),
            confidence=1.0,
            features={"custom": True}
        )

    async def cleanup(self):
        # 清理自定义资源
        pass
```

### 处理器工厂

```python
from core.perception import PerceptionBuilder

# 使用构建器创建复杂处理器
processor = (PerceptionBuilder()
    .with_id("complex_processor")
    .with_config({"custom_option": True})
    .with_middleware([
        LoggingMiddleware(),
        CacheMiddleware()
    ])
    .build(TextProcessor))
```

## 常见问题

### Q: 如何处理大量数据？

A: 使用批处理和流式处理：

```python
# 批处理
items = [f"文本 {i}" for i in range(1000)]
results = await optimizer.batch_process(processor, items)

# 流式处理
for chunk in large_data_stream:
    await engine.put_chunk(stream_id, chunk)
```

### Q: 如何提升处理速度？

A: 启用缓存和批处理：

```python
optimizer = PerformanceOptimizer({
    "enable_cache": True,
    "enable_batch_processing": True,
    "max_workers": 4
})
```

### Q: 如何监控性能？

A: 使用性能监控器：

```python
monitor = PerformanceMonitor(enable_alerts=True)
# 处理请求时记录
monitor.record_request(latency=0.1, success=True)
# 查看报告
report = monitor.get_performance_report()
```

## 测试

```bash
# 运行所有测试
pytest tests/core/perception/ -v

# 运行特定类型测试
pytest tests/core/perception/ -m unit          # 单元测试
pytest tests/core/perception/ -m integration   # 集成测试
pytest tests/core/perception/ -m performance  # 性能测试

# 查看测试覆盖率
pytest tests/core/perception/ --cov=core.perception --cov-report=html
```

## 相关文档

- [完整API文档](./API.md)
- [架构设计文档](./ARCHITECTURE.md)
- [性能优化指南](./PERFORMANCE.md)
- [部署指南](./DEPLOYMENT.md)

## 支持

如有问题或建议，请联系开发团队或提交Issue。

---

**版本**: 1.0.0
**最后更新**: 2026-01-24
