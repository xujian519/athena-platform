package config

import (
	"fmt"
	"net/url"
	"strings"
)

// Validate 验证配置
func Validate(cfg *Config) error {
	if err := validateServer(cfg.Server); err != nil {
		return fmt.Errorf("server config invalid: %w", err)
	}

	if err := validateRedis(cfg.Redis); err != nil {
		return fmt.Errorf("redis config invalid: %w", err)
	}

	if err := validateAuth(cfg.Auth); err != nil {
		return fmt.Errorf("auth config invalid: %w", err)
	}

	if err := validateLimiter(cfg.Limiter); err != nil {
		return fmt.Errorf("limiter config invalid: %w", err)
	}

	if err := validateProxy(cfg.Proxy); err != nil {
		return fmt.Errorf("proxy config invalid: %w", err)
	}

	if err := validateServices(cfg.Services); err != nil {
		return fmt.Errorf("services config invalid: %w", err)
	}

	if err := validateSecurity(cfg.Security); err != nil {
		return fmt.Errorf("security config invalid: %w", err)
	}

	return nil
}

// validateServer 验证服务器配置
func validateServer(cfg ServerConfig) error {
	if cfg.Port <= 0 || cfg.Port > 65535 {
		return fmt.Errorf("port must be between 1 and 65535")
	}

	if cfg.Host == "" {
		return fmt.Errorf("host cannot be empty")
	}

	if cfg.ReadTimeout <= 0 {
		return fmt.Errorf("read timeout must be positive")
	}

	if cfg.WriteTimeout <= 0 {
		return fmt.Errorf("write timeout must be positive")
	}

	if cfg.MaxHeaderBytes <= 0 {
		return fmt.Errorf("max header bytes must be positive")
	}

	return nil
}

// validateRedis 验证Redis配置
func validateRedis(cfg RedisConfig) error {
	if cfg.Host == "" {
		return fmt.Errorf("host cannot be empty")
	}

	if cfg.Port <= 0 || cfg.Port > 65535 {
		return fmt.Errorf("port must be between 1 and 65535")
	}

	if cfg.DB < 0 || cfg.DB > 15 {
		return fmt.Errorf("redis db must be between 0 and 15")
	}

	if cfg.PoolSize <= 0 {
		return fmt.Errorf("pool size must be positive")
	}

	if cfg.MinIdleConns < 0 {
		return fmt.Errorf("min idle conns cannot be negative")
	}

	if cfg.MaxRetries < 0 {
		return fmt.Errorf("max retries cannot be negative")
	}

	return nil
}

// validateAuth 验证认证配置
func validateAuth(cfg AuthConfig) error {
	if cfg.JWTSecret == "" {
		return fmt.Errorf("JWT_SECRET cannot be empty - must be set via environment variable")
	}

	if len(cfg.JWTSecret) < 32 {
		return fmt.Errorf("JWT_SECRET must be at least 32 characters for security")
	}

	// 检查是否使用了不安全的默认值
	unsafeDefaults := []string{
		"athena-gateway-jwt-secret-key-change-in-production",
		"athena-gateway-dev-jwt-secret-not-for-production",
		"your-secret-key-change-in-production",
		"test-secret",
		"dev-secret",
		"default-secret",
	}

	for _, unsafe := range unsafeDefaults {
		if cfg.JWTSecret == unsafe {
			return fmt.Errorf("JWT_SECRET appears to be using an unsafe default value: %s", unsafe)
		}
	}

	if cfg.TokenExpire <= 0 {
		return fmt.Errorf("token expire must be positive")
	}

	if cfg.RefreshExpire <= 0 {
		return fmt.Errorf("refresh expire must be positive")
	}

	if cfg.Issuer == "" {
		return fmt.Errorf("issuer cannot be empty")
	}

	for _, path := range cfg.SkipPaths {
		if path == "" {
			return fmt.Errorf("skip paths cannot contain empty strings")
		}
		if !strings.HasPrefix(path, "/") {
			return fmt.Errorf("skip path must start with '/': %s", path)
		}
	}

	return nil
}

// validateLimiter 验证限流配置
func validateLimiter(cfg LimiterConfig) error {
	if cfg.Enabled {
		if cfg.RequestsPerMinute <= 0 {
			return fmt.Errorf("requests per minute must be positive when limiter is enabled")
		}

		if cfg.Burst <= 0 {
			return fmt.Errorf("burst must be positive when limiter is enabled")
		}

		for i, strategy := range cfg.Strategies {
			if err := validateStrategy(strategy); err != nil {
				return fmt.Errorf("strategy %d invalid: %w", i, err)
			}
		}

		if cfg.DistributedEnabled && cfg.RedisKeyPrefix == "" {
			return fmt.Errorf("redis key prefix cannot be empty when distributed limiter is enabled")
		}
	}

	return nil
}

// validateStrategy 验证限流策略
func validateStrategy(strategy StrategyConf) error {
	validTypes := []string{"ip", "user", "api_key", "header"}
	validType := false
	for _, t := range validTypes {
		if strategy.Type == t {
			validType = true
			break
		}
	}
	if !validType {
		return fmt.Errorf("invalid strategy type: %s, must be one of %v", strategy.Type, validTypes)
	}

	if strategy.Limit <= 0 {
		return fmt.Errorf("strategy limit must be positive")
	}

	if strategy.Match != "" && strategy.Type != "header" {
		return fmt.Errorf("match can only be set for header type strategy")
	}

	return nil
}

// validateProxy 验证代理配置
func validateProxy(cfg ProxyConfig) error {
	if cfg.Timeout <= 0 {
		return fmt.Errorf("timeout must be positive")
	}

	if cfg.RetryAttempts < 0 {
		return fmt.Errorf("retry attempts cannot be negative")
	}

	if cfg.RetryDelay < 0 {
		return fmt.Errorf("retry delay cannot be negative")
	}

	if err := validateCircuitBreaker(cfg.CircuitBreaker); err != nil {
		return fmt.Errorf("circuit breaker config invalid: %w", err)
	}

	if err := validateLoadBalancer(cfg.LoadBalancer); err != nil {
		return fmt.Errorf("load balancer config invalid: %w", err)
	}

	if err := validateHealthCheck(cfg.HealthCheck); err != nil {
		return fmt.Errorf("health check config invalid: %w", err)
	}

	return nil
}

// validateCircuitBreaker 验证熔断器配置
func validateCircuitBreaker(cfg CircuitBreakerConf) error {
	if cfg.Enabled {
		if cfg.FailureThreshold <= 0 {
			return fmt.Errorf("failure threshold must be positive when circuit breaker is enabled")
		}

		if cfg.RecoveryTimeout <= 0 {
			return fmt.Errorf("recovery timeout must be positive when circuit breaker is enabled")
		}

		if cfg.SuccessThreshold <= 0 {
			return fmt.Errorf("success threshold must be positive when circuit breaker is enabled")
		}

		if cfg.Timeout <= 0 {
			return fmt.Errorf("timeout must be positive when circuit breaker is enabled")
		}
	}

	return nil
}

// validateLoadBalancer 验证负载均衡配置
func validateLoadBalancer(cfg LoadBalancerConf) error {
	validStrategies := []string{"round_robin", "weighted", "least_connections", "random"}
	validStrategy := false
	for _, s := range validStrategies {
		if cfg.Strategy == s {
			validStrategy = true
			break
		}
	}
	if !validStrategy {
		return fmt.Errorf("invalid load balancer strategy: %s, must be one of %v", cfg.Strategy, validStrategies)
	}

	if len(cfg.Nodes) > 0 {
		for i, node := range cfg.Nodes {
			if err := validateLoadBalancerNode(node); err != nil {
				return fmt.Errorf("node %d invalid: %w", i, err)
			}
		}
	}

	return nil
}

// validateLoadBalancerNode 验证负载均衡节点
func validateLoadBalancerNode(node LoadBalancerNode) error {
	if node.URL == "" {
		return fmt.Errorf("url cannot be empty")
	}

	if _, err := url.Parse(node.URL); err != nil {
		return fmt.Errorf("invalid url format: %w", err)
	}

	if node.Weight < 0 {
		return fmt.Errorf("weight cannot be negative")
	}

	return nil
}

// validateHealthCheck 验证健康检查配置
func validateHealthCheck(cfg HealthCheckConf) error {
	if cfg.Enabled {
		if cfg.Path == "" {
			return fmt.Errorf("path cannot be empty when health check is enabled")
		}

		if !strings.HasPrefix(cfg.Path, "/") {
			return fmt.Errorf("path must start with '/': %s", cfg.Path)
		}

		if cfg.Interval <= 0 {
			return fmt.Errorf("interval must be positive when health check is enabled")
		}

		if cfg.Timeout <= 0 {
			return fmt.Errorf("timeout must be positive when health check is enabled")
		}

		if cfg.UnhealthyThreshold <= 0 {
			return fmt.Errorf("unhealthy threshold must be positive when health check is enabled")
		}

		if cfg.HealthyThreshold <= 0 {
			return fmt.Errorf("healthy threshold must be positive when health check is enabled")
		}
	}

	return nil
}

// validateServices 验证服务配置
func validateServices(services []ServiceConfig) error {
	if len(services) == 0 {
		return fmt.Errorf("at least one service must be configured")
	}

	names := make(map[string]bool)
	for i, service := range services {
		if err := validateService(service); err != nil {
			return fmt.Errorf("service %d invalid: %w", i, err)
		}

		if names[service.Name] {
			return fmt.Errorf("duplicate service name: %s", service.Name)
		}
		names[service.Name] = true
	}

	return nil
}

// validateService 验证单个服务配置
func validateService(service ServiceConfig) error {
	if service.Name == "" {
		return fmt.Errorf("name cannot be empty")
	}

	if service.URL == "" {
		return fmt.Errorf("url cannot be empty")
	}

	if _, err := url.Parse(service.URL); err != nil {
		return fmt.Errorf("invalid url format: %w", err)
	}

	if service.HealthCheck != "" && !strings.HasPrefix(service.HealthCheck, "/") {
		return fmt.Errorf("health check path must start with '/': %s", service.HealthCheck)
	}

	if service.Timeout <= 0 {
		return fmt.Errorf("timeout must be positive")
	}

	if service.Retries < 0 {
		return fmt.Errorf("retries cannot be negative")
	}

	if err := validateCircuitBreaker(service.CircuitBreaker); err != nil {
		return fmt.Errorf("circuit breaker config invalid: %w", err)
	}

	if err := validateLoadBalancer(service.LoadBalancer); err != nil {
		return fmt.Errorf("load balancer config invalid: %w", err)
	}

	return nil
}

// validateSecurity 验证安全配置
func validateSecurity(cfg SecurityConfig) error {
	if err := validateCORS(cfg.CORS); err != nil {
		return fmt.Errorf("cors config invalid: %w", err)
	}

	if err := validateCSRF(cfg.CSRF); err != nil {
		return fmt.Errorf("csrf config invalid: %w", err)
	}

	if err := validateRateLimit(cfg.RateLimit); err != nil {
		return fmt.Errorf("rate limit config invalid: %w", err)
	}

	if err := validateIPWhitelist(cfg.IPWhitelist); err != nil {
		return fmt.Errorf("ip whitelist config invalid: %w", err)
	}

	return nil
}

// validateCORS 验证CORS配置
func validateCORS(cfg CORSConf) error {
	if cfg.Enabled {
		if len(cfg.AllowedOrigins) == 0 {
			return fmt.Errorf("allowed origins cannot be empty when cors is enabled")
		}

		for _, origin := range cfg.AllowedOrigins {
			if origin == "*" {
				continue
			}
			if _, err := url.Parse(origin); err != nil {
				return fmt.Errorf("invalid origin format: %s", origin)
			}
		}

		if len(cfg.AllowedMethods) == 0 {
			return fmt.Errorf("allowed methods cannot be empty when cors is enabled")
		}

		if cfg.MaxAge < 0 {
			return fmt.Errorf("max age cannot be negative")
		}
	}

	return nil
}

// validateCSRF 验证CSRF配置
func validateCSRF(cfg CSRFConf) error {
	if cfg.Enabled {
		if cfg.Secret == "" {
			return fmt.Errorf("secret cannot be empty when csrf is enabled")
		}

		if len(cfg.Secret) < 32 {
			return fmt.Errorf("secret must be at least 32 characters when csrf is enabled")
		}

		if cfg.CookieName == "" {
			return fmt.Errorf("cookie name cannot be empty when csrf is enabled")
		}

		if cfg.MaxAge < 0 {
			return fmt.Errorf("max age cannot be negative")
		}
	}

	return nil
}

// validateRateLimit 验证限流配置
func validateRateLimit(cfg RateLimitConf) error {
	if cfg.Enabled && cfg.Limit <= 0 {
		return fmt.Errorf("limit must be positive when rate limit is enabled")
	}
	return nil
}

// validateIPWhitelist 验证IP白名单配置
func validateIPWhitelist(cfg IPWhitelistConf) error {
	if cfg.Enabled && len(cfg.IPs) == 0 {
		return fmt.Errorf("ips cannot be empty when ip whitelist is enabled")
	}

	for _, ip := range cfg.IPs {
		if ip == "" {
			return fmt.Errorf("ip cannot be empty")
		}

		if ip != "*" {
			if !isValidIP(ip) && !isValidCIDR(ip) {
				return fmt.Errorf("invalid ip or cidr format: %s", ip)
			}
		}
	}

	return nil
}

// isValidIP 检查是否为有效IP地址
func isValidIP(ip string) bool {
	parts := strings.Split(ip, ".")
	if len(parts) != 4 {
		return false
	}

	for _, part := range parts {
		if part == "" {
			return false
		}
		num := 0
		for _, c := range part {
			if c < '0' || c > '9' {
				return false
			}
			num = num*10 + int(c-'0')
		}
		if num < 0 || num > 255 {
			return false
		}
	}

	return true
}

// isValidCIDR 检查是否为有效CIDR格式
func isValidCIDR(cidr string) bool {
	parts := strings.Split(cidr, "/")
	if len(parts) != 2 {
		return false
	}

	if !isValidIP(parts[0]) {
		return false
	}

	prefix := parts[1]
	if len(prefix) == 0 || len(prefix) > 2 {
		return false
	}

	for _, c := range prefix {
		if c < '0' || c > '9' {
			return false
		}
	}

	return true
}

// validateLogging 验证日志配置
func validateLogging(cfg LoggingConfig) error {
	validLevels := []string{"debug", "info", "warn", "error"}
	validLevel := false
	for _, level := range validLevels {
		if cfg.Level == level {
			validLevel = true
			break
		}
	}
	if !validLevel {
		return fmt.Errorf("invalid log level: %s, must be one of %v", cfg.Level, validLevels)
	}

	validFormats := []string{"json", "text"}
	validFormat := false
	for _, format := range validFormats {
		if cfg.Format == format {
			validFormat = true
			break
		}
	}
	if !validFormat {
		return fmt.Errorf("invalid log format: %s, must be one of %v", cfg.Format, validFormats)
	}

	validOutputs := []string{"stdout", "stderr", "file"}
	validOutput := false
	for _, output := range validOutputs {
		if cfg.Output == output {
			validOutput = true
			break
		}
	}
	if !validOutput {
		return fmt.Errorf("invalid log output: %s, must be one of %v", cfg.Output, validOutputs)
	}

	return nil
}

// validateMonitoring 验证监控配置
func validateMonitoring(cfg MonitoringConfig) error {
	if err := validatePrometheus(cfg.Prometheus); err != nil {
		return fmt.Errorf("prometheus config invalid: %w", err)
	}

	if err := validateTracing(cfg.Tracing); err != nil {
		return fmt.Errorf("tracing config invalid: %w", err)
	}

	if err := validateHealthCheck(cfg.HealthCheck); err != nil {
		return fmt.Errorf("health check config invalid: %w", err)
	}

	return nil
}

// validatePrometheus 验证Prometheus配置
func validatePrometheus(cfg PrometheusConf) error {
	if cfg.Enabled {
		if cfg.Path == "" {
			return fmt.Errorf("path cannot be empty when prometheus is enabled")
		}

		if !strings.HasPrefix(cfg.Path, "/") {
			return fmt.Errorf("path must start with '/': %s", cfg.Path)
		}

		if cfg.Port <= 0 || cfg.Port > 65535 {
			return fmt.Errorf("port must be between 1 and 65535")
		}
	}

	return nil
}

// validateTracing 验证链路追踪配置
func validateTracing(cfg TracingConf) error {
	if cfg.Enabled {
		if cfg.ServiceName == "" {
			return fmt.Errorf("service name cannot be empty when tracing is enabled")
		}

		if cfg.Jaeger.Endpoint == "" {
			return fmt.Errorf("jaeger endpoint cannot be empty when provider is jaeger")
		}

		if cfg.Sampling.Param < 0 || cfg.Sampling.Param > 1 {
			return fmt.Errorf("sample rate must be between 0 and 1")
		}
	}

	return nil
}
