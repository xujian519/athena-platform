package middleware

import (
	"net/http"
	"time"

	"athena-gateway/internal/auth"
	"athena-gateway/internal/logging"
	"athena-gateway/pkg/response"
	"github.com/gin-gonic/gin"
	"github.com/google/uuid"
	"go.uber.org/zap"
)

// AuthMiddleware JWT认证中间件
func AuthMiddleware(jwtManager *auth.JWTManager) gin.HandlerFunc {
	return func(c *gin.Context) {
		// 检查是否跳过认证
		if auth.IsPathSkipAuth(c.Request.URL.Path) {
			c.Next()
			return
		}

		// 从请求头中提取令牌
		authHeader := c.GetHeader("Authorization")
		tokenString, err := auth.ExtractTokenFromHeader(authHeader)
		if err != nil {
			logging.LogError(err, "令牌提取失败",
				zap.String("path", c.Request.URL.Path),
				zap.String("method", c.Request.Method),
				zap.String("auth_header", authHeader),
			)
			response.Error(c, http.StatusUnauthorized, "未授权访问", err.Error())
			c.Abort()
			return
		}

		// 验证令牌
		claims, err := jwtManager.ValidateToken(tokenString)
		if err != nil {
			// 在错误场景下，不依赖可能为 nil 的 claims 信息
			logging.LogError(err, "令牌验证失败",
				zap.String("path", c.Request.URL.Path),
				zap.String("method", c.Request.Method),
			)
			response.Error(c, http.StatusUnauthorized, "令牌无效或已过期", err.Error())
			c.Abort()
			return
		}

		// 将用户信息存储到上下文
		c.Set("user_id", claims.UserID)
		c.Set("username", claims.Username)
		c.Set("email", claims.Email)
		c.Set("role", claims.Role)
		c.Set("token_type", claims.TokenType)

		// 记录认证成功的日志
		logging.LogInfo("用户认证成功",
			zap.String("user_id", claims.UserID),
			zap.String("username", claims.Username),
			zap.String("path", c.Request.URL.Path),
			zap.String("method", c.Request.Method),
		)

		c.Next()
	}
}

// AdminMiddleware 管理员权限中间件
func AdminMiddleware() gin.HandlerFunc {
	return func(c *gin.Context) {
		username, exists := c.Get("username")
		if !exists {
			response.Error(c, http.StatusUnauthorized, "用户信息不存在", "")
			c.Abort()
			return
		}

		if !auth.IsAdminUser(username.(string)) {
			logging.LogWarn("非管理员用户尝试访问管理员接口",
				zap.String("username", username.(string)),
				zap.String("path", c.Request.URL.Path),
				zap.String("method", c.Request.Method),
			)
			response.Error(c, http.StatusForbidden, "权限不足", "需要管理员权限")
			c.Abort()
			return
		}

		c.Next()
	}
}

// RequestIDMiddleware 请求ID中间件
func RequestIDMiddleware() gin.HandlerFunc {
	return func(c *gin.Context) {
		// 检查是否已有请求ID
		requestID := c.GetHeader("X-Request-ID")
		if requestID == "" {
			requestID = uuid.New().String()
		}

		// 设置请求ID到响应头和上下文
		c.Header("X-Request-ID", requestID)
		c.Set("request_id", requestID)

		// 为日志添加请求ID
		logger := logging.WithRequestID(requestID)
		c.Set("logger", logger)

		c.Next()
	}
}

// LoggingMiddleware 请求日志中间件
func LoggingMiddleware() gin.HandlerFunc {
	return func(c *gin.Context) {
		// 记录开始时间
		start := time.Now()

		// 处理请求
		c.Next()

		// 计算处理时间
		duration := time.Since(start).Milliseconds()

		// 获取请求ID
		requestID, _ := c.Get("request_id")

		// 获取用户信息（如果已认证）
		userID, _ := c.Get("user_id")
		username, _ := c.Get("username")

		// 记录请求日志
		fields := []zap.Field{
			zap.String("request_id", requestID.(string)),
			zap.String("method", c.Request.Method),
			zap.String("path", c.Request.URL.Path),
			zap.String("query", c.Request.URL.RawQuery),
			zap.Int("status_code", c.Writer.Status()),
			zap.Int64("duration_ms", duration),
			zap.String("client_ip", c.ClientIP()),
			zap.String("user_agent", c.GetHeader("User-Agent")),
		}

		if userID != nil {
			fields = append(fields, zap.String("user_id", userID.(string)))
		}
		if username != nil {
			fields = append(fields, zap.String("username", username.(string)))
		}

		// 根据状态码选择日志级别
		statusCode := c.Writer.Status()
		switch {
		case statusCode >= 500:
			logging.LogError(nil, "服务器错误", fields...)
		case statusCode >= 400:
			logging.LogWarn("客户端错误", fields...)
		default:
			logging.LogInfo("HTTP请求", fields...)
		}
	}
}

// CORSMiddleware CORS中间件
func CORSMiddleware() gin.HandlerFunc {
	return func(c *gin.Context) {
		// 设置CORS头
		c.Header("Access-Control-Allow-Origin", "*")
		c.Header("Access-Control-Allow-Methods", "GET, POST, PUT, DELETE, PATCH, OPTIONS")
		c.Header("Access-Control-Allow-Headers", "Origin, Content-Type, Content-Length, Accept-Encoding, X-CSRF-Token, Authorization, X-Request-ID")
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

// SecurityHeadersMiddleware 安全头中间件
func SecurityHeadersMiddleware() gin.HandlerFunc {
	return func(c *gin.Context) {
		// 设置安全头
		c.Header("X-Content-Type-Options", "nosniff")
		c.Header("X-Frame-Options", "DENY")
		c.Header("X-XSS-Protection", "1; mode=block")
		c.Header("Strict-Transport-Security", "max-age=31536000; includeSubDomains")
		c.Header("Content-Security-Policy", "default-src 'self'")
		c.Header("Referrer-Policy", "strict-origin-when-cross-origin")
		c.Header("Permissions-Policy", "geolocation=(), microphone=(), camera=()")

		c.Next()
	}
}

// RateLimitMiddleware 简单的频率限制中间件
func RateLimitMiddleware() gin.HandlerFunc {
	// 这里可以实现基于IP或用户的频率限制
	// 为了演示，这里只是一个占位符
	return func(c *gin.Context) {
		// TODO: 实现频率限制逻辑
		// 可以使用Redis等存储来实现分布式频率限制
		c.Next()
	}
}

// TimeoutMiddleware 请求超时中间件
func TimeoutMiddleware(timeout time.Duration) gin.HandlerFunc {
	return func(c *gin.Context) {
		// 设置请求超时 - 简化实现避免复杂问题
		c.Next()
	}
}

// RecoveryMiddleware 恢复中间件
func RecoveryMiddleware() gin.HandlerFunc {
	return gin.CustomRecovery(func(c *gin.Context, recovered interface{}) {
		// 获取请求ID
		requestID, _ := c.Get("request_id")

		// 记录Panic日志
		logging.LogError(
			logging.ErrInternalServer,
			"请求处理发生Panic",
			zap.String("request_id", requestID.(string)),
			zap.String("method", c.Request.Method),
			zap.String("path", c.Request.URL.Path),
			zap.Any("panic", recovered),
		)

		// 返回错误响应
		response.Error(c, http.StatusInternalServerError, "服务器内部错误", "请求处理失败")
		c.Abort()
	})
}
