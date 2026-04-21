package circuitbreaker

import (
	"errors"
	"sync"
	"time"
)

// State 熔断器状态
type State int

const (
	StateClosed State = iota // 关闭（正常）
	StateOpen                // 打开（熔断）
	StateHalfOpen            // 半开（探测）
)

// String 返回状态字符串
func (s State) String() string {
	switch s {
	case StateClosed:
		return "closed"
	case StateOpen:
		return "open"
	case StateHalfOpen:
		return "half-open"
	default:
		return "unknown"
	}
}

// Config 熔断器配置
type Config struct {
	MaxRequests     uint32        // 半开状态最大请求数
	Interval        time.Duration // 统计时间窗口
	Timeout         time.Duration // 打开状态超时时间
	ReadyToTrip     ReadyToTripFunc // 熔断触发条件
	OnStateChange   StateChangeFunc // 状态变化回调
}

// ReadyToTripFunc 熔断触发条件函数
type ReadyToTripFunc func(counts Counts) bool

// StateChangeFunc 状态变化回调函数
type StateChangeFunc func(name string, from State, to State)

// Counts 计数器
type Counts struct {
	Requests             uint32
	TotalSuccesses       uint32
	TotalFailures        uint32
	ConsecutiveSuccesses uint32
	ConsecutiveFailures  uint32
}

// CircuitBreaker 熔断器
type CircuitBreaker struct {
	name          string
	maxRequests   uint32
	interval      time.Duration
	timeout       time.Duration
	readyToTrip   ReadyToTripFunc
	onStateChange StateChangeFunc

	mutex      sync.Mutex
	state      State
	generation uint64 // 世代号
	counts     Counts
	expiry     time.Time // 计数器过期时间
}

// NewCircuitBreaker 创建熔断器
func NewCircuitBreaker(name string, cfg Config) *CircuitBreaker {
	if cfg.MaxRequests == 0 {
		cfg.MaxRequests = 1
	}
	if cfg.Interval == 0 {
		cfg.Interval = 10 * time.Second
	}
	if cfg.Timeout == 0 {
		cfg.Timeout = 60 * time.Second
	}

	cb := &CircuitBreaker{
		name:        name,
		maxRequests: cfg.MaxRequests,
		interval:    cfg.Interval,
		timeout:     cfg.Timeout,
		readyToTrip: cfg.ReadyToTrip,
		onStateChange: cfg.OnStateChange,
		state:       StateClosed,
	}

	return cb
}

// Allow 判断是否允许请求通过
func (cb *CircuitBreaker) Allow() error {
	cb.mutex.Lock()
	defer cb.mutex.Unlock()

	now := time.Now()
	state, _ := cb.currentState(now)

	if state == StateOpen {
		return errors.New("circuit breaker is open")
	}

	if state == StateHalfOpen && cb.counts.Requests >= cb.maxRequests {
		return errors.New("too many requests in half-open state")
	}

	cb.counts.Requests++
	cb.counts.OnRequest()

	return nil
}

// Success 记录成功
func (cb *CircuitBreaker) Success() {
	cb.mutex.Lock()
	defer cb.mutex.Unlock()

	now := time.Now()
	state, _ := cb.currentState(now)

	if state == StateClosed || state == StateHalfOpen {
		cb.counts.OnSuccess()
		if state == StateHalfOpen && cb.counts.ConsecutiveSuccesses >= cb.maxRequests {
			cb.setState(StateClosed, 0)
		}
	}
}

// Failure 记录失败
func (cb *CircuitBreaker) Failure() {
	cb.mutex.Lock()
	defer cb.mutex.Unlock()

	now := time.Now()
	state, _ := cb.currentState(now)

	if state == StateClosed || state == StateHalfOpen {
		cb.counts.OnFailure()
		if cb.readyToTrip(cb.counts) {
			cb.setState(StateOpen, 0)
		}
	}
}

// currentState 获取当前状态和世代号
func (cb *CircuitBreaker) currentState(now time.Time) (State, uint64) {
	switch cb.state {
	case StateClosed:
		if !cb.expiry.IsZero() && now.After(cb.expiry) {
			cb.resetCounts()
		}
	case StateOpen:
		if now.After(cb.expiry) {
			cb.setState(StateHalfOpen, cb.generation)
		}
	}
	return cb.state, cb.generation
}

// setState 设置状态
func (cb *CircuitBreaker) setState(newState State, generation uint64) {
	if cb.state == newState {
		return
	}

	prevState := cb.state
	cb.state = newState

	cb.generation++

	// 重置计数器
	switch newState {
	case StateClosed:
		cb.resetCounts()
	case StateOpen:
		cb.expiry = time.Now().Add(cb.timeout)
	case StateHalfOpen:
		cb.resetCounts()
	}

	if cb.onStateChange != nil {
		cb.onStateChange(cb.name, prevState, newState)
	}
}

// resetCounts 重置计数器
func (cb *CircuitBreaker) resetCounts() {
	cb.counts = Counts{}
	cb.expiry = time.Now().Add(cb.interval)
}

// OnRequest 记录请求
func (c *Counts) OnRequest() {
	c.Requests++
}

// OnSuccess 记录成功
func (c *Counts) OnSuccess() {
	c.TotalSuccesses++
	c.ConsecutiveSuccesses++
	c.ConsecutiveFailures = 0
}

// OnFailure 记录失败
func (c *Counts) OnFailure() {
	c.TotalFailures++
	c.ConsecutiveFailures++
	c.ConsecutiveSuccesses = 0
}

// GetState 获取当前状态
func (cb *CircuitBreaker) GetState() State {
	cb.mutex.Lock()
	defer cb.mutex.Unlock()
	return cb.state
}

// GetCounts 获取计数器
func (cb *CircuitBreaker) GetCounts() Counts {
	cb.mutex.Lock()
	defer cb.mutex.Unlock()
	return cb.counts
}
