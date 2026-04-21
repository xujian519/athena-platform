# Athena团队 - Go网关集成方案

> **版本**: 1.0
> **日期**: 2026-04-21
> **状态**: 已定稿

---

## 📋 文档概述

本文档定义Athena团队与Go网关的集成方案，包括API设计、通信协议、性能优化等。

---

## 🎯 核心原则

### 1. API转发模式

**定义**：Go网关作为统一入口，所有请求通过网关转发到Python服务。

**优势**：
- 统一鉴权、限流、路由
- 连接池复用，降低开销
- 本地缓存，减少重复调用
- gRPC优化，降低延迟

### 2. 性能优先

**定义**：通信性能是最高优先级，不影响业务质量的前提下优化性能。

**优化策略**：
- 使用gRPC替代REST（降低延迟）
- 连接池复用
- 本地缓存
- 并行处理

---

## 🏗️ 架构设计

### 系统架构

```
┌─────────────────────────────────────────────────────────┐
│  用户                                                       │
└──────────────────────────────┬──────────────────────────────┘
                               │
                               ↓
┌────────────────────────────────────────────────────────────┐
│  Go网关（8005） - 统一入口                                │
│  - 鉴权、限流、路由                                         │
│  - 连接池、本地缓存、gRPC优化                              │
└──────────────────────────────┬──────────────────────────────┘
                               │ gRPC (30ms)
                               ↓
┌────────────────────────────────────────────────────────────┐
│  Python服务层                                               │
│  ┌──────────────────────────────────────────────────────┐   │
│  │ 小诺编排者（XiaonuoOrchestrator）                    │   │
│  │ - 场景识别                                            │   │
│  │ - 制定执行计划                                        │   │
│  │ - 展示计划并等待确认                                  │   │
│  │ - 调度Athena团队                                      │   │
│  │ - 汇总结果                                            │   │
│  └──────────────────────────────────────────────────────┘   │
│  ┌──────────────────────────────────────────────────────┐   │
│  │ Athena团队（专业智能体）                               │   │
│  └──────────────────────────────────────────────────────┘   │
└──────────────────────────────┬──────────────────────────────┘
                               │
                               ↓
┌────────────────────────────────────────────────────────────┐
│  知识库层                                                   │
│  - 宝宸知识库（厘清思路、用户参考）                         │
│  - 法律世界模型（专业知识、法规库、案例库）                 │
└────────────────────────────────────────────────────────────┘
```

---

## 🔌 API设计

### REST API（兼容层）

**基础URL**：`http://localhost:8005/api/athena`

#### 1. 处理用户请求

**请求**：
```http
POST /api/athena/process
Content-Type: application/json

{
  "user_input": "帮我检索关于自动驾驶掉头的专利",
  "session_id": "session_001",
  "config": {
    "limit": 50
  }
}
```

**响应**：
```http
HTTP/1.1 200 OK
Content-Type: application/json

{
  "status": "success",
  "scenario": "patent_search",
  "workflow_id": "workflow_20260421123456_abc12345",
  "total_time": 15.23,
  "steps_completed": 1,
  "steps_total": 1,
  "output": {
    "keywords": ["自动驾驶", "掉头", "路径规划"],
    "patents": [...],
    "total_count": 50
  }
}
```

#### 2. 获取智能体状态

**请求**：
```http
GET /api/athena/agents/status
```

**响应**：
```http
HTTP/1.1 200 OK
Content-Type: application/json

{
  "statistics": {
    "total_agents": 4,
    "enabled": 4,
    "total_capabilities": 12
  },
  "agents": {
    "xiaona_retriever": {
      "type": "检索者",
      "phase": 1,
      "enabled": true,
      "capabilities": ["patent_search", "keyword_expansion", "document_filtering"]
    }
  }
}
```

#### 3. 获取支持的场景

**请求**：
```http
GET /api/athena/scenarios
```

**响应**：
```http
HTTP/1.1 200 OK
Content-Type: application/json

{
  "scenarios": [
    {
      "scenario": "patent_search",
      "name": "专利检索",
      "description": "检索相关专利文献",
      "keywords": ["检索", "搜索", "查找专利"],
      "required_agents": ["xiaona_retriever"],
      "execution_mode": "sequential"
    }
  ]
}
```

#### 4. 控制工作流

**请求**：
```http
POST /api/athena/workflow/{workflow_id}/control
Content-Type: application/json

{
  "action": "pause",
  "reason": "用户要求暂停"
}
```

**响应**：
```http
HTTP/1.1 200 OK
Content-Type: application/json

{
  "status": "paused",
  "workflow_id": "workflow_001",
  "current_step": "step_2",
  "can_resume": true
}
```

---

### gRPC API（推荐）

**定义文件**：`protos/athena.proto`

```protobuf
syntax = "proto3";

package athena;

service AthenaService {
  // 处理用户请求
  rpc Process(ProcessRequest) returns (ProcessResponse);

  // 获取智能体状态
  rpc GetAgentStatus(StatusRequest) returns (AgentStatusResponse);

  // 获取支持的场景
  rpc GetScenarios(ScenariosRequest) returns (ScenariosResponse);

  // 控制工作流
  rpc ControlWorkflow(ControlRequest) returns (ControlResponse);

  // 流式处理（支持渐进式返回）
  rpc ProcessStream(ProcessRequest) returns (stream ProcessStreamResponse);
}

message ProcessRequest {
  string user_input = 1;
  string session_id = 2;
  map<string, string> config = 3;
}

message ProcessResponse {
  string status = 1;
  string scenario = 2;
  string workflow_id = 3;
  double total_time = 4;
  int32 steps_completed = 5;
  int32 steps_total = 6;
  map<string, string> output = 7;
}

message ProcessStreamResponse {
  string status = 1;  // "running", "completed", "error"
  string step_id = 2;
  string step_name = 3;
  double progress = 4;  // 0.0 - 1.0
  map<string, string> intermediate_result = 5;
}
```

**优势**：
- 更低的延迟（30ms vs 100ms）
- 更高的吞吐量
- 支持流式传输
- 强类型定义

---

## 🔧 Go网关配置

### 路由配置

**配置文件**：`gateway-unified/config.yaml`

```yaml
server:
  port: 8005
  production: false
  read_timeout: 30
  write_timeout: 30

gateway:
  routes:
    # Athena服务路由
    - path: /api/athena/*
      strip_path: true
      target_service: "athena-python"
      timeout: 120

    # WebSocket控制平面
    - path: /ws/athena/*
      strip_path: true
      target_service: "athena-python"
      timeout: 600
      websocket: true

  # 服务发现
  services:
    - id: athena-python
      name: Athena Python Service
      protocol: grpc
      host: localhost
      port: 50051
      health_check: /health
      health_check_interval: 10

  # 连接池配置
  connection_pool:
    max_connections: 100
    max_idle_connections: 10
    idle_timeout: 90

  # 本地缓存
  cache:
    enabled: true
    ttl: 300
    max_size: 1000
```

### 中间件配置

**鉴权中间件**：
```go
func AuthMiddleware() gin.HandlerFunc {
    return func(c *gin.Context) {
        token := c.GetHeader("Authorization")
        if token == "" {
            c.JSON(401, gin.H{"error": "未授权"})
            c.Abort()
            return
        }

        // 验证token
        user, err := validateToken(token)
        if err != nil {
            c.JSON(401, gin.H{"error": "无效的token"})
            c.Abort()
            return
        }

        c.Set("user", user)
        c.Next()
    }
}
```

**限流中间件**：
```go
func RateLimitMiddleware() gin.HandlerFunc {
    limiter := rate.NewLimiter(10, 100) // 10 req/s, burst 100

    return func(c *gin.Context) {
        if !limiter.Allow() {
            c.JSON(429, gin.H{"error": "请求过于频繁"})
            c.Abort()
            return
        }
        c.Next()
    }
}
```

---

## ⚡ 性能优化

### 1. gRPC优化

**连接复用**：
```go
// 创建gRPC连接池
func NewGRPCClientPool(target string, size int) []*grpc.ClientConn {
    pool := make([]*grpc.ClientConn, size)
    for i := 0; i < size; i++ {
        conn, err := grpc.Dial(
            target,
            grpc.WithTransportCodec(encoding.GetCodec(proto.Name)),
            grpc.WithDefaultCallOptions(
                grpc.MaxCallRecvMsgSize(10*1024*1024), // 10MB
            ),
        )
        if err != nil {
            log.Fatal(err)
        }
        pool[i] = conn
    }
    return pool
}
```

**目标延迟**：30ms（P95）

### 2. 本地缓存

**缓存配置**：
```go
type Cache struct {
    ttl     time.Duration
    maxSize int
    data    map[string]*CacheItem
    mu      sync.RWMutex
}

func (c *Cache) Get(key string) (interface{}, bool) {
    c.mu.RLock()
    defer c.mu.RUnlock()

    item, ok := c.data[key]
    if !ok {
        return nil, false
    }

    if time.Since(item.CreatedAt) > c.ttl {
        delete(c.data, key)
        return nil, false
    }

    return item.Value, true
}

func (c *Cache) Set(key string, value interface{}) {
    c.mu.Lock()
    defer c.mu.Unlock()

    if len(c.data) >= c.maxSize {
        // LRU淘汰
        c.evict()
    }

    c.data[key] = &CacheItem{
        Value:     value,
        CreatedAt: time.Now(),
    }
}
```

**缓存场景**：
- 智能体状态（TTL: 60s）
- 场景识别结果（TTL: 300s）
- 常见问题答案（TTL: 600s）

### 3. 并行处理

**并行场景**：
- 多数据源检索
- 多专利同时分析
- 多策略同时尝试

**实现**：
```go
func ParallelSearch(queries []string) []SearchResult {
    results := make([]SearchResult, len(queries))
    var wg sync.WaitGroup
    wg.Add(len(queries))

    for i, query := range queries {
        go func(idx int, q string) {
            defer wg.Done()
            results[idx] = search(q)
        }(i, query)
    }

    wg.Wait()
    return results
}
```

---

## 🔌 WebSocket集成

### 连接建立

**前端代码**：
```javascript
const ws = new WebSocket('ws://localhost:8005/ws/athena');

ws.onopen = () => {
    console.log('WebSocket连接已建立');
};

ws.onmessage = (event) => {
    const data = JSON.parse(event.data);
    handleMessage(data);
};

ws.onerror = (error) => {
    console.error('WebSocket错误:', error);
};

ws.onclose = () => {
    console.log('WebSocket连接已关闭');
};
```

### 消息格式

**客户端发送**：
```json
{
  "type": "process",
  "data": {
    "user_input": "帮我检索关于自动驾驶掉头的专利",
    "session_id": "session_001"
  }
}
```

**服务端推送**：
```json
{
  "type": "plan",
  "data": {
    "scenario": "patent_search",
    "steps": [...],
    "total_estimated_time": 70
  }
}
```

```json
{
  "type": "progress",
  "data": {
    "step_id": "step_2",
    "step_name": "检索对比文件",
    "progress": 0.5,
    "intermediate_result": {...}
  }
}
```

```json
{
  "type": "completed",
  "data": {
    "status": "success",
    "output": {...}
  }
}
```

### 控制消息

**暂停**：
```json
{
  "type": "control",
  "action": "pause",
  "workflow_id": "workflow_001"
}
```

**继续**：
```json
{
  "type": "control",
  "action": "resume",
  "workflow_id": "workflow_001"
}
```

**调整计划**：
```json
{
  "type": "control",
  "action": "adjust",
  "workflow_id": "workflow_001",
  "adjustments": {
    "add_steps": [...],
    "remove_steps": [...],
    "modify_steps": {...}
  }
}
```

---

## 📊 监控指标

### 性能指标

| 指标 | 目标 | 测量方式 |
|------|------|---------|
| API响应时间 | <100ms (P95) | Prometheus |
| gRPC延迟 | <30ms (P95) | Prometheus |
| 缓存命中率 | >90% | Prometheus |
| 请求吞吐量 | >100 QPS | Prometheus |
| 错误率 | <0.1% | Prometheus |

### 业务指标

| 指标 | 测量方式 |
|------|---------|
| 场景识别准确率 | 日志分析 |
| 智能体执行成功率 | 日志分析 |
| 用户满意度 | 用户反馈 |
| 任务完成时间 | 日志分析 |

---

## 🔗 关联文档

- [Athena团队架构设计](../ATHENA_TEAM_ARCHITECTURE_V2.md)
- [工作流程设计](../workflows/SCENARIO_BASED_WORKFLOWS.md)
- [数据契约规范](../api/DATA_CONTRACT_SPECIFICATION.md)

---

## 📞 维护者

- **团队**: Athena平台团队
- **联系**: xujian519@gmail.com
- **最后更新**: 2026-04-21

---

**End of Document**
