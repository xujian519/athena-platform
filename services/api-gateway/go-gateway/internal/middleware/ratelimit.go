package middleware

import (
	"fmt"
	"net/http"
	"sync"
	"time"

	"athena-gateway/internal/config"
	"athena-gateway/pkg/logger"

	"github.com/gin-gonic/gin"
	"go.uber.org/zap"
	"golang.org/x/time/rate"
)

// RateLimiter 限流器接口
type RateLimiter interface {
	Allow() bool
	AllowN(n int) bool
	Wait() error
	WaitN(n int) error
}

// IPRateLimiter IP限流器
type IPRateLimiter struct {
	limiter    *rate.Limiter
	lastAccess time.Time
}

// UserRateLimiter 用户限流器
type UserRateLimiter struct {
	limiters map[string]*rate.Limiter
	mu       sync.RWMutex
	rate     rate.Limit
	burst    int
}

// GlobalRateLimiter 全局限流器
type GlobalRateLimiter struct {
	limiter *rate.Limiter
}

// RateLimitMiddleware 限流中间件
func RateLimit(cfg *config.Config) gin.HandlerFunc {
	// 如果限流未启用，直接通过
	if !cfg.RateLimit.Enabled {
		return func(c *gin.Context) {
			c.Next()
		}
	}

	// 创建全局限流器
	globalLimiter := NewGlobalRateLimiter(
		rate.Every(time.Minute/time.Duration(cfg.RateLimit.RequestsPerMinute)),
		cfg.RateLimit.BurstSize,
	)

	// 创建用户限流器
	userLimiter := NewUserRateLimiter(
		rate.Every(time.Minute/time.Duration(cfg.RateLimit.RequestsPerMinute)),
		cfg.RateLimit.BurstSize,
	)

	return func(c *gin.Context) {
		// 检查IP白名单
		if cfg.RateLimit.WhitelistEnabled && isInWhitelist(c.ClientIP(), cfg.RateLimit.Whitelist) {
			c.Next()
			return
		}

		// 全局限流检查
		if !globalLimiter.Allow() {
			logger.Warn("全局限流触发",
				zap.String("ip", c.ClientIP()),
				zap.String("path", c.Request.URL.Path),
			)
			c.JSON(http.StatusTooManyRequests, gin.H{
				"error":       "请求过于频繁，请稍后再试",
				"retry_after": 60,
			})
			c.Abort()
			return
		}

		// 获取用户ID（如果已认证）
		userID, exists := c.Get("user_id")
		if exists {
			// 基于用户的限流
			userLimiter := userLimiter.GetLimiter(userID.(string))
			if !userLimiter.Allow() {
				logger.Warn("用户限流触发",
					zap.String("user_id", userID.(string)),
					zap.String("path", c.Request.URL.Path),
				)
				c.JSON(http.StatusTooManyRequests, gin.H{
					"error":       "请求过于频繁，请稍后再试",
					"retry_after": 60,
				})
				c.Abort()
				return
			}
		} else {
			// 基于IP的限流
			ipLimiter := getIPRateLimiter(c.ClientIP(), cfg.RateLimit.RequestsPerMinute, cfg.RateLimit.BurstSize)
			if !ipLimiter.Allow() {
				logger.Warn("IP限流触发",
					zap.String("ip", c.ClientIP()),
					zap.String("path", c.Request.URL.Path),
				)
				c.JSON(http.StatusTooManyRequests, gin.H{
					"error":       "请求过于频繁，请稍后再试",
					"retry_after": 60,
				})
				c.Abort()
				return
			}
		}

		c.Next()
	}
}

// 全局限流器映射
var (
	globalRateLimiters = make(map[string]*IPRateLimiter)
	globalRateMu       sync.RWMutex
)

// NewIPRateLimiter 创建IP限流器
func NewIPRateLimiter(requestsPerMinute, burst int) *IPRateLimiter {
	return &IPRateLimiter{
		limiter: rate.NewLimiter(
			rate.Every(time.Minute/time.Duration(requestsPerMinute)),
			burst,
		),
		lastAccess: time.Now(),
	}
}

// getIPRateLimiter 获取或创建IP限流器
func getIPRateLimiter(ip string, requestsPerMinute, burst int) *IPRateLimiter {
	globalRateMu.Lock()
	defer globalRateMu.Unlock()

	// 查找现有限流器
	if limiter, exists := globalRateLimiters[ip]; exists {
		limiter.lastAccess = time.Now()
		return limiter
	}

	// 创建新限流器
	limiter := NewIPRateLimiter(requestsPerMinute, burst)
	globalRateLimiters[ip] = limiter

	// 启动清理goroutine
	go cleanupStaleIPLimiters()

	return limiter
}

// cleanupStaleIPLimiters 清理过期的IP限流器
func cleanupStaleIPLimiters() {
	globalRateMu.Lock()
	defer globalRateMu.Unlock()

	for ip, limiter := range globalRateLimiters {
		if time.Since(limiter.lastAccess) > time.Hour {
			delete(globalRateLimiters, ip)
		}
	}
}

// Allow 实现RateLimiter接口
func (l *IPRateLimiter) Allow() bool {
	return l.limiter.Allow()
}

// AllowN 实现RateLimiter接口
func (l *IPRateLimiter) AllowN(n int) bool {
	return l.limiter.AllowN(time.Now(), n)
}

// Wait 实现RateLimiter接口
func (l *IPRateLimiter) Wait() error {
	return l.limiter.Wait(context.Background())
}

// WaitN 实现RateLimiter接口
func (l *IPRateLimiter) WaitN(n int) error {
	return l.limiter.WaitN(context.Background(), n)
}

// NewUserRateLimiter 创建用户限流器
func NewUserRateLimiter(r rate.Limit, burst int) *UserRateLimiter {
	return &UserRateLimiter{
		limiters: make(map[string]*rate.Limiter),
		rate:     r,
		burst:    burst,
	}
}

// GetLimiter 获取用户限流器
func (ul *UserRateLimiter) GetLimiter(userID string) *rate.Limiter {
	ul.mu.Lock()
	defer ul.mu.Unlock()

	// 查找现有限流器
	if limiter, exists := ul.limiters[userID]; exists {
		return limiter
	}

	// 创建新限流器
	limiter := rate.NewLimiter(ul.rate, ul.burst)
	ul.limiters[userID] = limiter

	// 启动清理goroutine
	go ul.cleanupStaleLimiters()

	return limiter
}

// cleanupStaleLimiters 清理过期的用户限流器
func (ul *UserRateLimiter) cleanupStaleLimiters() {
	ul.mu.Lock()
	defer ul.mu.Unlock()

	// 这里可以添加更复杂的清理逻辑，比如基于最后访问时间
	if len(ul.limiters) > 10000 {
		// 当限流器数量过多时，清理一半
		count := 0
		for userID := range ul.limiters {
			if count >= len(ul.limiters)/2 {
				break
			}
			delete(ul.limiters, userID)
			count++
		}
	}
}

// NewGlobalRateLimiter 创建全局限流器
func NewGlobalRateLimiter(r rate.Limit, burst int) *GlobalRateLimiter {
	return &GlobalRateLimiter{
		limiter: rate.NewLimiter(r, burst),
	}
}

// Allow 实现RateLimiter接口
func (gl *GlobalRateLimiter) Allow() bool {
	return gl.limiter.Allow()
}

// AllowN 实现RateLimiter接口
func (gl *GlobalRateLimiter) AllowN(n int) bool {
	return gl.limiter.AllowN(time.Now(), n)
}

// Wait 实现RateLimiter接口
func (gl *GlobalRateLimiter) Wait() error {
	return gl.limiter.Wait(context.Background())
}

// WaitN 实现RateLimiter接口
func (gl *GlobalRateLimiter) WaitN(n int) error {
	return gl.limiter.WaitN(context.Background(), n)
}

// isInWhitelist 检查IP是否在白名单中
func isInWhitelist(ip string, whitelist []string) bool {
	for _, whitelistIP := range whitelist {
		if ip == whitelistIP {
			return true
		}
	}
	return false
}

// CustomRateLimit 自定义限流中间件
func CustomRateLimit(requestsPerMinute, burst int) gin.HandlerFunc {
	limiter := rate.NewLimiter(
		rate.Every(time.Minute/time.Duration(requestsPerMinute)),
		burst,
	)

	return func(c *gin.Context) {
		if !limiter.Allow() {
			logger.Warn("自定义限流触发",
				zap.String("ip", c.ClientIP()),
				zap.String("path", c.Request.URL.Path),
				zap.Int("requests_per_minute", requestsPerMinute),
			)
			c.JSON(http.StatusTooManyRequests, gin.H{
				"error":       fmt.Sprintf("请求过于频繁，每分钟最多允许%d个请求", requestsPerMinute),
				"retry_after": 60,
			})
			c.Abort()
			return
		}

		c.Next()
	}
}

// APIKeyRateLimit API密钥限流中间件
func APIKeyRateLimit(apiKeyToRateLimit map[string]int, defaultRate int) gin.HandlerFunc {
	limiters := make(map[string]*rate.Limiter)
	mu := sync.RWMutex{}

	return func(c *gin.Context) {
		apiKey := c.GetHeader("X-API-Key")
		if apiKey == "" {
			// 没有API密钥，使用默认限流
			apiKey = "default"
		}

		mu.RLock()
		limiter, exists := limiters[apiKey]
		mu.RUnlock()

		if !exists {
			mu.Lock()
			// 双重检查
			if limiter, exists = limiters[apiKey]; !exists {
				rateLimit := defaultRate
				if r, ok := apiKeyToRateLimit[apiKey]; ok {
					rateLimit = r
				}
				limiter = rate.NewLimiter(
					rate.Every(time.Minute/time.Duration(rateLimit)),
					rateLimit,
				)
				limiters[apiKey] = limiter
			}
			mu.Unlock()
		}

		if !limiter.Allow() {
			logger.Warn("API密钥限流触发",
				zap.String("api_key", apiKey),
				zap.String("path", c.Request.URL.Path),
			)
			c.JSON(http.StatusTooManyRequests, gin.H{
				"error":       "API密钥请求过于频繁",
				"retry_after": 60,
			})
			c.Abort()
			return
		}

		c.Next()
	}
}
