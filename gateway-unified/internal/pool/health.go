// Package pool - 连接池健康检查
package pool

import (
	"context"
	"fmt"
	"net/http"
	"sync"
	"time"

	"github.com/athena-workspace/gateway-unified/internal/logging"
)

// HealthChecker 连接池健康检查器
type HealthChecker struct {
	pool   *ConnectionPool
	config *PoolConfig

	ctx       context.Context
	cancel    context.CancelFunc
	wg        sync.WaitGroup
	running   bool
	mu        sync.RWMutex

	// 健康检查目标
	checkTargets []HealthCheckTarget
}

// HealthCheckTarget 健康检查目标
type HealthCheckTarget struct {
	Name string
	URL  string
	// 自定义健康检查逻辑
	CheckFunc func(ctx context.Context) error
}

// HealthStatus 健康状态
type HealthStatus struct {
	IsHealthy   bool              `json:"is_healthy"`
	Timestamp   time.Time         `json:"timestamp"`
	CheckCount  int               `json:"check_count"`
	Targets     map[string]TargetStatus `json:"targets"`
}

// TargetStatus 单个目标的状态
type TargetStatus struct {
	IsHealthy     bool      `json:"is_healthy"`
	LastCheckTime time.Time `json:"last_check_time"`
	Error         string    `json:"error,omitempty"`
	ResponseTime  time.Duration `json:"response_time"`
}

// NewHealthChecker 创建健康检查器
func NewHealthChecker(pool *ConnectionPool, config *PoolConfig) *HealthChecker {
	ctx, cancel := context.WithCancel(context.Background())

	return &HealthChecker{
		pool:   pool,
		config: config,
		ctx:    ctx,
		cancel: cancel,
		checkTargets: make([]HealthCheckTarget, 0),
	}
}

// AddTarget 添加健康检查目标
func (h *HealthChecker) AddTarget(name, url string) {
	h.mu.Lock()
	defer h.mu.Unlock()

	h.checkTargets = append(h.checkTargets, HealthCheckTarget{
		Name: name,
		URL:  url,
	})
}

// AddTargetWithFunc 添加带自定义检查函数的目标
func (h *HealthChecker) AddTargetWithFunc(name string, checkFunc func(ctx context.Context) error) {
	h.mu.Lock()
	defer h.mu.Unlock()

	h.checkTargets = append(h.checkTargets, HealthCheckTarget{
		Name:     name,
		CheckFunc: checkFunc,
	})
}

// RemoveTarget 移除健康检查目标
func (h *HealthChecker) RemoveTarget(name string) {
	h.mu.Lock()
	defer h.mu.Unlock()

	newTargets := make([]HealthCheckTarget, 0, len(h.checkTargets))
	for _, target := range h.checkTargets {
		if target.Name != name {
			newTargets = append(newTargets, target)
		}
	}
	h.checkTargets = newTargets
}

// Start 启动健康检查
func (h *HealthChecker) Start(ctx context.Context) {
	h.mu.Lock()
	if h.running {
		h.mu.Unlock()
		return
	}
	h.running = true
	h.mu.Unlock()

	logging.LogInfo("启动连接池健康检查",
		logging.Duration("interval", h.config.HealthCheckInterval))

	// 启动健康检查循环
	h.wg.Add(1)
	go h.healthCheckLoop()

	// 启动连接池统计更新
	h.wg.Add(1)
	go h.updatePoolStats()
}

// Stop 停止健康检查
func (h *HealthChecker) Stop() {
	h.mu.Lock()
	if !h.running {
		h.mu.Unlock()
		return
	}
	h.running = false
	h.mu.Unlock()

	h.cancel()
	h.wg.Wait()

	logging.LogInfo("连接池健康检查已停止")
}

// healthCheckLoop 健康检查循环
func (h *HealthChecker) healthCheckLoop() {
	defer h.wg.Done()

	ticker := time.NewTicker(h.config.HealthCheckInterval)
	defer ticker.Stop()

	// 立即执行一次检查
	h.performHealthCheck()

	for {
		select {
		case <-h.ctx.Done():
			return
		case <-ticker.C:
			h.performHealthCheck()
		}
	}
}

// performHealthCheck 执行健康检查
func (h *HealthChecker) performHealthCheck() {
	h.mu.RLock()
	targets := make([]HealthCheckTarget, len(h.checkTargets))
	copy(targets, h.checkTargets)
	h.mu.RUnlock()

	status := &HealthStatus{
		Timestamp:   time.Now(),
		Targets:     make(map[string]TargetStatus),
	}

	allHealthy := true
	for _, target := range targets {
		targetStatus := h.checkTarget(target)
		status.Targets[target.Name] = targetStatus

		if !targetStatus.IsHealthy {
			allHealthy = false
		}
	}

	status.IsHealthy = allHealthy

	// 更新连接池统计
	h.pool.stats.mu.Lock()
	h.pool.stats.lastHealthCheckTime = status.Timestamp
	if allHealthy {
		h.pool.stats.lastHealthCheckStatus = "healthy"
	} else {
		h.pool.stats.lastHealthCheckStatus = "unhealthy"
	}
	h.pool.stats.mu.Unlock()

	if !allHealthy {
		logging.LogWarn("连接池健康检查发现问题",
			logging.Int("unhealthy_targets", len(status.Targets)))
	}
}

// checkTarget 检查单个目标
func (h *HealthChecker) checkTarget(target HealthCheckTarget) TargetStatus {
	status := TargetStatus{
		LastCheckTime: time.Now(),
	}

	ctx, cancel := context.WithTimeout(h.ctx, h.config.HealthCheckTimeout)
	defer cancel()

	startTime := time.Now()

	if target.CheckFunc != nil {
		// 使用自定义检查函数
		err := target.CheckFunc(ctx)
		status.ResponseTime = time.Since(startTime)
		status.IsHealthy = err == nil
		if err != nil {
			status.Error = err.Error()
		}
	} else if target.URL != "" {
		// 使用默认HTTP检查
		err := h.checkHTTP(ctx, target.URL)
		status.ResponseTime = time.Since(startTime)
		status.IsHealthy = err == nil
		if err != nil {
			status.Error = err.Error()
		}
	} else {
		status.IsHealthy = false
		status.Error = "no check method configured"
	}

	return status
}

// checkHTTP 执行HTTP健康检查
func (h *HealthChecker) checkHTTP(ctx context.Context, url string) error {
	req, err := http.NewRequestWithContext(ctx, http.MethodGet, url, nil)
	if err != nil {
		return fmt.Errorf("创建请求失败: %w", err)
	}

	resp, err := h.pool.client.Do(req)
	if err != nil {
		return fmt.Errorf("请求失败: %w", err)
	}
	defer resp.Body.Close()

	// 检查状态码
	if resp.StatusCode < 200 || resp.StatusCode >= 300 {
		return fmt.Errorf("不健康的状态码: %d", resp.StatusCode)
	}

	return nil
}

// updatePoolStats 定期更新连接池统计
func (h *HealthChecker) updatePoolStats() {
	defer h.wg.Done()

	ticker := time.NewTicker(10 * time.Second)
	defer ticker.Stop()

	for {
		select {
		case <-h.ctx.Done():
			return
		case <-ticker.C:
			h.collectPoolStats()
		}
	}
}

// collectPoolStats 收集连接池统计信息
func (h *HealthChecker) collectPoolStats() {
	stats := h.pool.GetStats()

	logging.LogDebug("连接池统计",
		logging.Int("active_connections", stats.ActiveConnections),
		logging.Int("idle_connections", stats.IdleConnections),
		logging.Uint64("total_requests", stats.TotalRequests),
		logging.Uint64("successful_requests", stats.SuccessfulRequests),
		logging.Uint64("failed_requests", stats.FailedRequests),
		logging.Duration("avg_response_time", stats.AverageResponseTime))
}

// GetHealthStatus 获取健康状态
func (h *HealthChecker) GetHealthStatus() HealthStatus {
	h.pool.stats.mu.RLock()
	defer h.pool.stats.mu.RUnlock()

	return HealthStatus{
		IsHealthy:   h.pool.stats.lastHealthCheckStatus == "healthy",
		Timestamp:   h.pool.stats.lastHealthCheckTime,
		CheckCount:  int(h.pool.stats.TotalRequests),
		Targets:     make(map[string]TargetStatus),
	}
}
