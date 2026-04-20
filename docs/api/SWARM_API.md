# Swarm模式API文档

**作者**: Athena平台团队
**创建时间**: 2026-04-20
**版本**: 1.0.0

---

## 概述

Swarm协作模式实现群体智能协作，支持自组织协调、分布式决策、状态同步和知识共享。

---

## 核心类

### SwarmCollaborationPattern

Swarm协作模式主类。

```python
from core.collaboration.collaboration_patterns.patterns import SwarmCollaborationPattern

swarm = SwarmCollaborationPattern(framework)
```

#### 方法

##### initiate_collaboration

启动Swarm协作会话。

```python
session_id = await swarm.initiate_collaboration(
    task=task,
    participants=["agent_001", "agent_002"],
    context={
        "mode": "exploration",
        "decision_type": SwarmDecisionType.MAJORITY,
        "consensus_threshold": 0.7,
    }
)
```

**参数**:
- `task`: 任务对象
- `participants`: 参与者ID列表
- `context`: 上下文信息

**返回**: 会话ID或None

##### coordinate_execution

协调执行过程。

```python
success = await swarm.coordinate_execution(session_id)
```

**参数**:
- `session_id`: 会话ID

**返回**: 是否成功

##### handle_conflicts

处理协作冲突。

```python
resolved = await swarm.handle_conflicts(session_id, conflicts)
```

##### add_member / remove_member

动态添加/移除成员。

```python
await swarm.add_member(session_id, "agent_003")
await swarm.remove_member(session_id, "agent_002")
```

##### initiate_emergency_mode

启动紧急模式。

```python
await swarm.initiate_emergency_mode(
    session_id,
    SwarmEmergencyType.HIGH_PRIORITY
)
```

---

### SwarmAgent

群体中的个体Agent。

```python
from core.collaboration.collaboration_patterns.patterns import SwarmAgent, SwarmRole

agent = SwarmAgent(
    agent_id="agent_001",
    capabilities=["search", "analyze"],
    initial_role=SwarmRole.WORKER
)
```

#### 属性

- `agent_id`: Agent ID
- `role`: 当前角色 (SwarmRole)
- `capabilities`: 能力列表
- `neighbors`: 邻居列表
- `current_load`: 当前负载 (0.0-1.0)
- `reputation_score`: 声誉评分 (0.0-1.0)

#### 方法

##### change_role

更改角色。

```python
agent.change_role(SwarmRole.EXPLORER)
```

##### is_available

检查是否可用。

```python
if agent.is_available():
    # 分配任务
    pass
```

---

### SwarmDecisionEngine

分布式决策引擎。

```python
from core.collaboration.collaboration_patterns.patterns import SwarmDecisionEngine

engine = SwarmDecisionEngine(
    default_decision_type=SwarmDecisionType.MAJORITY,
    default_consensus_threshold=0.7
)
```

#### 方法

##### create_proposal

创建提案。

```python
proposal = await engine.create_proposal(
    proposer="agent_001",
    content={"action": "use_model_BGE_M3"},
    proposal_type="model_selection"
)
```

##### cast_vote

投票。

```python
await engine.cast_vote(
    proposal_id="prop_001",
    voter_id="agent_002",
    vote="agree",
    weight=1.0
)
```

##### calculate_decision

计算决策结果。

```python
result = await engine.calculate_decision("prop_001")
# result: {"result": "approved", "tally": {...}}
```

---

### SwarmSharedState

群体共享状态。

```python
from core.collaboration.collaboration_patterns.patterns import SwarmSharedState

state = SwarmSharedState()
```

#### 方法

##### update_member_state

更新成员状态。

```python
state.update_member_state("agent_001", {
    "role": SwarmRole.WORKER,
    "current_load": 0.5
})
```

##### add_knowledge

添加知识。

```python
from core.collaboration.collaboration_patterns.patterns import SwarmKnowledgeItem

knowledge = SwarmKnowledgeItem(
    key="patent_info",
    value={"title": "测试专利"},
    source="agent_001",
    confidence=0.9
)
state.add_knowledge(knowledge)
```

##### get_knowledge

获取知识。

```python
knowledge = state.get_knowledge("patent_info")
```

---

### SwarmCommunicationProtocol

通信协议。

```python
from core.collaboration.collaboration_patterns.patterns import SwarmCommunicationProtocol

comm = SwarmCommunicationProtocol(session_id)
```

#### 方法

##### broadcast

广播消息。

```python
message = await comm.broadcast(
    sender_id="system",
    message_type=SwarmMessageType.TASK_ANNOUNCE,
    content={"task_id": "task_001"}
)
```

##### multicast

组播消息（特定角色）。

```python
message = await comm.multicast(
    sender_id="coordinator",
    message_type=SwarmMessageType.ROLE_CHANGE,
    content={"new_role": "explorer"},
    target_role=SwarmRole.WORKER
)
```

##### unicast

单播消息（点对点）。

```python
message = await comm.unicast(
    sender_id="agent_001",
    receiver_id="agent_002",
    message_type=SwarmMessageType.HELP_REQUEST,
    content={"help_type": "resource"}
)
```

---

## 枚举类型

### SwarmRole

群体角色。

```python
from core.collaboration.collaboration_patterns.patterns import SwarmRole

SwarmRole.EXPLORER      # 探索者
SwarmRole.WORKER        # 工作者
SwarmRole.ANALYZER      # 分析者
SwarmRole.COORDINATOR   # 协调者
SwarmRole.OBSERVER      # 观察者
SwarmRole.SCOUT         # 侦察兵
```

### SwarmDecisionType

决策类型。

```python
from core.collaboration.collaboration_patterns.patterns import SwarmDecisionType

SwarmDecisionType.CONSENSUS       # 完全共识
SwarmDecisionType.MAJORITY        # 多数决
SwarmDecisionType.SUPER_MAJORITY  # 超级多数
SwarmDecisionType.WEIGHTED        # 加权投票
SwarmDecisionType.DELEGATED       # 委托决策
SwarmDecisionType.EMERGENCY       # 紧急决策
```

### SwarmMessageType

消息类型。

```python
from core.collaboration.collaboration_patterns.patterns import SwarmMessageType

# 协调消息
SwarmMessageType.JOIN_SWARM
SwarmMessageType.LEAVE_SWARM
SwarmMessageType.ROLE_CHANGE
SwarmMessageType.HEARTBEAT

# 任务消息
SwarmMessageType.TASK_ANNOUNCE
SwarmMessageType.TASK_CLAIM
SwarmMessageType.TASK_COMPLETE
SwarmMessageType.TASK_FAILED

# 决策消息
SwarmMessageType.PROPOSAL
SwarmMessageType.VOTE
SwarmMessageType.DECISION
SwarmMessageType.DISCUSSION

# 状态消息
SwarmMessageType.STATE_UPDATE
SwarmMessageType.KNOWLEDGE_SHARE
SwarmMessageType.KNOWLEDGE_QUERY

# 紧急消息
SwarmMessageType.EMERGENCY
SwarmMessageType.HELP_REQUEST
SwarmMessageType.HELP_RESPONSE
```

### SwarmEmergencyType

紧急类型。

```python
from core.collaboration.collaboration_patterns.patterns import SwarmEmergencyType

SwarmEmergencyType.HIGH_PRIORITY
SwarmEmergencyType.DEADLINE
SwarmEmergencyType.FAILURE
SwarmEmergencyType.SECURITY
SwarmEmergencyType.RESOURCE_SHORTAGE
SwarmEmergencyType.NETWORK_PARTITION
SwarmEmergencyType.OVERLOAD
```

---

## 使用示例

### 基本使用

```python
import asyncio
from core.collaboration.collaboration_patterns.patterns import (
    SwarmCollaborationPattern,
    SwarmDecisionType,
    SwarmRole,
)

async def main():
    # 创建Swarm模式
    swarm = SwarmCollaborationPattern(framework)
    
    # 启动协作
    session_id = await swarm.initiate_collaboration(
        task=task,
        participants=["agent_001", "agent_002", "agent_003"],
        context={"mode": "exploration"}
    )
    
    # 协调执行
    await swarm.coordinate_execution(session_id)
    
    # 获取统计信息
    stats = swarm.get_statistics(session_id)
    print(stats)

asyncio.run(main())
```

### 创建提案并投票

```python
# 创建提案
proposal_id = await swarm.create_proposal(
    session_id,
    proposer="agent_001",
    content={"action": "use_model_BGE_M3"},
    proposal_type="model_selection"
)

# 投票
await swarm.handle_vote(session_id, {
    "proposal_id": proposal_id,
    "voter": "agent_002",
    "decision": "agree",
    "weight": 1.0
})

# 获取决策结果
decision_engine = swarm.decision_engines[session_id]
result = await decision_engine.calculate_decision(proposal_id)
```

### 知识共享

```python
from core.collaboration.collaboration_patterns.patterns import SwarmKnowledgeItem

# 创建知识
knowledge = SwarmKnowledgeItem(
    key="search_result",
    value={"patents": ["CN123", "CN456"]},
    source="agent_001",
    confidence=0.95
)

# 共享知识
await swarm.share_knowledge(session_id, knowledge)
```

### 紧急响应

```python
from core.collaboration.collaboration_patterns.patterns import SwarmEmergencyType

# 启动紧急模式
await swarm.initiate_emergency_mode(
    session_id,
    SwarmEmergencyType.HIGH_PRIORITY
)

# 处理紧急情况
await swarm.handle_emergency(session_id, {"action": "resolve"})

# 退出紧急模式
await swarm.exit_emergency_mode(session_id)
```

---

## 配置选项

### 会话配置

```python
context = {
    # 运行模式
    "mode": "exploration",  # standard, exploration, analysis
    
    # 决策配置
    "decision_type": SwarmDecisionType.MAJORITY,
    "consensus_threshold": 0.7,
    
    # Gossip配置
    "gossip_interval": 10.0,  # 秒
    
    # Agent能力（可选）
    "agent_capabilities": {
        "agent_001": ["search", "analyze"],
        "agent_002": ["write", "translate"],
    }
}
```

---

## 性能指标

### 统计信息

```python
stats = swarm.get_statistics(session_id)

# 共享状态统计
print(stats["shared_state"]["total_members"])
print(stats["shared_state"]["task_success_rate"])

# 决策统计
print(stats["decision"]["total_decisions"])
print(stats["decision"]["success_rate"])

# 通信统计
print(stats["communication"]["messages_sent"])
print(stats["communication"]["messages_broadcast"])

# Gossip统计
print(stats["gossip"]["gossip_rounds"])
print(stats["gossip"]["version_vector_size"])

# 知识共享统计
print(stats["knowledge"]["local_knowledge_size"])
```

---

## 错误处理

所有异步方法在失败时返回False或None，并记录错误日志。

```python
session_id = await swarm.initiate_collaboration(...)

if session_id is None:
    # 处理启动失败
    logger.error("无法启动Swarm协作")
```

---

## 注意事项

1. **Python版本**: 需要Python 3.9+
2. **异步操作**: 所有核心方法都是异步的，需要使用await
3. **会话管理**: 使用完毕后无需显式清理，会话自动管理
4. **线程安全**: 核心组件使用线程安全的数据结构
