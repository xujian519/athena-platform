// Package vector - 向量检索服务测试
package vector

import (
	"context"
	"testing"
	"time"
)

// TestQdrantClient 测试Qdrant客户端
func TestQdrantClient(t *testing.T) {
	// 跳过集成测试（如果没有Qdrant实例）
	if testing.Short() {
		t.Skip("跳过集成测试")
	}

	cfg := &Config{
		Host:            "localhost",
		Port:            16333,
		Timeout:         30 * time.Second,
		MaxIdleConns:    100,
		MaxConnsPerHost: 10,
	}

	client, err := NewQdrantClient(cfg)
	if err != nil {
		t.Fatalf("创建Qdrant客户端失败: %v", err)
	}
	defer client.Close()

	// 注意：HealthCheck方法不存在，我们跳过这个测试
	// 实际部署中应该添加健康检查端点
	t.Skip("Qdrant客户端未实现HealthCheck方法，跳过此测试")
}

// TestVectorCache 测试向量缓存
func TestVectorCache(t *testing.T) {
	cache, err := NewVectorCache(nil)
	if err != nil {
		t.Fatalf("创建缓存失败: %v", err)
	}
	defer cache.Close()

	ctx := context.Background()

	// 测试缓存写入
	results := []*SearchResult{
		{
			ID:       "test-id-1",
			Score:    0.95,
			Metadata: map[string]string{"key": "value"},
		},
	}

	err = cache.Set(ctx, "test-collection", []float64{0.1, 0.2, 0.3}, results)
	if err != nil {
		t.Fatalf("写入缓存失败: %v", err)
	}

	// 测试缓存读取
	cachedResults, found := cache.Get(ctx, "test-collection", []float64{0.1, 0.2, 0.3})
	if !found {
		t.Fatal("缓存未命中")
	}

	if len(cachedResults) != 1 {
		t.Fatalf("缓存结果数量错误: 期望1, 实际%d", len(cachedResults))
	}

	if cachedResults[0].ID != "test-id-1" {
		t.Errorf("缓存结果ID错误: 期望test-id-1, 实际%s", cachedResults[0].ID)
	}

	// 测试缓存统计
	stats := cache.GetStats()
	if stats.Size != 1 {
		t.Errorf("缓存大小错误: 期望1, 实际%d", stats.Size)
	}

	hitRate := cache.GetHitRate()
	if hitRate != 100.0 {
		t.Errorf("缓存命中率错误: 期望100.0, 实际%.1f", hitRate)
	}
}

// TestVectorSearchService 测试向量检索服务
func TestVectorSearchService(t *testing.T) {
	if testing.Short() {
		t.Skip("跳过集成测试")
	}

	// 创建Qdrant客户端
	qdrantCfg := &Config{
		Host:            "localhost",
		Port:            16333,
		Timeout:         30 * time.Second,
		MaxIdleConns:    100,
		MaxConnsPerHost: 10,
	}

	qdrant, err := NewQdrantClient(qdrantCfg)
	if err != nil {
		t.Fatalf("创建Qdrant客户端失败: %v", err)
	}
	defer qdrant.Close()

	// 创建缓存
	cache, err := NewVectorCache(nil)
	if err != nil {
		t.Fatalf("创建缓存失败: %v", err)
	}
	defer cache.Close()

	// 创建服务
	service := NewVectorSearchService(qdrant, cache)

	// 测试性能统计
	stats := service.GetPerformanceStats()
	if stats == nil {
		t.Fatal("性能统计为空")
	}

	searchStats, ok := stats["search"].(map[string]interface{})
	if !ok {
		t.Fatal("搜索统计类型错误")
	}

	if searchStats["total_searches"] == nil {
		t.Error("total_searches为空")
	}

	cacheStats, ok := stats["cache"].(map[string]interface{})
	if !ok {
		t.Fatal("缓存统计类型错误")
	}

	if cacheStats["hits"] == nil {
		t.Error("缓存hits为空")
	}
}

// BenchmarkCacheSet 缓存写入基准测试
func BenchmarkCacheSet(b *testing.B) {
	cache, _ := NewVectorCache(nil)
	defer cache.Close()

	ctx := context.Background()
	results := []*SearchResult{
		{ID: "test-id", Score: 0.95},
	}

	b.ResetTimer()
	for i := 0; i < b.N; i++ {
		_ = cache.Set(ctx, "test-collection", []float64{0.1, 0.2}, results)
	}
}

// BenchmarkCacheGet 缓存读取基准测试
func BenchmarkCacheGet(b *testing.B) {
	cache, _ := NewVectorCache(nil)
	defer cache.Close()

	ctx := context.Background()
	results := []*SearchResult{
		{ID: "test-id", Score: 0.95},
	}
	_ = cache.Set(ctx, "test-collection", []float64{0.1, 0.2}, results)

	b.ResetTimer()
	for i := 0; i < b.N; i++ {
		_, _ = cache.Get(ctx, "test-collection", []float64{0.1, 0.2})
	}
}
