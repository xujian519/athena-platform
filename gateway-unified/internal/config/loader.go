package config

import (
	"fmt"
	"os"
	"path/filepath"
	"strings"
	"sync"

	"gopkg.in/yaml.v3"
)

// 配置文件路径（按优先级排序）
var configPaths = []string{
	"./gateway-config.yaml",
	"./config/gateway.yaml",
	"/etc/athena/gateway.yaml",
}

// ConfigWatcher 配置热重载观察者
type ConfigWatcher struct {
	mu       sync.RWMutex
	config   *Config
	watchers []chan *Config
}

// NewConfigWatcher 创建配置观察者
func NewConfigWatcher(initial *Config) *ConfigWatcher {
	return &ConfigWatcher{
		config:   initial,
		watchers: make([]chan *Config, 0),
	}
}

// Get 获取当前配置
func (w *ConfigWatcher) Get() *Config {
	w.mu.RLock()
	defer w.mu.RUnlock()
	return w.config
}

// Update 更新配置并通知所有观察者
func (w *ConfigWatcher) Update(newConfig *Config) {
	w.mu.Lock()
	w.config = newConfig
	w.mu.Unlock()

	// 通知所有观察者
	for _, ch := range w.watchers {
		select {
		case ch <- newConfig:
		default:
			// 如果通道已满，跳过
		}
	}
}

// Watch 注册配置变更监听
func (w *ConfigWatcher) Watch() <-chan *Config {
	ch := make(chan *Config, 1)
	w.mu.Lock()
	w.watchers = append(w.watchers, ch)
	w.mu.Unlock()
	return ch
}

// globalWatcher 全局配置观察者
var globalWatcher *ConfigWatcher

// LoadWithFile 加载配置（支持YAML文件 + 环境变量）
// 加载优先级：环境变量 > YAML文件 > 默认值
func LoadWithFile(configFile string) (*Config, error) {
	// 从默认配置开始
	cfg := defaultConfig()

	// 尝试加载YAML文件
	if err := loadYAMLFile(cfg, configFile); err != nil {
		// YAML文件加载失败不是致命错误，使用默认配置
		fmt.Printf("警告: YAML配置加载失败: %v，使用默认配置\n", err)
	}

	// 环境变量覆盖（优先级最高）
	applyEnvOverrides(cfg)

	// 设置全局观察者
	globalWatcher = NewConfigWatcher(cfg)

	return cfg, nil
}

// Load 加载配置（自动查找配置文件）
func Load() (*Config, error) {
	// 尝试从环境变量获取配置文件路径
	if configFile := os.Getenv("GATEWAY_CONFIG"); configFile != "" {
		return LoadWithFile(configFile)
	}

	// 尝试默认路径
	for _, path := range configPaths {
		if _, err := os.Stat(path); err == nil {
			return LoadWithFile(path)
		}
	}

	// 没找到配置文件，使用默认配置
	fmt.Println("未找到配置文件，使用默认配置")
	cfg := defaultConfig()
	applyEnvOverrides(cfg)
	globalWatcher = NewConfigWatcher(cfg)
	return cfg, nil
}

// defaultConfig 返回默认配置
func defaultConfig() *Config {
	return &Config{
		Server: ServerConfig{
			Port:         8005,
			Production:   false,
			ReadTimeout:  30,
			WriteTimeout: 30,
			IdleTimeout:  120,
		},
		Logging: LoggingConfig{
			Level:  "info",
			Format: "json",
			Output: "stdout",
		},
		Monitoring: MonitoringConfig{
			Enabled: false,
			Port:    9090,
			Path:    "/metrics",
		},
		Tailscale: TailscaleConfig{
			Mode:               "off",
			ResetOnExit:        true,
			AllowTailscaleAuth: true,
		},
		Auth: AuthConfig{
			Mode:     "",
			Token:    "",
			Password: "",
		},
	}
}

// loadYAMLFile 从YAML文件加载配置
func loadYAMLFile(cfg *Config, configFile string) error {
	// 如果未指定文件，尝试默认路径
	if configFile == "" {
		for _, path := range configPaths {
			if _, err := os.Stat(path); err == nil {
				configFile = path
				break
			}
		}
	}

	// 如果仍然没有找到文件，返回
	if configFile == "" {
		return fmt.Errorf("未找到配置文件")
	}

	// 读取文件
	data, err := os.ReadFile(configFile)
	if err != nil {
		return fmt.Errorf("读取配置文件失败: %w", err)
	}

	// 解析YAML
	if err := yaml.Unmarshal(data, cfg); err != nil {
		return fmt.Errorf("解析YAML失败: %w", err)
	}

	fmt.Printf("已加载配置文件: %s\n", configFile)
	return nil
}

// applyEnvOverrides 应用环境变量覆盖
// 支持的环境变量格式：
// - GATEWAY_PORT (服务器端口)
// - GATEWAY_PRODUCTION (生产模式)
// - GATEWAY_READ_TIMEOUT (读取超时)
// - GATEWAY_WRITE_TIMEOUT (写入超时)
// - GATEWAY_IDLE_TIMEOUT (空闲超时)
// - GATEWAY_LOG_LEVEL (日志级别)
// - GATEWAY_LOG_FORMAT (日志格式)
// - GATEWAY_LOG_OUTPUT (日志输出)
// - GATEWAY_METRICS_ENABLED (启用指标)
// - GATEWAY_METRICS_PORT (指标端口)
// - GATEWAY_METRICS_PATH (指标路径)
// - GATEWAY_TAILSCALE_MODE (Tailscale模式: off, serve, funnel)
// - GATEWAY_TAILSCALE_RESET_ON_EXIT (退出时重置Tailscale)
// - GATEWAY_TAILSCALE_ALLOW_AUTH (允许Tailscale身份认证)
// - GATEWAY_AUTH_MODE (认证模式: token, password)
// - GATEWAY_AUTH_TOKEN (认证Token)
// - GATEWAY_AUTH_PASSWORD (认证密码)
// - OPENCLAW_GATEWAY_TOKEN (兼容OpenClaw格式的Token)
// - OPENCLAW_GATEWAY_PASSWORD (兼容OpenClaw格式的密码)
func applyEnvOverrides(cfg *Config) {
	// 服务器配置
	if port := os.Getenv("GATEWAY_PORT"); port != "" {
		var p int
		if _, err := fmt.Sscanf(port, "%d", &p); err == nil && p > 0 && p < 65536 {
			cfg.Server.Port = p
		}
	}

	if prod := os.Getenv("GATEWAY_PRODUCTION"); prod == "true" || prod == "1" {
		cfg.Server.Production = true
	}

	if rt := os.Getenv("GATEWAY_READ_TIMEOUT"); rt != "" {
		var t int
		if _, err := fmt.Sscanf(rt, "%d", &t); err == nil && t > 0 {
			cfg.Server.ReadTimeout = t
		}
	}

	if wt := os.Getenv("GATEWAY_WRITE_TIMEOUT"); wt != "" {
		var t int
		if _, err := fmt.Sscanf(wt, "%d", &t); err == nil && t > 0 {
			cfg.Server.WriteTimeout = t
		}
	}

	if it := os.Getenv("GATEWAY_IDLE_TIMEOUT"); it != "" {
		var t int
		if _, err := fmt.Sscanf(it, "%d", &t); err == nil && t > 0 {
			cfg.Server.IdleTimeout = t
		}
	}

	// 日志配置
	if level := os.Getenv("GATEWAY_LOG_LEVEL"); level != "" {
		cfg.Logging.Level = strings.ToLower(level)
	}

	if format := os.Getenv("GATEWAY_LOG_FORMAT"); format != "" {
		cfg.Logging.Format = strings.ToLower(format)
	}

	if output := os.Getenv("GATEWAY_LOG_OUTPUT"); output != "" {
		cfg.Logging.Output = output
	}

	// 监控配置
	if enabled := os.Getenv("GATEWAY_METRICS_ENABLED"); enabled == "true" || enabled == "1" {
		cfg.Monitoring.Enabled = true
	}

	if port := os.Getenv("GATEWAY_METRICS_PORT"); port != "" {
		var p int
		if _, err := fmt.Sscanf(port, "%d", &p); err == nil && p > 0 && p < 65536 {
			cfg.Monitoring.Port = p
		}
	}

	if path := os.Getenv("GATEWAY_METRICS_PATH"); path != "" {
		cfg.Monitoring.Path = path
	}

	// Tailscale配置
	if mode := os.Getenv("GATEWAY_TAILSCALE_MODE"); mode != "" {
		cfg.Tailscale.Mode = strings.ToLower(mode)
	}

	if reset := os.Getenv("GATEWAY_TAILSCALE_RESET_ON_EXIT"); reset == "true" || reset == "1" {
		cfg.Tailscale.ResetOnExit = true
	}

	if allowAuth := os.Getenv("GATEWAY_TAILSCALE_ALLOW_AUTH"); allowAuth == "true" || allowAuth == "1" {
		cfg.Tailscale.AllowTailscaleAuth = true
	}

	// 认证配置
	if mode := os.Getenv("GATEWAY_AUTH_MODE"); mode != "" {
		cfg.Auth.Mode = strings.ToLower(mode)
	}

	if token := os.Getenv("GATEWAY_AUTH_TOKEN"); token != "" {
		cfg.Auth.Token = token
	}

	if password := os.Getenv("GATEWAY_AUTH_PASSWORD"); password != "" {
		cfg.Auth.Password = password
	}

	// 兼容OpenClaw格式的环境变量
	if token := os.Getenv("OPENCLAW_GATEWAY_TOKEN"); token != "" && cfg.Auth.Token == "" {
		cfg.Auth.Token = token
	}

	if password := os.Getenv("OPENCLAW_GATEWAY_PASSWORD"); password != "" && cfg.Auth.Password == "" {
		cfg.Auth.Password = password
	}
}

// GetWatcher 获取全局配置观察者
func GetWatcher() *ConfigWatcher {
	return globalWatcher
}

// SaveConfig 保存配置到YAML文件
func SaveConfig(cfg *Config, filePath string) error {
	// 确保目录存在
	dir := filepath.Dir(filePath)
	if err := os.MkdirAll(dir, 0755); err != nil {
		return fmt.Errorf("创建目录失败: %w", err)
	}

	// 序列化为YAML
	data, err := yaml.Marshal(cfg)
	if err != nil {
		return fmt.Errorf("序列化配置失败: %w", err)
	}

	// 写入文件
	if err := os.WriteFile(filePath, data, 0644); err != nil {
		return fmt.Errorf("写入配置文件失败: %w", err)
	}

	fmt.Printf("配置已保存到: %s\n", filePath)
	return nil
}

// Reload 重新加载配置
func Reload(configFile string) error {
	// 加载新配置
	newConfig, err := LoadWithFile(configFile)
	if err != nil {
		return err
	}

	// 更新全局观察者
	if globalWatcher != nil {
		globalWatcher.Update(newConfig)
	}

	return nil
}
