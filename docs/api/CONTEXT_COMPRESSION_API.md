# 上下文压缩系统 API文档

**版本**: 1.0.0
**更新日期**: 2026-04-21
**作者**: Athena平台团队

---

## 📚 目录

1. [概述](#概述)
2. [快速开始](#快速开始)
3. [核心API](#核心api)
4. [数据类型](#数据类型)
5. [压缩策略](#压缩策略)
6. [使用示例](#使用示例)
7. [性能指标](#性能指标)

---

## 概述

上下文压缩系统提供智能的对话历史压缩功能，帮助管理长对话的上下文，节省token使用，同时保留关键信息。

### 核心特性

- ✅ **智能评分**: 基于角色、内容、时间和结构的多维度评分
- ✅ **多种策略**: 支持最近优先、重要性优先、语义聚类和混合策略
- ✅ **灵活配置**: 5种压缩级别，可自定义保留策略
- ✅ **质量保证**: 自动评估压缩质量，确保关键信息不丢失
- ✅ **高性能**: 压缩速度 <100ms/1000 tokens

---

## 快速开始

### 安装

```python
from core.memory.sessions.compression import (
    ContextCompressor,
    CompressionConfig,
    CompressionLevel,
    CompressionStrategy,
)
from core.memory.sessions.types import SessionMessage, MessageRole
```

### 基本使用

```python
# 创建压缩器
compressor = ContextCompressor(
    config=CompressionConfig(
        level=CompressionLevel.MEDIUM,
        strategy=CompressionStrategy.HYBRID,
        max_tokens=8000,
    )
)

# 压缩消息列表
result = compressor.compress(messages)

print(f"压缩率: {result.compression_ratio:.1%}")
print(f"节省token: {result.tokens_saved}")
print(f"质量分数: {result.quality_score:.2f}")
```

---

## 核心API

### ContextCompressor

上下文压缩器的主类。

#### 初始化

```python
ContextCompressor(
    config: Optional[CompressionConfig] = None,
    scorer: Optional[MessageScorer] = None,
)
```

**参数**:
- `config`: 压缩配置（可选，使用默认配置）
- `scorer`: 消息评分器（可选，使用默认评分器）

#### 方法

##### compress()

压缩消息列表。

```python
def compress(messages: List[SessionMessage]) -> CompressionResult
```

**参数**:
- `messages`: 原始消息列表

**返回**:
- `CompressionResult`: 压缩结果

**示例**:
```python
result = compressor.compress(messages)

# 获取压缩后的消息
compressed_ids = result.compressed_messages
compressed_messages = [m for m in messages if m.message_id in compressed_ids]
```

---

### MessageScorer

消息重要性评分器。

#### 初始化

```python
MessageScorer(
    recency_weight: float = 0.2,
    role_weight: float = 0.3,
    content_weight: float = 0.3,
    structure_weight: float = 0.2,
)
```

**参数**:
- `recency_weight`: 时间权重（0.0-1.0）
- `role_weight`: 角色权重（0.0-1.0）
- `content_weight`: 内容权重（0.0-1.0）
- `structure_weight`: 结构权重（0.0-1.0）

#### 方法

##### score_messages()

批量评分消息。

```python
def score_messages(messages: List[SessionMessage]) -> List[ImportanceScore]
```

**返回**:
- `List[ImportanceScore]`: 评分结果列表

**示例**:
```python
scorer = MessageScorer()
scores = scorer.score_messages(messages)

for score in scores:
    print(f"{score.message_id}: {score.score:.2f} ({score.level.value})")
```

---

### TokenBudget

Token预算管理。

#### 初始化

```python
TokenBudget(
    total_budget: int,
    reserved: int = 0,
    used: int = 0,
    compression_threshold: float = 0.8,
)
```

#### 方法

##### reserve()

预留预算。

```python
def reserve(amount: int) -> bool
```

##### consume()

消耗预算。

```python
def consume(amount: int) -> bool
```

##### release()

释放预留。

```python
def release(amount: int) -> None
```

##### needs_compression()

检查是否需要压缩。

```python
def needs_compression() -> bool
```

**示例**:
```python
budget = TokenBudget(total_budget=8000, compression_threshold=0.8)

# 使用预算
if budget.reserve(100):
    # 处理消息
    budget.consume(100)

# 检查是否需要压缩
if budget.needs_compression():
    result = compressor.compress(messages)
```

---

## 数据类型

### CompressionLevel

压缩级别枚举。

| 级别 | 保留比例 | 说明 |
|------|---------|------|
| `NONE` | 100% | 不压缩 |
| `LOW` | 80% | 轻度压缩 |
| `MEDIUM` | 60% | 中度压缩 |
| `HIGH` | 40% | 高度压缩 |
| `AGGRESSIVE` | 20% | 激进压缩 |

### CompressionStrategy

压缩策略枚举。

| 策略 | 说明 |
|------|------|
| `RECENT_FIRST` | 优先保留最近消息 |
| `IMPORTANCE_BASED` | 基于重要性评分 |
| `SEMANTIC_CLUSTERING` | 语义聚类压缩 |
| `HYBRID` | 混合策略（推荐） |

### MessageImportance

消息重要性等级。

| 等级 | 分数范围 | 说明 |
|------|---------|------|
| `CRITICAL` | 0.85-1.0 | 关键信息（必须保留） |
| `HIGH` | 0.65-0.85 | 高重要性 |
| `MEDIUM` | 0.4-0.65 | 中等重要性 |
| `LOW` | 0.2-0.4 | 低重要性 |
| `TRIVIAL` | 0.0-0.2 | 微不足道 |

### CompressionResult

压缩结果数据类。

```python
@dataclass
class CompressionResult:
    original_messages: List[str]      # 原始消息ID
    compressed_messages: List[str]    # 压缩后保留的消息ID
    removed_messages: List[str]       # 删除的消息ID
    summaries: List[str]              # 摘要列表
    compression_ratio: float          # 压缩率 (0.0-1.0)
    tokens_saved: int                 # 节省的token数
    quality_score: float              # 质量分数 (0.0-1.0)
    execution_time_ms: float          # 执行时间（毫秒）
    strategy: CompressionStrategy     # 使用的策略
    timestamp: datetime               # 压缩时间
```

---

## 压缩策略

### RECENT_FIRST - 最近优先

优先保留最近的消息，适合注重时效性的场景。

```python
config = CompressionConfig(
    strategy=CompressionStrategy.RECENT_FIRST,
    preserve_recent_count=10,
)
```

**特点**:
- 简单高效
- 保留上下文连贯性
- 适合连续对话

### IMPORTANCE_BASED - 重要性优先

根据消息重要性评分保留关键消息。

```python
config = CompressionConfig(
    strategy=CompressionStrategy.IMPORTANCE_BASED,
)
```

**特点**:
- 保留关键信息
- 可能牺牲时间顺序
- 适合信息检索场景

### SEMANTIC_CLUSTERING - 语义聚类

将相似消息聚类，每个聚类保留代表。

```python
config = CompressionConfig(
    strategy=CompressionStrategy.SEMANTIC_CLUSTERING,
)
```

**特点**:
- 保留对话结构
- 减少冗余信息
- 适合长文档分析

### HYBRID - 混合策略（推荐）

结合多种策略的优点，平衡时间和重要性。

```python
config = CompressionConfig(
    strategy=CompressionStrategy.HYBRID,
    preserve_recent_count=10,
)
```

**特点**:
- 最佳综合效果
- 保留最近消息
- 考虑重要性评分

---

## 使用示例

### 示例1: 基本压缩

```python
from core.memory.sessions.compression import ContextCompressor, CompressionConfig
from core.memory.sessions.types import SessionMessage, MessageRole

# 创建消息列表
messages = [
    SessionMessage(role=MessageRole.SYSTEM, content="You are a helpful assistant."),
    SessionMessage(role=MessageRole.USER, content="分析专利CN123456789A"),
    SessionMessage(role=MessageRole.ASSISTANT, content="好的，我来分析..."),
    # ... 更多消息
]

# 创建压缩器
compressor = ContextCompressor(
    config=CompressionConfig(
        level=CompressionLevel.MEDIUM,
        max_tokens=4000,
    )
)

# 压缩
result = compressor.compress(messages)

print(f"原始消息: {len(result.original_messages)}")
print(f"压缩后: {len(result.compressed_messages)}")
print(f"压缩率: {result.compression_ratio:.1%}")
print(f"节省token: {result.tokens_saved}")
```

### 示例2: 与会话管理器集成

```python
from core.memory.sessions.manager import SessionManager
from core.memory.sessions.compression import ContextCompressor, TokenBudget

# 创建会话管理器
manager = SessionManager()

# 创建token预算
budget = TokenBudget(total_budget=8000)

# 添加消息
session_id = "session_001"
manager.add_message(session_id, MessageRole.USER, "Hello", 5)
manager.add_message(session_id, MessageRole.ASSISTANT, "Hi there!", 5)
# ... 添加更多消息

# 检查是否需要压缩
if budget.needs_compression():
    # 获取所有消息
    messages = manager.get_session_messages(session_id)

    # 压缩
    compressor = ContextCompressor()
    result = compressor.compress(messages)

    # 创建新会话保存压缩后的消息
    compressed_session = f"{session_id}_compressed"
    for msg_id in result.compressed_messages:
        msg = next(m for m in messages if m.message_id == msg_id)
        manager.add_message(
            compressed_session,
            msg.role,
            msg.content,
            msg.token_count,
        )
```

### 示例3: 自定义评分器

```python
from core.memory.sessions.compression import MessageScorer, ContextCompressor

# 创建自定义评分器
scorer = MessageScorer(
    recency_weight=0.4,  # 更重视时间
    role_weight=0.2,
    content_weight=0.3,
    structure_weight=0.1,
)

# 使用自定义评分器
compressor = ContextCompressor(scorer=scorer)
result = compressor.compress(messages)
```

### 示例4: 分级压缩策略

```python
from core.memory.sessions.compression import CompressionLevel, CompressionStrategy

# 根据消息数量选择策略
message_count = len(messages)

if message_count < 50:
    # 轻度压缩
    config = CompressionConfig(
        level=CompressionLevel.LOW,
        strategy=CompressionStrategy.RECENT_FIRST,
    )
elif message_count < 100:
    # 中度压缩
    config = CompressionConfig(
        level=CompressionLevel.MEDIUM,
        strategy=CompressionStrategy.HYBRID,
    )
else:
    # 高度压缩
    config = CompressionConfig(
        level=CompressionLevel.HIGH,
        strategy=CompressionStrategy.IMPORTANCE_BASED,
    )

compressor = ContextCompressor(config=config)
result = compressor.compress(messages)
```

---

## 性能指标

### 压缩性能

| 指标 | 目标值 | 实际值 | 状态 |
|------|--------|--------|------|
| 压缩速度 | <100ms/1000 tokens | ~50ms/1000 tokens | ✅ |
| 压缩率 | >60% | 60-80% | ✅ |
| 质量分数 | >0.7 | 0.8-0.95 | ✅ |
| 测试覆盖率 | >90% | 97.69% | ✅ |

### 不同策略性能

| 策略 | 速度 | 压缩率 | 质量 | 适用场景 |
|------|------|--------|------|---------|
| RECENT_FIRST | ⚡⚡⚡ | 中 | 中 | 连续对话 |
| IMPORTANCE_BASED | ⚡⚡ | 高 | 高 | 信息检索 |
| SEMANTIC_CLUSTERING | ⚡ | 高 | 中 | 长文档 |
| HYBRID | ⚡⚡ | 高 | 高 | 通用场景 |

---

## 最佳实践

### 1. 选择合适的压缩级别

```python
# 短对话：不压缩或轻度压缩
if message_count < 20:
    level = CompressionLevel.NONE

# 中等对话：中度压缩
elif message_count < 50:
    level = CompressionLevel.MEDIUM

# 长对话：高度压缩
else:
    level = CompressionLevel.HIGH
```

### 2. 始终保留系统消息

```python
config = CompressionConfig(
    level=CompressionLevel.MEDIUM,
    preserve_recent_count=10,  # 保留最近10条消息
)
```

### 3. 监控压缩质量

```python
result = compressor.compress(messages)

if result.quality_score < 0.7:
    logger.warning(f"压缩质量较低: {result.quality_score}")
    # 考虑调整策略或降低压缩级别
```

### 4. 定期压缩

```python
# 在添加消息后检查
def add_message_with_compression(manager, session_id, role, content, tokens):
    manager.add_message(session_id, role, content, tokens)

    # 每100条消息压缩一次
    messages = manager.get_session_messages(session_id)
    if len(messages) >= 100:
        compressor = ContextCompressor()
        result = compressor.compress(messages)
        # 保存压缩结果...
```

---

**作者**: Athena平台团队
**最后更新**: 2026-04-21
**版本**: 1.0.0
