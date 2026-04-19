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
