# 意图识别服务 - 开发和使用最佳实践

## 目录

- [概述](#概述)
- [开发最佳实践](#开发最佳实践)
- [使用最佳实践](#使用最佳实践)
- [性能优化指南](#性能优化指南)
- [故障排查指南](#故障排查指南)
- [部署建议](#部署建议)

---

## 概述

本文档提供意图识别服务的开发和使用的最佳实践，帮助开发者高效地集成和使用该服务。

---

## 开发最佳实践

### 1. 引擎开发规范

#### 1.1 继承BaseIntentEngine

所有意图识别引擎都应该继承`BaseIntentEngine`基类：

```python
from core.intent.base_engine import BaseIntentEngine

class MyIntentEngine(BaseIntentEngine):
    engine_name = "my_engine"
    engine_version = "1.0.0"
    supported_intents = {IntentType.PATENT_SEARCH}

    def _initialize(self) -> None:
        """初始化引擎"""
        pass

    def recognize_intent(self, text: str, context: Optional[dict] = None) -> IntentResult:
        """识别意图"""
        # 1. 验证输入
        self._validate_input(text)

        # 2. 预处理
        normalized_text = self._normalize_text(text)

        # 3. 提取实体
        entities = self._extract_entities(normalized_text)

        # 4. 返回结果
        return IntentResult(...)
```

#### 1.2 使用公共工具函数

优先使用`core/intent/utils.py`中的工具函数，避免重复造轮子：

```python
from core.intent.utils import (
    TextPreprocessor,
    EntityExtractor,
    KeywordMatcher,
    SimpleCache
)

# 使用文本预处理器
preprocessor = TextPreprocessor()
cleaned = preprocessor.clean_text(raw_text)

# 使用实体提取器
extractor = EntityExtractor()
entities = extractor.extract_entities(text)

# 使用缓存
cache = SimpleCache(max_size=1000, ttl=3600)
cached_result = cache.get(text)
```

#### 1.3 注册引擎到工厂

使用`IntentEngineFactory`注册引擎：

```python
from core.intent.base_engine import IntentEngineFactory

# 注册引擎
IntentEngineFactory.register("my_engine", MyIntentEngine)

# 使用工厂创建
engine = IntentEngineFactory.create("my_engine", config={...})
```

---

### 2. 模型管理规范

#### 2.1 使用模型池

始终通过模型池管理模型，而不是直接加载：

```python
from core.intent.model_pool import get_model_pool

pool = get_model_pool()

# 获取模型（自动处理懒加载和卸载）
model, tokenizer = pool.get_model("bge-m3")

# 预加载模型
pool.preload_model("bge-m3")

# 卸载不再需要的模型
pool.unload_model("bert")
```

#### 2.2 配置模型TTL

根据使用频率配置合理的TTL：

```python
from core.intent.model_pool import ModelMetadata

# 高频模型：长TTL
frequent_model = ModelMetadata(
    name="bge-m3",
    model_type="bge-m3",
    model_path=path,
    ttl=7200  # 2小时
)

# 低频模型：短TTL
rare_model = ModelMetadata(
    name="bert",
    model_type="bert",
    model_path=path,
    ttl=1800  # 30分钟
)
```

#### 2.3 监控模型使用

定期检查模型池状态：

```python
stats = pool.get_stats()

print(f"已加载模型: {stats['loaded_models']}/{stats['total_models']}")
print(f"利用率: {stats['utilization']}")
```

---

### 3. 异常处理规范

#### 3.1 使用统一异常类

使用`core/intent/exceptions.py`中定义的异常类：

```python
from core.intent.exceptions import (
    ModelLoadError,
    ValidationError,
    InferenceError,
    ConfigurationError
)

def load_model(path: str):
    if not Path(path).exists():
        raise ModelLoadError(
            model_name=path,
            reason="模型文件不存在"
        )
```

#### 3.2 提供详细错误信息

异常消息应该包含足够的上下文信息：

```python
# ❌ 不好
raise ModelLoadError("加载失败")

# ✅ 好
raise ModelLoadError(
    model_name="bge-m3",
    reason="CUDA内存不足，需要至少4GB显存，当前可用2GB",
    details={"required_memory_mb": 4096, "available_memory_mb": 2048}
)
```

---

### 4. 测试规范

#### 4.1 测试覆盖

确保所有核心功能都有单元测试：

```python
# tests/unit/core/intent/test_my_engine.py

import pytest
from core.intent.my_engine import MyIntentEngine

class TestMyIntentEngine:
    def test_recognize_patent_search(self):
        engine = MyIntentEngine()
        result = engine.recognize_intent("检索专利")

        assert result.intent == IntentType.PATENT_SEARCH
        assert result.confidence > 0.5

    def test_invalid_input(self):
        engine = MyIntentEngine()

        with pytest.raises(ValidationError):
            engine.recognize_intent("")  # 空字符串
```

#### 4.2 使用测试标记

使用pytest标记分类测试：

```python
@pytest.mark.unit
def test_component():
    pass

@pytest.mark.integration
def test_workflow():
    pass

@pytest.mark.performance
def test_performance():
    pass
```

---

### 5. 日志规范

#### 5.1 使用结构化日志

```python
import logging

logger = logging.getLogger("intent.my_engine")

# 使用日志级别
logger.debug("调试信息")
logger.info("普通信息")
logger.warning("警告信息")
logger.error("错误信息")

# 包含上下文信息
logger.info(
    f"模型加载完成",
    extra={
        "model_name": "bge-m3",
        "load_time_ms": 1234.5,
        "device": "cuda:0"
    }
)
```

#### 5.2 避免敏感信息

不要在日志中记录敏感信息：

```python
# ❌ 不好
logger.info(f"用户登录: {username}, {password}")

# ✅ 好
logger.info(f"用户登录: {username}")
```

---

## 使用最佳实践

### 1. API调用规范

#### 1.1 使用批处理API

对于多个请求，使用批量接口以提高性能：

```python
# ❌ 不好：多次单个请求
for text in texts:
    result = recognize_intent(text)

# ✅ 好：单次批量请求
results = recognize_batch(texts)
```

#### 1.2 设置合理超时

为API请求设置超时：

```python
response = requests.post(
    url,
    json=data,
    timeout=(3.05, 27)  # 连接超时3.05s，读取超时27s
)
```

#### 1.3 实现重试机制

对于临时性错误，实现指数退避重试：

```python
from tenacity import retry, stop_after_attempt, wait_exponential

@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=1, max=10)
)
def call_intent_api(text):
    response = requests.post(url, json={"text": text})
    response.raise_for_status()
    return response.json()
```

---

### 2. 性能优化

#### 2.1 启用缓存

为重复请求启用缓存：

```python
from core.intent.utils import SimpleCache

cache = SimpleCache(max_size=1000, ttl=3600)

def get_intent_with_cache(text):
    cached = cache.get(text)
    if cached:
        return cached

    result = recognize_intent(text)
    cache.set(text, result)
    return result
```

#### 2.2 使用异步客户端

对于高并发场景，使用异步HTTP客户端：

```python
import aiohttp
import asyncio

async def async_recognize_intent(session, text):
    async with session.post(url, json={"text": text}) as response:
        return await response.json()

async def batch_recognize(texts):
    async with aiohttp.ClientSession() as session:
        tasks = [async_recognize_intent(session, text) for text in texts]
        return await asyncio.gather(*tasks)
```

#### 2.3 合理配置批处理

根据场景选择合适的批处理策略：

```python
from core.intent.batch_processor import (
    BatchConfig,
    BatchStrategy,
    DynamicBatchProcessor
)

# 低延迟场景
config = BatchConfig(
    strategy=BatchStrategy.LATENCY_OPTIMIZED,
    min_batch_size=1,
    max_batch_size=4,
    max_wait_time_ms=20
)

# 高吞吐量场景
config = BatchConfig(
    strategy=BatchStrategy.THROUGHPUT_OPTIMIZED,
    min_batch_size=8,
    max_batch_size=32,
    max_wait_time_ms=100
)
```

---

### 3. 监控和告警

#### 3.1 集成Prometheus监控

```python
from core.intent.prometheus_metrics import (
    get_metrics_manager,
    track_request
)

manager = get_metrics_manager()

# 记录请求指标
manager.record_request(
    engine_type="keyword",
    intent_type="PATENT_SEARCH",
    status="success",
    duration=0.045
)

# 或使用装饰器
@track_request(engine_type="keyword")
def my_recognize_function(text):
    # ...
    pass
```

#### 3.2 设置告警规则

在Prometheus中配置告警规则：

```yaml
groups:
  - name: intent_service_alerts
    rules:
      - alert: HighErrorRate
        expr: rate(intent_recognition_requests_total{status="error"}[5m]) > 0.05
        for: 5m
        annotations:
          summary: "意图识别服务错误率过高"

      - alert: HighLatency
        expr: histogram_quantile(0.95, rate(intent_recognition_latency_seconds_bucket[5m])) > 1.0
        for: 5m
        annotations:
          summary: "意图识别延迟过高"
```

---

## 性能优化指南

### 1. 内存优化

#### 1.1 模型卸载策略

根据业务模式选择合适的模型卸载策略：

```python
from core.intent.model_pool import ModelPool

# LRU：适合访问模式较均匀的场景
pool = ModelPool(unload_policy="lru")

# LFU：适合有明显热点的场景
pool = ModelPool(unload_policy="lfu")

# FIFO：适合顺序访问的场景
pool = ModelPool(unload_policy="fifo")
```

#### 1.2 控制并发模型数量

设置合理的最大模型数限制：

```python
pool = ModelPool(
    max_models=3,          # 最多同时加载3个模型
    max_memory_gb=12.0     # 最多使用12GB内存
)
```

---

### 2. 延迟优化

#### 2.1 模型预加载

在服务启动时预加载常用模型：

```python
from core.intent.model_pool import get_model_pool

pool = get_model_pool()

# 预加载高频模型
pool.preload_model("bge-m3")
pool.preload_model("bert")
```

#### 2.2 批处理优化

调整批处理参数以平衡延迟和吞吐量：

```python
config = BatchConfig(
    min_batch_size=1,           # 最小批大小
    max_batch_size=8,           # 最大批大小
    initial_batch_size=4,       # 初始批大小
    max_wait_time_ms=30,        # 最大等待时间
    max_latency_ms=100          # 最大延迟目标
)
```

---

### 3. 吞吐量优化

#### 3.1 GPU利用率优化

- 将多个小批次合并为大批次
- 使用GPU并行处理
- 启用CUDA图优化

#### 3.2 CPU并行处理

对于CPU推理，使用多进程并行：

```python
from multiprocessing import Pool

def process_text(text):
    return recognize_intent(text)

with Pool(processes=4) as pool:
    results = pool.map(process_text, texts)
```

---

## 故障排查指南

### 1. 常见问题

#### 1.1 模型加载失败

**症状**: `ModelLoadError: 模型加载失败`

**排查步骤**:
1. 检查模型路径是否正确
2. 验证模型文件完整性
3. 检查设备是否可用（CUDA/GPU）
4. 查看内存是否充足

**解决方案**:
```python
# 检查模型路径
from pathlib import Path
model_path = Path("/path/to/model")
assert model_path.exists(), "模型路径不存在"

# 检查GPU可用性
import torch
assert torch.cuda.is_available(), "CUDA不可用"

# 检查内存
import psutil
available_memory_gb = psutil.virtual_memory().available / (1024**3)
assert available_memory_gb > 4, "内存不足"
```

#### 1.2 意图识别错误率高

**症状**: 识别结果不符合预期

**排查步骤**:
1. 检查输入文本格式
2. 验证引擎类型选择
3. 查看置信度分数
4. 分析失败案例

**解决方案**:
```python
# 检查输入
assert len(text.strip()) > 0, "输入文本为空"
assert len(text) <= 10000, "输入文本过长"

# 尝试不同引擎
for engine_type in ["keyword", "semantic"]:
    result = recognize_intent(text, engine=engine_type)
    if result.confidence > 0.8:
        break
```

#### 1.3 性能下降

**症状**: 响应时间明显变慢

**排查步骤**:
1. 查看系统资源使用率
2. 检查模型池状态
3. 分析批处理统计
4. 查看缓存命中率

**解决方案**:
```python
# 检查资源使用
import psutil
cpu_percent = psutil.cpu_percent()
memory_percent = psutil.virtual_memory().percent

# 检查模型池
stats = pool.get_stats()
if stats["loaded_models"] > stats["max_models"]:
    # 卸载不常用模型
    pass

# 检查缓存
cache_stats = cache.get_stats()
if cache_stats["hit_rate"] < 0.5:
    # 调整缓存策略
    pass
```

---

### 2. 调试技巧

#### 2.1 启用详细日志

```python
import logging

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
```

#### 2.2 使用性能分析器

```python
import cProfile
import pstats

profiler = cProfile.Profile()
profiler.enable()

# 执行代码
result = recognize_intent(text)

profiler.disable()
stats = pstats.Stats(profiler)
stats.sort_stats('cumulative')
stats.print_stats(20)
```

#### 2.3 监控GPU使用

```bash
# 实时监控GPU使用
watch -n 1 nvidia-smi

# 记录GPU使用历史
nvidia-smi --query-gpu=timestamp,utilization.gpu,memory.used --format=csv -l 1 > gpu.log
```

---

## 部署建议

### 1. 容器化部署

#### 1.1 Docker镜像构建

```dockerfile
FROM python:3.14-slim

WORKDIR /app

# 安装依赖
COPY pyproject.toml ./
RUN pip install poetry && poetry install --only main

# 复制代码
COPY core/ core/
COPY config/ config/

# 暴露端口
EXPOSE 8000

# 启动服务
CMD ["uvicorn", "core.api.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

#### 1.2 Docker Compose配置

```yaml
version: '3.8'

services:
  intent-service:
    build: .
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql://db:5432/intent
      - REDIS_URL=redis://redis:6379
      - LOG_LEVEL=INFO
    depends_on:
      - db
      - redis
    volumes:
      - ./data/models:/app/data/models
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              count: 1
              capabilities: [gpu]
```

---

### 2. 负载均衡

#### 2.1 Nginx配置

```nginx
upstream intent_service {
    least_conn;
    server intent1:8000 weight=3;
    server intent2:8000 weight=2;
    server intent3:8000 weight=1;
}

server {
    listen 80;
    server_name intent.example.com;

    location /api/v1/intent {
        proxy_pass http://intent_service;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }
}
```

---

### 3. 监控部署

#### 3.1 Prometheus配置

```yaml
scrape_configs:
  - job_name: 'intent-service'
    static_configs:
      - targets: ['intent1:8000', 'intent2:8000', 'intent3:8000']
    metrics_path: '/api/v1/intent/metrics'
    scrape_interval: 15s
```

#### 3.2 Grafana仪表板

导入`config/monitoring/grafana-intent-dashboard.json`到Grafana。

---

## 附录

### A. 配置参考

完整的配置示例见`config/intent_config.yaml`。

### B. API参考

完整的API文档见`docs/api/intent-service-api.md`。

### C. 性能基准

性能基准测试报告见`docs/performance/intent-benchmark-report.md`。
