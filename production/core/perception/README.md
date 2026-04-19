# 感知模块 (Perception Module)

[![Python Version](https://img.shields.io/badge/python-3.14+-blue.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![Code Quality](https://img.shields.io/badge/code%20quality-8.5%2F10-brightgreen.svg)](https://github.com)

## 概述

感知模块是 Athena 工作平台的核心组件之一，负责多模态输入的感知和处理，包括文本、图像、音频、视频等多种数据类型的智能处理。

### 主要特性

- ✅ **多模态处理**: 支持文本、图像、音频、视频等多种输入类型
- ✅ **异步架构**: 基于 asyncio 的高性能异步处理
- ✅ **流式处理**: 支持实时流式数据处理
- ✅ **智能缓存**: 三层缓存架构，提升处理性能
- ✅ **性能监控**: 完善的性能监控和告警机制
- ✅ **容错机制**: 错误处理、重试和降级策略
- ✅ **安全验证**: 统一的输入验证和权限控制

## 架构设计

```
core/perception/
├── __init__.py                 # 模块入口，导出主要类
├── interfaces.py               # 统一接口定义
├── types.py                   # 类型定义
├── factory.py                 # 工厂模式，创建处理器
├── base_processor.py          # 基础处理器类
├── processors/                # 专用处理器
│   ├── text_processor.py      # 文本处理
│   ├── image_processor.py     # 图像处理
│   ├── audio_processor.py     # 音频处理
│   ├── video_processor.py     # 视频处理
│   └── multimodal_processor.py # 多模态处理
├── monitoring.py              # 性能监控
├── error_handler.py          # 错误处理
├── validation.py             # 输入验证
├── exceptions.py             # 自定义异常
├── access_control.py         # 权限控制
└── tests/                    # 测试文件
```

## 快速开始

### 安装依赖

```bash
# 基础依赖
pip install fastapi uvicorn pydantic

# 图像处理
pip install opencv-python pillow

# OCR支持
pip install pytesseract paddleocr

# 可选：深度学习支持
pip install torch torchvision
```

### 基础使用

```python
import asyncio
from core.perception import PerceptionEngine, InputType

async def main():
    # 创建感知引擎
    engine = PerceptionEngine(agent_id="test_agent")

    # 初始化引擎
    await engine.initialize()

    # 处理文本
    result = await engine.perceive(
        input_data="这是一段测试文本",
        input_type=InputType.TEXT
    )
    print(f"处理结果: {result}")

    # 处理图像
    result = await engine.perceive(
        input_data="/path/to/image.jpg",
        input_type=InputType.IMAGE
    )

    # 清理资源
    await engine.shutdown()

if __name__ == "__main__":
    asyncio.run(main())
```

### 高级使用

#### 流式处理

```python
async def process_stream():
    engine = PerceptionEngine(agent_id="stream_agent")
    await engine.initialize()

    # 创建数据流
    async def data_stream():
        for i in range(10):
            yield f"数据块 {i}"

    # 流式处理
    async for result in engine.stream_perceive(
        data_stream(),
        input_type=InputType.TEXT
    ):
        print(f"流式结果: {result}")

    await engine.shutdown()
```

#### 批量处理

```python
async def batch_process():
    engine = PerceptionEngine(agent_id="batch_agent")
    await engine.initialize()

    # 批量处理
    data_list = ["文本1", "文本2", "文本3"]
    results = await engine.batch_perceive(
        data_list=data_list,
        input_type=InputType.TEXT
    )

    for result in results:
        print(f"批量结果: {result}")

    await engine.shutdown()
```

## 配置

### 环境变量

```bash
# 日志配置
export LOG_LEVEL=INFO
export LOG_FILE=/var/log/perception.log

# 性能配置
export MAX_CONCURRENT_REQUESTS=100
export CACHE_TTL=3600
export BATCH_SIZE=50

# 安全配置
export ENABLE_AUTH=true
export API_KEY=your_api_key_here
```

### 配置文件

```python
# perception_config.py
PERCEPTION_CONFIG = {
    "max_concurrent_requests": 100,
    "cache_ttl": 3600,
    "enable_monitoring": True,
    "enable_validation": True,
    "enable_access_control": False,

    "processors": {
        "text": {
            "enabled": True,
            "max_length": 10000,
        },
        "image": {
            "enabled": True,
            "max_size_mb": 10.0,
            "supported_formats": [".jpg", ".png", ".gif"],
        },
    },
}
```

## API 文档

### 核心类

#### PerceptionEngine

主要的感知引擎类，负责协调各种处理器。

```python
class PerceptionEngine:
    async def initialize(self) -> bool
    async def perceive(self, input_data: Any, input_type: InputType, **kwargs) -> PerceptionResult
    async def stream_perceive(self, data_stream: AsyncIterator, **kwargs) -> AsyncIterator[PerceptionResult]
    async def health_check(self) -> dict[str, Any]
    async def shutdown(self) -> bool
```

#### BaseProcessor

处理器基类，所有处理器都继承此类。

```python
class BaseProcessor(ABC):
    @abstractmethod
    async def initialize(self) -> bool

    @abstractmethod
    async def process(self, data: Any, input_type: str) -> PerceptionResult

    @abstractmethod
    async def cleanup(self) -> bool

    def health_check(self) -> bool
```

### 接口定义

详见 [interfaces.py](interfaces.py) - 定义了所有标准接口：
- `IProcessor`: 基础处理器接口
- `IStreamProcessor`: 流式处理器接口
- `IPerceptionEngine`: 感知引擎接口
- `ICache`: 缓存接口
- `IMonitor`: 监控接口

## 性能优化

### 缓存策略

感知模块使用三层缓存架构：

1. **内存缓存**: 最快的访问速度，存储热点数据
2. **Redis缓存**: 分布式缓存，支持多实例共享
3. **数据库缓存**: 持久化缓存，容量大

```python
# 启用缓存
engine = PerceptionEngine(
    agent_id="cache_agent",
    config={
        "enable_cache": True,
        "cache_ttl": 3600,
        "cache_size": 1000,
    }
)
```

### 并发控制

```python
# 配置并发限制
engine = PerceptionEngine(
    agent_id="concurrent_agent",
    config={
        "max_concurrent_requests": 100,
        "max_batch_size": 50,
        "request_timeout": 30.0,
    }
)
```

## 监控和告警

### 性能指标

```python
from core.perception.monitoring import get_global_monitor

monitor = get_global_monitor()
await monitor.start_monitoring()

# 获取性能指标
metrics = monitor.get_metrics()
print(f"平均延迟: {metrics['latency']['average']} ms")
print(f"P95延迟: {metrics['latency']['p95']} ms")
print(f"吞吐量: {metrics['throughput']['per_second']} req/s")
```

### 告警配置

```python
monitor.alert_thresholds = {
    "p95_latency": 5.0,      # P95延迟超过5秒告警
    "error_rate": 0.05,       # 错误率超过5%告警
    "memory_usage": 0.8,      # 内存使用超过80%告警
}
```

## 安全性

### 输入验证

```python
from core.perception.validation import get_global_validator

validator = get_global_validator()

# 验证字符串输入
result = validator.validate(
    value="用户输入",
    validator_name="strict_string",
    field_name="username"
)

if not result.is_valid:
    print(f"验证失败: {result.errors}")
```

### 权限控制

```python
from core.perception.access_control import get_global_access_control, Permission

access_control = get_global_access_control()

# 检查权限
if access_control.check_permission("user_id", Permission.PROCESS_IMAGE):
    # 执行需要权限的操作
    pass
```

## 测试

### 运行测试

```bash
# 运行所有测试
pytest core/perception/tests/

# 运行特定测试
pytest core/perception/tests/test_validation.py

# 生成覆盖率报告
pytest --cov=core.perception --cov-report=html
```

### 性能测试

```bash
# 运行性能压力测试
python core/perception/test_performance_stress.py
```

## 故障排查

### 常见问题

#### 1. 导入错误

```python
# 错误: ImportError: cannot import name 'PerceptionEngine'
# 解决: 确保正确设置Python路径
import sys
sys.path.insert(0, '/path/to/Athena工作平台')
```

#### 2. 处理器初始化失败

```python
# 错误: InitializationError
# 解决: 检查依赖是否安装完整
pip list | grep -E "opencv|torch|pillow"
```

#### 3. 内存不足

```python
# 错误: MemoryError
# 解决: 调整并发限制或批处理大小
engine.config["max_concurrent_requests"] = 50
```

### 日志查看

```bash
# 查看应用日志
tail -f /var/log/perception.log

# 查看错误日志
grep ERROR /var/log/perception.log
```

## 贡献指南

欢迎贡献代码！请遵循以下步骤：

1. Fork 本仓库
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 开启 Pull Request

### 代码规范

- 遵循 PEP 8 编码规范
- 使用类型注解
- 添加完整的文档字符串
- 编写单元测试

## 许可证

本项目采用 MIT 许可证 - 详见 [LICENSE](LICENSE) 文件

## 联系方式

- 项目维护者: Athena AI系统
- 问题反馈: [GitHub Issues](https://github.com/your-repo/issues)
- 邮箱: support@athena-platform.com

## 更新日志

### v3.0.0 (2026-01-26)

- ✅ 新增统一输入验证框架
- ✅ 新增自定义异常类体系
- ✅ 新增权限控制系统
- ✅ 优化性能监控
- ✅ 修复安全问题
- ✅ 提升测试覆盖率

### v2.0.0 (2025-12-15)

- ✅ 重构为异步架构
- ✅ 新增多模态支持
- ✅ 新增流式处理

### v1.0.0 (2025-12-04)

- ✅ 初始版本
- ✅ 基础感知功能

## 相关文档

- [架构设计文档](ARCHITECTURE.md)
- [API完整文档](API.md)
- [部署指南](DEPLOYMENT.md)
- [安全指南](SECURITY.md)
- [性能优化指南](PERFORMANCE.md)

---

**Athena 工作平台** - 企业级AI智能平台

© 2025-2026 Athena AI System. All rights reserved.
