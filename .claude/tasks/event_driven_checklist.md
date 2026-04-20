# 事件驱动架构设计与实现 - 检查清单

> **任务ID**: #1
> **预计时间**: 1.5周
> **优先级**: 🔴 高

---

## 📋 Phase 1: 研究与设计（Day 1-2）

### 1.1 研究现有架构
- [ ] 阅读 `core/collaboration/` 现有实现
- [ ] 分析 Gateway (8005) WebSocket 架构
- [ ] 理解现有代理通信机制
- [ ] 识别事件化改造点

### 1.2 研究 OpenHarness 事件系统
- [ ] 阅读 `/Users/xujian/Downloads/OpenHarness-main/` 事件相关代码
- [ ] 分析事件类型定义
- [ ] 研究事件发布/订阅机制
- [ ] 理解事件流处理

### 1.3 设计事件类型体系
- [ ] 定义核心事件类型
  - [ ] AgentLifecycleEvent（代理生命周期）
  - [ ] ToolExecutionEvent（工具执行）
  - [ ] MessageEvent（消息传递）
  - [ ] SystemEvent（系统事件）
- [ ] 定义事件元数据结构
- [ ] 设计事件继承层次
- [ ] 确定事件序列化格式

### 1.4 设计事件总线架构
- [ ] 设计事件总线接口
- [ ] 设计发布/订阅模式
- [ ] 设计事件过滤机制
- [ ] 设计事件持久化策略
- [ ] 设计错误处理和重试
- [ ] 编写架构设计文档

**输出**：
- `docs/architecture/EVENT_DRIVEN_ARCHITECTURE.md`

---

## 📋 Phase 2: 核心组件实现（Day 3-7）

### 2.1 创建目录结构
- [ ] 创建 `core/events/` 目录
- [ ] 创建 `tests/events/` 测试目录
- [ ] 创建 `tests/events/test_event_bus.py` 测试文件

### 2.2 实现事件类型定义
- [ ] 定义 `BaseEvent` 抽象类
- [ ] 实现 `AgentLifecycleEvent`
  - [ ] AgentStarted
  - [ ] AgentStopped
  - [ ] AgentError
- [ ] 实现 `ToolExecutionEvent`
  - [ ] ToolExecutionStarted
  - [ ] ToolExecutionCompleted
  - [ ] ToolExecutionFailed
- [ ] 实现 `MessageEvent`
  - [ ] MessageReceived
  - [ ] MessageSent
  - [ ] MessageError
- [ ] 实现 `SystemEvent`
  - [ ] SystemStartup
  - [ ] SystemShutdown
  - [ ] SystemError
- [ ] 实现事件序列化/反序列化
- [ ] 添加事件验证

**文件**：`core/events/event_types.py`

### 2.3 实现事件总线
- [ ] 定义 `EventBus` 接口
- [ ] 实现 `InMemoryEventBus`（内存总线）
- [ ] 实现订阅管理
- [ ] 实现事件发布
- [ ] 实现事件分发
- [ ] 实现事件过滤
- [ ] 实现异步处理
- [ ] 添加错误处理

**文件**：`core/events/event_bus.py`

### 2.4 实现事件发布器
- [ ] 定义 `EventPublisher` 接口
- [ ] 实现 `SyncPublisher`（同步发布）
- [ ] 实现 `AsyncPublisher`（异步发布）
- [ ] 实现发布重试机制
- [ ] 实现发布超时控制
- [ ] 添加发布日志

**文件**：`core/events/publisher.py`

### 2.5 实现事件订阅器
- [ ] 定义 `EventSubscriber` 接口
- [ ] 实现 `CallbackSubscriber`（回调订阅）
- [ ] 实现 `QueueSubscriber`（队列订阅）
- [ ] 实现订阅过滤
- [ ] 实现订阅优先级
- [ ] 实现订阅异常处理

**文件**：`core/events/subscriber.py`

### 2.6 实现事件监控
- [ ] 定义 `EventMonitor` 接口
- [ ] 实现事件计数器
- [ ] 实现事件计时器
- [ ] 实现事件日志记录
- [ ] 实现事件统计
- [ ] 实现性能监控

**文件**：`core/events/monitors.py`

### 2.7 实现事件持久化
- [ ] 定义 `EventStore` 接口
- [ ] 实现 `SQLiteEventStore`（SQLite 存储）
- [ ] 实现事件追加
- [ ] 实现事件查询
- [ ] 实现事件清理策略
- [ ] 添加性能优化

**文件**：`core/events/event_store.py`

---

## 📋 Phase 3: 集成与改造（Day 8-9）

### 3.1 集成到代理系统
- [ ] 更新 `BaseAgent` 集成事件发布
- [ ] 在代理启动时发布 AgentStarted 事件
- [ ] 在代理停止时发布 AgentStopped 事件
- [ ] 在代理错误时发布 AgentError 事件
- [ ] 在消息处理时发布 MessageEvent

### 3.2 集成到工具系统
- [ ] 更新 `tool_call_manager.py` 集成事件发布
- [ ] 在工具执行前发布 ToolExecutionStarted
- [ ] 在工具执行后发布 ToolExecutionCompleted
- [ ] 在工具失败时发布 ToolExecutionFailed
- [ ] 添加工具执行监控

### 3.3 集成到 Gateway
- [ ] 更新 Gateway WebSocket 处理
- [ ] 将事件推送到 WebSocket 客户端
- [ ] 实现事件订阅 API
- [ ] 实现事件查询 API
- [ ] 添加事件认证

### 3.4 实现事件日志
- [ ] 配置事件日志记录
- [ ] 实现结构化日志输出
- [ ] 集成到现有日志系统
- [ ] 实现日志轮转
- [ ] 添加日志查询

---

## 📋 Phase 4: 测试与优化（Day 10-11）

### 4.1 单元测试
- [ ] 测试事件类型序列化/反序列化
- [ ] 测试事件总线发布/订阅
- [ ] 测试事件发布器（同步/异步）
- [ ] 测试事件订阅器（回调/队列）
- [ ] 测试事件过滤
- [ ] 测试事件监控
- [ ] 测试事件持久化
- [ ] 测试并发安全性
- [ ] 测试错误处理

**目标覆盖率**：>85%

### 4.2 集成测试
- [ ] 测试代理事件发布
- [ ] 测试工具执行事件发布
- [ ] 测试 Gateway 事件推送
- [ ] 测试事件订阅 API
- [ ] 测试事件查询 API
- [ ] 测试端到端事件流

### 4.3 性能测试
- [ ] 基准测试事件发布延迟
- [ ] 测试高并发事件发布
- [ ] 测试大量订阅者场景
- [ ] 测试事件持久化性能
- [ ] 优化性能瓶颈

**目标**：
- 事件发布延迟 <10ms
- 支持并发订阅者 >100
- 事件持久化吞吐量 >1000 events/s

### 4.4 可靠性测试
- [ ] 测试订阅者崩溃恢复
- [ ] 测试事件总线重启恢复
- [ ] 测试事件丢失恢复
- [ ] 测试网络分区恢复
- [ ] 测试内存泄漏

---

## 📋 Phase 5: 文档与部署（Day 12-14）

### 5.1 编写文档
- [ ] 更新 `CLAUDE.md` 架构说明
- [ ] 编写 `EVENT_DRIVEN_ARCHITECTURE.md` 架构文档
- [ ] 编写 `EVENT_SYSTEM_API.md` API 文档
- [ ] 编写 `EVENT_SYSTEM_GUIDE.md` 使用指南
- [ ] 编写 `EVENT_PATTERNS.md` 事件模式最佳实践
- [ ] 更新示例代码

### 5.2 代码审查
- [ ] 自我代码审查
- [ ] 运行 ruff 格式检查
- [ ] 运行 mypy 类型检查
- [ ] 运行 pytest 测试套件
- [ ] 修复所有警告和错误

### 5.3 部署准备
- [ ] 准备配置文件
- [ ] 准备数据库迁移脚本
- [ ] 准备回滚方案
- [ ] 通知团队成员
- [ ] 准备监控仪表板

### 5.4 部署与验证
- [ ] 部署到测试环境
- [ ] 执行事件流测试
- [ ] 验证事件监控
- [ ] 监控性能指标
- [ ] 收集用户反馈
- [ ] 优化发现的问题

---

## ✅ 验收标准

### 功能验收
- [ ] 所有核心事件类型正确实现
- [ ] 事件总线发布/订阅正常工作
- [ ] 事件持久化正常工作
- [ ] Gateway 事件推送正常
- [ ] 事件监控和日志正常

### 性能验收
- [ ] 事件发布延迟 <10ms
- [ ] 支持并发订阅者 >100
- [ ] 事件持久化吞吐量 >1000 events/s
- [ ] 内存占用增加可控（<15%）
- [ ] CPU 占用增加可控（<10%）

### 可靠性验收
- [ ] 订阅者崩溃自动恢复
- [ ] 事件总线重启自动恢复
- [ ] 无事件丢失
- [ ] 无内存泄漏
- [ ] 通过可靠性测试

### 质量验收
- [ ] 单元测试覆盖率 >85%
- [ ] 所有测试通过
- [ ] 代码审查通过
- [ ] 文档完整
- [ ] 无已知严重 Bug

---

## 🚨 风险与缓解

| 风险 | 影响 | 概率 | 缓解措施 |
|------|------|------|----------|
| 性能下降 | 中 | 中 | 性能基准测试，异步处理 |
| 事件丢失 | 高 | 低 | 持久化，重试机制 |
| 订阅者阻塞 | 中 | 中 | 异步分发，超时控制 |
| 内存泄漏 | 高 | 低 | 内存监控，压力测试 |
| 复杂度增加 | 中 | 高 | 清晰文档，示例代码 |

---

## 📊 进度跟踪

- **Phase 1 完成度**：___ / 8
- **Phase 2 完成度**：___ / 35
- **Phase 3 完成度**：___ / 17
- **Phase 4 完成度**：___ / 23
- **Phase 5 完成度**：___ / 19

**总体完成度**：___ / 102 (___%)

---

## 📝 事件类型示例

### 核心事件类型
```python
# 代理生命周期事件
class AgentLifecycleEvent(BaseEvent):
    agent_id: str
    agent_type: str
    timestamp: datetime

class AgentStarted(AgentLifecycleEvent):
    pass

class AgentStopped(AgentLifecycleEvent):
    reason: str | None = None

class AgentError(AgentLifecycleEvent):
    error: str
    traceback: str | None = None

# 工具执行事件
class ToolExecutionEvent(BaseEvent):
    tool_id: str
    agent_id: str
    timestamp: datetime

class ToolExecutionStarted(ToolExecutionEvent):
    parameters: dict[str, Any]

class ToolExecutionCompleted(ToolExecutionEvent):
    parameters: dict[str, Any]
    result: Any
    execution_time: float

class ToolExecutionFailed(ToolExecutionEvent):
    parameters: dict[str, Any]
    error: str
    execution_time: float
```

### 事件订阅示例
```python
# 订阅所有工具执行事件
event_bus.subscribe(
    event_type=ToolExecutionEvent,
    subscriber=CallbackSubscriber(
        callback=lambda event: print(f"Tool {event.tool_id} executed"),
        filter=lambda event: event.agent_id == "xiaona"
    )
)

# 订阅所有代理错误事件
event_bus.subscribe(
    event_type=AgentError,
    subscriber=QueueSubscriber(
        queue=error_queue,
        max_size=1000
    )
)
```

---

## 🎯 使用场景

### 1. 实时监控
```python
# 监控所有工具执行
async def monitor_tool_execution():
    async for event in event_bus.subscribe(ToolExecutionEvent):
        print(f"[{event.timestamp}] {event.tool_id} - {event.execution_time}ms")
```

### 2. 审计日志
```python
# 记录所有关键事件
async def audit_logger():
    async for event in event_bus.subscribe(BaseEvent):
        event_store.append(event)
```

### 3. 告警系统
```python
# 监控错误事件
async def alert_on_error():
    async for event in event_bus.subscribe(AgentError):
        send_alert(f"Agent {event.agent_id} error: {event.error}")
```

### 4. 性能分析
```python
# 统计工具执行时间
async def performance_analyzer():
    stats = {}
    async for event in event_bus.subscribe(ToolExecutionCompleted):
        tool_id = event.tool_id
        stats[tool_id] = stats.get(tool_id, 0) + event.execution_time
        print(f"{tool_id}: avg {stats[tool_id] / count}ms")
```

---

**创建时间**：2026-04-20
**最后更新**：2026-04-20
**负责人**：徐健
