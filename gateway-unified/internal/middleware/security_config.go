// Package middleware - 安全中间件配置加载器
package middleware

import (
	"fmt"
	"os"
	"strconv"
	"strings"
	"time"

	"gopkg.in/yaml.v3"
)

// SecurityConfig 安全配置
type SecurityConfig struct {
	JWT          JWTSecurityConfig          `yaml:"jwt"`
	RateLimit    RateLimitSecurityConfig    `yaml:"rate_limit"`
	CORS         CORSSecurityConfig         `yaml:"cors"`
	IPWhitelist  IPWhitelistSecurityConfig  `yaml:"ip_whitelist"`
	APIKeys      APIKeysSecurityConfig      `yaml:"api_keys"`
	BasicAuth    BasicAuthSecurityConfig    `yaml:"basic_auth"`
	SecurityHeaders SecurityHeadersConfig   `yaml:"security_headers"`
	AuditLog     AuditLogConfig             `yaml:"audit_log"`
}

// JWTSecurityConfig JWT安全配置
type JWTSecurityConfig struct {
	Enabled              bool          `yaml:"enabled"`
	Secret               string        `yaml:"secret"`
	Issuer               string        `yaml:"issuer"`
	AccessTokenExpire    int           `yaml:"access_token_expire"`    // 小时
	RefreshTokenExpire   int           `yaml:"refresh_token_expire"`   // 天
	CookieName           string        `yaml:"cookie_name"`
	UseCookie            bool          `yaml:"use_cookie"`
	UseHeader            bool          `yaml:"use_header"`
	HeaderName           string        `yaml:"header_name"`
	UseQuery             bool          `yaml:"use_query"`
	QueryName            string        `yaml:"query_name"`
}

// ToJWTConfig 转换为JWT配置
func (c *JWTSecurityConfig) ToJWTConfig() *JWTConfig {
	secret := c.Secret
	if secret == "" {
		secret = os.Getenv("JWT_SECRET")
		if secret == "" {
			secret = "change-me-in-production"
		}
	}

	return &JWTConfig{
		Secret:            secret,
		Issuer:            c.Issuer,
		Expiration:        time.Duration(c.AccessTokenExpire) * time.Hour,
		RefreshExpiration: time.Duration(c.RefreshTokenExpire) * 24 * time.Hour,
		CookieName:        c.CookieName,
		UseCookie:         c.UseCookie,
		UseHeader:         c.UseHeader,
		HeaderName:        c.HeaderName,
		UseQuery:          c.UseQuery,
		QueryName:         c.QueryName,
	}
}

// RateLimitSecurityConfig 速率限制安全配置
type RateLimitSecurityConfig struct {
	Enabled       bool                `yaml:"enabled"`
	GlobalLimit   int64               `yaml:"global_limit"`
	PerIPLimit    int64               `yaml:"per_ip_limit"`
	Burst         int64               `yaml:"burst"`
	Type          string              `yaml:"type"` // memory, redis
	Redis         RedisConfig         `yaml:"redis"`
	Tiers         []RateLimitTier     `yaml:"tiers"` // 分级限流
}

// RateLimitTier 速率限制等级
type RateLimitTier struct {
	Name      string        `yaml:"name"`
	Condition string        `yaml:"condition"` // IP范围, API Key前缀等
	Limit     int64         `yaml:"limit"`
	Burst     int64         `yaml:"burst"`
	Window    time.Duration `yaml:"window"`
}

// RedisConfig Redis配置
type RedisConfig struct {
	Host     string `yaml:"host"`
	Port     int    `yaml:"port"`
	Password string `yaml:"password"`
	DB       int    `yaml:"db"`
}

// CORSSecurityConfig CORS安全配置
type CORSSecurityConfig struct {
	Enabled          bool     `yaml:"enabled"`
	AllowedOrigins   []string `yaml:"allowed_origins"`
	AllowedMethods   []string `yaml:"allowed_methods"`
	AllowedHeaders   []string `yaml:"allowed_headers"`
	ExposedHeaders   []string `yaml:"exposed_headers"`
	AllowCredentials bool     `yaml:"allow_credentials"`
	MaxAge           int      `yaml:"max_age"`
}

// ToCORSConfig 转换为CORS配置
func (c *CORSSecurityConfig) ToCORSConfig() *CORSConfig {
	return &CORSConfig{
		AllowedOrigins:   c.AllowedOrigins,
		AllowedMethods:   c.AllowedMethods,
		AllowedHeaders:   c.AllowedHeaders,
		ExposedHeaders:   c.ExposedHeaders,
		AllowCredentials: c.AllowCredentials,
		MaxAge:           c.MaxAge,
	}
}

// IPWhitelistSecurityConfig IP白名单安全配置
type IPWhitelistSecurityConfig struct {
	Enabled     bool     `yaml:"enabled"`
	AllowedIPs  []string `yaml:"allowed_ips"`
}

// APIKeysSecurityConfig API密钥安全配置
type APIKeysSecurityConfig struct {
	Enabled bool                 `yaml:"enabled"`
	Keys    []APIKeyConfig       `yaml:"keys"`
}

// APIKeyConfig API密钥配置
type APIKeyConfig struct {
	Name   string   `yaml:"name"`
	Key    string   `yaml:"key"`
	Roles  []string `yaml:"roles"`
}

// BasicAuthSecurityConfig 基本认证安全配置
type BasicAuthSecurityConfig struct {
	Enabled bool                `yaml:"enabled"`
	Users   []BasicAuthUser     `yaml:"users"`
}

// BasicAuthUser 基本认证用户
type BasicAuthUser struct {
	Username string   `yaml:"username"`
	Password string   `yaml:"password"`
	Roles    []string `yaml:"roles"`
}

// SecurityHeadersConfig 安全头配置
type SecurityHeadersConfig struct {
	Enabled                   bool   `yaml:"enabled"`
	XContentTypeOptions       string `yaml:"x_content_type_options"`
	XFrameOptions             string `yaml:"x_frame_options"`
	XXSSProtection            string `yaml:"x_xss_protection"`
	StrictTransportSecurity   string `yaml:"strict_transport_security"`
	ContentSecurityPolicy     string `yaml:"content_security_policy"`
	ReferrerPolicy            string `yaml:"referrer_policy"`
}

// AuditLogConfig 审计日志配置
type AuditLogConfig struct {
	Enabled       bool   `yaml:"enabled"`
	Path          string `yaml:"path"`
	Level         string `yaml:"level"`
	LogRequests   string `yaml:"log_requests"` // all, auth, admin
}

// LoadSecurityConfigFromFile 从文件加载安全配置
func LoadSecurityConfigFromFile(path string) (*SecurityConfig, error) {
	data, err := os.ReadFile(path)
	if err != nil {
		return nil, fmt.Errorf("读取配置文件失败: %w", err)
	}

	var config SecurityConfig
	if err := yaml.Unmarshal(data, &config); err != nil {
		return nil, fmt.Errorf("解析配置文件失败: %w", err)
	}

	// 环境变量替换
	replaceEnvVars(&config)

	return &config, nil
}

// replaceEnvVars 替换环境变量
func replaceEnvVars(config *SecurityConfig) {
	// JWT密钥
	if strings.HasPrefix(config.JWT.Secret, "${") {
		config.JWT.Secret = getEnvOrDefault(config.JWT.Secret, config.JWT.Secret)
	}

	// API密钥
	for i := range config.APIKeys.Keys {
		if strings.HasPrefix(config.APIKeys.Keys[i].Key, "${") {
			config.APIKeys.Keys[i].Key = getEnvOrDefault(config.APIKeys.Keys[i].Key, "")
		}
	}

	// 基本认证密码
	for i := range config.BasicAuth.Users {
		if strings.HasPrefix(config.BasicAuth.Users[i].Password, "${") {
			config.BasicAuth.Users[i].Password = getEnvOrDefault(config.BasicAuth.Users[i].Password, "")
		}
	}

	// Redis密码
	if strings.HasPrefix(config.RateLimit.Redis.Password, "${") {
		config.RateLimit.Redis.Password = getEnvOrDefault(config.RateLimit.Redis.Password, "")
	}
}

// getEnvOrDefault 从环境变量获取值或使用默认值
func getEnvOrDefault(envVar string, defaultValue string) string {
	// 解析 ${VAR:default} 格式
	if strings.HasPrefix(envVar, "${") && strings.HasSuffix(envVar, "}") {
		inner := envVar[2 : len(envVar)-1]
		parts := strings.SplitN(inner, ":", 2)

		if len(parts) == 2 {
			// ${VAR:default} 格式
			if val := os.Getenv(parts[0]); val != "" {
				return val
			}
			return parts[1]
		}

		// ${VAR} 格式
		if val := os.Getenv(inner); val != "" {
			return val
		}
	}

	return defaultValue
}

// LoadSecurityConfigFromMap 从Map加载安全配置（兼容现有代码）
func LoadSecurityConfigFromMap(m map[string]interface{}) *SecurityConfig {
	config := &SecurityConfig{}

	// JWT配置
	if jwt, ok := m["jwt"].(map[string]interface{}); ok {
		if enabled, ok := jwt["enabled"].(bool); ok {
			config.JWT.Enabled = enabled
		}
		if secret, ok := jwt["secret"].(string); ok {
			config.JWT.Secret = secret
		}
	}

	// 速率限制配置
	if rateLimit, ok := m["rate_limit"].(map[string]interface{}); ok {
		if enabled, ok := rateLimit["enabled"].(bool); ok {
			config.RateLimit.Enabled = enabled
		}
		if globalLimit, ok := rateLimit["global_limit"].(int); ok {
			config.RateLimit.GlobalLimit = int64(globalLimit)
		}
		if perIPLimit, ok := rateLimit["per_ip_limit"].(int); ok {
			config.RateLimit.PerIPLimit = int64(perIPLimit)
		}
		if burst, ok := rateLimit["burst"].(int); ok {
			config.RateLimit.Burst = int64(burst)
		}
	}

	// CORS配置
	if cors, ok := m["cors"].(map[string]interface{}); ok {
		config.CORS.Enabled = cors["enabled"].(bool)

		if origins, ok := cors["allowed_origins"].([]interface{}); ok {
			for _, origin := range origins {
				if originStr, ok := origin.(string); ok {
					config.CORS.AllowedOrigins = append(config.CORS.AllowedOrigins, originStr)
				}
			}
		}

		if methods, ok := cors["allowed_methods"].([]interface{}); ok {
			for _, method := range methods {
				if methodStr, ok := method.(string); ok {
					config.CORS.AllowedMethods = append(config.CORS.AllowedMethods, methodStr)
				}
			}
		}

		if headers, ok := cors["allowed_headers"].([]interface{}); ok {
			for _, header := range headers {
				if headerStr, ok := header.(string); ok {
					config.CORS.AllowedHeaders = append(config.CORS.AllowedHeaders, headerStr)
				}
			}
		}

		config.CORS.AllowCredentials = cors["allow_credentials"].(bool)
		config.CORS.MaxAge = cors["max_age"].(int)
	}

	// IP白名单配置
	if ipWhitelist, ok := m["ip_whitelist"].(map[string]interface{}); ok {
		config.IPWhitelist.Enabled = ipWhitelist["enabled"].(bool)

		if ips, ok := ipWhitelist["allowed_ips"].([]interface{}); ok {
			for _, ip := range ips {
				if ipStr, ok := ip.(string); ok {
					config.IPWhitelist.AllowedIPs = append(config.IPWhitelist.AllowedIPs, ipStr)
				}
			}
		}
	}

	// API密钥配置
	if apiKeys, ok := m["api_keys"].(map[string]interface{}); ok {
		config.APIKeys.Enabled = apiKeys["enabled"].(bool)

		if keys, ok := apiKeys["keys"].([]interface{}); ok {
			for _, key := range keys {
				if keyStr, ok := key.(string); ok {
					config.APIKeys.Keys = append(config.APIKeys.Keys, APIKeyConfig{
						Name: keyStr,
						Key:  keyStr,
					})
				}
			}
		}
	}

	return config
}

// GetEnvInt 从环境变量获取整数
func GetEnvInt(key string, defaultValue int) int {
	if val := os.Getenv(key); val != "" {
		if intVal, err := strconv.Atoi(val); err == nil {
			return intVal
		}
	}
	return defaultValue
}

// GetEnvBool 从环境变量获取布尔值
func GetEnvBool(key string, defaultValue bool) bool {
	if val := os.Getenv(key); val != "" {
		if boolVal, err := strconv.ParseBool(val); err == nil {
			return boolVal
		}
	}
	return defaultValue
}

// GetEnvDuration 从环境变量获取时间间隔
func GetEnvDuration(key string, defaultValue time.Duration) time.Duration {
	if val := os.Getenv(key); val != "" {
		if duration, err := time.ParseDuration(val); err == nil {
			return duration
		}
	}
	return defaultValue
}
