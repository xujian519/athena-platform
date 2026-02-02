# 学习与适应模块 (Learning & Adaptation Module)

## 概述

学习与适应模块是Athena AI系统的核心组件，负责实现机器学习、经验积累、模式识别和自适应优化功能。

## 版本信息

- **版本**: v2.0.0
- **最后更新**: 2026-01-27
- **作者**: Athena AI系统

## 模块架构

```
core/learning/
├── learning_engine/          # 核心学习引擎
│   ├── engine.py            # 主引擎实现
│   ├── adaptive_optimizer.py # 自适应优化器
│   ├── experience_store.py  # 经验存储器
│   ├── pattern_recognizer.py # 模式识别器
│   └── knowledge_updater.py  # 知识图谱更新器
├── rapid_learning/          # 快速学习模块
│   ├── engine.py            # 快速学习引擎
│   ├── learners.py          # 学习器组件
│   ├── replay_buffer.py     # 优先重放缓冲区
│   └── types.py             # 类型定义
├── xiaona_adaptive_learning_system.py  # 小娜自适应学习系统
├── failure_learning.py      # 失败学习系统
├── learning_config.py       # 配置管理
└── exceptions.py            # 自定义异常
```

## 核心功能

### 1. 学习引擎 (LearningEngine)

完整的学习引擎实现，支持：

- **经验积累**: 从执行过程中积累经验数据
- **模式识别**: 使用TF-IDF和K-Means识别数据模式
- **自适应优化**: 根据性能自动调整参数
- **知识更新**: 将学习到的知识更新到知识图谱

**使用示例**:
```python
from core.learning import LearningEngine

# 创建学习引擎
engine = LearningEngine(agent_id="agent_001")

# 初始化
await engine.initialize(knowledge_manager)

# 学习
result = await engine.learn({
    "type": "knowledge_acquisition",
    "context": {"task": "patent_search"},
    "content": {"data": "..."},
    "outcome": {"success": True},
    "performance": 0.9
})

# 获取学习摘要
summary = await engine.get_learning_summary()

# 关闭
await engine.shutdown()
```

### 2. 快速学习引擎 (RapidLearningEngine)

支持在线学习和快速适应：

- **在线学习**: 支持增量学习和持续学习
- **模型管理**: 支持多种模型类型（神经网络、线性回归、随机森林）
- **优先重放**: 使用优先级缓冲区优化学习效率
- **环境适应**: 支持梯度下降、进化算法、迁移学习等适应策略

**使用示例**:
```python
from core.learning.rapid_learning import RapidLearningEngine, LearningTask, LearningType

# 创建快速学习引擎
engine = RapidLearningEngine(config={
    "learning_rate": 0.01,
    "batch_size": 32,
    "enable_meta_learning": True
})

# 创建学习任务
task = LearningTask(
    task_id="task_001",
    task_type=LearningType.SUPERVISED,
    learning_mode=LearningMode.ONLINE,
    data_source="training_data.csv",
    model_type="neural_network",
    hyperparameters={"epochs": 100},
    performance_metric="accuracy",
    target_performance=0.9
)

# 从经验中学习
from core.learning.rapid_learning.types import LearningExperience

experience = LearningExperience(
    experience_id="exp_001",
    task_type="classification",
    input_data=[1.0, 2.0, 3.0],
    output_data=1,
    context={},
    reward=0.9,
    timestamp=datetime.now(),
    importance=1.0
)

await engine.learn_from_experience(experience)
```

### 3. 小娜自适应学习系统 (XiaonaAdaptiveLearningSystem)

专为专利法律专家设计的自适应学习系统：

- **反思学习**: 从反思结果中学习
- **人工反馈学习**: 从人工反馈中学习
- **知识管理**: 管理法律知识和经验模式
- **性能追踪**: 追踪学习进度和性能趋势

**使用示例**:
```python
from core.learning import XiaonaAdaptiveLearningSystem

# 创建学习系统
learning_system = XiaonaAdaptiveLearningSystem()

# 处理反思结果
await learning_system.process_reflection_result(reflection_result)

# 处理人工反馈
await learning_system.process_human_feedback(
    session=collaboration_session,
    human_feedback="分析很好，但需要补充更多法律依据",
    feedback_quality="constructive"
)

# 获取学习总结
summary = learning_system.get_learning_summary()
```

### 4. 失败学习系统 (FailureLearning)

从失败中学习，持续改进：

- **失败分析**: 分析失败原因和模式
- **知识库**: 存储失败案例和解决方案
- **相似案例查找**: 查找历史相似失败
- **统计分析**: 失败类型统计和趋势

**使用示例**:
```python
from core.memory.failure_learning import FailureKnowledgeBase

# 创建知识库
kb = FailureKnowledgeBase(storage_path="data/failure_knowledge")

# 记录失败
case = kb.record_failure(
    task_description="搜索专利",
    error_message="工具未找到: patent_search",
    stack_trace="...",
    context={"task_type": "search", "user_id": "user_001"}
)

# 获取相似失败
similar = kb.get_similar_failures(
    task_description="搜索专利",
    task_type="search",
    limit=5
)

# 获取经验教训
lessons = kb.get_lessons_learned()
```

## 配置管理

配置通过 `learning_config.py` 集中管理：

```python
from core.learning.learning_config import LearningConfig

# 获取配置
config = LearningConfig()

# 访问配置
threshold = config.performance.PERFORMANCE_DECLINE_THRESHOLD  # -0.1
batch_size = config.batch.MODEL_UPDATE_BATCH_SIZE  # 100
cache_size = config.cache.MAX_EXPERIENCES  # 10000

# 更新配置
LearningConfig.update({
    "performance": {
        "PERFORMANCE_DECLINE_THRESHOLD": -0.15
    }
})
```

## 异常处理

模块使用自定义异常类：

```python
from core.learning.exceptions import (
    LearningEngineError,
    ModelValidationError,
    PatternRecognitionError
)

try:
    await engine.learn(data)
except LearningEngineError as e:
    print(f"学习引擎错误: {e.message}")
    print(f"错误代码: {e.error_code}")
except ModelValidationError as e:
    print(f"模型验证失败: {e}")
```

## 测试

运行单元测试：

```bash
# 运行所有学习模块测试
pytest tests/unit/core/learning/ -v

# 运行特定测试
pytest tests/unit/core/learning/learning_engine/test_experience_store.py -v

# 运行集成测试
pytest tests/integration/learning/test_learning_api.py -v
```

## 安全注意事项

1. **模型序列化**: 模型检查点使用pickle格式，仅加载可信来源的模型
2. **数据验证**: 所有外部数据都经过验证
3. **错误处理**: 使用自定义异常类进行错误处理
4. **资源限制**: 经验缓冲区和模型数量有限制

## 性能优化

1. **异步操作**: 所有I/O操作使用async/await
2. **缓存机制**: 模式和经验使用缓存
3. **批量处理**: 支持批量学习和更新
4. **资源限制**: deque限制内存使用

## 依赖项

- **必需**: Python 3.10+
- **可选**:
  - torch (PyTorch, 用于神经网络)
  - scikit-learn (用于机器学习算法)
  - numpy (数值计算)

## 贡献指南

1. 遵循PEP 8代码规范
2. 添加类型注解
3. 编写单元测试
4. 更新文档
5. 使用自定义异常类

## 许可证

版权所有 © 2025-2026 Athena AI系统
