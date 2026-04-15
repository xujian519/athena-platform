package services

import (
	"context"
	"fmt"
	"net/http"
	"sync"
	"time"

	"athena-gateway/internal/config"
	"athena-gateway/pkg/logger"

	"go.uber.org/zap"
)

// Service 服务接口
type Service interface {
	GetName() string
	GetURL() string
	IsHealthy() bool
	GetHealthCheck() HealthCheck
	GetRetryAttempts() int
	GetTimeout() time.Duration
	CheckHealth(ctx context.Context) error
}

// HealthCheck 健康检查配置
type HealthCheck struct {
	Path     string        `json:"path"`
	Interval time.Duration `json:"interval"`
	Timeout  time.Duration `json:"timeout"`
	Attempts int           `json:"attempts"`
}

// ServiceImpl 服务实现
type ServiceImpl struct {
	name        string
	url         string
	healthy     bool
	mu          sync.RWMutex
	healthCheck HealthCheck
	client      *http.Client
	retryConfig RetryConfig
}

// RetryConfig 重试配置
type RetryConfig struct {
	Attempts int
	Backoff  time.Duration
	MaxWait  time.Duration
}

// NewService 创建新服务
func NewService(name, url string, cfg config.ServiceConfig) *ServiceImpl {
	return &ServiceImpl{
		name:    name,
		url:     url,
		healthy: false,
		healthCheck: HealthCheck{
			Path:     "/health",
			Interval: 30 * time.Second,
			Timeout:  time.Duration(cfg.Timeout) * time.Second,
			Attempts: 3,
		},
		client: &http.Client{
			Timeout: time.Duration(cfg.Timeout) * time.Second,
		},
		retryConfig: RetryConfig{
			Attempts: cfg.RetryAttempts,
			Backoff:  100 * time.Millisecond,
			MaxWait:  5 * time.Second,
		},
	}
}

// GetName 获取服务名称
func (s *ServiceImpl) GetName() string {
	return s.name
}

// GetURL 获取服务URL
func (s *ServiceImpl) GetURL() string {
	return s.url
}

// IsHealthy 检查服务是否健康
func (s *ServiceImpl) IsHealthy() bool {
	s.mu.RLock()
	defer s.mu.RUnlock()
	return s.healthy
}

// GetHealthCheck 获取健康检查配置
func (s *ServiceImpl) GetHealthCheck() HealthCheck {
	return s.healthCheck
}

// GetRetryAttempts 获取重试次数
func (s *ServiceImpl) GetRetryAttempts() int {
	return s.retryConfig.Attempts
}

// GetTimeout 获取超时时间
func (s *ServiceImpl) GetTimeout() time.Duration {
	return s.client.Timeout
}

// CheckHealth 检查服务健康状态
func (s *ServiceImpl) CheckHealth(ctx context.Context) error {
	s.mu.Lock()
	defer s.mu.Unlock()

	// 创建健康检查请求
	url := s.url + s.healthCheck.Path
	req, err := http.NewRequestWithContext(ctx, "GET", url, nil)
	if err != nil {
		return fmt.Errorf("创建健康检查请求失败: %w", err)
	}

	// 设置请求头
	req.Header.Set("User-Agent", "athena-gateway/health-checker")
	req.Header.Set("X-Request-ID", getOrCreateRequestID(ctx))

	// 执行请求
	resp, err := s.client.Do(req)
	if err != nil {
		s.healthy = false
		return fmt.Errorf("健康检查请求失败: %w", err)
	}
	defer resp.Body.Close()

	// 检查状态码
	if resp.StatusCode < 200 || resp.StatusCode >= 300 {
		s.healthy = false
		return fmt.Errorf("健康检查失败，状态码: %d", resp.StatusCode)
	}

	// 服务健康
	wasHealthy := s.healthy
	s.healthy = true

	// 如果从不健康变为健康，记录日志
	if !wasHealthy {
		logger.Info("服务恢复正常",
			zap.String("service", s.name),
			zap.String("url", s.url),
		)
	}

	return nil
}

// ServiceManager 服务管理器
type ServiceManager struct {
	services map[string]Service
	mu       sync.RWMutex
	config   config.ServicesConfig
	ctx      context.Context
	cancel   context.CancelFunc
	wg       sync.WaitGroup
}

// NewServiceManager 创建服务管理器
func NewServiceManager(cfg config.ServicesConfig) (*ServiceManager, error) {
	ctx, cancel := context.WithCancel(context.Background())

	sm := &ServiceManager{
		services: make(map[string]Service),
		config:   cfg,
		ctx:      ctx,
		cancel:   cancel,
	}

	// 初始化服务
	if err := sm.initServices(); err != nil {
		cancel()
		return nil, err
	}

	// 启动健康检查
	sm.startHealthCheck()

	return sm, nil
}

// initServices 初始化服务
func (sm *ServiceManager) initServices() error {
	services := map[string]config.ServiceConfig{
		"auth":            sm.config.Auth,
		"patent_search":   sm.config.PatentSearch,
		"user_management": sm.config.UserManagement,
		"analytics":       sm.config.Analytics,
	}

	for name, cfg := range services {
		service := NewService(name, cfg.URL, cfg)
		sm.services[name] = service

		logger.Info("服务已注册",
			zap.String("name", name),
			zap.String("url", cfg.URL),
			zap.Int("timeout", cfg.Timeout),
			zap.Int("retry_attempts", cfg.RetryAttempts),
		)
	}

	return nil
}

// startHealthCheck 启动健康检查
func (sm *ServiceManager) startHealthCheck() {
	sm.wg.Add(1)
	go func() {
		defer sm.wg.Done()
		ticker := time.NewTicker(30 * time.Second)
		defer ticker.Stop()

		for {
			select {
			case <-sm.ctx.Done():
				return
			case <-ticker.C:
				sm.checkAllServices()
			}
		}
	}()
}

// checkAllServices 检查所有服务健康状态
func (sm *ServiceManager) checkAllServices() {
	sm.mu.RLock()
	services := make(map[string]Service)
	for name, service := range sm.services {
		services[name] = service
	}
	sm.mu.RUnlock()

	for name, service := range services {
		ctx, cancel := context.WithTimeout(sm.ctx, service.GetTimeout())
		if err := service.CheckHealth(ctx); err != nil {
			logger.Warn("服务健康检查失败",
				zap.String("service", name),
				zap.Error(err),
			)
		}
		cancel()
	}
}

// GetService 获取服务
func (sm *ServiceManager) GetService(name string) (Service, error) {
	sm.mu.RLock()
	defer sm.mu.RUnlock()

	service, exists := sm.services[name]
	if !exists {
		return nil, fmt.Errorf("服务不存在: %s", name)
	}

	return service, nil
}

// GetAllServices 获取所有服务
func (sm *ServiceManager) GetAllServices() map[string]Service {
	sm.mu.RLock()
	defer sm.mu.RUnlock()

	services := make(map[string]Service)
	for name, service := range sm.services {
		services[name] = service
	}

	return services
}

// GetHealthyServices 获取健康的服务
func (sm *ServiceManager) GetHealthyServices() map[string]Service {
	sm.mu.RLock()
	defer sm.mu.RUnlock()

	healthyServices := make(map[string]Service)
	for name, service := range sm.services {
		if service.IsHealthy() {
			healthyServices[name] = service
		}
	}

	return healthyServices
}

// GetServiceStatus 获取服务状态
func (sm *ServiceManager) GetServiceStatus() map[string]interface{} {
	sm.mu.RLock()
	defer sm.mu.RUnlock()

	status := make(map[string]interface{})
	for name, service := range sm.services {
		status[name] = map[string]interface{}{
			"name":    service.GetName(),
			"url":     service.GetURL(),
			"healthy": service.IsHealthy(),
			"timeout": service.GetTimeout().String(),
		}
	}

	return status
}

// Close 关闭服务管理器
func (sm *ServiceManager) Close() error {
	sm.cancel()
	sm.wg.Wait()

	logger.Info("服务管理器已关闭")
	return nil
}

// getOrCreateRequestID 获取或创建请求ID
func getOrCreateRequestID(ctx context.Context) string {
	if requestID := ctx.Value("request_id"); requestID != nil {
		if id, ok := requestID.(string); ok {
			return id
		}
	}
	return "health-check-" + fmt.Sprintf("%d", time.Now().Unix())
}

// CircuitBreaker 熔断器
type CircuitBreaker struct {
	name         string
	maxFailures  int
	resetTimeout time.Duration
	mu           sync.Mutex
	failures     int
	lastFailTime time.Time
	state        CircuitState
}

// CircuitState 熔断器状态
type CircuitState int

const (
	StateClosed CircuitState = iota
	StateOpen
	StateHalfOpen
)

// NewCircuitBreaker 创建熔断器
func NewCircuitBreaker(name string, maxFailures int, resetTimeout time.Duration) *CircuitBreaker {
	return &CircuitBreaker{
		name:         name,
		maxFailures:  maxFailures,
		resetTimeout: resetTimeout,
		state:        StateClosed,
	}
}

// Call 调用服务
func (cb *CircuitBreaker) Call(fn func() error) error {
	cb.mu.Lock()
	defer cb.mu.Unlock()

	// 检查熔断器状态
	switch cb.state {
	case StateOpen:
		// 检查是否可以进入半开状态
		if time.Since(cb.lastFailTime) > cb.resetTimeout {
			cb.state = StateHalfOpen
			logger.Info("熔断器进入半开状态", zap.String("service", cb.name))
		} else {
			return fmt.Errorf("熔断器开启，服务暂时不可用")
		}
	case StateHalfOpen:
		// 半开状态，允许少量请求通过
	}

	// 执行请求
	err := fn()

	// 处理结果
	if err != nil {
		cb.failures++
		cb.lastFailTime = time.Now()

		if cb.failures >= cb.maxFailures {
			cb.state = StateOpen
			logger.Warn("熔断器开启",
				zap.String("service", cb.name),
				zap.Int("failures", cb.failures),
			)
		}

		return err
	}

	// 请求成功，重置失败计数
	if cb.state == StateHalfOpen {
		cb.state = StateClosed
		logger.Info("熔断器关闭", zap.String("service", cb.name))
	}

	cb.failures = 0
	return nil
}

// GetState 获取熔断器状态
func (cb *CircuitBreaker) GetState() CircuitState {
	cb.mu.Lock()
	defer cb.mu.Unlock()
	return cb.state
}

// GetFailures 获取失败次数
func (cb *CircuitBreaker) GetFailures() int {
	cb.mu.Lock()
	defer cb.mu.Unlock()
	return cb.failures
}
