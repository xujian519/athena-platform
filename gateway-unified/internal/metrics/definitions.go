// Package metrics - 高级业务指标定义
// 包含认证、限流、代理、熔断器、缓存等业务指标的Prometheus定义
package metrics

import (
	"github.com/prometheus/client_golang/prometheus"
	"github.com/prometheus/client_golang/prometheus/promauto"
)

// 业务指标定义 - 使用promauto自动注册到默认registry

var (
	// ==================== 认证指标 ====================

	// AuthTotal 认证请求总数
	AuthTotal = promauto.NewCounterVec(
		prometheus.CounterOpts{
			Namespace: "athena_gateway",
			Subsystem: "auth",
			Name:      "requests_total",
			Help:      "认证请求总数",
		},
		[]string{"status", "auth_type", "user_type"},
	)

	// AuthDuration 认证处理时间
	AuthDuration = promauto.NewHistogramVec(
		prometheus.HistogramOpts{
			Namespace: "athena_gateway",
			Subsystem: "auth",
			Name:      "duration_seconds",
			Help:      "认证处理时间（秒）",
			Buckets:   []float64{0.001, 0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1},
		},
		[]string{"auth_type"},
	)

	// ==================== 限流指标 ====================

	// RateLimitTotal 限流检查总数
	RateLimitTotal = promauto.NewCounterVec(
		prometheus.CounterOpts{
			Namespace: "athena_gateway",
			Subsystem: "ratelimit",
			Name:      "checks_total",
			Help:      "限流检查总数",
		},
		[]string{"status", "strategy", "key_type"},
	)

	// RateLimitRejected 限流拒绝请求总数
	RateLimitRejected = promauto.NewCounterVec(
		prometheus.CounterOpts{
			Namespace: "athena_gateway",
			Subsystem: "ratelimit",
			Name:      "rejected_total",
			Help:      "限流拒绝请求总数",
		},
		[]string{"strategy", "key_type"},
	)

	// ==================== 代理指标 ====================

	// ProxyTotal 代理请求总数
	ProxyTotal = promauto.NewCounterVec(
		prometheus.CounterOpts{
			Namespace: "athena_gateway",
			Subsystem: "proxy",
			Name:      "requests_total",
			Help:      "代理请求总数",
		},
		[]string{"service", "method", "status"},
	)

	// ProxyDuration 代理请求处理时间
	ProxyDuration = promauto.NewHistogramVec(
		prometheus.HistogramOpts{
			Namespace: "athena_gateway",
			Subsystem: "proxy",
			Name:      "duration_seconds",
			Help:      "代理请求处理时间（秒）",
			Buckets:   []float64{0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1, 2.5, 5, 10},
		},
		[]string{"service", "method"},
	)

	// ProxyRetryTotal 代理重试总数
	ProxyRetryTotal = promauto.NewCounterVec(
		prometheus.CounterOpts{
			Namespace: "athena_gateway",
			Subsystem: "proxy",
			Name:      "retries_total",
			Help:      "代理重试总数",
		},
		[]string{"service", "reason"},
	)

	// ==================== 熔断器指标 ====================

	// CircuitBreakerState 熔断器状态 (0=closed, 1=open, 2=half-open)
	CircuitBreakerState = promauto.NewGaugeVec(
		prometheus.GaugeOpts{
			Namespace: "athena_gateway",
			Subsystem: "circuitbreaker",
			Name:      "state",
			Help:      "熔断器状态 (0=closed, 1=open, 2=half-open)",
		},
		[]string{"service", "breaker_name"},
	)

	// CircuitBreakerRequestsTotal 熔断器请求总数
	CircuitBreakerRequestsTotal = promauto.NewCounterVec(
		prometheus.CounterOpts{
			Namespace: "athena_gateway",
			Subsystem: "circuitbreaker",
			Name:      "requests_total",
			Help:      "经过熔断器的请求总数",
		},
		[]string{"service", "breaker_name", "result"},
	)

	// CircuitBreakerFailuresTotal 熔断器失败总数
	CircuitBreakerFailuresTotal = promauto.NewCounterVec(
		prometheus.CounterOpts{
			Namespace: "athena_gateway",
			Subsystem: "circuitbreaker",
			Name:      "failures_total",
			Help:      "熔断器记录的失败总数",
		},
		[]string{"service", "breaker_name", "reason"},
	)

	// CircuitBreakerRecoveriesTotal 熔断器恢复总数
	CircuitBreakerRecoveriesTotal = promauto.NewCounterVec(
		prometheus.CounterOpts{
			Namespace: "athena_gateway",
			Subsystem: "circuitbreaker",
			Name:      "recoveries_total",
			Help:      "熔断器从打开到半开/关闭的恢复次数",
		},
		[]string{"service", "breaker_name"},
	)

	// ==================== 缓存指标 ====================

	// CacheOperationsTotal 缓存操作总数
	CacheOperationsTotal = promauto.NewCounterVec(
		prometheus.CounterOpts{
			Namespace: "athena_gateway",
			Subsystem: "cache",
			Name:      "operations_total",
			Help:      "缓存操作总数",
		},
		[]string{"operation", "result", "cache_type"},
	)

	// CacheSize 缓存大小（字节）
	CacheSize = promauto.NewGaugeVec(
		prometheus.GaugeOpts{
			Namespace: "athena_gateway",
			Subsystem: "cache",
			Name:      "size_bytes",
			Help:      "缓存大小（字节）",
		},
		[]string{"cache_type"},
	)

	// CacheHitsTotal 缓存命中总数
	CacheHitsTotal = promauto.NewCounterVec(
		prometheus.CounterOpts{
			Namespace: "athena_gateway",
			Subsystem: "cache",
			Name:      "hits_total",
			Help:      "缓存命中总数",
		},
		[]string{"cache_type"},
	)

	// CacheMissesTotal 缓存未命中总数
	CacheMissesTotal = promauto.NewCounterVec(
		prometheus.CounterOpts{
			Namespace: "athena_gateway",
			Subsystem: "cache",
			Name:      "misses_total",
			Help:      "缓存未命中总数",
		},
		[]string{"cache_type"},
	)

	// ==================== 错误指标 ====================

	// ErrorsTotal 错误总数
	ErrorsTotal = promauto.NewCounterVec(
		prometheus.CounterOpts{
			Namespace: "athena_gateway",
			Subsystem: "http",
			Name:      "errors_total",
			Help:      "HTTP错误总数",
		},
		[]string{"method", "path", "status", "error_type", "service"},
	)

	// ==================== 负载均衡指标 ====================

	// LoadBalancerSelectionsTotal 负载均衡选择总数
	LoadBalancerSelectionsTotal = promauto.NewCounterVec(
		prometheus.CounterOpts{
			Namespace: "athena_gateway",
			Subsystem: "loadbalancer",
			Name:      "selections_total",
			Help:      "负载均衡器选择实例总数",
		},
		[]string{"service", "strategy", "instance_id"},
	)

	// LoadBalancerInstanceHealth 实例健康状态
	LoadBalancerInstanceHealth = promauto.NewGaugeVec(
		prometheus.GaugeOpts{
			Namespace: "athena_gateway",
			Subsystem: "loadbalancer",
			Name:      "instance_health",
			Help:      "负载均衡实例健康状态 (0=unhealthy, 1=healthy)",
		},
		[]string{"service", "instance_id"},
	)
)

// RecordAuth 记录认证指标
func RecordAuth(status, authType, userType string, duration float64) {
	AuthTotal.WithLabelValues(status, authType, userType).Inc()
	AuthDuration.WithLabelValues(authType).Observe(duration)
}

// RecordRateLimit 记录限流检查
func RecordRateLimit(status, strategy, keyType string) {
	RateLimitTotal.WithLabelValues(status, strategy, keyType).Inc()
	if status == "rejected" {
		RateLimitRejected.WithLabelValues(strategy, keyType).Inc()
	}
}

// RecordProxy 记录代理请求
func RecordProxy(service, method, status string, duration float64) {
	ProxyTotal.WithLabelValues(service, method, status).Inc()
	ProxyDuration.WithLabelValues(service, method).Observe(duration)
}

// RecordProxyRetry 记录代理重试
func RecordProxyRetry(service, reason string) {
	ProxyRetryTotal.WithLabelValues(service, reason).Inc()
}

// SetCircuitBreakerState 设置熔断器状态
func SetCircuitBreakerState(service, breakerName string, state float64) {
	CircuitBreakerState.WithLabelValues(service, breakerName).Set(state)
}

// RecordCircuitBreakerRequest 记录熔断器请求
func RecordCircuitBreakerRequest(service, breakerName, result string) {
	CircuitBreakerRequestsTotal.WithLabelValues(service, breakerName, result).Inc()
}

// RecordCircuitBreakerFailure 记录熔断器失败
func RecordCircuitBreakerFailure(service, breakerName, reason string) {
	CircuitBreakerFailuresTotal.WithLabelValues(service, breakerName, reason).Inc()
}

// RecordCircuitBreakerRecovery 记录熔断器恢复
func RecordCircuitBreakerRecovery(service, breakerName string) {
	CircuitBreakerRecoveriesTotal.WithLabelValues(service, breakerName).Inc()
}

// RecordCacheOperation 记录缓存操作
func RecordCacheOperation(operation, result, cacheType string) {
	CacheOperationsTotal.WithLabelValues(operation, result, cacheType).Inc()

	// 同时记录命中/未命中
	if operation == "get" {
		if result == "hit" {
			CacheHitsTotal.WithLabelValues(cacheType).Inc()
		} else if result == "miss" {
			CacheMissesTotal.WithLabelValues(cacheType).Inc()
		}
	}
}

// SetCacheSize 设置缓存大小
func SetCacheSize(cacheType string, size float64) {
	CacheSize.WithLabelValues(cacheType).Set(size)
}

// RecordError 记录错误
func RecordError(method, path, status, errorType, service string) {
	ErrorsTotal.WithLabelValues(method, path, status, errorType, service).Inc()
}

// RecordLoadBalancerSelection 记录负载均衡选择
func RecordLoadBalancerSelection(service, strategy, instanceID string) {
	LoadBalancerSelectionsTotal.WithLabelValues(service, strategy, instanceID).Inc()
}

// SetLoadBalancerInstanceHealth 设置实例健康状态
func SetLoadBalancerInstanceHealth(service, instanceID string, healthy float64) {
	LoadBalancerInstanceHealth.WithLabelValues(service, instanceID).Set(healthy)
}
