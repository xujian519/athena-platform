# Athena Gateway WebSocket Hub 实施文档

> 实施日期: 2026-04-21
> 状态: ✅ 完成

## 概述

WebSocket Hub是Athena Gateway的新增控制平面组件，用于实时任务控制、进度更新和用户交互。它与现有的WebSocket Controller并行工作，提供更灵活的消息路由和会话管理。

## 架构设计

### 组件关系

```
┌─────────────────────────────────────────────────────────┐
│              Athena Gateway (Go)                        │
│                                                          │
│  ┌────────────────────┐  ┌────────────────────┐        │
│  │ WebSocket Controller│  │   WebSocket Hub    │        │
│  │  (现有实现)        │  │   (新增)           │        │
│  │                    │  │                    │        │
│  │  - Agent路由       │  │  - 会话管理        │        │
│  │  - 消息处理        │  │  - 消息广播        │        │
│  │  - Canvas Host     │  │  - 任务控制        │        │
│  └────────────────────┘  └────────────────────┘        │
│           │                        │                    │
│           └────────────┬───────────┘                    │
│                        │                                │
│                  ┌─────▼─────┐                          │
│                  │ HTTP Router│                          │
│                  └─────┬─────┘                          │
└────────────────────────┼────────────────────────────────┘
                       │
         ┌─────────────┼─────────────┐
         │             │             │
    /ws (Controller) /ws/hub (Hub)  /api/*
```

### 消息类型

| 消息类型 | 方向 | 说明 |
|---------|-----|------|
| `task_create` | C→S | 创建新任务 |
| `task_start` | C→S | 开始任务 |
| `task_pause` | C→S | 暂停任务 |
| `task_resume` | C→S | 恢复任务 |
| `task_cancel` | C→S | 取消任务 |
| `task_progress` | S→C | 任务进度更新 |
| `task_complete` | S→C | 任务完成通知 |
| `task_error` | S→C | 任务错误通知 |
| `user_confirm_request` | S→C | 请求用户确认 |
| `user_confirm_response` | C→S | 用户确认响应 |
| `user_interrupt` | C→S | 用户中断请求 |
| `agent_message` | S→C | 智能体消息 |
| `agent_collaboration` | S→C | 智能体协作消息 |

## 实施详情

### 1. 核心文件

#### `internal/websocket/types.go`
定义所有WebSocket消息类型和载荷结构：

```go
// 消息类型
type MessageType string

// 基础消息结构
type WSMessage struct {
    Type      string      `json:"type"`
    SessionID string      `json:"session_id"`
    Timestamp string      `json:"timestamp"`
    Payload   interface{} `json:"payload"`
}

// 各种载荷类型
type TaskCreatePayload struct { ... }
type TaskProgressPayload struct { ... }
// ... 其他载荷类型
```

#### `internal/websocket/hub_handler.go`
实现Hub模式的WebSocket处理器：

```go
type Hub struct {
    clients    map[string]*Client
    register   chan *Client
    unregister chan *Client
    broadcast  chan WSMessage
    mu         sync.RWMutex
}

// 核心方法
func (h *Hub) Run()
func (h *Hub) HandleWebSocket(w http.ResponseWriter, r *http.Request)
func (h *Hub) BroadcastToSession(sessionID string, message WSMessage)
func (h *Hub) readPump(client *Client)
func (h *Hub) writePump(client *Client)
```

### 2. 集成点

#### `cmd/gateway/main.go`
```go
// 创建WebSocket Hub
wsHub := websocket.NewHub()
go wsHub.Run()

// 设置路由（传入Hub）
router.SetupRoutes(gw.GetRouter(), cfg, wsController, wsHub)
```

#### `internal/router/router.go`
```go
func SetupRoutes(router *gin.Engine, cfg *config.Config,
                 wsController *websocket.Controller,
                 wsHub *websocket.Hub) error {
    // Hub路由
    router.GET("/ws/hub", wsHub.HandleWebSocket)

    // Hub统计API
    hubGroup.GET("/stats", ...)
}
```

## 使用指南

### 客户端连接

#### JavaScript示例
```javascript
const sessionId = 'session_123';
const ws = new WebSocket(`ws://localhost:8005/ws/hub?session_id=${sessionId}`);

ws.onmessage = (event) => {
    const message = JSON.parse(event.data);
    console.log('收到消息:', message.type, message.payload);
};

// 发送任务创建
ws.send(JSON.stringify({
    type: 'task_create',
    session_id: sessionId,
    timestamp: new Date().toISOString(),
    payload: {
        task_id: 'task_001',
        task_type: 'patent_search',
        user_input: '检索自动驾驶专利',
        priority: 'medium'
    }
}));
```

#### Python示例
```python
import asyncio
import websockets
import json

async def test_websocket():
    uri = "ws://localhost:8005/ws/hub?session_id=test_session"
    async with websockets.connect(uri) as websocket:
        # 发送任务创建
        message = {
            "type": "task_create",
            "session_id": "test_session",
            "timestamp": "2026-04-21T10:00:00Z",
            "payload": {
                "task_id": "task_001",
                "task_type": "patent_search",
                "user_input": "检索自动驾驶专利",
                "priority": "medium"
            }
        }
        await websocket.send(json.dumps(message))

        # 接收响应
        response = await websocket.recv()
        print(f"收到: {response}")

asyncio.run(test_websocket())
```

### API端点

#### 1. WebSocket连接
```
GET /ws/hub?session_id={session_id}
```

#### 2. Hub统计信息
```
GET /api/hub/stats

响应:
{
  "success": true,
  "data": {
    "session_count": 5,
    "connected_sessions": ["session_1", "session_2", ...]
  }
}
```

## 测试方法

### 1. 使用HTML测试页面

```bash
# 在浏览器中打开
open gateway-unified/test_websocket_hub.html
```

### 2. 使用wscat命令行工具

```bash
# 安装wscat
npm install -g wscat

# 连接WebSocket
wscat -c "ws://localhost:8005/ws/hub?session_id=test123"

# 发送消息
{"type":"task_create","session_id":"test123","timestamp":"2026-04-21T10:00:00Z","payload":{"task_id":"task_001","task_type":"patent_search","user_input":"检索自动驾驶专利","priority":"medium"}}
```

### 3. 使用测试脚本

```bash
cd gateway-unified
./test_websocket_hub.sh
```

### 4. 查看Hub统计

```bash
curl http://localhost:8005/api/hub/stats | python3 -m json.tool
```

## 性能特性

### 并发安全
- 使用`sync.RWMutex`保护clients map
- 使用缓冲channel（256）避免阻塞
- goroutine安全的读写分离

### 资源管理
- 心跳检测（30秒）
- 读超时（60秒）
- 写超时（10秒）
- 优雅关闭处理

### 扩展性
- 支持多会话并发
- 消息广播到指定会话
- 可扩展的消息处理器

## 与现有Controller的对比

| 特性 | WebSocket Controller | WebSocket Hub |
|-----|---------------------|---------------|
| 用途 | Agent通信 | 任务控制 |
| 路由 | 消息路由器 | 会话管理器 |
| 协议 | 自定义协议 | 统一消息格式 |
| 状态管理 | 会话管理器 | Hub clients |
| 适用场景 | 智能体协作 | 用户交互、进度更新 |

## 待实现功能

### Phase 2: 任务管理集成
- [ ] 集成任务管理器
- [ ] 实现任务状态持久化
- [ ] 添加任务队列管理
- [ ] 实现任务优先级调度

### Phase 3: 高级功能
- [ ] 用户确认对话框
- [ ] 任务进度可视化
- [ ] 多任务并发控制
- [ ] 任务超时处理

### Phase 4: 监控和诊断
- [ ] Prometheus指标集成
- [ ] WebSocket消息追踪
- [ ] 性能监控面板
- [ ] 错误率统计

## 故障排查

### 常见问题

**1. WebSocket连接失败**
```bash
# 检查Gateway是否运行
curl http://localhost:8005/health

# 检查端口占用
lsof -i :8005
```

**2. 消息发送无响应**
- 检查消息格式是否正确
- 查看Gateway日志
- 验证session_id是否有效

**3. 会话断开**
- 检查心跳超时设置
- 验证网络连接稳定性
- 查看客户端重连逻辑

## 维护指南

### 日志位置
```bash
# Gateway日志
tail -f /usr/local/athena-gateway/logs/gateway.log

# 系统日志（如果使用systemd）
sudo journalctl -u athena-gateway -f
```

### 重启服务
```bash
# macOS
sudo /usr/local/athena-gateway/restart.sh

# Linux
sudo systemctl restart athena-gateway
```

### 配置文件
```bash
# Gateway配置
vim /usr/local/athena-gateway/config.yaml

# 路由配置
vim gateway-unified/config/routes.yaml
```

## 总结

WebSocket Hub为Athena Gateway提供了强大的实时控制能力，使得：

1. ✅ 用户可以实时控制任务执行
2. ✅ 智能体可以推送进度更新
3. ✅ 系统可以请求用户确认
4. ✅ 支持多会话并发管理

下一步工作：
- 集成Python Agent系统
- 实现任务管理器
- 添加用户界面组件

---

**实施者**: Claude Code (Sonnet 4.6)
**审查状态**: 待审查
**文档版本**: 1.0
