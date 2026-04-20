// Package middleware - CORS中间件
package middleware

import (
	"net/http"
	"strconv"
	"strings"

	"github.com/gin-gonic/gin"
)

// CORSConfig CORS配置
type CORSConfig struct {
	// 允许的源（支持通配符*）
	// 示例: ["http://localhost:3000", "https://example.com", "*"]
	AllowedOrigins []string

	// 允许的HTTP方法
	AllowedMethods []string

	// 允许的请求头
	AllowedHeaders []string

	// 暴露的响应头
	ExposedHeaders []string

	// 是否允许携带凭证（Cookie等）
	AllowCredentials bool

	// 预检请求缓存时间（秒）
	MaxAge int

	// 是否启用调试日志
	Debug bool
}

// DefaultCORSConfig 默认CORS配置
func DefaultCORSConfig() *CORSConfig {
	return &CORSConfig{
		AllowedOrigins: []string{"*"},
		AllowedMethods: []string{"GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"},
		AllowedHeaders: []string{"Origin", "Content-Type", "Accept", "Authorization", "X-API-Key"},
		ExposedHeaders: []string{"Content-Length", "Content-Type"},
		AllowCredentials: false,
		MaxAge:          86400, // 24小时
		Debug:           false,
	}
}

// DevelopmentCORSConfig 开发环境CORS配置
func DevelopmentCORSConfig() *CORSConfig {
	return &CORSConfig{
		AllowedOrigins: []string{
			"http://localhost:3000",
			"http://localhost:3001",
			"http://127.0.0.1:3000",
			"http://127.0.0.1:3001",
			"http://localhost:8080",
			"http://localhost:8005",
		},
		AllowedMethods: []string{"GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"},
		AllowedHeaders: []string{"Origin", "Content-Type", "Accept", "Authorization", "X-API-Key", "X-Request-ID"},
		ExposedHeaders: []string{"Content-Length", "Content-Type", "X-Request-ID"},
		AllowCredentials: true,
		MaxAge:          86400,
		Debug:           true,
	}
}

// ProductionCORSConfig 生产环境CORS配置
func ProductionCORSConfig(allowedOrigins []string) *CORSConfig {
	return &CORSConfig{
		AllowedOrigins: allowedOrigins,
		AllowedMethods: []string{"GET", "POST", "PUT", "DELETE", "OPTIONS"},
		AllowedHeaders: []string{"Origin", "Content-Type", "Accept", "Authorization", "X-API-Key"},
		ExposedHeaders: []string{"Content-Length"},
		AllowCredentials: false, // 生产环境使用通配符时不允许携带凭证
		MaxAge:          3600,   // 1小时
		Debug:           false,
	}
}

// CORSMiddleware CORS中间件
func CORSMiddleware(config *CORSConfig) gin.HandlerFunc {
	if config == nil {
		config = DefaultCORSConfig()
	}

	// 设置默认值
	if len(config.AllowedMethods) == 0 {
		config.AllowedMethods = []string{"GET", "POST", "PUT", "DELETE", "OPTIONS"}
	}
	if len(config.AllowedHeaders) == 0 {
		config.AllowedHeaders = []string{"Origin", "Content-Type", "Accept", "Authorization"}
	}
	if config.MaxAge == 0 {
		config.MaxAge = 86400
	}

	// 预计算允许的源（用于快速查找）
	allowedOriginsMap := make(map[string]bool)
	hasWildcard := false
	for _, origin := range config.AllowedOrigins {
		if origin == "*" {
			hasWildcard = true
		} else {
			allowedOriginsMap[origin] = true
		}
	}

	return func(c *gin.Context) {
		origin := c.GetHeader("Origin")

		// 处理预检请求
		if c.Request.Method == "OPTIONS" {
			c.Header("Access-Control-Allow-Methods", strings.Join(config.AllowedMethods, ", "))
			c.Header("Access-Control-Allow-Headers", strings.Join(config.AllowedHeaders, ", "))
			c.Header("Access-Control-Max-Age", formatInt(config.MaxAge))

			// 设置允许的源
			if hasWildcard {
				if config.AllowCredentials {
					// 允许凭证时不能使用通配符
					if origin != "" && isOriginAllowed(origin, allowedOriginsMap) {
						c.Header("Access-Control-Allow-Origin", origin)
						c.Header("Access-Control-Allow-Credentials", "true")
					}
				} else {
					c.Header("Access-Control-Allow-Origin", "*")
				}
			} else if origin != "" && isOriginAllowed(origin, allowedOriginsMap) {
				c.Header("Access-Control-Allow-Origin", origin)
				if config.AllowCredentials {
					c.Header("Access-Control-Allow-Credentials", "true")
				}
			}

			if config.Debug {
				c.Header("X-CORS-Debug", "preflight")
			}

			c.AbortWithStatus(http.StatusNoContent)
			return
		}

		// 处理普通请求
		if hasWildcard {
			if config.AllowCredentials {
				// 允许凭证时不能使用通配符
				if origin != "" && isOriginAllowed(origin, allowedOriginsMap) {
					c.Header("Access-Control-Allow-Origin", origin)
					c.Header("Access-Control-Allow-Credentials", "true")
				}
			} else {
				c.Header("Access-Control-Allow-Origin", "*")
			}
		} else if origin != "" && isOriginAllowed(origin, allowedOriginsMap) {
			c.Header("Access-Control-Allow-Origin", origin)
			if config.AllowCredentials {
				c.Header("Access-Control-Allow-Credentials", "true")
			}
		}

		// 设置暴露的响应头
		if len(config.ExposedHeaders) > 0 {
			c.Header("Access-Control-Expose-Headers", strings.Join(config.ExposedHeaders, ", "))
		}

		if config.Debug {
			c.Header("X-CORS-Debug", "request")
		}

		c.Next()
	}
}

// isOriginAllowed 检查源是否被允许
func isOriginAllowed(origin string, allowedOrigins map[string]bool) bool {
	// 精确匹配
	if allowedOrigins[origin] {
		return true
	}

	// 支持子域名匹配
	// 例如: *.example.com 匹配 foo.example.com, bar.example.com
	for allowedOrigin := range allowedOrigins {
		if strings.HasPrefix(allowedOrigin, "*.") {
			suffix := strings.TrimPrefix(allowedOrigin, "*.")
			if strings.HasSuffix(origin, "."+suffix) || origin == suffix {
				return true
			}
		}
	}

	return false
}

// formatInt 格式化整数
func formatInt(n int) string {
	return strconv.Itoa(n)
}

// CORSByOrigin 按源动态设置CORS的中间件
// 允许在运行时动态判断是否允许某个源
func CORSByOrigin(allowFunc func(origin string) bool) gin.HandlerFunc {
	return func(c *gin.Context) {
		origin := c.GetHeader("Origin")

		// 处理预检请求
		if c.Request.Method == "OPTIONS" {
			c.Header("Access-Control-Allow-Methods", "GET, POST, PUT, DELETE, OPTIONS, PATCH")
			c.Header("Access-Control-Allow-Headers", "Origin, Content-Type, Accept, Authorization, X-API-Key")
			c.Header("Access-Control-Max-Age", "86400")

			if origin != "" && allowFunc(origin) {
				c.Header("Access-Control-Allow-Origin", origin)
				c.Header("Access-Control-Allow-Credentials", "true")
			}

			c.AbortWithStatus(http.StatusNoContent)
			return
		}

		// 处理普通请求
		if origin != "" && allowFunc(origin) {
			c.Header("Access-Control-Allow-Origin", origin)
			c.Header("Access-Control-Allow-Credentials", "true")
			c.Header("Access-Control-Expose-Headers", "Content-Length, Content-Type")
		}

		c.Next()
	}
}

// CORSByWhitelist 基于白名单的CORS中间件
func CORSByWhitelist(whitelist []string) gin.HandlerFunc {
	whitelistMap := make(map[string]bool)
	for _, origin := range whitelist {
		whitelistMap[origin] = true
	}

	return CORSByOrigin(func(origin string) bool {
		return whitelistMap[origin]
	})
}

// CORSByRegex 基于正则表达式的CORS中间件
// 支持通配符匹配，如 *.example.com
func CORSByRegex(patterns []string) gin.HandlerFunc {
	return CORSByOrigin(func(origin string) bool {
		for _, pattern := range patterns {
			// 支持通配符端口匹配，如 localhost:*
			if strings.Contains(pattern, ":*") {
				prefix := strings.TrimSuffix(pattern, ":*")
				if strings.HasPrefix(origin, prefix+":") {
					return true
				}
			}
			// 支持子域名匹配，如 *.example.com
			if strings.HasPrefix(pattern, "*.") {
				suffix := strings.TrimPrefix(pattern, "*.")
				if strings.HasSuffix(origin, "."+suffix) || origin == suffix {
					return true
				}
			}
			// 精确匹配
			if pattern == origin {
				return true
			}
		}
		return false
	})
}
