// Package discovery - 健康检查器
// 实现服务实例的HTTP健康检查
package discovery

import (
	"fmt"
	"net/http"
	"time"
)

// HealthChecker 健康检查器
// 通过HTTP请求检查服务实例的健康状态
type HealthChecker struct {
	timeout   time.Duration
	userAgent string
}

// NewHealthChecker 创建健康检查器
func NewHealthChecker(config *ServiceDiscoveryConfig) *HealthChecker {
	return &HealthChecker{
		timeout:   5 * time.Second,
		userAgent: "Athena-Gateway-HealthCheck/1.0",
	}
}

// Check 检查服务健康状态
// 向服务的健康检查端点发送GET请求，根据响应判断服务是否健康
func (h *HealthChecker) Check(instance *ServiceInstance) bool {
	// 构造健康检查URL
	// 默认使用 /health 端点
	healthPath := "/health"

	// 如果元数据中有自定义健康检查端点，优先使用
	if healthEndpoint, ok := instance.Metadata["health_endpoint"].(string); ok && healthEndpoint != "" {
		healthPath = healthEndpoint
	}

	url := fmt.Sprintf("http://%s:%d%s", instance.Host, instance.Port, healthPath)

	// 创建HTTP客户端
	client := &http.Client{
		Timeout: h.timeout,
		// 禁止自动跟随重定向
		CheckRedirect: func(req *http.Request, via []*http.Request) error {
			return http.ErrUseLastResponse
		},
	}

	// 创建请求
	req, err := http.NewRequest("GET", url, nil)
	if err != nil {
		return false
	}

	req.Header.Set("User-Agent", h.userAgent)
	req.Header.Set("X-Health-Check", "true")

	// 发送请求
	resp, err := client.Do(req)
	if err != nil {
		return false
	}
	defer resp.Body.Close()

	// 检查状态码 (200-299视为健康)
	return resp.StatusCode >= 200 && resp.StatusCode < 300
}

// CheckWithRetry 带重试的健康检查
// 在服务暂时不可用时进行重试
func (h *HealthChecker) CheckWithRetry(instance *ServiceInstance, maxRetries int) bool {
	for i := 0; i < maxRetries; i++ {
		if h.Check(instance) {
			return true
		}
		// 等待后重试
		if i < maxRetries-1 {
			time.Sleep(time.Duration(i+1) * time.Second)
		}
	}
	return false
}

// SetTimeout 设置健康检查超时时间
func (h *HealthChecker) SetTimeout(timeout time.Duration) {
	h.timeout = timeout
}

// GetTimeout 获取健康检查超时时间
func (h *HealthChecker) GetTimeout() time.Duration {
	return h.timeout
}
