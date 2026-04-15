// Package logging - 日志配置
package logging

import "time"

// Config 日志配置
type Config struct {
	// 日志级别: debug, info, warn, error, fatal
	Level string `yaml:"level" mapstructure:"level" json:"level"`

	// 日志格式: json, text
	Format string `yaml:"format" mapstructure:"format" json:"format"`

	// 输出目标: stdout, stderr, 或文件路径
	Output string `yaml:"output" mapstructure:"output" json:"output"`

	// 日志轮转配置（文件输出时有效）
	Rotation *RotationConfig `yaml:"rotation" mapstructure:"rotation" json:"rotation"`

	// 是否启用调用者信息（文件名、行号）
	EnableCaller bool `yaml:"enable_caller" mapstructure:"enable_caller" json:"enable_caller"`

	// 是否启用堆栈跟踪（Error级别及以上）
	EnableStacktrace bool `yaml:"enable_stacktrace" mapstructure:"enable_stacktrace" json:"enable_stacktrace"`

	// 时间格式
	TimeFormat string `yaml:"time_format" mapstructure:"time_format" json:"time_format"`

	// 初始字段（所有日志都会包含）
	InitialFields map[string]interface{} `yaml:"initial_fields" mapstructure:"initial_fields" json:"initial_fields"`
}

// DefaultConfig 返回默认配置
func DefaultConfig() *Config {
	return &Config{
		Level:            "info",
		Format:           "text",
		Output:           "stdout",
		Rotation:         DefaultRotationConfig(),
		EnableCaller:     true,
		EnableStacktrace: true,
		TimeFormat:       "2006-01-02 15:04:05.000",
		InitialFields:    make(map[string]interface{}),
	}
}

// DevelopmentConfig 返回开发环境配置
func DevelopmentConfig() *Config {
	cfg := DefaultConfig()
	cfg.Level = "debug"
	cfg.EnableCaller = true
	cfg.EnableStacktrace = true
	cfg.Output = "stdout"
	return cfg
}

// ProductionConfig 返回生产环境配置
func ProductionConfig() *Config {
	cfg := DefaultConfig()
	cfg.Level = "info"
	cfg.EnableCaller = false
	cfg.EnableStacktrace = false
	cfg.Output = "/var/log/athena-gateway/gateway.log"
	cfg.Rotation = &RotationConfig{
		MaxSize:   100,
		MaxBackups: 10,
		MaxAge:     30,
		Compress:   true,
	}
	return cfg
}

// Validate 验证配置
func (c *Config) Validate() error {
	// 验证日志级别
	switch c.Level {
	case "debug", "info", "warn", "error", "fatal":
		// 有效级别
	default:
		c.Level = "info" // 默认使用info
	}

	// 验证格式
	switch c.Format {
	case "json", "text":
		// 有效格式
	default:
		c.Format = "text" // 默认使用text
	}

	return nil
}

// GetLevelWeight 获取日志级别权重
func (c *Config) GetLevelWeight() int {
	switch c.Level {
	case "debug":
		return 0
	case "info":
		return 1
	case "warn":
		return 2
	case "error":
		return 3
	case "fatal":
		return 4
	default:
		return 1
	}
}

// ShouldLog 判断是否应该记录指定级别的日志
func (c *Config) ShouldLog(level string) bool {
	return c.GetLevelWeight() <= getLevelWeight(level)
}

// getLevelWeight 获取日志级别权重
func getLevelWeight(level string) int {
	switch level {
	case "debug":
		return 0
	case "info":
		return 1
	case "warn":
		return 2
	case "error":
		return 3
	case "fatal":
		return 4
	default:
		return 1
	}
}

// RotationConfig 日志轮转配置（复制自rotation.go，保持一致性）
type RotationConfig struct {
	// 单个日志文件最大大小 (MB)
	MaxSize int `yaml:"max_size" mapstructure:"max_size" json:"max_size"`
	// 保留的旧日志文件数量
	MaxBackups int `yaml:"max_backups" mapstructure:"max_backups" json:"max_backups"`
	// 保留的最大天数 (0表示不限制)
	MaxAge int `yaml:"max_age" mapstructure:"max_age" json:"max_age"`
	// 是否压缩旧日志
	Compress bool `yaml:"compress" mapstructure:"compress" json:"compress"`
	// 轮转间隔（可选，按时间轮转）
	RotationInterval time.Duration `yaml:"rotation_interval" mapstructure:"rotation_interval" json:"rotation_interval"`
	// 是否使用本地时间（true）或UTC（false）
	UseLocalTime bool `yaml:"use_local_time" mapstructure:"use_local_time" json:"use_local_time"`
}

// DefaultRotationConfig 返回默认轮转配置
func DefaultRotationConfig() *RotationConfig {
	return &RotationConfig{
		MaxSize:         100, // 100MB
		MaxBackups:      10,  // 保留10个备份
		MaxAge:          30,  // 保留30天
		Compress:        true,
		RotationInterval: 24 * time.Hour, // 每天轮转
		UseLocalTime:    true,
	}
}
