# Athena感知模块 - 用户手册

## 目录

1. [系统概述](#系统概述)
2. [核心概念](#核心概念)
3. [详细功能说明](#详细功能说明)
4. [API参考](#api参考)
5. [配置指南](#配置指南)
6. [最佳实践](#最佳实践)
7. [故障排除](#故障排除)
8. [性能调优](#性能调优)

---

## 系统概述

Athena感知模块是一个企业级的多模态数据处理引擎，专为处理复杂的感知任务而设计。该模块采用模块化架构，提供了高度可扩展和可配置的API。

### 主要组件

```
感知模块 (Perception Module)
├── 核心处理器 (Processors)
│   ├── TextProcessor - 文本处理
│   ├── ImageProcessor - 图像处理
│   ├── AudioProcessor - 音频处理
│   ├── VideoProcessor - 视频处理
│   └── MultimodalProcessor - 多模态处理
├── 性能优化 (Performance)
│   ├── PerformanceOptimizer - 性能优化器
│   └── 缓存系统 (Caching)
├── 流式处理 (Streaming)
│   └── StreamingPerceptionEngine - 流式引擎
├── 监控系统 (Monitoring)
│   ├── PerformanceMonitor - 性能监控
│   └── MetricsCollector - 指标收集
└── 工厂模式 (Factory)
    └── PerceptionBuilder - 构建器
```

---

## 核心概念

### 1. 处理器 (Processor)

处理器是感知模块的核心组件，负责处理特定类型的数据。每个处理器继承自`BaseProcessor`基类。

#### 处理器生命周期

```python
# 1. 创建处理器
processor = TextProcessor("my_processor", config)

# 2. 初始化
await processor.initialize()

# 3. 处理数据
result = await processor.process(data, input_type)

# 4. 清理资源
await processor.cleanup()
```

### 2. 输入类型 (InputType)

支持的输入类型：

- `TEXT` - 文本数据
- `IMAGE` - 图像数据
- `AUDIO` - 音频数据
- `VIDEO` - 视频数据
- `MULTIMODAL` - 多模态数据
- `UNKNOWN` - 未知类型

### 3. 处理结果 (PerceptionResult)

处理结果包含：

```python
@dataclass
class PerceptionResult:
    input_type: InputType           # 输入类型
    raw_content: Any                 # 原始内容
    processed_content: Any          # 处理后内容
    features: dict[str, Any]         # 提取的特征
    confidence: float                # 置信度 (0-1)
    metadata: dict[str, Any]         # 元数据
    timestamp: datetime              # 处理时间戳
```

### 4. 性能优化

#### 缓存策略

```python
from core.perception.types import CacheConfig
from datetime import timedelta

cache_config = CacheConfig(
    result_cache_ttl=timedelta(hours=1),     # 结果缓存TTL
    ocr_cache_ttl=timedelta(days=7),         # OCR缓存TTL
    metadata_cache_ttl=timedelta(minutes=10)  # 元数据缓存TTL
)
```

#### 批处理

```python
optimizer = PerformanceOptimizer({
    "enable_batch_processing": True,
    "max_batch_size": 10,
    "batch_timeout_ms": 100
})

# 批量处理
items = [{"data": data, "input_type": "text"} for data in datasets]
results = await optimizer.batch_process(processor, items)
```

---

## 详细功能说明

### 文本处理

```python
from core.perception import TextProcessor

# 创建配置
config = {
    "enable_sentiment_analysis": True,    # 启用情感分析
    "enable_entity_extraction": True,      # 启用实体提取
    "enable_keyword_extraction": True,     # 启用关键词提取
    "max_text_length": 10000               # 最大文本长度
}

processor = TextProcessor("text_processor", config)
await processor.initialize()

# 处理文本
text = "Athena是一个优秀的AI智能平台"
result = await processor.process(text, "text")

# 访问特征
if "sentiment" in result.features:
    sentiment = result.features["sentiment"]
    print(f"情感倾向: {sentiment}")

if "entities" in result.features:
    entities = result.features["entities"]
    print(f"识别实体: {entities}")

await processor.cleanup()
```

### 图像处理

```python
from core.perception import ImageProcessor

config = {
    "max_size": 10 * 1024 * 1024,    # 10MB
    "supported_formats": [".jpg", ".png", ".gif"],
    "enable_ocr": True,              # 启用OCR
    "enable_face_detection": False   # 启用人脸检测
}

processor = ImageProcessor("image_processor", config)
await processor.initialize()

# 读取并处理图像
with open("document.jpg", "rb") as f:
    image_data = f.read()

result = await processor.process(image_data, "image")

# 访问OCR结果
if "text" in result.features:
    ocr_text = result.features["text"]
    print(f"OCR文本: {ocr_text}")

await processor.cleanup()
```

### 流式处理

```python
from core.perception.streaming_perception_processor import (
    StreamingPerceptionEngine,
    StreamConfig,
    StreamType
)

# 配置流式引擎
config = StreamConfig(
    buffer_size=1000,              # 缓冲区大小
    max_queue_size=5000,           # 队列大小
    enable_backpressure=True,      # 启用背压
    chunk_size=1024                # 数据块大小
)

engine = StreamingPerceptionEngine(config)
await engine.initialize()

# 启动流
stream_id = "document_stream"
await engine.start_streaming(stream_id, StreamType.TEXT)

# 发送数据块
chunks = ["这是", "第一段", "文档", "内容"]
for chunk in chunks:
    await engine.put_chunk(stream_id, chunk)

# 结束流
await engine.end_stream(stream_id)
```

### 性能监控

```python
from core.perception.monitoring import PerformanceMonitor

# 创建监控器
monitor = PerformanceMonitor(
    window_size=1000,      # 滑动窗口大小
    update_interval=10,    # 更新间隔(秒)
    enable_alerts=True     # 启用告警
)

# 配置告警阈值
monitor.alert_thresholds = {
    "p95_latency": 5.0,        # P95延迟阈值(秒)
    "error_rate": 0.1,         # 错误率阈值
    "memory_usage": 0.85,       # 内存使用率阈值
    "cpu_usage": 0.80           # CPU使用率阈值
}

# 记录处理事件
monitor.record_request(
    latency=0.15,
    success=True,
    confidence=0.92
)

# 获取指标
metrics = monitor.get_metrics()
print(f"总请求数: {metrics['total_requests']}")
print(f"成功率: {metrics['success_rate']}")

# 获取性能报告
report = monitor.get_performance_report()
print(f"平均响应时间: {report['avg_response_time']}秒")
```

---

## API参考

### PerceptionEngine

```python
class PerceptionEngine:
    def __init__(
        self,
        engine_id: str,
        config: dict[str, Any],
        cache_config: CacheConfig | None = None
    ):
        """初始化感知引擎"""

    async def initialize(self) -> None:
        """初始化引擎"""

    async def process(
        self,
        data: Any,
        input_type: str,
        metadata: dict[str, Any] | None = None
    ) -> PerceptionResult:
        """处理数据"""

    async def shutdown(self) -> None:
        """关闭引擎"""
```

### TextProcessor

```python
class TextProcessor(BaseProcessor):
    def __init__(
        self,
        processor_id: str,
        config: dict[str, Any]
    ):
        """初始化文本处理器"""

    async def process(
        self,
        data: str,
        input_type: str
    ) -> PerceptionResult:
        """处理文本数据"""
```

### PerformanceOptimizer

```python
class PerformanceOptimizer:
    def __init__(
        self,
        config: dict[str, Any] | None = None
    ):
        """初始化性能优化器"""

    async def batch_process(
        self,
        processor: BaseProcessor,
        items: list[dict[str, Any]],
        max_concurrent: int | None = None
    ) -> list[PerceptionResult]:
        """批量处理"""

    def cache_decorator(self, func: Callable) -> Callable:
        """缓存装饰器"""

    async def invalidate_cache(
        self,
        pattern: str | None = None
    ) -> None:
        """失效缓存"""
```

### StreamingPerceptionEngine

```python
class StreamingPerceptionEngine:
    def __init__(
        self,
        config: StreamConfig | None = None
    ):
        """初始化流式引擎"""

    async def initialize(self) -> None:
        """初始化引擎"""

    async def start_streaming(
        self,
        stream_id: str,
        stream_type: StreamType
    ) -> str:
        """启动数据流"""

    async def put_chunk(
        self,
        stream_id: str,
        data: Any,
        metadata: dict[str, Any] | None = None
    ) -> bool:
        """发送数据块"""

    async def end_stream(
        self,
        stream_id: str
    ) -> None:
        """结束数据流"""
```

---

## 配置指南

### 全局配置

```python
# config/perception.yaml
perception:
  # 文本处理配置
  text:
    enable_sentiment_analysis: true
    enable_entity_extraction: true
    enable_keyword_extraction: true
    max_text_length: 10000

  # 图像处理配置
  image:
    max_size: 10485760  # 10MB
    supported_formats:
      - .jpg
      - .png
      - .gif
      - .bmp
    enable_ocr: true
    ocr_engine: rapidocr

  # 性能配置
  performance:
    enable_cache: true
    enable_batch_processing: true
    max_batch_size: 10
    max_workers: 4

  # 缓存配置
  cache:
    result_cache_ttl: 3600     # 1小时
    ocr_cache_ttl: 604800       # 7天
    metadata_cache_ttl: 600    # 10分钟

  # 监控配置
  monitoring:
    enabled: true
    collect_interval: 10        # 秒
    enable_alerts: true

  # 流式配置
  streaming:
    buffer_size: 1000
    max_queue_size: 5000
    enable_backpressure: true
```

### 环境变量

```bash
# .env
PERCEPTION_CACHE_ENABLED=true
PERFORMANCE_MAX_WORKERS=4
MONITORING_ENABLED=true
LOG_LEVEL=INFO
```

---

## 最佳实践

### 1. 资源管理

始终正确处理处理器的生命周期：

```python
async def process_documents(documents: list[str]):
    processor = TextProcessor("batch_processor", {})
    try:
        await processor.initialize()

        results = []
        for doc in documents:
            result = await processor.process(doc, "text")
            results.append(result)

        return results
    finally:
        await processor.cleanup()
```

### 2. 错误处理

```python
async def safe_process(processor: BaseProcessor, data: str):
    try:
        result = await processor.process(data, "text")

        if result.confidence < 0.5:
            logger.warning(f"低置信度结果: {result.confidence}")

        return result
    except Exception as e:
        logger.error(f"处理失败: {e}")
        # 返回默认结果或重试
        return None
```

### 3. 性能优化

```python
# 使用连接池
async def create_processor_pool(size: int = 5):
    processors = []
    for i in range(size):
        processor = TextProcessor(f"pool_{i}", {})
        await processor.initialize()
        processors.append(processor)
    return processors

# 轮询分配任务
async def process_with_pool(processors: list[BaseProcessor], items: list[str]):
    results = []
    for i, item in enumerate(items):
        processor = processors[i % len(processors)]
        result = await processor.process(item, "text")
        results.append(result)
    return results
```

### 4. 监控和日志

```python
import logging
from core.perception.monitoring import PerformanceMonitor, track_performance

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# 使用监控装饰器
monitor = PerformanceMonitor(enable_alerts=True)

@track_performance("document_processor", "process_document")
async def process_document(text: str) -> str:
    # 处理逻辑
    return text.upper()
```

---

## 故障排除

### 常见问题

#### 问题1: 内存泄漏

**症状**: 长时间运行后内存持续增长

**解决方案**:
```python
# 定期清理缓存
async def periodic_cleanup(optimizer: PerformanceOptimizer):
    while True:
        await asyncio.sleep(300)  # 每5分钟
        await optimizer.invalidate_cache()
        await optimizer.cleanup_expired()
```

#### 问题2: 处理延迟高

**症状**: 处理请求响应时间长

**解决方案**:
```python
# 1. 启用缓存
optimizer = PerformanceOptimizer({
    "enable_cache": True,
    "enable_batch_processing": True
})

# 2. 使用批处理
items = [{"data": d, "input_type": "text"} for d in data_list]
results = await optimizer.batch_process(processor, items, max_concurrent=10)

# 3. 检查性能瓶颈
report = monitor.get_performance_report()
print(report["recommendations"])
```

#### 问题3: OCR识别错误

**症状**: OCR结果不准确

**解决方案**:
```python
from core.perception.chinese_ocr_optimizer import ChineseOCROptimizer

# 使用OCR优化器
optimizer = ChineseOCROptimizer()

# 预处理图像
preprocessed_path = await optimizer.preprocess_image(
    input_path="raw.jpg",
    output_path="preprocessed.jpg"
)

# 纠错文本
corrected = await optimizer.correct_text("这  是  测  试")
```

### 调试技巧

```python
# 启用详细日志
import logging
logging.getLogger("core.perception").setLevel(logging.DEBUG)

# 检查处理器状态
print(f"处理器状态: {processor.is_initialized}")
print(f"配置: {processor.config}")

# 监控性能
import time
start = time.time()
result = await processor.process(data, "text")
elapsed = time.time() - start
print(f"处理时间: {elapsed:.3f}秒")
```

---

## 性能调优

### 性能基准

| 操作类型 | 平均延迟 | P95延迟 | 吞吐量 |
|---------|---------|--------|--------|
| 文本处理 | 10ms | 50ms | 100次/秒 |
| 图像处理 | 200ms | 500ms | 5次/秒 |
| OCR处理 | 500ms | 2000ms | 2次/秒 |
| 批处理(10项) | 50ms | 200ms | 200次/秒 |

### 优化建议

1. **启用缓存**: 相同输入可节省90%+处理时间
2. **批处理**: 批量处理比单独处理快3-5倍
3. **并发处理**: 使用asyncio.gather并发执行
4. **流式处理**: 大数据集使用流式处理避免内存溢出

### 性能监控

```python
# 定期检查性能
async def monitor_performance():
    monitor = PerformanceMonitor()

    while True:
        await asyncio.sleep(60)  # 每分钟

        metrics = monitor.get_metrics()

        # 检查告警条件
        if metrics["error_rate"] > 0.1:
            logger.error(f"错误率过高: {metrics['error_rate']}")

        if metrics["latency"]["p95"] > 5.0:
            logger.warning(f"P95延迟过高: {metrics['latency']['p95']}秒")
```

---

## 附录

### 术语表

- **处理器 (Processor)**: 处理特定类型数据的组件
- **输入类型 (InputType)**: 数据类型的枚举
- **感知结果 (PerceptionResult)**: 处理后的返回值
- **缓存 (Cache)**: 存储处理结果以提升性能
- **流式处理 (Streaming)**: 处理连续数据流的方式

### 版本历史

- **v1.0.0** (2026-01-24): 初始版本
  - 核心处理器实现
  - 性能优化和监控
  - 流式处理支持
  - 完整测试覆盖

---

**文档版本**: 1.0.0
**最后更新**: 2026-01-24
**维护者**: Athena AI团队
