package config

import (
	"fmt"
	"os"
	"path/filepath"

	"github.com/joho/godotenv"
	"github.com/spf13/viper"
)

// Load 加载配置
func Load() (*Config, error) {
	// 加载环境变量文件
	if err := loadEnvFile(); err != nil {
		fmt.Printf("Warning: Failed to load .env file: %v\n", err)
	}

	// 设置配置文件路径
	configPath := getConfigPath()

	// 配置viper
	v := viper.New()
	v.SetConfigName("config")
	v.SetConfigType("yaml")
	v.AddConfigPath(configPath)
	v.AddConfigPath("./configs")
	v.AddConfigPath(".")

	// 设置环境变量前缀
	v.SetEnvPrefix("GATEWAY")
	v.AutomaticEnv()

	// 读取配置文件
	if err := v.ReadInConfig(); err != nil {
		return nil, fmt.Errorf("failed to read config file: %w", err)
	}

	// 解析配置到结构体
	var cfg Config
	if err := v.Unmarshal(&cfg); err != nil {
		return nil, fmt.Errorf("failed to unmarshal config: %w", err)
	}

	// 验证配置
	if err := Validate(&cfg); err != nil {
		return nil, fmt.Errorf("config validation failed: %w", err)
	}

	// 设置默认环境
	if cfg.Environment == "" {
		cfg.Environment = os.Getenv("ENV")
		if cfg.Environment == "" {
			cfg.Environment = "development"
		}
	}

	return &cfg, nil
}

// loadEnvFile 加载环境变量文件
func loadEnvFile() error {
	// 尝试加载.env文件
	if err := godotenv.Load(); err != nil {
		// 尝试加载环境特定的env文件
		env := os.Getenv("ENV")
		if env == "" {
			env = "development"
		}

		envFile := fmt.Sprintf(".env.%s", env)
		if err := godotenv.Load(envFile); err != nil {
			return fmt.Errorf("neither .env nor %s found", envFile)
		}
	}
	return nil
}

// getConfigPath 获取配置文件路径
func getConfigPath() string {
	configPath := os.Getenv("CONFIG_PATH")
	if configPath == "" {
		configPath = "./configs"
	}
	return configPath
}

// LoadFromPath 从指定路径加载配置
func LoadFromPath(configPath, configName string) (*Config, error) {
	v := viper.New()
	v.SetConfigName(configName)
	v.SetConfigType("yaml")
	v.AddConfigPath(configPath)

	if err := v.ReadInConfig(); err != nil {
		return nil, fmt.Errorf("failed to read config file: %w", err)
	}

	var cfg Config
	if err := v.Unmarshal(&cfg); err != nil {
		return nil, fmt.Errorf("failed to unmarshal config: %w", err)
	}

	if err := Validate(&cfg); err != nil {
		return nil, fmt.Errorf("config validation failed: %w", err)
	}

	return &cfg, nil
}

// SaveConfig 保存配置到文件
func SaveConfig(cfg *Config, filePath string) error {
	v := viper.New()

	// 设置配置值
	if err := v.MergeConfigMap(cfgToMap(cfg)); err != nil {
		return fmt.Errorf("failed to merge config: %w", err)
	}

	// 确保目录存在
	dir := filepath.Dir(filePath)
	if err := os.MkdirAll(dir, 0755); err != nil {
		return fmt.Errorf("failed to create config directory: %w", err)
	}

	// 写入配置文件
	if err := v.WriteConfigAs(filePath); err != nil {
		return fmt.Errorf("failed to write config file: %w", err)
	}

	return nil
}

// cfgToMap 将配置结构体转换为map
func cfgToMap(cfg *Config) map[string]interface{} {
	return map[string]interface{}{
		"server": map[string]interface{}{
			"host":             cfg.Server.Host,
			"port":             cfg.Server.Port,
			"read_timeout":     cfg.Server.ReadTimeout,
			"write_timeout":    cfg.Server.WriteTimeout,
			"max_header_bytes": cfg.Server.MaxHeaderBytes,
		},
		"logging": map[string]interface{}{
			"level":  cfg.Logging.Level,
			"format": cfg.Logging.Format,
			"output": cfg.Logging.Output,
		},
		"redis": map[string]interface{}{
			"host":           cfg.Redis.Host,
			"port":           cfg.Redis.Port,
			"password":       cfg.Redis.Password,
			"db":             cfg.Redis.DB,
			"pool_size":      cfg.Redis.PoolSize,
			"min_idle_conns": cfg.Redis.MinIdleConns,
			"max_retries":    cfg.Redis.MaxRetries,
			"dial_timeout":   cfg.Redis.DialTimeout,
			"read_timeout":   cfg.Redis.ReadTimeout,
			"write_timeout":  cfg.Redis.WriteTimeout,
		},
		"auth": map[string]interface{}{
			"jwt_secret":      cfg.Auth.JWTSecret,
			"token_expire":    cfg.Auth.TokenExpire,
			"refresh_expire":  cfg.Auth.RefreshExpire,
			"issuer":          cfg.Auth.Issuer,
			"skip_paths":      cfg.Auth.SkipPaths,
			"required_scopes": cfg.Auth.RequiredScopes,
		},
		"limiter": map[string]interface{}{
			"enabled":             cfg.Limiter.Enabled,
			"requests_per_minute": cfg.Limiter.RequestsPerMinute,
			"burst":               cfg.Limiter.Burst,
			"strategies":          cfg.Limiter.Strategies,
			"distributed_enabled": cfg.Limiter.DistributedEnabled,
			"redis_key_prefix":    cfg.Limiter.RedisKeyPrefix,
		},
		"proxy": map[string]interface{}{
			"timeout":         cfg.Proxy.Timeout,
			"retry_attempts":  cfg.Proxy.RetryAttempts,
			"retry_delay":     cfg.Proxy.RetryDelay,
			"circuit_breaker": cfg.Proxy.CircuitBreaker,
			"load_balancer":   cfg.Proxy.LoadBalancer,
			"health_check":    cfg.Proxy.HealthCheck,
		},
		"monitoring": map[string]interface{}{
			"prometheus":   cfg.Monitoring.Prometheus,
			"tracing":      cfg.Monitoring.Tracing,
			"health_check": cfg.Monitoring.HealthCheck,
		},
		"security": map[string]interface{}{
			"cors":         cfg.Security.CORS,
			"csrf":         cfg.Security.CSRF,
			"rate_limit":   cfg.Security.RateLimit,
			"ip_whitelist": cfg.Security.IPWhitelist,
		},
		"services":    cfg.Services,
		"environment": cfg.Environment,
	}
}
