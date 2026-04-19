package config

import (
	"time"
)

// Config 应用配置结构
type Config struct {
	Server      ServerConfig     `yaml:"server" mapstructure:"server"`
	Logging     LoggingConfig    `yaml:"logging" mapstructure:"logging"`
	Redis       RedisConfig      `yaml:"redis" mapstructure:"redis"`
	Auth        AuthConfig       `yaml:"auth" mapstructure:"auth"`
	Limiter     LimiterConfig    `yaml:"limiter" mapstructure:"limiter"`
	Proxy       ProxyConfig      `yaml:"proxy" mapstructure:"proxy"`
	Monitoring  MonitoringConfig `yaml:"monitoring" mapstructure:"monitoring"`
	Security    SecurityConfig   `yaml:"security" mapstructure:"security"`
	Services    []ServiceConfig  `yaml:"services" mapstructure:"services"`
	Environment string           `yaml:"environment" mapstructure:"environment"`
}

// ServerConfig 服务器配置
type ServerConfig struct {
	Host           string        `yaml:"host" mapstructure:"host"`
	Port           int           `yaml:"port" mapstructure:"port"`
	ReadTimeout    time.Duration `yaml:"read_timeout" mapstructure:"read_timeout"`
	WriteTimeout   time.Duration `yaml:"write_timeout" mapstructure:"write_timeout"`
	MaxHeaderBytes int           `yaml:"max_header_bytes" mapstructure:"max_header_bytes"`
}

// LoggingConfig 日志配置
type LoggingConfig struct {
	Level  string `yaml:"level" mapstructure:"level"`
	Format string `yaml:"format" mapstructure:"format"`
	Output string `yaml:"output" mapstructure:"output"`
}

// RedisConfig Redis配置
type RedisConfig struct {
	Host         string        `yaml:"host" mapstructure:"host"`
	Port         int           `yaml:"port" mapstructure:"port"`
	Password     string        `yaml:"password" mapstructure:"password"`
	DB           int           `yaml:"db" mapstructure:"db"`
	PoolSize     int           `yaml:"pool_size" mapstructure:"pool_size"`
	MinIdleConns int           `yaml:"min_idle_conns" mapstructure:"min_idle_conns"`
	MaxRetries   int           `yaml:"max_retries" mapstructure:"max_retries"`
	DialTimeout  time.Duration `yaml:"dial_timeout" mapstructure:"dial_timeout"`
	ReadTimeout  time.Duration `yaml:"read_timeout" mapstructure:"read_timeout"`
	WriteTimeout time.Duration `yaml:"write_timeout" mapstructure:"write_timeout"`
}

// AuthConfig 认证配置
type AuthConfig struct {
	JWTSecret      string        `yaml:"jwt_secret" mapstructure:"jwt_secret"`
	TokenExpire    time.Duration `yaml:"token_expire" mapstructure:"token_expire"`
	RefreshExpire  time.Duration `yaml:"refresh_expire" mapstructure:"refresh_expire"`
	Issuer         string        `yaml:"issuer" mapstructure:"issuer"`
	SkipPaths      []string      `yaml:"skip_paths" mapstructure:"skip_paths"`
	RequiredScopes []string      `yaml:"required_scopes" mapstructure:"required_scopes"`
}

// LimiterConfig 限流配置
type LimiterConfig struct {
	Enabled            bool           `yaml:"enabled" mapstructure:"enabled"`
	RequestsPerMinute  int            `yaml:"requests_per_minute" mapstructure:"requests_per_minute"`
	Burst              int            `yaml:"burst" mapstructure:"burst"`
	Strategies         []StrategyConf `yaml:"strategies" mapstructure:"strategies"`
	DistributedEnabled bool           `yaml:"distributed_enabled" mapstructure:"distributed_enabled"`
	RedisKeyPrefix     string         `yaml:"redis_key_prefix" mapstructure:"redis_key_prefix"`
}

// StrategyConf 限流策略配置
type StrategyConf struct {
	Type  string `yaml:"type" mapstructure:"type"`
	Limit int    `yaml:"limit" mapstructure:"limit"`
	Match string `yaml:"match" mapstructure:"match"`
}

// ProxyConfig 代理配置
type ProxyConfig struct {
	Timeout        time.Duration      `yaml:"timeout" mapstructure:"timeout"`
	RetryAttempts  int                `yaml:"retry_attempts" mapstructure:"retry_attempts"`
	RetryDelay     time.Duration      `yaml:"retry_delay" mapstructure:"retry_delay"`
	CircuitBreaker CircuitBreakerConf `yaml:"circuit_breaker" mapstructure:"circuit_breaker"`
	LoadBalancer   LoadBalancerConf   `yaml:"load_balancer" mapstructure:"load_balancer"`
	HealthCheck    HealthCheckConf    `yaml:"health_check" mapstructure:"health_check"`
}

// CircuitBreakerConf 熔断器配置
type CircuitBreakerConf struct {
	Enabled          bool          `yaml:"enabled" mapstructure:"enabled"`
	FailureThreshold int           `yaml:"failure_threshold" mapstructure:"failure_threshold"`
	RecoveryTimeout  time.Duration `yaml:"recovery_timeout" mapstructure:"recovery_timeout"`
	SuccessThreshold int           `yaml:"success_threshold" mapstructure:"success_threshold"`
	Timeout          time.Duration `yaml:"timeout" mapstructure:"timeout"`
}

// LoadBalancerConf 负载均衡配置
type LoadBalancerConf struct {
	Strategy string             `yaml:"strategy" mapstructure:"strategy"`
	Nodes    []LoadBalancerNode `yaml:"nodes" mapstructure:"nodes"`
}

// LoadBalancerNode 负载均衡节点
type LoadBalancerNode struct {
	URL     string `yaml:"url" mapstructure:"url"`
	Weight  int    `yaml:"weight" mapstructure:"weight"`
	Healthy bool   `yaml:"healthy" mapstructure:"healthy"`
}

// HealthCheckConf 健康检查配置
type HealthCheckConf struct {
	Enabled            bool          `yaml:"enabled" mapstructure:"enabled"`
	Path               string        `yaml:"path" mapstructure:"path"`
	Interval           time.Duration `yaml:"interval" mapstructure:"interval"`
	Timeout            time.Duration `yaml:"timeout" mapstructure:"timeout"`
	UnhealthyThreshold int           `yaml:"unhealthy_threshold" mapstructure:"unhealthy_threshold"`
	HealthyThreshold   int           `yaml:"healthy_threshold" mapstructure:"healthy_threshold"`
}

// MonitoringConfig 监控配置
type MonitoringConfig struct {
	Prometheus  PrometheusConf  `yaml:"prometheus" mapstructure:"prometheus"`
	Tracing     TracingConf     `yaml:"tracing" mapstructure:"tracing"`
	HealthCheck HealthCheckConf `yaml:"health_check" mapstructure:"health_check"`
}

// PrometheusConf Prometheus配置
type PrometheusConf struct {
	Enabled bool   `yaml:"enabled" mapstructure:"enabled"`
	Path    string `yaml:"path" mapstructure:"path"`
	Port    int    `yaml:"port" mapstructure:"port"`
}

// TracingConf 链路追踪配置
type TracingConf struct {
	Enabled            bool                `yaml:"enabled" mapstructure:"enabled"`
	ServiceName        string              `yaml:"service_name" mapstructure:"service_name"`
	ServiceVersion     string              `yaml:"service_version" mapstructure:"service_version"`
	Environment        string              `yaml:"environment" mapstructure:"environment"`
	Jaeger             JaegerTracingConf   `yaml:"jaeger" mapstructure:"jaeger"`
	Sampling           TracingSamplingConf `yaml:"sampling" mapstructure:"sampling"`
	BatchTimeout       time.Duration       `yaml:"batch_timeout" mapstructure:"batch_timeout"`
	ExportTimeout      time.Duration       `yaml:"export_timeout" mapstructure:"export_timeout"`
	MaxExportBatchSize int                 `yaml:"max_export_batch_size" mapstructure:"max_export_batch_size"`
}

// JaegerTracingConf Jaeger追踪配置
type JaegerTracingConf struct {
	Endpoint string `yaml:"endpoint" mapstructure:"endpoint"`
	Username string `yaml:"username" mapstructure:"username"`
	Password string `yaml:"password" mapstructure:"password"`
	Insecure bool   `yaml:"insecure" mapstructure:"insecure"`
}

// TracingSamplingConf 采样配置
type TracingSamplingConf struct {
	Type  string  `yaml:"type" mapstructure:"type"`
	Param float64 `yaml:"param" mapstructure:"param"`
}

// SecurityConfig 安全配置
type SecurityConfig struct {
	CORS        CORSConf        `yaml:"cors" mapstructure:"cors"`
	CSRF        CSRFConf        `yaml:"csrf" mapstructure:"csrf"`
	RateLimit   RateLimitConf   `yaml:"rate_limit" mapstructure:"rate_limit"`
	IPWhitelist IPWhitelistConf `yaml:"ip_whitelist" mapstructure:"ip_whitelist"`
}

// CORSConf CORS配置
type CORSConf struct {
	Enabled          bool     `yaml:"enabled" mapstructure:"enabled"`
	AllowedOrigins   []string `yaml:"allowed_origins" mapstructure:"allowed_origins"`
	AllowedMethods   []string `yaml:"allowed_methods" mapstructure:"allowed_methods"`
	AllowedHeaders   []string `yaml:"allowed_headers" mapstructure:"allowed_headers"`
	ExposedHeaders   []string `yaml:"exposed_headers" mapstructure:"exposed_headers"`
	AllowCredentials bool     `yaml:"allow_credentials" mapstructure:"allow_credentials"`
	MaxAge           int      `yaml:"max_age" mapstructure:"max_age"`
}

// CSRFConf CSRF配置
type CSRFConf struct {
	Enabled    bool   `yaml:"enabled" mapstructure:"enabled"`
	Secret     string `yaml:"secret" mapstructure:"secret"`
	CookieName string `yaml:"cookie_name" mapstructure:"cookie_name"`
	Domain     string `yaml:"domain" mapstructure:"domain"`
	Path       string `yaml:"path" mapstructure:"path"`
	MaxAge     int    `yaml:"max_age" mapstructure:"max_age"`
	Secure     bool   `yaml:"secure" mapstructure:"secure"`
	HttpOnly   bool   `yaml:"http_only" mapstructure:"http_only"`
}

// RateLimitConf 限流配置
type RateLimitConf struct {
	Enabled bool `yaml:"enabled" mapstructure:"enabled"`
	Limit   int  `yaml:"limit" mapstructure:"limit"`
}

// IPWhitelistConf IP白名单配置
type IPWhitelistConf struct {
	Enabled bool     `yaml:"enabled" mapstructure:"enabled"`
	IPs     []string `yaml:"ips" mapstructure:"ips"`
}

// ServiceConfig 服务配置
type ServiceConfig struct {
	Name           string                 `yaml:"name" mapstructure:"name"`
	URL            string                 `yaml:"url" mapstructure:"url"`
	HealthCheck    string                 `yaml:"health_check" mapstructure:"health_check"`
	Timeout        time.Duration          `yaml:"timeout" mapstructure:"timeout"`
	Retries        int                    `yaml:"retries" mapstructure:"retries"`
	CircuitBreaker CircuitBreakerConf     `yaml:"circuit_breaker" mapstructure:"circuit_breaker"`
	LoadBalancer   LoadBalancerConf       `yaml:"load_balancer" mapstructure:"load_balancer"`
	Metadata       map[string]interface{} `yaml:"metadata" mapstructure:"metadata"`
}
