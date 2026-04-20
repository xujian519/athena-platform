# LLM调用优化系统 - 完整实现指南

## 📋 概述

本文档提供Go语言LLM调用优化系统的完整实现，用于优化Athena平台的LLM调用性能和成本。

## 🎯 优化目标

- **成本降低**: 30% LLM调用成本节省
- **性能提升**: 响应时间降低50%（通过缓存）
- **智能路由**: 自动选择最优模型
- **并发处理**: 批量请求性能提升5倍

---

## 📦 文件结构

```
gateway-unified/services/llm/
├── client.go      # LLM HTTP客户端
├── routing.go     # 智能路由系统
├── cache.go       # 响应缓存层
├── concurrent.go  # 并发处理模块
├── service.go     # 统一服务层
└── README.md      # 本文档
```

---

## 🏗️ 架构设计

### 三层架构

```
┌─────────────────────────────────────┐
│       LLMService (统一服务层)        │
│  - 统一接口                          │
│  - 自动缓存管理                      │
│  - 性能统计                          │
└──────────────┬──────────────────────┘
               │
    ┌──────────┼──────────┬────────────┐
    ↓          ↓          ↓            ↓
┌────────┐ ┌───────┐ ┌────────┐ ┌──────────┐
│ Client │ │ Router│ │  Cache │ │Processor │
│ HTTP   │ │Smart  │ │  LRU   │ │Concurrent│
│        │ │Routing│ │ Redis  │ │  Pool    │
└────────┘ └───────┘ └────────┘ └──────────┘
```

### 核心组件

**1. HTTP Client (client.go)**
- 连接池优化（MaxIdleConns: 50, MaxIdleConnsPerHost: 10）
- 智能重试（最多3次，指数退避）
- 性能统计（QPS、延迟、token使用、成本）

**2. Smart Router (routing.go)**
- 任务复杂度分析（0.0-1.0评分）
- 三层模型架构：
  - **Economy**: gpt-3.5-turbo（快速、低成本）
  - **Balanced**: gpt-4o-mini（性能与成本平衡）
  - **Premium**: gpt-4o（最佳质量）
- 自动模型选择
- 成本节省计算

**3. Response Cache (cache.go)**
- 本地缓存（sync.Map，500条容量）
- Redis分布式缓存
- 24小时TTL
- 语义缓存（基于prompt hash）
- 缓存命中率统计

**4. Concurrent Processor (concurrent.go)**
- Goroutine池（默认10并发）
- 批量请求优化
- 自动重试机制
- 性能监控

**5. Unified Service (service.go)**
- 统一接口
- 自动路由+缓存
- 完整统计
- 监控指标导出

---

## 📊 性能预期

### 成本优化

| 场景 | 无优化 | 有优化 | 节省 |
|-----|-------|-------|------|
| **简单问答** | $0.002/1K | $0.002/1K | 0% |
| **代码生成** | $2.50/1K | $0.15/1K | **94%** |
| **专利分析** | $2.50/1K | $2.50/1K | 0% |
| **混合负载** | $1.00/1K | $0.70/1K | **30%** |

**总体成本节省**: 30%（假设70%简单任务使用经济型模型）

### 性能优化

| 场景 | 无缓存 | 有缓存 | 提升 |
|-----|-------|-------|------|
| **重复查询** | 2000ms | <1ms | **99.95%** |
| **批量请求(10)** | 20000ms | 2000ms | **90%** |
| **缓存命中率** | 0% | 80%+ | - |

### 并发优化

| 指标 | 无并发 | 有并发 | 提升 |
|-----|-------|-------|------|
| **批量处理(10)** | 20秒 | 2秒 | **90%** |
| **吞吐量** | 0.5 QPS | 5 QPS | **10倍** |

---

## 🚀 使用示例

### 1. 基础使用

```go
package main

import (
    "context"
    "log"
    "time"

    "github.com/athena-workspace/gateway-unified/services/llm"
)

func main() {
    // 创建LLM服务
    cfg := &llm.LLMServiceConfig{
        ClientConfig: &llm.Config{
            BaseURL:    "https://api.openai.com/v1",
            APIKey:     "your-api-key",
            Model:      "gpt-3.5-turbo",
            Timeout:    30 * time.Second,
            MaxRetries: 3,
        },
        CacheConfig:      llm.DefaultLLMCacheConfig(),
        ConcurrentConfig: llm.DefaultConcurrentConfig(),
        Enabled:          true,
    }

    service, err := llm.NewLLMService(cfg)
    if err != nil {
        log.Fatal(err)
    }
    defer service.Close()

    // 执行聊天请求
    ctx := context.Background()
    req := &llm.ChatRequest{
        Messages: []llm.Message{
            {Role: "user", Content: "什么是专利？"},
        },
    }

    resp, err := service.Chat(ctx, req)
    if err != nil {
        log.Fatal(err)
    }

    log.Printf("响应: %s", resp.Choices[0].Message.Content)
    log.Printf("模型: %s", resp.Model)
    log.Printf("Tokens: %d", resp.Usage.TotalTokens)
}
```

### 2. 批量请求

```go
// 批量请求（自动并发）
reqs := make([]*llm.ChatRequest, 10)
for i := 0; i < 10; i++ {
    reqs[i] = &llm.ChatRequest{
        Messages: []llm.Message{
            {Role: "user", Content: fmt.Sprintf("问题%d: ...", i)},
        },
    }
}

results, err := service.BatchChat(ctx, reqs)
if err != nil {
    log.Fatal(err)
}

for i, resp := range results {
    log.Printf("响应[%d]: %s", i, resp.Choices[0].Message.Content)
}
```

### 3. 指定模型层级

```go
// 强制使用高级模型
resp, err := service.ChatWithModel(ctx, req, llm.TierPremium)
if err != nil {
    log.Fatal(err)
}

// 自动路由（推荐）
resp, err := service.Chat(ctx, req)
```

### 4. 查看性能统计

```go
// 获取完整统计
stats := service.GetStats()

// 服务统计
serviceStats := stats["service"].(map[string]interface{})
log.Printf("总请求: %d", serviceStats["total_requests"])
log.Printf("缓存命中率: %.1f%%",
    float64(serviceStats["cache_hits"].(uint64)) /
    float64(serviceStats["total_requests"].(uint64)) * 100)

// 路由统计
routerStats := stats["router"].(map[string]interface{})
log.Printf("经济型使用: %d", routerStats["economy_count"])
log.Printf("平衡型使用: %d", routerStats["balanced_count"])
log.Printf("高级型使用: %d", routerStats["premium_count"])

// 成本统计
log.Printf("总成本: $%.4f", serviceStats["total_cost"])
log.Printf("节省成本: $%.4f", serviceStats["cost_saved"])
```

### 5. 缓存预热

```go
// 预热热点数据
hotPrompts := []string{
    "什么是专利？",
    "如何申请专利？",
    "专利的有效期是多久？",
}

err := service.WarmupCache(ctx, hotPrompts, "gpt-3.5-turbo")
if err != nil {
    log.Fatal(err)
}

log.Println("缓存预热完成")
```

---

## 🔧 安装和集成

### 1. 安装依赖

```bash
cd gateway-unified/services/llm

# 初始化Go模块
go mod init github.com/athena-workspace/gateway-unified/services/llm

# 安装依赖
go get github.com/go-redis/redis/v8
go get go.uber.org/zap

# 整理依赖
go mod tidy
```

### 2. 编译

```bash
# 编译为库
go build -o llm-service.a

# 或编译为可执行文件（如果包含main.go）
go build -o llm-service
```

### 3. 集成到Gateway

#### 方案A：作为Go库集成

```go
// 在gateway-unified中导入
import (
    llmservice "github.com/athena-workspace/gateway-unified/services/llm"
)

// 在Gateway中初始化
llmService := llmservice.NewLLMService(cfg)

// 在HTTP handler中使用
func handleLLMRequest(w http.ResponseWriter, r *http.Request) {
    req := &llmservice.ChatRequest{...}
    resp, err := llmService.Chat(r.Context(), req)
    // ...
}
```

#### 方案B：作为独立服务

```bash
# 启动独立服务
./llm-service --port 8024

# Gateway通过HTTP调用
curl http://localhost:8024/chat -d '{"messages": [...]}'
```

---

## 📈 监控和指标

### Prometheus指标

```go
import "github.com/prometheus/client_golang/prometheus"

var (
    llmRequestsTotal = prometheus.NewCounterVec(
        prometheus.CounterOpts{
            Name: "llm_requests_total",
        },
        []string{"model", "tier"},
    )

    llmCacheHits = prometheus.NewCounterVec(
        prometheus.CounterOpts{
            Name: "llm_cache_hits_total",
        },
        []string{"cache_type"},
    )

    llmResponseTime = prometheus.NewHistogramVec(
        prometheus.HistogramOpts{
            Name:    "llm_response_time_milliseconds",
            Buckets: []float64{10, 50, 100, 500, 1000, 2000, 5000},
        },
        []string{"model"},
    )

    llmCost = prometheus.NewCounterVec(
        prometheus.CounterOpts{
            Name: "llm_cost_total_dollars",
        },
        []string{"model"},
    )
)

// 注册指标
prometheus.MustRegister(llmRequestsTotal)
prometheus.MustRegister(llmCacheHits)
prometheus.MustRegister(llmResponseTime)
prometheus.MustRegister(llmCost)
```

### Grafana仪表板

建议监控面板：
- **请求总量**: `llm_requests_total`
- **缓存命中率**: `llm_cache_hits_total / llm_requests_total`
- **响应时间**: P50, P95, P99
- **成本统计**: 按模型分组
- **错误率**: 4xx/5xx占比

---

## 🎯 验收标准

### 功能验收
- [ ] 支持单次聊天请求
- [ ] 支持批量请求
- [ ] 智能路由正常工作
- [ ] 缓存自动管理
- [ ] 性能统计准确

### 性能验收
- [ ] 缓存命中率 >80%
- [ ] 成本节省 >30%
- [ ] P95延迟 <100ms（缓存命中）
- [ ] 批量请求吞吐量 >5 QPS

### 稳定性验收
- [ ] 零崩溃运行24小时
- [ ] 内存占用稳定
- [ ] 错误率 <0.1%

---

## 🚨 常见问题

### Q1: Redis连接失败

**解决**：
- 检查Redis是否运行：`docker ps | grep redis`
- 检查端口：`lsof -i :16379`
- 检查配置：`CacheConfig.RedisAddr`

### Q2: 模型选择不正确

**解决**：
- 检查路由规则：`router.ListRules()`
- 调整规则优先级
- 使用指定模型：`ChatWithModel(req, TierPremium)`

### Q3: 缓存命中率低

**解决**：
- 增加缓存容量：`CacheConfig.LocalSize`
- 延长TTL：`CacheConfig.TTL`
- 预热热点数据：`WarmupCache()`

---

## 📊 最佳实践

### 1. 合理设置缓存策略

```go
// 简单问答：长TTL
qaCacheCfg := &LLMCacheConfig{
    TTL: 24 * time.Hour,
    MinTokens: 10,
}

// 复杂分析：短TTL
analysisCacheCfg := &LLMCacheConfig{
    TTL: 1 * time.Hour,
    MinTokens: 100,
}
```

### 2. 优化并发数

```go
// CPU密集型任务：减少并发
cfg := &ConcurrentConfig{
    MaxConcurrency: 5,
}

// I/O密集型任务：增加并发
cfg := &ConcurrentConfig{
    MaxConcurrency: 20,
}
```

### 3. 监控成本

```go
// 定期检查成本
stats := service.GetStats()
serviceStats := stats["service"].(map[string]interface{})
totalCost := serviceStats["total_cost"].(float64)
costSaved := serviceStats["cost_saved"].(float64)

log.Printf("总成本: $%.2f, 节省: $%.2f (%.1f%%)",
    totalCost, costSaved, costSaved/totalCost*100)
```

---

## 🎊 总结

### 核心优势

1. **成本优化**
   - 智能路由节省30%成本
   - 缓存节省重复调用成本
   - 批量处理降低API调用次数

2. **性能提升**
   - 缓存命中时延迟<1ms
   - 并发处理提升5倍吞吐量
   - 连接池优化降低延迟

3. **易于使用**
   - 统一接口
   - 自动优化
   - 完善监控

### 下一步

1. ✅ 代码实现完成
2. ⏳ 单元测试
3. ⏳ 集成到Gateway
4. ⏳ 性能验证
5. ⏳ 生产部署

---

**文档版本**: v1.0
**创建时间**: 2026-04-20
**维护者**: Athena平台团队
