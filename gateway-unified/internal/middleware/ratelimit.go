// Package middleware - 限流中间件
package middleware

import (
	"context"
	"net/http"
	"time"

	"github.com/gin-gonic/gin"
	"github.com/athena-workspace/gateway-unified/internal/ratelimit"
)

// RateLimitConfig 限流中间件配置
type RateLimitConfig struct {
	DefaultLimit int64 // 默认限制（每分钟）
	DefaultBurst int64 // 默认突发
}

// DefaultRateLimitConfig 默认限流配置
func DefaultRateLimitConfig() *RateLimitConfig {
	return &RateLimitConfig{
		DefaultLimit: 1000, // 1000 requests/min
		DefaultBurst: 100,  // 100 burst
	}
}

// RateLimitMiddleware 创建限流中间件
func RateLimitMiddleware(limiter *ratelimit.AdaptiveRateLimiter) gin.HandlerFunc {
	return func(c *gin.Context) {
		// 获取客户端标识（IP地址）
		clientIP := c.ClientIP()

		// 创建超时上下文
		ctx, cancel := context.WithTimeout(c.Request.Context(), 100*time.Millisecond)
		defer cancel()

		// 检查是否允许请求
		if !limiter.Allow(ctx, clientIP) {
			// 获取限流信息
			result := limiter.Limit(ctx, clientIP)

			c.JSON(http.StatusTooManyRequests, gin.H{
				"error":        "Rate limit exceeded",
				"limit":        result.Limit,
				"remaining":    result.Remaining,
				"retry_after":  result.RetryAfter.Seconds(),
			})
			c.Abort()
			return
		}

		c.Next()
	}
}
