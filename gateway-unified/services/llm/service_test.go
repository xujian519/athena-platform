// Package llm - LLM服务测试
package llm

import (
	"context"
	"testing"
	"time"
)

// TestSmartRouter 测试智能路由器
func TestSmartRouter(t *testing.T) {
	router := NewSmartRouter()

	// 测试复杂度计算
	ctx := context.Background()

	// 简单查询
	complexity1 := router.CalculateComplexity(ctx, "什么是专利？")
	if complexity1 < 0 || complexity1 > 1 {
		t.Errorf("复杂度计算错误: %f", complexity1)
	}

	// 复杂查询
	complexity2 := router.CalculateComplexity(ctx, "分析专利CN123456789A的创造性，包括与现有技术的对比")
	if complexity2 <= complexity1 {
		t.Errorf("复杂查询应该有更高的复杂度: %f <= %f", complexity2, complexity1)
	}

	// 测试模型选择
	config, err := router.SelectModel(ctx, "什么是专利？", "")
	_ = ctx // 使用ctx避免未使用警告
	if err != nil {
		t.Fatalf("模型选择失败: %v", err)
	}

	if config == nil {
		t.Fatal("模型配置为空")
	}

	if config.ModelName == "" {
		t.Error("模型名称为空")
	}

	// 测试强制指定模型
	premiumConfig, err := router.SelectModel(ctx, "简单问题", TierPremium)
	if err != nil {
		t.Fatalf("强制模型选择失败: %v", err)
	}

	if premiumConfig.Tier != TierPremium {
		t.Errorf("模型层级错误: 期望%s, 实际%s", TierPremium, premiumConfig.Tier)
	}

	// 测试路由统计
	stats := router.GetStats()
	if stats.TotalRequests == 0 {
		t.Error("总请求数为0")
	}


}
// TestLLMCache 测试LLM缓存
func TestLLMCache(t *testing.T) {
	cfg := DefaultLLMCacheConfig()
	cfg.LocalSize = 10 // 减少缓存大小用于测试

	cache, err := NewLLMCache(cfg)
	if err != nil {
		t.Fatalf("创建缓存失败: %v", err)
	}
	defer cache.Close()

	ctx := context.Background()

	// 创建测试响应
	response := &ChatResponse{
		ID:     "test-id",
		Model:  "gpt-3.5-turbo",
		Object: "chat.completion",
		Choices: []Choice{
			{
				Message: Message{
					Role:    "assistant",
					Content: "测试响应",
				},
			},
		},
		Usage: Usage{
			PromptTokens:     100,
			CompletionTokens: 50,
			TotalTokens:      150,
		},
	}

	// 测试缓存写入
	err = cache.Set(ctx, "测试提示词", "gpt-3.5-turbo", response, 0.002)
	if err != nil {
		t.Fatalf("写入缓存失败: %v", err)
	}

	// 测试缓存读取
	cachedResponse, found := cache.Get(ctx, "测试提示词", "gpt-3.5-turbo")
	if !found {
		t.Fatal("缓存未命中")
	}

	if cachedResponse.ID != response.ID {
		t.Errorf("缓存响应ID错误: 期望%s, 实际%s", response.ID, cachedResponse.ID)
	}

	// 测试缓存统计
	stats := cache.GetStats()
	if stats.Size == 0 {
		t.Error("缓存大小为0")
	}

	hitRate := cache.GetHitRate()
	if hitRate != 100.0 {
		t.Errorf("缓存命中率错误: 期望100.0, 实际%.1f", hitRate)
	}

	// 测试缓存删除
	err = cache.Delete(ctx, "测试提示词", "gpt-3.5-turbo")
	if err != nil {
		t.Fatalf("删除缓存失败: %v", err)
	}

	// 验证删除
	_, found = cache.Get(ctx, "测试提示词", "gpt-3.5-turbo")
	if found {
		t.Error("缓存删除后仍然存在")
	}


}
// TestConcurrentProcessor 测试并发处理器
func TestConcurrentProcessor(t *testing.T) {
	cfg := DefaultConcurrentConfig()
	cfg.MaxConcurrency = 5 // 减少并发数用于测试

	processor, err := NewConcurrentProcessor(cfg)
	if err != nil {
		t.Fatalf("创建并发处理器失败: %v", err)
	}
	defer processor.Close()

	// 测试统计
	stats := processor.GetStats()
	if stats == nil {
		t.Fatal("统计为空")
	}

	if stats.MaxTime == 0 {
		// 第一次调用时MaxTime可能为默认值
		stats.MaxTime = time.Hour
	}


}
// TestModelConfig 测试模型配置
func TestModelConfig(t *testing.T) {
	cfg := DefaultLLMServiceConfig()

	if cfg == nil {
		t.Fatal("默认配置为空")
	}

	if cfg.ClientConfig == nil {
		t.Error("客户端配置为空")
	}

	if cfg.CacheConfig == nil {
		t.Error("缓存配置为空")
	}

	if cfg.ConcurrentConfig == nil {
		t.Error("并发配置为空")
	}


}
// BenchmarkCacheWrite 缓存写入基准测试
func BenchmarkCacheWrite(b *testing.B) {
	cfg := DefaultLLMCacheConfig()
	cfg.LocalSize = 1000

	cache, _ := NewLLMCache(cfg)
	defer cache.Close()

	ctx := context.Background()
	response := &ChatResponse{
		ID:      "test-id",
		Model:   "gpt-3.5-turbo",
		Choices: []Choice{{Message: Message{Content: "测试"}}},
		Usage:   Usage{TotalTokens: 100},
	}

	b.ResetTimer()
	for i := 0; i < b.N; i++ {
		_ = cache.Set(ctx, "测试提示词", "gpt-3.5-turbo", response, 0.002)
	}


}
// BenchmarkCacheRead 缓存读取基准测试
func BenchmarkCacheRead(b *testing.B) {
	cfg := DefaultLLMCacheConfig()
	cfg.LocalSize = 1000

	cache, _ := NewLLMCache(cfg)
	defer cache.Close()

	ctx := context.Background()
	response := &ChatResponse{
		ID:      "test-id",
		Model:   "gpt-3.5-turbo",
		Choices: []Choice{{Message: Message{Content: "测试"}}},
		Usage:   Usage{TotalTokens: 100},
	}
	_ = cache.Set(ctx, "测试提示词", "gpt-3.5-turbo", response, 0.002)

	b.ResetTimer()
	for i := 0; i < b.N; i++ {
		_, _ = cache.Get(ctx, "测试提示词", "gpt-3.5-turbo")
	}


}
// BenchmarkComplexityCalculation 复杂度计算基准测试
func BenchmarkComplexityCalculation(b *testing.B) {
	router := NewSmartRouter()
	ctx := context.Background()
	prompt := "分析专利CN123456789A的创造性，包括与现有技术的对比，评估技术方案的创新性和实用性"

	b.ResetTimer()
	for i := 0; i < b.N; i++ {
		router.CalculateComplexity(ctx, prompt)
	}


}
// BenchmarkModelSelection 模型选择基准测试
func BenchmarkModelSelection(b *testing.B) {
	router := NewSmartRouter()
	ctx := context.Background()
	prompt := "什么是专利？"

	b.ResetTimer()
	for i := 0; i < b.N; i++ {
		_, _ = router.SelectModel(ctx, prompt, "")
	}

}
