package config

import (
	"fmt"
	"os"
	"strings"

	"github.com/spf13/viper"
)

// Config 应用程序配置结构体
type Config struct {
	Server      ServerConfig      `mapstructure:"server"`
	Auth        AuthConfig        `mapstructure:"auth"`
	Logging     LoggingConfig     `mapstructure:"logging"`
	Upstream    UpstreamConfig    `mapstructure:"upstream"`
	Database    DatabaseConfig    `mapstructure:"database"`
	Redis       RedisConfig       `mapstructure:"redis"`
	HTTPClient  HTTPClientConfig  `mapstructure:"http_client"`
	RateLimit   RateLimiterConfig `mapstructure:"rate_limit"`
	Performance PerformanceConfig `mapstructure:"performance"`
}

// ServerConfig 服务器配置
type ServerConfig struct {
	Host         string `mapstructure:"host"`
	Port         int    `mapstructure:"port"`
	ReadTimeout  int    `mapstructure:"read_timeout"`  // 读取超时（秒）
	WriteTimeout int    `mapstructure:"write_timeout"` // 写入超时（秒）
	IdleTimeout  int    `mapstructure:"idle_timeout"`  // 空闲超时（秒）
	GraceTimeout int    `mapstructure:"grace_timeout"` // 优雅关闭超时（秒）
}

// AuthConfig 认证配置
type AuthConfig struct {
	JWTSecret       string   `mapstructure:"jwt_secret"`
	AccessTokenExp  int      `mapstructure:"access_token_exp"`  // 访问令牌过期时间（分钟）
	RefreshTokenExp int      `mapstructure:"refresh_token_exp"` // 刷新令牌过期时间（小时）
	Issuer          string   `mapstructure:"issuer"`
	SkipAuthPaths   []string `mapstructure:"skip_auth_paths"` // 跳过认证的路径
	AdminUsers      []string `mapstructure:"admin_users"`     // 管理员用户列表
}

// LoggingConfig 日志配置
type LoggingConfig struct {
	Level      string `mapstructure:"level"`       // 日志级别 (debug, info, warn, error)
	Format     string `mapstructure:"format"`      // 日志格式 (json, text)
	Output     string `mapstructure:"output"`      // 输出 (stdout, file)
	FilePath   string `mapstructure:"file_path"`   // 日志文件路径
	MaxSize    int    `mapstructure:"max_size"`    // 单个日志文件最大大小（MB）
	MaxBackups int    `mapstructure:"max_backups"` // 保留的旧日志文件数量
	MaxAge     int    `mapstructure:"max_age"`     // 保留日志文件的最大天数
	Compress   bool   `mapstructure:"compress"`    // 是否压缩旧日志文件
}

// UpstreamConfig 上游服务配置
type UpstreamConfig struct {
	Services map[string]ServiceConfig `mapstructure:"services"`
	Timeout  int                      `mapstructure:"timeout"` // 上游请求超时（秒）
}

// ServiceConfig 单个服务配置
type ServiceConfig struct {
	URL     string            `mapstructure:"url"`
	Weight  int               `mapstructure:"weight"`
	Headers map[string]string `mapstructure:"headers"`
}

// DatabaseConfig 数据库配置
type DatabaseConfig struct {
	Host            string `mapstructure:"host"`
	Port            int    `mapstructure:"port"`
	Username        string `mapstructure:"username"`
	Password        string `mapstructure:"password"`
	Database        string `mapstructure:"database"`
	MaxOpenConns    int    `mapstructure:"max_open_conns"`
	MaxIdleConns    int    `mapstructure:"max_idle_conns"`
	ConnMaxLifetime int    `mapstructure:"conn_max_lifetime"`
}

// RedisConfig Redis配置
type RedisConfig struct {
	Host         string `mapstructure:"host"`
	Port         int    `mapstructure:"port"`
	Password     string `mapstructure:"password"`
	Database     int    `mapstructure:"database"`
	PoolSize     int    `mapstructure:"pool_size"`
	MinIdleConns int    `mapstructure:"min_idle_conns"`
}

// HTTPClientConfig HTTP客户端配置
type HTTPClientConfig struct {
	RequestTimeout      int `mapstructure:"request_timeout"`
	MaxIdleConns        int `mapstructure:"max_idle_conns"`
	MaxIdleConnsPerHost int `mapstructure:"max_idle_conns_per_host"`
	IdleConnTimeout     int `mapstructure:"idle_conn_timeout"`
}

// RateLimiterConfig 限流器配置
type RateLimiterConfig struct {
	DefaultLimit     int64   `mapstructure:"default_limit"`
	DefaultBurst     int64   `mapstructure:"default_burst"`
	Window           int64   `mapstructure:"window"`
	AdaptiveMode     bool    `mapstructure:"adaptive_mode"`
	MinLimit         int64   `mapstructure:"min_limit"`
	MaxLimit         int64   `mapstructure:"max_limit"`
	AdjustmentFactor float64 `mapstructure:"adjustment_factor"`
	StatsWindow      int64   `mapstructure:"stats_window"`
}

// PerformanceConfig 性能配置
type PerformanceConfig struct {
	EnablePprof   bool   `mapstructure:"enable_pprof"`
	PprofPath     string `mapstructure:"pprof_path"`
	EnableMetrics bool   `mapstructure:"enable_metrics"`
	MetricsPath   string `mapstructure:"metrics_path"`
	GCPercent     int    `mapstructure:"gc_percent"`
	MaxGoroutines int    `mapstructure:"max_goroutines"`
}

// 全局配置实例
var (
	AppConfig *Config
)

// LoadConfig 加载配置文件
func LoadConfig(configPath string) (*Config, error) {
	if configPath == "" {
		configPath = "./configs/config.yaml"
	}

	// 创建viper实例
	v := viper.New()

	// 设置配置文件路径和名称
	v.SetConfigFile(configPath)

	// 设置配置文件类型
	v.SetConfigType("yaml")

	// 环境变量前缀
	v.SetEnvPrefix("ATHENA_GATEWAY")
	v.SetEnvKeyReplacer(strings.NewReplacer(".", "_"))
	v.AutomaticEnv()

	// 设置默认值
	setDefaults(v)

	// 尝试读取配置文件
	if err := v.ReadInConfig(); err != nil {
		if _, ok := err.(viper.ConfigFileNotFoundError); ok {
			// 配置文件未找到，使用默认值
			fmt.Printf("配置文件 %s 未找到，使用默认值\n", configPath)
		} else {
			return nil, fmt.Errorf("读取配置文件失败: %w", err)
		}
	}

	// 解析配置到结构体
	config := &Config{}
	if err := v.Unmarshal(config); err != nil {
		return nil, fmt.Errorf("解析配置失败: %w", err)
	}

	// 验证配置
	if err := validateConfig(config); err != nil {
		return nil, fmt.Errorf("配置验证失败: %w", err)
	}

	// 设置全局配置实例
	AppConfig = config

	fmt.Printf("配置加载成功: %s\n", configPath)
	return config, nil
}

// setDefaults 设置默认配置值
func setDefaults(v *viper.Viper) {
	// 服务器默认配置
	v.SetDefault("server.host", "0.0.0.0")
	v.SetDefault("server.port", 8080)
	v.SetDefault("server.read_timeout", 30)
	v.SetDefault("server.write_timeout", 30)
	v.SetDefault("server.idle_timeout", 60)
	v.SetDefault("server.grace_timeout", 30)

	// 认证默认配置
	v.SetDefault("auth.jwt_secret", "your-secret-key-change-in-production")
	v.SetDefault("auth.access_token_exp", 60)  // 60分钟
	v.SetDefault("auth.refresh_token_exp", 24) // 24小时
	v.SetDefault("auth.issuer", "athena-gateway")
	v.SetDefault("auth.skip_auth_paths", []string{
		"/health",
		"/health/ready",
		"/health/live",
		"/api/v1/auth/login",
		"/api/v1/auth/refresh",
	})
	v.SetDefault("auth.admin_users", []string{"admin"})

	// 日志默认配置
	v.SetDefault("logging.level", "info")
	v.SetDefault("logging.format", "json")
	v.SetDefault("logging.output", "stdout")
	v.SetDefault("logging.max_size", 100)
	v.SetDefault("logging.max_backups", 3)
	v.SetDefault("logging.max_age", 28)
	v.SetDefault("logging.compress", true)

	// 上游服务默认配置
	v.SetDefault("upstream.timeout", 30)

	// 数据库默认配置
	v.SetDefault("database.host", "localhost")
	v.SetDefault("database.port", 5432)
	v.SetDefault("database.username", "athena")
	v.SetDefault("database.password", "password")
	v.SetDefault("database.database", "athena_gateway")
	v.SetDefault("database.max_open_conns", 25)
	v.SetDefault("database.max_idle_conns", 5)
	v.SetDefault("database.conn_max_lifetime", 300)

	// Redis默认配置
	v.SetDefault("redis.host", "localhost")
	v.SetDefault("redis.port", 6379)
	v.SetDefault("redis.password", "")
	v.SetDefault("redis.database", 0)
	v.SetDefault("redis.pool_size", 10)
	v.SetDefault("redis.min_idle_conns", 5)

	// HTTP客户端默认配置
	v.SetDefault("http_client.request_timeout", 30)
	v.SetDefault("http_client.max_idle_conns", 100)
	v.SetDefault("http_client.max_idle_conns_per_host", 10)
	v.SetDefault("http_client.idle_conn_timeout", 90)

	// 限流器默认配置
	v.SetDefault("rate_limit.default_limit", 1000)
	v.SetDefault("rate_limit.default_burst", 100)
	v.SetDefault("rate_limit.window", 60)
	v.SetDefault("rate_limit.adaptive_mode", true)
	v.SetDefault("rate_limit.min_limit", 10)
	v.SetDefault("rate_limit.max_limit", 10000)
	v.SetDefault("rate_limit.adjustment_factor", 0.1)
	v.SetDefault("rate_limit.stats_window", 300)

	// 性能默认配置
	v.SetDefault("performance.enable_pprof", false)
	v.SetDefault("performance.pprof_path", "/debug/pprof")
	v.SetDefault("performance.enable_metrics", true)
	v.SetDefault("performance.metrics_path", "/metrics")
	v.SetDefault("performance.gc_percent", 100)
	v.SetDefault("performance.max_goroutines", 1000)
}

// validateConfig 验证配置
func validateConfig(config *Config) error {
	// 验证服务器配置
	if config.Server.Port <= 0 || config.Server.Port > 65535 {
		return fmt.Errorf("无效的端口号: %d", config.Server.Port)
	}

	if config.Server.ReadTimeout <= 0 {
		return fmt.Errorf("读取超时时间必须大于0")
	}

	if config.Server.WriteTimeout <= 0 {
		return fmt.Errorf("写入超时时间必须大于0")
	}

	// 验证认证配置
	if config.Auth.JWTSecret == "" || config.Auth.JWTSecret == "your-secret-key-change-in-production" {
		return fmt.Errorf("JWT密钥不能为空且必须修改默认值")
	}

	if config.Auth.AccessTokenExp <= 0 {
		return fmt.Errorf("访问令牌过期时间必须大于0")
	}

	if config.Auth.RefreshTokenExp <= 0 {
		return fmt.Errorf("刷新令牌过期时间必须大于0")
	}

	// 验证日志配置
	validLogLevels := map[string]bool{
		"debug": true,
		"info":  true,
		"warn":  true,
		"error": true,
	}

	if !validLogLevels[config.Logging.Level] {
		return fmt.Errorf("无效的日志级别: %s", config.Logging.Level)
	}

	validLogFormats := map[string]bool{
		"json": true,
		"text": true,
	}

	if !validLogFormats[config.Logging.Format] {
		return fmt.Errorf("无效的日志格式: %s", config.Logging.Format)
	}

	validLogOutputs := map[string]bool{
		"stdout": true,
		"file":   true,
	}

	if !validLogOutputs[config.Logging.Output] {
		return fmt.Errorf("无效的日志输出: %s", config.Logging.Output)
	}

	if config.Logging.Output == "file" && config.Logging.FilePath == "" {
		return fmt.Errorf("文件输出模式下必须指定文件路径")
	}

	// 验证上游服务配置
	if config.Upstream.Timeout <= 0 {
		return fmt.Errorf("上游请求超时时间必须大于0")
	}

	return nil
}

// GetConfig 获取全局配置实例
func GetConfig() *Config {
	return AppConfig
}

// IsDevelopment 判断是否为开发环境
func (c *Config) IsDevelopment() bool {
	return os.Getenv("ATHENA_GATEWAY_ENV") == "development" ||
		os.Getenv("GO_ENV") == "development"
}

// IsProduction 判断是否为生产环境
func (c *Config) IsProduction() bool {
	return os.Getenv("ATHENA_GATEWAY_ENV") == "production" ||
		os.Getenv("GO_ENV") == "production"
}

// GetServerAddr 获取服务器地址
func (c *Config) GetServerAddr() string {
	return fmt.Sprintf("%s:%d", c.Server.Host, c.Server.Port)
}

// ReloadConfig 重新加载配置
func ReloadConfig(configPath string) error {
	newConfig, err := LoadConfig(configPath)
	if err != nil {
		return err
	}

	// 更新全局配置
	AppConfig = newConfig

	fmt.Println("配置重新加载成功")
	return nil
}
