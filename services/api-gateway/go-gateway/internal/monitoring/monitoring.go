package monitoring

import (
	"context"
	"fmt"
	"net/http"
	"time"

	"athena-gateway/internal/config"
	"athena-gateway/pkg/logger"

	"github.com/prometheus/client_golang/api"
	v1 "github.com/prometheus/client_golang/api/prometheus/v1"
	"github.com/prometheus/client_golang/prometheus"
	"github.com/prometheus/client_golang/prometheus/promhttp"
	"go.uber.org/zap"
)

// MonitoringServer 监控服务器
type MonitoringServer struct {
	config     config.MonitoringConfig
	server     *http.Server
	registry   *prometheus.Registry
	metrics    *Metrics
	promClient api.Client
	promAPI    v1.API
}

// Metrics 监控指标
type Metrics struct {
	// HTTP请求指标
	httpRequestsTotal   *prometheus.CounterVec
	httpRequestDuration *prometheus.HistogramVec
	httpResponseSize    *prometheus.HistogramVec
	requestSize         *prometheus.HistogramVec

	// 服务健康指标
	serviceHealth  *prometheus.GaugeVec
	serviceLatency *prometheus.HistogramVec

	// 认证指标
	authTotal      *prometheus.CounterVec
	authDuration   *prometheus.HistogramVec
	activeSessions *prometheus.GaugeVec

	// 限流指标
	rateLimitTotal *prometheus.CounterVec
	rateLimitHits  *prometheus.CounterVec

	// 数据库指标
	dbConnections   *prometheus.GaugeVec
	dbQueryDuration *prometheus.HistogramVec
	dbErrors        *prometheus.CounterVec

	// 系统指标
	memoryUsage prometheus.Gauge
	cpuUsage    prometheus.Gauge
	goroutines  prometheus.Gauge

	// 网关指标
	proxyLatency   *prometheus.HistogramVec
	proxyErrors    *prometheus.CounterVec
	circuitBreaker *prometheus.GaugeVec
}

// NewMonitoringServer 创建监控服务器
func NewMonitoringServer(cfg config.MonitoringConfig) *MonitoringServer {
	if !cfg.Enabled {
		logger.Info("监控服务已禁用")
		return &MonitoringServer{config: cfg}
	}

	registry := prometheus.NewRegistry()
	metrics := createMetrics(registry)

	// 创建Prometheus客户端
	var promClient api.Client
	var promAPI v1.API
	var err error

	if cfg.MetricsURL != "" {
		promClient, err = api.NewClient(api.Config{
			Address: cfg.MetricsURL,
		})
		if err != nil {
			logger.Error("创建Prometheus客户端失败", zap.Error(err))
		} else {
			promAPI = v1.NewAPI(promClient)
		}
	}

	return &MonitoringServer{
		config:     cfg,
		registry:   registry,
		metrics:    metrics,
		promClient: promClient,
		promAPI:    promAPI,
	}
}

// createMetrics 创建监控指标
func createMetrics(registry *prometheus.Registry) *Metrics {
	metrics := &Metrics{
		// HTTP请求指标
		httpRequestsTotal: prometheus.NewCounterVec(
			prometheus.CounterOpts{
				Name: "gateway_http_requests_total",
				Help: "HTTP请求总数",
			},
			[]string{"method", "path", "status", "user_id"},
		),
		httpRequestDuration: prometheus.NewHistogramVec(
			prometheus.HistogramOpts{
				Name:    "gateway_http_request_duration_seconds",
				Help:    "HTTP请求持续时间",
				Buckets: prometheus.DefBuckets,
			},
			[]string{"method", "path", "status"},
		),
		httpResponseSize: prometheus.NewHistogramVec(
			prometheus.HistogramOpts{
				Name:    "gateway_http_response_size_bytes",
				Help:    "HTTP响应大小",
				Buckets: []float64{100, 1000, 10000, 100000, 1000000},
			},
			[]string{"method", "path"},
		),
		requestSize: prometheus.NewHistogramVec(
			prometheus.HistogramOpts{
				Name:    "gateway_http_request_size_bytes",
				Help:    "HTTP请求大小",
				Buckets: []float64{100, 1000, 10000, 100000, 1000000},
			},
			[]string{"method", "path"},
		),

		// 服务健康指标
		serviceHealth: prometheus.NewGaugeVec(
			prometheus.GaugeOpts{
				Name: "gateway_service_health",
				Help: "服务健康状态 (1=健康, 0=不健康)",
			},
			[]string{"service_name"},
		),
		serviceLatency: prometheus.NewHistogramVec(
			prometheus.HistogramOpts{
				Name:    "gateway_service_latency_seconds",
				Help:    "服务响应延迟",
				Buckets: prometheus.DefBuckets,
			},
			[]string{"service_name"},
		),

		// 认证指标
		authTotal: prometheus.NewCounterVec(
			prometheus.CounterOpts{
				Name: "gateway_auth_total",
				Help: "认证请求总数",
			},
			[]string{"method", "status"},
		),
		authDuration: prometheus.NewHistogramVec(
			prometheus.HistogramOpts{
				Name:    "gateway_auth_duration_seconds",
				Help:    "认证处理时间",
				Buckets: prometheus.DefBuckets,
			},
			[]string{"method"},
		),
		activeSessions: prometheus.NewGaugeVec(
			prometheus.GaugeOpts{
				Name: "gateway_active_sessions",
				Help: "活跃会话数",
			},
			[]string{"user_id"},
		),

		// 限流指标
		rateLimitTotal: prometheus.NewCounterVec(
			prometheus.CounterOpts{
				Name: "gateway_rate_limit_total",
				Help: "限流触发总数",
			},
			[]string{"type", "identifier"},
		),
		rateLimitHits: prometheus.NewCounterVec(
			prometheus.CounterOpts{
				Name: "gateway_rate_limit_hits",
				Help: "限流命中次数",
			},
			[]string{"type", "identifier"},
		),

		// 数据库指标
		dbConnections: prometheus.NewGaugeVec(
			prometheus.GaugeOpts{
				Name: "gateway_db_connections",
				Help: "数据库连接数",
			},
			[]string{"state"}, // idle, in_use, open
		),
		dbQueryDuration: prometheus.NewHistogramVec(
			prometheus.HistogramOpts{
				Name:    "gateway_db_query_duration_seconds",
				Help:    "数据库查询时间",
				Buckets: prometheus.DefBuckets,
			},
			[]string{"operation", "table"},
		),
		dbErrors: prometheus.NewCounterVec(
			prometheus.CounterOpts{
				Name: "gateway_db_errors_total",
				Help: "数据库错误总数",
			},
			[]string{"operation", "error_type"},
		),

		// 系统指标
		memoryUsage: prometheus.NewGauge(
			prometheus.GaugeOpts{
				Name: "gateway_memory_usage_bytes",
				Help: "内存使用量（字节）",
			},
		),
		cpuUsage: prometheus.NewGauge(
			prometheus.GaugeOpts{
				Name: "gateway_cpu_usage_percent",
				Help: "CPU使用率（百分比）",
			},
		),
		goroutines: prometheus.NewGauge(
			prometheus.GaugeOpts{
				Name: "gateway_goroutines",
				Help: "Goroutine数量",
			},
		),

		// 网关指标
		proxyLatency: prometheus.NewHistogramVec(
			prometheus.HistogramOpts{
				Name:    "gateway_proxy_latency_seconds",
				Help:    "代理请求延迟",
				Buckets: prometheus.DefBuckets,
			},
			[]string{"service", "method"},
		),
		proxyErrors: prometheus.NewCounterVec(
			prometheus.CounterOpts{
				Name: "gateway_proxy_errors_total",
				Help: "代理错误总数",
			},
			[]string{"service", "error_type"},
		),
		circuitBreaker: prometheus.NewGaugeVec(
			prometheus.GaugeOpts{
				Name: "gateway_circuit_breaker_state",
				Help: "熔断器状态 (0=关闭, 1=开启, 2=半开)",
			},
			[]string{"service"},
		),
	}

	// 注册所有指标
	registry.MustRegister(
		metrics.httpRequestsTotal,
		metrics.httpRequestDuration,
		metrics.httpResponseSize,
		metrics.requestSize,
		metrics.serviceHealth,
		metrics.serviceLatency,
		metrics.authTotal,
		metrics.authDuration,
		metrics.activeSessions,
		metrics.rateLimitTotal,
		metrics.rateLimitHits,
		metrics.dbConnections,
		metrics.dbQueryDuration,
		metrics.dbErrors,
		metrics.memoryUsage,
		metrics.cpuUsage,
		metrics.goroutines,
		metrics.proxyLatency,
		metrics.proxyErrors,
		metrics.circuitBreaker,
	)

	return metrics
}

// Start 启动监控服务器
func (ms *MonitoringServer) Start() error {
	if !ms.config.Enabled {
		logger.Info("监控服务已禁用，跳过启动")
		return nil
	}

	// 创建HTTP路由
	mux := http.NewServeMux()

	// 指标端点
	mux.Handle(ms.config.Path, promhttp.HandlerFor(ms.registry, promhttp.HandlerOpts{}))

	// 健康检查端点
	mux.HandleFunc("/health", func(w http.ResponseWriter, r *http.Request) {
		w.WriteHeader(http.StatusOK)
		w.Write([]byte("OK"))
	})

	// 创建HTTP服务器
	ms.server = &http.Server{
		Addr:         fmt.Sprintf(":%d", ms.config.Port),
		Handler:      mux,
		ReadTimeout:  10 * time.Second,
		WriteTimeout: 10 * time.Second,
		IdleTimeout:  60 * time.Second,
	}

	logger.Info("监控服务启动",
		zap.Int("port", ms.config.Port),
		zap.String("path", ms.config.Path),
	)

	return ms.server.ListenAndServe()
}

// Stop 停止监控服务器
func (ms *MonitoringServer) Stop() error {
	if ms.server == nil {
		return nil
	}

	ctx, cancel := context.WithTimeout(context.Background(), 30*time.Second)
	defer cancel()

	logger.Info("正在停止监控服务器...")
	return ms.server.Shutdown(ctx)
}

// Shutdown 关闭监控服务器
func (ms *MonitoringServer) Shutdown(ctx context.Context) error {
	if ms.server == nil {
		return nil
	}

	logger.Info("正在关闭监控服务器...")
	return ms.server.Shutdown(ctx)
}

// GetMetrics 获取指标实例
func (ms *MonitoringServer) GetMetrics() *Metrics {
	return ms.metrics
}

// RecordHTTPRequest 记录HTTP请求指标
func (m *Metrics) RecordHTTPRequest(method, path, userID string, statusCode int, duration time.Duration, requestSize, responseSize int64) {
	m.httpRequestsTotal.WithLabelValues(method, path, fmt.Sprintf("%d", statusCode), userID).Inc()
	m.httpRequestDuration.WithLabelValues(method, path, fmt.Sprintf("%d", statusCode)).Observe(duration.Seconds())

	if requestSize > 0 {
		m.requestSize.WithLabelValues(method, path).Observe(float64(requestSize))
	}

	if responseSize > 0 {
		m.httpResponseSize.WithLabelValues(method, path).Observe(float64(responseSize))
	}
}

// RecordServiceHealth 记录服务健康指标
func (m *Metrics) RecordServiceHealth(serviceName string, healthy bool, latency time.Duration) {
	var healthValue float64 = 0
	if healthy {
		healthValue = 1
	}

	m.serviceHealth.WithLabelValues(serviceName).Set(healthValue)
	m.serviceLatency.WithLabelValues(serviceName).Observe(latency.Seconds())
}

// RecordAuth 记录认证指标
func (m *Metrics) RecordAuth(method, status string, duration time.Duration) {
	m.authTotal.WithLabelValues(method, status).Inc()
	m.authDuration.WithLabelValues(method).Observe(duration.Seconds())
}

// UpdateActiveSessions 更新活跃会话数
func (m *Metrics) UpdateActiveSessions(userID string, count float64) {
	m.activeSessions.WithLabelValues(userID).Set(count)
}

// RecordRateLimit 记录限流指标
func (m *Metrics) RecordRateLimit(limitType, identifier string) {
	m.rateLimitTotal.WithLabelValues(limitType, identifier).Inc()
	m.rateLimitHits.WithLabelValues(limitType, identifier).Inc()
}

// UpdateDBConnections 更新数据库连接指标
func (m *Metrics) UpdateDBConnections(state string, count float64) {
	m.dbConnections.WithLabelValues(state).Set(count)
}

// RecordDBQuery 记录数据库查询指标
func (m *Metrics) RecordDBQuery(operation, table string, duration time.Duration) {
	m.dbQueryDuration.WithLabelValues(operation, table).Observe(duration.Seconds())
}

// RecordDBError 记录数据库错误指标
func (m *Metrics) RecordDBError(operation, errorType string) {
	m.dbErrors.WithLabelValues(operation, errorType).Inc()
}

// UpdateSystemMetrics 更新系统指标
func (m *Metrics) UpdateSystemMetrics(memoryBytes, cpuPercent, goroutinesCount float64) {
	m.memoryUsage.Set(memoryBytes)
	m.cpuUsage.Set(cpuPercent)
	m.goroutines.Set(goroutinesCount)
}

// RecordProxyLatency 记录代理延迟
func (m *Metrics) RecordProxyLatency(service, method string, duration time.Duration) {
	m.proxyLatency.WithLabelValues(service, method).Observe(duration.Seconds())
}

// RecordProxyError 记录代理错误
func (m *Metrics) RecordProxyError(service, errorType string) {
	m.proxyErrors.WithLabelValues(service, errorType).Inc()
}

// UpdateCircuitBreaker 更新熔断器状态
func (m *Metrics) UpdateCircuitBreaker(service string, state float64) {
	m.circuitBreaker.WithLabelValues(service).Set(state)
}
