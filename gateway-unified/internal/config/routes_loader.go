package config

import (
	"fmt"
	"os"
	"sync"

	"gopkg.in/yaml.v3"
)

// RouteRule 路由规则配置
type RouteRule struct {
	ID            string                 `yaml:"id" json:"id"`
	Path          string                 `yaml:"path" json:"path"`
	TargetService string                 `yaml:"target_service" json:"target_service"`
	Methods       []string               `yaml:"methods" json:"methods"`
	StripPrefix   bool                   `yaml:"strip_prefix" json:"strip_prefix"`
	Timeout       int                    `yaml:"timeout" json:"timeout"`
	Retries       int                    `yaml:"retries" json:"retries"`
	AuthRequired  bool                   `yaml:"auth_required" json:"auth_required"`
	Priority      int                    `yaml:"priority" json:"priority"`
	Weight        int                    `yaml:"weight" json:"weight"`
	Enabled       bool                   `yaml:"enabled" json:"enabled"`
	Metadata      map[string]interface{} `yaml:"metadata,omitempty" json:"metadata,omitempty"`
}

// RoutesConfig 路由配置
type RoutesConfig struct {
	Routes []RouteRule `yaml:"routes"`
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
			Routes: make([]RouteRule, 0),
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
		if config.Routes[i].StripPrefix == false && i > 0 {
			// 对于非根路径，默认启用路径前缀剥离
			if len(config.Routes[i].Path) > 1 {
				config.Routes[i].StripPrefix = true
			}
		}
		if config.Routes[i].Priority == 0 {
			config.Routes[i].Priority = 50 // 默认优先级
		}
		if config.Routes[i].Weight == 0 {
			config.Routes[i].Weight = 1 // 默认权重
		}
		config.Routes[i].Enabled = true // 默认启用
	}

	l.config = &config

	// 通知监听器
	for _, watcher := range l.watchers {
		watcher(&config)
	}

	return nil
}

// GetRoutes 获取所有路由
func (l *RoutesLoader) GetRoutes() []RouteRule {
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

// GetConfig 获取当前配置
func (l *RoutesLoader) GetConfig() *RoutesConfig {
	l.mu.RLock()
	defer l.mu.RUnlock()

	return l.config
}

// GetRouteCount 获取路由数量
func (l *RoutesLoader) GetRouteCount() int {
	l.mu.RLock()
	defer l.mu.RUnlock()

	return len(l.config.Routes)
}

// GetRouteByID 根据ID获取路由
func (l *RoutesLoader) GetRouteByID(id string) *RouteRule {
	l.mu.RLock()
	defer l.mu.RUnlock()

	for i := range l.config.Routes {
		if l.config.Routes[i].ID == id {
			return &l.config.Routes[i]
		}
	}
	return nil
}

// Validate 验证路由配置
func (l *RoutesLoader) Validate() error {
	l.mu.RLock()
	defer l.mu.RUnlock()

	seenPaths := make(map[string]bool)

	for i, route := range l.config.Routes {
		// 检查必填字段
		if route.ID == "" {
			return fmt.Errorf("路由 #%d: ID不能为空", i+1)
		}
		if route.Path == "" {
			return fmt.Errorf("路由 #%d (%s): 路径不能为空", i+1, route.ID)
		}
		if route.TargetService == "" {
			return fmt.Errorf("路由 #%d (%s): 目标服务不能为空", i+1, route.ID)
		}

		// 检查路径格式
		if route.Path[0] != '/' {
			return fmt.Errorf("路由 #%d (%s): 路径必须以/开头: %s", i+1, route.ID, route.Path)
		}

		// 检查路径重复
		pathKey := fmt.Sprintf("%s:%v", route.Path, route.Methods)
		if seenPaths[pathKey] {
			return fmt.Errorf("路由 #%d (%s): 路径和方法的组合重复: %s", i+1, route.ID, route.Path)
		}
		seenPaths[pathKey] = true

		// 检查方法
		if len(route.Methods) == 0 {
			return fmt.Errorf("路由 #%d (%s): 至少需要指定一个HTTP方法", i+1, route.ID)
		}

		// 检查超时
		if route.Timeout < 0 || route.Timeout > 600 {
			return fmt.Errorf("路由 #%d (%s): 超时时间必须在0-600秒之间: %d", i+1, route.ID, route.Timeout)
		}

		// 检查重试次数
		if route.Retries < 0 || route.Retries > 10 {
			return fmt.Errorf("路由 #%d (%s): 重试次数必须在0-10之间: %d", i+1, route.ID, route.Retries)
		}
	}

	return nil
}
