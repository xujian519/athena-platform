package gateway

import (
	"fmt"
	"hash/fnv"
	"math/rand"
	"sync"
	"sync/atomic"
	"time"
)

// LoadBalanceStrategy 负载均衡策略类型
type LoadBalanceStrategy string

const (
	// RoundRobin 轮询策略
	RoundRobin LoadBalanceStrategy = "round_robin"
	// WeightedRoundRobin 加权轮询策略
	WeightedRoundRobin LoadBalanceStrategy = "weighted_round_robin"
	// LeastConnections 最少连接策略
	LeastConnections LoadBalanceStrategy = "least_connections"
	// ConsistentHash 一致性哈希策略
	ConsistentHash LoadBalanceStrategy = "consistent_hash"
	// Random 随机策略
	Random LoadBalanceStrategy = "random"
)

// LoadBalancer 负载均衡器接口
type LoadBalancer interface {
	// Select 选择一个服务实例
	Select(instances []*ServiceInstance) *ServiceInstance
	// Strategy 获取当前策略
	Strategy() LoadBalanceStrategy
	// RecordResponse 记录响应时间（用于性能感知负载均衡）
	RecordResponse(serviceName, instanceID string, responseTime time.Duration)
	// GetStats 获取统计信息
	GetStats(serviceName string) map[string]interface{}
}

// LoadBalancerConfig 负载均衡器配置
type LoadBalancerConfig struct {
	Strategy          LoadBalanceStrategy `json:"strategy"`                      // 负载均衡策略
	HashKey           func(*ServiceInstance) string `json:"-"`                   // 一致性哈希的键生成函数
	PerformanceAware  bool                `json:"performance_aware"`             // 是否启用性能感知
	ResponseTimeWindow time.Duration      `json:"response_time_window"`          // 响应时间统计窗口
}

// BaseLoadBalancer 基础负载均衡器
type BaseLoadBalancer struct {
	config       LoadBalancerConfig
	roundRobins  map[string]*roundRobinState
	weightedRBs  map[string]*weightedRoundRobinState
	connections  map[string]*connectionStats
	mu           sync.RWMutex
}

// roundRobinState 轮询状态
type roundRobinState struct {
	current uint64
}

// weightedRoundRobinState 加权轮询状态
type weightedRoundRobinState struct {
	currentWeight int
	effectiveWeight []int
}

// connectionStats 连接统计
type connectionStats struct {
	connections map[string]int32 // instanceID -> 连接数
	responseTime map[string]time.Duration // instanceID -> 平均响应时间
	lastUpdate time.Time
	mu sync.RWMutex
}

// NewLoadBalancer 创建负载均衡器
func NewLoadBalancer(config LoadBalancerConfig) LoadBalancer {
	if config.Strategy == "" {
		config.Strategy = RoundRobin // 默认策略
	}
	if config.ResponseTimeWindow == 0 {
		config.ResponseTimeWindow = 5 * time.Minute // 默认5分钟窗口
	}

	lb := &BaseLoadBalancer{
		config:      config,
		roundRobins: make(map[string]*roundRobinState),
		weightedRBs: make(map[string]*weightedRoundRobinState),
		connections: make(map[string]*connectionStats),
	}

	// 启动性能监控协程
	if config.PerformanceAware {
		go lb.performanceMonitor()
	}

	return lb
}

// Select 选择实例
func (lb *BaseLoadBalancer) Select(instances []*ServiceInstance) *ServiceInstance {
	if len(instances) == 0 {
		return nil
	}

	if len(instances) == 1 {
		return instances[0]
	}

	// 根据策略选择实例
	switch lb.config.Strategy {
	case RoundRobin:
		return lb.roundRobinSelect(instances)
	case WeightedRoundRobin:
		return lb.weightedRoundRobinSelect(instances)
	case LeastConnections:
		return lb.leastConnectionsSelect(instances)
	case ConsistentHash:
		return lb.consistentHashSelect(instances)
	case Random:
		return lb.randomSelect(instances)
	default:
		return lb.roundRobinSelect(instances)
	}
}

// Strategy 获取当前策略
func (lb *BaseLoadBalancer) Strategy() LoadBalanceStrategy {
	return lb.config.Strategy
}

// roundRobinSelect 轮询选择
func (lb *BaseLoadBalancer) roundRobinSelect(instances []*ServiceInstance) *ServiceInstance {
	if len(instances) == 0 {
		return nil
	}

	// 使用服务名作为键
	serviceName := instances[0].ServiceName

	lb.mu.Lock()
	state, exists := lb.roundRobins[serviceName]
	if !exists {
		state = &roundRobinState{current: 0}
		lb.roundRobins[serviceName] = state
	}
	lb.mu.Unlock()

	// 原子递增
	idx := atomic.AddUint64(&state.current, 1) - 1
	return instances[idx%uint64(len(instances))]
}

// weightedRoundRobinSelect 加权轮询选择
func (lb *BaseLoadBalancer) weightedRoundRobinSelect(instances []*ServiceInstance) *ServiceInstance {
	if len(instances) == 0 {
		return nil
	}

	serviceName := instances[0].ServiceName

	lb.mu.Lock()
	state, exists := lb.weightedRBs[serviceName]
	if !exists {
		state = &weightedRoundRobinState{
			currentWeight: 0,
			effectiveWeight: make([]int, len(instances)),
		}
		lb.weightedRBs[serviceName] = state
	}
	lb.mu.Unlock()

	// 使用简单的加权轮询算法
	// 1. 构建按权重重复的实例列表
	expandedInstances := make([]*ServiceInstance, 0)
	for _, inst := range instances {
		w := inst.Weight
		if w <= 0 {
			w = 1
		}
		// 根据权重重复添加实例
		for i := 0; i < w; i++ {
			expandedInstances = append(expandedInstances, inst)
		}
	}

	// 2. 使用轮询选择
	idx := int(state.currentWeight) % len(expandedInstances)
	state.currentWeight++

	return expandedInstances[idx]
}

// leastConnectionsSelect 最少连接选择
func (lb *BaseLoadBalancer) leastConnectionsSelect(instances []*ServiceInstance) *ServiceInstance {
	if len(instances) == 0 {
		return nil
	}

	serviceName := instances[0].ServiceName

	// 获取或创建连接统计
	lb.mu.Lock()
	stats, exists := lb.connections[serviceName]
	if !exists {
		stats = &connectionStats{
			connections: make(map[string]int32),
			responseTime: make(map[string]time.Duration),
			lastUpdate: time.Now(),
		}
		lb.connections[serviceName] = stats
	}
	lb.mu.Unlock()

	stats.mu.Lock()
	defer stats.mu.Unlock()

	// 查找连接数最少的实例
	minConnections := int32(-1)
	selectedIdx := 0

	for i, inst := range instances {
		conn := stats.connections[inst.ID]
		if minConnections == -1 || conn < minConnections {
			minConnections = conn
			selectedIdx = i
		}
	}

	// 增加连接数
	stats.connections[instances[selectedIdx].ID]++

	return instances[selectedIdx]
}

// consistentHashSelect 一致性哈希选择
func (lb *BaseLoadBalancer) consistentHashSelect(instances []*ServiceInstance) *ServiceInstance {
	if len(instances) == 0 {
		return nil
	}

	// 如果没有提供哈希键函数，使用时间戳
	hashKey := fmt.Sprintf("%d", time.Now().UnixNano())
	if lb.config.HashKey != nil {
		// 使用第一个实例生成哈希键（实际应用中应该使用请求特征）
		hashKey = lb.config.HashKey(instances[0])
	}

	// 使用FNV哈希算法
	hash := fnv.New32a()
	hash.Write([]byte(hashKey))
	hashValue := hash.Sum32()

	// 简单的一致性哈希实现
	idx := int(hashValue) % len(instances)
	return instances[idx]
}

// randomSelect 随机选择
func (lb *BaseLoadBalancer) randomSelect(instances []*ServiceInstance) *ServiceInstance {
	if len(instances) == 0 {
		return nil
	}

	// 使用时间戳种子初始化随机数生成器
	r := rand.New(rand.NewSource(time.Now().UnixNano()))
	idx := r.Intn(len(instances))
	return instances[idx]
}

// RecordResponse 记录响应时间（用于性能感知负载均衡）
func (lb *BaseLoadBalancer) RecordResponse(serviceName, instanceID string, responseTime time.Duration) {
	if !lb.config.PerformanceAware {
		return
	}

	lb.mu.RLock()
	stats, exists := lb.connections[serviceName]
	lb.mu.RUnlock()

	if !exists {
		return
	}

	stats.mu.Lock()
	defer stats.mu.Unlock()

	// 更新平均响应时间
	oldTime := stats.responseTime[instanceID]
	if oldTime == 0 {
		stats.responseTime[instanceID] = responseTime
	} else {
		// 指数移动平均
		alpha := 0.3
		stats.responseTime[instanceID] = time.Duration(float64(oldTime)*(1-alpha) + float64(responseTime)*alpha)
	}

	// 减少连接数
	if conn, ok := stats.connections[instanceID]; ok && conn > 0 {
		stats.connections[instanceID] = conn - 1
	}
}

// performanceMonitor 性能监控协程
func (lb *BaseLoadBalancer) performanceMonitor() {
	ticker := time.NewTicker(lb.config.ResponseTimeWindow)
	defer ticker.Stop()

	for range ticker.C {
		lb.mu.Lock()
		for _, stats := range lb.connections {
			stats.mu.Lock()
			// 清理过期的响应时间记录
			if time.Since(stats.lastUpdate) > lb.config.ResponseTimeWindow*2 {
				for instanceID := range stats.responseTime {
					delete(stats.responseTime, instanceID)
				}
			}
			stats.lastUpdate = time.Now()
			stats.mu.Unlock()
		}
		lb.mu.Unlock()
	}
}

// UpdateStrategy 动态更新负载均衡策略
func (lb *BaseLoadBalancer) UpdateStrategy(strategy LoadBalanceStrategy) {
	lb.mu.Lock()
	defer lb.mu.Unlock()
	lb.config.Strategy = strategy
}

// GetStats 获取负载均衡统计信息
func (lb *BaseLoadBalancer) GetStats(serviceName string) map[string]interface{} {
	lb.mu.RLock()
	defer lb.mu.RUnlock()

	stats := make(map[string]interface{})
	stats["strategy"] = lb.config.Strategy
	stats["performance_aware"] = lb.config.PerformanceAware

	if connStats, exists := lb.connections[serviceName]; exists {
		connStats.mu.RLock()
		defer connStats.mu.RUnlock()

		connections := make(map[string]int)
		for k, v := range connStats.connections {
			connections[k] = int(v)
		}
		stats["connections"] = connections

		responseTimes := make(map[string]string)
		for k, v := range connStats.responseTime {
			responseTimes[k] = v.String()
		}
		stats["average_response_times"] = responseTimes
	}

	return stats
}
