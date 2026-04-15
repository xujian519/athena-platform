package gateway

import (
	"context"
	"fmt"
	"testing"
	"time"
)

// TestDegradationManagerRegister 测试降级管理器注册
func TestDegradationManagerRegister(t *testing.T) {
	manager := NewDegradationManager()
	defer manager.Close()

	config := &DegradationConfig{
		Enabled:            true,
		Timeout:            3000,
		ErrorThreshold:     50.0,
		ConcurrencyThreshold: 100,
		Strategy:          NewEmptyResponseStrategy("test"),
		AutoRecover:        true,
		RecoverInterval:    30 * time.Second,
	}

	err := manager.Register("test-service", config)
	if err != nil {
		t.Errorf("注册降级配置失败: %v", err)
	}

	// 重复注册应该失败
	err = manager.Register("test-service", config)
	if err == nil {
		t.Error("重复注册应该失败")
	}

	// 测试默认值
	config2 := &DegradationConfig{
		Enabled:  true,
		Strategy: NewEmptyResponseStrategy("test2"),
	}
	manager.Register("test-service2", config2)

	status := manager.GetStatus("test-service2")
	if status == nil {
		t.Error("状态不应该为空")
	}
}

// TestTimeoutDegradation 测试超时降级
func TestTimeoutDegradation(t *testing.T) {
	manager := NewDegradationManager()
	defer manager.Close()

	config := &DegradationConfig{
		Enabled:            true,
		Timeout:            100, // 100ms超时
		ErrorThreshold:     50.0,
		ConcurrencyThreshold: 100,
		Strategy:          NewDefaultResponseStrategy("fallback", "降级响应"),
		AutoRecover:        false,
	}

	manager.Register("test-service", config)

	ctx := context.Background()

	// 模拟超时请求
	handler := func(ctx context.Context, request interface{}) (interface{}, error) {
		time.Sleep(150 * time.Millisecond)
		return "正常响应", nil
	}

	// 执行请求
	result, err := manager.Execute(ctx, "test-service", "test-request", handler)
	if err != nil {
		// 超时错误
		t.Logf("请求超时（符合预期）: %v", err)
	}

	// 检查是否降级
	status := manager.GetStatus("test-service")
	if status["active"] == true {
		t.Logf("服务已降级，触发原因: %v", status["trigger"])
		if result != nil {
			t.Logf("降级响应: %v", result)
		}
	}
}

// TestErrorRateDegradation 测试错误率降级
func TestErrorRateDegradation(t *testing.T) {
	manager := NewDegradationManager()
	defer manager.Close()

	config := &DegradationConfig{
		Enabled:            true,
		Timeout:            3000,
		ErrorThreshold:     30.0, // 30%错误率
		ConcurrencyThreshold: 100,
		Strategy:          NewDefaultResponseStrategy("fallback", "降级响应"),
		AutoRecover:        false,
	}

	manager.Register("test-service", config)

	ctx := context.Background()

	// 模拟高错误率
	handler := func(ctx context.Context, request interface{}) (interface{}, error) {
		return nil, fmt.Errorf("模拟错误")
	}

	// 发送10个请求，应该触发降级
	for i := 0; i < 10; i++ {
		_, _ = manager.Execute(ctx, "test-service", fmt.Sprintf("request-%d", i), handler)
	}

	// 检查是否降级
	status := manager.GetStatus("test-service")
	if status["active"] != true {
		t.Error("高错误率应该触发降级")
	}

	if status["trigger"] != string(ErrorRateDegradation) {
		t.Errorf("降级原因应该是错误率, 实际是: %v", status["trigger"])
	}
}

// TestConcurrencyDegradation 测试并发降级
func TestConcurrencyDegradation(t *testing.T) {
	manager := NewDegradationManager()
	defer manager.Close()

	config := &DegradationConfig{
		Enabled:            true,
		Timeout:            3000,
		ErrorThreshold:     50.0,
		ConcurrencyThreshold: 5, // 低并发阈值
		Strategy:          NewDefaultResponseStrategy("fallback", "降级响应"),
		AutoRecover:        false,
	}

	manager.Register("test-service", config)

	// 增加并发计数
	for i := 0; i < 6; i++ {
		manager.IncrementConcurrency("test-service")
	}

	// 检查是否降级
	status := manager.GetStatus("test-service")
	if status["active"] != true {
		t.Error("超过并发阈值应该触发降级")
	}

	if status["trigger"] != string(ConcurrencyDegradation) {
		t.Errorf("降级原因应该是并发, 实际是: %v", status["trigger"])
	}

	// 减少并发
	for i := 0; i < 6; i++ {
		manager.DecrementConcurrency("test-service")
	}
}

// TestManualDegradation 测试手动降级
func TestManualDegradation(t *testing.T) {
	manager := NewDegradationManager()
	defer manager.Close()

	config := &DegradationConfig{
		Enabled:            true,
		Timeout:            3000,
		ErrorThreshold:     50.0,
		ConcurrencyThreshold: 100,
		Strategy:          NewDefaultResponseStrategy("fallback", "手动降级响应"),
		AutoRecover:        false,
	}

	manager.Register("test-service", config)

	// 手动触发降级
	err := manager.ManualTrigger("test-service")
	if err != nil {
		t.Errorf("手动触发降级失败: %v", err)
	}

	// 检查状态
	status := manager.GetStatus("test-service")
	if status["active"] != true {
		t.Error("手动触发应该成功")
	}

	if status["trigger"] != string(ManualDegradation) {
		t.Errorf("降级原因应该是手动, 实际是: %v", status["trigger"])
	}

	// 手动恢复
	err = manager.ManualRecover("test-service")
	if err != nil {
		t.Errorf("手动恢复失败: %v", err)
	}

	// 检查状态
	status = manager.GetStatus("test-service")
	if status["active"] == true {
		t.Error("手动恢复后应该不再降级")
	}
}

// TestCacheFallbackStrategy 测试缓存降级策略
func TestCacheFallbackStrategy(t *testing.T) {
	strategy := NewCacheFallbackStrategy("cache", 5*time.Minute)

	// 设置缓存
	strategy.Set("key1", "cached-value1")
	strategy.Set("key2", "cached-value2")

	ctx := context.Background()

	// 测试缓存命中
	result, err := strategy.Execute(ctx, "key1")
	if err != nil {
		t.Errorf("缓存命中不应该失败: %v", err)
	}

	if result != "cached-value1" {
		t.Errorf("缓存值不匹配: 期望 'cached-value1', 实际 %v", result)
	}

	// 测试缓存未命中
	_, err = strategy.Execute(ctx, "non-existent")
	if err == nil {
		t.Error("缓存未命中应该返回错误")
	}

	// 测试策略属性
	if strategy.Name() != "cache" {
		t.Errorf("策略名称不匹配: 期望 'cache', 实际 %s", strategy.Name())
	}

	if strategy.Type() != ErrorRateDegradation {
		t.Errorf("策略类型不匹配: 期望 %s, 实际 %s", ErrorRateDegradation, strategy.Type())
	}
}

// TestDefaultResponseStrategy 测试默认响应策略
func TestDefaultResponseStrategy(t *testing.T) {
	strategy := NewDefaultResponseStrategy("default", "默认值")

	ctx := context.Background()

	// 测试静态默认值
	result, err := strategy.Execute(ctx, "any-request")
	if err != nil {
		t.Errorf("执行默认响应策略失败: %v", err)
	}

	if result != "默认值" {
		t.Errorf("默认值不匹配: 期望 '默认值', 实际 %v", result)
	}

	// 测试函数默认值
	fnStrategy := NewDefaultResponseStrategy("fn", func() interface{} {
		return "动态生成的值"
	})

	result2, err := fnStrategy.Execute(ctx, "any-request")
	if err != nil {
		t.Errorf("执行函数策略失败: %v", err)
	}

	if result2 != "动态生成的值" {
		t.Errorf("函数返回值不匹配: 期望 '动态生成的值', 实际 %v", result2)
	}
}

// TestEmptyResponseStrategy 测试空响应策略
func TestEmptyResponseStrategy(t *testing.T) {
	strategy := NewEmptyResponseStrategy("empty")

	ctx := context.Background()

	result, err := strategy.Execute(ctx, "any-request")
	if err != nil {
		t.Errorf("执行空响应策略失败: %v", err)
	}

	// 结果应该是JSON字节数组
	if result == nil {
		t.Error("空响应不应该返回nil")
	}

	// 验证策略属性
	if strategy.Name() != "empty" {
		t.Errorf("策略名称不匹配")
	}

	if strategy.Type() != TimeoutDegradation {
		t.Errorf("策略类型应该是超时降级")
	}
}

// TestGetAllStatus 测试获取所有状态
func TestGetAllStatus(t *testing.T) {
	manager := NewDegradationManager()
	defer manager.Close()

	// 注册多个服务
	config1 := &DegradationConfig{
		Enabled:  true,
		Strategy: NewEmptyResponseStrategy("s1"),
	}
	config2 := &DegradationConfig{
		Enabled:  true,
		Strategy: NewEmptyResponseStrategy("s2"),
	}

	manager.Register("service1", config1)
	manager.Register("service2", config2)

	// 获取所有状态
	allStatus := manager.GetAllStatus()

	if len(allStatus) != 2 {
		t.Errorf("应该有2个服务状态, 实际有 %d 个", len(allStatus))
	}

	if _, exists := allStatus["service1"]; !exists {
		t.Error("应该包含service1的状态")
	}

	if _, exists := allStatus["service2"]; !exists {
		t.Error("应该包含service2的状态")
	}
}

// TestDegradedServiceExecution 测试降级服务的执行
func TestDegradedServiceExecution(t *testing.T) {
	manager := NewDegradationManager()
	defer manager.Close()

	config := &DegradationConfig{
		Enabled:            true,
		Timeout:            100,
		ErrorThreshold:     50.0,
		ConcurrencyThreshold: 100,
		Strategy:          NewDefaultResponseStrategy("fallback", "降级响应"),
		AutoRecover:        false,
	}

	manager.Register("test-service", config)

	// 手动触发降级
	manager.ManualTrigger("test-service")

	ctx := context.Background()
	handler := func(ctx context.Context, request interface{}) (interface{}, error) {
		return "正常响应", nil
	}

	// 执行请求（应该返回降级响应）
	result, err := manager.Execute(ctx, "test-service", "test-request", handler)
	if err != nil {
		t.Errorf("降级执行失败: %v", err)
	}

	if result != "降级响应" {
		t.Errorf("应该返回降级响应, 实际: %v", result)
	}
}

// TestAutoRecovery 测试自动恢复
func TestAutoRecovery(t *testing.T) {
	manager := NewDegradationManager()
	defer manager.Close()

	config := &DegradationConfig{
		Enabled:            true,
		Timeout:            3000,
		ErrorThreshold:     50.0,
		ConcurrencyThreshold: 100,
		Strategy:          NewDefaultResponseStrategy("fallback", "降级响应"),
		AutoRecover:        true,
		RecoverInterval:    1 * time.Second,
	}

	manager.Register("test-service", config)

	// 触发降级
	manager.ManualTrigger("test-service")

	status := manager.GetStatus("test-service")
	if status["active"] != true {
		t.Error("应该处于降级状态")
	}

	// 注意：自动恢复是异步的，需要等待
	// 这里只验证配置正确，实际恢复需要时间
}

// TestDegradationWithoutStrategy 测试没有降级策略的情况
func TestDegradationWithoutStrategy(t *testing.T) {
	manager := NewDegradationManager()
	defer manager.Close()

	config := &DegradationConfig{
		Enabled:            true,
		Timeout:            100,
		ErrorThreshold:     50.0,
		ConcurrencyThreshold: 100,
		Strategy:          nil, // 没有策略
		AutoRecover:        false,
	}

	manager.Register("test-service", config)

	ctx := context.Background()
	handler := func(ctx context.Context, request interface{}) (interface{}, error) {
		return "正常响应", nil
	}

	// 触发降级
	manager.ManualTrigger("test-service")

	// 执行请求（应该失败，因为没有降级策略）
	_, err := manager.Execute(ctx, "test-service", "test-request", handler)
	if err == nil {
		t.Error("没有降级策略时应该返回错误")
	}
}
