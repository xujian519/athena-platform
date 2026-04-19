# Athena Gateway功能迁移计划

**创建时间**: 2026-02-20
**目标**: 将其他Gateway实现的优秀功能迁移到统一Gateway
**基础**: api-gateway/

---

## 📋 迁移清单

### Phase 1: 从 core/gateway/ 迁移可观测性特性

#### 1.1 OpenTelemetry追踪集成

**源位置**: `core/gateway/pkg/tracing/`

**目标功能**:
```go
// 追踪配置
type TracerConfig struct {
    ServiceName    string
    ServiceVersion string
    Environment    string
    Enabled        bool
    Jaeger         JaegerConfig
    Sampling       SamplingConfig
    BatchTimeout   time.Duration
    ExportTimeout  time.Duration
}

// 追踪器接口
type Tracer interface {
    Start(ctx context.Context, spanName string, opts ...trace.SpanStartOption) (context.Context, trace.Span)
    Shutdown(ctx context.Context) error
}
```

**迁移目标**: `gateway-unified/internal/tracing/`

**优先级**: P0 (核心功能)

---

#### 1.2 Prometheus指标增强

**源位置**: `core/gateway/internal/handler/metrics.go`

**目标功能**:
```go
// 增强的指标处理器
type MetricsHandler struct {
    prometheus.Handler
    customMetrics map[string]prometheus.Collector
}

// 自定义指标
func (h *MetricsHandler) RegisterCustomMetric(name string, metric prometheus.Collector)
```

**迁移目标**: `gateway-unified/internal/monitoring/prometheus_enhanced.go`

**优先级**: P0 (核心功能)

---

#### 1.3 结构化日志

**源位置**: `core/gateway/pkg/logger/`

**目标功能**:
```go
// 日志配置
type LoggingConfig struct {
    Level      string
    Format     string // json, text
    Output     []string
    MaxSize    int
    MaxBackups int
    MaxAge     int
    Compress   bool
}

// 日志接口
type Logger interface {
    Debug(msg string, fields ...Field)
    Info(msg string, fields ...Field)
    Warn(msg string, fields ...Field)
    Error(msg string, fields ...Field)
    Fatal(msg string, fields ...Field)
}
```

**迁移目标**: `gateway-unified/internal/logging/logger.go`

**优先级**: P1 (重要功能)

---

### Phase 2: 从 services/api-gateway/go-gateway/ 迁移生命周期管理

#### 2.1 优雅关闭增强

**源位置**: `services/api-gateway/go-gateway/cmd/gateway/main.go`

**目标功能**:
```go
// 优雅关闭管理器
type GracefulShutdown struct {
    server     *http.Server
    gateway    Gateway
    monitoring *MonitoringServer
    timeout    time.Duration
}

func (g *GracefulShutdown) Shutdown() error {
    // 1. 停止接受新请求
    // 2. 等待现有请求完成（超时控制）
    // 3. 关闭HTTP服务器
    // 4. 关闭网关资源
    // 5. 关闭监控服务
    // 6. 刷新日志
}
```

**迁移目标**: `gateway-unified/internal/lifecycle/shutdown.go`

**优先级**: P0 (核心功能)

---

#### 2.2 监控服务集成

**源位置**: `services/api-gateway/go-gateway/internal/monitoring/`

**目标功能**:
```go
// 监控服务器
type MonitoringServer struct {
    config   config.MonitoringConfig
    prometheus *PrometheusServer
    jaeger    *JaegerServer
}

func (m *MonitoringServer) Start() error
func (m *MonitoringServer) Shutdown(ctx context.Context) error
```

**迁移目标**: `gateway-unified/internal/monitoring/server.go`

**优先级**: P1 (重要功能)

---

### Phase 3: 从 gateway_extended.py 借鉴API设计

#### 3.1 批量服务注册

**源设计**: `gateway_extended.py`

```python
@gateway_ext.post("/services/batch_register")
async def batch_register(req: BatchRegisterRequest):
    results = []
    for svc in req.services:
        sid = f"{svc.name}:{svc.host}:{svc.port}"
        inst = ServiceInstance(
            id=sid,
            service_name=svc.name,
            host=svc.host,
            port=svc.port,
        )
        _registry["instances"][sid] = inst.dict()
        results.append(inst)
    return {"success": True, "data": results}
```

**Go实现**:
```go
// 批量注册请求
type BatchRegisterRequest struct {
    Services []ServiceRegistration `json:"services" binding:"required"`
}

// 批量注册处理器
func (h *Handler) BatchRegister(c *gin.Context) {
    var req BatchRegisterRequest
    if err := c.ShouldBindJSON(&req); err != nil {
        c.JSON(400, gin.H{"error": err.Error()})
        return
    }

    results := make([]*ServiceInstance, 0, len(req.Services))
    for _, svc := range req.Services {
        inst, err := h.registry.Register(svc)
        if err != nil {
            c.JSON(500, gin.H{"error": err.Error()})
            return
        }
        results = append(results, inst)
    }

    c.JSON(200, gin.H{
        "success": true,
        "data": results,
    })
}
```

**迁移目标**: `gateway-unified/internal/handlers/service.go`

**优先级**: P0 (核心功能)

---

#### 3.2 依赖关系管理

**源设计**: `gateway_extended.py`

```python
@gateway_ext.post("/dependencies")
async def set_dependencies(dep: DependencySpec):
    service = dep.service
    _registry["dependencies"].setdefault(service, [])
    for d in dep.depends_on:
        if d not in _registry["dependencies"][service]:
            _registry["dependencies"][service].append(d)
    return {
        "success": True,
        "data": {
            "service": service,
            "dependencies": _registry["dependencies"][service]
        }
    }
```

**Go实现**:
```go
// 依赖规范
type DependencySpec struct {
    Service   string   `json:"service" binding:"required"`
    DependsOn []string `json:"depends_on"`
}

// 设置依赖
func (h *Handler) SetDependencies(c *gin.Context) {
    var req DependencySpec
    if err := c.ShouldBindJSON(&req); err != nil {
        c.JSON(400, gin.H{"error": err.Error()})
        return
    }

    h.registry.SetDependencies(req.Service, req.DependsOn)

    c.JSON(200, gin.H{
        "success": true,
        "data": gin.H{
            "service": req.Service,
            "dependencies": req.DependsOn,
        },
    })
}
```

**迁移目标**: `gateway-unified/internal/handlers/dependency.go`

**优先级**: P1 (重要功能)

---

#### 3.3 动态配置加载

**源设计**: `gateway_extended.py`

```python
@gateway_ext.post("/config/load")
async def load_config(text: str):
    try:
        import yaml
        cfg = yaml.safe_load(text)
    except Exception:
        cfg = json.loads(text)
    return {"success": True, "data": cfg}
```

**Go实现**:
```go
// 动态配置加载
func (h *Handler) LoadConfig(c *gin.Context) {
    var text string
    if err := c.ShouldBindJSON(&text); err != nil {
        c.JSON(400, gin.H{"error": err.Error()})
        return
    }

    // 尝试YAML
    var cfg map[string]interface{}
    if err := yaml.Unmarshal([]byte(text), &cfg); err != nil {
        // 尝试JSON
        if err := json.Unmarshal([]byte(text), &cfg); err != nil {
            c.JSON(400, gin.H{"error": "invalid config format"})
            return
        }
    }

    // 应用配置
    if err := h.config.Reload(cfg); err != nil {
        c.JSON(500, gin.H{"error": err.Error()})
        return
    }

    c.JSON(200, gin.H{
        "success": true,
        "data": cfg,
    })
}
```

**迁移目标**: `gateway-unified/internal/handlers/config.go`

**优先级**: P2 (增强功能)

---

## 🚀 实施计划

### Week 1: 核心功能迁移

**Day 1-2: 可观测性迁移**
- [ ] 创建 `gateway-unified/internal/tracing/` 目录
- [ ] 迁移 OpenTelemetry 追踪代码
- [ ] 集成 Jaeger 追踪
- [ ] 编写追踪测试

**Day 3-4: 监控指标迁移**
- [ ] 创建 `gateway-unified/internal/monitoring/` 目录
- [ ] 迁移 Prometheus 指标采集
- [ ] 增强自定义指标支持
- [ ] 编写指标测试

**Day 5: 日志系统迁移**
- [ ] 创建 `gateway-unified/internal/logging/` 目录
- [ ] 迁移结构化日志代码
- [ ] 集成 zap logger
- [ ] 编写日志测试

### Week 2: 生命周期和API迁移

**Day 1-2: 生命周期管理**
- [ ] 创建 `gateway-unified/internal/lifecycle/` 目录
- [ ] 实现优雅关闭逻辑
- [ ] 集成监控服务关闭
- [ ] 编写生命周期测试

**Day 3-4: API设计迁移**
- [ ] 创建 `gateway-unified/internal/handlers/` 目录
- [ ] 实现批量注册API
- [ ] 实现依赖管理API
- [ ] 编写API测试

**Day 5: 集成测试**
- [ ] 端到端测试
- [ ] 性能基准测试
- [ ] 文档更新

### Week 3: 优化和文档

**Day 1-2: 性能优化**
- [ ] 连接池优化
- [ ] 缓存优化
- [ ] 并发优化

**Day 3-4: 文档完善**
- [ ] API文档
- [ ] 架构文档
- [ ] 部署文档

**Day 5: 验收和发布**
- [ ] 功能验收
- [ ] 性能验收
- [ ] 质量验收
- [ ] 发布准备

---

## 📊 验收标准

### 功能验收

- [ ] OpenTelemetry追踪正常工作
- [ ] Prometheus指标采集完整
- [ ] 结构化日志输出正确
- [ ] 优雅关闭流程正确
- [ ] 批量注册API功能正常
- [ ] 依赖管理API功能正常
- [ ] 动态配置加载功能正常

### 性能验收

- [ ] 追踪开销 <5%
- [ ] 指标采集开销 <2%
- [ ] 日志记录开销 <3%
- [ ] 优雅关闭时间 <30s
- [ ] API响应时间符合标准

### 质量验收

- [ ] 单元测试覆盖率 >80%
- [ ] 集成测试通过
- [ ] 代码审查通过
- [ ] 文档完整

---

## 🔄 迁移流程

1. **分析源代码**: 理解源实现的设计和功能
2. **设计适配方案**: 适配到统一Gateway的架构
3. **编写代码**: 实现迁移功能
4. **编写测试**: 单元测试和集成测试
5. **代码审查**: 团队审查代码质量
6. **集成验证**: 与现有系统集成测试
7. **文档更新**: 更新相关文档
8. **性能验证**: 性能基准测试
9. **发布准备**: 准备发布

---

**责任人**: Athena Gateway团队
**预计完成时间**: 3周
**最后更新**: 2026-02-20
