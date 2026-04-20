// Package ratelimit - 自适应限流器
// 从api-gateway项目迁移而来
package ratelimit

import (
	"context"
	"fmt"
	"sync"
	"time"

	"github.com/athena-workspace/gateway-unified/internal/logging"
)

// RateLimiter 限流器接口
type RateLimiter interface {
	Allow(ctx context.Context, key string) bool
	Wait(ctx context.Context, key string) error
	Limit(ctx context.Context, key string) RateLimitResult
	Reset(ctx context.Context, key string)
}

// RateLimitResult 限流结果
type RateLimitResult struct {
	Allowed    bool          `json:"allowed"`
	Limit      int64         `json:"limit"`
	Remaining  int64         `json:"remaining"`
	ResetTime  time.Time     `json:"reset_time"`
	RetryAfter time.Duration `json:"retry_after"`
}

// AdaptiveRateLimiter 自适应限流器
type AdaptiveRateLimiter struct {
	limiters map[string]*TokenBucket
	mutex    sync.RWMutex
	config   *RateLimiterConfig
	stats    *RateLimiterStats
}

// RateLimiterConfig 限流器配置
type RateLimiterConfig struct {
	DefaultLimit     int64         `json:"default_limit"`
	DefaultBurst     int64         `json:"default_burst"`
	Window           time.Duration `json:"window"`
	AdaptiveMode     bool          `json:"adaptive_mode"`
	MinLimit         int64         `json:"min_limit"`
	MaxLimit         int64         `json:"max_limit"`
	AdjustmentFactor float64       `json:"adjustment_factor"`
	StatsWindow      time.Duration `json:"stats_window"`
}

// RateLimiterStats 限流器统计
type RateLimiterStats struct {
	TotalRequests    int64     `json:"total_requests"`
	AllowedRequests  int64     `json:"allowed_requests"`
	RejectedRequests int64     `json:"rejected_requests"`
	CurrentRate      float64   `json:"current_rate"`
	ErrorRate        float64   `json:"error_rate"`
	Adjustments      int64     `json:"adjustments"`
	LastAdjustment   time.Time `json:"last_adjustment"`
	mutex            sync.RWMutex
}

// TokenBucket 令牌桶
type TokenBucket struct {
	capacity   int64
	tokens     int64
	refillRate int64
	lastRefill time.Time
	mutex      sync.Mutex
	stats      *BucketStats
}

// BucketStats 桶统计
type BucketStats struct {
	refillCount int64
	emptyCount  int64
	lastRefill  time.Time
}

// NewAdaptiveRateLimiter 创建自适应限流器
func NewAdaptiveRateLimiter(defaultLimit, defaultBurst int64) (*AdaptiveRateLimiter, error) {
	config := &RateLimiterConfig{
		DefaultLimit:     defaultLimit,
		DefaultBurst:     defaultBurst,
		Window:           time.Minute,
		AdaptiveMode:     true,
		MinLimit:         10,
		MaxLimit:         10000,
		AdjustmentFactor: 0.1,
		StatsWindow:      time.Minute * 5,
	}

	limiter := &AdaptiveRateLimiter{
		limiters: make(map[string]*TokenBucket),
		config:   config,
		stats:    &RateLimiterStats{},
	}

	// 启动自适应调整
	if config.AdaptiveMode {
		go limiter.adaptiveAdjustment()
	}

	// 启动统计清理
	go limiter.statsCleanup()

	logging.LogInfo("自适应限流器初始化成功",
		logging.Int64("default_limit", config.DefaultLimit),
		logging.Bool("adaptive_mode", config.AdaptiveMode),
	)

	return limiter, nil
}

// Allow 检查是否允许请求
func (r *AdaptiveRateLimiter) Allow(ctx context.Context, key string) bool {
	bucket := r.getOrCreateBucket(key)

	r.mutex.RLock()
	currentLimit := bucket.capacity
	r.mutex.RUnlock()

	bucket.mutex.Lock()
	defer bucket.mutex.Unlock()

	// 补充令牌
	r.refillTokens(bucket)

	// 检查令牌
	if bucket.tokens >= 1 {
		bucket.tokens--
		r.recordRequest(true, currentLimit)
		return true
	}

	r.recordRequest(false, currentLimit)
	bucket.stats.emptyCount++
	return false
}

// Wait 等待直到可以处理请求
func (r *AdaptiveRateLimiter) Wait(ctx context.Context, key string) error {
	for {
		if r.Allow(ctx, key) {
			return nil
		}

		bucket := r.getBucket(key)
		if bucket == nil {
			return fmt.Errorf("令牌桶不存在")
		}

		// 计算等待时间
		waitTime := r.calculateWaitTime(bucket)

		select {
		case <-ctx.Done():
			return ctx.Err()
		case <-time.After(waitTime):
			continue
		}
	}
}

// Limit 获取限流信息
func (r *AdaptiveRateLimiter) Limit(ctx context.Context, key string) RateLimitResult {
	bucket := r.getBucket(key)
	if bucket == nil {
		return RateLimitResult{
			Allowed:   true,
			Limit:     r.config.DefaultLimit,
			Remaining: r.config.DefaultLimit - 1,
			ResetTime: time.Now().Add(r.config.Window),
		}
	}

	bucket.mutex.Lock()
	defer bucket.mutex.Unlock()

	r.refillTokens(bucket)

	allowed := bucket.tokens >= 1
	if allowed {
		bucket.tokens--
	}

	return RateLimitResult{
		Allowed:    allowed,
		Limit:      bucket.capacity,
		Remaining:  bucket.tokens,
		ResetTime:  bucket.lastRefill.Add(r.config.Window),
		RetryAfter: r.calculateWaitTime(bucket),
	}
}

// Reset 重置限流器
func (r *AdaptiveRateLimiter) Reset(ctx context.Context, key string) {
	r.mutex.Lock()
	defer r.mutex.Unlock()

	delete(r.limiters, key)
}

// getOrCreateBucket 获取或创建令牌桶
func (r *AdaptiveRateLimiter) getOrCreateBucket(key string) *TokenBucket {
	r.mutex.RLock()
	bucket, exists := r.limiters[key]
	r.mutex.RUnlock()

	if exists {
		return bucket
	}

	r.mutex.Lock()
	defer r.mutex.Unlock()

	// 双重检查
	if bucket, exists := r.limiters[key]; exists {
		return bucket
	}

	bucket = &TokenBucket{
		capacity:   r.config.DefaultLimit,
		tokens:     r.config.DefaultBurst,
		refillRate: r.config.DefaultLimit,
		lastRefill: time.Now(),
		stats:      &BucketStats{},
	}

	r.limiters[key] = bucket
	return bucket
}

// getBucket 获取令牌桶
func (r *AdaptiveRateLimiter) getBucket(key string) *TokenBucket {
	r.mutex.RLock()
	defer r.mutex.RUnlock()

	return r.limiters[key]
}

// refillTokens 补充令牌
func (r *AdaptiveRateLimiter) refillTokens(bucket *TokenBucket) {
	now := time.Now()
	elapsed := now.Sub(bucket.lastRefill)

	if elapsed > 0 {
		tokensToAdd := int64(float64(elapsed) * float64(bucket.refillRate) / float64(r.config.Window))
		if tokensToAdd > 0 {
			bucket.tokens = min(bucket.capacity, bucket.tokens+tokensToAdd)
			bucket.lastRefill = now
			bucket.stats.refillCount++
			bucket.stats.lastRefill = now
		}
	}
}

// calculateWaitTime 计算等待时间
func (r *AdaptiveRateLimiter) calculateWaitTime(bucket *TokenBucket) time.Duration {
	if bucket.refillRate <= 0 {
		return r.config.Window
	}

	neededTokens := 1 - bucket.tokens
	if neededTokens <= 0 {
		return 0
	}

	waitTime := time.Duration(float64(neededTokens)*float64(r.config.Window)/float64(bucket.refillRate)) * time.Second
	if waitTime > time.Duration(r.config.Window)*time.Second {
		return time.Duration(r.config.Window) * time.Second
	}
	return waitTime
}

// recordRequest 记录请求
func (r *AdaptiveRateLimiter) recordRequest(allowed bool, limit int64) {
	r.stats.mutex.Lock()
	defer r.stats.mutex.Unlock()

	r.stats.TotalRequests++

	if allowed {
		r.stats.AllowedRequests++
	} else {
		r.stats.RejectedRequests++
	}

	if r.stats.TotalRequests > 0 {
		r.stats.CurrentRate = float64(r.stats.AllowedRequests) / float64(r.stats.TotalRequests)
	}
}

// adaptiveAdjustment 自适应调整
func (r *AdaptiveRateLimiter) adaptiveAdjustment() {
	ticker := time.NewTicker(r.config.StatsWindow)
	defer ticker.Stop()

	for range ticker.C {
		r.adjustLimits()
	}
}

// adjustLimits 调整限制
func (r *AdaptiveRateLimiter) adjustLimits() {
	r.stats.mutex.RLock()
	currentRate := r.stats.CurrentRate
	rejectionRate := float64(r.stats.RejectedRequests) / float64(r.stats.TotalRequests)
	r.stats.mutex.RUnlock()

	r.mutex.Lock()
	defer r.mutex.Unlock()

	adjustmentMade := false

	for key, bucket := range r.limiters {
		oldLimit := bucket.capacity
		newLimit := oldLimit

		// 根据拒绝率调整
		if rejectionRate > 0.1 { // 拒绝率超过10%，降低限制
			newLimit = max(r.config.MinLimit, int64(float64(oldLimit)*(1-r.config.AdjustmentFactor)))
		} else if rejectionRate < 0.01 && currentRate > 0.8 { // 拒绝率低且使用率高，提高限制
			newLimit = min(r.config.MaxLimit, int64(float64(oldLimit)*(1+r.config.AdjustmentFactor)))
		}

		// 根据错误率调整
		bucket.mutex.Lock()
		emptyRate := float64(bucket.stats.emptyCount) / float64(maxInt64(1, bucket.stats.refillCount))
		bucket.mutex.Unlock()

		if emptyRate > 0.5 { // 桶经常为空，需要增加容量
			newLimit = min(r.config.MaxLimit, newLimit+1)
		} else if emptyRate < 0.1 { // 桶很少为空，可以减少容量
			newLimit = max(r.config.MinLimit, newLimit-1)
		}

		if newLimit != oldLimit {
			bucket.capacity = newLimit
			bucket.refillRate = newLimit
			adjustmentMade = true

			logging.LogInfo("自适应调整限流参数",
				logging.String("key", key),
				logging.Int64("old_limit", oldLimit),
				logging.Int64("new_limit", newLimit),
				logging.Float64("rejection_rate", rejectionRate),
				logging.Float64("empty_rate", emptyRate),
			)
		}
	}

	if adjustmentMade {
		r.stats.mutex.Lock()
		r.stats.Adjustments++
		r.stats.LastAdjustment = time.Now()
		r.stats.mutex.Unlock()
	}
}

func (r *AdaptiveRateLimiter) statsCleanup() {
	ticker := time.NewTicker(time.Hour)
	defer ticker.Stop()

	for range ticker.C {
		r.mutex.Lock()
		for key, bucket := range r.limiters {
			bucket.mutex.Lock()

			bucket.stats.refillCount = 0
			bucket.stats.emptyCount = 0

			bucket.mutex.Unlock()

			if time.Since(bucket.lastRefill) > r.config.StatsWindow*10 {
				delete(r.limiters, key)
			}
		}
		r.mutex.Unlock()
	}
}

// Stats 获取统计信息
func (r *AdaptiveRateLimiter) Stats() map[string]interface{} {
	r.stats.mutex.RLock()
	stats := map[string]interface{}{
		"total_requests":    r.stats.TotalRequests,
		"allowed_requests":  r.stats.AllowedRequests,
		"rejected_requests": r.stats.RejectedRequests,
		"current_rate":      r.stats.CurrentRate,
		"adjustments":       r.stats.Adjustments,
		"last_adjustment":   r.stats.LastAdjustment,
		"bucket_count":      len(r.limiters),
	}
	r.stats.mutex.RUnlock()

	return stats
}

// 辅助函数
func min(a, b int64) int64 {
	if a < b {
		return a
	}
	return b
}

func max(a, b int64) int64 {
	if a > b {
		return a
	}
	return b
}

func maxInt64(a, b int64) int64 {
	if a > b {
		return a
	}
	return b
}
