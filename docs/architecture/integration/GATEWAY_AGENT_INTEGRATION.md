# Gateway与智能体集成方案

> **版本**: 1.0
> **创建日期**: 2026-04-21
> **状态**: 设计阶段

---

## 📋 设计目标

基于Gateway现有能力（端口8005，Go实现），设计智能体与Gateway的集成方案。

**核心目标**：
1. ✅ **统一入口**：所有请求通过Gateway（端口8005）
2. ✅ **控制平面分离**：WebSocket实时控制
3. ✅ **高性能数据传输**：gRPC高性能通信
4. ✅ **会话管理**：统一会话生命周期
5. ✅ **智能路由**：自动路由到合适的智能体

---

## 🏗️ 集成架构

```
┌─────────────────────────────────────────────────────────┐
│              Gateway (Go, Port 8005)                     │
├─────────────────────────────────────────────────────────┤
│                                                           │
│  ┌──────────────────────────────────────────────────┐   │
│  │  控制平面 (WebSocket)                             │   │
│  │  - 小诺调度                                       │   │
│  │  - 任务分配                                       │   │
│  │  - 进度更新                                       │   │
│  │  - 用户交互                                       │   │
│  └──────────────────────────────────────────────────┘   │
│                        ↕                                 │
│  ┌──────────────────────────────────────────────────┐   │
│  │  消息路由 (Router)                                │   │
│  │  - 意图识别                                       │   │
│  │  - 智能体选择                                     │   │
│  │  - 负载均衡                                       │   │
│  └──────────────────────────────────────────────────┘   │
│                        ↕                                 │
│  ┌──────────────────────────────────────────────────┐   │
│  │  数据平面 (gRPC)                                  │   │
│  │  - 高性能数据传输                                 │   │
│  │  - 流式响应                                       │   │
│  │  - 二进制协议                                     │   │
│  └──────────────────────────────────────────────────┘   │
│                                                           │
└─────────────────────────────────────────────────────────┘
         │ gRPC                    │ gRPC
         ↓                         ↓
┌────────────────┐       ┌────────────────┐
│  小娜代理       │       │  小诺代理       │
│  (Python)      │       │  (Python)      │
│  Port 8006     │       │  Port 8007     │
└────────────────┘       └────────────────┘
```

---

## 1️⃣ 通信协议设计

### 1.1 协议选择

| 场景 | 协议 | 端口 | 原因 |
|------|------|------|------|
| **实时控制** | WebSocket | 8005 | 双向通信、实时性强 |
| **高性能数据传输** | gRPC | 8005+ | 二进制协议、性能高 |
| **REST API** | HTTP/REST | 8005 | 简单兼容、调试方便 |

### 1.2 WebSocket控制平面

**用途**：
- 小诺任务调度
- 进度实时更新
- 用户交互（确认、打断）
- 智能体协作消息

**协议设计**：

```typescript
// WebSocket消息协议

interface WSMessage {
  type: MessageType;
  session_id: string;
  timestamp: string;
  payload: any;
}

enum MessageType {
  // 控制消息
  TASK_CREATE = "task_create",           // 创建任务
  TASK_START = "task_start",             // 开始任务
  TASK_PAUSE = "task_pause",             // 暂停任务
  TASK_RESUME = "task_resume",           // 恢复任务
  TASK_CANCEL = "task_cancel",           // 取消任务

  // 状态消息
  TASK_PROGRESS = "task_progress",       // 任务进度
  TASK_COMPLETE = "task_complete",       // 任务完成
  TASK_ERROR = "task_error",             // 任务错误

  // 用户交互
  USER_CONFIRM_REQUEST = "user_confirm_request",  // 请求确认
  USER_CONFIRM_RESPONSE = "user_confirm_response",// 确认响应
  USER_INTERRUPT = "user_interrupt",     // 用户打断

  // 智能体消息
  AGENT_MESSAGE = "agent_message",       // 智能体消息
  AGENT_COLLABORATION = "agent_collaboration"  // 智能体协作
}

// 任务创建消息
interface TaskCreateMessage extends WSMessage {
  type: MessageType.TASK_CREATE;
  payload: {
    task_id: string;
    task_type: string;  // "patent_search", "technical_analysis", etc.
    user_input: string;
    project_path?: string;
    priority?: "low" | "medium" | "high";
  };
}

// 任务进度消息
interface TaskProgressMessage extends WSMessage {
  type: MessageType.TASK_PROGRESS;
  payload: {
    task_id: string;
    agent_name: string;
    progress: number;  // 0-100
    message: string;
    details?: any;
  };
}

// 用户确认请求
interface UserConfirmRequestMessage extends WSMessage {
  type: MessageType.USER_CONFIRM_REQUEST;
  payload: {
    task_id: string;
    title: string;
    description: string;
    plan: Step[];
    timeout_seconds?: number;
  };
}

interface Step {
  step_id: string;
  agent: string;
  description: string;
  estimated_time_minutes: number;
}

// 用户确认响应
interface UserConfirmResponseMessage extends WSMessage {
  type: MessageType.USER_CONFIRM_RESPONSE;
  payload: {
    task_id: string;
    approved: boolean;
    feedback?: string;
  };
}
```

**Go实现示例**：

```go
// gateway-unified/internal/websocket/agent_control_handler.go
package websocket

import (
    "encoding/json"
    "log"
    "net/http"
    "sync"

    "github.com/gorilla/websocket"
)

type AgentControlHandler struct {
    upgrader websocket.Upgrader
    clients  map[string]*WSClient
    mu       sync.RWMutex
}

type WSClient struct {
    SessionID string
    Conn      *websocket.Conn
    Send      chan WSMessage
}

type WSMessage struct {
    Type      string      `json:"type"`
    SessionID string      `json:"session_id"`
    Timestamp string      `json:"timestamp"`
    Payload   interface{} `json:"payload"`
}

func NewAgentControlHandler() *AgentControlHandler {
    return &AgentControlHandler{
        upgrader: websocket.Upgrader{
            ReadBufferSize:  1024,
            WriteBufferSize: 1024,
            CheckOrigin: func(r *http.Request) bool {
                return true // 生产环境需要验证Origin
            },
        },
        clients: make(map[string]*WSClient),
    }
}

func (h *AgentControlHandler) HandleWebSocket(w http.ResponseWriter, r *http.Request) {
    // 升级到WebSocket
    conn, err := h.upgrader.Upgrade(w, r, nil)
    if err != nil {
        log.Printf("WebSocket upgrade error: %v", err)
        return
    }

    // 获取session_id
    sessionID := r.URL.Query().Get("session_id")
    if sessionID == "" {
        sessionID = generateSessionID()
    }

    // 创建客户端
    client := &WSClient{
        SessionID: sessionID,
        Conn:      conn,
        Send:      make(chan WSMessage, 256),
    }

    // 注册客户端
    h.mu.Lock()
    h.clients[sessionID] = client
    h.mu.Unlock()

    // 启动读写goroutine
    go h.readPump(client)
    go h.writePump(client)
}

func (h *AgentControlHandler) readPump(client *WSClient) {
    defer func() {
        client.Conn.Close()
        close(client.Send)
    }()

    for {
        _, message, err := client.Conn.ReadMessage()
        if err != nil {
            break
        }

        // 解析消息
        var wsMsg WSMessage
        if err := json.Unmarshal(message, &wsMsg); err != nil {
            log.Printf("JSON parse error: %v", err)
            continue
        }

        // 处理消息
        h.handleMessage(client, wsMsg)
    }
}

func (h *AgentControlHandler) writePump(client *WSClient) {
    defer client.Conn.Close()

    for message := range client.Send {
        data, err := json.Marshal(message)
        if err != nil {
            log.Printf("JSON marshal error: %v", err)
            continue
        }

        err = client.Conn.WriteMessage(websocket.TextMessage, data)
        if err != nil {
            break
        }
    }
}

func (h *AgentControlHandler) handleMessage(client *WSClient, msg WSMessage) {
    switch msg.Type {
    case "task_create":
        h.handleTaskCreate(client, msg)
    case "user_confirm_response":
        h.handleUserConfirmResponse(client, msg)
    case "user_interrupt":
        h.handleUserInterrupt(client, msg)
    default:
        log.Printf("Unknown message type: %s", msg.Type)
    }
}

func (h *AgentControlHandler) BroadcastToSession(sessionID string, msg WSMessage) {
    h.mu.RLock()
    client, exists := h.clients[sessionID]
    h.mu.RUnlock()

    if exists {
        client.Send <- msg
    }
}
```

### 1.3 gRPC数据平面

**用途**：
- 智能体执行
- 大数据传输
- 流式响应

**Protocol定义**：

```protobuf
// gateway-unified/proto/agent_service.proto
syntax = "proto3";

package athena.agent.v1;

service AgentService {
  // 执行任务
  rpc ExecuteTask(TaskRequest) returns (stream TaskResponse);

  // 获取智能体状态
  rpc GetAgentStatus(AgentStatusRequest) returns (AgentStatusResponse);

  // 心跳
  rpc Heartbeat(HeartbeatRequest) returns (HeartbeatResponse);
}

message TaskRequest {
  string task_id = 1;
  string agent_type = 2;  // "xiaona", "xiaonuo", "retriever", etc.
  string scenario = 3;    // "patent_search", "technical_analysis", etc.
  string user_input = 4;
  map<string, string> context = 5;  // 上下文信息
  string project_path = 6;
}

message TaskResponse {
  string task_id = 1;
  string agent_type = 2;
  ResponseType type = 3;
  oneof payload {
    ProgressUpdate progress = 4;
    string partial_result = 5;
    string final_result = 6;
    Error error = 7;
  }
}

enum ResponseType {
  PROGRESS = 0;
  PARTIAL = 1;
  FINAL = 2;
  ERROR = 3;
}

message ProgressUpdate {
  int32 percentage = 1;
  string message = 2;
  map<string, string> details = 3;
}

message Error {
  string code = 1;
  string message = 2;
  string details = 3;
}

message AgentStatusRequest {
  string agent_type = 1;
}

message AgentStatusResponse {
  string agent_type = 1;
  bool is_healthy = 2;
  int32 current_tasks = 3;
  int64 total_completed = 4;
  double cpu_usage = 5;
  double memory_usage = 6;
}

message HeartbeatRequest {
  string agent_type = 1;
  int64 timestamp = 2;
}

message HeartbeatResponse {
  string status = 1;
  int64 timestamp = 2;
}
```

**Python gRPC客户端**：

```python
# core/orchestration/grpc_agent_client.py
import grpc
from proto import agent_service_pb2, agent_service_pb2_grpc
from typing import AsyncIterator, Dict, Any


class GrpcAgentClient:
    """gRPC智能体客户端"""

    def __init__(self, gateway_address: str = "localhost:8005"):
        self.channel = grpc.insecure_channel(gateway_address)
        self.stub = agent_service_pb2_grpc.AgentServiceStub(self.channel)

    async def execute_task(
        self,
        task_id: str,
        agent_type: str,
        scenario: str,
        user_input: str,
        context: Dict[str, str],
        project_path: str
    ) -> AsyncIterator[Dict[str, Any]]:
        """
        执行任务（流式响应）

        Args:
            task_id: 任务ID
            agent_type: 智能体类型
            scenario: 场景
            user_input: 用户输入
            context: 上下文
            project_path: 项目路径

        Yields:
            任务响应（进度/部分结果/最终结果）
        """
        request = agent_service_pb2.TaskRequest(
            task_id=task_id,
            agent_type=agent_type,
            scenario=scenario,
            user_input=user_input,
            context=context,
            project_path=project_path
        )

        try:
            for response in self.stub.ExecuteTask(request):
                yield self._parse_response(response)
        except grpc.RpcError as e:
            yield {
                "type": "error",
                "error": {
                    "code": e.code(),
                    "message": e.details()
                }
            }

    def _parse_response(self, response: agent_service_pb2.TaskResponse) -> Dict[str, Any]:
        """解析响应"""
        result = {
            "task_id": response.task_id,
            "agent_type": response.agent_type,
            "type": response.Type.name.lower()
        }

        if response.type == agent_service_pb2.PROGRESS:
            result["progress"] = {
                "percentage": response.progress.percentage,
                "message": response.progress.message,
                "details": dict(response.progress.details)
            }
        elif response.type == agent_service_pb2.PARTIAL:
            result["partial_result"] = response.partial_result
        elif response.type == agent_service_pb2.FINAL:
            result["final_result"] = response.final_result
        elif response.type == agent_service_pb2.ERROR:
            result["error"] = {
                "code": response.error.code,
                "message": response.error.message,
                "details": response.error.details
            }

        return result

    async def get_agent_status(self, agent_type: str) -> Dict[str, Any]:
        """获取智能体状态"""
        request = agent_service_pb2.AgentStatusRequest(agent_type=agent_type)
        response = self.stub.GetAgentStatus(request)

        return {
            "agent_type": response.agent_type,
            "is_healthy": response.is_healthy,
            "current_tasks": response.current_tasks,
            "total_completed": response.total_completed,
            "cpu_usage": response.cpu_usage,
            "memory_usage": response.memory_usage
        }

    def close(self):
        """关闭连接"""
        self.channel.close()
```

---

## 2️⃣ 智能路由设计

### 2.1 意图识别

```go
// gateway-unified/internal/router/intent_router.go
package router

import (
    "strings"
)

type Intent struct {
    Scenario      string
    AgentType     string
    Confidence    float64
    Context       map[string]string
}

type IntentRouter struct {
    patterns map[string]IntentPattern
}

type IntentPattern struct {
    Keywords   []string
    Scenario   string
    AgentType  string
    Priority   int
}

func NewIntentRouter() *IntentRouter {
    router := &IntentRouter{
        patterns: make(map[string]IntentPattern),
    }

    // 注册模式
    router.registerPatterns()

    return router
}

func (r *IntentRouter) registerPatterns() {
    // 专利检索
    r.patterns["patent_search"] = IntentPattern{
        Keywords:  []string{"检索", "搜索", "专利", "现有技术", "prior art"},
        Scenario:  "patent_search",
        AgentType: "retriever",
        Priority:  10,
    }

    // 技术分析
    r.patterns["technical_analysis"] = IntentPattern{
        Keywords:  []string{"技术交底书", "技术方案", "技术特征", "要素提取", "双图"},
        Scenario:  "technical_analysis",
        AgentType: "analyzer",
        Priority:  10,
    }

    // 创造性分析
    r.patterns["creativity_analysis"] = IntentPattern{
        Keywords:  []string{"创造性", "创新性", "显而易见", "技术效果", "区别特征"},
        Scenario:  "creativity_analysis",
        AgentType: "creativity_analyzer",
        Priority:  10,
    }

    // 新颖性分析
    r.patterns["novelty_analysis"] = IntentPattern{
        Keywords:  []string{"新颖性", "公开", "现有技术", "单独对比"},
        Scenario:  "novelty_analysis",
        AgentType: "novelty_analyzer",
        Priority:  10,
    }

    // 侵权分析
    r.patterns["infringement_analysis"] = IntentPattern{
        Keywords:  []string{"侵权", "权利要求", "等同", "覆盖"},
        Scenario:  "infringement_analysis",
        AgentType: "infringement_analyzer",
        Priority:  10,
    }

    // 无效宣告
    r.patterns["invalidation_analysis"] = IntentPattern{
        Keywords:  []string{"无效宣告", "无效", "复审"},
        Scenario:  "invalidation_analysis",
        AgentType: "invalidation_analyzer",
        Priority:  10,
    }
}

func (r *IntentRouter) Route(userInput string) Intent {
    input := strings.ToLower(userInput)

    // 匹配模式
    bestMatch := Intent{
        Scenario:   "general",
        AgentType:  "xiaonuo",  // 默认由小诺处理
        Confidence: 0.0,
        Context:    make(map[string]string),
    }

    maxScore := 0

    for name, pattern := range r.patterns {
        score := r.calculateScore(input, pattern)
        if score > maxScore {
            maxScore = score
            bestMatch = Intent{
                Scenario:   pattern.Scenario,
                AgentType:  pattern.AgentType,
                Confidence: float64(score) / float64(len(pattern.Keywords)),
                Context: map[string]string{
                    "matched_pattern": name,
                },
            }
        }
    }

    return bestMatch
}

func (r *IntentRouter) calculateScore(input string, pattern IntentPattern) int {
    score := 0
    for _, keyword := range pattern.Keywords {
        if strings.Contains(input, keyword) {
            score++
        }
    }
    return score * pattern.Priority
}
```

### 2.2 负载均衡

```go
// gateway-unified/internal/router/load_balancer.go
package router

import (
    "hash/fnv"
    "sync"
)

type AgentInstance struct {
    ID       string
    Address  string
    Port     int
    Healthy  bool
    Load     int  // 当前负载
    Priority int  // 优先级
}

type LoadBalancer struct {
    agents      map[string][]*AgentInstance  // agent_type -> instances
    mu          sync.RWMutex
    strategy    BalancingStrategy
}

type BalancingStrategy int

const (
    RoundRobin BalancingStrategy = iota
    LeastConnections
    IPHash
    Priority
)

func NewLoadBalancer(strategy BalancingStrategy) *LoadBalancer {
    return &LoadBalancer{
        agents:   make(map[string][]*AgentInstance),
        strategy: strategy,
    }
}

func (lb *LoadBalancer) RegisterAgent(agentType string, instance *AgentInstance) {
    lb.mu.Lock()
    defer lb.mu.Unlock()

    lb.agents[agentType] = append(lb.agents[agentType], instance)
}

func (lb *LoadBalancer) SelectAgent(agentType string, clientIP string) *AgentInstance {
    lb.mu.RLock()
    defer lb.mu.RUnlock()

    instances, exists := lb.agents[agentType]
    if !exists || len(instances) == 0 {
        return nil
    }

    // 过滤健康实例
    healthy := make([]*AgentInstance, 0)
    for _, inst := range instances {
        if inst.Healthy {
            healthy = append(healthy, inst)
        }
    }

    if len(healthy) == 0 {
        return nil
    }

    switch lb.strategy {
    case RoundRobin:
        return lb.roundRobin(healthy)
    case LeastConnections:
        return lb.leastConnections(healthy)
    case IPHash:
        return lb.ipHash(healthy, clientIP)
    case Priority:
        return lb.priority(healthy)
    default:
        return healthy[0]
    }
}

func (lb *LoadBalancer) roundRobin(instances []*AgentInstance) *AgentInstance {
    // 简化实现，实际需要维护round-robin索引
    return instances[0]
}

func (lb *LoadBalancer) leastConnections(instances []*AgentInstance) *AgentInstance {
    minLoad := instances[0].Load
    selected := instances[0]

    for _, inst := range instances {
        if inst.Load < minLoad {
            minLoad = inst.Load
            selected = inst
        }
    }

    return selected
}

func (lb *LoadBalancer) ipHash(instances []*AgentInstance, clientIP string) *AgentInstance {
    h := fnv.New32a()
    h.Write([]byte(clientIP))
    hash := h.Sum32()
    index := int(hash) % len(instances)
    return instances[index]
}

func (lb *LoadBalancer) priority(instances []*AgentInstance) *AgentInstance {
    // 按优先级排序，返回最高优先级的健康实例
    maxPriority := instances[0].Priority
    selected := instances[0]

    for _, inst := range instances {
        if inst.Priority > maxPriority {
            maxPriority = inst.Priority
            selected = inst
        }
    }

    return selected
}
```

---

## 3️⃣ 会话管理

### 3.1 会话生命周期

```go
// gateway-unified/internal/session/manager.go
package session

import (
    "sync"
    "time"
)

type SessionState string

const (
    SessionCreated   SessionState = "created"
    SessionActive    SessionState = "active"
    SessionPaused    SessionState = "paused"
    SessionCompleted SessionState = "completed"
    SessionError     SessionState = "error"
)

type Session struct {
    ID              string
    UserID          string
    ProjectPath     string
    State           SessionState
    CreatedAt       time.Time
    UpdatedAt       time.Time
    LastActivityAt  time.Time
    CurrentTaskID   string
    Context         map[string]interface{}
    WebSocketConnID string
}

type SessionManager struct {
    sessions map[string]*Session
    mu       sync.RWMutex
    timeout  time.Duration
}

func NewSessionManager(timeout time.Duration) *SessionManager {
    return &SessionManager{
        sessions: make(map[string]*Session),
        timeout:  timeout,
    }
}

func (sm *SessionManager) Create(userID string, projectPath string) *Session {
    sm.mu.Lock()
    defer sm.mu.Unlock()

    session := &Session{
        ID:             generateSessionID(),
        UserID:         userID,
        ProjectPath:    projectPath,
        State:          SessionCreated,
        CreatedAt:      time.Now(),
        UpdatedAt:      time.Now(),
        LastActivityAt: time.Now(),
        Context:        make(map[string]interface{}),
    }

    sm.sessions[session.ID] = session
    return session
}

func (sm *SessionManager) Get(sessionID string) (*Session, bool) {
    sm.mu.RLock()
    defer sm.mu.RUnlock()

    session, exists := sm.sessions[sessionID]
    if !exists {
        return nil, false
    }

    // 检查超时
    if time.Since(session.LastActivityAt) > sm.timeout {
        delete(sm.sessions, sessionID)
        return nil, false
    }

    return session, true
}

func (sm *SessionManager) UpdateState(sessionID string, state SessionState) error {
    sm.mu.Lock()
    defer sm.mu.Unlock()

    session, exists := sm.sessions[sessionID]
    if !exists {
        return ErrSessionNotFound
    }

    session.State = state
    session.UpdatedAt = time.Now()
    session.LastActivityAt = time.Now()

    return nil
}

func (sm *SessionManager) SetContext(sessionID string, key string, value interface{}) error {
    sm.mu.Lock()
    defer sm.mu.Unlock()

    session, exists := sm.sessions[sessionID]
    if !exists {
        return ErrSessionNotFound
    }

    session.Context[key] = value
    session.LastActivityAt = time.Now()

    return nil
}

func (sm *SessionManager) CleanupExpiredSessions() {
    sm.mu.Lock()
    defer sm.mu.Unlock()

    now := time.Now()
    for id, session := range sm.sessions {
        if now.Sub(session.LastActivityAt) > sm.timeout {
            delete(sm.sessions, id)
        }
    }
}
```

---

## 4️⃣ 智能体代理实现

### 4.1 Python智能体代理

```python
# core/orchestration/agent_proxy.py
import asyncio
import grpc
from proto import agent_service_pb2, agent_service_pb2_grpc
from typing import AsyncIterator, Dict, Any
import logging


class AgentProxy:
    """
    智能体代理

    负责与Gateway通信，接收任务并执行
    """

    def __init__(
        self,
        agent_type: str,
        gateway_address: str = "localhost:8005",
        agent_port: int = 0  # 0表示自动分配
    ):
        self.agent_type = agent_type
        self.gateway_address = gateway_address
        self.agent_port = agent_port
        self.logger = logging.getLogger(f"AgentProxy[{agent_type}]")

    async def start(self):
        """启动代理服务"""
        # 1. 连接到Gateway
        self.channel = grpc.insecure_channel(self.gateway_address)
        self.stub = agent_service_pb2_grpc.AgentServiceStub(self.channel)

        # 2. 注册到Gateway
        await self._register_to_gateway()

        # 3. 启动gRPC服务器（接收Gateway请求）
        await self._start_grpc_server()

        self.logger.info(f"Agent proxy started: {self.agent_type}")

    async def _register_to_gateway(self):
        """注册到Gateway"""
        # TODO: 实现注册逻辑
        pass

    async def _start_grpc_server(self):
        """启动gRPC服务器"""
        # TODO: 实现gRPC服务器
        pass

    async def execute_task(
        self,
        task_id: str,
        scenario: str,
        user_input: str,
        context: Dict[str, str],
        project_path: str
    ) -> AsyncIterator[Dict[str, Any]]:
        """
        执行任务

        Args:
            task_id: 任务ID
            scenario: 场景
            user_input: 用户输入
            context: 上下文
            project_path: 项目路径

        Yields:
            任务响应
        """
        self.logger.info(f"Executing task: {task_id}")

        try:
            # 加载智能体
            agent = await self._load_agent(scenario)

            # 执行任务
            async for result in agent.execute(user_input, context, project_path):
                yield {
                    "type": "partial" if result.get("partial") else "final",
                    "result": result
                }

        except Exception as e:
            self.logger.error(f"Task execution error: {e}")
            yield {
                "type": "error",
                "error": {
                    "code": "EXECUTION_ERROR",
                    "message": str(e)
                }
            }

    async def _load_agent(self, scenario: str):
        """加载智能体"""
        # 根据scenario和agent_type加载相应的智能体
        # 例如：
        # if self.agent_type == "xiaona":
        #     from core.agents.xiaona_agent import XiaonaAgent
        #     return XiaonaAgent()
        pass


# 示例：小娜代理
class XiaonaAgentProxy(AgentProxy):
    """小娜智能体代理"""

    def __init__(self, gateway_address: str = "localhost:8005"):
        super().__init__(
            agent_type="xiaona",
            gateway_address=gateway_address,
            agent_port=8006
        )

    async def _load_agent(self, scenario: str):
        """加载小娜智能体"""
        from core.agents.xiaona_agent import XiaonaAgent
        return XiaonaAgent()


# 示例：小诺代理
class XiaonuoAgentProxy(AgentProxy):
    """小诺智能体代理"""

    def __init__(self, gateway_address: str = "localhost:8005"):
        super().__init__(
            agent_type="xiaonuo",
            gateway_address=gateway_address,
            agent_port=8007
        )

    async def _load_agent(self, scenario: str):
        """加载小诺智能体"""
        from core.orchestration.xiaonuo_orchestrator import XiaonuoOrchestrator
        return XiaonuoOrchestrator()


# 启动脚本
async def main():
    """启动智能体代理"""
    import sys

    agent_type = sys.argv[1] if len(sys.argv) > 1 else "xiaona"

    if agent_type == "xiaona":
        proxy = XiaonaAgentProxy()
    elif agent_type == "xiaonuo":
        proxy = XiaonuoAgentProxy()
    else:
        print(f"Unknown agent type: {agent_type}")
        return

    await proxy.start()

    # 保持运行
    await asyncio.Event().wait()


if __name__ == "__main__":
    asyncio.run(main())
```

---

## 5️⃣ 完整工作流程

### 5.1 任务执行流程

```
用户请求
    ↓
Gateway (WebSocket)
    ├─ 1. 意图识别 → 确定智能体和场景
    ├─ 2. 创建会话 → Session管理器
    └─ 3. 路由决策 → 选择智能体实例
    ↓
小诺（编排者）
    ├─ 4. 制定计划 → 展示给用户
    ├─ 5. 等待确认 → 用户确认
    └─ 6. 分解任务 → 分配给子智能体
    ↓
子智能体（小娜/检索者/分析者）
    ├─ 7. 接收任务 → gRPC调用
    ├─ 8. 执行任务 → 流式返回进度
    └─ 9. 返回结果 → gRPC流式响应
    ↓
Gateway
    ├─ 10. 聚合结果 → 整合子智能体输出
    └─ 11. 返回用户 → WebSocket实时推送
    ↓
用户看到最终结果
```

### 5.2 示例：专利检索任务

```typescript
// 1. 用户发起请求
const userRequest = {
  type: "task_create",
  session_id: "session_001",
  payload: {
    task_id: "task_001",
    user_input: "帮我检索关于自动驾驶掉头的专利",
    project_path: "/Users/xujian/Desktop/睿羿科技1件/"
  }
};

// 2. Gateway意图识别
const intent = gateway.intentRouter.route(userRequest.payload.user_input);
// 结果: { scenario: "patent_search", agent_type: "retriever", confidence: 0.9 }

// 3. Gateway创建会话
const session = gateway.sessionManager.create("user_001", "/path/to/project/");

// 4. Gateway路由到小诺（编排者）
gateway.routeToAgent("xiaonuo", {
  task_id: "task_001",
  scenario: "patent_search",
  user_input: userRequest.payload.user_input,
  context: { session_id: session.ID }
});

// 5. 小诺制定计划
const plan = await xiaonuo.createPlan({
  scenario: "patent_search",
  user_input: "帮我检索关于自动驾驶掉头的专利"
});

// 6. 小诺请求用户确认
gateway.websocketHandler.broadcastToSession(session.ID, {
  type: "user_confirm_request",
  payload: {
    task_id: "task_001",
    title: "专利检索计划",
    description: "将按以下步骤执行专利检索",
    plan: [
      {
        step_id: "step_1",
        agent: "analyzer",
        description: "分析技术方案，提取关键词",
        estimated_time_minutes: 5
      },
      {
        step_id: "step_2",
        agent: "retriever",
        description: "执行专利检索（本地PG + Google Patents）",
        estimated_time_minutes: 10
      },
      {
        step_id: "step_3",
        agent: "retriever",
        description: "去重排序，下载全文",
        estimated_time_minutes: 5
      }
    ]
  }
});

// 7. 用户确认
const userConfirm = {
  type: "user_confirm_response",
  payload: {
    task_id: "task_001",
    approved: true
  }
};

// 8. 小诺开始执行，调度子智能体
// 8.1 调度分析者
const analyzerResult = await gateway.executeAgentTask({
  agent_type: "analyzer",
  task: {
    task_id: "task_001_step_1",
    scenario: "technical_analysis",
    user_input: "分析技术方案：自动驾驶掉头",
    project_path: "/Users/xujian/Desktop/睿羿科技1件/"
  }
});

// 8.2 调度检索者
const retrieverResult = await gateway.executeAgentTask({
  agent_type: "retriever",
  task: {
    task_id: "task_001_step_2",
    scenario: "patent_search",
    user_input: "检索关键词：自动驾驶、掉头、轨迹规划",
    context: analyzerResult.context,
    project_path: "/Users/xujian/Desktop/睿羿科技1件/"
  }
});

// 9. 智能体流式返回进度
gateway.websocketHandler.broadcastToSession(session.ID, {
  type: "task_progress",
  payload: {
    task_id: "task_001_step_2",
    agent_name: "retriever",
    progress: 50,
    message: "正在检索本地PostgreSQL专利库...",
    details: {
      total_patents: 1000,
      processed: 500
    }
  }
});

// 10. 小诺聚合结果
const finalResult = await xiaonuo.aggregateResults([
  analyzerResult,
  retrieverResult
]);

// 11. Gateway返回最终结果
gateway.websocketHandler.broadcastToSession(session.ID, {
  type: "task_complete",
  payload: {
    task_id: "task_001",
    result: finalResult
  }
});
```

---

## 6️⃣ 实施计划

### Phase 1: Gateway增强（1周）

**任务**:
1. 实现WebSocket控制平面
2. 实现gRPC数据平面
3. 实现智能路由
4. 实现会话管理

**产出**:
- `gateway-unified/internal/websocket/`
- `gateway-unified/internal/router/`
- `gateway-unified/internal/session/`

### Phase 2: 智能体代理（1周）

**任务**:
1. 实现AgentProxy基类
2. 实现小娜代理
3. 实现小诺代理
4. 实现其他智能体代理

**产出**:
- `core/orchestration/agent_proxy.py`
- `scripts/start_agent_proxy.sh`

### Phase 3: 集成测试（1周）

**任务**:
1. 端到端测试
2. 性能测试
3. 压力测试
4. 优化调整

**产出**:
- `tests/integration/test_gateway_integration.py`
- 性能测试报告

---

## 7️⃣ 参考资源

### gRPC文档
- [gRPC Python Quick Start](https://grpc.io/docs/languages/python/quickstart/)
- [gRPC Go Quick Start](https://grpc.io/docs/languages/go/quickstart/)

### WebSocket文档
- [Gorilla WebSocket](https://github.com/gorilla/websocket)
- [WebSocket Protocol](https://tools.ietf.org/html/rfc6455)

### 负载均衡算法
- [Consistent Hashing](https://en.wikipedia.org/wiki/Consistent_hashing)
- [Least Connections](https://en.wikipedia.org/wiki/Least_connections_scheduling)

---

**End of Document**
