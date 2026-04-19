# CORE SYSTEM

## OVERVIEW
四层记忆架构和AI认知引擎的核心组件集合，为Athena平台提供智能数据处理和存储能力。

## STRUCTURE
```
core/
├── 🧠 memory/           # 四层记忆架构 (HOT/WARM/COLD/ARCHIVE)
├── 🤔 cognition/        # 认知处理核心 (CognitionEngine)
├── 🔍 embedding/        # 向量嵌入服务 (EmbeddingService)
├── 📊 perception/       # 感知系统 (数据处理管道)
├── ⚡ cache/           # 缓存系统 (多级缓存策略)
├── 🧠 nlp/             # 自然语言处理模块
└── 📄 patent/          # 专利数据处理 (PatentProcessor)
```

## WHERE TO LOOK
| 任务 | 位置 | 关键组件 |
|------|--------|-------|
| 记忆存储 | core/memory/ | MemorySystem, 四层架构 |
| 认知推理 | core/cognition/ | CognitionEngine, 推理逻辑 |
| 向量计算 | core/embedding/ | EmbeddingService, 向量操作 |
| 专利处理 | core/patent/ | PatentProcessor, 数据分析 |
| 缓存策略 | core/cache/ | 多级缓存, TTL管理 |
| NLP处理 | core/nlp/ | 文本解析, 语义分析 |

## CONVENTIONS
### 核心架构规范
- **模块独立性**: 每个子模块都有明确的 __init__.py 边界，避免循环依赖
- **接口优先**: 所有核心服务必须定义抽象接口，支持多种实现
- **异常处理**: 使用统一的异常体系，core.exceptions.BaseException 作为基类
- **配置驱动**: 所有核心模块通过 configs/core/ 统一配置，禁止硬编码

### 命名约定
- **服务类**: 以 Service 结尾 (MemoryService, CognitionService)
- **引擎类**: 以 Engine 结尾 (CognitionEngine, EmbeddingEngine)
- **处理器**: 以 Processor 结尾 (PatentProcessor, TextProcessor)
- **存储类**: 以 Store 结尾 (MemoryStore, VectorStore)

## ANTI-PATTERNS
### 架构反模式
- **直接调用**: 禁止跨模块直接调用内部实现，必须通过接口
- **状态共享**: 避免在模块间共享可变状态，使用消息传递
- **阻塞操作**: 核心服务中禁止长时间阻塞操作，必须异步化
- **循环依赖**: 严格禁止模块间的循环导入依赖

### 代码反模式
- **全局变量**: 禁止使用模块级全局变量存储状态
- **硬编码配置**: 所有配置参数必须通过配置文件或环境变量
- **异常吞噬**: 禁止静默忽略异常，必须记录和适当处理
- **内存泄漏**: 向量操作和大对象处理必须显式释放资源

---
*Core System - 2026-02-20*