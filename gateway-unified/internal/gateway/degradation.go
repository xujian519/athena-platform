package gateway

import (
	"context"
	"encoding/json"
	"fmt"
	"sync"
	"time"
)

// DegradationType 降级类型
type DegradationType string

const (
	// TimeoutDegradation 超时降级
	TimeoutDegradation DegradationType = "timeout"
	// ErrorRateDegradation 错误率降级
	ErrorRateDegradation DegradationType = "error_rate"
	// ConcurrencyDegradation 并发量降级
	ConcurrencyDegradation DegradationType = "concurrency"
	// ManualDegradation 手动降级
	ManualDegradation DegradationType = "manual"
)

// DegradationStrategy 降级策略接口
type DegradationStrategy interface {
	// Execute 执行降级策略
	Execute(ctx context.Context, request interface{}) (interface{}, error)
	// Name 策略名称
	Name() string
	// Type 策略类型
	Type() DegradationType
}

// DegradationConfig 降级配置
type DegradationConfig struct {
	// Enabled 是否启用降级
	Enabled bool `json:"enabled"`
	// Timeout 超时阈值（毫秒）
	Timeout int64 `json:"timeout"`
	// ErrorThreshold 错误率阈值（百分比）
	ErrorThreshold float64 `json:"error_threshold"`
	// ConcurrencyThreshold 并发阈值
	ConcurrencyThreshold int `json:"concurrency_threshold"`
	// Strategy 降级策略
	Strategy DegradationStrategy `json:"-"`
	// AutoRecover 是否自动恢复
	AutoRecover bool `json:"auto_recover"`
	// RecoverInterval 恢复检查间隔
	RecoverInterval time.Duration `json:"recover_interval"`
}

// degradationStatus 降级状态
type degradationStatus struct {
	active      bool
	degradedAt  time.Time
	recoveredAt time.Time
	trigger     DegradationType
	errorCount  int
	totalCount  int
	concurrency int
	mu          sync.RWMutex
}

// DegradationManager 降级管理器
type DegradationManager struct {
	configs  map[string]*DegradationConfig
	statuses map[string]*degradationStatus
	mu       sync.RWMutex
	done     chan struct{}
}

// NewDegradationManager 创建降级管理器
func NewDegradationManager() *DegradationManager {
	dm := &DegradationManager{
		configs:  make(map[string]*DegradationConfig),
		statuses: make(map[string]*degradationStatus),
		done:     make(chan struct{}),
	}

	// 启动自动恢复检查
	go dm.autoRecoverChecker()

	return dm
}

// Register 注册服务降级配置
func (dm *DegradationManager) Register(serviceName string, config *DegradationConfig) error {
	dm.mu.Lock()
	defer dm.mu.Unlock()

	if config == nil {
		return fmt.Errorf("降级配置不能为空")
	}

	// 检查是否已存在
	if _, exists := dm.configs[serviceName]; exists {
		return fmt.Errorf("服务 %s 的降级配置已存在", serviceName)
	}

	// 设置默认值
	if config.RecoverInterval == 0 {
		config.RecoverInterval = 30 * time.Second
	}
	if config.Timeout == 0 {
		config.Timeout = 3000 // 默认3秒超时
	}
	if config.ErrorThreshold == 0 {
		config.ErrorThreshold = 50.0 // 默认50%错误率
	}
	if config.ConcurrencyThreshold == 0 {
		config.ConcurrencyThreshold = 100 // 默认100并发
	}

	dm.configs[serviceName] = config
	dm.statuses[serviceName] = &degradationStatus{
		active: false,
	}

	return nil
}

// Execute 执行请求（带降级保护）
func (dm *DegradationManager) Execute(ctx context.Context, serviceName string, request interface{}, handler func(context.Context, interface{}) (interface{}, error)) (interface{}, error) {
	// 检查是否需要降级
	if dm.shouldDegrade(serviceName) {
		return dm.executeFallback(ctx, serviceName, request)
	}

	// 执行实际请求
	startTime := time.Now()
	result, err := handler(ctx, request)
	duration := time.Since(startTime)

	// 记录执行结果
	dm.recordExecution(serviceName, err, duration)

	// 检查是否需要触发降级
	dm.checkAndTrigger(serviceName, err, duration)

	return result, err
}

// shouldDegrade 判断是否应该降级
func (dm *DegradationManager) shouldDegrade(serviceName string) bool {
	dm.mu.RLock()
	defer dm.mu.RUnlock()

	config, exists := dm.configs[serviceName]
	if !exists || !config.Enabled {
		return false
	}

	status, exists := dm.statuses[serviceName]
	if !exists {
		return false
	}

	status.mu.RLock()
	defer status.mu.RUnlock()
	return status.active
}

// executeFallback 执行降级策略
func (dm *DegradationManager) executeFallback(ctx context.Context, serviceName string, request interface{}) (interface{}, error) {
	dm.mu.RLock()
	defer dm.mu.RUnlock()

	config, exists := dm.configs[serviceName]
	if !exists || config.Strategy == nil {
		return nil, fmt.Errorf("服务 %s 已降级且无降级策略", serviceName)
	}

	return config.Strategy.Execute(ctx, request)
}

// recordExecution 记录执行结果
func (dm *DegradationManager) recordExecution(serviceName string, err error, duration time.Duration) {
	dm.mu.RLock()
	defer dm.mu.RUnlock()

	status, exists := dm.statuses[serviceName]
	if !exists {
		return
	}

	status.mu.Lock()
	defer status.mu.Unlock()

	status.totalCount++
	if err != nil {
		status.errorCount++
	}
}

// checkAndTrigger 检查并触发降级
func (dm *DegradationManager) checkAndTrigger(serviceName string, err error, duration time.Duration) {
	// 获取配置并检查是否需要触发
	dm.mu.RLock()
	config, exists := dm.configs[serviceName]
	dm.mu.RUnlock()

	if !exists || !config.Enabled {
		return
	}

	// 检查是否需要触发降级
	shouldTrigger := false
	triggerType := TimeoutDegradation

	dm.mu.Lock()
	status, statusExists := dm.statuses[serviceName]
	dm.mu.Unlock()

	if !statusExists {
		return
	}

	status.mu.Lock()
	active := status.active
	errorCount := status.errorCount
	totalCount := status.totalCount
	status.mu.Unlock()

	// 如果已经降级，不重复触发
	if active {
		return
	}

	// 检查超时降级
	if duration.Milliseconds() > config.Timeout {
		shouldTrigger = true
		triggerType = TimeoutDegradation
	}

	// 检查错误率降级
	if !shouldTrigger && totalCount >= 10 {
		errorRate := float64(errorCount) / float64(totalCount) * 100
		if errorRate >= config.ErrorThreshold {
			shouldTrigger = true
			triggerType = ErrorRateDegradation
		}
	}

	// 如果需要触发，调用触发方法
	if shouldTrigger {
		dm.triggerDegradation(serviceName, triggerType)
	}
}

// IncrementConcurrency 增加并发计数
func (dm *DegradationManager) IncrementConcurrency(serviceName string) {
	dm.mu.RLock()
	config, exists := dm.configs[serviceName]
	dm.mu.RUnlock()

	if !exists || !config.Enabled {
		return
	}

	status, exists := dm.statuses[serviceName]
	if !exists {
		return
	}

	status.mu.Lock()
	status.concurrency++

	// 检查是否需要触发降级（在持有status锁的情况下检查）
	shouldTrigger := status.concurrency >= config.ConcurrencyThreshold && !status.active
	status.mu.Unlock() // 释放status锁，避免死锁

	// 在释放status锁后再触发降级
	if shouldTrigger {
		dm.triggerDegradation(serviceName, ConcurrencyDegradation)
	}
}

// DecrementConcurrency 减少并发计数
func (dm *DegradationManager) DecrementConcurrency(serviceName string) {
	dm.mu.RLock()
	defer dm.mu.RUnlock()

	status, exists := dm.statuses[serviceName]
	if !exists {
		return
	}

	status.mu.Lock()
	defer status.mu.Unlock()

	if status.concurrency > 0 {
		status.concurrency--
	}
}

// triggerDegradation 触发降级
func (dm *DegradationManager) triggerDegradation(serviceName string, triggerType DegradationType) {
	// 不持有外层锁的情况下获取status
	dm.mu.Lock()
	status, exists := dm.statuses[serviceName]
	dm.mu.Unlock()

	if !exists {
		return
	}

	status.mu.Lock()
	defer status.mu.Unlock()

	if status.active {
		return // 已经降级
	}

	status.active = true
	status.degradedAt = time.Now()
	status.trigger = triggerType

	// 重置计数器
	status.errorCount = 0
	status.totalCount = 0

	// 记录日志
	fmt.Printf("[降级] 服务 %s 已触发降级，类型: %s\n", serviceName, triggerType)
}

// recoverDegradation 恢复服务
func (dm *DegradationManager) recoverDegradation(serviceName string) {
	// 获取配置
	dm.mu.Lock()
	config, exists := dm.configs[serviceName]
	status, statusExists := dm.statuses[serviceName]
	dm.mu.Unlock()

	if !exists || !config.AutoRecover || !statusExists {
		return
	}

	status.mu.Lock()
	defer status.mu.Unlock()

	if !status.active {
		return
	}

	// 检查是否可以恢复
	timeSinceDegraded := time.Since(status.degradedAt)
	if timeSinceDegraded < config.RecoverInterval {
		return
	}

	// 检查错误率是否降低
	if status.totalCount >= 5 {
		errorRate := float64(status.errorCount) / float64(status.totalCount) * 100
		if errorRate < config.ErrorThreshold/2 {
			status.active = false
			status.recoveredAt = time.Now()
			status.errorCount = 0
			status.totalCount = 0
			fmt.Printf("[降级] 服务 %s 已恢复正常\n", serviceName)
		}
	} else {
		// 重置计数器重新统计
		status.errorCount = 0
		status.totalCount = 0
	}
}

// autoRecoverChecker 自动恢复检查
func (dm *DegradationManager) autoRecoverChecker() {
	ticker := time.NewTicker(10 * time.Second)
	defer ticker.Stop()

	for {
		select {
		case <-ticker.C:
			dm.mu.RLock()
			serviceNames := make([]string, 0, len(dm.configs))
			for name := range dm.configs {
				serviceNames = append(serviceNames, name)
			}
			dm.mu.RUnlock()

			for _, name := range serviceNames {
				dm.recoverDegradation(name)
			}
		case <-dm.done:
			return
		}
	}
}

// ManualTrigger 手动触发降级
func (dm *DegradationManager) ManualTrigger(serviceName string) error {
	dm.mu.RLock()
	config, exists := dm.configs[serviceName]
	dm.mu.RUnlock()

	if !exists {
		return fmt.Errorf("服务 %s 未配置降级", serviceName)
	}

	if !config.Enabled {
		return fmt.Errorf("服务 %s 降级未启用", serviceName)
	}

	dm.triggerDegradation(serviceName, ManualDegradation)
	return nil
}

// ManualRecover 手动恢复服务
func (dm *DegradationManager) ManualRecover(serviceName string) error {
	dm.mu.RLock()
	defer dm.mu.RUnlock()

	status, exists := dm.statuses[serviceName]
	if !exists {
		return fmt.Errorf("服务 %s 未配置降级", serviceName)
	}

	status.mu.Lock()
	defer status.mu.Unlock()

	if !status.active {
		return fmt.Errorf("服务 %s 未处于降级状态", serviceName)
	}

	status.active = false
	status.recoveredAt = time.Now()
	status.errorCount = 0
	status.totalCount = 0

	fmt.Printf("[降级] 服务 %s 已手动恢复\n", serviceName)
	return nil
}

// GetStatus 获取降级状态
func (dm *DegradationManager) GetStatus(serviceName string) map[string]interface{} {
	dm.mu.RLock()
	defer dm.mu.RUnlock()

	status, exists := dm.statuses[serviceName]
	if !exists {
		return nil
	}

	status.mu.RLock()
	defer status.mu.RUnlock()

	result := map[string]interface{}{
		"active":      status.active,
		"trigger":     string(status.trigger),
		"concurrency": status.concurrency,
	}

	if !status.degradedAt.IsZero() {
		result["degraded_at"] = status.degradedAt
	}

	if !status.recoveredAt.IsZero() {
		result["recovered_at"] = status.recoveredAt
	}

	if status.totalCount > 0 {
		errorRate := float64(status.errorCount) / float64(status.totalCount) * 100
		result["error_rate"] = fmt.Sprintf("%.2f%%", errorRate)
		result["total_count"] = status.totalCount
		result["error_count"] = status.errorCount
	}

	return result
}

// GetAllStatus 获取所有服务降级状态
func (dm *DegradationManager) GetAllStatus() map[string]interface{} {
	dm.mu.RLock()
	defer dm.mu.RUnlock()

	result := make(map[string]interface{})
	for name := range dm.configs {
		result[name] = dm.GetStatus(name)
	}
	return result
}

// ============================================
// 预定义降级策略
// ============================================

// CacheFallbackStrategy 缓存降级策略
type CacheFallbackStrategy struct {
	name     string
	cache    map[string]interface{}
	cacheTTL time.Duration
	mu       sync.RWMutex
}

// NewCacheFallbackStrategy 创建缓存降级策略
func NewCacheFallbackStrategy(name string, cacheTTL time.Duration) *CacheFallbackStrategy {
	return &CacheFallbackStrategy{
		name:     name,
		cache:    make(map[string]interface{}),
		cacheTTL: cacheTTL,
	}
}

// Execute 执行缓存降级
func (s *CacheFallbackStrategy) Execute(ctx context.Context, request interface{}) (interface{}, error) {
	s.mu.RLock()
	defer s.mu.RUnlock()

	// 从请求中提取key
	key := fmt.Sprintf("%v", request)
	if cached, exists := s.cache[key]; exists {
		return cached, nil
	}

	return nil, fmt.Errorf("缓存中无数据")
}

// Name 返回策略名称
func (s *CacheFallbackStrategy) Name() string {
	return s.name
}

// Type 返回策略类型
func (s *CacheFallbackStrategy) Type() DegradationType {
	return ErrorRateDegradation
}

// Set 设置缓存
func (s *CacheFallbackStrategy) Set(key string, value interface{}) {
	s.mu.Lock()
	defer s.mu.Unlock()
	s.cache[key] = value
}

// DefaultResponseStrategy 默认响应降级策略
type DefaultResponseStrategy struct {
	name         string
	defaultValue interface{}
}

// NewDefaultResponseStrategy 创建默认响应策略
func NewDefaultResponseStrategy(name string, defaultValue interface{}) *DefaultResponseStrategy {
	return &DefaultResponseStrategy{
		name:         name,
		defaultValue: defaultValue,
	}
}

// Execute 执行默认响应
func (s *DefaultResponseStrategy) Execute(ctx context.Context, request interface{}) (interface{}, error) {
	// 返回默认值
	if s.defaultValue != nil {
		// 如果默认值是函数，执行它
		if fn, ok := s.defaultValue.(func() interface{}); ok {
			return fn(), nil
		}
	}
	return s.defaultValue, nil
}

// Name 返回策略名称
func (s *DefaultResponseStrategy) Name() string {
	return s.name
}

// Type 返回策略类型
func (s *DefaultResponseStrategy) Type() DegradationType {
	return ErrorRateDegradation
}

// EmptyResponseStrategy 空响应降级策略
type EmptyResponseStrategy struct {
	name string
}

// NewEmptyResponseStrategy 创建空响应策略
func NewEmptyResponseStrategy(name string) *EmptyResponseStrategy {
	return &EmptyResponseStrategy{name: name}
}

// Execute 执行空响应
func (s *EmptyResponseStrategy) Execute(ctx context.Context, request interface{}) (interface{}, error) {
	// 返回空JSON对象
	return json.Marshal(map[string]interface{}{})
}

// Name 返回策略名称
func (s *EmptyResponseStrategy) Name() string {
	return s.name
}

// Type 返回策略类型
func (s *EmptyResponseStrategy) Type() DegradationType {
	return TimeoutDegradation
}

// Close 关闭降级管理器，停止自动恢复检查
func (dm *DegradationManager) Close() error {
	select {
	case <-dm.done:
		// 已经关闭
		return nil
	default:
		close(dm.done)
		return nil
	}
}
