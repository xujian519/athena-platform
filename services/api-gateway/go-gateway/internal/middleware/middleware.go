package middleware

import (
	"bytes"
	"fmt"
	"io"
	"net/http"
	"runtime/debug"
	"strings"
	"time"

	"athena-gateway/pkg/logger"

	"github.com/gin-gonic/gin"
	"github.com/google/uuid"
	"go.uber.org/zap"
)

// Logger 日志中间件
func Logger() gin.HandlerFunc {
	return func(c *gin.Context) {
		// 记录开始时间
		start := time.Now()

		// 读取请求体（用于日志记录）
		var requestBody []byte
		if c.Request.Body != nil {
			requestBody, _ = io.ReadAll(c.Request.Body)
			c.Request.Body = io.NopCloser(bytes.NewBuffer(requestBody))
		}

		// 处理请求
		c.Next()

		// 计算处理时间
		duration := time.Since(start)

		// 获取响应状态
		status := c.Writer.Status()

		// 构建日志字段
		fields := []zap.Field{
			zap.String("request_id", c.GetString("request_id")),
			zap.String("method", c.Request.Method),
			zap.String("path", c.Request.URL.Path),
			zap.String("query", c.Request.URL.RawQuery),
			zap.String("ip", c.ClientIP()),
			zap.String("user_agent", c.Request.UserAgent()),
			zap.Int("status", status),
			zap.Duration("duration", duration),
			zap.Int("response_size", c.Writer.Size()),
		}

		// 添加用户信息（如果已认证）
		if userID, exists := c.Get("user_id"); exists {
			fields = append(fields, zap.String("user_id", userID.(string)))
		}

		// 根据状态码选择日志级别
		switch {
		case status >= 500:
			// 服务器错误
			fields = append(fields, zap.String("error", c.Errors.String()))
			if len(requestBody) > 0 {
				fields = append(fields, zap.ByteString("request_body", requestBody))
			}
			logger.Error("HTTP请求处理失败", fields...)
		case status >= 400:
			// 客户端错误
			fields = append(fields, zap.String("error", c.Errors.String()))
			logger.Warn("HTTP请求错误", fields...)
		default:
			// 成功请求
			logger.Info("HTTP请求处理成功", fields...)
		}
	}
}

// RequestID 请求ID中间件
func RequestID() gin.HandlerFunc {
	return func(c *gin.Context) {
		// 检查是否已有请求ID
		requestID := c.GetHeader("X-Request-ID")
		if requestID == "" {
			requestID = uuid.New().String()
		}

		// 设置到上下文和响应头
		c.Set("request_id", requestID)
		c.Header("X-Request-ID", requestID)

		c.Next()
	}
}

// Recovery 恢复中间件
func Recovery() gin.HandlerFunc {
	return func(c *gin.Context) {
		defer func() {
			if err := recover(); err != nil {
				// 记录panic信息
				logger.Error("服务器发生panic",
					zap.String("request_id", c.GetString("request_id")),
					zap.Any("error", err),
					zap.String("stack", string(debug.Stack())),
					zap.String("method", c.Request.Method),
					zap.String("path", c.Request.URL.Path),
					zap.String("ip", c.ClientIP()),
				)

				// 返回错误响应
				c.JSON(http.StatusInternalServerError, gin.H{
					"error":      "服务器内部错误",
					"request_id": c.GetString("request_id"),
				})

				c.Abort()
			}
		}()

		c.Next()
	}
}

// CORS 跨域中间件
func CORS(cfg interface{}) gin.HandlerFunc {
	return func(c *gin.Context) {
		origin := c.Request.Header.Get("Origin")

		// 设置CORS头
		c.Header("Access-Control-Allow-Origin", "*")
		c.Header("Access-Control-Allow-Methods", "GET, POST, PUT, DELETE, OPTIONS, PATCH")
		c.Header("Access-Control-Allow-Headers", "Origin, Content-Type, Accept, Authorization, X-Requested-With, X-Request-ID, X-API-Key")
		c.Header("Access-Control-Expose-Headers", "X-Request-ID, X-Total-Count")
		c.Header("Access-Control-Allow-Credentials", "true")
		c.Header("Access-Control-Max-Age", "86400")

		// 处理预检请求
		if c.Request.Method == "OPTIONS" {
			c.AbortWithStatus(http.StatusNoContent)
			return
		}

		c.Next()
	}
}

// Security 安全中间件
func Security() gin.HandlerFunc {
	return func(c *gin.Context) {
		// 设置安全头
		c.Header("X-Content-Type-Options", "nosniff")
		c.Header("X-Frame-Options", "DENY")
		c.Header("X-XSS-Protection", "1; mode=block")
		c.Header("Strict-Transport-Security", "max-age=31536000; includeSubDomains")
		c.Header("Content-Security-Policy", "default-src 'self'")
		c.Header("Referrer-Policy", "strict-origin-when-cross-origin")

		c.Next()
	}
}

// Timeout 超时中间件
func Timeout(timeout time.Duration) gin.HandlerFunc {
	return func(c *gin.Context) {
		// 设置请求超时
		c.Request = c.Request.WithContext(
			createContextWithTimeout(c.Request.Context(), timeout),
		)

		c.Next()
	}
}

// createContextWithTimeout 创建带超时的上下文
func createContextWithTimeout(parent context.Context, timeout time.Duration) context.Context {
	ctx, cancel := context.WithTimeout(parent, timeout)

	// 在请求完成时取消上下文
	go func() {
		defer cancel()
		select {
		case <-ctx.Done():
			// 上下文已取消或超时
		case <-parent.Done():
			// 父上下文已取消
		}
	}()

	return ctx
}

// RequestSize 请求大小限制中间件
func RequestSize(maxSize int64) gin.HandlerFunc {
	return func(c *gin.Context) {
		if c.Request.ContentLength > maxSize {
			logger.Warn("请求体过大",
				zap.String("request_id", c.GetString("request_id")),
				zap.Int64("content_length", c.Request.ContentLength),
				zap.Int64("max_size", maxSize),
			)
			c.JSON(http.StatusRequestEntityTooLarge, gin.H{
				"error": fmt.Sprintf("请求体过大，最大允许%d字节", maxSize),
			})
			c.Abort()
			return
		}

		c.Next()
	}
}

// StripTrailingSlash 移除尾部斜杠中间件
func StripTrailingSlash() gin.HandlerFunc {
	return func(c *gin.Context) {
		path := c.Request.URL.Path
		if len(path) > 1 && strings.HasSuffix(path, "/") {
			c.Request.URL.Path = strings.TrimSuffix(path, "/")
		}
		c.Next()
	}
}

// ForceHTTPS 强制HTTPS中间件
func ForceHTTPS() gin.HandlerFunc {
	return func(c *gin.Context) {
		// 检查是否为HTTPS请求
		if c.Request.TLS == nil {
			// 转换为HTTPS URL
			httpsURL := "https://" + c.Request.Host + c.Request.URL.RequestURI()

			logger.Info("重定向到HTTPS",
				zap.String("request_id", c.GetString("request_id")),
				zap.String("from", c.Request.URL.String()),
				zap.String("to", httpsURL),
			)

			c.Redirect(http.StatusMovedPermanently, httpsURL)
			c.Abort()
			return
		}

		c.Next()
	}
}

// Version 版本中间件
func Version(version string) gin.HandlerFunc {
	return func(c *gin.Context) {
		c.Header("X-API-Version", version)
		c.Next()
	}
}

// Maintenance 维护模式中间件
func Maintenance(enabled bool, message string) gin.HandlerFunc {
	return func(c *gin.Context) {
		if enabled {
			// 允许健康检查请求
			if c.Request.URL.Path == "/health" || c.Request.URL.Path == "/ready" {
				c.Next()
				return
			}

			// 返回维护模式响应
			c.JSON(http.StatusServiceUnavailable, gin.H{
				"error":     "系统维护中",
				"message":   message,
				"timestamp": time.Now().UTC(),
			})
			c.Abort()
			return
		}

		c.Next()
	}
}

// APIKey API密钥认证中间件
func APIKey(validKeys []string) gin.HandlerFunc {
	return func(c *gin.Context) {
		apiKey := c.GetHeader("X-API-Key")
		if apiKey == "" {
			c.JSON(http.StatusUnauthorized, gin.H{
				"error": "缺少API密钥",
			})
			c.Abort()
			return
		}

		// 验证API密钥
		valid := false
		for _, key := range validKeys {
			if apiKey == key {
				valid = true
				break
			}
		}

		if !valid {
			logger.Warn("无效的API密钥",
				zap.String("request_id", c.GetString("request_id")),
				zap.String("api_key", apiKey),
				zap.String("ip", c.ClientIP()),
			)
			c.JSON(http.StatusUnauthorized, gin.H{
				"error": "API密钥无效",
			})
			c.Abort()
			return
		}

		c.Next()
	}
}
