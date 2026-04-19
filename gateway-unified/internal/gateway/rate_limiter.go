package gateway

import (
	"context"
	"fmt"
	"sync"
	"time"
)

// ==================== 滑动窗口限流器 ====================

// SlidingWindowLimiter 滑动窗口限流器
type SlidingWindowLimiter struct {
	windows map[string]*Window // 按key分组的窗口
	mu      sync.RWMutex
}

// Window 滑动窗口
type Window struct {
	requests []time.Time // 请求时间戳队列
	limit    int         // 限流阈值
	window   time.Duration // 窗口大小
	mu       sync.Mutex
}

// NewSlidingWindowLimiter 创建滑动窗口限流器
func NewSlidingWindowLimiter() *SlidingWindowLimiter {
	return &SlidingWindowLimiter{
		windows: make(map[string]*Window),
	}
}

// Allow 检查是否允许请求
func (l *SlidingWindowLimiter) Allow(key string, limit int, window time.Duration) bool {
	l.mu.Lock()
	w, exists := l.windows[key]
	if !exists {
		w = &Window{
			requests: make([]time.Time, 0, limit*2),
			limit:    limit,
			window:   window,
		}
		l.windows[key] = w
	}
	l.mu.Unlock()

	return w.Allow()
}

// Allow 检查窗口内是否允许请求
func (w *Window) Allow() bool {
	w.mu.Lock()
	defer w.mu.Unlock()

	now := time.Now()
	// 清理过期请求
	cutoff := now.Add(-w.window)
	validIdx := 0
	for i, t := range w.requests {
		if t.After(cutoff) {
			validIdx = i
			break
		}
	}
	if validIdx > 0 {
		w.requests = w.requests[validIdx:]
	}

	// 检查是否超限
	if len(w.requests) >= w.limit {
		return false
	}

	// 记录当前请求
	w.requests = append(w.requests, now)
	return true
}

// ==================== 限流插件（使用滑动窗口） ====================

// EnhancedRateLimitPlugin 增强的限流插件（使用滑动窗口）
type EnhancedRateLimitPlugin struct {
	*BasePlugin
	limiter    *SlidingWindowLimiter
	maxRequest int
	window     time.Duration
}

// NewEnhancedRateLimitPlugin 创建增强的限流插件
func NewEnhancedRateLimitPlugin(maxRequests int, window time.Duration) *EnhancedRateLimitPlugin {
	return &EnhancedRateLimitPlugin{
		BasePlugin: NewBasePlugin("enhanced_rate_limit", PhaseBeforeRequest, 90),
		limiter:    NewSlidingWindowLimiter(),
		maxRequest: maxRequests,
		window:     window,
	}
}

// Init 初始化限流插件
func (p *EnhancedRateLimitPlugin) Init(config map[string]interface{}) error {
	if err := p.BasePlugin.Init(config); err != nil {
		return err
	}

	if maxRequests, ok := config["max_requests"].(int); ok {
		p.maxRequest = maxRequests
	}

	// 默认窗口大小为1分钟
	if windowSeconds, ok := config["window_seconds"].(int); ok {
		p.window = time.Duration(windowSeconds) * time.Second
	} else {
		p.window = 1 * time.Minute
	}

	return nil
}

// Execute 执行限流检查
func (p *EnhancedRateLimitPlugin) Execute(ctx context.Context, pluginCtx *PluginContext) error {
	// 构建限流key（可按IP/用户/路由分组）
	key := "default"
	if pluginCtx.Metadata != nil {
		// 优先使用用户ID
		if userID, ok := pluginCtx.Metadata["user_id"].(string); ok && userID != "" {
			key = "user:" + userID
		} else if ip, ok := pluginCtx.Metadata["client_ip"].(string); ok {
			key = "ip:" + ip
		}
	}

	// 检查是否允许请求
	allowed := p.limiter.Allow(key, p.maxRequest, p.window)
	if !allowed {
		return fmt.Errorf("请求过于频繁，请稍后再试（限制: %d次/%s）", p.maxRequest, p.window)
	}

	return nil
}

// Shutdown 关闭限流插件
func (p *EnhancedRateLimitPlugin) Shutdown() error {
	// 清理所有窗口
	p.limiter.windows = make(map[string]*Window)
	return nil
}

// GetStats 获取限流统计信息
func (p *EnhancedRateLimitPlugin) GetStats() map[string]interface{} {
	p.limiter.mu.RLock()
	defer p.limiter.mu.RUnlock()

	stats := make(map[string]interface{})
	stats["total_keys"] = len(p.limiter.windows)
	stats["max_requests"] = p.maxRequest
	stats["window_duration"] = p.window.String()

	// 获取每个key的当前请求数
	keyStats := make(map[string]int)
	for key, window := range p.limiter.windows {
		window.mu.Lock()
		keyStats[key] = len(window.requests)
		window.mu.Unlock()
	}
	stats["keys"] = keyStats

	return stats
}
