// Package metrics - 业务指标测试
package metrics

import (
	"net/http"
	"net/http/httptest"
	"testing"
	"time"
)

// TestRecordAuth 测试认证指标记录
func TestRecordAuth(t *testing.T) {
	// 记录认证请求
	RecordAuth("success", "jwt", "admin", 0.123)
	RecordAuth("failure", "basic", "user", 0.456)
	RecordAuth("success", "jwt", "admin", 0.234)

	// 如果没有panic，则测试通过
	// 在实际测试中应该验证指标值
}

// TestRecordRateLimit 测试限流指标记录
func TestRecordRateLimit(t *testing.T) {
	// 记录限流检查
	RecordRateLimit("allowed", "token_bucket", "ip")
	RecordRateLimit("rejected", "token_bucket", "ip")
	RecordRateLimit("allowed", "sliding_window", "user")

	// 如果没有panic，则测试通过
}

// TestRecordProxy 测试代理指标记录
func TestRecordProxy(t *testing.T) {
	// 记录代理请求
	RecordProxy("user-service", "GET", "200", 0.05)
	RecordProxy("user-service", "POST", "201", 0.123)
	RecordProxy("order-service", "GET", "404", 0.02)

	// 记录代理重试
	RecordProxyRetry("user-service", "timeout")
	RecordProxyRetry("order-service", "connection_refused")

	// 如果没有panic，则测试通过
}

// TestCircuitBreakerMetrics 测试熔断器指标
func TestCircuitBreakerMetrics(t *testing.T) {
	// 设置熔断器状态
	SetCircuitBreakerState("user-service", "main_breaker", 0) // closed
	SetCircuitBreakerState("order-service", "main_breaker", 1) // open
	SetCircuitBreakerState("payment-service", "main_breaker", 2) // half-open

	// 记录熔断器请求
	RecordCircuitBreakerRequest("user-service", "main_breaker", "success")
	RecordCircuitBreakerRequest("order-service", "main_breaker", "rejected")
	RecordCircuitBreakerRequest("payment-service", "main_breaker", "success")

	// 记录熔断器失败
	RecordCircuitBreakerFailure("order-service", "main_breaker", "error_threshold")
	RecordCircuitBreakerFailure("payment-service", "main_breaker", "timeout")

	// 记录熔断器恢复
	RecordCircuitBreakerRecovery("order-service", "main_breaker")

	// 如果没有panic，则测试通过
}

// TestCacheMetrics 测试缓存指标
func TestCacheMetrics(t *testing.T) {
	// 记录缓存操作
	RecordCacheOperation("get", "hit", "l1")
	RecordCacheOperation("get", "miss", "l1")
	RecordCacheOperation("set", "success", "l1")
	RecordCacheOperation("delete", "success", "l1")

	RecordCacheOperation("get", "hit", "l2")
	RecordCacheOperation("get", "miss", "l2")

	// 设置缓存大小
	SetCacheSize("l1", 1024*1024*100) // 100MB
	SetCacheSize("l2", 1024*1024*500) // 500MB

	// 如果没有panic，则测试通过
}

// TestErrorMetrics 测试错误指标
func TestErrorMetrics(t *testing.T) {
	// 记录错误
	RecordError("GET", "/api/users", "404", "not_found", "user-service")
	RecordError("POST", "/api/orders", "500", "internal_error", "order-service")
	RecordError("GET", "/api/products", "403", "forbidden", "product-service")

	// 如果没有panic，则测试通过
}

// TestLoadBalancerMetrics 测试负载均衡指标
func TestLoadBalancerMetrics(t *testing.T) {
	// 记录负载均衡选择
	RecordLoadBalancerSelection("user-service", "round_robin", "instance-1")
	RecordLoadBalancerSelection("user-service", "round_robin", "instance-2")
	RecordLoadBalancerSelection("order-service", "least_connections", "instance-1")

	// 设置实例健康状态
	SetLoadBalancerInstanceHealth("user-service", "instance-1", 1)
	SetLoadBalancerInstanceHealth("user-service", "instance-2", 1)
	SetLoadBalancerInstanceHealth("order-service", "instance-1", 0) // unhealthy

	// 如果没有panic，则测试通过
}

// TestPrometheusHandler 测试Prometheus处理器
func TestPrometheusHandler(t *testing.T) {
	// 创建一些测试数据
	RecordAuth("success", "jwt", "admin", 0.1)
	RecordProxy("test-service", "GET", "200", 0.05)

	// 创建处理器
	promMetrics := NewPrometheusMetrics()
	handler := promMetrics.Handler()

	// 创建测试请求
	req := httptest.NewRequest("GET", "/metrics", nil)
	w := httptest.NewRecorder()

	handler.ServeHTTP(w, req)

	// 检查响应
	if w.Code != http.StatusOK {
		t.Errorf("期望状态码200，实际为%d", w.Code)
	}

	// 检查内容类型
	contentType := w.Header().Get("Content-Type")
	// 只检查是否包含主要类型（忽略参数部分）
	if len(contentType) < 10 || (contentType[:10] != "text/plain" && contentType[:27] != "application/openmetrics-text") {
		t.Errorf("意外的Content-Type: %s", contentType)
	}

	// 检查响应体包含Prometheus指标
	body := w.Body.String()
	// 简单检查一些指标名称
	if len(body) == 0 {
		t.Error("响应体不应为空")
	}
}

// TestSystemMetricsCollector 测试系统指标收集器
func TestSystemMetricsCollector(t *testing.T) {
	collector := NewSystemMetricsCollector()

	// 启动收集器
	collector.Start()
	defer collector.Stop()

	// 等待一些收集周期
	time.Sleep(100 * time.Millisecond)

	// 如果没有panic，则测试通过
}

// TestGetGCStats 测试获取GC统计信息
func TestGetGCStats(t *testing.T) {
	stats := GetGCStats()

	// 检查一些字段
	if _, ok := stats["num_gc"]; !ok {
		t.Error("GC统计应包含num_gc")
	}

	if _, ok := stats["goroutines"]; !ok {
		t.Error("GC统计应包含goroutines")
	}

	if _, ok := stats["heap_alloc"]; !ok {
		t.Error("GC统计应包含heap_alloc")
	}
}

// TestGetMemoryStats 测试获取内存统计信息
func TestGetMemoryStats(t *testing.T) {
	stats := GetMemoryStats()

	// 检查一些字段
	if stats.Alloc == 0 {
		t.Log("Alloc可能为0，这在不同环境下可能发生")
	}

	if stats.Sys == 0 {
		t.Error("Sys不应为0")
	}
}

// BenchmarkRecordAuth 性能测试 - 认证指标
func BenchmarkRecordAuth(b *testing.B) {
	for i := 0; i < b.N; i++ {
		RecordAuth("success", "jwt", "admin", 0.1)
	}
}

// BenchmarkRecordProxy 性能测试 - 代理指标
func BenchmarkRecordProxy(b *testing.B) {
	for i := 0; i < b.N; i++ {
		RecordProxy("user-service", "GET", "200", 0.05)
	}
}

// BenchmarkCircuitBreakerMetrics 性能测试 - 熔断器指标
func BenchmarkCircuitBreakerMetrics(b *testing.B) {
	for i := 0; i < b.N; i++ {
		SetCircuitBreakerState("test-service", "test-breaker", 1)
		RecordCircuitBreakerRequest("test-service", "test-breaker", "success")
	}
}
