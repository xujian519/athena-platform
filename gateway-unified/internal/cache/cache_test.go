// Package cache - 缓存系统测试
package cache

import (
	"context"
	"fmt"
	"testing"
	"time"
)

// TestDefaultCacheConfig 测试默认配置
func TestDefaultCacheConfig(t *testing.T) {
	cfg := DefaultCacheConfig()

	if cfg.L1MaxSize != 10000 {
		t.Errorf("期望L1MaxSize=10000，实际为%d", cfg.L1MaxSize)
	}

	if cfg.L1TTL != 5*time.Minute {
		t.Errorf("期望L1TTL=5m，实际为%v", cfg.L1TTL)
	}

	if !cfg.L1EnableLRU {
		t.Error("期望启用LRU")
	}

	if !cfg.WarmupEnabled {
		t.Error("期望启用预热")
	}
}

// TestNewMemoryCache 测试创建内存缓存
func TestNewMemoryCache(t *testing.T) {
	cache := NewMemoryCache(100, 5*time.Minute, true)

	if cache == nil {
		t.Fatal("缓存不应为nil")
	}

	if cache.maxSize != 100 {
		t.Errorf("期望maxSize=100，实际为%d", cache.maxSize)
	}
}

// TestMemoryCache_SetAndGet 测试设置和获取
func TestMemoryCache_SetAndGet(t *testing.T) {
	cache := NewMemoryCache(100, 5*time.Minute, false)
	ctx := context.Background()

	// 设置缓存
	err := cache.Set(ctx, "key1", "value1", 0)
	if err != nil {
		t.Fatalf("设置缓存失败: %v", err)
	}

	// 获取缓存
	var result interface{}
	err = cache.Get(ctx, "key1", &result)
	if err != nil {
		t.Fatalf("获取缓存失败: %v", err)
	}

	if result != "value1" {
		t.Errorf("期望value1，实际为%v", result)
	}
}

// TestMemoryCache_Expiration 测试过期
func TestMemoryCache_Expiration(t *testing.T) {
	// 使用较短的TTL
	cache := NewMemoryCache(100, 50*time.Millisecond, false)
	ctx := context.Background()

	// 设置缓存，使用自定义TTL
	err := cache.Set(ctx, "key1", "value1", 50*time.Millisecond)
	if err != nil {
		t.Fatalf("设置缓存失败: %v", err)
	}

	// 立即获取应该成功
	var result interface{}
	err = cache.Get(ctx, "key1", &result)
	if err != nil {
		t.Fatal("立即获取应该成功")
	}

	if result != "value1" {
		t.Errorf("期望value1，实际为%v", result)
	}

	// 等待过期
	time.Sleep(60 * time.Millisecond)

	// 过期后获取应该失败
	err = cache.Get(ctx, "key1", &result)
	if err == nil {
		t.Error("过期后获取应该失败")
	}
}

// TestMemoryCache_Delete 测试删除
func TestMemoryCache_Delete(t *testing.T) {
	cache := NewMemoryCache(100, 5*time.Minute, false)
	ctx := context.Background()

	// 设置缓存
	_ = cache.Set(ctx, "key1", "value1", 0)

	// 删除缓存
	err := cache.Delete(ctx, "key1")
	if err != nil {
		t.Fatalf("删除缓存失败: %v", err)
	}

	// 获取应该失败
	var result interface{}
	err = cache.Get(ctx, "key1", &result)
	if err == nil {
		t.Error("删除后获取应该失败")
	}
}

// TestMemoryCache_Clear 测试清空
func TestMemoryCache_Clear(t *testing.T) {
	cache := NewMemoryCache(100, 5*time.Minute, false)
	ctx := context.Background()

	// 设置多个缓存
	_ = cache.Set(ctx, "key1", "value1", 0)
	_ = cache.Set(ctx, "key2", "value2", 0)

	// 清空缓存
	cache.Clear()

	// 获取应该失败
	var result interface{}
	err := cache.Get(ctx, "key1", &result)
	if err == nil {
		t.Error("清空后获取应该失败")
	}
}

// TestMemoryCache_LRU 测试LRU淘汰
func TestMemoryCache(t *testing.T) {
	maxSize := 3
	cache := NewMemoryCache(maxSize, 5*time.Minute, true)
	ctx := context.Background()

	// 添加maxSize个项目
	for i := 0; i < maxSize; i++ {
		key := fmt.Sprintf("key%d", i)
		_ = cache.Set(ctx, key, i, 0)
	}

	// 访问第一个项目（使其变为最近使用）
	var result interface{}
	_ = cache.Get(ctx, "key0", &result)

	// 添加第maxSize+1个项目，应该淘汰key1（LRU）
	_ = cache.Set(ctx, "key3", 3, 0)

	// key1应该被淘汰
	err := cache.Get(ctx, "key1", &result)
	if err == nil {
		t.Error("key1应该被LRU淘汰")
	}

	// key0应该仍然存在
	err = cache.Get(ctx, "key0", &result)
	if err != nil {
		t.Error("key0应该仍然存在")
	}
}

// TestNewMultiLevelCache 测试创建多级缓存
func TestNewMultiLevelCache(t *testing.T) {
	cfg := DefaultCacheConfig()
	cache, err := NewMultiLevelCache(cfg)

	if err != nil {
		t.Fatalf("创建多级缓存失败: %v", err)
	}

	if cache == nil {
		t.Fatal("缓存不应为nil")
	}

	if cache.l1Cache == nil {
		t.Error("L1缓存不应为nil")
	}

	// 清理
	cache.Close()
}

// TestMultiLevelCache_GetAndSet 测试多级缓存获取和设置
func TestMultiLevelCache_GetAndSet(t *testing.T) {
	cfg := DefaultCacheConfig()
	cfg.WarmupEnabled = false // 禁用预热以加快测试
	cache, err := NewMultiLevelCache(cfg)
	if err != nil {
		t.Fatalf("创建多级缓存失败: %v", err)
	}
	defer cache.Close()

	ctx := context.Background()

	// 设置缓存
	err = cache.Set(ctx, "key1", "value1", 0)
	if err != nil {
		t.Fatalf("设置缓存失败: %v", err)
	}

	// 获取缓存
	var result string
	err = cache.Get(ctx, "key1", &result)
	if err != nil {
		t.Fatalf("获取缓存失败: %v", err)
	}

	if result != "value1" {
		t.Errorf("期望value1，实际为%s", result)
	}

	// 检查统计
	stats := cache.GetStats()
	if stats.TotalSets != 1 {
		t.Errorf("期望1次设置，实际为%d", stats.TotalSets)
	}

	if stats.TotalGets != 1 {
		t.Errorf("期望1次获取，实际为%d", stats.TotalGets)
	}

	if stats.Hits != 1 {
		t.Errorf("期望1次命中，实际为%d", stats.Hits)
	}
}

// TestMultiLevelCache_Miss 测试缓存未命中
func TestMultiLevelCache_Miss(t *testing.T) {
	cfg := DefaultCacheConfig()
	cfg.WarmupEnabled = false
	cache, err := NewMultiLevelCache(cfg)
	if err != nil {
		t.Fatalf("创建多级缓存失败: %v", err)
	}
	defer cache.Close()

	ctx := context.Background()

	// 获取不存在的键
	var result string
	err = cache.Get(ctx, "nonexistent", &result)
	if err == nil {
		t.Error("获取不存在的键应该失败")
	}

	// 检查统计
	stats := cache.GetStats()
	if stats.Misses != 1 {
		t.Errorf("期望1次未命中，实际为%d", stats.Misses)
	}
}

// TestMultiLevelCache_Delete 测试删除缓存
func TestMultiLevelCache_Delete(t *testing.T) {
	cfg := DefaultCacheConfig()
	cfg.WarmupEnabled = false
	cache, err := NewMultiLevelCache(cfg)
	if err != nil {
		t.Fatalf("创建多级缓存失败: %v", err)
	}
	defer cache.Close()

	ctx := context.Background()

	// 设置缓存
	_ = cache.Set(ctx, "key1", "value1", 0)

	// 删除缓存
	err = cache.Delete(ctx, "key1")
	if err != nil {
		t.Fatalf("删除缓存失败: %v", err)
	}

	// 获取应该失败
	var result string
	err = cache.Get(ctx, "key1", &result)
	if err == nil {
		t.Error("删除后获取应该失败")
	}

	// 检查统计
	stats := cache.GetStats()
	if stats.TotalDeletes != 1 {
		t.Errorf("期望1次删除，实际为%d", stats.TotalDeletes)
	}
}

// TestMultiLevelCache_Clear 测试清空缓存
func TestMultiLevelCache_Clear(t *testing.T) {
	cfg := DefaultCacheConfig()
	cfg.WarmupEnabled = false
	cache, err := NewMultiLevelCache(cfg)
	if err != nil {
		t.Fatalf("创建多级缓存失败: %v", err)
	}
	defer cache.Close()

	ctx := context.Background()

	// 设置多个缓存
	_ = cache.Set(ctx, "key1", "value1", 0)
	_ = cache.Set(ctx, "key2", "value2", 0)

	// 清空缓存
	err = cache.Clear(ctx)
	if err != nil {
		t.Fatalf("清空缓存失败: %v", err)
	}

	// 获取应该失败
	var result string
	err = cache.Get(ctx, "key1", &result)
	if err == nil {
		t.Error("清空后获取应该失败")
	}
}

// TestCacheStats 测试缓存统计
func TestCacheStats(t *testing.T) {
	cfg := DefaultCacheConfig()
	cfg.WarmupEnabled = false
	cache, err := NewMultiLevelCache(cfg)
	if err != nil {
		t.Fatalf("创建多级缓存失败: %v", err)
	}
	defer cache.Close()

	ctx := context.Background()

	// 执行一些操作
	_ = cache.Set(ctx, "key1", "value1", 0)
	_ = cache.Set(ctx, "key2", "value2", 0)

	var result string
	_ = cache.Get(ctx, "key1", &result) // 命中
	_ = cache.Get(ctx, "nonexistent", &result) // 未命中

	// 获取统计
	stats := cache.GetStats()

	if stats.TotalSets != 2 {
		t.Errorf("期望2次设置，实际为%d", stats.TotalSets)
	}

	if stats.TotalGets != 2 {
		t.Errorf("期望2次获取，实际为%d", stats.TotalGets)
	}

	if stats.Hits != 1 {
		t.Errorf("期望1次命中，实际为%d", stats.Hits)
	}

	if stats.Misses != 1 {
		t.Errorf("期望1次未命中，实际为%d", stats.Misses)
	}

	expectedHitRatio := 0.5
	if stats.HitRatio < expectedHitRatio-0.01 || stats.HitRatio > expectedHitRatio+0.01 {
		t.Errorf("期望命中率%.2f，实际为%.2f", expectedHitRatio, stats.HitRatio)
	}
}

// TestMultiLevelCache_Concurrency 测试并发访问
func TestMultiLevelCache_Concurrency(t *testing.T) {
	cfg := DefaultCacheConfig()
	cfg.WarmupEnabled = false
	cache, err := NewMultiLevelCache(cfg)
	if err != nil {
		t.Fatalf("创建多级缓存失败: %v", err)
	}
	defer cache.Close()

	ctx := context.Background()

	// 并发设置
	done := make(chan bool)
	for i := 0; i < 100; i++ {
		go func(n int) {
			key := "key" + string(rune('0'+n%10))
			_ = cache.Set(ctx, key, n, 0)
			done <- true
		}(i)
	}

	// 等待所有设置完成
	for i := 0; i < 100; i++ {
		<-done
	}

	// 并发获取
	hitCount := 0
	for i := 0; i < 100; i++ {
		go func(n int) {
			key := "key" + string(rune('0'+n%10))
			var result int
			err := cache.Get(ctx, key, &result)
			if err == nil {
				hitCount++
			}
			done <- true
		}(i)
	}

	// 等待所有获取完成
	for i := 0; i < 100; i++ {
		<-done
	}

	stats := cache.GetStats()
	t.Logf("并发测试完成 - 命中: %d, 设置: %d, 获取: %d",
		hitCount, stats.TotalSets, stats.TotalGets)

	if stats.TotalSets != 100 {
		t.Errorf("期望100次设置，实际为%d", stats.TotalSets)
	}
}

// TestWarmup 测试缓存预热
func TestWarmup(t *testing.T) {
	cfg := DefaultCacheConfig()
	cfg.WarmupEnabled = true
	cfg.WarmupSources = []WarmupSource{
		{
			Name: "test-source",
			LoadFunc: func(ctx context.Context) (map[string]interface{}, error) {
				return map[string]interface{}{
					"warm1": "value1",
					"warm2": "value2",
					"warm3": "value3",
				}, nil
			},
		},
	}

	cache, err := NewMultiLevelCache(cfg)
	if err != nil {
		t.Fatalf("创建多级缓存失败: %v", err)
	}
	defer cache.Close()

	// 等待预热完成
	time.Sleep(100 * time.Millisecond)

	// 检查预热的数据是否可用
	ctx := context.Background()
	var result string

	err = cache.Get(ctx, "warm1", &result)
	if err != nil {
		t.Error("预热数据应该可用")
	}

	if result != "value1" {
		t.Errorf("期望value1，实际为%s", result)
	}
}
