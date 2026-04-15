package metrics

import (
	"net/http"
	"strconv"
	"sync"
	"time"

	"github.com/prometheus/client_golang/prometheus"
	"github.com/prometheus/client_golang/prometheus/promhttp"
)

// Metrics 指标收集器
type Metrics struct {
	registry prometheus.Gatherer
	registerer prometheus.Registerer

	// HTTP请求指标
	httpRequestsTotal    *prometheus.CounterVec
	httpRequestDuration  *prometheus.HistogramVec
	httpRequestSize      *prometheus.HistogramVec
	httpResponseSize     *prometheus.HistogramVec

	// 服务注册指标
	servicesTotal      prometheus.Gauge
	healthyServices    *prometheus.GaugeVec
	unhealthyServices   *prometheus.GaugeVec

	// 路由指标
	routesTotal        prometheus.Gauge
	routeMatches       *prometheus.CounterVec
	routeMatchDuration *prometheus.HistogramVec

	// 系统指标
	activeConnections   prometheus.Gauge
	checkErrors         *prometheus.CounterVec

	mu sync.RWMutex
}

var (
	// 全局指标实例
	defaultMetrics *Metrics
	once           sync.Once
)

// GetDefault 获取默认指标实例
func GetDefault() *Metrics {
	once.Do(func() {
		registry := prometheus.NewRegistry()
		defaultMetrics = NewWithRegistry(registry)
	})
	return defaultMetrics
}

// NewWithRegistry 使用指定的registry创建指标收集器
func NewWithRegistry(registry *prometheus.Registry) *Metrics {
	m := &Metrics{
		registry: registry,
		registerer: registry,
	}

	// 初始化HTTP请求指标
	m.httpRequestsTotal = prometheus.NewCounterVec(
		prometheus.CounterOpts{
			Name: "gateway_http_requests_total",
			Help: "HTTP请求总数",
		},
		[]string{"method", "path", "status"},
	)

	m.httpRequestDuration = prometheus.NewHistogramVec(
		prometheus.HistogramOpts{
			Name:    "gateway_http_request_duration_seconds",
			Help:    "HTTP请求处理时间",
			Buckets: []float64{0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1, 2.5, 5, 10},
		},
		[]string{"method", "path"},
	)

	m.httpRequestSize = prometheus.NewHistogramVec(
		prometheus.HistogramOpts{
			Name:    "gateway_http_request_size_bytes",
			Help:    "HTTP请求大小",
			Buckets: []float64{100, 1000, 10000, 100000, 1000000, 10000000},
		},
		[]string{"method"},
	)

	m.httpResponseSize = prometheus.NewHistogramVec(
		prometheus.HistogramOpts{
			Name:    "gateway_http_response_size_bytes",
			Help:    "HTTP响应大小",
			Buckets: []float64{100, 1000, 10000, 100000, 1000000, 10000000},
		},
		[]string{"method", "status"},
	)

	// 初始化服务注册指标
	m.servicesTotal = prometheus.NewGauge(
		prometheus.GaugeOpts{
			Name: "gateway_services_total",
			Help: "注册的服务总数",
		},
	)

	m.healthyServices = prometheus.NewGaugeVec(
		prometheus.GaugeOpts{
			Name: "gateway_healthy_services",
			Help: "健康的服务实例数",
		},
		[]string{"service_name"},
	)

	m.unhealthyServices = prometheus.NewGaugeVec(
		prometheus.GaugeOpts{
			Name: "gateway_unhealthy_services",
			Help: "不健康的服务实例数",
		},
		[]string{"service_name"},
	)

	// 初始化路由指标
	m.routesTotal = prometheus.NewGauge(
		prometheus.GaugeOpts{
			Name: "gateway_routes_total",
			Help: "配置的路由总数",
		},
	)

	m.routeMatches = prometheus.NewCounterVec(
		prometheus.CounterOpts{
			Name: "gateway_route_matches_total",
			Help: "路由匹配次数",
		},
		[]string{"route_id", "target_service"},
	)

	m.routeMatchDuration = prometheus.NewHistogramVec(
		prometheus.HistogramOpts{
			Name:    "gateway_route_match_duration_seconds",
			Help:    "路由匹配时间",
			Buckets: []float64{0.001, 0.005, 0.01, 0.025, 0.05, 0.1, 0.25},
		},
		[]string{"matched"},
	)

	// 初始化系统指标
	m.activeConnections = prometheus.NewGauge(
		prometheus.GaugeOpts{
			Name: "gateway_active_connections",
			Help: "当前活动连接数",
		},
	)

	m.checkErrors = prometheus.NewCounterVec(
		prometheus.CounterOpts{
			Name: "gateway_health_check_errors_total",
			Help: "健康检查错误总数",
		},
		[]string{"service_name", "error_type"},
	)

	// 注册所有指标
	m.registerer.MustRegister(
		m.httpRequestsTotal,
		m.httpRequestDuration,
		m.httpRequestSize,
		m.httpResponseSize,
		m.servicesTotal,
		m.healthyServices,
		m.unhealthyServices,
		m.routesTotal,
		m.routeMatches,
		m.routeMatchDuration,
		m.activeConnections,
		m.checkErrors,
	)

	return m
}

// New 创建新的指标收集器（兼容旧代码）
func New(registry *prometheus.Registry) *Metrics {
	return NewWithRegistry(registry)
}

// RecordRequest 记录HTTP请求
func (m *Metrics) RecordRequest(method, path string, status int, duration time.Duration, reqSize, respSize int) {
	statusStr := strconv.Itoa(status)

	m.httpRequestsTotal.WithLabelValues(method, path, statusStr).Inc()
	m.httpRequestDuration.WithLabelValues(method, path).Observe(duration.Seconds())
	m.httpRequestSize.WithLabelValues(method).Observe(float64(reqSize))
	m.httpResponseSize.WithLabelValues(method, statusStr).Observe(float64(respSize))
}

// UpdateServices 更新服务指标
func (m *Metrics) UpdateServices(total int, healthy, unhealthy map[string]int) {
	m.servicesTotal.Set(float64(total))

	for service, count := range healthy {
		m.healthyServices.WithLabelValues(service).Set(float64(count))
	}

	for service, count := range unhealthy {
		m.unhealthyServices.WithLabelValues(service).Set(float64(count))
	}
}

// UpdateRoutes 更新路由指标
func (m *Metrics) UpdateRoutes(total int) {
	m.routesTotal.Set(float64(total))
}

// RecordRouteMatch 记录路由匹配
func (m *Metrics) RecordRouteMatch(routeID, targetService string, matched bool, duration time.Duration) {
	matchedStr := "false"
	if matched {
		matchedStr = "true"
		m.routeMatches.WithLabelValues(routeID, targetService).Inc()
	}
	m.routeMatchDuration.WithLabelValues(matchedStr).Observe(duration.Seconds())
}

// RecordHealthCheckError 记录健康检查错误
func (m *Metrics) RecordHealthCheckError(serviceName, errorType string) {
	m.checkErrors.WithLabelValues(serviceName, errorType).Inc()
}

// IncActiveConnections 增加活动连接数
func (m *Metrics) IncActiveConnections() {
	m.activeConnections.Inc()
}

// DecActiveConnections 减少活动连接数
func (m *Metrics) DecActiveConnections() {
	m.activeConnections.Dec()
}

// Handler 返回Prometheus指标处理器
func (m *Metrics) Handler() http.Handler {
	return promhttp.HandlerFor(m.registry, promhttp.HandlerOpts{})
}

// Middleware HTTP中间件，用于记录请求指标
func (m *Metrics) Middleware(next http.Handler) http.Handler {
	return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		start := time.Now()

		// 包装ResponseWriter以捕获状态码和响应大小
		wrapped := &responseWriter{ResponseWriter: w, status: 200}

		// 增加活动连接
		m.IncActiveConnections()
		defer m.DecActiveConnections()

		// 调用下一个处理器
		next.ServeHTTP(wrapped, r)

		// 记录指标
		duration := time.Since(start)
		reqSize := approximateRequestSize(r)
		respSize := wrapped.size

		m.RecordRequest(
			r.Method,
			r.URL.Path,
			wrapped.status,
			duration,
			reqSize,
			respSize,
		)
	})
}

// responseWriter 包装的ResponseWriter用于捕获状态码和响应大小
type responseWriter struct {
	http.ResponseWriter
	status int
	size   int
}

func (w *responseWriter) WriteHeader(status int) {
	w.status = status
	w.ResponseWriter.WriteHeader(status)
}

func (w *responseWriter) Write(b []byte) (int, error) {
	size, err := w.ResponseWriter.Write(b)
	w.size += size
	return size, err
}

// approximateRequestSize 估算请求大小
func approximateRequestSize(r *http.Request) int {
	size := len(r.URL.Path) + len(r.Method)
	if r.URL.RawQuery != "" {
		size += len(r.URL.RawQuery)
	}
	if r.Header != nil {
		for k, v := range r.Header {
			size += len(k) + len(v)
		}
	}
	if r.Body != nil {
		// 无法读取body，假设0
	}
	return size
}

// RecordRequest 使用默认指标实例记录请求
func RecordRequest(method, path string, status int, duration time.Duration, reqSize, respSize int) {
	GetDefault().RecordRequest(method, path, status, duration, reqSize, respSize)
}

// UpdateServices 使用默认指标实例更新服务指标
func UpdateServices(total int, healthy, unhealthy map[string]int) {
	GetDefault().UpdateServices(total, healthy, unhealthy)
}

// UpdateRoutes 使用默认指标实例更新路由指标
func UpdateRoutes(total int) {
	GetDefault().UpdateRoutes(total)
}

// RecordRouteMatch 使用默认指标实例记录路由匹配
func RecordRouteMatch(routeID, targetService string, matched bool, duration time.Duration) {
	GetDefault().RecordRouteMatch(routeID, targetService, matched, duration)
}

// RecordHealthCheckError 使用默认指标实例记录健康检查错误
func RecordHealthCheckError(serviceName, errorType string) {
	GetDefault().RecordHealthCheckError(serviceName, errorType)
}

// Handler 使用默认指标实例返回处理器
func Handler() http.Handler {
	return GetDefault().Handler()
}
