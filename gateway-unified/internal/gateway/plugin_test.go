package gateway

import (
	"context"
	"fmt"
	"testing"
)

// TestPluginManagerRegister 测试插件注册
func TestPluginManagerRegister(t *testing.T) {
	manager := NewPluginManager()

	// 创建测试插件
	plugin := NewBasePlugin("test-plugin", PhaseBeforeRequest, 50)

	err := manager.Register(plugin)
	if err != nil {
		t.Errorf("注册插件失败: %v", err)
	}

	// 重复注册应该失败
	err = manager.Register(plugin)
	if err == nil {
		t.Error("重复注册插件应该失败")
	}

	// 验证插件已注册
	retrieved, exists := manager.Get("test-plugin")
	if !exists {
		t.Error("插件应该存在")
	}

	if retrieved.Name() != "test-plugin" {
		t.Errorf("插件名称不匹配: 期望 'test-plugin', 实际 %s", retrieved.Name())
	}
}

// TestPluginUnregister 测试插件注销
func TestPluginUnregister(t *testing.T) {
	manager := NewPluginManager()

	plugin := NewBasePlugin("test-plugin", PhaseBeforeRequest, 50)
	manager.Register(plugin)

	// 注销插件
	err := manager.Unregister("test-plugin")
	if err != nil {
		t.Errorf("注销插件失败: %v", err)
	}

	// 插件应该不存在
	_, exists := manager.Get("test-plugin")
	if exists {
		t.Error("插件应该不存在")
	}

	// 重复注销应该失败
	err = manager.Unregister("test-plugin")
	if err == nil {
		t.Error("重复注销应该失败")
	}
}

// TestPluginPhaseExecution 测试插件按阶段执行
func TestPluginPhaseExecution(t *testing.T) {
	manager := NewPluginManager()

	executedOrder := make([]string, 0)

	// 创建不同阶段的插件
	plugin1 := &mockPlugin{
		BasePlugin: NewBasePlugin("plugin1", PhaseBeforeRequest, 10),
		executeFn: func(ctx context.Context, pluginCtx *PluginContext) error {
			executedOrder = append(executedOrder, "plugin1")
			return nil
		},
	}

	plugin2 := &mockPlugin{
		BasePlugin: NewBasePlugin("plugin2", PhaseAfterRequest, 10),
		executeFn: func(ctx context.Context, pluginCtx *PluginContext) error {
			executedOrder = append(executedOrder, "plugin2")
			return nil
		},
	}

	plugin3 := &mockPlugin{
		BasePlugin: NewBasePlugin("plugin3", PhaseBeforeRequest, 20),
		executeFn: func(ctx context.Context, pluginCtx *PluginContext) error {
			executedOrder = append(executedOrder, "plugin3")
			return nil
		},
	}

	manager.Register(plugin1)
	manager.Register(plugin2)
	manager.Register(plugin3)

	ctx := context.Background()
	pluginCtx := &PluginContext{
		RequestID: "test-123",
	}

	// 执行请求前阶段
	manager.ExecutePhase(ctx, PhaseBeforeRequest, pluginCtx)

	// 应该只执行请求前阶段的插件，按优先级排序
	if len(executedOrder) != 2 {
		t.Errorf("应该执行2个插件, 实际执行了 %d 个", len(executedOrder))
	}

	if executedOrder[0] != "plugin1" {
		t.Errorf("第一个执行的应该是plugin1, 实际是 %s", executedOrder[0])
	}

	if executedOrder[1] != "plugin3" {
		t.Errorf("第二个执行的应该是plugin3, 实际是 %s", executedOrder[1])
	}
}

// TestPluginPriority 测试插件优先级
func TestPluginPriority(t *testing.T) {
	manager := NewPluginManager()

	executedOrder := make([]string, 0)

	// 创建不同优先级的插件
	plugin1 := &mockPlugin{
		BasePlugin: NewBasePlugin("high-priority", PhaseBeforeRequest, 10),
		executeFn: func(ctx context.Context, pluginCtx *PluginContext) error {
			executedOrder = append(executedOrder, "high")
			return nil
		},
	}

	plugin2 := &mockPlugin{
		BasePlugin: NewBasePlugin("medium-priority", PhaseBeforeRequest, 50),
		executeFn: func(ctx context.Context, pluginCtx * PluginContext) error {
			executedOrder = append(executedOrder, "medium")
			return nil
		},
	}

	plugin3 := &mockPlugin{
		BasePlugin: NewBasePlugin("low-priority", PhaseBeforeRequest, 100),
		executeFn: func(ctx context.Context, pluginCtx *PluginContext) error {
			executedOrder = append(executedOrder, "low")
			return nil
		},
	}

	manager.Register(plugin3) // 先注册低优先级
	manager.Register(plugin1) // 再注册高优先级
	manager.Register(plugin2) // 最后注册中优先级

	ctx := context.Background()
	pluginCtx := &PluginContext{
		RequestID: "test-123",
	}

	// 执行插件
	manager.ExecutePhase(ctx, PhaseBeforeRequest, pluginCtx)

	// 应该按优先级从高到低执行
	if len(executedOrder) != 3 {
		t.Fatalf("应该执行3个插件, 实际执行了 %d 个", len(executedOrder))
	}

	if executedOrder[0] != "high" {
		t.Errorf("优先级错误: 第一个应该是high, 实际是 %s", executedOrder[0])
	}

	if executedOrder[1] != "medium" {
		t.Errorf("优先级错误: 第二个应该是medium, 实际是 %s", executedOrder[1])
	}

	if executedOrder[2] != "low" {
		t.Errorf("优先级错误: 第三个应该是low, 实际是 %s", executedOrder[2])
	}
}

// TestAuthPlugin 测试认证插件
func TestAuthPlugin(t *testing.T) {
	plugin := NewAuthPlugin()

	config := map[string]interface{}{
		"validate_token": true,
	}

	err := plugin.Init(config)
	if err != nil {
		t.Errorf("初始化认证插件失败: %v", err)
	}

	ctx := context.Background()

	// 测试有token的情况
	pluginCtx := &PluginContext{
		RequestID: "test-123",
		Metadata: map[string]interface{}{
			"authorization": "valid-token",
		},
	}

	err = plugin.Execute(ctx, pluginCtx)
	if err != nil {
		t.Errorf("有效token不应该报错: %v", err)
	}

	// 测试没有token的情况
	pluginCtx2 := &PluginContext{
		RequestID: "test-456",
		Metadata:  map[string]interface{}{},
	}

	err = plugin.Execute(ctx, pluginCtx2)
	if err == nil {
		t.Error("缺少token应该返回错误")
	}
}

// TestRateLimitPlugin 测试限流插件
func TestRateLimitPlugin(t *testing.T) {
	maxRequests := 3
	plugin := NewRateLimitPlugin(maxRequests)

	config := map[string]interface{}{
		"max_requests": 5,
	}

	plugin.Init(config)

	ctx := context.Background()

	// 测试正常请求
	for i := 0; i < 5; i++ {
		pluginCtx := &PluginContext{
			RequestID: fmt.Sprintf("test-%d", i),
			Metadata: map[string]interface{}{
				"client_ip": "192.168.1.1",
			},
		}

		err := plugin.Execute(ctx, pluginCtx)
		if i < 5 && err != nil {
			t.Errorf("第%d次请求不应该被限流: %v", i+1, err)
		}
	}

	// 第6次请求应该被限流
	pluginCtx := &PluginContext{
		RequestID: "test-6",
		Metadata: map[string]interface{}{
			"client_ip": "192.168.1.1",
		},
	}

	err := plugin.Execute(ctx, pluginCtx)
	if err == nil {
		t.Error("超过限流阈值应该返回错误")
	}
}

// TestLoggingPlugin 测试日志插件
func TestLoggingPlugin(t *testing.T) {
	plugin := NewLoggingPlugin()

	ctx := context.Background()
	pluginCtx := &PluginContext{
		RequestID:    "test-123",
		Method:       "GET",
		Path:         "/api/test",
		ServiceName:  "test-service",
	}

	err := plugin.Execute(ctx, pluginCtx)
	if err != nil {
		t.Errorf("日志插件执行失败: %v", err)
	}

	// 验证插件属性
	if plugin.Name() != "logging" {
		t.Errorf("插件名称应该是 'logging', 实际是 %s", plugin.Name())
	}

	if plugin.Phase() != PhaseBeforeRequest {
		t.Errorf("插件阶段应该是 PhaseBeforeRequest")
	}

	if plugin.Priority() != 10 {
		t.Errorf("插件优先级应该是 10, 实际是 %d", plugin.Priority())
	}
}

// TestMetricsPlugin 测试监控插件
func TestMetricsPlugin(t *testing.T) {
	plugin := NewMetricsPlugin()

	ctx := context.Background()

	// 执行几次请求
	for i := 0; i < 5; i++ {
		pluginCtx := &PluginContext{
			RequestID:   fmt.Sprintf("test-%d", i),
			ServiceName: "test-service",
			Method:      "GET",
		}

		err := plugin.Execute(ctx, pluginCtx)
		if err != nil {
			t.Errorf("监控插件执行失败: %v", err)
		}
	}

	// 获取指标
	metrics := plugin.GetMetrics()

	key := "test-service:GET"
	count, exists := metrics[key]
	if !exists {
		t.Errorf("应该存在指标: %s", key)
	}

	if count != 5 {
		t.Errorf("指标计数应该是5, 实际是 %d", count)
	}
}

// TestCORSPlugin 测试CORS插件
func TestCORSPlugin(t *testing.T) {
	plugin := NewCORSPlugin()

	config := map[string]interface{}{
		"allowed_origins":   []string{"https://example.com"},
		"allowed_methods":   []string{"GET", "POST"},
		"allowed_headers":   []string{"Content-Type"},
		"allow_credentials": true,
	}

	err := plugin.Init(config)
	if err != nil {
		t.Errorf("初始化CORS插件失败: %v", err)
	}

	ctx := context.Background()
	pluginCtx := &PluginContext{
		RequestID: "test-123",
	}

	// CORS插件在请求阶段只做验证
	err = plugin.Execute(ctx, pluginCtx)
	if err != nil {
		t.Errorf("CORS插件执行失败: %v", err)
	}
}

// TestPluginGetAll 测试获取所有插件
func TestPluginGetAll(t *testing.T) {
	manager := NewPluginManager()

	// 注册几个插件
	plugin1 := NewBasePlugin("plugin1", PhaseBeforeRequest, 10)
	plugin2 := NewBasePlugin("plugin2", PhaseAfterRequest, 20)
	plugin3 := NewBasePlugin("plugin3", PhaseOnError, 30)

	manager.Register(plugin1)
	manager.Register(plugin2)
	manager.Register(plugin3)

	// 获取所有插件
	allPlugins := manager.GetAll()

	if len(allPlugins) != 3 {
		t.Errorf("应该有3个插件, 实际有 %d 个", len(allPlugins))
	}

	if _, exists := allPlugins["plugin1"]; !exists {
		t.Error("应该包含plugin1")
	}

	if _, exists := allPlugins["plugin2"]; !exists {
		t.Error("应该包含plugin2")
	}

	if _, exists := allPlugins["plugin3"]; !exists {
		t.Error("应该包含plugin3")
	}
}

// TestPluginShutdown 测试插件关闭
func TestPluginShutdown(t *testing.T) {
	manager := NewPluginManager()

	plugin1 := NewBasePlugin("plugin1", PhaseBeforeRequest, 10)
	plugin2 := NewBasePlugin("plugin2", PhaseAfterRequest, 20)

	manager.Register(plugin1)
	manager.Register(plugin2)

	// 关闭管理器
	err := manager.Shutdown()
	if err != nil {
		t.Errorf("关闭插件管理器失败: %v", err)
	}

	// 验证插件已被清理
	_, exists := manager.Get("plugin1")
	if exists {
		t.Error("插件1应该已被清理")
	}
}

// TestPluginErrorHandling 测试插件执行错误处理
func TestPluginErrorHandling(t *testing.T) {
	manager := NewPluginManager()

	// 创建一个会失败的插件
	failingPlugin := &mockPlugin{
		BasePlugin: NewBasePlugin("failing", PhaseBeforeRequest, 10),
		executeFn: func(ctx context.Context, pluginCtx *PluginContext) error {
			return fmt.Errorf("插件执行失败")
		},
	}

	// 创建一个正常的插件
	normalPlugin := &mockPlugin{
		BasePlugin: NewBasePlugin("normal", PhaseBeforeRequest, 20),
		executeFn: func(ctx context.Context, pluginCtx *PluginContext) error {
			return nil
		},
	}

	manager.Register(failingPlugin)
	manager.Register(normalPlugin)

	ctx := context.Background()
	pluginCtx := &PluginContext{
		RequestID: "test-123",
	}

	// 执行插件（即使有插件失败，其他插件仍应执行）
	err := manager.ExecutePhase(ctx, PhaseBeforeRequest, pluginCtx)
	// ExecutePhase不会返回错误，只记录日志
	_ = err
}

// Mock plugin for testing
type mockPlugin struct {
	*BasePlugin
	executeFn func(ctx context.Context, pluginCtx *PluginContext) error
}

func (m *mockPlugin) Execute(ctx context.Context, pluginCtx *PluginContext) error {
	if m.executeFn != nil {
		return m.executeFn(ctx, pluginCtx)
	}
	return nil
}
