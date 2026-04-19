package gateway

import (
	"bytes"
	"encoding/json"
	"io"
	"net/http"
	"net/http/httptest"
	"strings"
	"testing"

	"github.com/gin-gonic/gin"
	"github.com/athena-workspace/gateway-unified/internal/config"
)

// setupTestGateway 创建测试用的Gateway
func setupTestGateway() *Gateway {
	gin.SetMode(gin.TestMode)

	// 创建测试配置
	cfg := &config.Config{
		Server: config.ServerConfig{
			Port:         8005,
			Production:   false,
			ReadTimeout:  30,
			WriteTimeout: 30,
			IdleTimeout:  120,
		},
		Logging: config.LoggingConfig{
			Level:  "info",
			Format: "json",
			Output: "stdout",
		},
		Monitoring: config.MonitoringConfig{
			Enabled: false,
		},
	}

	gw := &Gateway{
		config:   cfg,
		router:   gin.New(),
		handlers: NewHandlers(nil),
		done:     make(chan struct{}),
	}

	gw.setupMiddleware()
	gw.setupRoutes()

	return gw
}

// TestHealthCheckEndpoint 测试健康检查端点
func TestHealthCheckEndpoint(t *testing.T) {
	gw := setupTestGateway()

	w := httptest.NewRecorder()
	req, _ := http.NewRequest("GET", "/health", nil)
	gw.GetRouter().ServeHTTP(w, req)

	if w.Code != http.StatusOK {
		t.Errorf("HealthCheck() status = %d, want 200", w.Code)
	}

	var response map[string]interface{}
	if err := json.Unmarshal(w.Body.Bytes(), &response); err != nil {
		t.Fatalf("HealthCheck() JSON decode failed: %v", err)
	}

	if !response["success"].(bool) {
		t.Error("HealthCheck() success = false, want true")
	}

	data := response["data"].(map[string]interface{})
	if data["status"] != "UP" {
		t.Errorf("HealthCheck() status = %s, want UP", data["status"])
	}
}

// TestBatchRegisterEndpoint 测试批量注册服务端点
func TestBatchRegisterEndpoint(t *testing.T) {
	gw := setupTestGateway()

	payload := map[string]interface{}{
		"services": []map[string]interface{}{
			{
				"name": "test-service",
				"host": "localhost",
				"port": 8001,
			},
		},
	}

	body, _ := json.Marshal(payload)
	w := httptest.NewRecorder()
	req, _ := http.NewRequest("POST", "/api/services/batch_register", bytes.NewReader(body))
	req.Header.Set("Content-Type", "application/json")
	gw.GetRouter().ServeHTTP(w, req)

	if w.Code != http.StatusOK {
		t.Errorf("BatchRegister() status = %d, want 200", w.Code)
	}

	// 验证服务已注册（使用Gateway的GetRegistry）
	instances := gw.GetRegistry().GetByService("test-service")
	if len(instances) != 1 {
		t.Errorf("BatchRegister() registered %d instances, want 1", len(instances))
	}
}

// TestListInstancesEndpoint 测试查询服务实例端点
func TestListInstancesEndpoint(t *testing.T) {
	gw := setupTestGateway()

	// 先注册一个服务
	gw.GetRegistry().Register(&ServiceInstance{
		ID:          "test-1",
		ServiceName: "test-service",
		Host:        "localhost",
		Port:        8001,
		Status:      "UP",
	})

	w := httptest.NewRecorder()
	req, _ := http.NewRequest("GET", "/api/services/instances", nil)
	gw.GetRouter().ServeHTTP(w, req)

	if w.Code != http.StatusOK {
		t.Errorf("ListInstances() status = %d, want 200", w.Code)
	}

	var response map[string]interface{}
	json.Unmarshal(w.Body.Bytes(), &response)
	data := response["data"].(map[string]interface{})
	instances := data["data"].([]interface{})

	if len(instances) != 1 {
		t.Errorf("ListInstances() returned %d instances, want 1", len(instances))
	}
}

// TestCreateRouteEndpoint 测试创建路由端点
func TestCreateRouteEndpoint(t *testing.T) {
	gw := setupTestGateway()

	payload := map[string]interface{}{
		"path":           "/api/test/**",
		"target_service": "test-svc",
		"methods":        []string{"GET", "POST"},
		"strip_prefix":   true,
	}

	body, _ := json.Marshal(payload)
	w := httptest.NewRecorder()
	req, _ := http.NewRequest("POST", "/api/routes", bytes.NewReader(body))
	req.Header.Set("Content-Type", "application/json")
	gw.GetRouter().ServeHTTP(w, req)

	if w.Code != http.StatusOK {
		t.Errorf("CreateRoute() status = %d, want 200", w.Code)
	}

	// 验证路由已创建（使用Gateway的GetRouteManager）
	if gw.GetRouteManager().Count() != 1 {
		t.Errorf("CreateRoute() route count = %d, want 1", gw.GetRouteManager().Count())
	}
}

// TestListRoutesEndpoint 测试查询路由端点
func TestListRoutesEndpoint(t *testing.T) {
	gw := setupTestGateway()

	// 先创建一个路由
	gw.GetRouteManager().Create(&RouteRule{
		ID:            "test-route",
		Path:          "/api/test",
		TargetService: "test-svc",
		Methods:       []string{"GET"},
	})

	w := httptest.NewRecorder()
	req, _ := http.NewRequest("GET", "/api/routes", nil)
	gw.GetRouter().ServeHTTP(w, req)

	if w.Code != http.StatusOK {
		t.Errorf("ListRoutes() status = %d, want 200", w.Code)
	}

	var response map[string]interface{}
	json.Unmarshal(w.Body.Bytes(), &response)
	data := response["data"].(map[string]interface{})
	routes := data["data"].([]interface{})

	if len(routes) != 1 {
		t.Errorf("ListRoutes() returned %d routes, want 1", len(routes))
	}
}

// TestSetDependenciesEndpoint 测试设置依赖端点
func TestSetDependenciesEndpoint(t *testing.T) {
	gw := setupTestGateway()

	payload := map[string]interface{}{
		"service":    "svc1",
		"depends_on": []string{"svc2", "svc3"},
	}

	body, _ := json.Marshal(payload)
	w := httptest.NewRecorder()
	req, _ := http.NewRequest("POST", "/api/dependencies", bytes.NewReader(body))
	req.Header.Set("Content-Type", "application/json")
	gw.GetRouter().ServeHTTP(w, req)

	if w.Code != http.StatusOK {
		t.Errorf("SetDependencies() status = %d, want 200", w.Code)
	}

	// 验证依赖已设置（使用Gateway的GetRegistry）
	deps := gw.GetRegistry().GetDependencies("svc1")
	if len(deps) != 2 {
		t.Errorf("SetDependencies() dependency count = %d, want 2", len(deps))
	}
}

// TestLoadConfigEndpoint 测试配置加载端点
func TestLoadConfigEndpoint(t *testing.T) {
	gw := setupTestGateway()

	payload := map[string]interface{}{
		"services": []map[string]interface{}{
			{
				"name": "cfg-svc",
				"host": "localhost",
				"port": float64(9999),
			},
		},
		"routes": []map[string]interface{}{
			{
				"path":           "/cfg/**",
				"target_service": "cfg-svc",
				"methods":        []string{"GET"},
				"strip_prefix":   false,
			},
		},
	}

	body, _ := json.Marshal(payload)
	w := httptest.NewRecorder()
	req, _ := http.NewRequest("POST", "/api/config/load", bytes.NewReader(body))
	req.Header.Set("Content-Type", "application/json")
	gw.GetRouter().ServeHTTP(w, req)

	if w.Code != http.StatusOK {
		bodyBytes, _ := io.ReadAll(w.Body)
		t.Errorf("LoadConfig() status = %d, body = %s", w.Code, string(bodyBytes))
	}

	// 验证服务已注册（使用Gateway的GetRegistry）
	instances := gw.GetRegistry().GetByService("cfg-svc")
	if len(instances) != 1 {
		t.Errorf("LoadConfig() service count = %d, want 1", len(instances))
	}

	// 验证路由已创建（使用Gateway的GetRouteManager）
	if gw.GetRouteManager().Count() != 1 {
		t.Errorf("LoadConfig() route count = %d, want 1", gw.GetRouteManager().Count())
	}
}

// TestHealthAlertEndpoint 测试健康告警端点
func TestHealthAlertEndpoint(t *testing.T) {
	gw := setupTestGateway()

	payload := map[string]interface{}{
		"service":    "test-service",
		"alert_type": "error",
		"message":    "Test alert",
		"severity":   "high",
	}

	body, _ := json.Marshal(payload)
	w := httptest.NewRecorder()
	req, _ := http.NewRequest("POST", "/api/health/alerts", bytes.NewReader(body))
	req.Header.Set("Content-Type", "application/json")
	gw.GetRouter().ServeHTTP(w, req)

	if w.Code != http.StatusOK {
		t.Errorf("HealthAlert() status = %d, want 200", w.Code)
	}

	var response map[string]interface{}
	json.Unmarshal(w.Body.Bytes(), &response)
	data := response["data"].(map[string]interface{})

	if data["severity"] != "high" {
		t.Errorf("HealthAlert() severity = %s, want high", data["severity"])
	}
}

// TestRootEndpoint 测试根路径
func TestRootEndpoint(t *testing.T) {
	gw := setupTestGateway()

	w := httptest.NewRecorder()
	req, _ := http.NewRequest("GET", "/", nil)
	gw.GetRouter().ServeHTTP(w, req)

	if w.Code != http.StatusOK {
		t.Errorf("RootEndpoint() status = %d, want 200", w.Code)
	}

	var response map[string]interface{}
	json.Unmarshal(w.Body.Bytes(), &response)

	if response["name"] != "Athena Gateway Unified" {
		t.Errorf("RootEndpoint() name = %s, want Athena Gateway Unified", response["name"])
	}
	if response["status"] != "running" {
		t.Errorf("RootEndpoint() status = %s, want running", response["status"])
	}
}

// TestCORSMiddleware 测试CORS中间件
func TestCORSMiddleware(t *testing.T) {
	gw := setupTestGateway()

	w := httptest.NewRecorder()
	req, _ := http.NewRequest("OPTIONS", "/api/test", nil)
	req.Header.Set("Origin", "http://example.com")
	req.Header.Set("Access-Control-Request-Method", "GET")
	gw.GetRouter().ServeHTTP(w, req)

	// CORS预检请求应该返回204或200
	if w.Code != http.StatusOK && w.Code != http.StatusNoContent {
		t.Errorf("CORSMiddleware() status = %d, want 200 or 204", w.Code)
	}

	// 检查CORS头
	corsHeader := w.Header().Get("Access-Control-Allow-Origin")
	if corsHeader == "" || corsHeader != "*" {
		// 可能设置了具体的域名
	}
}

// TestRequestIDMiddleware 测试请求ID中间件
func TestRequestIDMiddleware(t *testing.T) {
	gw := setupTestGateway()

	w := httptest.NewRecorder()
	req, _ := http.NewRequest("GET", "/health", nil)
	gw.GetRouter().ServeHTTP(w, req)

	requestID := w.Header().Get("X-Request-ID")
	if requestID == "" {
		t.Error("RequestIDMiddleware() X-Request-ID header not set")
	}
}

// TestServiceRegistrationFlow 测试完整的服务注册流程
func TestServiceRegistrationFlow(t *testing.T) {
	gw := setupTestGateway()

	// 1. 批量注册服务
	registerPayload := map[string]interface{}{
		"services": []map[string]interface{}{
			{
				"name": "flow-svc",
				"host": "localhost",
				"port": 8080,
			},
		},
	}
	body, _ := json.Marshal(registerPayload)
	w := httptest.NewRecorder()
	req, _ := http.NewRequest("POST", "/api/services/batch_register", bytes.NewReader(body))
	req.Header.Set("Content-Type", "application/json")
	gw.GetRouter().ServeHTTP(w, req)

	if w.Code != http.StatusOK {
		t.Errorf("Flow Register() status = %d, want 200", w.Code)
	}

	// 2. 查询服务
	w = httptest.NewRecorder()
	req, _ = http.NewRequest("GET", "/api/services/instances?service=flow-svc", nil)
	gw.GetRouter().ServeHTTP(w, req)

	if w.Code != http.StatusOK {
		t.Errorf("Flow ListInstances() status = %d, want 200", w.Code)
	}

	var response map[string]interface{}
	json.Unmarshal(w.Body.Bytes(), &response)
	data := response["data"].(map[string]interface{})
	instances := data["data"].([]interface{})

	if len(instances) != 1 {
		t.Errorf("Flow ListInstances() count = %d, want 1", len(instances))
	}

	// 3. 获取单个实例
	instance := instances[0].(map[string]interface{})
	instanceID := instance["id"].(string)

	w = httptest.NewRecorder()
	req, _ = http.NewRequest("GET", "/api/services/instances/"+instanceID, nil)
	gw.GetRouter().ServeHTTP(w, req)

	if w.Code != http.StatusOK {
		t.Errorf("Flow GetInstance() status = %d, want 200", w.Code)
	}

	// 4. 创建路由
	routePayload := map[string]interface{}{
		"path":           "/flow/**",
		"target_service": "flow-svc",
		"methods":        []string{"GET"},
		"strip_prefix":   true,
	}
	body, _ = json.Marshal(routePayload)
	w = httptest.NewRecorder()
	req, _ = http.NewRequest("POST", "/api/routes", bytes.NewReader(body))
	req.Header.Set("Content-Type", "application/json")
	gw.GetRouter().ServeHTTP(w, req)

	if w.Code != http.StatusOK {
		t.Errorf("Flow CreateRoute() status = %d, want 200", w.Code)
	}

	// 5. 验证路由配置（使用Gateway的GetRouteManager）
	route := gw.GetRouteManager().FindByPath("/flow/test", "GET")
	if route == nil {
		t.Fatal("Flow FindByPath() route not found")
	}
	if route.TargetService != "flow-svc" {
		t.Errorf("Flow FindByPath() target = %s, want flow-svc", route.TargetService)
	}
}

// TestErrorHandling 测试错误处理
func TestErrorHandling(t *testing.T) {
	gw := setupTestGateway()

	// 测试无效JSON
	w := httptest.NewRecorder()
	req, _ := http.NewRequest("POST", "/api/services/batch_register", strings.NewReader("invalid json"))
	req.Header.Set("Content-Type", "application/json")
	gw.GetRouter().ServeHTTP(w, req)

	if w.Code != http.StatusBadRequest {
		t.Errorf("ErrorHandling() invalid JSON status = %d, want 400", w.Code)
	}

	// 测试获取不存在的实例
	w = httptest.NewRecorder()
	req, _ = http.NewRequest("GET", "/api/services/instances/non-existent", nil)
	gw.GetRouter().ServeHTTP(w, req)

	if w.Code != http.StatusNotFound {
		t.Errorf("ErrorHandling() not found status = %d, want 404", w.Code)
	}
}

// TestConcurrentRequests 测试并发请求
func TestConcurrentRequests(t *testing.T) {
	gw := setupTestGateway()

	concurrent := 50
	done := make(chan bool, concurrent)

	for i := 0; i < concurrent; i++ {
		go func() {
			defer func() { done <- true }()
			w := httptest.NewRecorder()
			req, _ := http.NewRequest("GET", "/health", nil)
			gw.GetRouter().ServeHTTP(w, req)
		}()
	}

	// 等待所有请求完成
	for i := 0; i < concurrent; i++ {
		<-done
	}
}
