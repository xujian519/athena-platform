package cache

import (
	"context"
	"encoding/json"
	"fmt"
	"time"

	"athena-gateway/internal/config"
	"athena-gateway/internal/logging"

	"go.uber.org/zap"
)

// CacheLevel 缓存级别
type CacheLevel int

const (
	// CacheLevelL1 L1缓存（内存缓存）
	CacheLevelL1 CacheLevel = iota
	// CacheLevelL2 L2缓存（Redis缓存）
	CacheLevelL2
	// CacheLevelL3 L3缓存（持久化缓存）
	CacheLevelL3
)

// CacheItem 缓存项
type CacheItem struct {
	Key         string      `json:"key"`
	Value       interface{} `json:"value"`
	Level       CacheLevel  `json:"level"`
	ExpiresAt   time.Time   `json:"expires_at"`
	CreatedAt   time.Time   `json:"created_at"`
	AccessCount int64       `json:"access_count"`
	LastAccess  time.Time   `json:"last_access"`
}

// MultiLevelCache 多级缓存管理器
type MultiLevelCache struct {
	l1Cache *MemoryCache
	l2Cache *RedisCache
	l3Cache *PersistentCache
	config  *config.RedisConfig
}

// NewMultiLevelCache 创建多级缓存
func NewMultiLevelCache(cfg *config.RedisConfig) (*MultiLevelCache, error) {
	// 创建L1内存缓存
	l1Cache := NewMemoryCache()

	// 创建L2 Redis缓存
	l2Cache, err := NewRedisCache(cfg)
	if err != nil {
		return nil, fmt.Errorf("创建Redis缓存失败: %w", err)
	}

	// 创建L3持久化缓存
	l3Cache := NewPersistentCache()

	cache := &MultiLevelCache{
		l1Cache: l1Cache,
		l2Cache: l2Cache,
		l3Cache: l3Cache,
		config:  cfg,
	}

	// 启动缓存清理和统计
	go cache.cleanupExpiredItems()
	go cache.cacheStatistics()

	logging.LogInfo("多级缓存系统初始化成功",
		zap.Int("l1_max_size", 1000),
		zap.Int("l2_pool_size", cfg.PoolSize),
	)

	return cache, nil
}

// Set 设置缓存项
func (c *MultiLevelCache) Set(ctx context.Context, key string, value interface{}, ttl time.Duration) error {
	item := &CacheItem{
		Key:         key,
		Value:       value,
		ExpiresAt:   time.Now().Add(ttl),
		CreatedAt:   time.Now(),
		AccessCount: 0,
		LastAccess:  time.Now(),
	}

	// 根据数据大小和访问频率决定缓存级别
	level := c.determineCacheLevel(key, value)
	item.Level = level

	// 根据级别设置缓存
	switch level {
	case CacheLevelL1:
		return c.l1Cache.Set(key, item)
	case CacheLevelL2:
		return c.l2Cache.Set(ctx, key, item, ttl)
	case CacheLevelL3:
		return c.l3Cache.Set(key, item)
	}

	return fmt.Errorf("无效的缓存级别: %d", level)
}

// Get 获取缓存项
func (c *MultiLevelCache) Get(ctx context.Context, key string) (interface{}, error) {
	// 首先从L1缓存获取
	if item, err := c.l1Cache.Get(key); err == nil {
		if !item.IsExpired() {
			item.AccessCount++
			item.LastAccess = time.Now()
			c.l1Cache.Update(key, item)
			return item.Value, nil
		}
		c.l1Cache.Delete(key)
	}

	// 从L2缓存获取
	if item, err := c.l2Cache.Get(ctx, key); err == nil {
		if !item.IsExpired() {
			item.AccessCount++
			item.LastAccess = time.Now()

			// 提升到L1缓存
			if c.shouldPromoteToL1(item) {
				c.l1Cache.Set(key, item)
			}

			// 更新L2缓存
			c.l2Cache.Update(ctx, key, item)

			return item.Value, nil
		}
		c.l2Cache.Delete(ctx, key)
	}

	// 从L3缓存获取
	if item, err := c.l3Cache.Get(key); err == nil {
		if !item.IsExpired() {
			item.AccessCount++
			item.LastAccess = time.Now()

			// 提升到更高级别缓存
			if c.shouldPromoteToL1(item) {
				c.l1Cache.Set(key, item)
			} else if c.shouldPromoteToL2(item) {
				c.l2Cache.Set(ctx, key, item, time.Until(item.ExpiresAt))
			}

			// 更新L3缓存
			c.l3Cache.Update(key, item)

			return item.Value, nil
		}
		c.l3Cache.Delete(key)
	}

	return nil, fmt.Errorf("缓存项不存在: %s", key)
}

func (c *MultiLevelCache) Delete(ctx context.Context, key string) error {
	var errs []error

	if err := c.l1Cache.Delete(key); err != nil {
		errs = append(errs, fmt.Errorf("L1缓存删除失败: %w", err))
	}

	if err := c.l2Cache.Delete(ctx, key); err != nil {
		errs = append(errs, fmt.Errorf("L2缓存删除失败: %w", err))
	}

	if err := c.l3Cache.Delete(key); err != nil {
		errs = append(errs, fmt.Errorf("L3缓存删除失败: %w", err))
	}

	if len(errs) > 0 {
		return fmt.Errorf("删除缓存项时发生错误: %v", errs)
	}

	return nil
}

// Clear 清空所有缓存
func (c *MultiLevelCache) Clear(ctx context.Context) error {
	var errs []error

	if err := c.l1Cache.Clear(); err != nil {
		errs = append(errs, fmt.Errorf("清空L1缓存失败: %w", err))
	}

	if err := c.l2Cache.Clear(ctx); err != nil {
		errs = append(errs, fmt.Errorf("清空L2缓存失败: %w", err))
	}

	if err := c.l3Cache.Clear(); err != nil {
		errs = append(errs, fmt.Errorf("清空L3缓存失败: %w", err))
	}

	if len(errs) > 0 {
		return fmt.Errorf("清空缓存时发生错误: %v", errs)
	}

	logging.LogInfo("所有缓存已清空")
	return nil
}

// Stats 获取缓存统计信息
func (c *MultiLevelCache) Stats(ctx context.Context) map[string]interface{} {
	stats := make(map[string]interface{})

	l1Stats := c.l1Cache.Stats()
	l2Stats := c.l2Cache.Stats(ctx)
	l3Stats := c.l3Cache.Stats()

	stats["l1_memory"] = l1Stats
	stats["l2_redis"] = l2Stats
	stats["l3_persistent"] = l3Stats

	return stats
}

// determineCacheLevel 根据数据特性决定缓存级别
func (c *MultiLevelCache) determineCacheLevel(key string, value interface{}) CacheLevel {
	dataSize := c.estimateSize(value)

	// 小数据且高频访问的数据放入L1
	if dataSize < 1024 && c.isHotKey(key) {
		return CacheLevelL1
	}

	// 中等大小的数据放入L2
	if dataSize < 10240 {
		return CacheLevelL2
	}

	// 大数据或不重要的数据放入L3
	return CacheLevelL3
}

// shouldPromoteToL1 判断是否应该提升到L1缓存
func (c *MultiLevelCache) shouldPromoteToL1(item *CacheItem) bool {
	return item.AccessCount > 10 && time.Since(item.LastAccess) < time.Hour
}

// shouldPromoteToL2 判断是否应该提升到L2缓存
func (c *MultiLevelCache) shouldPromoteToL2(item *CacheItem) bool {
	return item.AccessCount > 5 && time.Since(item.LastAccess) < 6*time.Hour
}

// isHotKey 判断是否为热key
func (c *MultiLevelCache) isHotKey(key string) bool {
	// 这里可以实现更复杂的热key检测逻辑
	// 例如基于访问频率、时间窗口等
	return false
}

// estimateSize 估算数据大小（字节）
func (c *MultiLevelCache) estimateSize(value interface{}) int {
	if data, err := json.Marshal(value); err == nil {
		return len(data)
	}
	return 0
}

// cleanupExpiredItems 清理过期项
func (c *MultiLevelCache) cleanupExpiredItems() {
	ticker := time.NewTicker(5 * time.Minute)
	defer ticker.Stop()

	for range ticker.C {
		c.l1Cache.CleanupExpired()

		// L2和L3缓存通常有自动TTL机制
		logging.LogDebug("执行缓存过期项清理")
	}
}

// cacheStatistics 缓存统计信息收集
func (c *MultiLevelCache) cacheStatistics() {
	ticker := time.NewTicker(1 * time.Minute)
	defer ticker.Stop()

	for range ticker.C {
		stats := c.l1Cache.Stats()
		logging.LogInfo("L1内存缓存统计",
			zap.Int("items_count", stats["items_count"].(int)),
			zap.Int64("total_memory", stats["total_memory"].(int64)),
			zap.Float64("hit_rate", stats["hit_rate"].(float64)),
		)
	}
}

// Close 关闭缓存系统
func (c *MultiLevelCache) Close(ctx context.Context) error {
	var errs []error

	if err := c.l1Cache.Close(); err != nil {
		errs = append(errs, fmt.Errorf("关闭L1缓存失败: %w", err))
	}

	if err := c.l2Cache.Close(ctx); err != nil {
		errs = append(errs, fmt.Errorf("关闭L2缓存失败: %w", err))
	}

	if err := c.l3Cache.Close(); err != nil {
		errs = append(errs, fmt.Errorf("关闭L3缓存失败: %w", err))
	}

	if len(errs) > 0 {
		return fmt.Errorf("关闭缓存系统时发生错误: %v", errs)
	}

	logging.LogInfo("多级缓存系统已关闭")
	return nil
}

// IsExpired 检查缓存项是否过期
func (item *CacheItem) IsExpired() bool {
	return time.Now().After(item.ExpiresAt)
}
