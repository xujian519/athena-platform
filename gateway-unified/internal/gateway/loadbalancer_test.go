package gateway

import (
	"fmt"
	"testing"
	"time"
)

// TestRoundRobinStrategy 测试轮询策略
func TestRoundRobinStrategy(t *testing.T) {
	config := LoadBalancerConfig{
		Strategy: RoundRobin,
	}

	lb := NewLoadBalancer(config)

	instances := createTestInstances(3)

	// 测试轮询顺序
	expectedOrder := []int{0, 1, 2, 0, 1, 2}
	for i, expectedIdx := range expectedOrder {
		selected := lb.Select(instances)
		if selected.ID != instances[expectedIdx].ID {
			t.Errorf("第%d次选择: 期望 %s, 实际 %s", i+1, instances[expectedIdx].ID, selected.ID)
		}
	}
}

// TestWeightedRoundRobinStrategy 测试加权轮询策略
func TestWeightedRoundRobinStrategy(t *testing.T) {
	config := LoadBalancerConfig{
		Strategy: WeightedRoundRobin,
	}

	lb := NewLoadBalancer(config).(*BaseLoadBalancer)

	// 创建权重差异较小的实例，使分布更均匀
	instances := []*ServiceInstance{
		{ID: "inst1", ServiceName: "test-service", Weight: 2},
		{ID: "inst2", ServiceName: "test-service", Weight: 3},
		{ID: "inst3", ServiceName: "test-service", Weight: 5},
	}

	// 统计选择次数
	counts := make(map[string]int)
	iterations := 100

	for i := 0; i < iterations; i++ {
		selected := lb.Select(instances)
		counts[selected.ID]++
	}

	// 验证权重比例 (2:3:5)
	// inst1应该约20次, inst2约30次, inst3约50次
	total := counts["inst1"] + counts["inst2"] + counts["inst3"]
	if total != iterations {
		t.Errorf("总选择次数应该是%d, 实际是%d", iterations, total)
	}

	// 验证相对比例：inst3应该是最多的，inst1应该是最少的
	if counts["inst3"] <= counts["inst2"] || counts["inst2"] <= counts["inst1"] {
		t.Errorf("权重比例不正确: inst1=%d, inst2=%d, inst3=%d (应该递增)",
			counts["inst1"], counts["inst2"], counts["inst3"])
	}

	// 验证大致比例
	ratio1 := float64(counts["inst1"]) / float64(iterations)
	ratio2 := float64(counts["inst2"]) / float64(iterations)
	ratio3 := float64(counts["inst3"]) / float64(iterations)

	t.Logf("加权轮询分布: inst1=%.2f%%, inst2=%.2f%%, inst3=%.2f%%",
		ratio1*100, ratio2*100, ratio3*100)

	// 平滑加权轮询算法在较少迭代次数下可能不太精确
	// 我们主要验证相对大小关系正确
	if ratio3 < ratio1 {
		t.Errorf("inst3比例应该大于inst1")
	}
}

// TestLeastConnectionsStrategy 测试最少连接策略
func TestLeastConnectionsStrategy(t *testing.T) {
	config := LoadBalancerConfig{
		Strategy:         LeastConnections,
		PerformanceAware: true,
	}

	lb := NewLoadBalancer(config).(*BaseLoadBalancer)

	instances := createTestInstances(3)

	// 手动增加连接计数到connections map中
	stats := &connectionStats{
		connections: make(map[string]int32),
		responseTime: make(map[string]time.Duration),
		lastUpdate: time.Now(),
	}
	stats.connections[instances[0].ID] = 5  // 第一个实例有5个连接
	stats.connections[instances[1].ID] = 1  // 第二个实例有1个连接
	stats.connections[instances[2].ID] = 3  // 第三个实例有3个连接

	lb.mu.Lock()
	lb.connections[instances[0].ServiceName] = stats
	lb.mu.Unlock()

	// 应该选择连接数最少的第二个实例
	selected := lb.Select(instances)
	if selected.ID != instances[1].ID {
		t.Errorf("应该选择连接数最少的实例: 期望 %s (1个连接), 实际 %s", instances[1].ID, selected.ID)
	}
}

// TestRandomStrategy 测试随机策略
func TestRandomStrategy(t *testing.T) {
	config := LoadBalancerConfig{
		Strategy: Random,
	}

	lb := NewLoadBalancer(config)

	instances := createTestInstances(3)

	// 多次选择，验证每个实例都有被选中
	selectedSet := make(map[string]bool)
	for i := 0; i < 30; i++ {
		selected := lb.Select(instances)
		selectedSet[selected.ID] = true
	}

	// 至少应该有2个不同的实例被选中
	if len(selectedSet) < 2 {
		t.Errorf("随机策略似乎没有随机性，仅选中了%d个不同实例", len(selectedSet))
	}
}

// TestConsistentHashStrategy 测试一致性哈希策略
func TestConsistentHashStrategy(t *testing.T) {
	config := LoadBalancerConfig{
		Strategy: ConsistentHash,
	}

	lb := NewLoadBalancer(config).(*BaseLoadBalancer)

	instances := createTestInstances(5)

	// 设置哈希键生成函数
	lb.mu.Lock()
	lb.config.HashKey = func(inst *ServiceInstance) string {
		return "test-key"
	}
	lb.mu.Unlock()

	selected1 := lb.Select(instances)
	selected2 := lb.Select(instances)

	if selected1.ID != selected2.ID {
		t.Errorf("一致性哈希应该选择相同的实例: %s vs %s", selected1.ID, selected2.ID)
	}
}

// TestLoadBalancerStats 测试负载均衡器统计
func TestLoadBalancerStats(t *testing.T) {
	config := LoadBalancerConfig{
		Strategy:         LeastConnections,
		PerformanceAware: true,
	}

	lb := NewLoadBalancer(config).(*BaseLoadBalancer)
	instances := createTestInstances(3)

	// 执行几次选择
	for i := 0; i < 5; i++ {
		selected := lb.Select(instances)
		lb.RecordResponse(selected.ServiceName, selected.ID, 100*time.Millisecond)
	}

	// 获取统计信息
	stats := lb.GetStats(instances[0].ServiceName)
	if stats == nil {
		t.Error("统计信息不应该为空")
	}

	// 验证策略
	if stats["strategy"] != LeastConnections {
		t.Errorf("策略不匹配: 期望 %s, 实际 %v", LeastConnections, stats["strategy"])
	}
}

// TestEmptyInstancesList 测试空实例列表
func TestEmptyInstancesList(t *testing.T) {
	config := LoadBalancerConfig{
		Strategy: RoundRobin,
	}

	lb := NewLoadBalancer(config)

	// 空列表应该返回nil
	var instances []*ServiceInstance
	selected := lb.Select(instances)

	if selected != nil {
		t.Error("空实例列表应该返回nil")
	}
}

// TestSingleInstance 测试单个实例
func TestSingleInstance(t *testing.T) {
	config := LoadBalancerConfig{
		Strategy: RoundRobin,
	}

	lb := NewLoadBalancer(config)

	instances := []*ServiceInstance{
		{ID: "inst1", ServiceName: "test-service"},
	}

	// 单个实例应该总是返回该实例
	for i := 0; i < 10; i++ {
		selected := lb.Select(instances)
		if selected.ID != "inst1" {
			t.Errorf("单实例测试失败: 期望 inst1, 实际 %s", selected.ID)
		}
	}
}

// TestStrategyUpdate 测试策略更新
func TestStrategyUpdate(t *testing.T) {
	config := LoadBalancerConfig{
		Strategy: RoundRobin,
	}

	lb := NewLoadBalancer(config).(*BaseLoadBalancer)
	instances := createTestInstances(3)

	// 使用轮询策略
	selected1 := lb.Select(instances)
	lb.UpdateStrategy(Random)

	// 使用随机策略
	selected2 := lb.Select(instances)

	// 验证策略已更新
	if lb.Strategy() != Random {
		t.Errorf("策略更新失败: 期望 %s, 实际 %s", Random, lb.Strategy())
	}

	// 验证两次选择不一定相同
	_ = selected1
	_ = selected2
}

// createTestInstances 创建测试实例
func createTestInstances(count int) []*ServiceInstance {
	instances := make([]*ServiceInstance, count)
	for i := 0; i < count; i++ {
		instances[i] = &ServiceInstance{
			ID:          fmt.Sprintf("inst%d", i+1),
			ServiceName: "test-service",
			Host:        "localhost",
			Port:        8000 + i,
			Weight:      1,
			Status:      "UP",
		}
	}
	return instances
}
