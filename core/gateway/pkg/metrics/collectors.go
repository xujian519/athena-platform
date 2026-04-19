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
	var m runtime.MemStats
	runtime.ReadMemStats(&m)

	goGoroutines.Set(float64(runtime.NumGoroutine()))
	goMemory.WithLabelValues("heap").Set(float64(m.HeapInuse))
	goMemory.WithLabelValues("stack").Set(float64(m.StackInuse))
	goMemory.WithLabelValues("sys").Set(float64(m.Sys))

	goGC.WithLabelValues("mark").Observe(float64(m.PauseNs[(m.NumGC+255)%256] / 1000000000))
}

func (c *SystemMetricsCollector) Stop() {
	c.cancel()
}

func RecordHTTPRequest(method, path, status, service, userAgent string, duration time.Duration, reqSize, respSize int64) {
	requestTotal.WithLabelValues(method, path, status, service, userAgent).Inc()
	requestDuration.WithLabelValues(method, path, service).Observe(duration.Seconds())

	if reqSize > 0 {
		requestSize.WithLabelValues(method, path).Observe(float64(reqSize))
	}

	if respSize > 0 {
		responseSize.WithLabelValues(method, path, status).Observe(float64(respSize))
	}

	if isHTTPError(status) {
		errorType := getErrorType(status)
		errorTotal.WithLabelValues(method, path, status, errorType, service).Inc()
	}
}

func RecordAuth(status, authType, userType string, duration time.Duration) {
	authTotal.WithLabelValues(status, authType, userType).Inc()
	authDuration.WithLabelValues(authType).Observe(duration.Seconds())
}

func RecordRateLimit(status, strategy, keyType string) {
	rateLimitTotal.WithLabelValues(status, strategy, keyType).Inc()
}

func RecordProxy(service, method, status string, duration time.Duration) {
	proxyTotal.WithLabelValues(service, method, status).Inc()
	proxyDuration.WithLabelValues(service, method).Observe(duration.Seconds())
}

func RecordProxyRetry(service, reason string) {
	proxyRetryTotal.WithLabelValues(service, reason).Inc()
}

func SetCircuitBreakerState(service, breakerName string, state float64) {
	circuitBreakerState.WithLabelValues(service, breakerName).Set(state)
}

func RecordCacheOperation(operation, result, cacheType string) {
	cacheOperations.WithLabelValues(operation, result, cacheType).Inc()
}

func SetCacheSize(cacheType string, size float64) {
	cacheSize.WithLabelValues(cacheType).Set(size)
}

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
