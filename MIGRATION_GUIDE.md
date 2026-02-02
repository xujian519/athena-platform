# 重构模块迁移指南

## 📚 新导入方式完整参考

### 1. 记忆系统 (Memory System)

```python
# ✅ 推荐的新导入方式
from core.memory.unified_memory import (
    UnifiedAgentMemorySystem,
    MemoryType,
    AgentType,
    MemoryTier,
    AgentIdentity,
    MemoryItem,
    CacheStatistics,
    AGENT_REGISTRY,
)

# 📋 可用的MemoryType枚举
MemoryType.CONVERSATION     # 对话记忆
MemoryType.EMOTIONAL        # 情感记忆
MemoryType.KNOWLEDGE        # 知识记忆
MemoryType.FAMILY           # 家庭记忆
MemoryType.PROFESSIONAL     # 专业记忆
MemoryType.LEARNING         # 学习记忆
MemoryType.REFLECTION       # 反思记忆
MemoryType.CONTEXT          # 上下文记忆
MemoryType.PREFERENCE       # 偏好记忆
MemoryType.EXPERIENCE       # 经验记忆
MemoryType.SCHEDULE         # 日程记忆

# 🤖 可用的AgentType枚举
AgentType.ATHENA     # 智慧女神
AgentType.XIAONA     # 小娜·天秤女神
AgentType.YUNXI      # 云熙.vega
AgentType.XIAOCHEN   # 小宸·星河射手
AgentType.XIAONUO    # 小诺·双鱼座

# 💾 可用的MemoryTier枚举
MemoryTier.HOT       # 热层 - 快速访问，内存中
MemoryTier.WARM      # 温层 - Redis缓存
MemoryTier.COLD      # 冷层 - 持久化存储
MemoryTier.ETERNAL   # 永恒层 - 永不遗忘
```

### 2. 协作协议 (Collaboration Protocols)

```python
# ✅ 推荐的新导入方式
from core.protocols.collaboration import (
    # 基础类
    BaseProtocol,
    # 具体协议实现
    CommunicationProtocol,    # 通信协议
    CoordinationProtocol,     # 协调协议
    DecisionProtocol,         # 决策协议
    # 数据模型
    ProtocolType,
    ProtocolPhase,
    ProtocolStatus,
    ProtocolMessage,
    ProtocolContext,
    # 管理器和工具
    ProtocolManager,
    protocol_manager,
    create_protocol_session,
    start_protocol_session,
    get_protocol_session_status,
    shutdown_protocol_manager,
)

# 📋 使用示例
from core.protocols.collaboration import CommunicationProtocol, ProtocolManager

# 创建通信协议
protocol = CommunicationProtocol("comm_001")
protocol.add_participant("agent1")
protocol.add_participant("agent2")
await protocol.start()

# 或使用管理器
manager = ProtocolManager()
protocol_id = manager.create_communication_protocol(
    participants=["agent1", "agent2"]
)
await manager.start_protocol(protocol_id)
```

### 3. 专业Agent (Specialized Agents)

```python
# ✅ 推荐的新导入方式
from core.agent_collaboration.specialized_agents import (
    SearchAgent,      # 搜索Agent - 专利检索专家
    AnalysisAgent,    # 分析Agent - 专利技术分析专家
    CreativeAgent,    # 创意Agent - 创新思维专家
)

# 📋 使用示例
from core.agent_collaboration.specialized_agents import SearchAgent, AnalysisAgent

# 创建搜索Agent
search_agent = SearchAgent(
    agent_id="search_agent_001",
    config={"max_concurrent_searches": 5}
)

# 执行专利搜索
results = await search_agent.enhanced_patent_search(
    query="人工智能在医疗领域的应用",
    databases=["google_patents", "cnipa"],
    max_results=10
)

# 创建分析Agent
analysis_agent = AnalysisAgent(
    agent_id="analysis_agent_001",
    config={"analysis_depth": "deep"}
)

# 分析专利
analysis = await analysis_agent.analyze_patent(
    patent_number="CN202310000000"
)
```

### 4. 网络搜索 (Web Search)

```python
# ✅ 推荐的新导入方式
from core.search.external.web_search import (
    # 核心类
    UnifiedWebSearchManager,
    # 数据类型
    SearchEngineType,
    SearchQuery,
    SearchResult,
    SearchResponse,
)

# 📋 可用的搜索引擎
SearchEngineType.TAVILY               # Tavily搜索
SearchEngineType.GOOGLE_CUSTOM_SEARCH # Google Custom Search
SearchEngineType.BING_SEARCH          # Bing搜索
SearchEngineType.DUCKDUCKGO           # DuckDuckGo搜索
SearchEngineType.BRAVE                # Brave搜索
SearchEngineType.PERPLEXITY           # Perplexity搜索
SearchEngineType.BOCHA                # 博查搜索
SearchEngineType.METASO               # 秘塔搜索
SearchEngineType.DEEPSEARCH           # DeepSearch深度搜索

# 📋 使用示例
from core.search.external.web_search import (
    UnifiedWebSearchManager,
    SearchEngineType,
)

# 创建搜索管理器
manager = UnifiedWebSearchManager()

# 执行搜索
response = await manager.search(
    query="Python异步编程最佳实践",
    engines=[SearchEngineType.TAVILY],
    max_results=10,
    language="zh-CN"
)

# 查看结果
if response.success:
    for result in response.results:
        print(f"标题: {result.title}")
        print(f"URL: {result.url}")
        print(f"摘要: {result.snippet}")
        print(f"相关度: {result.relevance_score}")
```

### 5. Agent协调器 (Agent Coordinator)

```python
# ✅ 推荐的新导入方式
from core.agent_collaboration.agent_coordinator import (
    AgentCoordinator,
    get_agent_coordinator,
    TaskStatus,
    WorkflowType,
    TaskDefinition,
)

# 📋 可用的TaskStatus枚举
TaskStatus.PENDING       # 待处理
TaskStatus.ASSIGNED      # 已分配
TaskStatus.IN_PROGRESS   # 进行中
TaskStatus.COMPLETED     # 已完成
TaskStatus.FAILED        # 失败
TaskStatus.CANCELLED     # 已取消

# 📋 可用的WorkflowType枚举
WorkflowType.SEQUENTIAL     # 串行执行
WorkflowType.PARALLEL       # 并行执行
WorkflowType.PIPELINE       # 流水线执行
WorkflowType.COLLABORATIVE  # 协作执行

# 📋 使用示例
from core.agent_collaboration.agent_coordinator import get_agent_coordinator

# 获取协调器单例
coordinator = get_agent_coordinator()
await coordinator.initialize()

# 协调工作流
result = await coordinator._coordinate_workflow({
    "workflow_type": "parallel",
    "tasks": [
        {"type": "patent_search", "content": {"query": "AI"}},
        {"type": "patent_analysis", "content": {"patent_id": "123"}},
    ],
    "user_request": "分析AI专利"
})
```

### 6. 自适应元规划器 (Adaptive Meta Planner)

```python
# ✅ 推荐的新导入方式
from core.planning.adaptive_meta_planner import (
    AdaptiveMetaPlanner,
    get_adaptive_meta_planner,
    plan_adaptive,
    WorkflowReuseManager,
    PerformanceTracker,
)

# 📋 使用示例
from core.planning.adaptive_meta_planner import plan_adaptive
from core.planning.models import Task

# 使用便捷函数规划任务
task = Task(description="分析专利的新颖性")
plan = await plan_adaptive(task)

# 或使用完整API
from core.planning.adaptive_meta_planner import get_adaptive_meta_planner

planner = get_adaptive_meta_planner()
plan = await planner.plan(task)
```

### 7. 协作模式 (Collaboration Patterns)

```python
# ✅ 推荐的新导入方式
from core.collaboration.collaboration_patterns import (
    # 基础类
    CollaborationPattern,
    # 具体模式实现
    SequentialCollaborationPattern,    # 串行协作模式
    ParallelCollaborationPattern,      # 并行协作模式
    HierarchicalCollaborationPattern,  # 层次协作模式
    ConsensusCollaborationPattern,     # 共识协作模式
    # 工厂类
    CollaborationPatternFactory,
)

# 📋 使用示例
from core.collaboration.collaboration_patterns import CollaborationPatternFactory

# 创建协作模式工厂
factory = CollaborationPatternFactory()

# 查看可用模式
available_patterns = factory.get_available_patterns()
print(f"可用模式: {available_patterns}")  # ['sequential', 'parallel', 'hierarchical', 'consensus']

# 创建具体模式实例
from core.collaboration.multi_agent_collaboration import MultiAgentCollaborationFramework

framework = MultiAgentCollaborationFramework()
pattern = factory.create_pattern("sequential", framework)

# 使用模式启动协作
task = Task(title="专利分析任务", description="分析专利的新颖性")
participants = ["agent_001", "agent_002", "agent_003"]
session_id = await pattern.initiate_collaboration(task, participants, context={})
```

### 8. 评估引擎 (Evaluation Engine)

```python
# ✅ 推荐的新导入方式
from core.evaluation.evaluation_engine import (
    # 类型定义
    EvaluationCriteria,
    EvaluationResult,
    EvaluationLevel,
    EvaluationType,
    ReflectionRecord,
    ReflectionType,
    # 核心类
    EvaluationEngine,
    MetricsCalculator,
    QualityAssuranceChecker,
    ReflectionEngine,
)

# 📋 使用示例
from core.evaluation.evaluation_engine import EvaluationEngine, EvaluationCriteria

# 创建评估引擎
engine = EvaluationEngine(agent_id="evaluator_001")
await engine.initialize()

# 创建评估标准
criteria = [
    EvaluationCriteria(
        id="quality",
        name="质量评估",
        description="评估输出质量",
        current_value=85.0,
        min_value=0.0,
        max_value=100.0,
        weight=1.0,
    ),
    EvaluationCriteria(
        id="efficiency",
        name="效率评估",
        description="评估执行效率",
        current_value=75.0,
        min_value=0.0,
        max_value=100.0,
        weight=0.8,
    ),
]

# 执行评估
result = await engine.evaluate(
    target_type="task",
    target_id="task_001",
    evaluation_type=EvaluationType.QUALITY,
    criteria=criteria,
)

print(f"评估完成: {result.overall_score:.1f} ({result.level.value})")
print(f"强项: {result.strengths}")
print(f"弱项: {result.weaknesses}")

# 对评估结果进行反思
reflection = await engine.reflect(result.id)
print(f"见解数量: {len(reflection.insights)}")
print(f"行动项: {reflection.action_items}")
```

## 🔄 向后兼容

旧代码仍然可以使用，但会收到DeprecationWarning：

```python
# ⚠️ 旧方式（仍可用，但会收到警告）
from core.memory.unified_agent_memory_system import UnifiedAgentMemorySystem
from core.protocols.collaboration_protocols import CommunicationProtocol
from core.agent_collaboration.agents import SearchAgent
```

## 📝 完整迁移示例

### 迁移前（旧代码）

```python
# 旧代码
from core.memory.unified_agent_memory_system import (
    UnifiedAgentMemorySystem,
    MemoryType,
    AgentType,
)

from core.protocols.collaboration_protocols import (
    CommunicationProtocol,
)

from core.agent_collaboration.agents import (
    SearchAgent,
    AnalysisAgent,
)

from core.search.external.web_search_engines import (
    UnifiedWebSearchManager,
    SearchEngineType,
)
```

### 迁移后（新代码）

```python
# 新代码 - 更清晰的模块结构
from core.memory.unified_memory import (
    UnifiedAgentMemorySystem,
    MemoryType,
    AgentType,
)

from core.protocols.collaboration import (
    CommunicationProtocol,
)

from core.agent_collaboration.specialized_agents import (
    SearchAgent,
    AnalysisAgent,
)

from core.search.external.web_search import (
    UnifiedWebSearchManager,
    SearchEngineType,
)
```

## 🎯 快速参考

| 旧模块路径 | 新模块路径 |
|-----------|-----------|
| `core.memory.unified_agent_memory_system` | `core.memory.unified_memory` |
| `core.protocols.collaboration_protocols` | `core.protocols.collaboration` |
| `core.agent_collaboration.agents` | `core.agent_collaboration.specialized_agents` |
| `core.search.external.web_search_engines` | `core.search.external.web_search` |
| `core.agent_collaboration.agent_coordinator` | `core.agent_collaboration.agent_coordinator` |
| `core.planning.adaptive_meta_planner` | `core.planning.adaptive_meta_planner` |
| `core.collaboration.collaboration_patterns` | `core.collaboration.collaboration_patterns` (模块化目录) |
| `core.evaluation.evaluation_engine` | `core.evaluation.evaluation_engine` (模块化目录) |
| `core.cognition.xiaona_patent_naming_system` | `core.cognition.xiaona_patent_naming_system` (模块化目录) |
| `core.execution.optimized_execution_module` | `core.execution.optimized_execution_module` (模块化目录) |
| `core.search.selector.athena_search_selector` | `core.search.selector.athena_search_selector` (模块化目录) |
| `core.cognition.super_reasoning` | `core.cognition.super_reasoning` (模块化目录) |

### 9. 小娜专利命名系统 (Xiaona Patent Naming System)

```python
# ✅ 推荐的新导入方式
from core.cognition.xiaona_patent_naming_system import (
    # 类型定义
    PatentType,
    NamingStyle,
    PatentNamingRequest,
    PatentNamingResult,
    # 主系统
    XiaonaPatentNamingSystem,
)

# 📋 可用的PatentType枚举
PatentType.INVENTION       # 发明专利
PatentType.UTILITY_MODEL   # 实用新型专利
PatentType.DESIGN          # 外观设计专利

# 📋 可用的NamingStyle枚举
NamingStyle.TECHNICAL      # 技术导向型
NamingStyle.FUNCTIONAL     # 功能导向型
NamingStyle.INNOVATION     # 创新导向型
NamingStyle.APPLICATION    # 应用导向型

# 📋 使用示例
from core.cognition.xiaona_patent_naming_system import (
    XiaonaPatentNamingSystem,
    PatentType,
    NamingStyle,
    PatentNamingRequest,
)

# 创建命名系统
naming_system = XiaonaPatentNamingSystem()

# 创建命名请求
request = PatentNamingRequest(
    patent_type=PatentType.INVENTION,
    technical_field="化学工程",
    invention_description="异丁烷脱氢制MTBE的组合工艺...",
    key_features=["异丁烷脱氢", "MTBE合成", "组合工艺"],
    application_scenarios=["石油化工", "汽油添加剂生产"],
    innovation_points=["多级反应器设计", "工艺参数优化"],
    naming_style=NamingStyle.TECHNICAL,
)

# 生成专利名称
result = await naming_system.generate_patent_name(request)

print(f"专利名称: {result.patent_name}")
print(f"备选名称: {', '.join(result.alternative_names)}")
print(f"命名置信度: {result.naming_confidence:.2f}")
print(f"专业见解: {result.professional_insights}")
```

### 10. 优化版执行模块 (Optimized Execution Module)

```python
# ✅ 推荐的新导入方式
from core.execution.optimized_execution_module import (
    # 类型定义
    TaskPriority,
    TaskStatus,
    ResourceType,
    Task,
    ResourceRequirement,
    ResourceUsage,
    # 核心组件
    TaskPriorityQueue,
    IntelligentScheduler,
    ResourceMonitor,
    LoadBalancer,
    # 主模块
    OptimizedExecutionModule,
)

# 📋 可用的TaskPriority枚举
TaskPriority.CRITICAL      # 关键任务,最高优先级
TaskPriority.HIGH          # 高优先级
TaskPriority.NORMAL        # 普通优先级
TaskPriority.LOW           # 低优先级
TaskPriority.BACKGROUND    # 后台任务,最低优先级

# 📋 可用的TaskStatus枚举
TaskStatus.PENDING         # 等待中
TaskStatus.RUNNING         # 运行中
TaskStatus.COMPLETED       # 已完成
TaskStatus.FAILED          # 失败
TaskStatus.CANCELLED       # 已取消
TaskStatus.TIMEOUT         # 超时
TaskStatus.PAUSED          # 暂停

# 📋 使用示例
from core.execution.optimized_execution_module import (
    OptimizedExecutionModule,
    Task,
    TaskPriority,
)

# 创建执行模块
execution_module = OptimizedExecutionModule(
    agent_id="test_agent",
    config={
        "intelligent_scheduling": True,
        "load_balancing": True,
        "auto_scaling": True,
    }
)

# 提交任务
async def example_task():
    return "任务执行完成"

task_id = await execution_module.submit_task_optimized(
    name="example_task",
    function=example_task,
    priority=TaskPriority.HIGH,
    estimated_cpu=0.5,
    estimated_memory=0.3,
)

print(f"任务ID: {task_id}")

# 获取任务状态
status = await execution_module.get_task_status(task_id)
print(f"任务状态: {status}")

# 获取优化统计信息
stats = execution_module.get_optimization_stats()
print(f"统计信息: {stats}")
```

### 11. Athena超级推理引擎 (Athena Super Reasoning Engine)

```python
# ✅ 推荐的新导入方式
from core.cognition.super_reasoning import (
    # 类型定义
    ThinkingPhase,
    ReasoningMode,
    ThinkingState,
    ReasoningConfig,
    # 核心引擎
    AthenaSuperReasoningEngine,
    AthenaSuperReasoning,
    SuperReasoningEngine,
)

# 📋 可用的ThinkingPhase枚举
ThinkingPhase.INITIAL_ENGAGEMENT      # 初始参与
ThinkingPhase.PROBLEM_ANALYSIS         # 问题分析
ThinkingPhase.MULTIPLE_HYPOTHESES      # 多假设生成
ThinkingPhase.NATURAL_DISCOVERY        # 自然发现流
ThinkingPhase.TESTING_VERIFICATION     # 测试验证
ThinkingPhase.ERROR_RECOGNITION        # 错误识别
ThinkingPhase.KNOWLEDGE_SYNTHESIS      # 知识合成

# 📋 可用的ReasoningMode枚举
ReasoningMode.STANDARD                # 标准推理
ReasoningMode.DEEP                    # 深度推理
ReasoningMode.SUPER                   # 超级推理

# 📋 使用示例
from core.cognition.super_reasoning import (
    AthenaSuperReasoningEngine,
    ReasoningConfig,
    ReasoningMode,
)

# 创建推理引擎配置
config = ReasoningConfig(
    mode=ReasoningMode.SUPER,
    max_hypotheses=5,
    verification_rounds=3,
    confidence_threshold=0.7,
    depth_level=3,
)

# 创建并初始化推理引擎
engine = AthenaSuperReasoningEngine(config)
await engine.initialize()

# 执行推理
result = await engine.reason(
    query="如何分析这个专利技术的创新点?",
    context={"domain": "patent_analysis"}
)

print(f"推理成功: {result['success']}")
print(f"置信度: {result['confidence_level']:.2f}")
print(f"推理时间: {result['reasoning_time']:.2f}秒")
print(f"假设数量: {result['hypotheses_explored']}")
print(f"证据数量: {result['evidence_collected']}")

# 获取推理历史
history = engine.get_reasoning_history()
print(f"历史记录数: {len(history)}")
```

## ⚠️ 注意事项

1. **API未改变**: 所有类的公共接口保持不变，只是导入路径变化
2. **功能相同**: 重构只是拆分文件，没有修改核心功能
3. **向后兼容**: 旧的导入方式仍然可用，但会收到DeprecationWarning
4. **迁移建议**: 在下一个迭代中逐步更新导入语句

---

**文档版本**: 2.6.0
**更新时间**: 2026-01-27
**新增**: Athena超级推理引擎 (Athena Super Reasoning Engine) 迁移指南
**维护者**: Athena AI Platform Team
