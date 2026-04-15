# 协作协议模块 - 快速参考指南

## 模块概览

Athena协作协议模块提供标准化的多智能体协作协议实现。

## 文件结构

```
core/protocols/
├── __init__.py                          # 模块入口，导出所有公共接口
├── collaboration_protocols.py           # 核心基础类和数据定义
├── advanced_coordination.py             # 高级协调协议
├── error_handling.py                    # 错误处理和异常定义
├── manager.py                           # 协议管理器 ✨ 新增
├── utils.py                             # 工具函数 ✨ 新增
├── REFACTORING_SUMMARY.md               # 重构总结文档
├── QUICK_REFERENCE.md                   # 本文档
└── collaboration/                       # 具体协议实现 ✨ 新目录
    ├── __init__.py                      # 协作子模块入口
    ├── communication_protocol.py        # 通信协议 ✨ 新增
    ├── coordination_protocol.py         # 协调协议 ✨ 新增
    └── decision_protocol.py             # 决策协议 ✨ 新增
```

## 快速开始

### 方式1: 使用协议管理器 (推荐)

```python
from core.protocols import protocol_manager

# 1. 创建通信协议
protocol_id = protocol_manager.create_communication_protocol(
    participants=["agent1", "agent2", "agent3"]
)

# 2. 启动协议
await protocol_manager.start_protocol(protocol_id)

# 3. 发送消息
message = ProtocolMessage(
    protocol_id=protocol_id,
    sender="agent1",
    content="Hello, agents!",
    message_type="broadcast"
)
protocol_manager.route_message(message)

# 4. 获取状态
status = protocol_manager.get_protocol_status(protocol_id)
print(f"协议状态: {status}")

# 5. 停止协议
await protocol_manager.stop_protocol(protocol_id)
```

### 方式2: 使用便捷函数

```python
from core.protocols.utils import (
    create_protocol_session,
    start_protocol_session,
    get_protocol_session_status,
    shutdown_protocol_manager
)

# 创建会话
protocol_id = create_protocol_session(
    protocol_type="communication",  # 或 "coordination", "decision"
    participants=["agent1", "agent2"]
)

# 启动会话
await start_protocol_session(protocol_id)

# 查看状态
status = get_protocol_session_status(protocol_id)

# 关闭管理器
await shutdown_protocol_manager()
```

### 方式3: 直接使用协议类

```python
from core.protocols.collaboration.communication_protocol import CommunicationProtocol

# 创建协议实例
protocol = CommunicationProtocol("comm_001")
protocol.add_participant("agent1")
protocol.add_participant("agent2")

# 设置配置
protocol.set_timeout(30)
protocol.set_retry_count(3)

# 启动协议
await protocol.start()

# 发送消息
message = ProtocolMessage(
    protocol_id="comm_001",
    sender="agent1",
    receiver="agent2",
    content="Direct message"
)
protocol.receive_message(message)
```

## 三种协议类型对比

### 1. 通信协议 (CommunicationProtocol)

**用途**: 智能体之间的基本消息传递

**特点**:
- ✅ 支持点对点和广播消息
- ✅ 消息持久化和历史记录
- ✅ 可配置的优先级和TTL
- ✅ 消息确认和重试机制

**适用场景**:
- 智能体间日常通信
- 信息共享和通知
- 简单的请求-响应模式

**示例**:
```python
from core.protocols import protocol_manager

protocol_id = protocol_manager.create_communication_protocol(
    participants=["patent_agent", "search_agent", "analysis_agent"]
)

# 发送广播消息
broadcast_msg = ProtocolMessage(
    protocol_id=protocol_id,
    sender="patent_agent",
    content="开始新的专利分析任务",
    message_type="broadcast"
)
protocol_manager.route_message(broadcast_msg)

# 发送点对点消息
direct_msg = ProtocolMessage(
    protocol_id=protocol_id,
    sender="patent_agent",
    receiver="search_agent",
    content="请搜索相关专利",
    message_type="direct",
    priority=10
)
protocol_manager.route_message(direct_msg)
```

### 2. 协调协议 (CoordinationProtocol)

**用途**: 多智能体任务协调和同步

**特点**:
- ✅ 任务分配和调度
- ✅ 进度跟踪和同步
- ✅ 资源分配和冲突解决
- ✅ 依赖关系管理

**适用场景**:
- 复杂任务的并行处理
- 工作流协调
- 资源共享和调度

**示例**:
```python
from core.protocols import protocol_manager

protocol_id = protocol_manager.create_coordination_protocol(
    participants=["agent1", "agent2", "agent3"]
)

# 分配任务
coord_protocol = protocol_manager.protocols[protocol_id]
coord_protocol.assign_task("task_001", "agent1", priority=5)
coord_protocol.assign_task("task_002", "agent2", priority=3, dependencies=["task_001"])

# 检查进度
status = coord_protocol.get_coordination_status()
print(f"总任务: {status.total_tasks}")
print(f"已完成: {status.completed_tasks}")
print(f"进行中: {status.in_progress_tasks}")
```

### 3. 决策协议 (DecisionProtocol)

**用途**: 多智能体集体决策和投票

**特点**:
- ✅ 支持多种投票机制 (多数决、共识、加权)
- ✅ 投票超时和自动决策
- ✅ 决策历史和审计
- ✅ 可配置的决策阈值

**适用场景**:
- 需要多个智能体达成共识的决策
- 风险评估和选择
- 冲突解决和仲裁

**示例**:
```python
from core.protocols import protocol_manager

protocol_id = protocol_manager.create_decision_protocol(
    participants=["expert1", "expert2", "expert3"]
)

# 启动投票
decision_protocol = protocol_manager.protocols[protocol_id]
decision_protocol.start_voting(
    proposal_id="decision_001",
    proposal="选择技术方案A",
    voting_method="majority",  # 多数决
    timeout=60
)

# 智能体投票
decision_protocol.cast_vote("expert1", "decision_001", "approve")
decision_protocol.cast_vote("expert2", "decision_001", "approve")
decision_protocol.cast_vote("expert3", "decision_001", "reject")

# 查看结果
result = decision_protocol.get_decision_result("decision_001")
print(f"决策结果: {result.outcome}")  # approved
print(f"赞成票: {result.approval_count}")  # 2
print(f"反对票: {result.rejection_count}")  # 1
```

## 常用配置参数

### 通信协议配置
```python
protocol.set_timeout(30)              # 消息超时时间(秒)
protocol.set_retry_count(3)           # 重试次数
protocol.enable_persistence(True)     # 启用消息持久化
protocol.set_max_history(1000)        # 最大历史记录数
```

### 协调协议配置
```python
protocol.enable_auto_escalation(True) # 启用自动升级
protocol.set_conflict_timeout(10)     # 冲突解决超时(秒)
protocol.set_max_parallel_tasks(5)    # 最大并行任务数
```

### 决策协议配置
```python
protocol.set_voting_method("consensus")  # 投票方法: majority/consensus/weighted
protocol.set_consensus_threshold(0.75)   # 共识阈值 (0-1)
protocol.set_default_timeout(60)         # 默认投票超时(秒)
protocol.enable_abstention(True)         # 允许弃权
```

## 错误处理

```python
from core.protocols.error_handling import (
    ProtocolError,
    ProtocolValidationError,
    ProtocolTimeoutError,
    ProtocolConflictError
)

try:
    protocol_id = protocol_manager.create_communication_protocol(
        participants=["agent1", "agent2"]
    )
    await protocol_manager.start_protocol(protocol_id)
except ProtocolValidationError as e:
    print(f"协议验证失败: {e}")
except ProtocolTimeoutError as e:
    print(f"协议超时: {e}")
except ProtocolConflictError as e:
    print(f"协议冲突: {e}")
except ProtocolError as e:
    print(f"协议错误: {e}")
```

## 监控和调试

### 获取所有协议状态
```python
all_status = protocol_manager.get_all_protocols_status()
for protocol_id, status in all_status.items():
    print(f"协议 {protocol_id}: {status['status']}")
```

### 获取协议统计信息
```python
# 通信协议统计
comm_protocol = protocol_manager.protocols[protocol_id]
stats = comm_protocol.get_communication_statistics()
print(f"发送消息: {stats.messages_sent}")
print(f"接收消息: {stats.messages_received}")
print(f"平均延迟: {stats.average_latency}ms")

# 协调协议统计
coord_protocol = protocol_manager.protocols[protocol_id]
stats = coord_protocol.get_coordination_statistics()
print(f"总任务: {stats.total_tasks}")
print(f"完成率: {stats.completion_rate}%")

# 决策协议统计
decision_protocol = protocol_manager.protocols[protocol_id]
stats = decision_protocol.get_decision_statistics()
print(f"总决策: {stats.total_decisions}")
print(f"通过率: {stats.approval_rate}%")
```

## 最佳实践

### 1. 选择合适的协议类型
- **简单消息传递** → CommunicationProtocol
- **任务协调** → CoordinationProtocol
- **集体决策** → DecisionProtocol

### 2. 合理设置超时时间
```python
# 短期任务
protocol.set_timeout(30)  # 30秒

# 长期任务
protocol.set_timeout(300)  # 5分钟

# 不确定时长的任务
protocol.set_timeout(0)  # 无限制
```

### 3. 启用消息持久化
```python
# 重要通信启用持久化
protocol.enable_persistence(True)
protocol.set_max_history(10000)
```

### 4. 使用适当的投票方法
```python
# 快速决策 - 多数决
protocol.set_voting_method("majority")

# 重要决策 - 共识
protocol.set_voting_method("consensus")
protocol.set_consensus_threshold(0.8)

# 专家加权决策
protocol.set_voting_method("weighted")
```

### 5. 错误恢复
```python
# 自动重试
protocol.set_retry_count(3)

# 失败时回退
protocol.enable_auto_rollback(True)

# 记录错误日志
import logging
logging.basicConfig(level=logging.INFO)
```

## 性能优化建议

1. **消息批处理**: 批量发送消息而不是逐条发送
2. **异步处理**: 使用async/await避免阻塞
3. **连接池**: 复用协议连接
4. **缓存**: 缓存频繁访问的协议状态
5. **监控**: 定期检查协议性能指标

## 相关文档

- [重构总结](REFACTORING_SUMMARY.md) - 详细的模块重构信息
- [错误处理](error_handling.py) - 错误类型和异常处理
- [高级协调](advanced_coordination.py) - 高级协调协议实现

## 版本历史

- **v2.1.0** (2026-01-26): 模块化重构，提取独立协议文件
- **v1.0.0** (2025-12-04): 初始版本

## 支持

如有问题或建议，请联系 Athena AI Team。
