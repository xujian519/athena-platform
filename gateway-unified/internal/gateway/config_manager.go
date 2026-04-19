package gateway

import (
	"context"
	"encoding/json"
	"fmt"
	"os"
	"path/filepath"
	"sync"
	"time"
)

// ConfigSource 配置来源类型
type ConfigSource string

const (
	// ConfigSourceFile 文件配置源
	ConfigSourceFile ConfigSource = "file"
	// ConfigSourceEnv 环境变量配置源
	ConfigSourceEnv ConfigSource = "env"
	// ConfigSourceEtcd ETCD配置源
	ConfigSourceEtcd ConfigSource = "etcd"
	// ConfigSourceConsul Consul配置源
	ConfigSourceConsul ConfigSource = "consul"
)

// ConfigChange 配置变更事件
type ConfigChange struct {
	Key       string      `json:"key"`
	OldValue  interface{} `json:"old_value,omitempty"`
	NewValue  interface{} `json:"new_value,omitempty"`
	Source    ConfigSource `json:"source"`
	Timestamp time.Time   `json:"timestamp"`
}

// ConfigChangeListener 配置变更监听器
type ConfigChangeListener func(change ConfigChange)

// ConfigValidator 配置验证器
type ConfigValidator func(key string, value interface{}) error

// ConfigManager 配置管理器接口
type ConfigManager interface {
	// Get 获取配置值
	Get(key string) (interface{}, bool)
	// Set 设置配置值
	Set(key string, value interface{}) error
	// Watch 监听配置变更
	Watch(key string, listener ConfigChangeListener)
	// Unwatch 取消监听
	Unwatch(key string, listener ConfigChangeListener)
	// LoadFromFile 从文件加载配置
	LoadFromFile(path string) error
	// LoadFromEnv 从环境变量加载配置
	LoadFromEnv(prefix string) error
	// SaveToFile 保存配置到文件
	SaveToFile(path string) error
	// GetAll 获取所有配置
	GetAll() map[string]interface{}
	// Close 关闭配置管理器
	Close() error
}

// defaultConfigManager 默认配置管理器实现
type defaultConfigManager struct {
	configs    map[string]interface{}
	listeners  map[string][]ConfigChangeListener
	validators map[string]ConfigValidator
	mu         sync.RWMutex
	watcherCtx context.Context
	cancel     context.CancelFunc
}

// NewConfigManager 创建配置管理器
func NewConfigManager() ConfigManager {
	ctx, cancel := context.WithCancel(context.Background())

	cm := &defaultConfigManager{
		configs:    make(map[string]interface{}),
		listeners:  make(map[string][]ConfigChangeListener),
		validators: make(map[string]ConfigValidator),
		watcherCtx: ctx,
		cancel:     cancel,
	}

	return cm
}

// Get 获取配置值
func (cm *defaultConfigManager) Get(key string) (interface{}, bool) {
	cm.mu.RLock()
	defer cm.mu.RUnlock()

	value, exists := cm.configs[key]
	return value, exists
}

// Set 设置配置值
func (cm *defaultConfigManager) Set(key string, value interface{}) error {
	cm.mu.Lock()
	defer cm.mu.Unlock()

	// 验证配置值
	if validator, exists := cm.validators[key]; exists {
		if err := validator(key, value); err != nil {
			return fmt.Errorf("配置验证失败: %w", err)
		}
	}

	oldValue, exists := cm.configs[key]
	cm.configs[key] = value

	// 触发变更事件
	change := ConfigChange{
		Key:       key,
		NewValue:  value,
		Source:    ConfigSourceFile,
		Timestamp: time.Now(),
	}

	if exists {
		change.OldValue = oldValue
	}

	cm.notifyListeners(change)

	return nil
}

// Watch 监听配置变更
func (cm *defaultConfigManager) Watch(key string, listener ConfigChangeListener) {
	cm.mu.Lock()
	defer cm.mu.Unlock()

	if _, exists := cm.listeners[key]; !exists {
		cm.listeners[key] = make([]ConfigChangeListener, 0)
	}

	cm.listeners[key] = append(cm.listeners[key], listener)
}

// Unwatch 取消监听
func (cm *defaultConfigManager) Unwatch(key string, listener ConfigChangeListener) {
	cm.mu.Lock()
	defer cm.mu.Unlock()

	_, exists := cm.listeners[key]
	if !exists {
		return
	}

	// 由于Go中函数不能直接比较，我们简化实现：删除该key的所有监听器
	// 实际应用中可以使用监听器ID或其他标识符
	_ = listener // 参数保留以保持接口一致性
	delete(cm.listeners, key)
}

// LoadFromFile 从文件加载配置
func (cm *defaultConfigManager) LoadFromFile(path string) error {
	// 检查文件是否存在
	if _, err := os.Stat(path); os.IsNotExist(err) {
		return fmt.Errorf("配置文件不存在: %s", path)
	}

	// 读取文件内容
	data, err := os.ReadFile(path)
	if err != nil {
		return fmt.Errorf("读取配置文件失败: %w", err)
	}

	// 解析配置
	var config map[string]interface{}
	if err := json.Unmarshal(data, &config); err != nil {
		return fmt.Errorf("解析配置文件失败: %w", err)
	}

	// 扁平化配置键
	flatConfig := cm.flattenConfig(config, "")

	// 应用配置
	cm.mu.Lock()
	defer cm.mu.Unlock()

	for key, value := range flatConfig {
		change := ConfigChange{
			Key:       key,
			NewValue:  value,
			Source:    ConfigSourceFile,
			Timestamp: time.Now(),
		}

		if oldValue, exists := cm.configs[key]; exists {
			change.OldValue = oldValue
		}

		cm.configs[key] = value
		cm.notifyListeners(change)
	}

	// 启动文件监听
	go cm.watchFile(path)

	return nil
}

// LoadFromEnv 从环境变量加载配置
func (cm *defaultConfigManager) LoadFromEnv(prefix string) error {
	cm.mu.Lock()
	defer cm.mu.Unlock()

	for _, env := range os.Environ() {
		pair := splitEnv(env)
		if len(pair) != 2 {
			continue
		}

		key, value := pair[0], pair[1]

		// 检查前缀
		if prefix != "" {
			if len(key) <= len(prefix) || key[:len(prefix)] != prefix {
				continue
			}
			key = key[len(prefix):]
		}

		change := ConfigChange{
			Key:       key,
			NewValue:  value,
			Source:    ConfigSourceEnv,
			Timestamp: time.Now(),
		}

		if oldValue, exists := cm.configs[key]; exists {
			change.OldValue = oldValue
		}

		cm.configs[key] = value
		cm.notifyListeners(change)
	}

	return nil
}

// SaveToFile 保存配置到文件
func (cm *defaultConfigManager) SaveToFile(path string) error {
	cm.mu.RLock()
	defer cm.mu.RUnlock()

	// 确保目录存在
	dir := filepath.Dir(path)
	if err := os.MkdirAll(dir, 0755); err != nil {
		return fmt.Errorf("创建目录失败: %w", err)
	}

	// 序列化配置
	data, err := json.MarshalIndent(cm.configs, "", "  ")
	if err != nil {
		return fmt.Errorf("序列化配置失败: %w", err)
	}

	// 写入文件
	if err := os.WriteFile(path, data, 0644); err != nil {
		return fmt.Errorf("写入配置文件失败: %w", err)
	}

	return nil
}

// GetAll 获取所有配置
func (cm *defaultConfigManager) GetAll() map[string]interface{} {
	cm.mu.RLock()
	defer cm.mu.RUnlock()

	result := make(map[string]interface{}, len(cm.configs))
	for k, v := range cm.configs {
		result[k] = v
	}
	return result
}

// RegisterValidator 注册配置验证器
func (cm *defaultConfigManager) RegisterValidator(key string, validator ConfigValidator) {
	cm.mu.Lock()
	defer cm.mu.Unlock()

	cm.validators[key] = validator
}

// notifyListeners 通知监听器
func (cm *defaultConfigManager) notifyListeners(change ConfigChange) {
	listeners, exists := cm.listeners[change.Key]
	if !exists {
		return
	}

	// 异步通知监听器
	for _, listener := range listeners {
		go func(l ConfigChangeListener) {
			defer func() {
				if r := recover(); r != nil {
					fmt.Printf("[配置管理器] 监听器panic: %v\n", r)
				}
			}()
			l(change)
		}(listener)
	}
}

// flattenConfig 扁平化配置
func (cm *defaultConfigManager) flattenConfig(config map[string]interface{}, prefix string) map[string]interface{} {
	result := make(map[string]interface{})

	for key, value := range config {
		fullKey := key
		if prefix != "" {
			fullKey = prefix + "." + key
		}

		switch v := value.(type) {
		case map[string]interface{}:
			// 递归处理嵌套对象
			nested := cm.flattenConfig(v, fullKey)
			for nk, nv := range nested {
				result[nk] = nv
			}
		default:
			result[fullKey] = value
		}
	}

	return result
}

// watchFile 监听文件变更
func (cm *defaultConfigManager) watchFile(path string) {
	ticker := time.NewTicker(5 * time.Second)
	defer ticker.Stop()

	lastModTime := cm.getFileModTime(path)

	for {
		select {
		case <-ticker.C:
			currentModTime := cm.getFileModTime(path)
			if currentModTime.After(lastModTime) {
				lastModTime = currentModTime
				// 重新加载配置
				if err := cm.LoadFromFile(path); err != nil {
					fmt.Printf("[配置管理器] 重新加载配置失败: %v\n", err)
				} else {
					fmt.Printf("[配置管理器] 配置文件已重新加载: %s\n", path)
				}
			}
		case <-cm.watcherCtx.Done():
			return
		}
	}
}

// getFileModTime 获取文件修改时间
func (cm *defaultConfigManager) getFileModTime(path string) time.Time {
	info, err := os.Stat(path)
	if err != nil {
		return time.Time{}
	}
	return info.ModTime()
}

// splitEnv 分割环境变量
func splitEnv(env string) []string {
	for i := 0; i < len(env); i++ {
		if env[i] == '=' {
			return []string{env[:i], env[i+1:]}
		}
	}
	return []string{env}
}

// Close 关闭配置管理器
func (cm *defaultConfigManager) Close() error {
	cm.cancel()
	return nil
}

// ============================================
// 配置验证器
// ============================================

// PositiveIntValidator 正整数验证器
func PositiveIntValidator(key string, value interface{}) error {
	intValue, ok := value.(int)
	if !ok {
		return fmt.Errorf("配置 %s 必须是整数", key)
	}
	if intValue < 0 {
		return fmt.Errorf("配置 %s 必须是正整数", key)
	}
	return nil
}

// PortValidator 端口验证器
func PortValidator(key string, value interface{}) error {
	port, ok := value.(int)
	if !ok {
		return fmt.Errorf("配置 %s 必须是整数", key)
	}
	if port < 1 || port > 65535 {
		return fmt.Errorf("配置 %s 必须在1-65535之间", key)
	}
	return nil
}

// StringValidator 字符串验证器
func StringValidator(key string, value interface{}) error {
	if _, ok := value.(string); !ok {
		return fmt.Errorf("配置 %s 必须是字符串", key)
	}
	return nil
}

// BoolValidator 布尔验证器
func BoolValidator(key string, value interface{}) error {
	if _, ok := value.(bool); !ok {
		return fmt.Errorf("配置 %s 必须是布尔值", key)
	}
	return nil
}

// OneOfValidator 枚举验证器
func OneOfValidator(allowedValues []string) ConfigValidator {
	return func(key string, value interface{}) error {
		strValue, ok := value.(string)
		if !ok {
			return fmt.Errorf("配置 %s 必须是字符串", key)
		}

		for _, allowed := range allowedValues {
			if strValue == allowed {
				return nil
			}
		}

		return fmt.Errorf("配置 %s 必须是以下值之一: %v", key, allowedValues)
	}
}

// RangeValidator 范围验证器
func RangeValidator(min, max int) ConfigValidator {
	return func(key string, value interface{}) error {
		intValue, ok := value.(int)
		if !ok {
			return fmt.Errorf("配置 %s 必须是整数", key)
		}

		if intValue < min || intValue > max {
			return fmt.Errorf("配置 %s 必须在%d-%d之间", key, min, max)
		}

		return nil
	}
}
