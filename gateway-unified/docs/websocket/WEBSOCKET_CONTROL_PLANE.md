# WebSocket控制平面实现文档

**版本**: v1.0.0
**完成日期**: 2026-04-20
**状态**: ✅ 已完成

---

## 📋 目录

- [概述](#概述)
- [架构设计](#架构设计)
- [核心组件](#核心组件)
- [消息协议](#消息协议)
- [部署指南](#部署指南)
- [测试指南](#测试指南)
- [API文档](#api文档)
- [故障排查](#故障排查)

---

## 概述

### 什么是WebSocket控制平面？

WebSocket控制平面是Athena Gateway的实时双向通信层，负责：

- **会话管理**: 管理所有WebSocket连接和会话状态
- **消息路由**: 将消息路由到正确的Agent（小娜、小诺、云熙）
- **Canvas Host**: 渲染实时UI界面
- **进度推送**: 主动推送任务进度和结果

### 核心特性

✅ **实时双向通信** - WebSocket持久连接
✅ **会话管理** - 自动管理连接生命周期
✅ **智能路由** - 基于消息类型的自动路由
✅ **Canvas Host** - 内置UI渲染引擎
✅ **心跳机制** - 自动保持连接活跃
✅ **优雅关闭** - 分阶段关闭，保证资源清理

---

## 架构设计

### 系统架构

```
┌─────────────────────────────────────────────────────────┐
│              Athena Gateway (Port 8005)                  │
│  ┌──────────────────────────────────────────────────┐  │
│  │   WebSocket控制平面 (ws://localhost:8005/ws)     │  │
│  │                                                   │  │
│  │   ┌────────────────────────────────────────┐     │  │
│  │   │  Controller (控制器)                   │     │  │
│  │   │  - WebSocket Upgrader                 │     │  │
│  │   │  - 消息循环                            │     │  │
│  │   └────────────────────────────────────────┘     │  │
│  │                                                   │  │
│  │   ┌──────────┐  ┌──────────┐  ┌──────────────┐  │  │
│  │   │Session   │  │ Router   │  │Canvas Host   │  │  │
│  │   │Manager   │  │          │  │              │  │  │
│  │   │          │  │          │  │              │  │  │
│  │   └──────────┘  └──────────┘  └──────────────┘  │  │
│  └──────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────┘
         │         │         │
    ┌────┴────┐ ┌──┴────┐ ┌┴──────┐
    │小娜代理  │ │小诺代理 │ │云熙代理 │
    │(Legal)  │ │(Coord) │ │ (IP)   │
    └─────────┘ └───────┘ └───────┘
```

### 目录结构

```
gateway-unified/internal/websocket/
├── protocol/
│   └── message.go          # 消息协议定义
├── session/
│   └── manager.go          # 会话管理器
├── router/
│   └── router.go           # 消息路由器
├── canvas/
│   └── host.go             # Canvas Host服务
└── websocket.go            # WebSocket控制器
```

---

## 核心组件

### 1. Controller (控制器)

**位置**: `internal/websocket/websocket.go`

**职责**:
- 接受WebSocket连接请求
- 升级HTTP到WebSocket
- 管理消息循环

**核心方法**:
```go
// HandleWebSocket WebSocket连接处理器
func (c *Controller) HandleWebSocket(ginCtx *gin.Context)

// BroadcastToAll 向所有会话广播消息
func (c *Controller) BroadcastToAll(message *protocol.Message) error

// SendToSession 向指定会话发送消息
func (c *Controller) SendToSession(sessionID string, message *protocol.Message) error
```

### 2. Session Manager (会话管理器)

**位置**: `internal/websocket/session/manager.go`

**职责**:
- 管理所有WebSocket会话
- 处理会话超时
- 维护会话状态

**核心功能**:
```go
// CreateSession 创建新会话
func (m *Manager) CreateSession(conn *websocket.Conn, clientID, userAgent, remoteAddr string) (*Session, error)

// GetSession 获取会话
func (m *Manager) GetSession(sessionID string) (*Session, bool)

// RemoveSession 移除会话
func (m *Manager) RemoveSession(sessionID string)
```

### 3. Message Router (消息路由器)

**位置**: `internal/websocket/router/router.go`

**职责**:
- 根据消息类型路由到对应处理器
- 注册Agent处理器
- 处理握手、任务、查询等消息

**核心功能**:
```go
// Route 路由消息
func (r *Router) Route(msg *protocol.Message, sess *session.Session) error

// RegisterHandler 注册消息处理器
func (r *Router) RegisterHandler(msgType protocol.MessageType, handler HandlerFunc)

// RegisterAgentHandler 注册Agent处理器
func (r *Router) RegisterAgentHandler(agentType protocol.AgentType, handler HandlerFunc)
```

### 4. Canvas Host (画布主机)

**位置**: `internal/websocket/canvas/host.go`

**职责**:
- 渲染HTML/CSS/JS界面
- 管理Canvas实例
- 提供默认UI模板

**核心功能**:
```go
// CreateCanvas 创建新Canvas
func (ch *CanvasHost) CreateCanvas(sessionID, title string) *Canvas

// Render 渲染Canvas为HTML
func (ch *CanvasHost) Render(canvasID string) (string, error)

// UpdateCanvas 更新Canvas
func (ch *CanvasHost) UpdateCanvas(canvasID string, updates map[string]interface{}) error
```

---

## 消息协议

### 消息类型

| 类型 | 说明 | 方向 |
|-----|------|------|
| `handshake` | 握手 | 客户端→服务器 |
| `task` | 任务请求 | 客户端→服务器 |
| `query` | 查询请求 | 客户端→服务器 |
| `cancel` | 取消请求 | 客户端→服务器 |
| `response` | 响应 | 服务器→客户端 |
| `progress` | 进度更新 | 服务器→客户端 |
| `error` | 错误消息 | 服务器→客户端 |
| `notify` | 通知消息 | 服务器→客户端 |
| `ping` | 心跳 | 双向 |
| `pong` | 心跳响应 | 双向 |

### 消息格式

```json
{
  "id": "msg_1234567890_abc123",
  "type": "task",
  "timestamp": 1713576000000000000,
  "session_id": "session-uuid",
  "data": {
    "task_type": "patent_analysis",
    "target_agent": "xiaona",
    "priority": 5,
    "parameters": {
      "query": "分析专利CN123456789A"
    }
  }
}
```

### 握手流程

```
1. 客户端连接
   ↓
2. 发送握手消息
   {
     "type": "handshake",
     "data": {
       "client_id": "client_xxx",
       "auth_token": "token_xxx"
     }
   }
   ↓
3. 服务器响应
   {
     "type": "handshake",
     "session_id": "session-uuid"
   }
   ↓
4. 握手成功，可以发送消息
```

---

## 部署指南

### 1. 编译Gateway

```bash
cd /Users/xujian/Athena工作平台/gateway-unified
go build -o bin/gateway ./cmd/gateway
```

### 2. 配置文件

编辑 `config.yaml`:

```yaml
websocket:
  enabled: true
  path: /ws
  read_buffer_size: 1024
  write_buffer_size: 1024
  heartbeat_interval: 30
  session_timeout: 600
  enable_canvas_host: true
```

### 3. 启动Gateway

```bash
# 方式1: 直接运行
./bin/gateway

# 方式2: 使用配置文件
./bin/gateway -config config.yaml

# 方式3: 后台运行
nohup ./bin/gateway > gateway.log 2>&1 &
```

### 4. 验证部署

```bash
# 检查健康状态
curl http://localhost:8005/health

# 检查WebSocket统计
curl http://localhost:8005/api/websocket/stats

# 查看日志
tail -f gateway.log
```

---

## 测试指南

### 1. 运行自动化测试

```bash
cd /Users/xujian/Athena工作平台/gateway-unified
./tests/test_websocket.sh
```

**测试覆盖**:
- ✅ Gateway启动
- ✅ 健康检查
- ✅ WebSocket端点
- ✅ 统计API
- ✅ Canvas Host服务

### 2. 手动测试（浏览器）

1. 启动Gateway:
```bash
./bin/gateway
```

2. 打开测试页面:
```
http://localhost:8005/tests/websocket_test_client.html
```

3. 测试流程:
   - 点击"连接"按钮
   - 等待连接成功
   - 选择消息类型
   - 点击"发送消息"
   - 查看消息日志

### 3. Python客户端测试

```python
import asyncio
import websockets
import json

async def test_websocket():
    uri = "ws://localhost:8005/ws?client_id=test_client"

    async with websockets.connect(uri) as websocket:
        # 发送握手消息
        handshake = {
            "id": "msg_001",
            "type": "handshake",
            "timestamp": int(asyncio.get_event_loop().time() * 1000000000),
            "session_id": None,
            "data": {
                "client_id": "test_client",
                "auth_token": "demo_token",
                "capabilities": ["task", "query"],
                "user_agent": "Python/3.11"
            }
        }

        await websocket.send(json.dumps(handshake))

        # 接收响应
        response = await websocket.recv()
        print(f"收到响应: {response}")

        # 发送任务
        task = {
            "id": "msg_002",
            "type": "task",
            "timestamp": int(asyncio.get_event_loop().time() * 1000000000),
            "session_id": json.loads(response)["session_id"],
            "data": {
                "task_type": "patent_analysis",
                "target_agent": "xiaona",
                "priority": 5,
                "parameters": {"query": "测试"}
            }
        }

        await websocket.send(json.dumps(task))
        response = await websocket.recv()
        print(f"收到响应: {response}")

asyncio.run(test_websocket())
```

---

## API文档

### WebSocket端点

**URL**: `ws://localhost:8005/ws`

**参数**:
- `client_id` (可选): 客户端ID

**示例**:
```javascript
const ws = new WebSocket('ws://localhost:8005/ws?client_id=my_client');
```

### HTTP API

#### 1. 获取WebSocket统计

**URL**: `GET /api/websocket/stats`

**响应**:
```json
{
  "success": true,
  "data": {
    "session_count": 5,
    "active_sessions": [...]
  }
}
```

---

## 故障排查

### 问题1: WebSocket连接失败

**症状**: 客户端无法连接到WebSocket端点

**排查步骤**:
1. 检查Gateway是否运行:
```bash
curl http://localhost:8005/health
```

2. 检查端口是否被占用:
```bash
lsof -i :8005
```

3. 查看Gateway日志:
```bash
tail -f /tmp/gateway.log
```

### 问题2: 会话超时

**症状**: WebSocket连接频繁断开

**解决方案**:
1. 增加 `session_timeout` 配置
2. 实现客户端心跳重连机制
3. 检查网络稳定性

### 问题3: 消息路由失败

**症状**: 消息发送后没有响应

**排查步骤**:
1. 检查消息格式是否正确
2. 确认 `session_id` 是否有效
3. 查看Gateway日志中的错误信息

---

## 性能指标

| 指标 | 目标值 | 当前值 |
|-----|-------|--------|
| 并发连接数 | 10,000+ | 待测试 |
| 消息延迟 | <50ms | 待测试 |
| 吞吐量 | 100,000 msg/s | 待测试 |
| 内存占用 | <500MB | 待测试 |
| 连接稳定性 | 99.9% | 待测试 |

---

## 下一步计划

### Phase 2: Python Agent适配器

- [ ] 实现Python WebSocket客户端
- [ ] 创建Agent通信协议
- [ ] 实现消息序列化/反序列化

### Phase 3: 生产部署

- [ ] 添加TLS支持
- [ ] 实现负载均衡
- [ ] 配置Prometheus监控
- [ ] 编写部署文档

---

## 维护者

**开发团队**: Athena平台团队
**技术负责人**: 徐健 (xujian519@gmail.com)
**文档更新**: 2026-04-20

---

**状态**: ✅ WebSocket控制平面核心实现已完成
