package gateway

import (
	"sync"
	"time"
)

// CircuitBreakerState 熔断器状态
type CircuitBreakerState int

const (
	// StateClosed 熔断器关闭（正常状态）
	StateClosed CircuitBreakerState = iota
	// StateOpen 熔断器打开（拒绝请求）
	StateOpen
	// StateHalfOpen 熔断器半开（尝试恢复）
	StateHalfOpen
)

// String 返回状态的字符串表示
func (s CircuitBreakerState) String() string {
	switch s {
	case StateClosed:
		return "CLOSED"
	case StateOpen:
		return "OPEN"
	case StateHalfOpen:
		return "HALF_OPEN"
	default:
		return "UNKNOWN"
	}
}

// CircuitBreakerConfig 熔断器配置
type CircuitBreakerConfig struct {
	// MaxRequests 半开状态下的最大请求数
	MaxRequests uint32 `json:"max_requests"`
	// Interval 统计时间间隔
	Interval time.Duration `json:"interval"`
	// Timeout 熔断器打开后的超时时间
	Timeout time.Duration `json:"timeout"`
	// ReadyToTrip 触发熔断的条件判断函数
	ReadyToTrip func(counts Counts) bool `json:"-"`
	// OnStateChange 状态变更回调
	OnStateChange func(name string, from, to CircuitBreakerState) `json:"-"`
}

// Counts 统计计数
type Counts struct {
	Requests             uint32 `json:"requests"`
	TotalSuccesses       uint32 `json:"total_successes"`
	TotalFailures        uint32 `json:"total_failures"`
	ConsecutiveSuccesses uint32 `json:"consecutive_successes"`
	ConsecutiveFailures  uint32 `json:"consecutive_failures"`
}

// CircuitBreaker 熔断器接口
type CircuitBreaker interface {
	// Allow 判断是否允许通过
	Allow() bool
	// Success 记录成功
	Success()
	// Failure 记录失败
	Failure()
	// State 获取当前状态
	State() CircuitBreakerState
	// Name 获取熔断器名称
	Name() string
}

// gcBreaker 熔断器实现
type gcBreaker struct {
	name          string
	config        CircuitBreakerConfig
	state         CircuitBreakerState
	generation    uint64 // 代际标记
	counts        Counts
	expiry        time.Time
	mu            sync.Mutex
}

// NewCircuitBreaker 创建熔断器
func NewCircuitBreaker(name string, config CircuitBreakerConfig) CircuitBreaker {
	// 设置默认值
	if config.MaxRequests == 0 {
		config.MaxRequests = 1
	}
	if config.Interval == 0 {
		config.Interval = 10 * time.Second
	}
	if config.Timeout == 0 {
		config.Timeout = 60 * time.Second
	}
	if config.ReadyToTrip == nil {
		// 默认条件：连续失败5次或失败率超过50%
		config.ReadyToTrip = func(counts Counts) bool {
			failureRatio := float64(counts.TotalFailures) / float64(counts.Requests)
			return counts.ConsecutiveFailures > 5 || (counts.Requests >= 10 && failureRatio > 0.5)
		}
	}

	return &gcBreaker{
		name:       name,
		config:     config,
		state:      StateClosed,
		generation: 0,
	}
}

// Allow 判断是否允许通过
func (cb *gcBreaker) Allow() bool {
	cb.mu.Lock()
	defer cb.mu.Unlock()

	now := time.Now()

	// 检查是否需要重置计数器
	if cb.config.Interval > 0 && !cb.expiry.IsZero() && now.After(cb.expiry) {
		cb.resetCounts()
	}

	switch cb.state {
	case StateClosed:
		// 关闭状态：允许请求通过
		cb.counts.Requests++
		return true

	case StateOpen:
		// 打开状态：检查是否超时
		if now.After(cb.expiry) {
			// 超时后进入半开状态
			cb.setState(StateHalfOpen)
			return true
		}
		return false

	case StateHalfOpen:
		// 半开状态：限制请求数量
		if cb.counts.Requests < cb.config.MaxRequests {
			cb.counts.Requests++
			return true
		}
		return false

	default:
		return false
	}
}

// Success 记录成功
func (cb *gcBreaker) Success() {
	cb.mu.Lock()
	defer cb.mu.Unlock()

	now := time.Now()

	// 检查是否需要重置计数器
	if cb.config.Interval > 0 && !cb.expiry.IsZero() && now.After(cb.expiry) {
		cb.resetCounts()
	}

	switch cb.state {
	case StateClosed:
		cb.counts.TotalSuccesses++
		cb.counts.ConsecutiveSuccesses++
		cb.counts.ConsecutiveFailures = 0

	case StateHalfOpen:
		cb.counts.TotalSuccesses++
		cb.counts.ConsecutiveSuccesses++
		cb.counts.ConsecutiveFailures = 0

		// 半开状态下成功达到阈值，恢复到关闭状态
		if cb.counts.ConsecutiveSuccesses >= cb.config.MaxRequests {
			cb.setState(StateClosed)
		}
	}
}

// Failure 记录失败
func (cb *gcBreaker) Failure() {
	cb.mu.Lock()
	defer cb.mu.Unlock()

	now := time.Now()

	// 检查是否需要重置计数器
	if cb.config.Interval > 0 && !cb.expiry.IsZero() && now.After(cb.expiry) {
		cb.resetCounts()
	}

	switch cb.state {
	case StateClosed:
		cb.counts.TotalFailures++
		cb.counts.ConsecutiveFailures++
		cb.counts.ConsecutiveSuccesses = 0

		// 检查是否需要熔断
		if cb.config.ReadyToTrip(cb.counts) {
			cb.setState(StateOpen)
		}

	case StateHalfOpen:
		cb.counts.TotalFailures++
		cb.counts.ConsecutiveFailures++
		cb.counts.ConsecutiveSuccesses = 0

		// 半开状态下失败，重新进入打开状态
		cb.setState(StateOpen)
	}
}

// State 获取当前状态
func (cb *gcBreaker) State() CircuitBreakerState {
	cb.mu.Lock()
	defer cb.mu.Unlock()
	return cb.state
}

// Name 获取熔断器名称
func (cb *gcBreaker) Name() string {
	return cb.name
}

// setState 设置状态
func (cb *gcBreaker) setState(state CircuitBreakerState) {
	if cb.state == state {
		return
	}

	prevState := cb.state
	cb.state = state

	// 更新代际标记
	cb.generation++

	// 设置过期时间
	now := time.Now()
	switch state {
	case StateClosed:
		if cb.config.Interval > 0 {
			cb.expiry = now.Add(cb.config.Interval)
		}
	case StateOpen:
		cb.expiry = now.Add(cb.config.Timeout)
	case StateHalfOpen:
		cb.expiry = now.Add(cb.config.Timeout)
	}

	// 重置计数器
	cb.resetCounts()

	// 触发回调
	if cb.config.OnStateChange != nil {
		go cb.config.OnStateChange(cb.name, prevState, state)
	}
}

// resetCounts 重置计数器
func (cb *gcBreaker) resetCounts() {
	cb.counts = Counts{}
	cb.expiry = time.Time{}

	if cb.config.Interval > 0 && cb.state == StateClosed {
		cb.expiry = time.Now().Add(cb.config.Interval)
	}
}

// GetCounts 获取当前计数
func (cb *gcBreaker) GetCounts() Counts {
	cb.mu.Lock()
	defer cb.mu.Unlock()
	return cb.counts
}

// CircuitBreakerManager 熔断器管理器
type CircuitBreakerManager struct {
	breakers map[string]CircuitBreaker
	configs  map[string]CircuitBreakerConfig
	mu       sync.RWMutex
}

// NewCircuitBreakerManager 创建熔断器管理器
func NewCircuitBreakerManager() *CircuitBreakerManager {
	return &CircuitBreakerManager{
		breakers: make(map[string]CircuitBreaker),
		configs:  make(map[string]CircuitBreakerConfig),
	}
}

// GetOrCreate 获取或创建熔断器
func (m *CircuitBreakerManager) GetOrCreate(name string, config CircuitBreakerConfig) CircuitBreaker {
	m.mu.Lock()
	defer m.mu.Unlock()

	if breaker, exists := m.breakers[name]; exists {
		return breaker
	}

	breaker := NewCircuitBreaker(name, config)
	m.breakers[name] = breaker
	m.configs[name] = config

	return breaker
}

// Get 获取熔断器
func (m *CircuitBreakerManager) Get(name string) (CircuitBreaker, bool) {
	m.mu.RLock()
	defer m.mu.RUnlock()

	breaker, exists := m.breakers[name]
	return breaker, exists
}

// GetAll 获取所有熔断器
func (m *CircuitBreakerManager) GetAll() map[string]CircuitBreaker {
	m.mu.RLock()
	defer m.mu.RUnlock()

	result := make(map[string]CircuitBreaker, len(m.breakers))
	for k, v := range m.breakers {
		result[k] = v
	}
	return result
}

// Delete 删除熔断器
func (m *CircuitBreakerManager) Delete(name string) bool {
	m.mu.Lock()
	defer m.mu.Unlock()

	if _, exists := m.breakers[name]; exists {
		delete(m.breakers, name)
		delete(m.configs, name)
		return true
	}
	return false
}

// UpdateConfig 更新熔断器配置
func (m *CircuitBreakerManager) UpdateConfig(name string, config CircuitBreakerConfig) bool {
	m.mu.Lock()
	defer m.mu.Unlock()

	if _, exists := m.breakers[name]; exists {
		m.configs[name] = config
		// 重新创建熔断器以应用新配置
		m.breakers[name] = NewCircuitBreaker(name, config)
		return true
	}
	return false
}

// GetStats 获取所有熔断器的统计信息
func (m *CircuitBreakerManager) GetStats() map[string]interface{} {
	m.mu.RLock()
	defer m.mu.RUnlock()

	stats := make(map[string]interface{})
	breakers := make(map[string]interface{})

	for name, breaker := range m.breakers {
		if gb, ok := breaker.(*gcBreaker); ok {
			breakerInfo := map[string]interface{}{
				"state":  gb.State().String(),
				"counts": gb.GetCounts(),
			}
			breakers[name] = breakerInfo
		}
	}

	stats["breakers"] = breakers
	stats["total"] = len(m.breakers)

	return stats
}
