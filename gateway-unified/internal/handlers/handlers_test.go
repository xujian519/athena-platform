// Package handlers - API处理器测试
package handlers

import (
	"bytes"
	"encoding/json"
	"net/http"
	"net/http/httptest"
	"testing"

	"github.com/gin-gonic/gin"
)

// TestNewServiceRegistry 测试创建服务注册表
func TestNewServiceRegistry(t *testing.T) {
	registry := NewServiceRegistry()

	if registry == nil {
		t.Fatal("注册表不应为nil")
	}

	if registry.instances == nil {
		t.Error("实例映射不应为nil")
	}

	if registry.routes == nil {
		t.Error("路由映射不应为nil")
	}

	if registry.dependencies == nil {
		t.Error("依赖映射不应为nil")
	}
}

// TestServiceHandler_BatchRegister 测试批量注册服务
func TestServiceHandler_BatchRegister(t *testing.T) {
	registry := NewServiceRegistry()
	handler := NewServiceHandler(registry)

	// 创建测试路由
	router := gin.New()
	router.POST("/batch", handler.BatchRegister)

	// 创建批量注册请求
	services := []ServiceRegistration{
		{
			Name: "test-service-1",
			Host: "localhost",
			Port: 8080,
			Metadata: map[string]interface{}{
				"version": "1.0.0",
			},
		},
		{
			Name: "test-service-2",
			Host: "localhost",
			Port: 8081,
			Metadata: map[string]interface{}{
				"version": "1.0.0",
			},
		},
	}

	reqBody, _ := json.Marshal(map[string][]ServiceRegistration{
		"services": services,
	})

	req := httptest.NewRequest("POST", "/batch", bytes.NewReader(reqBody))
	req.Header.Set("Content-Type", "application/json")
	w := httptest.NewRecorder()

	router.ServeHTTP(w, req)

	// 检查响应
	if w.Code != http.StatusOK {
		t.Errorf("期望状态200，实际为%d", w.Code)
	}

	var resp map[string]interface{}
	json.Unmarshal(w.Body.Bytes(), &resp)

	if !resp["success"].(bool) {
		t.Error("批量注册应该成功")
	}

	data := resp["data"].([]interface{})
	if len(data) != 2 {
		t.Errorf("期望注册2个实例，实际为%d", len(data))
	}
}

// TestServiceHandler_ListInstances 测试列出实例
func TestServiceHandler_ListInstances(t *testing.T) {
	registry := NewServiceRegistry()
	handler := NewServiceHandler(registry)

	// 先注册一个实例
	registry.mu.Lock()
	registry.instances["test-1"] = &ServiceInstance{
		ID:          "test-1",
		ServiceName: "test-service",
		Host:        "localhost",
		Port:        8080,
		Status:      "UP",
	}
	registry.mu.Unlock()

	// 创建测试路由
	router := gin.New()
	router.GET("/instances", handler.ListInstances)

	req := httptest.NewRequest("GET", "/instances", nil)
	w := httptest.NewRecorder()

	router.ServeHTTP(w, req)

	// 检查响应
	if w.Code != http.StatusOK {
		t.Errorf("期望状态200，实际为%d", w.Code)
	}

	var resp map[string]interface{}
	json.Unmarshal(w.Body.Bytes(), &resp)

	data := resp["data"].([]interface{})
	if len(data) != 1 {
		t.Errorf("期望1个实例，实际为%d", len(data))
	}
}

// TestServiceHandler_GetInstance 测试获取单个实例
func TestServiceHandler_GetInstance(t *testing.T) {
	registry := NewServiceRegistry()
	handler := NewServiceHandler(registry)

	// 先注册一个实例
	testInst := &ServiceInstance{
		ID:          "test-1",
		ServiceName: "test-service",
		Host:        "localhost",
		Port:        8080,
		Status:      "UP",
	}

	registry.mu.Lock()
	registry.instances["test-1"] = testInst
	registry.mu.Unlock()

	// 创建测试路由
	router := gin.New()
	router.GET("/instances/:inst_id", handler.GetInstance)

	req := httptest.NewRequest("GET", "/instances/test-1", nil)
	w := httptest.NewRecorder()

	router.ServeHTTP(w, req)

	// 检查响应
	if w.Code != http.StatusOK {
		t.Errorf("期望状态200，实际为%d", w.Code)
	}

	var resp map[string]interface{}
	json.Unmarshal(w.Body.Bytes(), &resp)

	if !resp["success"].(bool) {
		t.Error("获取实例应该成功")
	}
}

// TestServiceHandler_GetInstanceNotFound 测试获取不存在的实例
func TestServiceHandler_GetInstanceNotFound(t *testing.T) {
	registry := NewServiceRegistry()
	handler := NewServiceHandler(registry)

	// 创建测试路由
	router := gin.New()
	router.GET("/instances/:inst_id", handler.GetInstance)

	req := httptest.NewRequest("GET", "/instances/not-found", nil)
	w := httptest.NewRecorder()

	router.ServeHTTP(w, req)

	// 检查响应
	if w.Code != http.StatusNotFound {
		t.Errorf("期望状态404，实际为%d", w.Code)
	}
}

// TestDependencyHandler_SetDependencies 测试设置依赖
func TestDependencyHandler_SetDependencies(t *testing.T) {
	registry := NewServiceRegistry()
	handler := NewDependencyHandler(registry)

	// 创建测试路由
	router := gin.New()
	router.POST("/dependencies", handler.SetDependencies)

	dep := DependencySpec{
		Service:   "service-a",
		DependsOn: []string{"service-b", "service-c"},
	}

	reqBody, _ := json.Marshal(dep)
	req := httptest.NewRequest("POST", "/dependencies", bytes.NewReader(reqBody))
	req.Header.Set("Content-Type", "application/json")
	w := httptest.NewRecorder()

	router.ServeHTTP(w, req)

	// 检查响应
	if w.Code != http.StatusOK {
		t.Errorf("期望状态200，实际为%d", w.Code)
	}

	var resp map[string]interface{}
	json.Unmarshal(w.Body.Bytes(), &resp)

	if !resp["success"].(bool) {
		t.Error("设置依赖应该成功")
	}

	data := resp["data"].(map[string]interface{})
	deps := data["dependencies"].([]interface{})
	if len(deps) != 2 {
		t.Errorf("期望2个依赖，实际为%d", len(deps))
	}
}

// TestDependencyHandler_GetDependencies 测试获取依赖
func TestDependencyHandler_GetDependencies(t *testing.T) {
	registry := NewServiceRegistry()
	handler := NewDependencyHandler(registry)

	// 先设置依赖
	registry.mu.Lock()
	registry.dependencies["service-a"] = []string{"service-b", "service-c"}
	registry.mu.Unlock()

	// 创建测试路由
	router := gin.New()
	router.GET("/dependencies/:service", handler.GetDependencies)

	req := httptest.NewRequest("GET", "/dependencies/service-a", nil)
	w := httptest.NewRecorder()

	router.ServeHTTP(w, req)

	// 检查响应
	if w.Code != http.StatusOK {
		t.Errorf("期望状态200，实际为%d", w.Code)
	}

	var resp map[string]interface{}
	json.Unmarshal(w.Body.Bytes(), &resp)

	data := resp["data"].(map[string]interface{})
	deps := data["dependencies"].([]interface{})

	if len(deps) != 2 {
		t.Errorf("期望2个依赖，实际为%d", len(deps))
	}
}

// TestDependencyHandler_GetDependenciesNotFound 测试获取不存在的服务依赖
func TestDependencyHandler_GetDependenciesNotFound(t *testing.T) {
	registry := NewServiceRegistry()
	handler := NewDependencyHandler(registry)

	// 创建测试路由
	router := gin.New()
	router.GET("/dependencies/:service", handler.GetDependencies)

	req := httptest.NewRequest("GET", "/dependencies/not-found", nil)
	w := httptest.NewRecorder()

	router.ServeHTTP(w, req)

	// 检查响应
	if w.Code != http.StatusOK {
		t.Errorf("期望状态200，实际为%d", w.Code)
	}

	var resp map[string]interface{}
	json.Unmarshal(w.Body.Bytes(), &resp)

	data := resp["data"].(map[string]interface{})
	deps := data["dependencies"].([]interface{})

	if len(deps) != 0 {
		t.Errorf("不存在的服务应该返回空依赖列表，实际为%d", len(deps))
	}
}

// TestRouteHandler_CreateRoute 测试创建路由
func TestRouteHandler_CreateRoute(t *testing.T) {
	registry := NewServiceRegistry()
	handler := NewRouteHandler(registry)

	// 先注册一个服务实例
	registry.mu.Lock()
	registry.instances["service-1"] = &ServiceInstance{
		ID:          "service-1",
		ServiceName: "user-service",
		Host:        "localhost",
		Port:        8080,
		Status:      "UP",
	}
	registry.mu.Unlock()

	// 创建测试路由
	router := gin.New()
	router.POST("/routes", handler.CreateRoute)

	route := RouteRule{
		ID:            "route-1",
		Path:          "/api/users",
		TargetService: "user-service",
		Methods:       []string{"GET", "POST"},
		Weight:        1,
	}

	reqBody, _ := json.Marshal(route)
	req := httptest.NewRequest("POST", "/routes", bytes.NewReader(reqBody))
	req.Header.Set("Content-Type", "application/json")
	w := httptest.NewRecorder()

	router.ServeHTTP(w, req)

	// 检查响应
	if w.Code != http.StatusOK {
		t.Errorf("期望状态200，实际为%d", w.Code)
	}

	var resp map[string]interface{}
	json.Unmarshal(w.Body.Bytes(), &resp)

	if !resp["success"].(bool) {
		t.Error("创建路由应该成功")
	}
}

// TestRouteHandler_CreateRouteInvalidTarget 测试创建路由到不存在的服务
func TestRouteHandler_CreateRouteInvalidTarget(t *testing.T) {
	registry := NewServiceRegistry()
	handler := NewRouteHandler(registry)

	// 创建测试路由
	router := gin.New()
	router.POST("/routes", handler.CreateRoute)

	route := RouteRule{
		ID:            "route-1",
		Path:          "/api/users",
		TargetService: "non-existent-service",
		Methods:       []string{"GET"},
	}

	reqBody, _ := json.Marshal(route)
	req := httptest.NewRequest("POST", "/routes", bytes.NewReader(reqBody))
	req.Header.Set("Content-Type", "application/json")
	w := httptest.NewRecorder()

	router.ServeHTTP(w, req)

	// 检查响应
	if w.Code != http.StatusBadRequest {
		t.Errorf("期望状态400，实际为%d", w.Code)
	}
}

// TestRouteHandler_ListRoutes 测试列出路由
func TestRouteHandler_ListRoutes(t *testing.T) {
	registry := NewServiceRegistry()
	handler := NewRouteHandler(registry)

	// 先创建一个路由
	registry.mu.Lock()
	registry.routes["route-1"] = &RouteRule{
		ID:            "route-1",
		Path:          "/api/users",
		TargetService: "user-service",
		Methods:       []string{"GET"},
		Weight:        1,
		Enabled:       true,
	}
	registry.mu.Unlock()

	// 创建测试路由
	router := gin.New()
	router.GET("/routes", handler.ListRoutes)

	req := httptest.NewRequest("GET", "/routes", nil)
	w := httptest.NewRecorder()

	router.ServeHTTP(w, req)

	// 检查响应
	if w.Code != http.StatusOK {
		t.Errorf("期望状态200，实际为%d", w.Code)
	}

	var resp map[string]interface{}
	json.Unmarshal(w.Body.Bytes(), &resp)

	data := resp["data"].([]interface{})
	if len(data) != 1 {
		t.Errorf("期望1个路由，实际为%d", len(data))
	}
}

// TestHealthHandler_Health 测试健康检查
func TestHealthHandler_Health(t *testing.T) {
	registry := NewServiceRegistry()
	handler := NewHealthHandler(registry)

	// 创建测试路由
	router := gin.New()
	router.GET("/health", handler.Health)

	req := httptest.NewRequest("GET", "/health", nil)
	w := httptest.NewRecorder()

	router.ServeHTTP(w, req)

	// 检查响应
	if w.Code != http.StatusOK {
		t.Errorf("期望状态200，实际为%d", w.Code)
	}

	var resp map[string]interface{}
	json.Unmarshal(w.Body.Bytes(), &resp)

	if resp["success"].(bool) != true {
		t.Error("健康检查应该成功")
	}

	data := resp["data"].(map[string]interface{})
	status := data["status"].(string)

	// 没有实例时应该是NOT_READY
	if status != "NOT_READY" {
		t.Errorf("没有实例时状态应为NOT_READY，实际为%s", status)
	}
}

// TestHealthHandler_HealthWithInstances 测试有实例的健康检查
func TestHealthHandler_HealthWithInstances(t *testing.T) {
	registry := NewServiceRegistry()
	handler := NewHealthHandler(registry)

	// 添加一些实例
	registry.mu.Lock()
	registry.instances["inst-1"] = &ServiceInstance{
		ID:          "inst-1",
		ServiceName: "service-1",
		Host:        "localhost",
		Port:        8080,
		Status:      "UP",
	}
	registry.instances["inst-2"] = &ServiceInstance{
		ID:          "inst-2",
		ServiceName: "service-2",
		Host:        "localhost",
		Port:        8081,
		Status:      "DOWN",
	}
	registry.mu.Unlock()

	// 创建测试路由
	router := gin.New()
	router.GET("/health", handler.Health)

	req := httptest.NewRequest("GET", "/health", nil)
	w := httptest.NewRecorder()

	router.ServeHTTP(w, req)

	// 检查响应
	if w.Code != http.StatusOK {
		t.Errorf("期望状态200，实际为%d", w.Code)
	}

	var resp map[string]interface{}
	json.Unmarshal(w.Body.Bytes(), &resp)

	data := resp["data"].(map[string]interface{})
	status := data["status"].(string)

	// 有健康实例时应该是UP
	if status != "UP" {
		t.Errorf("有健康实例时状态应为UP，实际为%s", status)
	}
}

// TestResponseHelpers 测试响应辅助函数
func TestResponseHelpers(t *testing.T) {
	router := gin.New()

	// 测试Success
	router.GET("/success", func(c *gin.Context) {
		Success(c, map[string]string{"key": "value"})
	})

	// 测试Error
	router.GET("/error", func(c *gin.Context) {
		Error(c, http.StatusInternalServerError, "test error")
	})

	// 测试BadRequest
	router.GET("/bad-request", func(c *gin.Context) {
		BadRequest(c, "bad request")
	})

	// 测试NotFound
	router.GET("/not-found", func(c *gin.Context) {
		NotFound(c, "not found")
	})

	// 测试Success响应
	req := httptest.NewRequest("GET", "/success", nil)
	w := httptest.NewRecorder()
	router.ServeHTTP(w, req)
	if w.Code != http.StatusOK {
		t.Errorf("/success 期望200，实际为%d", w.Code)
	}

	// 测试错误响应
	req = httptest.NewRequest("GET", "/error", nil)
	w = httptest.NewRecorder()
	router.ServeHTTP(w, req)
	if w.Code != http.StatusInternalServerError {
		t.Errorf("/error 期望500，实际为%d", w.Code)
	}

	// 测试400错误响应
	req = httptest.NewRequest("GET", "/bad-request", nil)
	w = httptest.NewRecorder()
	router.ServeHTTP(w, req)
	if w.Code != http.StatusBadRequest {
		t.Errorf("/bad-request 期望400，实际为%d", w.Code)
	}

	// 测试404错误响应
	req = httptest.NewRequest("GET", "/not-found", nil)
	w = httptest.NewRecorder()
	router.ServeHTTP(w, req)
	if w.Code != http.StatusNotFound {
		t.Errorf("/not-found 期望404，实际为%d", w.Code)
	}
}
