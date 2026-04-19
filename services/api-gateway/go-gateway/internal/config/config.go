package config

import (
	"fmt"
	"os"

	"github.com/spf13/viper"
)

// Config 应用配置结构
type Config struct {
	Server     ServerConfig     `mapstructure:"server"`
	Database   DatabaseConfig   `mapstructure:"database"`
	Redis      RedisConfig      `mapstructure:"redis"`
	JWT        JWTConfig        `mapstructure:"jwt"`
	RateLimit  RateLimitConfig  `mapstructure:"rate_limit"`
	Services   ServicesConfig   `mapstructure:"services"`
	Monitoring MonitoringConfig `mapstructure:"monitoring"`
	Logging    LoggingConfig    `mapstructure:"logging"`
}

// ServerConfig 服务器配置
type ServerConfig struct {
	Port         int    `mapstructure:"port" validate:"required,min=1,max=65535"`
	Host         string `mapstructure:"host" validate:"required"`
	Mode         string `mapstructure:"mode" validate:"required,oneof=debug release test"`
	ReadTimeout  int    `mapstructure:"read_timeout" validate:"required,min=1"`
	WriteTimeout int    `mapstructure:"write_timeout" validate:"required,min=1"`
	IdleTimeout  int    `mapstructure:"idle_timeout" validate:"required,min=1"`
}

// DatabaseConfig 数据库配置
type DatabaseConfig struct {
	Host         string `mapstructure:"host" validate:"required"`
	Port         int    `mapstructure:"port" validate:"required,min=1,max=65535"`
	User         string `mapstructure:"user" validate:"required"`
	Password     string `mapstructure:"password" validate:"required"`
	DBName       string `mapstructure:"db_name" validate:"required"`
	SSLMode      string `mapstructure:"ssl_mode" validate:"required"`
	MaxIdleConns int    `mapstructure:"max_idle_conns" validate:"min=0"`
	MaxOpenConns int    `mapstructure:"max_open_conns" validate:"min=1"`
	MaxLifetime  int    `mapstructure:"max_lifetime" validate:"min=0"`
}

// RedisConfig Redis配置
type RedisConfig struct {
	Host     string `mapstructure:"host" validate:"required"`
	Port     int    `mapstructure:"port" validate:"required,min=1,max=65535"`
	Password string `mapstructure:"password"`
	DB       int    `mapstructure:"db" validate:"min=0,max=15"`
	PoolSize int    `mapstructure:"pool_size" validate:"min=1"`
}

// JWTConfig JWT配置
type JWTConfig struct {
	Secret         string `mapstructure:"secret" validate:"required,min=32"`
	ExpirationTime int    `mapstructure:"expiration_time" validate:"required,min=1"`
	RefreshTime    int    `mapstructure:"refresh_time" validate:"required,min=1"`
	Issuer         string `mapstructure:"issuer" validate:"required"`
}

// RateLimitConfig 限流配置
type RateLimitConfig struct {
	Enabled           bool     `mapstructure:"enabled"`
	RequestsPerMinute int      `mapstructure:"requests_per_minute" validate:"min=1"`
	BurstSize         int      `mapstructure:"burst_size" validate:"min=1"`
	WhitelistEnabled  bool     `mapstructure:"whitelist_enabled"`
	Whitelist         []string `mapstructure:"whitelist"`
}

// ServicesConfig 服务配置
type ServicesConfig struct {
	Auth           ServiceConfig `mapstructure:"auth"`
	PatentSearch   ServiceConfig `mapstructure:"patent_search"`
	UserManagement ServiceConfig `mapstructure:"user_management"`
	Analytics      ServiceConfig `mapstructure:"analytics"`
}

// ServiceConfig 单个服务配置
type ServiceConfig struct {
	URL            string               `mapstructure:"url" validate:"required,url"`
	Timeout        int                  `mapstructure:"timeout" validate:"min=1"`
	RetryAttempts  int                  `mapstructure:"retry_attempts" validate:"min=0"`
	CircuitBreaker CircuitBreakerConfig `mapstructure:"circuit_breaker"`
}

// CircuitBreakerConfig 熔断器配置
type CircuitBreakerConfig struct {
	Enabled      bool    `mapstructure:"enabled"`
	Threshold    int     `mapstructure:"threshold" validate:"min=1"`
	Timeout      int     `mapstructure:"timeout" validate:"min=1"`
	ResetTimeout int     `mapstructure:"reset_timeout" validate:"min=1"`
	FailureRate  float64 `mapstructure:"failure_rate" validate:"min=0,max=1"`
}

// MonitoringConfig 监控配置
type MonitoringConfig struct {
	Enabled    bool   `mapstructure:"enabled"`
	Port       int    `mapstructure:"port" validate:"min=1,max=65535"`
	Path       string `mapstructure:"path"`
	MetricsURL string `mapstructure:"metrics_url"`
}

// LoggingConfig 日志配置
type LoggingConfig struct {
	Level      string `mapstructure:"level" validate:"required,oneof=debug info warn error"`
	Format     string `mapstructure:"format" validate:"required,oneof=json text"`
	Output     string `mapstructure:"output" validate:"required,oneof=stdout file"`
	Filename   string `mapstructure:"filename"`
	MaxSize    int    `mapstructure:"max_size" validate:"min=1"`
	MaxBackups int    `mapstructure:"max_backups" validate:"min=0"`
	MaxAge     int    `mapstructure:"max_age" validate:"min=0"`
	Compress   bool   `mapstructure:"compress"`
}

// LoadConfig 加载配置文件
func LoadConfig(configPath string) (*Config, error) {
	// 检查配置文件是否存在
	if _, err := os.Stat(configPath); os.IsNotExist(err) {
		return nil, fmt.Errorf("配置文件不存在: %s", configPath)
	}

	// 设置配置文件路径和名称
	viper.SetConfigFile(configPath)

	// 设置环境变量前缀
	viper.SetEnvPrefix("ATHENA_GATEWAY")
	viper.AutomaticEnv()

	// 读取配置文件
	if err := viper.ReadInConfig(); err != nil {
		return nil, fmt.Errorf("读取配置文件失败: %w", err)
	}

	// 解析配置到结构体
	var config Config
	if err := viper.Unmarshal(&config); err != nil {
		return nil, fmt.Errorf("解析配置失败: %w", err)
	}

	return &config, nil
}

// ValidateConfig 验证配置
func ValidateConfig(cfg *Config) error {
	// TODO: 实现配置验证逻辑
	// 可以使用validator库来验证配置
	return nil
}
