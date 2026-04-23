# Python WebSocket Agent适配器

Athena Gateway的Python Agent WebSocket通信库。

## 快速开始

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
    print(f"✅ Agent已启动，Session ID: {xiaona.session_id}")

    # 保持运行
    await asyncio.sleep(60)

    # 停止Agent
    await xiaona.stop()

asyncio.run(main())
```

## 特性

✅ **实时双向通信** - 基于WebSocket的持久连接
✅ **自动重连机制** - 连接断开时自动重连
✅ **进度推送** - 支持任务进度实时推送
✅ **消息路由** - 智能路由到对应Agent
✅ **异步支持** - 完全基于asyncio
✅ **类型安全** - 完整的类型注解

## 组件

### WebSocketClient

低级WebSocket客户端，用于直接与Gateway通信。

### BaseAgentAdapter

Agent适配器基类，提供统一的Agent接口。

### 内置Agent适配器

- **XiaonaAgentAdapter** - 法律专家Agent
- **XiaonuoAgentAdapter** - 调度官Agent
- **YunxiAgentAdapter** - IP管理Agent

## 文档

完整文档请参考: [docs/python/PYTHON_WEBSOCKET_ADAPTER.md](../../../docs/python/PYTHON_WEBSOCKET_ADAPTER.md)

## 示例

查看示例代码: [examples/websocket_agent_example.py](../../../examples/websocket_agent_example.py)

## 测试

```bash
# 确保Gateway正在运行
cd /Users/xujian/Athena工作平台/gateway-unified
./bin/gateway

# 运行测试
pytest tests/agents/test_websocket_adapter.py -v -s
```

## 依赖

- Python 3.9+
- websockets>=10.0

## 安装

```bash
pip install websockets
```

## 维护者

Athena平台团队
