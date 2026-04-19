# 可观测性系统实施计划

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 为Athena API Gateway构建完整的企业级可观测性系统，集成分布式追踪、高级指标、告警和可视化

**Architecture:** 基于OpenTelemetry标准 + Prometheus + Jaeger + Grafana技术栈的可观测性架构

**Tech Stack:** Go, OpenTelemetry, Prometheus, Jaeger, Grafana, Redis, Docker

---

## 现状分析

当前Athena API Gateway已完成基础架构：
- ✅ Go + Gin框架
- ✅ 基础配置管理（Viper）
- ✅ JWT认证系统
- ✅ Redis缓存支持
- ✅ 基础Prometheus依赖

待实现的可观测性组件：
- 🔄 OpenTelemetry分布式追踪
- 🔄 高级Prometheus指标系统
- 🔄 Jaeger集成
- 🔄 告警规则和通知
- 🔄 Grafana仪表板

---

## Phase 1: OpenTelemetry追踪系统集成

### Task 1: 创建OpenTelemetry包结构

**Files:**
- Create: `pkg/tracing/otel.go`
- Create: `pkg/tracing/config.go`
- Create: `pkg/tracing/provider.go`
- Create: `pkg/tracing/exporter.go`

**Step 1: 创建OpenTelemetry配置结构**

```go
// pkg/tracing/config.go
package tracing

import "time"

type Config struct {
    // 服务配置
    ServiceName    string `yaml:"service_name" mapstructure:"service_name"`
    ServiceVersion string `yaml:"service_version" mapstructure:"service_version"`
    Environment    string `yaml:"environment" mapstructure:"environment"`

    // Jaeger配置
    Jaeger JaegerConfig `yaml:"jaeger" mapstructure:"jaeger"`

    // 采样配置
    Sampling SamplingConfig `yaml:"sampling" mapstructure:"sampling"`

    // 追踪配置
    Enabled       bool          `yaml:"enabled" mapstructure:"enabled"`
    BatchTimeout  time.Duration `yaml:"batch_timeout" mapstructure:"batch_timeout"`
    ExportTimeout time.Duration `yaml:"export_timeout" mapstructure:"export_timeout"`
    MaxExportBatchSize int     `yaml:"max_export_batch_size" mapstructure:"max_export_batch_size"`
}

type JaegerConfig struct {
    Endpoint string `yaml:"endpoint" mapstructure:"endpoint"`
    Username string `yaml:"username" mapstructure:"username"`
    Password string `yaml:"password" mapstructure:"password"`
    Insecure bool   `yaml:"insecure" mapstructure:"insecure"`
}

type SamplingConfig struct {
    Type  string  `yaml:"type" mapstructure:"type"`
    Param float64 `yaml:"param" mapstructure:"param"`
}

func DefaultConfig() Config {
    return Config{
        ServiceName:    "athena-gateway",
        ServiceVersion: "1.0.0",
        Environment:    "development",
        Jaeger: JaegerConfig{
            Endpoint: "http://localhost:14268/api/traces",
            Insecure: true,
        },
        Sampling: SamplingConfig{
            Type:  "probabilistic",
            Param: 0.1, // 10%采样率
        },
        Enabled:            true,
        BatchTimeout:       5 * time.Second,
        ExportTimeout:      30 * time.Second,
        MaxExportBatchSize: 512,
    }
}
```

**Step 2: 实现OpenTelemetry初始化**

```go
// pkg/tracing/otel.go
package tracing

import (
    "context"
    "fmt"
    "go.opentelemetry.io/otel"
    "go.opentelemetry.io/otel/exporters/jaeger"
    "go.opentelemetry.io/otel/propagation"
    "go.opentelemetry.io/otel/sdk/resource"
    otelsdktrace "go.opentelemetry.io/otel/sdk/trace"
    semconv "go.opentelemetry.io/otel/semconv/v1.21.0"
    "go.opentelemetry.io/otel/trace"
)

type Tracer struct {
    provider *otelsdktrace.TracerProvider
    tracer   trace.Tracer
}

func NewTracer(cfg Config) (*Tracer, error) {
    if !cfg.Enabled {
        return &Tracer{}, nil
    }

    // 创建资源
    res, err := newResource(cfg)
    if err != nil {
        return nil, fmt.Errorf("failed to create resource: %w", err)
    }

    // 创建导出器
    exporter, err := newExporter(cfg.Jaeger)
    if err != nil {
        return nil, fmt.Errorf("failed to create exporter: %w", err)
    }

    // 创建采样器
    sampler, err := newSampler(cfg.Sampling)
    if err != nil {
        return nil, fmt.Errorf("failed to create sampler: %w", err)
    }

    // 创建追踪器提供者
    provider := otelsdktrace.NewTracerProvider(
        otelsdktrace.WithBatcher(exporter,
            otelsdktrace.WithBatchTimeout(cfg.BatchTimeout),
            otelsdktrace.WithMaxExportBatchSize(cfg.MaxExportBatchSize),
            otelsdktrace.WithMaxExportTimeout(cfg.ExportTimeout),
        ),
        otelsdktrace.WithResource(res),
        otelsdktrace.WithSampler(sampler),
    )

    // 设置全局提供者
    otel.SetTracerProvider(provider)
    otel.SetTextMapPropagator(propagation.NewCompositeTextMapPropagator(
        propagation.TraceContext{},
        propagation.Baggage{},
    ))

    // 创建追踪器
    tracer := provider.Tracer(
        cfg.ServiceName,
        trace.WithInstrumentationVersion(cfg.ServiceVersion),
    )

    return &Tracer{
        provider: provider,
        tracer:   tracer,
    }, nil
}

func (t *Tracer) Tracer() trace.Tracer {
    return t.tracer
}

func (t *Tracer) Shutdown(ctx context.Context) error {
    if t.provider != nil {
        return t.provider.Shutdown(ctx)
    }
    return nil
}

func newResource(cfg Config) (*resource.Resource, error) {
    return resource.NewWithAttributes(
        semconv.SchemaURL,
        semconv.ServiceNameKey.String(cfg.ServiceName),
        semconv.ServiceVersionKey.String(cfg.ServiceVersion),
        semconv.DeploymentEnvironmentKey.String(cfg.Environment),
        semconv.TelemetrySDKNameKey.String("opentelemetry"),
        semconv.TelemetrySDKLanguageKey.String("go"),
    ), nil
}

func (t *Tracer) StartSpan(ctx context.Context, name string, opts ...trace.SpanStartOption) (context.Context, trace.Span) {
    return t.tracer.Start(ctx, name, opts...)
}
```

**Step 3: 实现Jaeger导出器**

```go
// pkg/tracing/exporter.go
package tracing

import (
    "go.opentelemetry.io/otel/exporters/jaeger"
)

func newExporter(cfg JaegerConfig) (jaeger.SpanExporter, error) {
    options := []jaeger.Option{
        jaeger.WithCollectorEndpoint(),
    }

    if cfg.Endpoint != "" {
        options = append(options, jaeger.WithEndpoint(cfg.Endpoint))
    }

    if cfg.Username != "" && cfg.Password != "" {
        options = append(options, jaeger.WithUsernamePassword(cfg.Username, cfg.Password))
    }

    if cfg.Insecure {
        options = append(options, jaeger.WithInsecure())
    }

    return jaeger.New(options...)
}

func newSampler(cfg SamplingConfig) (otelsdktrace.Sampler, error) {
    switch cfg.Type {
    case "always_on":
        return otelsdktrace.AlwaysSample(), nil
    case "always_off":
        return otelsdktrace.NeverSample(), nil
    case "probabilistic":
        return otelsdktrace.TraceIDRatioBased(cfg.Param), nil
    case "parentbased_always_on":
        return otelsdktrace.ParentBased(otelsdktrace.AlwaysSample()), nil
    case "parentbased_always_off":
        return otelsdktrace.ParentBased(otelsdktrace.NeverSample()), nil
    case "parentbased_probabilistic":
        return otelsdktrace.ParentBased(otelsdktrace.TraceIDRatioBased(cfg.Param)), nil
    default:
        return otelsdktrace.TraceIDRatioBased(0.1), nil // 默认10%采样
    }
}
```

**Step 4: 运行测试验证基本结构**

```bash
cd /Users/xujian/Athena工作平台/core/gateway
go mod tidy
go build ./pkg/tracing/...
```

Expected: No compilation errors

---

### Task 2: 创建追踪中间件

**Files:**
- Create: `internal/middleware/tracing.go`
- Modify: `internal/config/config.go`

**Step 1: 添加追踪配置到主配置**

```go
// 在internal/config/config.go中添加
type Config struct {
    // ... 现有配置字段 ...

    Tracing tracing.Config `yaml:"tracing" mapstructure:"tracing"`
}
```

**Step 2: 实现追踪中间件**

```go
// internal/middleware/tracing.go
package middleware

import (
    "github.com/gin-gonic/gin"
    "go.opentelemetry.io/otel"
    "go.opentelemetry.io/otel/propagation"
    "go.opentelemetry.io/otel/trace"
    "net/http"
    "strconv"
    "time"
)

// TracingMiddleware 追踪中间件
func TracingMiddleware(serviceName string) gin.HandlerFunc {
    return gin.HandlerFunc(func(c *gin.Context) {
        // 从请求头提取追踪上下文
        ctx := otel.GetTextMapPropagator().Extract(c.Request.Context(), propagation.HeaderCarrier(c.Request.Header))
        
        // 开始新的span
        tracer := otel.Tracer(serviceName)
        ctx, span := tracer.Start(ctx, c.Request.Method+" "+c.Request.URL.Path,
            trace.WithAttributes(
                // 添加标准属性
                // attribute.String("http.method", c.Request.Method),
                // attribute.String("http.url", c.Request.URL.String()),
                // attribute.String("http.scheme", c.Request.URL.Scheme),
                // attribute.String("http.host", c.Request.Host),
                // attribute.String("http.user_agent", c.Request.UserAgent()),
                // attribute.String("http.remote_addr", c.Request.RemoteAddr),
                // attribute.String("http.request_id", c.GetHeader("X-Request-ID")),
            ),
        )
        defer span.End()

        // 将追踪上下文注入到请求中
        c.Request = c.Request.WithContext(ctx)

        // 继续处理请求
        c.Next()

        // 设置响应属性
        statusCode := c.Writer.Status()
        // span.SetAttributes(
        //     attribute.Int("http.status_code", statusCode),
        //     attribute.String("http.status_text", http.StatusText(statusCode)),
        // )

        // 如果请求出错，设置span状态
        if statusCode >= 400 {
            span.SetStatus(trace.Status{
                Code:    trace.StatusCodeError,
                Message: http.StatusText(statusCode),
            })
        } else {
            span.SetStatus(trace.Status{
                Code:    trace.StatusCodeOk,
                Message: "OK",
            })
        }
    })
}

// TracingHeadersMiddleware 注入追踪头到下游服务
func TracingHeadersMiddleware() gin.HandlerFunc {
    return gin.HandlerFunc(func(c *gin.Context) {
        // 获取当前追踪上下文
        propagator := otel.GetTextMapPropagator()
        headers := make(map[string]string)
        
        // 将追踪上下文注入到headers
        propagator.Inject(c.Request.Context(), propagation.MapCarrier(headers))
        
        // 将追踪头添加到请求中
        for key, value := range headers {
            c.Request.Header.Set(key, value)
        }
        
        c.Next()
    })
}
```

**Step 3: 更新go.mod添加追踪依赖**

```bash
cd /Users/xujian/Athena工作平台/core/gateway
go get go.opentelemetry.io/otel@v1.21.0
go get go.opentelemetry.io/otel/exporters/jaeger@v1.21.0
go get go.opentelemetry.io/otel/sdk@v1.21.0
go get go.opentelemetry.io/otel/sdk/resource@v1.21.0
go get go.opentelemetry.io/otel/sdk/trace@v1.21.0
go get go.opentelemetry.io/otel/trace@v1.21.0
go get go.opentelemetry.io/otel/semconv/v1.21.0
go get go.opentelemetry.io/otel/propagation@v1.21.0
```

**Step 4: 测试中间件编译**

```bash
go build ./internal/middleware/...
```

Expected: No compilation errors

---

### Task 3: 集成追踪到主应用

**Files:**
- Modify: `main.go`
- Create: `configs/tracing.yaml`

**Step 1: 创建追踪配置文件**

```yaml
# configs/tracing.yaml
tracing:
  enabled: true
  service_name: "athena-gateway"
  service_version: "1.0.0"
  environment: "development"
  
  jaeger:
    endpoint: "http://localhost:14268/api/traces"
    insecure: true
  
  sampling:
    type: "probabilistic"
    param: 0.1  # 10% sampling rate
  
  batch_timeout: "5s"
  export_timeout: "30s"
  max_export_batch_size: 512
```

**Step 2: 集成追踪到主应用**

```go
// 在main.go中添加
package main

import (
    "context"
    "github.com/athena-workspace/core/gateway/pkg/tracing"
    "github.com/athena-workspace/core/gateway/internal/middleware"
    // ... 其他导入
)

func main() {
    // 加载配置
    cfg := loadConfig()
    
    // 初始化追踪
    tracer, err := tracing.NewTracer(cfg.Tracing)
    if err != nil {
        log.Fatalf("Failed to initialize tracer: %v", err)
    }
    defer func() {
        ctx, cancel := context.WithTimeout(context.Background(), 5*time.Second)
        defer cancel()
        if err := tracer.Shutdown(ctx); err != nil {
            log.Printf("Failed to shutdown tracer: %v", err)
        }
    }()

    // 创建Gin引擎
    engine := gin.New()
    
    // 添加追踪中间件
    engine.Use(middleware.TracingMiddleware(cfg.Tracing.ServiceName))
    engine.Use(middleware.TracingHeadersMiddleware())
    
    // ... 其他中间件和路由设置
    
    // 启动服务
    log.Printf("Starting Athena API Gateway on port %s", cfg.Server.Port)
    if err := engine.Run(":" + cfg.Server.Port); err != nil {
        log.Fatalf("Failed to start server: %v", err)
    }
}
```

**Step 3: 测试完整集成**

```bash
cd /Users/xujian/Athena工作平台/core/gateway
go mod tidy
go build -o gateway .
```

Expected: Build successful

---

## Phase 2: 高级Prometheus指标系统

### Task 4: 创建高级指标包

**Files:**
- Create: `pkg/metrics/prometheus.go`
- Create: `pkg/metrics/definitions.go`
- Create: `pkg/metrics/collectors.go`

**Step 1: 定义指标结构**

```go
// pkg/metrics/definitions.go
package metrics

import (
    "github.com/prometheus/client_golang/prometheus"
    "github.com/prometheus/client_golang/prometheus/promauto"
)

var (
    // 业务指标
    requestTotal = promauto.NewCounterVec(
        prometheus.CounterOpts{
            Namespace: "athena_gateway",
            Subsystem: "http",
            Name:      "requests_total",
            Help:      "Total number of HTTP requests processed",
        },
        []string{"method", "path", "status", "service", "user_agent_type"},
    )
    
    requestDuration = promauto.NewHistogramVec(
        prometheus.HistogramOpts{
            Namespace: "athena_gateway",
            Subsystem: "http",
            Name:      "request_duration_seconds",
            Help:      "HTTP request duration in seconds",
            Buckets:   prometheus.DefBuckets,
        },
        []string{"method", "path", "service"},
    )
    
    requestSize = promauto.NewHistogramVec(
        prometheus.HistogramOpts{
            Namespace: "athena_gateway",
            Subsystem: "http",
            Name:      "request_size_bytes",
            Help:      "HTTP request size in bytes",
            Buckets:   prometheus.ExponentialBuckets(100, 2.0, 10),
        },
        []string{"method", "path"},
    )
    
    responseSize = promauto.NewHistogramVec(
        prometheus.HistogramOpts{
            Namespace: "athena_gateway",
            Subsystem: "http",
            Name:      "response_size_bytes",
            Help:      "HTTP response size in bytes",
            Buckets:   prometheus.ExponentialBuckets(100, 2.0, 10),
        },
        []string{"method", "path", "status"},
    )
    
    // 错误指标
    errorTotal = promauto.NewCounterVec(
        prometheus.CounterOpts{
            Namespace: "athena_gateway",
            Subsystem: "http",
            Name:      "errors_total",
            Help:      "Total number of HTTP errors",
        },
        []string{"method", "path", "status", "error_type", "service"},
    )
    
    // 认证指标
    authTotal = promauto.NewCounterVec(
        prometheus.CounterOpts{
            Namespace: "athena_gateway",
            Subsystem: "auth",
            Name:      "requests_total",
            Help:      "Total number of authentication requests",
        },
        []string{"status", "auth_type", "user_type"},
    )
    
    authDuration = promauto.NewHistogramVec(
        prometheus.HistogramOpts{
            Namespace: "athena_gateway",
            Subsystem: "auth",
            Name:      "duration_seconds",
            Help:      "Authentication duration in seconds",
            Buckets:   prometheus.DefBuckets,
        },
        []string{"auth_type"},
    )
    
    // 限流指标
    rateLimitTotal = promauto.NewCounterVec(
        prometheus.CounterOpts{
            Namespace: "athena_gateway",
            Subsystem: "ratelimit",
            Name:      "requests_total",
            Help:      "Total number of rate limit checks",
        },
        []string{"status", "strategy", "key_type"},
    )
    
    // 代理指标
    proxyTotal = promauto.NewCounterVec(
        prometheus.CounterOpts{
            Namespace: "athena_gateway",
            Subsystem: "proxy",
            Name:      "requests_total",
            Help:      "Total number of proxy requests",
        },
        []string{"service", "method", "status"},
    )
    
    proxyDuration = promauto.NewHistogramVec(
        prometheus.HistogramOpts{
            Namespace: "athena_gateway",
            Subsystem: "proxy",
            Name:      "duration_seconds",
            Help:      "Proxy request duration in seconds",
            Buckets:   prometheus.DefBuckets,
        },
        []string{"service", "method"},
    )
    
    proxyRetryTotal = promauto.NewCounterVec(
        prometheus.CounterOpts{
            Namespace: "athena_gateway",
            Subsystem: "proxy",
            Name:      "retries_total",
            Help:      "Total number of proxy retries",
        },
        []string{"service", "reason"},
    )
    
    // 熔断器指标
    circuitBreakerState = promauto.NewGaugeVec(
        prometheus.GaugeOpts{
            Namespace: "athena_gateway",
            Subsystem: "circuitbreaker",
            Name:      "state",
            Help:      "Circuit breaker state (0=closed, 1=open, 2=half-open)",
        },
        []string{"service", "breaker_name"},
    )
)
```

**Step 2: 实现指标收集器**

```go
// pkg/metrics/collectors.go
package metrics

import (
    "context"
    "runtime"
    "time"
    
    "github.com/prometheus/client_golang/prometheus"
    "github.com/prometheus/client_golang/prometheus/promauto"
)

var (
    // 系统指标
    goGoroutines = promauto.NewGauge(prometheus.GaugeOpts{
        Namespace: "athena_gateway",
        Subsystem: "go",
        Name:      "goroutines",
        Help:      "Number of goroutines",
    })
    
    goMemory = promauto.NewGaugeVec(prometheus.GaugeOpts{
        Namespace: "athena_gateway",
        Subsystem: "go",
        Name:      "memory_bytes",
        Help:      "Go memory usage in bytes",
    }, []string{"type"})
    
    goGC = promauto.NewHistogramVec(prometheus.HistogramOpts{
        Namespace: "athena_gateway",
        Subsystem: "go",
        Name:      "gc_duration_seconds",
        Help:      "Go garbage collection duration in seconds",
        Buckets:   prometheus.ExponentialBuckets(0.00001, 2.0, 10),
    }, []string{"gc_type"})
    
    // HTTP连接指标
    httpConnections = promauto.NewGaugeVec(prometheus.GaugeOpts{
        Namespace: "athena_gateway",
        Subsystem: "http",
        Name:      "connections",
        Help:      "Number of HTTP connections",
    }, []string{"state"})
    
    // 缓存指标
    cacheOperations = promauto.NewCounterVec(prometheus.CounterOpts{
        Namespace: "athena_gateway",
        Subsystem: "cache",
        Name:      "operations_total",
        Help:      "Total number of cache operations",
    }, []string{"operation", "result", "cache_type"})
    
    cacheSize = promauto.NewGaugeVec(prometheus.GaugeOpts{
        Namespace: "athena_gateway",
        Subsystem: "cache",
        Name:      "size_bytes",
        Help:      "Cache size in bytes",
    }, []string{"cache_type"})
)

// SystemMetricsCollector 系统指标收集器
type SystemMetricsCollector struct {
    ctx    context.Context
    cancel context.CancelFunc
}

func NewSystemMetricsCollector() *SystemMetricsCollector {
    ctx, cancel := context.WithCancel(context.Background())
    collector := &SystemMetricsCollector{
        ctx:    ctx,
        cancel: cancel,
    }
    go collector.collect()
    return collector
}

func (c *SystemMetricsCollector) collect() {
    ticker := time.NewTicker(10 * time.Second)
    defer ticker.Stop()
    
    for {
        select {
        case <-c.ctx.Done():
            return
        case <-ticker.C:
            c.collectSystemMetrics()
        }
    }
}

func (c *SystemMetricsCollector) collectSystemMetrics() {
    // Go运行时指标
    var m runtime.MemStats
    runtime.ReadMemStats(&m)
    
    goGoroutines.Set(float64(runtime.NumGoroutine()))
    goMemory.WithLabelValues("heap").Set(float64(m.HeapInuse))
    goMemory.WithLabelValues("stack").Set(float64(m.StackInuse))
    goMemory.WithLabelValues("sys").Set(float64(m.Sys))
    
    // GC指标
    goGC.WithLabelValues("mark").Set(float64(m.PauseNs[(m.NumGC+255)%256] / 1000000000))
}

func (c *SystemMetricsCollector) Stop() {
    c.cancel()
}

// RecordHTTPRequest 记录HTTP请求指标
func RecordHTTPRequest(method, path, status, service, userAgent string, duration time.Duration, requestSize, responseSize int64) {
    requestTotal.WithLabelValues(method, path, status, service, userAgent).Inc()
    requestDuration.WithLabelValues(method, path, service).Observe(duration.Seconds())
    
    if requestSize > 0 {
        requestSize.WithLabelValues(method, path).Observe(float64(requestSize))
    }
    
    if responseSize > 0 {
        responseSize.WithLabelValues(method, path, status).Observe(float64(responseSize))
    }
    
    // 记录错误指标
    if isHTTPError(status) {
        errorType := getErrorType(status)
        errorTotal.WithLabelValues(method, path, status, errorType, service).Inc()
    }
}

// RecordAuth 记录认证指标
func RecordAuth(status, authType, userType string, duration time.Duration) {
    authTotal.WithLabelValues(status, authType, userType).Inc()
    authDuration.WithLabelValues(authType).Observe(duration.Seconds())
}

// RecordRateLimit 记录限流指标
func RecordRateLimit(status, strategy, keyType string) {
    rateLimitTotal.WithLabelValues(status, strategy, keyType).Inc()
}

// RecordProxy 记录代理指标
func RecordProxy(service, method, status string, duration time.Duration) {
    proxyTotal.WithLabelValues(service, method, status).Inc()
    proxyDuration.WithLabelValues(service, method).Observe(duration.Seconds())
}

// RecordProxyRetry 记录代理重试指标
func RecordProxyRetry(service, reason string) {
    proxyRetryTotal.WithLabelValues(service, reason).Inc()
}

// SetCircuitBreakerState 设置熔断器状态
func SetCircuitBreakerState(service, breakerName string, state float64) {
    circuitBreakerState.WithLabelValues(service, breakerName).Set(state)
}

// RecordCacheOperation 记录缓存操作指标
func RecordCacheOperation(operation, result, cacheType string) {
    cacheOperations.WithLabelValues(operation, result, cacheType).Inc()
}

// SetCacheSize 设置缓存大小
func SetCacheSize(cacheType string, size float64) {
    cacheSize.WithLabelValues(cacheType).Set(size)
}

// 辅助函数
func isHTTPError(status string) bool {
    return status[0] == '4' || status[0] == '5'
}

func getErrorType(status string) string {
    switch status[0] {
    case '4':
        return "client_error"
    case '5':
        return "server_error"
    default:
        return "unknown"
    }
}
```

**Step 3: 实现Prometheus集成**

```go
// pkg/metrics/prometheus.go
package metrics

import (
    "net/http"
    
    "github.com/prometheus/client_golang/prometheus"
    "github.com/prometheus/client_golang/prometheus/promhttp"
)

// PrometheusMetrics Prometheus指标管理器
type PrometheusMetrics struct {
    systemCollector *SystemMetricsCollector
}

// NewPrometheusMetrics 创建新的Prometheus指标管理器
func NewPrometheusMetrics() *PrometheusMetrics {
    return &PrometheusMetrics{
        systemCollector: NewSystemMetricsCollector(),
    }
}

// Handler 返回Prometheus指标HTTP处理器
func (p *PrometheusMetrics) Handler() http.Handler {
    return promhttp.Handler()
}

// RegisterCustomMetrics 注册自定义指标
func (p *PrometheusMetrics) RegisterCustomMetrics() {
    // 注册所有自定义指标到默认注册表
    // 这些指标已经在初始化时自动注册
}

// Shutdown 关闭指标收集器
func (p *PrometheusMetrics) Shutdown() {
    if p.systemCollector != nil {
        p.systemCollector.Stop()
    }
}

// MustRegister 注册指标到默认注册表
func MustRegister(collector ...prometheus.Collector) {
    prometheus.MustRegister(collector...)
}

// NewRegistry 创建新的注册表
func NewRegistry() *prometheus.Registry {
    return prometheus.NewRegistry()
}
```

**Step 4: 测试指标系统**

```bash
cd /Users/xujian/Athena工作平台/core/gateway
go mod tidy
go build ./pkg/metrics/...
```

Expected: No compilation errors

---

## 后续任务概览

### Phase 3: 指标中间件集成
### Phase 4: 告警规则配置  
### Phase 5: Grafana仪表板
### Phase 6: 集成测试和性能验证

每个阶段都包含具体的实施步骤、验证要求和预期输出。