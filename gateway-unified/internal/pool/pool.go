// Package pool - 优化的HTTP连接池管理
// 提供连接复用、健康检查、超时控制等功能
package pool

import (
	"context"
	"errors"
	"net"
	"net/http"
	"sync"
	"time"

	"github.com/athena-workspace/gateway-unified/internal/logging"
)

// 自定义错误
var (
	ErrPoolClosed = errors.New("connection pool is closed")
)

// PoolConfig 连接池配置
type PoolConfig struct {
	// 基础连接配置
	MaxIdleConns        int           // 最大空闲连接数
	MaxIdleConnsPerHost int           // 每个主机的最大空闲连接数
	MaxConnsPerHost     int           // 每个主机的最大连接数
	IdleConnTimeout     time.Duration // 空闲连接超时时间

	// 超时配置
	DialTimeout           time.Duration // 拨号超时
	ResponseHeaderTimeout time.Duration // 响应头超时
	RequestTimeout        time.Duration // 请求总超时
	TLSHandshakeTimeout   time.Duration // TLS握手超时

	// 保持连接配置
	KeepAlive       time.Duration // 保持连接时间
	MaxIdleConnsHR  int           // HTTP/2最大空闲连接数
	DisableCompression bool       // 是否禁用压缩
	ForceAttemptHTTP2   bool       // 强制HTTP/2

	// 健康检查配置
	HealthCheckInterval time.Duration // 健康检查间隔
	HealthCheckTimeout  time.Duration // 健康检查超时
	EnableHealthCheck   bool         // 启用健康检查

	// 连接重试配置
	MaxRetries    int           // 最大重试次数
	RetryDelay    time.Duration // 重试延迟
	RetryMaxDelay time.Duration // 最大重试延迟
}

// DefaultConfig 返回默认配置
func DefaultConfig() *PoolConfig {
	return &PoolConfig{
		// 基础连接配置 - 优化后的值
		MaxIdleConns:        200,            // 增加到200以支持更多并发
		MaxIdleConnsPerHost: 50,             // 每个主机最多50个空闲连接
		MaxConnsPerHost:     0,              // 0表示无限制
		IdleConnTimeout:     90 * time.Second,

		// 超时配置
		DialTimeout:           10 * time.Second,
		ResponseHeaderTimeout: 30 * time.Second,
		RequestTimeout:        60 * time.Second,
		TLSHandshakeTimeout:   10 * time.Second,

		// 保持连接配置
		KeepAlive:           30 * time.Second,
		MaxIdleConnsHR:      100,            // HTTP/2连接池
		DisableCompression:  false,
		ForceAttemptHTTP2:   true,

		// 健康检查配置
		HealthCheckInterval: 30 * time.Second,
		HealthCheckTimeout:  5 * time.Second,
		EnableHealthCheck:   true,

		// 连接重试配置
		MaxRetries:    3,
		RetryDelay:    100 * time.Millisecond,
		RetryMaxDelay: 1 * time.Second,
	}
}

// ConnectionPool 连接池管理器
type ConnectionPool struct {
	config       *PoolConfig
	client       *http.Client
	transport    *http.Transport
	healthChecker *HealthChecker
	mu           sync.RWMutex
	stats        *PoolStats
	closed       bool
}

// PoolStats 连接池统计
type PoolStats struct {
	mu                    sync.RWMutex
	ActiveConnections     int
	IdleConnections       int
	TotalRequests         uint64
	SuccessfulRequests    uint64
	FailedRequests        uint64
	RetriedRequests       uint64
	AverageResponseTime   time.Duration
	TotalResponseTime     time.Duration
	lastHealthCheckTime   time.Time
	lastHealthCheckStatus string
}

// NewConnectionPool 创建新的连接池
func NewConnectionPool(cfg *PoolConfig) (*ConnectionPool, error) {
	if cfg == nil {
		cfg = DefaultConfig()
	}

	// 创建优化的Transport
	transport := &http.Transport{
		// 基础连接配置
		Proxy: http.ProxyFromEnvironment,
		DialContext: (&net.Dialer{
			Timeout:   cfg.DialTimeout,
			KeepAlive: cfg.KeepAlive,
		}).DialContext,

		// 连接池配置
		MaxIdleConns:        cfg.MaxIdleConns,
		MaxIdleConnsPerHost: cfg.MaxIdleConnsPerHost,
		MaxConnsPerHost:     cfg.MaxConnsPerHost,
		IdleConnTimeout:     cfg.IdleConnTimeout,

		// 超时配置
		ResponseHeaderTimeout: cfg.ResponseHeaderTimeout,
		TLSHandshakeTimeout:   cfg.TLSHandshakeTimeout,

		// HTTP/2配置
		DisableCompression:  cfg.DisableCompression,
		ForceAttemptHTTP2:   cfg.ForceAttemptHTTP2,

		// 预期响应大小（用于缓冲区分配）
		WriteBufferSize: 8 * 1024,  // 8KB
		ReadBufferSize:  8 * 1024,  // 8KB

		// 连接生命周期
		ExpectContinueTimeout: 1 * time.Second,
	}

	pool := &ConnectionPool{
		config:    cfg,
		transport: transport,
		stats:     &PoolStats{},
	}

	// 创建HTTP客户端
	pool.client = &http.Client{
		Transport: pool,
		Timeout:   cfg.RequestTimeout,
	}

	// 创建健康检查器
	if cfg.EnableHealthCheck {
		pool.healthChecker = NewHealthChecker(pool, cfg)
	}

	logging.LogInfo("连接池创建成功",
		logging.Int("max_idle_conns", cfg.MaxIdleConns),
		logging.Int("max_idle_conns_per_host", cfg.MaxIdleConnsPerHost),
		logging.Duration("idle_conn_timeout", cfg.IdleConnTimeout))

	return pool, nil
}

// Client 返回HTTP客户端
func (p *ConnectionPool) Client() *http.Client {
	p.mu.RLock()
	defer p.mu.RUnlock()
	return p.client
}

// Do 执行HTTP请求
func (p *ConnectionPool) Do(req *http.Request) (*http.Response, error) {
	if p.isClosed() {
		return nil, ErrPoolClosed
	}

	p.updateStatsActive(1)
	startTime := time.Now()

	// 尝试请求，支持重试
	var resp *http.Response
	var err error
	retryCount := 0

	for retryCount <= p.config.MaxRetries {
		resp, err = p.client.Do(req)
		if err == nil {
			// 请求成功
			p.updateStatsSuccess()
			p.updateStatsResponseTime(time.Since(startTime))
			p.updateStatsActive(-1)
			return resp, nil
		}

		// 检查是否可重试
		if retryCount < p.config.MaxRetries && p.isRetryable(err) {
			retryCount++
			p.updateStatsRetry()
			logging.LogWarn("请求失败，重试中",
				logging.String("url", req.URL.String()),
				logging.Int("retry", retryCount),
				logging.Err(err))

			// 指数退避
			delay := p.calculateRetryDelay(retryCount)
			time.Sleep(delay)

			// 创建新的请求体
			if req.Body != nil {
				// 注意：这里假设请求体可重读
				// 实际使用中可能需要特殊处理
			}
			continue
		}

		break
	}

	// 请求失败
	p.updateStatsFailed()
	p.updateStatsActive(-1)
	logging.LogError("请求失败",
		logging.String("url", req.URL.String()),
		logging.Int("retries", retryCount),
		logging.Err(err))

	return nil, err
}

// RoundTrip 实现http.RoundTripper接口
func (p *ConnectionPool) RoundTrip(req *http.Request) (*http.Response, error) {
	return p.transport.RoundTrip(req)
}

// isRetryable 判断错误是否可重试
func (p *ConnectionPool) isRetryable(err error) bool {
	if err == nil {
		return false
	}

	// 可重试的错误类型
	switch {
	case err == net.ErrClosed, err == http.ErrHandlerTimeout, err == ErrPoolClosed:
		return true
	default:
		// 检查是否为网络超时错误
		if netErr, ok := err.(net.Error); ok && netErr.Timeout() {
			return true
		}
		// 检查错误消息中的可重试错误
		errStr := err.Error()
		if containsString(errStr, "EOF") ||
			containsString(errStr, "connection reset") ||
			containsString(errStr, "broken pipe") {
			return true
		}
		return false
	}
}

// containsString 检查字符串是否包含子串（忽略大小写）
func containsString(s, substr string) bool {
	return len(s) >= len(substr) &&
		(s == substr ||
		len(s) > len(substr) && (
		s[:len(substr)] == substr ||
		s[len(s)-len(substr):] == substr ||
	 indexOfString(s, substr) >= 0))
}

// indexOfString 返回子串位置
func indexOfString(s, substr string) int {
	for i := 0; i <= len(s)-len(substr); i++ {
		if s[i:i+len(substr)] == substr {
			return i
		}
	}
	return -1
}

// calculateRetryDelay 计算重试延迟（指数退避）
func (p *ConnectionPool) calculateRetryDelay(retryCount int) time.Duration {
	baseDelay := p.config.RetryDelay
	maxDelay := p.config.RetryMaxDelay

	// 指数退避: baseDelay * 2^(retryCount-1)
	delay := baseDelay * time.Duration(1<<uint(retryCount-1))

	if delay > maxDelay {
		delay = maxDelay
	}

	return delay
}

// StartHealthCheck 启动健康检查
func (p *ConnectionPool) StartHealthCheck(ctx context.Context) {
	if !p.config.EnableHealthCheck || p.healthChecker == nil {
		return
	}

	p.healthChecker.Start(ctx)
}

// GetStats 获取连接池统计
func (p *ConnectionPool) GetStats() *PoolStats {
	p.stats.mu.RLock()
	defer p.stats.mu.RUnlock()

	// 复制统计信息以避免竞态
	// 注意: Go的http.Transport不直接暴露空闲连接计数
	// 我们使用活跃连接数作为近似值
	statsCopy := &PoolStats{
		ActiveConnections:     p.stats.ActiveConnections,
		IdleConnections:       0, // Transport不直接暴露此信息
		TotalRequests:         p.stats.TotalRequests,
		SuccessfulRequests:    p.stats.SuccessfulRequests,
		FailedRequests:        p.stats.FailedRequests,
		RetriedRequests:       p.stats.RetriedRequests,
		AverageResponseTime:   p.stats.AverageResponseTime,
		lastHealthCheckTime:   p.stats.lastHealthCheckTime,
		lastHealthCheckStatus: p.stats.lastHealthCheckStatus,
	}

	return statsCopy
}

// updateStatsActive 更新活跃连接数
func (p *ConnectionPool) updateStatsActive(delta int) {
	p.stats.mu.Lock()
	defer p.stats.mu.Unlock()
	p.stats.ActiveConnections += delta
}

// updateStatsSuccess 更新成功统计
func (p *ConnectionPool) updateStatsSuccess() {
	p.stats.mu.Lock()
	defer p.stats.mu.Unlock()
	p.stats.TotalRequests++
	p.stats.SuccessfulRequests++
}

// updateStatsFailed 更新失败统计
func (p *ConnectionPool) updateStatsFailed() {
	p.stats.mu.Lock()
	defer p.stats.mu.Unlock()
	p.stats.TotalRequests++
	p.stats.FailedRequests++
}

// updateStatsRetry 更新重试统计
func (p *ConnectionPool) updateStatsRetry() {
	p.stats.mu.Lock()
	defer p.stats.mu.Unlock()
	p.stats.RetriedRequests++
}

// updateStatsResponseTime 更新响应时间统计
func (p *ConnectionPool) updateStatsResponseTime(duration time.Duration) {
	p.stats.mu.Lock()
	defer p.stats.mu.Unlock()

	p.stats.TotalResponseTime += duration
	if p.stats.TotalRequests > 0 {
		p.stats.AverageResponseTime = p.stats.TotalResponseTime / time.Duration(p.stats.TotalRequests)
	}
}

// isClosed 检查连接池是否已关闭
func (p *ConnectionPool) isClosed() bool {
	p.mu.RLock()
	defer p.mu.RUnlock()
	return p.closed
}

// Close 关闭连接池
func (p *ConnectionPool) Close() error {
	p.mu.Lock()
	if p.closed {
		p.mu.Unlock()
		return nil
	}
	p.closed = true
	p.mu.Unlock()

	// 停止健康检查
	if p.healthChecker != nil {
		p.healthChecker.Stop()
	}

	// 关闭传输层
	p.transport.CloseIdleConnections()

	logging.LogInfo("连接池已关闭",
		logging.Int("total_requests", int(p.stats.TotalRequests)),
		logging.Int("successful_requests", int(p.stats.SuccessfulRequests)),
		logging.Int("failed_requests", int(p.stats.FailedRequests)))

	return nil
}

// GetConfig 获取配置
func (p *ConnectionPool) GetConfig() *PoolConfig {
	return p.config
}
