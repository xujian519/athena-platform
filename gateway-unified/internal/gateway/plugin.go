package gateway

import (
	"context"
	"fmt"
	"sync"
)

// PluginContext 插件上下文
type PluginContext struct {
	// RequestID 请求ID
	RequestID string
	// ServiceName 目标服务名
	ServiceName string
	// Method 请求方法
	Method string
	// Path 请求路径
	Path string
	// Metadata 元数据
	Metadata map[string]interface{}
}

// PluginPhase 插件执行阶段
type PluginPhase int

const (
	// PhaseBeforeRequest 请求前阶段
	PhaseBeforeRequest PluginPhase = iota
	// PhaseAfterRequest 请求后阶段
	PhaseAfterRequest
	// PhaseOnError 错误阶段
	PhaseOnError
)

// Plugin 插件接口
type Plugin interface {
	// Name 插件名称
	Name() string
	// Init 初始化插件
	Init(config map[string]interface{}) error
	// Execute 执行插件逻辑
	Execute(ctx context.Context, pluginCtx *PluginContext) error
	// Phase 插件执行阶段
	Phase() PluginPhase
	// Priority 插件优先级（数字越小越先执行）
	Priority() int
	// Shutdown 关闭插件
	Shutdown() error
}

// BasePlugin 基础插件
type BasePlugin struct {
	name     string
	phase    PluginPhase
	priority int
	config   map[string]interface{}
}

// NewBasePlugin 创建基础插件
func NewBasePlugin(name string, phase PluginPhase, priority int) *BasePlugin {
	return &BasePlugin{
		name:     name,
		phase:    phase,
		priority: priority,
		config:   make(map[string]interface{}),
	}
}

// Name 返回插件名称
func (p *BasePlugin) Name() string {
	return p.name
}

// Init 初始化插件
func (p *BasePlugin) Init(config map[string]interface{}) error {
	p.config = config
	return nil
}

// Execute 执行插件逻辑（基类默认实现）
func (p *BasePlugin) Execute(ctx context.Context, pluginCtx *PluginContext) error {
	return nil
}

// Phase 返回插件执行阶段
func (p *BasePlugin) Phase() PluginPhase {
	return p.phase
}

// Priority 返回插件优先级
func (p *BasePlugin) Priority() int {
	return p.priority
}

// Shutdown 关闭插件
func (p *BasePlugin) Shutdown() error {
	return nil
}

// PluginManager 插件管理器
type PluginManager struct {
	plugins     map[string]Plugin
	pluginsByPhase map[PluginPhase][]Plugin
	mu          sync.RWMutex
}

// NewPluginManager 创建插件管理器
func NewPluginManager() *PluginManager {
	return &PluginManager{
		plugins:        make(map[string]Plugin),
		pluginsByPhase: make(map[PluginPhase][]Plugin),
	}
}

// Register 注册插件
func (pm *PluginManager) Register(plugin Plugin) error {
	if plugin == nil {
		return fmt.Errorf("插件不能为空")
	}

	pm.mu.Lock()
	defer pm.mu.Unlock()

	name := plugin.Name()
	if _, exists := pm.plugins[name]; exists {
		return fmt.Errorf("插件 %s 已存在", name)
	}

	pm.plugins[name] = plugin

	// 按阶段组织插件
	phase := plugin.Phase()
	pm.pluginsByPhase[phase] = append(pm.pluginsByPhase[phase], plugin)

	// 按优先级排序
	pm.sortPluginsByPriority(phase)

	return nil
}

// Unregister 注销插件
func (pm *PluginManager) Unregister(name string) error {
	pm.mu.Lock()
	defer pm.mu.Unlock()

	plugin, exists := pm.plugins[name]
	if !exists {
		return fmt.Errorf("插件 %s 不存在", name)
	}

	// 从阶段列表中移除
	phase := plugin.Phase()
	plugins := pm.pluginsByPhase[phase]
	for i, p := range plugins {
		if p.Name() == name {
			pm.pluginsByPhase[phase] = append(plugins[:i], plugins[i+1:]...)
			break
		}
	}

	// 关闭插件
	plugin.Shutdown()

	delete(pm.plugins, name)
	return nil
}

// Get 获取插件
func (pm *PluginManager) Get(name string) (Plugin, bool) {
	pm.mu.RLock()
	defer pm.mu.RUnlock()

	plugin, exists := pm.plugins[name]
	return plugin, exists
}

// GetAll 获取所有插件
func (pm *PluginManager) GetAll() map[string]Plugin {
	pm.mu.RLock()
	defer pm.mu.RUnlock()

	result := make(map[string]Plugin, len(pm.plugins))
	for k, v := range pm.plugins {
		result[k] = v
	}
	return result
}

// ExecutePhase 执行指定阶段的所有插件
func (pm *PluginManager) ExecutePhase(ctx context.Context, phase PluginPhase, pluginCtx *PluginContext) error {
	pm.mu.RLock()
	defer pm.mu.RUnlock()

	plugins, exists := pm.pluginsByPhase[phase]
	if !exists || len(plugins) == 0 {
		return nil
	}

	// 按优先级顺序执行插件
	for _, plugin := range plugins {
		if err := plugin.Execute(ctx, pluginCtx); err != nil {
			// 插件执行失败，记录错误但继续执行其他插件
			fmt.Printf("[插件] 插件 %s 执行失败: %v\n", plugin.Name(), err)
		}
	}

	return nil
}

// sortPluginsByPriority 按优先级排序插件
func (pm *PluginManager) sortPluginsByPriority(phase PluginPhase) {
	plugins := pm.pluginsByPhase[phase]

	// 简单的冒泡排序（按优先级升序）
	n := len(plugins)
	for i := 0; i < n-1; i++ {
		for j := 0; j < n-i-1; j++ {
			if plugins[j].Priority() > plugins[j+1].Priority() {
				plugins[j], plugins[j+1] = plugins[j+1], plugins[j]
			}
		}
	}
}

// Shutdown 关闭所有插件
func (pm *PluginManager) Shutdown() error {
	pm.mu.Lock()
	defer pm.mu.Unlock()

	var lastErr error
	for _, plugin := range pm.plugins {
		if err := plugin.Shutdown(); err != nil {
			fmt.Printf("[插件] 关闭插件 %s 失败: %v\n", plugin.Name(), err)
			lastErr = err
		}
	}

	// 清空插件列表
	pm.plugins = make(map[string]Plugin)
	pm.pluginsByPhase = make(map[PluginPhase][]Plugin)

	return lastErr
}

// ============================================
// 预定义插件
// ============================================

// AuthPlugin 认证插件
type AuthPlugin struct {
	*BasePlugin
	validateToken func(string) bool
}

// NewAuthPlugin 创建认证插件
func NewAuthPlugin() *AuthPlugin {
	return &AuthPlugin{
		BasePlugin: NewBasePlugin("auth", PhaseBeforeRequest, 100),
	}
}

// Init 初始化认证插件
func (p *AuthPlugin) Init(config map[string]interface{}) error {
	if err := p.BasePlugin.Init(config); err != nil {
		return err
	}

	// 这里可以配置token验证函数
	// 默认实现：所有token都有效
	p.validateToken = func(token string) bool {
		return token != ""
	}

	return nil
}

// Execute 执行认证
func (p *AuthPlugin) Execute(ctx context.Context, pluginCtx *PluginContext) error {
	// 从上下文中获取token
	if pluginCtx.Metadata == nil {
		return fmt.Errorf("未找到认证信息")
	}

	token, ok := pluginCtx.Metadata["authorization"].(string)
	if !ok || token == "" {
		return fmt.Errorf("缺少认证token")
	}

	// 验证token
	if !p.validateToken(token) {
		return fmt.Errorf("无效的认证token")
	}

	return nil
}

// RateLimitPlugin 限流插件
type RateLimitPlugin struct {
	*BasePlugin
	rateLimiter map[string]int // 简单实现：每个IP的请求计数
	mu          sync.RWMutex
	maxRequests int
}

// NewRateLimitPlugin 创建限流插件
func NewRateLimitPlugin(maxRequests int) *RateLimitPlugin {
	return &RateLimitPlugin{
		BasePlugin:  NewBasePlugin("rate_limit", PhaseBeforeRequest, 90),
		rateLimiter: make(map[string]int),
		maxRequests: maxRequests,
	}
}

// Init 初始化限流插件
func (p *RateLimitPlugin) Init(config map[string]interface{}) error {
	if err := p.BasePlugin.Init(config); err != nil {
		return err
	}

	if maxRequests, ok := config["max_requests"].(int); ok {
		p.maxRequests = maxRequests
	}

	return nil
}

// Execute 执行限流
func (p *RateLimitPlugin) Execute(ctx context.Context, pluginCtx *PluginContext) error {
	// 从请求中提取客户端标识（如IP）
	clientID := "default"
	if pluginCtx.Metadata != nil {
		if ip, ok := pluginCtx.Metadata["client_ip"].(string); ok {
			clientID = ip
		}
	}

	p.mu.Lock()
	defer p.mu.Unlock()

	count := p.rateLimiter[clientID]
	if count >= p.maxRequests {
		return fmt.Errorf("超过限流阈值")
	}

	p.rateLimiter[clientID] = count + 1
	return nil
}

// LoggingPlugin 日志插件
type LoggingPlugin struct {
	*BasePlugin
}

// NewLoggingPlugin 创建日志插件
func NewLoggingPlugin() *LoggingPlugin {
	return &LoggingPlugin{
		BasePlugin: NewBasePlugin("logging", PhaseBeforeRequest, 10),
	}
}

// Execute 执行日志记录
func (p *LoggingPlugin) Execute(ctx context.Context, pluginCtx *PluginContext) error {
	fmt.Printf("[日志] 请求: %s %s (ID: %s)\n",
		pluginCtx.Method,
		pluginCtx.Path,
		pluginCtx.RequestID,
	)
	return nil
}

// MetricsPlugin 监控插件
type MetricsPlugin struct {
	*BasePlugin
	requestCount map[string]int64
	mu           sync.RWMutex
}

// NewMetricsPlugin 创建监控插件
func NewMetricsPlugin() *MetricsPlugin {
	return &MetricsPlugin{
		BasePlugin:  NewBasePlugin("metrics", PhaseAfterRequest, 10),
		requestCount: make(map[string]int64),
	}
}

// Execute 执行监控指标收集
func (p *MetricsPlugin) Execute(ctx context.Context, pluginCtx *PluginContext) error {
	p.mu.Lock()
	defer p.mu.Unlock()

	key := fmt.Sprintf("%s:%s", pluginCtx.ServiceName, pluginCtx.Method)
	p.requestCount[key]++

	return nil
}

// GetMetrics 获取监控指标
func (p *MetricsPlugin) GetMetrics() map[string]int64 {
	p.mu.RLock()
	defer p.mu.RUnlock()

	metrics := make(map[string]int64, len(p.requestCount))
	for k, v := range p.requestCount {
		metrics[k] = v
	}
	return metrics
}

// CORSPlugin CORS插件
type CORSPlugin struct {
	*BasePlugin
	allowedOrigins     []string
	allowedMethods     []string
	allowedHeaders     []string
	allowCredentials   bool
}

// NewCORSPlugin 创建CORS插件
func NewCORSPlugin() *CORSPlugin {
	return &CORSPlugin{
		BasePlugin:       NewBasePlugin("cors", PhaseBeforeRequest, 80),
		allowedOrigins:   []string{"*"},
		allowedMethods:   []string{"GET", "POST", "PUT", "DELETE", "OPTIONS"},
		allowedHeaders:   []string{"Content-Type", "Authorization"},
		allowCredentials: false,
	}
}

// Init 初始化CORS插件
func (p *CORSPlugin) Init(config map[string]interface{}) error {
	if err := p.BasePlugin.Init(config); err != nil {
		return err
	}

	if origins, ok := config["allowed_origins"].([]string); ok {
		p.allowedOrigins = origins
	}
	if methods, ok := config["allowed_methods"].([]string); ok {
		p.allowedMethods = methods
	}
	if headers, ok := config["allowed_headers"].([]string); ok {
		p.allowedHeaders = headers
	}
	if credentials, ok := config["allow_credentials"].(bool); ok {
		p.allowCredentials = credentials
	}

	return nil
}

// Execute 执行CORS检查
func (p *CORSPlugin) Execute(ctx context.Context, pluginCtx *PluginContext) error {
	// 在实际实现中，这里会设置CORS响应头
	// 由于这是在请求阶段，我们只做验证
	return nil
}
