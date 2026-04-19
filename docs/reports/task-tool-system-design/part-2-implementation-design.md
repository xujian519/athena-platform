---

## 3. Python实现设计

### 3.1 核心模块架构

```
core/agents/
├── base_agent.py                    # 现有BaseAgent
├── task_tool.py                     # ⭐ 新增：Task Tool实现
├── background_task_manager.py       # ⭐ 新增：后台任务管理器
├── model_mapper.py                  # ⭐ 新增：模型映射器
├── fork_context_builder.py          # ⭐ 新增：Fork上下文构建
└── subagent_registry.py             # ⭐ 新增：子代理注册表

core/task/
├── __init__.py
├── task_store.py                    # ⭐ 任务存储 (四层记忆集成)
├── task_scheduler.py                # ⭐ 任务调度器
└── task_monitor.py                  # ⭐ 任务监控

core/collaboration/
├── subagent_delegation.py           # 🔄 扩展：子代理委托模式
├── fork_context.py                  # ⭐ 新增：Fork上下文
└── background_coordination.py       # ⭐ 新增：后台任务协调
```

### 3.2 实现优先级

**P0 - 核心模块 (必须实现)**:
1. model_mapper.py - 模型映射器
2. background_task_manager.py - 后台任务管理器
3. task_store.py - 任务存储
4. task_tool.py - Task Tool主体

**P1 - 扩展模块 (建议实现)**:
1. subagent_registry.py - 子代理注册表
2. fork_context_builder.py - Fork上下文构建
3. task_scheduler.py - 任务调度器

**P2 - 增强模块 (可选实现)**:
1. task_monitor.py - 任务监控
2. background_coordination.py - 后台任务协调

### 3.3 关键数据流

```
用户请求
    ↓
TaskTool.execute()
    ↓
验证输入
    ↓
选择模型 (ModelMapper)
    ↓
获取子代理
    ↓
过滤工具
    ↓
构建Fork上下文
    ↓
执行模式选择
    ├─→ 同步执行
    │   ↓
    │   查询循环
    │   ↓
    │   进度跟踪
    │   ↓
    │   返回结果
    └─→ 异步后台执行
        ↓
        创建TaskRecord
        ↓
        提交到BackgroundTaskManager
        ↓
        立即返回
```

### 3.4 四层记忆系统集成方案

| 数据类型 | 存储层级 | 保留策略 | 访问模式 |
|---------|---------|---------|---------|
| **运行中任务状态** | HOT (memory) | 24小时 | 读写 |
| **Agent transcript** | WARM (Redis) | 7天 | 读写 |
| **历史任务记录** | COLD (SQLite) | 90天 | 追加/查询 |
| **任务归档** | ARCHIVE (文件) | 永久 | 只读 |

---

## 4. 专利领域特定代理类型

### 4.1 代理类型定义

```python
PATENT_AGENT_TYPES = {
    "patent-analyst": {
        "description": "专利分析师 - 分析专利技术方案和创新点",
        "model": "task",  # sonnet → task
        "tools": [
            "patent-search",
            "patent-analysis",
            "knowledge-graph-query",
            "embedding-search",
        ],
        "capabilities": [
            "patent-technical-analysis",
            "patent-innovation-assessment",
            "patent-comparative-analysis",
        ],
    },
    "patent-searcher": {
        "description": "专利检索专家 - 执行专利检索和筛选",
        "model": "quick",  # haiku → quick
        "tools": [
            "patent-search",
            "patent-filter",
            "patent-export",
        ],
        "capabilities": [
            "patent-bibliographic-search",
            "patent-semantic-search",
            "patent-facet-search",
        ],
    },
    "legal-researcher": {
        "description": "法律研究员 - 研究专利法律法规和案例",
        "model": "main",  # opus → main
        "tools": [
            "legal-knowledge-query",
            "case-law-search",
            "statute-lookup",
        ],
        "capabilities": [
            "legal-knowledge-retrieval",
            "case-law-analysis",
            "statute-interpretation",
        ],
    },
    "patent-drafter": {
        "description": "专利撰写专家 - 撰写专利申请文件",
        "model": "main",  # opus → main
        "tools": [
            "patent-drafting",
            "patent-review",
            "patent-formatting",
        ],
        "capabilities": [
            "patent-claims-drafting",
            "patent-description-writing",
            "patent-specification-review",
        ],
    },
}
```

### 4.2 代理工作流示例

**专利分析工作流**:
```
小娜 (主代理)
    ↓
Task: "分析专利CN202310123456.7的技术方案"
    ↓
Subagent: patent-analyst (model: sonnet → task)
    ↓
执行流程:
1. 专利检索 (patent-search)
2. 技术分析 (patent-analysis)
3. 创新点评估 (knowledge-graph-query)
    ↓
返回分析报告
```

**专利检索工作流**:
```
小娜 (主代理)
    ↓
Task: "检索关于量子计算的专利"
    ↓
Subagent: patent-searcher (model: haiku → quick, run_in_background=True)
    ↓
执行流程:
1. 构建检索策略
2. 执行检索 (patent-search)
3. 结果筛选和排序
4. 导出结果
    ↓
后台运行，立即返回 task_id
    ↓
用户可以随时查询任务状态
```

---

## 5. 实施计划

### 5.1 Phase 0: 准备阶段 (2天)
**目标**: 环境准备和架构设计

**任务**:
- [P0-5.1] 创建模块目录结构
- [P0-5.2] 定义数据模型和接口
- [P0-5.3] 设计四层记忆集成方案
- [P0-5.4] 编写单元测试框架

### 5.2 Phase 1: 核心模块开发 (5天)
**目标**: 实现P0核心模块

**任务**:
- [P1-5.1] 实现ModelMapper
- [P1-5.2] 实现BackgroundTaskManager
- [P1-5.3] 实现TaskStore (四层记忆集成)
- [P1-5.4] 实现TaskTool主体
- [P1-5.5] 单元测试和集成测试

### 5.3 Phase 2: 扩展功能开发 (4天)
**目标**: 实现P1扩展模块

**任务**:
- [P2-5.1] 实现SubagentRegistry
- [P2-5.2] 实现ForkContextBuilder
- [P2-5.3] 实现TaskScheduler
- [P2-5.4] 集成现有ToolManager
- [P2.5] 系统测试

### 5.4 Phase 3: 专利领域适配 (3天)
**目标**: 专利特定代理类型和工作流

**任务**:
- [P3-5.1] 定义专利代理类型配置
- [P3-5.2] 实现专利分析工作流
- [P3-5.3] 实现专利检索工作流
- [P3-5.4] 端到端测试

### 5.5 Phase 4: 文档和优化 (2天)
**目标**: 完善文档和性能优化

**任务**:
- [P4-5.1] 编写API文档
- [P4-5.2] 编写使用示例
- [P4-5.3] 性能测试和优化
- [P4-5.4] 生产环境准备

---

## 6. 风险和挑战

### 6.1 技术风险

| 风险 | 影响 | 概率 | 缓解措施 |
|------|------|------|---------|
| 四层记忆系统集成复杂 | 高 | 中 | 分阶段集成，先HOT再WARM/COLD |
| 后台任务资源泄露 | 高 | 低 | 引用计数 + 定期清理机制 |
| Fork上下文隔离不完整 | 中 | 中 | 使用进程隔离而非线程 |
| 模型映射不兼容 | 中 | 低 | 支持自定义映射配置 |

### 6.2 架构挑战

1. **BaseAgent扩展兼容性**
   - 需要保持向后兼容
   - 不能破坏现有代理功能

2. **ToolManager集成**
   - 需要适配现有工具系统
   - 避免工具注册冲突

3. **异步一致性**
   - 同步/异步模式数据一致性
   - 任务状态持久化可靠性

### 6.3 性能挑战

1. **并发任务调度**
   - 最大并发任务数限制
   - 任务优先级调度

2. **内存管理**
   - HOT层容量控制 (100MB)
   - 消息缓存大小限制

3. **I/O性能**
   - 任务持久化批量写入
   - 任务查询索引优化

---

## 7. 成功指标

### 7.1 功能指标

- ✅ 成功实现Task Tool核心功能
- ✅ 支持同步/异步两种执行模式
- ✅ 完整的输入验证和错误处理
- ✅ 模型映射和选择机制

### 7.2 质量指标

- **测试覆盖率**: >85% (核心模块)
- **代码规范**: 符合PEP 8和Athena代码规范
- **文档完整性**: 所有公共API都有文档
- **类型注解**: 100%覆盖

### 7.3 性能指标

- **任务启动延迟**: <100ms
- **后台任务并发**: 支持10+并发任务
- **内存占用**: HOT层 <100MB
- **API响应时间**: P95 <200ms

### 7.4 兼容性指标

- ✅ 与BaseAgent完全兼容
- ✅ 与ToolManager无缝集成
- ✅ 与四层记忆系统完全集成
- ✅ 支持现有所有工具类型

---

**文档结束**
