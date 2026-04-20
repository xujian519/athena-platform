# 事件驱动架构设计文档

> **文档版本**: v1.0
> **创建日期**: 2026-04-20
> **作者**: 徐健
> **状态**: 设计阶段

---

## 📋 执行摘要

本文档描述了 Athena 平台事件驱动架构的设计，参考 OpenHarness 项目的实现，为多代理协调提供实时性和可观测性。

### 核心目标
1. **事件类型体系**: 定义 4 大类事件
2. **事件总线**: 发布/订阅模式的实时通信
3. **事件持久化**: SQLite 存储的事件历史
4. **Gateway 集成**: WebSocket 实时推送

---

## 🏗️ 架构设计

### 整体架构图

```
┌─────────────────────────────────────────────────────────┐
│                    Event Bus Core                      │
│  ┌──────────────────────────────────────────────────┐  │
│  │   EventBus (发布/订阅)                         │  │
│  │   - subscribe() / unsubscribe()                │  │
│  │   - publish() / publish_async()               │  │
│  │   - event filtering                           │  │
│  └──────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────┘
         │                    │                    │
    ┌────▼────┐        ┌─────▼─────┐      ┌─────▼─────┐
    │Publisher│        │Subscriber │      │EventStore│
    │ (Sync/   │        │ (Callback/ │      │(SQLite)  │
    │  Async)  │        │   Queue)   │      │          │
    └─────────┘        └───────────┘      └───────────┘
```

### 数据流

```
Agent Action → Publish Event → EventBus → Subscribers → Action
                                    ↓
                              EventStore → History
```

---

## 📦 核心组件

### 1. 事件类型体系

#### AgentLifecycleEvent
代理生命周期事件：
- `AgentStarted`: 代理启动
- `AgentStopped`: 代理停止
- `AgentError`: 代理错误

#### ToolExecutionEvent
工具执行事件：
- `ToolExecutionStarted`: 工具开始执行
- `ToolExecutionCompleted`: 工具执行完成
- `ToolExecutionFailed`: 工具执行失败

#### MessageEvent
消息传递事件：
- `MessageReceived`: 收到消息
- `MessageSent`: 发送消息
- `MessageError`: 消息错误

#### SystemEvent
系统事件：
- `SystemStartup`: 系统启动
- `SystemShutdown`: 系统关闭
- `SystemError`: 系统错误

### 2. 事件总线 (EventBus)

**核心接口**:
```python
class EventBus:
    async def publish(self, event: BaseEvent) -> None
    async def subscribe(
        self,
        event_type: type[BaseEvent],
        subscriber: EventSubscriber
    ) -> str
    async def unsubscribe(self, subscription_id: str) -> bool
```

**特性**:
- 异步发布/订阅
- 事件过滤
- 订阅管理
- 错误处理

### 3. 事件持久化 (EventStore)

**存储结构**:
```sql
CREATE TABLE events (
    id INTEGER PRIMARY KEY,
    event_type TEXT NOT NULL,
    event_data JSON NOT NULL,
    timestamp REAL NOT NULL,
    source TEXT,
    INDEX(event_type, timestamp)
);
```

### 4. Gateway 集成

**WebSocket 推送**:
```python
# Gateway 端点
@ws_router.websocket("/events")
async def event_stream(websocket: WebSocket):
    async for event in event_bus.subscribe(BaseEvent):
        await websocket.send_json(event.to_dict())
```

---

## 🎯 关键特性

### 1. 类型安全

使用 Python 类型注解确保类型安全：
```python
@dataclass
class BaseEvent:
    event_type: str
    timestamp: float
    source: str
```

### 2. 序列化

支持 JSON 序列化/反序列化：
```python
event.to_dict()  # 序列化
BaseEvent.from_dict(data)  # 反序列化
```

### 3. 异步优先

全面支持异步操作：
```python
await event_bus.publish_async(event)
await subscriber.on_event(event)
```

### 4. 事件过滤

支持基于类型的过滤：
```python
# 只订阅代理生命周期事件
await event_bus.subscribe(AgentLifecycleEvent, subscriber)
```

---

## 📊 性能目标

| 指标 | 目标 | 说明 |
|------|------|------|
| 事件发布延迟 | <10ms | 从 publish 到所有 subscriber 收到 |
| 事件吞吐量 | >1000 events/s | 持续吞吐量 |
| 订阅者数量 | >100 | 单个事件类型 |
| 内存占用 | <10MB | 1000 个事件缓存 |

---

## 🔌 集成点

### 1. 代理系统

```python
# 在代理启动时发布事件
await event_bus.publish(AgentStarted(
    agent_id="xiaona",
    agent_type="legal",
    timestamp=time.time()
))
```

### 2. 工具系统

```python
# 在工具执行前后发布事件
await event_bus.publish(ToolExecutionStarted(
    tool_id="patent_search",
    agent_id="xiaona",
    parameters={"query": "AI"}
))
```

### 3. Gateway

```python
# Gateway 推送事件到客户端
@ws_router.websocket("/events")
async def event_stream(websocket: WebSocket):
    async for event in event_bus.subscribe(BaseEvent):
        await websocket.send_json(event.to_dict())
```

---

## 🚀 实施计划

### Phase 1: 核心实现（Day 1-3）
- [x] 设计事件类型体系
- [ ] 实现 BaseEvent 和子类
- [ ] 实现 EventBus
- [ ] 实现 EventPublisher
- [ ] 实现 EventSubscriber

### Phase 2: 存储与监控（Day 4-5）
- [ ] 实现 EventStore
- [ ] 实现事件监控
- [ ] 实现事件查询

### Phase 3: 集成（Day 6-7）
- [ ] 集成到代理系统
- [ ] 集成到工具系统
- [ ] 集成到 Gateway

### Phase 4: 测试（Day 8-9）
- [ ] 单元测试
- [ ] 集成测试
- [ ] 性能测试

### Phase 5: 文档（Day 10）
- [ ] API 文档
- [ ] 使用指南
- [ ] 部署文档

---

## 📝 API 设计

### 发布事件

```python
# 同步发布
event_bus.publish(event)

# 异步发布
await event_bus.publish_async(event)

# 发布并等待所有订阅者处理完成
await event_bus.publish_and_await(event)
```

### 订阅事件

```python
# 回调订阅
class MySubscriber:
    async def on_agent_started(self, event: AgentStarted):
        print(f"Agent {event.agent_id} started")

subscriber = CallbackSubscriber(
    event_type=AgentStarted,
    callback=subscriber.on_agent_started
)

subscription_id = await event_bus.subscribe(AgentStarted, subscriber)
```

### 取消订阅

```python
await event_bus.unsubscribe(subscription_id)
```

---

## 🎨 设计模式

### 1. 观察者模式 (Observer)
EventBus 实现了经典的观察者模式：
- Subject: EventBus
- Observer: EventSubscriber
- Event: 被观察的对象

### 2. 发布-订阅模式 (Pub-Sub)
解耦事件发布者和订阅者：
- Publisher 不需要知道 Subscriber 的存在
- Subscriber 可以动态订阅/取消订阅

### 3. 中介者模式 (Mediator)
EventBus 作为中介者协调多个代理：
- 代理之间不直接通信
- 通过事件总线解耦

---

## 📊 事件流程示例

### 场景：专利检索流程

```
1. 用户请求专利检索
   ↓
2. Xiaonuo 收到请求
   ↓
3. 发布 MessageReceived 事件
   ↓
4. 委托给 Xiaona
   ↓
5. 发布 AgentStarted 事件
   ↓
6. Xiaona 执行专利检索工具
   ↓
7. 发布 ToolExecutionStarted 事件
   ↓
8. 工具执行完成
   ↓
9. 发布 ToolExecutionCompleted 事件
   ↓
10. Xiaona 返回结果
    ↓
11. 发布 AgentStopped 事件
    ↓
12. 返回结果给用户
```

---

## 🔍 与 OpenHarness 对比

| 特性 | OpenHarness | Athena 设计 |
|------|-------------|-----------|
| 事件类型 | 基础类型 | 4 大类详细类型 |
| 存储 | 文件系统 | SQLite |
| 订阅模式 | 回调 | 回调 + 队列 |
| 过滤 | 基于类型 | 基于类型 + 过滤器 |
| WebSocket | 原生支持 | Gateway 集成 |

---

## 🎯 成功标准

### 功能验收
- [ ] 4 大类事件正确实现
- [ ] 事件总线发布/订阅正常工作
- [ ] 事件持久化正常工作
- [ ] Gateway 事件推送正常

### 性能验收
- [ ] 事件发布延迟 <10ms
- [ ] 事件吞吐量 >1000 events/s
- [ ] 支持并发订阅者 >100
- [ ] 内存占用 <10MB

### 质量验收
- [ ] 单元测试覆盖率 >85%
- [ ] 所有测试通过
- [ ] 代码审查通过
- [ ] 文档完整

---

## 📚 参考资料

### 内部文档
- [Athena 平台架构](../../CLAUDE.md)
- [多代理协作](../../core/collaboration/)

### 外部参考
- [OpenHarness 事件系统](/Users/xujian/Downloads/OpenHarness-main/)

---

**创建时间**: 2026-04-20 17:45
**最后更新**: 2026-04-20 17:45
**作者**: 徐健
**状态**: 设计完成，待实施
