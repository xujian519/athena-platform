package health

import (
	"context"
	"fmt"
	"net/http"
	"sync"
	"time"
)

// HealthStatus 健康状态
type HealthStatus string

const (
	StatusUp      HealthStatus = "UP"
	StatusDown    HealthStatus = "DOWN"
	StatusDegraded HealthStatus = "DEGRADED"
)

// CheckResult 健康检查结果
type CheckResult struct {
	Name     string                 `json:"name"`
	Status   HealthStatus           `json:"status"`
	Message  string                 `json:"message,omitempty"`
	Duration time.Duration          `json:"duration_ms"`
	Details  map[string]interface{} `json:"details,omitempty"`
}

// HealthCheck 健康检查接口
type HealthCheck interface {
	// Name 返回检查名称
	Name() string
	// Check 执行检查
	Check(ctx context.Context) *CheckResult
}

// Checker 健康检查器
type Checker struct {
	checks  map[string]HealthCheck
	timeout time.Duration
	mu      sync.RWMutex
}

// NewChecker 创建健康检查器
func NewChecker() *Checker {
	return &Checker{
		checks:  make(map[string]HealthCheck),
		timeout: 10 * time.Second,
	}
}

// Register 注册健康检查
func (c *Checker) Register(check HealthCheck) {
	c.mu.Lock()
	defer c.mu.Unlock()
	c.checks[check.Name()] = check
}

// Unregister 注销健康检查
func (c *Checker) Unregister(name string) {
	c.mu.Lock()
	defer c.mu.Unlock()
	delete(c.checks, name)
}

// Check 执行所有健康检查
func (c *Checker) Check(ctx context.Context) map[string]*CheckResult {
	c.mu.RLock()
	checks := make(map[string]HealthCheck, len(c.checks))
	for name, check := range c.checks {
		checks[name] = check
	}
	c.mu.RUnlock()

	results := make(map[string]*CheckResult)
	var wg sync.WaitGroup
	var resultsMu sync.Mutex

	for name, check := range checks {
		wg.Add(1)
		go func(name string, check HealthCheck) {
			defer wg.Done()

			// 设置超时
			checkCtx, cancel := context.WithTimeout(ctx, c.timeout)
			defer cancel()

			start := time.Now()
			result := check.Check(checkCtx)
			result.Duration = time.Since(start)

			resultsMu.Lock()
			results[name] = result
			resultsMu.Unlock()
		}(name, check)
	}

	wg.Wait()
	return results
}

// GetOverallStatus 获取整体状态
func (c *Checker) GetOverallStatus(results map[string]*CheckResult) HealthStatus {
	hasDown := false
	hasDegraded := false

	for _, result := range results {
		switch result.Status {
		case StatusDown:
			hasDown = true
		case StatusDegraded:
			hasDegraded = true
		}
	}

	if hasDown {
		return StatusDown
	}
	if hasDegraded {
		return StatusDegraded
	}
	return StatusUp
}

// SetTimeout 设置检查超时
func (c *Checker) SetTimeout(timeout time.Duration) {
	c.mu.Lock()
	defer c.mu.Unlock()
	c.timeout = timeout
}

// ========== 内置健康检查 ==========

// HTTPCheck HTTP端点健康检查
type HTTPCheck struct {
	name     string
	url      string
	client   *http.Client
	expected int
}

// NewHTTPCheck 创建HTTP健康检查
func NewHTTPCheck(name, url string, expectedStatus int) *HTTPCheck {
	return &HTTPCheck{
		name:     name,
		url:      url,
		client:   &http.Client{Timeout: 5 * time.Second},
		expected: expectedStatus,
	}
}

// Name 返回检查名称
func (h *HTTPCheck) Name() string {
	return h.name
}

// Check 执行检查
func (h *HTTPCheck) Check(ctx context.Context) *CheckResult {
	start := time.Now()
	result := &CheckResult{
		Name:    h.name,
		Details: make(map[string]interface{}),
	}

	req, err := http.NewRequestWithContext(ctx, "GET", h.url, nil)
	if err != nil {
		result.Status = StatusDown
		result.Message = fmt.Sprintf("创建请求失败: %v", err)
		return result
	}

	resp, err := h.client.Do(req)
	if err != nil {
		result.Status = StatusDown
		result.Message = fmt.Sprintf("请求失败: %v", err)
		return result
	}
	defer resp.Body.Close()

	result.Details["status_code"] = resp.StatusCode
	result.Details["url"] = h.url

	if resp.StatusCode == h.expected {
		result.Status = StatusUp
		result.Message = "OK"
	} else {
		result.Status = StatusDown
		result.Message = fmt.Sprintf("期望状态码 %d, 得到 %d", h.expected, resp.StatusCode)
	}

	result.Duration = time.Since(start)
	return result
}

// TCPCheck TCP连接健康检查
type TCPCheck struct {
	name string
	host string
	port int
}

// NewTCPCheck 创建TCP健康检查
func NewTCPCheck(name string, host string, port int) *TCPCheck {
	return &TCPCheck{
		name: name,
		host: host,
		port: port,
	}
}

// Name 返回检查名称
func (c *TCPCheck) Name() string {
	return c.name
}

// Check 执行检查
func (c *TCPCheck) Check(ctx context.Context) *CheckResult {
	result := &CheckResult{
		Name:    c.name,
		Details: make(map[string]interface{}),
	}

	// TODO: 实现TCP连接检查
	// 使用 net.Dialer 的 DialContext 方法

	result.Status = StatusDown
	result.Message = "TCP检查未实现"
	result.Details["host"] = c.host
	result.Details["port"] = c.port

	return result
}

// CustomCheck 自定义函数健康检查
type CustomCheck struct {
	name string
	fn   func(ctx context.Context) *CheckResult
}

// NewCustomCheck 创建自定义健康检查
func NewCustomCheck(name string, fn func(ctx context.Context) *CheckResult) *CustomCheck {
	return &CustomCheck{
		name: name,
		fn:   fn,
	}
}

// Name 返回检查名称
func (c *CustomCheck) Name() string {
	return c.name
}

// Check 执行检查
func (c *CustomCheck) Check(ctx context.Context) *CheckResult {
	return c.fn(ctx)
}
