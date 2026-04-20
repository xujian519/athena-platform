# Gateway优化实施计划

**创建日期**: 2026-04-20
**版本**: 1.0.0
**负责人**: Agent Team
**预计完成**: 2026-05-15 (25天)

---

## 📋 目录

- [执行摘要](#执行摘要)
- [任务分解](#任务分解)
- [详细实施步骤](#详细实施步骤)
- [测试验证方案](#测试验证方案)
- [风险点和缓解措施](#风险点和缓解措施)
- [回滚方案](#回滚方案)

---

## 执行摘要

### 优化目标

基于Gateway探索分析，本次优化聚焦于以下核心领域：

| 优先级 | 任务 | 预计工期 | 价值评估 |
|--------|------|---------|---------|
| P0 | 配置核心路由规则 | 2天 | 高 |
| P0 | 服务发现集成 | 3天 | 极高 |
| P1 | Agent通信统一 | 5天 | 高 |
| P1 | 端口规范化 | 3天 | 中 |
| P2 | API版本管理 | 5天 | 中 |
| P2 | 安全增强 | 7天 | 高 |

### 当前Gateway状态

- **核心路由**: 已实现基础路由管理器
- **服务注册**: 内存级别注册表已就绪
- **WebSocket**: 完整集成 (1,287行代码)
- **监控**: Prometheus指标导出已启用
- **认证**: HMAC令牌 + RBAC已实现

---

## 任务分解

### 阶段1: P0任务 (5天)

#### 任务1.1: 配置核心路由规则 (2天)

**目标**: 建立完整的路由配置系统

**现状分析**:
- ✅ 已有 `RouteManager` 基础实现
- ✅ 支持通配符匹配 (精确 > 单层 > 多层)
- ❌ 缺少配置文件加载
- ❌ 缺少路由优先级管理
- ❌ 缺少路由健康检查

**实施步骤**:

**步骤1.1.1**: 创建路由配置文件 (4小时)
```yaml
# config/routes.yaml
routes:
  # 小娜法律专家路由
  - id: "xiaona-legal"
    path: "/api/xiaona/*"
    target_service: "xiaona-legal"
    methods: ["GET", "POST", "PUT", "DELETE"]
    strip_prefix: true
    timeout: 30
    retries: 3
    auth_required: true
    priority: 100
    metadata:
      description: "小娜法律专家服务"
      version: "1.0.0"

  # 小诺协调器路由
  - id: "xiaonuo-coordinator"
    path: "/api/xiaonuo/*"
    target_service: "xiaonuo-coordinator"
    methods: ["GET", "POST"]
    strip_prefix: true
    timeout: 20
    retries: 2
    auth_required: true
    priority: 90
    metadata:
      description: "小诺任务协调服务"

  # 云熙IP管理路由
  - id: "yunxi-ip"
    path: "/api/yunxi/*"
    target_service: "yunxi-ip"
    methods: ["GET", "POST", "PUT"]
    strip_prefix: true
    timeout: 25
    retries: 2
    auth_required: true
    priority: 80
    metadata:
      description: "云熙IP管理服务"

  # Coordinator模式路由
  - id: "coordinator"
    path: "/api/coordinator/*"
    target_service: "coordinator"
    methods: ["GET", "POST", "PUT", "DELETE"]
    strip_prefix: true
    timeout: 30
    retries: 3
    auth_required: true
    priority: 95
    metadata:
      description: "Coordinator协调模式"

  # Swarm模式路由
  - id: "swarm"
    path: "/api/swarm/*"
    target_service: "swarm"
    methods: ["GET", "POST"]
    strip_prefix: true
    timeout: 30
    retries: 2
    auth_required: true
    priority: 85
    metadata:
      description: "Swarm协作模式"

  # WebSocket控制平面
  - id: "websocket-control"
    path: "/ws"
    target_service: "gateway-websocket"
    methods: ["GET"]
    strip_prefix: false
    timeout: 600
    retries: 0
    auth_required: true
    priority: 100
    metadata:
      description: "WebSocket控制平面"

  # Canvas Host服务
  - id: "canvas-host"
    path: "/api/canvas/*"
    target_service: "canvas-host"
    methods: ["GET", "POST"]
    strip_prefix: true
    timeout: 15
    retries: 2
    auth_required: true
    priority: 70
    metadata:
      description: "Canvas UI渲染服务"
```

**步骤1.1.2**: 实现路由配置加载器 (4小时)

**文件**: `gateway-unified/internal/config/routes_loader.go`

```go
package config

import (
	"fmt"
	"os"
	"sync"

	"gopkg.in/yaml.v3"
	"github.com/athena-workspace/gateway-unified/internal/gateway"
)

// RoutesConfig 路由配置
type RoutesConfig struct {
	Routes []gateway.RouteRule `yaml:"routes"`
}

// RoutesLoader 路由配置加载器
type RoutesLoader struct {
	mu       sync.RWMutex
	config   *RoutesConfig
	watchers []func(*RoutesConfig)
}

// NewRoutesLoader 创建路由配置加载器
func NewRoutesLoader() *RoutesLoader {
	return &RoutesLoader{
		config: &RoutesConfig{
			Routes: make([]gateway.RouteRule, 0),
		},
		watchers: make([]func(*RoutesConfig), 0),
	}
}

// LoadFromFile 从文件加载配置
func (l *RoutesLoader) LoadFromFile(path string) error {
	l.mu.Lock()
	defer l.mu.Unlock()

	data, err := os.ReadFile(path)
	if err != nil {
		return fmt.Errorf("读取配置文件失败: %w", err)
	}

	var config RoutesConfig
	if err := yaml.Unmarshal(data, &config); err != nil {
		return fmt.Errorf("解析配置文件失败: %w", err)
	}

	// 设置默认值
	for i := range config.Routes {
		if config.Routes[i].Timeout == 0 {
			config.Routes[i].Timeout = 30
		}
		if config.Routes[i].Retries == 0 {
			config.Routes[i].Retries = 3
		}
		if config.Routes[i].Methods == nil {
			config.Routes[i].Methods = []string{"GET", "POST"}
		}
		if config.Routes[i].Metadata == nil {
			config.Routes[i].Metadata = make(map[string]interface{})
		}
	}

	l.config = &config

	// 通知监听器
	for _, watcher := range l.watchers {
		watcher(&config)
	}

	return nil
}

// GetRoutes 获取所有路由
func (l *RoutesLoader) GetRoutes() []gateway.RouteRule {
	l.mu.RLock()
	defer l.mu.RUnlock()

	return l.config.Routes
}

// Watch 监听配置变化
func (l *RoutesLoader) Watch(watcher func(*RoutesConfig)) {
	l.mu.Lock()
	defer l.mu.Unlock()

	l.watchers = append(l.watchers, watcher)
}
```

**步骤1.1.3**: 集成到Gateway启动流程 (2小时)

**文件**: `gateway-unified/cmd/gateway/main.go`

```go
// 在启动时加载路由配置
routesLoader := config.NewRoutesLoader()
if err := routesLoader.LoadFromFile("config/routes.yaml"); err != nil {
    log.Fatalf("加载路由配置失败: %v", err)
}

// 批量创建路由
for _, route := range routesLoader.GetRoutes() {
    gw.GetRouteManager().Create(&route)
    log.Printf("路由已加载: %s -> %s", route.Path, route.TargetService)
}
```

**步骤1.1.4**: 添加路由验证 (2小时)

**文件**: `gateway-unified/internal/gateway/routes_validator.go`

```go
package gateway

import (
	"fmt"
	"net/http"
	"strings"
)

// RouteValidator 路由验证器
type RouteValidator struct{}

// NewRouteValidator 创建路由验证器
func NewRouteValidator() *RouteValidator {
	return &RouteValidator{}
}

// Validate 验证路由规则
func (v *RouteValidator) Validate(route *RouteRule) error {
	// 检查必填字段
	if route.ID == "" {
		return fmt.Errorf("路由ID不能为空")
	}
	if route.Path == "" {
		return fmt.Errorf("路由路径不能为空")
	}
	if route.TargetService == "" {
		return fmt.Errorf("目标服务不能为空")
	}

	// 检查路径格式
	if !strings.HasPrefix(route.Path, "/") {
		return fmt.Errorf("路径必须以/开头: %s", route.Path)
	}

	// 检查方法
	if len(route.Methods) == 0 {
		return fmt.Errorf("至少需要指定一个HTTP方法")
	}
	validMethods := map[string]bool{
		"GET": true, "POST": true, "PUT": true,
		"DELETE": true, "PATCH": true, "OPTIONS": true,
	}
	for _, method := range route.Methods {
		if !validMethods[method] {
			return fmt.Errorf("无效的HTTP方法: %s", method)
		}
	}

	// 检查超时
	if route.Timeout < 0 || route.Timeout > 300 {
		return fmt.Errorf("超时时间必须在0-300秒之间")
	}

	// 检查重试次数
	if route.Retries < 0 || route.Retries > 10 {
		return fmt.Errorf("重试次数必须在0-10之间")
	}

	return nil
}

// ValidateConflict 检查路由冲突
func (v *RouteValidator) ValidateConflict(route *RouteRule, existing []*RouteRule) error {
	for _, existingRoute := range existing {
		if existingRoute.ID == route.ID {
			continue // 跳过自己
		}

		// 检查路径冲突
		if v.pathsConflict(route.Path, existingRoute.Path) {
			// 检查方法冲突
			for _, method := range route.Methods {
				for _, existingMethod := range existingRoute.Methods {
					if method == existingMethod {
						return fmt.Errorf(
							"路径冲突: %s (方法: %s) 与 %s (方法: %s)",
							route.Path, method, existingRoute.Path, existingMethod,
						)
					}
				}
			}
		}
	}
	return nil
}

// pathsConflict 检查两个路径是否冲突
func (v *RouteValidator) pathsConflict(path1, path2 string) bool {
	// 精确匹配
	if path1 == path2 {
		return true
	}

	// 通配符匹配
	if strings.HasSuffix(path1, "/*") || strings.HasSuffix(path1, "/**") {
		prefix1 := strings.TrimSuffix(path1, "/*")
		prefix1 = strings.TrimSuffix(prefix1, "/**")
		if strings.HasPrefix(path2, prefix1) {
			return true
		}
	}

	if strings.HasSuffix(path2, "/*") || strings.HasSuffix(path2, "/**") {
		prefix2 := strings.TrimSuffix(path2, "/*")
		prefix2 = strings.TrimSuffix(prefix2, "/**")
		if strings.HasPrefix(path1, prefix2) {
			return true
		}
	}

	return false
}
```

**步骤1.1.5**: 编写测试 (4小时)

**文件**: `gateway-unified/internal/gateway/routes_loader_test.go`

```go
package gateway

import (
	"testing"

	"github.com/athena-workspace/gateway-unified/internal/config"
)

func TestRoutesLoader(t *testing.T) {
	loader := config.NewRoutesLoader()

	// 测试加载配置
	err := loader.LoadFromFile("../../../config/routes.yaml")
	if err != nil {
		t.Fatalf("加载配置失败: %v", err)
	}

	routes := loader.GetRoutes()
	if len(routes) == 0 {
		t.Fatal("没有加载到路由")
	}

	// 验证路由
	validator := NewRouteValidator()
	for _, route := range routes {
		if err := validator.Validate(&route); err != nil {
			t.Errorf("路由验证失败: %s - %v", route.ID, err)
		}
	}
}

func TestRouteConflictDetection(t *testing.T) {
	validator := NewRouteValidator()

	route1 := &RouteRule{
		ID:            "route1",
		Path:          "/api/test/*",
		TargetService: "service1",
		Methods:       []string{"GET"},
	}

	route2 := &RouteRule{
		ID:            "route2",
		Path:          "/api/test/*",
		TargetService: "service2",
		Methods:       []string{"GET"},
	}

	err := validator.ValidateConflict(route1, []*RouteRule{route2})
	if err == nil {
		t.Error("应该检测到路由冲突")
	}
}
```

**交付物**:
- ✅ 路由配置文件 (`config/routes.yaml`)
- ✅ 路由加载器 (~150行)
- ✅ 路由验证器 (~120行)
- ✅ 测试代码 (~100行)
- ✅ 集成到Gateway启动流程

---

#### 任务1.2: 服务发现集成 (3天)

**目标**: 实现Gateway与服务发现系统的完整集成

**现状分析**:
- ✅ 已有 `ServiceRegistry` 内存注册表
- ✅ 已有健康检查基础
- ✅ 已有负载均衡器
- ❌ 缺少与 `config/service_discovery.json` 的集成
- ❌ 缺少动态服务注册/注销
- ❌ 缺少服务健康探测

**实施步骤**:

**步骤1.2.1**: 实现服务发现适配器 (6小时)

**文件**: `gateway-unified/internal/discovery/adapter.go`

```go
package discovery

import (
	"context"
	"encoding/json"
	"fmt"
	"time"

	"github.com/athena-workspace/gateway-unified/internal/gateway"
	"github.com/athena-workspace/gateway-unified/internal/logging"
)

// ServiceDiscoveryConfig 服务发现配置
type ServiceDiscoveryConfig struct {
	ConfigPath     string        `yaml:"config_path"`
	ScanInterval   time.Duration `yaml:"scan_interval"`
	AutoRegister   bool          `yaml:"auto_register"`
	HealthCheck    bool          `yaml:"health_check"`
	HealthEndpoint string        `yaml:"health_endpoint"`
}

// Adapter 服务发现适配器
type Adapter struct {
	config         *ServiceDiscoveryConfig
	registry       *gateway.ServiceRegistry
	configData     *ServiceDiscoveryFile
	ctx            context.Context
	cancel         context.CancelFunc
	healthChecker  *HealthChecker
}

// ServiceDiscoveryFile 服务发现配置文件结构
type ServiceDiscoveryFile struct {
	Services []ServiceInfo `json:"services"`
}

// ServiceInfo 服务信息
type ServiceInfo struct {
	Name           string                 `json:"name"`
	Type           string                 `json:"type"`
	Provider       string                 `json:"provider"`
	Protocol       string                 `json:"protocol"`
	Enabled        bool                   `json:"enabled"`
	Port           int                    `json:"port,omitempty"`
	BaseURL        string                 `json:"base_url,omitempty"`
	HealthEndpoint string                 `json:"health_endpoint,omitempty"`
	Description    string                 `json:"description"`
	Metadata       map[string]interface{} `json:"metadata,omitempty"`
}

// NewAdapter 创建服务发现适配器
func NewAdapter(
	config *ServiceDiscoveryConfig,
	registry *gateway.ServiceRegistry,
) *Adapter {
	ctx, cancel := context.WithCancel(context.Background())

	adapter := &Adapter{
		config:        config,
		registry:      registry,
		ctx:           ctx,
		cancel:        cancel,
		healthChecker: NewHealthChecker(config),
	}

	return adapter
}

// LoadConfig 加载服务发现配置
func (a *Adapter) LoadConfig() error {
	data, err := os.ReadFile(a.config.ConfigPath)
	if err != nil {
		return fmt.Errorf("读取配置文件失败: %w", err)
	}

	var configData ServiceDiscoveryFile
	if err := json.Unmarshal(data, &configData); err != nil {
		return fmt.Errorf("解析配置文件失败: %w", err)
	}

	a.configData = &configData
	return nil
}

// SyncServices 同步服务到注册表
func (a *Adapter) SyncServices() error {
	if a.configData == nil {
		if err := a.LoadConfig(); err != nil {
			return err
		}
	}

	// 获取当前已注册的服务ID集合
	registeredIDs := make(map[string]bool)
	for _, instance := range a.registry.GetAll() {
		registeredIDs[instance.ID] = true
	}

	// 注册或更新服务
	for _, svc := range a.configData.Services {
		if !svc.Enabled {
			continue
		}

		// 生成服务实例
		instance := a.createInstance(svc)

		// 检查是否已注册
		if a.registry.GetByID(instance.ID) != nil {
			// 更新现有服务
			a.registry.Update(instance)
			logging.LogInfo("服务已更新",
				logging.String("service", instance.ServiceName),
				logging.String("id", instance.ID),
			)
		} else {
			// 注册新服务
			a.registry.Register(instance)
			logging.LogInfo("服务已注册",
				logging.String("service", instance.ServiceName),
				logging.String("id", instance.ID),
			)
		}

		delete(registeredIDs, instance.ID)
	}

	// 注销不再存在的服务
	for id := range registeredIDs {
		a.registry.Delete(id)
		logging.LogInfo("服务已注销",
			logging.String("id", id),
		)
	}

	return nil
}

// createInstance 从服务信息创建实例
func (a *Adapter) createInstance(svc ServiceInfo) *gateway.ServiceInstance {
	// 确定主机和端口
	host := "127.0.0.1"
	port := svc.Port

	if svc.BaseURL != "" {
		// 从BaseURL解析主机和端口
		// TODO: 实现URL解析
	}

	// 生成实例ID
	instanceID := fmt.Sprintf("%s:%s:%d:0", svc.Name, host, port)

	instance := &gateway.ServiceInstance{
		ID:          instanceID,
		ServiceName: svc.Name,
		Host:        host,
		Port:        port,
		Status:      "UP",
		Weight:      1,
		Metadata: map[string]interface{}{
			"type":        svc.Type,
			"provider":    svc.Provider,
			"protocol":    svc.Protocol,
			"description": svc.Description,
		},
	}

	// 添加自定义元数据
	for k, v := range svc.Metadata {
		instance.Metadata[k] = v
	}

	return instance
}

// Start 启动服务发现适配器
func (a *Adapter) Start() error {
	// 初始同步
	if err := a.SyncServices(); err != nil {
		return err
	}

	// 启动定期同步
	go a.syncLoop()

	// 启动健康检查
	if a.config.HealthCheck {
		go a.healthCheckLoop()
	}

	return nil
}

// syncLoop 定期同步服务
func (a *Adapter) syncLoop() {
	ticker := time.NewTicker(a.config.ScanInterval)
	defer ticker.Stop()

	for {
		select {
		case <-ticker.C:
			if err := a.SyncServices(); err != nil {
				logging.LogError("服务同步失败", logging.Err(err))
			}
		case <-a.ctx.Done():
			return
		}
	}
}

// healthCheckLoop 健康检查循环
func (a *Adapter) healthCheckLoop() {
	ticker := time.NewTicker(30 * time.Second)
	defer ticker.Stop()

	for {
		select {
		case <-ticker.C:
			a.checkAllServices()
		case <-a.ctx.Done():
			return
		}
	}
}

// checkAllServices 检查所有服务健康状态
func (a *Adapter) checkAllServices() {
	instances := a.registry.GetAll()

	for _, instance := range instances {
		healthy := a.healthChecker.Check(instance)

		if healthy {
			if instance.Status != "UP" {
				instance.Status = "UP"
				logging.LogInfo("服务恢复健康",
					logging.String("service", instance.ServiceName),
					logging.String("id", instance.ID),
				)
			}
		} else {
			if instance.Status != "DOWN" {
				instance.Status = "DOWN"
				logging.LogWarn("服务不健康",
					logging.String("service", instance.ServiceName),
					logging.String("id", instance.ID),
				)
			}
		}
	}
}

// Close 关闭适配器
func (a *Adapter) Close() error {
	a.cancel()
	return nil
}
```

**步骤1.2.2**: 实现健康检查器 (4小时)

**文件**: `gateway-unified/internal/discovery/health_checker.go`

```go
package discovery

import (
	"fmt"
	"net/http"
	"time"

	"github.com/athena-workspace/gateway-unified/internal/gateway"
)

// HealthChecker 健康检查器
type HealthChecker struct {
	timeout    time.Duration
	userAgent  string
}

// NewHealthChecker 创建健康检查器
func NewHealthChecker(config *ServiceDiscoveryConfig) *HealthChecker {
	return &HealthChecker{
		timeout:   5 * time.Second,
		userAgent: "Athena-Gateway-HealthCheck/1.0",
	}
}

// Check 检查服务健康状态
func (h *HealthChecker) Check(instance *gateway.ServiceInstance) bool {
	// 构造健康检查URL
	url := fmt.Sprintf("http://%s:%d/health", instance.Host, instance.Port)

	// 如果元数据中有自定义健康检查端点
	if healthEndpoint, ok := instance.Metadata["health_endpoint"].(string); ok {
		url = fmt.Sprintf("http://%s:%d%s", instance.Host, instance.Port, healthEndpoint)
	}

	// 创建请求
	client := &http.Client{
		Timeout: h.timeout,
	}

	req, err := http.NewRequest("GET", url, nil)
	if err != nil {
		return false
	}

	req.Header.Set("User-Agent", h.userAgent)

	// 发送请求
	resp, err := client.Do(req)
	if err != nil {
		return false
	}
	defer resp.Body.Close()

	// 检查状态码
	return resp.StatusCode == http.StatusOK
}
```

**步骤1.2.3**: 集成到Gateway (2小时)

**文件**: `gateway-unified/cmd/gateway/main.go`

```go
// 创建服务发现适配器
discoveryConfig := &discovery.ServiceDiscoveryConfig{
	ConfigPath:     "config/service_discovery.json",
	ScanInterval:   30 * time.Second,
	AutoRegister:   true,
	HealthCheck:    true,
	HealthEndpoint: "/health",
}

discoveryAdapter := discovery.NewAdapter(discoveryConfig, gw.GetRegistry())
if err := discoveryAdapter.Start(); err != nil {
	log.Fatalf("启动服务发现失败: %v", err)
}
defer discoveryAdapter.Close()
```

**步骤1.2.4**: 实现动态服务注册API (4小时)

**文件**: `gateway-unified/internal/handlers/discovery.go`

```go
package handlers

import (
	"github.com/gin-gonic/gin"
	"github.com/athena-workspace/gateway-unified/internal/discovery"
)

// DiscoveryHandlers 服务发现处理器
type DiscoveryHandlers struct {
	adapter *discovery.Adapter
}

// NewDiscoveryHandlers 创建服务发现处理器
func NewDiscoveryHandlers(adapter *discovery.Adapter) *DiscoveryHandlers {
	return &DiscoveryHandlers{
		adapter: adapter,
	}
}

// SyncNow 立即同步服务
func (h *DiscoveryHandlers) SyncNow(c *gin.Context) {
	if err := h.adapter.SyncServices(); err != nil {
		c.JSON(500, gin.H{
			"success": false,
			"error":   err.Error(),
		})
		return
	}

	c.JSON(200, gin.H{
		"success": true,
		"message": "服务同步完成",
	})
}

// GetServices 获取所有已注册的服务
func (h *DiscoveryHandlers) GetServices(c *gin.Context) {
	services := h.adapter.GetRegistry().GetAll()

	c.JSON(200, gin.H{
		"success": true,
		"data":    services,
		"count":   len(services),
	})
}

// RegisterService 手动注册服务
func (h *DiscoveryHandlers) RegisterService(c *gin.Context) {
	var req discovery.ServiceInfo
	if err := c.ShouldBindJSON(&req); err != nil {
		c.JSON(400, gin.H{
			"success": false,
			"error":   err.Error(),
		})
		return
	}

	// TODO: 实现服务注册逻辑

	c.JSON(200, gin.H{
		"success": true,
		"message": "服务已注册",
	})
}
```

**步骤1.2.5**: 编写测试 (4小时)

**文件**: `gateway-unified/internal/discovery/adapter_test.go`

```go
package discovery

import (
	"testing"
	"time"

	"github.com/athena-workspace/gateway-unified/internal/gateway"
)

func TestServiceDiscoveryAdapter(t *testing.T) {
	// 创建注册表
	registry := gateway.NewServiceRegistry()

	// 创建适配器
	config := &ServiceDiscoveryConfig{
		ConfigPath:     "../../../config/service_discovery.json",
		ScanInterval:   5 * time.Second,
		AutoRegister:   true,
		HealthCheck:    false, // 测试时禁用健康检查
	}

	adapter := NewAdapter(config, registry)

	// 加载配置
	err := adapter.LoadConfig()
	if err != nil {
		t.Fatalf("加载配置失败: %v", err)
	}

	// 同步服务
	err = adapter.SyncServices()
	if err != nil {
		t.Fatalf("同步服务失败: %v", err)
	}

	// 验证服务已注册
	services := registry.GetAll()
	if len(services) == 0 {
		t.Fatal("没有注册任何服务")
	}

	t.Logf("已注册 %d 个服务", len(services))
}

func TestHealthChecker(t *testing.T) {
	checker := NewHealthChecker(&ServiceDiscoveryConfig{})

	// 测试健康检查
	instance := &gateway.ServiceInstance{
		ID:          "test:127.0.0.1:8005:0",
		ServiceName: "test",
		Host:        "127.0.0.1",
		Port:        8005,
		Status:      "UP",
	}

	healthy := checker.Check(instance)
	t.Logf("健康检查结果: %v", healthy)
}
```

**交付物**:
- ✅ 服务发现适配器 (~250行)
- ✅ 健康检查器 (~80行)
- ✅ 动态服务注册API (~100行)
- ✅ 测试代码 (~150行)
- ✅ 集成到Gateway启动流程

---

### 阶段2: P1任务 (8天)

#### 任务2.1: Agent通信统一 (5天)

**目标**: 统一Gateway与各Agent的通信协议

**现状分析**:
- ✅ WebSocket已集成
- ✅ 基础消息路由已实现
- ❌ Agent通信协议不统一
- ❌ 缺少消息序列化/反序列化标准
- ❌ 缺少消息确认机制

**实施步骤**:

**步骤2.1.1**: 定义统一通信协议 (4小时)

**文件**: `gateway-unified/internal/protocol/agent_message.proto`

```protobuf
syntax = "proto3";

package athena.gateway;

// Agent消息类型
enum MessageType {
  UNKNOWN = 0;
  // 请求类型
  TASK_REQUEST = 1;
  QUERY_REQUEST = 2;
  CONTROL_REQUEST = 3;
  // 响应类型
  TASK_RESPONSE = 10;
  QUERY_RESPONSE = 11;
  CONTROL_RESPONSE = 12;
  // 事件类型
  STATUS_UPDATE = 20;
  PROGRESS_UPDATE = 21;
  ERROR_EVENT = 22;
  HEARTBEAT = 23;
}

// Agent类型
enum AgentType {
  AGENT_UNKNOWN = 0;
  XIAONA = 1;       // 小娜法律专家
  XIAONUO = 2;      // 小诺协调器
  YUNXI = 3;        // 云熙IP管理
  COORDINATOR = 4;  // Coordinator模式
  SWARM = 5;        // Swarm模式
}

// 消息头
message MessageHeader {
  string message_id = 1;
  MessageType type = 2;
  AgentType target_agent = 3;
  string session_id = 4;
  int64 timestamp = 5;
  map<string, string> metadata = 6;
}

// 任务请求
message TaskRequest {
  string task_id = 1;
  string task_type = 2;
  map<string, string> parameters = 3;
  string payload = 4;
  int32 priority = 5;
}

// 任务响应
message TaskResponse {
  string task_id = 1;
  bool success = 2;
  string result = 3;
  string error = 4;
  int32 exit_code = 5;
}

// Agent消息
message AgentMessage {
  MessageHeader header = 1;
  oneof body {
    TaskRequest task_request = 10;
    TaskResponse task_response = 11;
    bytes raw_data = 20;
  }
}
```

**步骤2.1.2**: 实现协议编解码器 (6小时)

**文件**: `gateway-unified/internal/protocol/codec.go`

```go
package protocol

import (
	"encoding/json"
	"fmt"
)

// Codec 消息编解码器接口
type Codec interface {
	Encode(msg *AgentMessage) ([]byte, error)
	Decode(data []byte) (*AgentMessage, error)
}

// JSONCodec JSON编解码器
type JSONCodec struct{}

// NewJSONCodec 创建JSON编解码器
func NewJSONCodec() *JSONCodec {
	return &JSONCodec{}
}

// Encode 编码消息
func (c *JSONCodec) Encode(msg *AgentMessage) ([]byte, error) {
	return json.Marshal(msg)
}

// Decode 解码消息
func (c *JSONCodec) Decode(data []byte) (*AgentMessage, error) {
	var msg AgentMessage
	if err := json.Unmarshal(data, &msg); err != nil {
		return nil, fmt.Errorf("解码失败: %w", err)
	}
	return &msg, nil
}

// MessageFactory 消息工厂
type MessageFactory struct{}

// NewMessageFactory 创建消息工厂
func NewMessageFactory() *MessageFactory {
	return &MessageFactory{}
}

// CreateTaskRequest 创建任务请求
func (f *MessageFactory) CreateTaskRequest(
	targetAgent AgentType,
	taskID string,
	taskType string,
	parameters map[string]string,
	payload string,
) *AgentMessage {
	return &AgentMessage{
		Header: &MessageHeader{
			MessageID:   generateMessageID(),
			Type:        MessageType_TASK_REQUEST,
			TargetAgent: targetAgent,
			Timestamp:   time.Now().Unix(),
			Metadata:    make(map[string]string),
		},
		Body: &AgentMessage_TaskRequest{
			TaskRequest: &TaskRequest{
				TaskID:     taskID,
				TaskType:   taskType,
				Parameters: parameters,
				Payload:    payload,
				Priority:   1,
			},
		},
	}
}

// CreateTaskResponse 创建任务响应
func (f *MessageFactory) CreateTaskResponse(
	taskID string,
	success bool,
	result string,
	err string,
) *AgentMessage {
	return &AgentMessage{
		Header: &MessageHeader{
			MessageID: generateMessageID(),
			Type:      MessageType_TASK_RESPONSE,
			Timestamp: time.Now().Unix(),
			Metadata:  make(map[string]string),
		},
		Body: &AgentMessage_TaskResponse{
			TaskResponse: &TaskResponse{
				TaskID:   taskID,
				Success:  success,
				Result:   result,
				Error:    err,
				ExitCode: 0,
			},
		},
	}
}

func generateMessageID() string {
	return fmt.Sprintf("msg_%d", time.Now().UnixNano())
}
```

**步骤2.1.3**: 实现Agent客户端 (8小时)

**文件**: `gateway-unified/internal/agent/client.go`

```go
package agent

import (
	"context"
	"fmt"
	"time"

	"github.com/athena-workspace/gateway-unified/internal/gateway"
	"github.com/athena-workspace/gateway-unified/internal/protocol"
)

// Client Agent客户端
type Client struct {
	agentType    protocol.AgentType
	serviceName  string
	registry     *gateway.ServiceRegistry
	codec        protocol.Codec
	messageFactory *protocol.MessageFactory
	timeout      time.Duration
}

// NewClient 创建Agent客户端
func NewClient(
	agentType protocol.AgentType,
	serviceName string,
	registry *gateway.ServiceRegistry,
) *Client {
	return &Client{
		agentType:      agentType,
		serviceName:    serviceName,
		registry:       registry,
		codec:          protocol.NewJSONCodec(),
		messageFactory: protocol.NewMessageFactory(),
		timeout:        30 * time.Second,
	}
}

// ExecuteTask 执行Agent任务
func (c *Client) ExecuteTask(
	ctx context.Context,
	taskType string,
	parameters map[string]string,
	payload string,
) (*protocol.TaskResponse, error) {
	// 选择服务实例
	instance := c.registry.SelectInstance(c.serviceName)
	if instance == nil {
		return nil, fmt.Errorf("没有可用的%s服务实例", c.serviceName)
	}

	// 创建任务请求
	taskID := generateTaskID()
	reqMsg := c.messageFactory.CreateTaskRequest(
		c.agentType,
		taskID,
		taskType,
		parameters,
		payload,
	)

	// 编码消息
	data, err := c.codec.Encode(reqMsg)
	if err != nil {
		return nil, fmt.Errorf("编码请求失败: %w", err)
	}

	// 发送请求
	respData, err := c.sendRequest(ctx, instance, data)
	if err != nil {
		return nil, fmt.Errorf("发送请求失败: %w", err)
	}

	// 解码响应
	respMsg, err := c.codec.Decode(respData)
	if err != nil {
		return nil, fmt.Errorf("解码响应失败: %w", err)
	}

	// 提取任务响应
	taskResp, ok := respMsg.Body.(*protocol.AgentMessage_TaskResponse)
	if !ok {
		return nil, fmt.Errorf("无效的响应类型")
	}

	return taskResp.TaskResponse, nil
}

// sendRequest 发送HTTP请求
func (c *Client) sendRequest(
	ctx context.Context,
	instance *gateway.ServiceInstance,
	data []byte,
) ([]byte, error) {
	url := fmt.Sprintf("http://%s:%d/agent/task", instance.Host, instance.Port)

	// TODO: 实现HTTP请求
	return nil, nil
}

func generateTaskID() string {
	return fmt.Sprintf("task_%d", time.Now().UnixNano())
}
```

**步骤2.1.4**: 实现Agent通信中间件 (6小时)

**文件**: `gateway-unified/internal/middleware/agent_comm.go`

```go
package middleware

import (
	"bytes"
	"io"
	"net/http"

	"github.com/gin-gonic/gin"
	"github.com/athena-workspace/gateway-unified/internal/protocol"
)

// AgentCommunication Agent通信中间件
type AgentCommunication struct {
	codec          protocol.Codec
	messageFactory *protocol.MessageFactory
}

// NewAgentCommunication 创建Agent通信中间件
func NewAgentCommunication() *AgentCommunication {
	return &AgentCommunication{
		codec:          protocol.NewJSONCodec(),
		messageFactory: protocol.NewMessageFactory(),
	}
}

// ProcessRequest 处理Agent请求
func (m *AgentCommunication) ProcessRequest() gin.HandlerFunc {
	return func(c *gin.Context) {
		// 读取请求体
		body, err := io.ReadAll(c.Request.Body)
		if err != nil {
			c.JSON(http.StatusBadRequest, gin.H{
				"success": false,
				"error":   "读取请求体失败",
			})
			return
		}

		// 解码消息
		msg, err := m.codec.Decode(body)
		if err != nil {
			c.JSON(http.StatusBadRequest, gin.H{
				"success": false,
				"error":   "解码消息失败",
			})
			return
		}

		// 验证消息
		if msg.Header == nil {
			c.JSON(http.StatusBadRequest, gin.H{
				"success": false,
				"error":   "无效的消息格式",
			})
			return
		}

		// 将消息存入上下文
		c.Set("agent_message", msg)
		c.Set("message_id", msg.Header.MessageID)
		c.Set("agent_type", msg.Header.TargetAgent)

		// 继续处理
		c.Next()
	}
}

// WrapResponse 包装响应
func (m *AgentCommunication) WrapResponse() gin.HandlerFunc {
	return func(c *gin.Context) {
		// 获取原始响应写入器
		w := c.Writer

		// 创建缓冲写入器
		buf := &bytes.Buffer{}
		c.Writer = &responseWriter{
			ResponseWriter: w,
			buffer:         buf,
		}

		c.Next()

		// 如果有Agent消息，包装响应
		if msg, exists := c.Get("agent_message"); exists {
			if agentMsg, ok := msg.(*protocol.AgentMessage); ok {
				// 创建响应消息
				respMsg := m.messageFactory.CreateTaskResponse(
					getTaskID(agentMsg),
					c.Writer.Status() == 200,
					buf.String(),
					getErrorMessage(c),
				)

				// 编码响应
				data, err := m.codec.Encode(respMsg)
				if err != nil {
					c.JSON(http.StatusInternalServerError, gin.H{
						"success": false,
						"error":   "编码响应失败",
					})
					return
				}

				// 写入响应
				w.Header().Set("Content-Type", "application/json")
				w.Write(data)
				return
			}
		}

		// 没有Agent消息，直接返回原始响应
		w.Write(buf.Bytes())
	}
}

type responseWriter struct {
	gin.ResponseWriter
	buffer *bytes.Buffer
}

func (w *responseWriter) Write(b []byte) (int, error) {
	return w.buffer.Write(b)
}

func getTaskID(msg *protocol.AgentMessage) string {
	if taskReq, ok := msg.Body.(*protocol.AgentMessage_TaskRequest); ok {
		return taskReq.TaskRequest.TaskID
	}
	return ""
}

func getErrorMessage(c *gin.Context) string {
	if len(c.Errors) > 0 {
		return c.Errors.String()
	}
	return ""
}
```

**步骤2.1.5**: 编写测试 (6小时)

**交付物**:
- ✅ 统一通信协议定义 (protobuf)
- ✅ 协议编解码器 (~150行)
- ✅ Agent客户端 (~200行)
- ✅ 通信中间件 (~150行)
- ✅ 测试代码 (~200行)

---

#### 任务2.2: 端口规范化 (3天)

**目标**: 统一所有服务的端口配置

**现状分析**:
- Gateway: 8005 ✅
- WebSocket: 8005 (集成) ✅
- Agent服务: 端口分散 ❌
- 监控服务: 端口不统一 ❌

**实施步骤**:

**步骤2.2.1**: 定义端口分配标准 (2小时)

**文件**: `config/port_allocation.yaml`

```yaml
# Athena端口分配标准
#
# 范围分配:
# - 8000-8099: 核心服务
# - 8100-8199: Agent服务
# - 8200-8299: 协作模式
# - 8300-8399: 工具服务
# - 9000-9099: 监控和管理
# - 3000-3099: 前端服务

services:
  # 核心服务 (8000-8099)
  gateway:
    port: 8005
    description: "统一Gateway"

  websocket:
    port: 8005  # 与Gateway共享
    description: "WebSocket控制平面"

  # Agent服务 (8100-8199)
  xiaona_agent:
    port: 8101
    description: "小娜法律专家"

  xiaonuo_agent:
    port: 8102
    description: "小诺协调器"

  yunxi_agent:
    port: 8103
    description: "云熙IP管理"

  # 协作模式 (8200-8299)
  coordinator:
    port: 8201
    description: "Coordinator模式"

  swarm:
    port: 8202
    description: "Swarm模式"

  canvas_host:
    port: 8203
    description: "Canvas Host服务"

  # 工具服务 (8300-8399)
  vector_service:
    port: 8301
    description: "向量检索服务"

  llm_service:
    port: 8302
    description: "LLM服务"

  embedding_service:
    port: 8303
    description: "嵌入服务"

  # 监控和管理 (9000-9099)
  prometheus:
    port: 9090
    description: "Prometheus监控"

  grafana:
    port: 9000  # 保持默认
    description: "Grafana可视化"

  metrics_exporter:
    port: 9091
    description: "Gateway指标导出"

  # 前端服务 (3000-3099)
  web_ui:
    port: 3000
    description: "Web前端界面"

  patent_search_ui:
    port: 3001
    description: "专利检索前端"
```

**步骤2.2.2**: 创建端口管理工具 (4小时)

**文件**: `tools/port_manager.py`

```python
#!/usr/bin/env python3
"""
Athena端口管理工具

功能:
- 检查端口占用
- 分配新端口
- 验证端口配置
- 生成端口报告
"""

import socket
import subprocess
import yaml
from pathlib import Path
from typing import Dict, List, Optional


class PortManager:
    """端口管理器"""

    def __init__(self, config_path: str = "config/port_allocation.yaml"):
        self.config_path = Path(config_path)
        self.config = self._load_config()

    def _load_config(self) -> dict:
        """加载端口配置"""
        if not self.config_path.exists():
            return {}

        with open(self.config_path) as f:
            return yaml.safe_load(f)

    def is_port_in_use(self, port: int) -> bool:
        """检查端口是否被占用"""
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            return s.connect_ex(("localhost", port)) == 0

    def get_service_port(self, service_name: str) -> Optional[int]:
        """获取服务端口"""
        services = self.config.get("services", {})
        service = services.get(service_name, {})
        return service.get("port")

    def allocate_port(self, service_name: str, preferred_port: Optional[int] = None) -> int:
        """分配端口"""
        if preferred_port:
            if not self.is_port_in_use(preferred_port):
                return preferred_port

        # 自动分配端口
        for port in range(8100, 8199):
            if not self.is_port_in_use(port):
                return port

        raise RuntimeError("没有可用端口")

    def check_all_ports(self) -> Dict[str, bool]:
        """检查所有服务端口状态"""
        result = {}
        services = self.config.get("services", {})

        for service_name, service_config in services.items():
            port = service_config.get("port")
            if port:
                result[service_name] = self.is_port_in_use(port)

        return result

    def generate_report(self) -> str:
        """生成端口报告"""
        report = []
        report.append("=" * 60)
        report.append("Athena端口使用报告")
        report.append("=" * 60)
        report.append("")

        services = self.config.get("services", {})
        status = self.check_all_ports()

        for service_name, service_config in services.items():
            port = service_config.get("port")
            description = service_config.get("description", "")
            in_use = status.get(service_name, False)

            status_icon = "✓" if in_use else "✗"
            report.append(f"{status_icon} {service_name:20} : {port:5} - {description}")

        report.append("")
        report.append("=" * 60)

        return "\n".join(report)


def main():
    """主函数"""
    import sys

    manager = PortManager()

    if len(sys.argv) > 1:
        command = sys.argv[1]

        if command == "check":
            print(manager.generate_report())
        elif command == "allocate":
            if len(sys.argv) > 2:
                service = sys.argv[2]
                port = manager.allocate_port(service)
                print(f"为服务 {service} 分配端口: {port}")
        else:
            print(f"未知命令: {command}")
    else:
        print(manager.generate_report())


if __name__ == "__main__":
    main()
```

**步骤2.2.3**: 更新服务配置 (4小时)

**步骤2.2.4**: 编写端口检查测试 (2小时)

**交付物**:
- ✅ 端口分配标准文档
- ✅ 端口管理工具 (~200行)
- ✅ 更新的服务配置
- ✅ 测试代码 (~100行)

---

### 阶段3: P2任务 (12天)

#### 任务3.1: API版本管理 (5天)

**目标**: 实现完整的API版本管理

**实施步骤**:

**步骤3.1.1**: 实现版本路由中间件

**步骤3.1.2**: 添加版本弃用机制

**步骤3.1.3**: 实现版本兼容性检查

**步骤3.1.4**: 编写版本管理文档

**交付物**:
- ✅ 版本路由中间件 (~150行)
- ✅ 版本管理API (~100行)
- ✅ 版本文档

---

#### 任务3.2: 安全增强 (7天)

**目标**: 加强Gateway安全性

**实施步骤**:

**步骤3.2.1**: 实现JWT认证 (8小时)

**步骤3.2.2**: 添加API密钥管理 (6小时)

**步骤3.2.3**: 实现IP白名单 (4小时)

**步骤3.2.4**: 添加请求签名验证 (6小时)

**步骤3.2.5**: 实现速率限制增强 (8小时)

**步骤3.2.6**: 添加安全审计日志 (6小时)

**步骤3.2.7**: 编写安全测试 (6小时)

**交付物**:
- ✅ JWT认证模块 (~200行)
- ✅ API密钥管理 (~150行)
- ✅ IP白名单 (~100行)
- ✅ 请求签名验证 (~150行)
- ✅ 速率限制增强 (~200行)
- ✅ 审计日志 (~150行)
- ✅ 安全测试 (~200行)

---

## 测试验证方案

### 单元测试

每个模块都需要完整的单元测试覆盖：

```bash
# Gateway测试
cd gateway-unified
go test ./internal/gateway/... -v -cover

# 配置测试
go test ./internal/config/... -v -cover

# 服务发现测试
go test ./internal/discovery/... -v -cover

# 协议测试
go test ./internal/protocol/... -v -cover

# Agent通信测试
go test ./internal/agent/... -v -cover
```

### 集成测试

**文件**: `tests/integration/gateway_integration_test.py`

```python
"""Gateway集成测试"""

import pytest
import requests
import json


class TestGatewayIntegration:
    """Gateway集成测试"""

    @pytest.fixture(scope="module")
    def gateway_url(self):
        return "http://localhost:8005"

    def test_health_check(self, gateway_url):
        """测试健康检查"""
        resp = requests.get(f"{gateway_url}/health")
        assert resp.status_code == 200
        data = resp.json()
        assert data["success"] is True

    def test_route_configuration(self, gateway_url):
        """测试路由配置"""
        resp = requests.get(f"{gateway_url}/api/routes")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data["data"]) > 0

    def test_service_discovery(self, gateway_url):
        """测试服务发现"""
        resp = requests.get(f"{gateway_url}/api/services/instances")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data["data"]) > 0

    def test_agent_communication(self, gateway_url):
        """测试Agent通信"""
        # 准备任务请求
        task_req = {
            "header": {
                "message_id": "test_001",
                "type": "TASK_REQUEST",
                "target_agent": "XIAONA",
                "session_id": "test_session",
            },
            "body": {
                "task_request": {
                    "task_id": "task_001",
                    "task_type": "patent_analysis",
                    "parameters": {"patent_id": "CN123456789A"},
                }
            }
        }

        # 发送请求
        resp = requests.post(
            f"{gateway_url}/api/xiaona/task",
            json=task_req,
            headers={"Content-Type": "application/json"},
        )

        assert resp.status_code in [200, 202]
```

### 性能测试

**文件**: `tests/performance/gateway_benchmark_test.go`

```go
package performance

import (
	"testing"
	"net/http"
	"sync"
)

func BenchmarkGatewayRouting(b *testing.B) {
	client := &http.Client{}

	b.ResetTimer()
	b.RunParallel(func(pb *testing.PB) {
		for pb.Next() {
			resp, err := client.Get("http://localhost:8005/health")
			if err != nil {
				b.Fatal(err)
			}
			resp.Body.Close()
		}
	})
}
```

---

## 风险点和缓解措施

### 风险1: 服务迁移导致中断

**风险等级**: 高

**缓解措施**:
1. 采用蓝绿部署策略
2. 保留旧服务并行运行
3. 逐步切换流量 (10% → 50% → 100%)
4. 保留快速回滚机制

### 风险2: 配置错误导致服务不可用

**风险等级**: 中

**缓解措施**:
1. 配置验证工具
2. 配置测试环境
3. 配置版本控制
4. 配置回滚机制

### 风险3: 性能回归

**风险等级**: 中

**缓解措施**:
1. 建立性能基准
2. 每个阶段进行性能测试
3. 监控关键指标
4. 及时优化热点

### 风险4: 测试覆盖不足

**风险等级**: 中

**缓解措施**:
1. 强制测试覆盖率 > 80%
2. 代码审查必须检查测试
3. 集成测试覆盖关键路径
4. 端到端测试验证完整流程

---

## 回滚方案

### 快速回滚

**触发条件**:
- 核心服务不可用 > 5分钟
- 错误率 > 10%
- 性能下降 > 50%

**回滚步骤**:
1. 停止新服务
2. 启动旧版本服务
3. 恢复旧配置
4. 验证服务状态

### 配置回滚

**触发条件**:
- 配置加载失败
- 路由规则错误
- 服务注册失败

**回滚步骤**:
1. 使用Git恢复配置文件
2. 重启Gateway
3. 验证配置

### 数据回滚

**触发条件**:
- 数据迁移失败
- 数据不一致

**回滚步骤**:
1. 停止数据迁移
2. 从备份恢复数据
3. 验证数据一致性

---

## 验收标准

### 功能完整性

- [ ] 所有P0任务完成 (路由配置 + 服务发现)
- [ ] 所有P1任务完成 (Agent通信 + 端口规范)
- [ ] 所有P2任务完成 (API版本 + 安全增强)
- [ ] 所有测试通过 (单元 + 集成 + 性能)

### 质量标准

- [ ] 测试覆盖率 > 80%
- [ ] 代码审查通过
- [ ] 无严重bug
- [ ] 文档完整

### 性能标准

- [ ] API响应时间 < 100ms (P95)
- [ ] Gateway吞吐量 > 1000 QPS
- [ ] 内存使用 < 512MB
- [ ] CPU使用 < 50% (正常负载)

---

## 进度跟踪

### 里程碑

| 里程碑 | 日期 | 交付物 | 状态 |
|--------|------|--------|------|
| M1: P0完成 | Day 5 | 路由配置 + 服务发现 | ⏳ |
| M2: P1完成 | Day 13 | Agent通信 + 端口规范 | ⏳ |
| M3: P2完成 | Day 25 | API版本 + 安全增强 | ⏳ |

### 每日检查

- [ ] 代码提交
- [ ] 测试通过
- [ ] 文档更新
- [ ] 问题跟踪

---

## 附录

### A. 文件修改清单

#### 新增文件

```
gateway-unified/
├── config/
│   └── routes.yaml                    # 路由配置
├── internal/
│   ├── config/
│   │   └── routes_loader.go           # 路由加载器
│   ├── discovery/
│   │   ├── adapter.go                 # 服务发现适配器
│   │   └── health_checker.go          # 健康检查器
│   ├── protocol/
│   │   ├── agent_message.proto        # 协议定义
│   │   └── codec.go                   # 编解码器
│   ├── agent/
│   │   └── client.go                  # Agent客户端
│   └── middleware/
│       └── agent_comm.go              # Agent通信中间件
tools/
└── port_manager.py                    # 端口管理工具
tests/
├── integration/
│   └── gateway_integration_test.py    # 集成测试
└── performance/
    └── gateway_benchmark_test.go      # 性能测试
```

#### 修改文件

```
gateway-unified/
├── cmd/gateway/main.go                # 集成服务发现
├── internal/gateway/
│   ├── routes.go                      # 添加路由验证
│   └── gateway.go                     # 集成新功能
└── internal/handlers/
    └── discovery.go                   # 服务发现API
```

### B. 依赖清单

```go
// 新增Go依赖
require (
    github.com/gorilla/websocket v1.5.0
    gopkg.in/yaml.v3 v3.0.1
    github.com/golang-jwt/jwt v5.0.0
    github.com/stretchr/testify v1.8.4
)
```

---

**计划状态**: ✅ 已完成
**准备开始**: 等待确认

---

**制定者**: Claude Code + Agent Team
**审核者**: 待指定
**批准者**: 徐健
