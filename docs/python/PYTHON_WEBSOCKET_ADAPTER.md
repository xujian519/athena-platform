# Python WebSocket Agent适配器文档

**版本**: v1.0.0
**完成日期**: 2026-04-20
**状态**: ✅ 已完成

---

## 📋 目录

- [概述](#概述)
- [架构设计](#架构设计)
- [快速开始](#快速开始)
- [API文档](#api文档)
- [使用示例](#使用示例)
- [测试指南](#测试指南)
- [故障排查](#故障排查)

---

## 概述

### 什么是Python WebSocket Agent适配器？

Python WebSocket Agent适配器是一个Python库，使Python Agent能够通过WebSocket与Athena Gateway进行实时通信。

### 核心特性

✅ **实时双向通信** - 基于WebSocket的持久连接
✅ **自动重连机制** - 连接断开时自动重连
✅ **进度推送** - 支持任务进度实时推送
✅ **消息路由** - 智能路由到对应Agent
✅ **异步支持** - 完全基于asyncio
✅ **类型安全** - 完整的类型注解

---

## 架构设计

### 模块结构

```
core/agents/websocket_adapter/
├── __init__.py              # 模块初始化
├── client.py                # WebSocket客户端
├── agent_adapter.py         # Agent适配器基类
├── xiaona_adapter.py        # 小娜Agent适配器
└── xiaonuo_adapter.py       # 小诺和云希Agent适配器
```

### 组件关系

```
WebSocketClient
      ↓
BaseAgentAdapter (抽象基类)
      ↓
├──────────┬──────────┬──────────┐
↓          ↓          ↓          ↓
Xiaona    Xiaonuo    Yunxi     自定义Agent
Agent     Agent      Agent     Adapter
```

---

## 快速开始

### 安装依赖

```bash
# 安装websockets库
pip install websockets

# 或使用poetry
poetry add websockets
```

### 基本使用

```python
import asyncio
from core.agents.websocket_adapter import create_xiaona_agent

async def main():
    # 创建并启动小娜Agent
    xiaona = await create_xiaona_agent(
        gateway_url="ws://localhost:8005/ws",
        auth_token="demo_token"
    )

    # Agent现在已连接并可以接收任务
    print(f"Agent已启动，Session ID: {xiaona.session_id}")

    # 保持运行
    await asyncio.sleep(60)

    # 停止Agent
    await xiaona.stop()

asyncio.run(main())
```

---

## API文档

### WebSocketClient

#### 初始化

```python
from core.agents.websocket_adapter import WebSocketClient

client = WebSocketClient(
    gateway_url="ws://localhost:8005/ws",
    client_id=None,  # 可选，自动生成
    auth_token="demo_token",
    auto_reconnect=True,
    reconnect_interval=3.0,
    ping_interval=30.0,
    capabilities=["task", "query", "progress"]
)
```

#### 方法

**连接**
```python
await client.connect() -> bool
```

**发送任务**
```python
task_id = await client.send_task(
    task_type="patent_analysis",
    target_agent=AgentType.XIAONA,
    parameters={
        "patent_id": "CN123456789A",
        "analysis_type": "creativity"
    },
    priority=5
)
```

**发送查询**
```python
query_id = await client.send_query(
    query_type="agent_status",
    parameters={}
)
```

**发送进度**
```python
await client.send_progress(
    progress=50,
    status="正在分析...",
    current_step="步骤2/4",
    total_steps=4
)
```

**发送响应**
```python
await client.send_response(
    success=True,
    result={"key": "value"},
    metadata={"task_type": "patent_analysis"}
)
```

**发送错误**
```python
await client.send_error(
    error_code="TASK_ERROR",
    error_msg="任务处理失败",
    details="详细错误信息"
)
```

**注册消息处理器**
```python
def handle_progress(message):
    progress = message.data.get("progress")
    print(f"进度: {progress}%")

client.register_handler(MessageType.PROGRESS, handle_progress)
```

**断开连接**
```python
await client.disconnect()
```

#### 属性

- `client_id` - 客户端ID
- `session_id` - 会话ID
- `is_connected` - 是否已连接

---

### BaseAgentAdapter

#### 初始化

```python
from core.agents.websocket_adapter import BaseAgentAdapter, AgentType

class MyAgent(BaseAgentAdapter):
    async def handle_task(self, task_type, parameters, progress_callback):
        # 处理任务
        result = {"status": "completed"}
        return result

    async def handle_query(self, query_type, parameters):
        # 处理查询
        result = {"data": "query result"}
        return result

agent = MyAgent(
    agent_type=AgentType.XIAONA,
    gateway_url="ws://localhost:8005/ws",
    auth_token="demo_token"
)
```

#### 方法

**启动Agent**
```python
await agent.start()
```

**停止Agent**
```python
await agent.stop()
```

**运行Agent（阻塞）**
```python
await agent.run()
```

**发送通知**
```python
await agent.notify(
    level="info",
    title="任务完成",
    body="专利分析已完成"
)
```

#### 抽象方法

子类必须实现以下方法：

```python
async def handle_task(
    self,
    task_type: str,
    parameters: Dict[str, Any],
    progress_callback: callable
) -> Dict[str, Any]:
    """处理任务"""
    raise NotImplementedError

async def handle_query(
    self,
    query_type: str,
    parameters: Dict[str, Any]
) -> Dict[str, Any]:
    """处理查询"""
    raise NotImplementedError
```

#### 属性

- `agent_type` - Agent类型
- `is_running` - 是否正在运行
- `is_connected` - 是否已连接
- `session_id` - 会话ID

---

### XiaonaAgentAdapter

小娜Agent适配器，专用于法律相关任务。

#### 支持的任务类型

| 任务类型 | 说明 | 参数 |
|---------|------|------|
| `patent_search` | 专利检索 | query, field, limit |
| `patent_analysis` | 专利分析 | patent_id, analysis_type |
| `creativity_assessment` | 创造性评估 | patent_id, prior_art |
| `legal_consultation` | 法律咨询 | question, context |
| `case_retrieval` | 案例检索 | keywords, case_type |

#### 使用示例

```python
from core.agents.websocket_adapter import create_xiaona_agent

xiaona = await create_xiaona_agent()

# 处理专利分析
async def progress(progress, status, step="", total=0):
    print(f"{progress}% - {status}")

result = await xiaona.handle_task(
    task_type="patent_analysis",
    parameters={
        "patent_id": "CN123456789A",
        "analysis_type": "comprehensive"
    },
    progress_callback=progress
)

print(f"创造性评分: {result['creativity']['score']}")
```

---

### XiaonuoAgentAdapter

小诺Agent适配器，专用于任务协调。

#### 支持的任务类型

| 任务类型 | 说明 |
|---------|------|
| `orchestrate_task` | 编排任务 |
| `coordinate_agents` | 协调Agent |
| `monitor_progress` | 监控进度 |
| `aggregate_results` | 汇总结果 |

---

### YunxiAgentAdapter

云希Agent适配器，专用于IP管理。

#### 支持的任务类型

| 任务类型 | 说明 |
|---------|------|
| `manage_client` | 管理客户 |
| `manage_project` | 管理项目 |
| `check_deadline` | 检查期限 |
| `generate_report` | 生成报告 |

---

## 使用示例

### 示例1: 创建自定义Agent

```python
import asyncio
from core.agents.websocket_adapter import BaseAgentAdapter, AgentType

class CustomAgent(BaseAgentAdapter):
    """自定义Agent示例"""

    def __init__(self, **kwargs):
        super().__init__(
            agent_type=AgentType.XIAONA,  # 或其他类型
            **kwargs
        )

    async def handle_task(self, task_type, parameters, progress_callback):
        """处理任务"""
        # 报告进度
        await progress_callback(0, "开始处理")

        # 执行任务
        result = await self._do_work(parameters, progress_callback)

        # 完成
        await progress_callback(100, "处理完成")
        return result

    async def handle_query(self, query_type, parameters):
        """处理查询"""
        return {
            "query_type": query_type,
            "result": "查询结果"
        }

    async def _do_work(self, parameters, progress_callback):
        """实际工作"""
        # 模拟工作
        for i in range(1, 101, 20):
            await progress_callback(i, f"处理中... {i}%")
            await asyncio.sleep(0.5)

        return {"status": "completed", "data": "结果数据"}

# 使用
async def main():
    agent = CustomAgent(
        gateway_url="ws://localhost:8005/ws",
        auth_token="demo_token"
    )

    await agent.start()
    await asyncio.sleep(30)  # 保持运行
    await agent.stop()

asyncio.run(main())
```

### 示例2: 直接使用WebSocket客户端

```python
import asyncio
from core.agents.websocket_adapter import WebSocketClient, AgentType

async def main():
    # 创建客户端
    client = WebSocketClient(
        gateway_url="ws://localhost:8005/ws",
        auth_token="demo_token"
    )

    # 连接
    await client.connect()

    # 注册消息处理器
    def handle_progress(message):
        progress = message.data.get("progress", 0)
        status = message.data.get("status", "")
        print(f"进度: {progress}% - {status}")

    client.register_handler("progress", handle_progress)

    # 发送任务
    task_id = await client.send_task(
        task_type="patent_analysis",
        target_agent=AgentType.XIAONA,
        parameters={
            "patent_id": "CN123456789A"
        }
    )

    print(f"任务已发送: {task_id}")

    # 保持连接
    await asyncio.sleep(10)

    # 断开
    await client.disconnect()

asyncio.run(main())
```

### 示例3: 多Agent协作

```python
import asyncio
from core.agents.websocket_adapter import (
    create_xiaona_agent,
    create_xiaonuo_agent
)

async def main():
    # 创建小娜和小诺
    xiaona = await create_xiaona_agent()
    xiaonuo = await create_xiaonuo_agent()

    print("✅ 两个Agent已启动")

    # 小娜处理专利分析
    result = await xiaona.handle_task(
        task_type="patent_analysis",
        parameters={"patent_id": "CN123456789A"},
        progress_callback=lambda p, s, **kw: print(f"小娜: {p}% - {s}")
    )

    # 小诺协调任务
    await xiaonuo.handle_task(
        task_type="orchestrate_task",
        parameters={"task_name": "综合分析"},
        progress_callback=lambda p, s, **kw: print(f"小诺: {p}% - {s}")
    )

    # 停止Agent
    await xiaona.stop()
    await xiaonuo.stop()

asyncio.run(main())
```

---

## 测试指南

### 运行测试

```bash
# 确保Gateway正在运行
cd /Users/xujian/Athena工作平台/gateway-unified
./bin/gateway

# 运行测试（新终端）
cd /Users/xujian/Athena工作平台
pytest tests/agents/test_websocket_adapter.py -v -s

# 或使用poetry
poetry run pytest tests/agents/test_websocket_adapter.py -v -s
```

### 测试覆盖

- ✅ WebSocket客户端连接
- ✅ 消息发送和接收
- ✅ Agent启动和停止
- ✅ 任务处理
- ✅ 查询处理
- ✅ 进度推送
- ✅ 错误处理

---

## 故障排查

### 问题1: 连接失败

**症状**: 无法连接到Gateway

**解决方案**:
1. 确保Gateway正在运行
2. 检查URL是否正确: `ws://localhost:8005/ws`
3. 检查防火墙设置
4. 查看Gateway日志

### 问题2: Agent未收到任务

**症状**: Agent已启动但未收到任务消息

**解决方案**:
1. 确认Agent已成功握手（检查session_id）
2. 确认目标Agent类型正确
3. 查看Agent日志
4. 使用浏览器测试客户端验证Gateway正常工作

### 问题3: 进度推送不工作

**症状**: 进度更新未显示

**解决方案**:
1. 确认progress_callback被正确调用
2. 检查消息处理器是否已注册
3. 查看Gateway和Agent日志

---

## 性能优化

### 异步处理

使用`asyncio.create_task`在后台处理任务：

```python
async def handle_task(self, task_type, parameters, progress_callback):
    # 在后台任务中处理
    task = asyncio.create_task(self._process_task(parameters, progress_callback))

    # 立即返回
    return {"task_id": "pending", "status": "started"}
```

### 批量操作

批量发送多个消息：

```python
async def send_batch_tasks(client, tasks):
    """批量发送任务"""
    for task in tasks:
        await client.send_task(**task)

    await asyncio.sleep(0.1)  # 给服务器一些处理时间
```

---

## 最佳实践

1. **使用上下文管理器**
```python
async with agent:
    await agent.start()
    # Agent会在退出时自动停止
```

2. **优雅关闭**
```python
try:
    await agent.run()
except KeyboardInterrupt:
    logger.info("收到中断信号")
    await agent.stop()
```

3. **错误处理**
```python
try:
    result = await agent.handle_task(...)
except Exception as e:
    logger.error(f"任务失败: {e}")
    await agent.notify("error", "任务失败", str(e))
```

4. **日志记录**
```python
logger = logging.getLogger(__name__)
logger.info(f"Agent {self.agent_type} 已启动")
```

---

## 维护者

**开发团队**: Athena平台团队
**技术负责人**: 徐健 (xujian519@gmail.com)
**完成日期**: 2026-04-20

---

**状态**: ✅ Python WebSocket Agent适配器已完成，可以与Gateway进行端到端通信！
