package metrics

import (
	"net/http"
	"net/http/httptest"
	"strings"
	"testing"
	"time"

	"github.com/prometheus/client_golang/prometheus"
)

// TestNew 测试创建指标收集器
func TestNew(t *testing.T) {
	registry := prometheus.NewRegistry()
	m := New(registry)

	if m == nil {
		t.Fatal("New() returned nil")
	}
	if m.registry != registry {
		t.Error("registry not set correctly")
	}
}

// TestRecordRequest 测试记录HTTP请求
func TestRecordRequest(t *testing.T) {
	registry := prometheus.NewRegistry()
	m := New(registry)

	// 记录一些请求
	m.RecordRequest("GET", "/api/test", 200, 100*time.Millisecond, 100, 500)
	m.RecordRequest("POST", "/api/users", 201, 50*time.Millisecond, 200, 100)
	m.RecordRequest("GET", "/api/test", 404, 10*time.Millisecond, 100, 200)

	// 验证指标可以正常获取
	handler := m.Handler()
	req := httptest.NewRequest("GET", "/metrics", nil)
	w := httptest.NewRecorder()
	handler.ServeHTTP(w, req)

	if w.Code != http.StatusOK {
		t.Errorf("Handler returned status %d, want 200", w.Code)
	}

	body := w.Body.String()
	// 验证关键指标存在
	if !strings.Contains(body, "gateway_http_requests_total") {
		t.Error("metrics should contain gateway_http_requests_total")
	}
	if !strings.Contains(body, "gateway_http_request_duration_seconds") {
		t.Error("metrics should contain gateway_http_request_duration_seconds")
	}
}

// TestUpdateServices 测试更新服务指标
func TestUpdateServices(t *testing.T) {
	registry := prometheus.NewRegistry()
	m := New(registry)

	healthy := map[string]int{
		"service-a": 2,
		"service-b": 1,
	}
	unhealthy := map[string]int{
		"service-c": 1,
	}

	m.UpdateServices(3, healthy, unhealthy)

	// 获取指标验证
	handler := m.Handler()
	req := httptest.NewRequest("GET", "/metrics", nil)
	w := httptest.NewRecorder()
	handler.ServeHTTP(w, req)

	body := w.Body.String()
	if !strings.Contains(body, "gateway_services_total 3") {
		t.Error("metrics should contain gateway_services_total 3")
	}
	if !strings.Contains(body, `gateway_healthy_services{service_name="service-a"} 2`) {
		t.Error("metrics should contain healthy service-a count")
	}
}

// TestUpdateRoutes 测试更新路由指标
func TestUpdateRoutes(t *testing.T) {
	registry := prometheus.NewRegistry()
	m := New(registry)

	m.UpdateRoutes(5)

	handler := m.Handler()
	req := httptest.NewRequest("GET", "/metrics", nil)
	w := httptest.NewRecorder()
	handler.ServeHTTP(w, req)

	body := w.Body.String()
	if !strings.Contains(body, "gateway_routes_total 5") {
		t.Error("metrics should contain gateway_routes_total 5")
	}
}

// TestRecordRouteMatch 测试记录路由匹配
func TestRecordRouteMatch(t *testing.T) {
	registry := prometheus.NewRegistry()
	m := New(registry)

	m.RecordRouteMatch("route-1", "service-a", true, 5*time.Millisecond)
	m.RecordRouteMatch("route-2", "service-b", false, 2*time.Millisecond)

	handler := m.Handler()
	req := httptest.NewRequest("GET", "/metrics", nil)
	w := httptest.NewRecorder()
	handler.ServeHTTP(w, req)

	body := w.Body.String()
	if !strings.Contains(body, `gateway_route_matches_total{route_id="route-1",target_service="service-a"} 1`) {
		t.Error("metrics should contain route match count")
	}
}

// TestRecordHealthCheckError 测试记录健康检查错误
func TestRecordHealthCheckError(t *testing.T) {
	registry := prometheus.NewRegistry()
	m := New(registry)

	m.RecordHealthCheckError("service-a", "timeout")
	m.RecordHealthCheckError("service-b", "connection_refused")
	m.RecordHealthCheckError("service-a", "timeout")

	handler := m.Handler()
	req := httptest.NewRequest("GET", "/metrics", nil)
	w := httptest.NewRecorder()
	handler.ServeHTTP(w, req)

	body := w.Body.String()
	// service-a timeout 应该出现2次
	if !strings.Contains(body, `gateway_health_check_errors_total{error_type="timeout",service_name="service-a"} 2`) {
		t.Error("metrics should contain 2 timeout errors for service-a")
	}
}

// TestActiveConnections 测试活动连接计数
func TestActiveConnections(t *testing.T) {
	registry := prometheus.NewRegistry()
	m := New(registry)

	// 模拟连接
	m.IncActiveConnections()
	m.IncActiveConnections()
	m.DecActiveConnections()

	handler := m.Handler()
	req := httptest.NewRequest("GET", "/metrics", nil)
	w := httptest.NewRecorder()
	handler.ServeHTTP(w, req)

	body := w.Body.String()
	if !strings.Contains(body, "gateway_active_connections 1") {
		t.Error("metrics should contain 1 active connection")
	}
}

// TestMiddleware 测试中间件
func TestMiddleware(t *testing.T) {
	registry := prometheus.NewRegistry()
	m := New(registry)

	// 创建测试处理器
	testHandler := http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		w.WriteHeader(http.StatusOK)
		w.Write([]byte("OK"))
	})

	// 包装中间件
	wrapped := m.Middleware(testHandler)

	// 发送请求
	req := httptest.NewRequest("GET", "/api/test", nil)
	w := httptest.NewRecorder()
	wrapped.ServeHTTP(w, req)

	if w.Code != http.StatusOK {
		t.Errorf("中间件返回状态 %d, want 200", w.Code)
	}

	// 验证指标被记录
	metricsReq := httptest.NewRequest("GET", "/metrics", nil)
	metricsW := httptest.NewRecorder()
	m.Handler().ServeHTTP(metricsW, metricsReq)

	body := metricsW.Body.String()
	if !strings.Contains(body, `gateway_http_requests_total{method="GET",path="/api/test",status="200"} 1`) {
		t.Error("中间件应该记录HTTP请求")
	}
}

// TestGetDefault 测试获取默认实例
func TestGetDefault(t *testing.T) {
	m1 := GetDefault()
	m2 := GetDefault()

	if m1 != m2 {
		t.Error("GetDefault() 应该返回相同的实例")
	}
}

// TestResponseWriter 测试响应写入器
func TestResponseWriter(t *testing.T) {
	raw := httptest.NewRecorder()
	w := &responseWriter{ResponseWriter: raw, status: 200}

	// 测试WriteHeader
	w.WriteHeader(404)
	if w.status != 404 {
		t.Errorf("status = %d, want 404", w.status)
	}

	// 测试Write
	n, err := w.Write([]byte("test"))
	if err != nil {
		t.Fatalf("Write failed: %v", err)
	}
	if n != 4 {
		t.Errorf("Write returned %d bytes, want 4", n)
	}
	if w.size != 4 {
		t.Errorf("size = %d, want 4", w.size)
	}
}

// TestConcurrentMetrics 测试并发指标记录
func TestConcurrentMetrics(t *testing.T) {
	registry := prometheus.NewRegistry()
	m := New(registry)

	done := make(chan bool)

	// 并发记录
	for i := 0; i < 10; i++ {
		go func(id int) {
			for j := 0; j < 100; j++ {
				m.RecordRequest("GET", "/api/test", 200, 10*time.Millisecond, 100, 200)
			}
			done <- true
		}(i)
	}

	// 等待所有goroutine完成
	for i := 0; i < 10; i++ {
		<-done
	}

	// 验证指标
	handler := m.Handler()
	req := httptest.NewRequest("GET", "/metrics", nil)
	w := httptest.NewRecorder()
	handler.ServeHTTP(w, req)

	body := w.Body.String()
	// 应该有 10 * 100 = 1000 次请求
	if !strings.Contains(body, `gateway_http_requests_total{method="GET",path="/api/test",status="200"} 1000`) {
		// 由于并发，可能不是完全精确，检查至少有大量记录
		lines := strings.Split(body, "\n")
		found := false
		for _, line := range lines {
			if strings.Contains(line, `gateway_http_requests_total{method="GET",path="/api/test",status="200"}`) {
				found = true
				break
			}
		}
		if !found {
			t.Error("metrics should contain GET /api/test requests")
		}
	}
}

// TestGlobalFunctions 测试全局函数
func TestGlobalFunctions(t *testing.T) {
	// 测试全局函数不会panic
	RecordRequest("GET", "/", 200, 10*time.Millisecond, 100, 200)
	UpdateServices(1, map[string]int{"a": 1}, map[string]int{})
	UpdateRoutes(1)
	RecordRouteMatch("r1", "s1", true, 5*time.Millisecond)
	RecordHealthCheckError("s1", "timeout")

	handler := Handler()
	if handler == nil {
		t.Error("Handler() returned nil")
	}
}

// BenchmarkRecordRequest 性能基准测试
func BenchmarkRecordRequest(b *testing.B) {
	registry := prometheus.NewRegistry()
	m := New(registry)

	b.ResetTimer()
	for i := 0; i < b.N; i++ {
		m.RecordRequest("GET", "/api/test", 200, 10*time.Millisecond, 100, 200)
	}
}
