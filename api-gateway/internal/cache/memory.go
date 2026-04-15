package cache

import (
	"sync"
	"time"
)

// MemoryCache L1内存缓存
type MemoryCache struct {
	items map[string]*CacheItem
	mutex sync.RWMutex
	stats CacheStats
}

// CacheStats 缓存统计
type CacheStats struct {
	Hits        int64 `json:"hits"`
	Misses      int64 `json:"misses"`
	Sets        int64 `json:"sets"`
	Deletes     int64 `json:"deletes"`
	TotalMemory int64 `json:"total_memory"`
}

// NewMemoryCache 创建内存缓存
func NewMemoryCache() *MemoryCache {
	return &MemoryCache{
		items: make(map[string]*CacheItem),
		stats: CacheStats{},
	}
}

// Set 设置缓存项
func (c *MemoryCache) Set(key string, item *CacheItem) error {
	c.mutex.Lock()
	defer c.mutex.Unlock()

	// 如果已存在，先删除旧项
	if oldItem, exists := c.items[key]; exists {
		c.stats.TotalMemory -= c.estimateItemSize(oldItem)
	}

	c.items[key] = item
	c.stats.TotalMemory += c.estimateItemSize(item)
	c.stats.Sets++

	return nil
}

// Get 获取缓存项
func (c *MemoryCache) Get(key string) (*CacheItem, error) {
	c.mutex.RLock()
	defer c.mutex.RUnlock()

	item, exists := c.items[key]
	if !exists {
		c.stats.Misses++
		return nil, ErrCacheNotFound
	}

	c.stats.Hits++
	return item, nil
}

// Update 更新缓存项
func (c *MemoryCache) Update(key string, item *CacheItem) error {
	c.mutex.Lock()
	defer c.mutex.Unlock()

	if _, exists := c.items[key]; !exists {
		return ErrCacheNotFound
	}

	oldItem := c.items[key]
	c.stats.TotalMemory -= c.estimateItemSize(oldItem)
	c.stats.TotalMemory += c.estimateItemSize(item)
	c.items[key] = item

	return nil
}

func (c *MemoryCache) Delete(key string) error {
	c.mutex.Lock()
	defer c.mutex.Unlock()

	item, exists := c.items[key]
	if !exists {
		return ErrCacheNotFound
	}

	c.stats.TotalMemory -= c.estimateItemSize(item)
	delete(c.items, key)
	c.stats.Deletes++

	return nil
}

// Clear 清空缓存
func (c *MemoryCache) Clear() error {
	c.mutex.Lock()
	defer c.mutex.Unlock()

	c.items = make(map[string]*CacheItem)
	c.stats.TotalMemory = 0

	return nil
}

// CleanupExpired 清理过期项
func (c *MemoryCache) CleanupExpired() {
	c.mutex.Lock()
	defer c.mutex.Unlock()

	now := time.Now()
	for key, item := range c.items {
		if now.After(item.ExpiresAt) {
			c.stats.TotalMemory -= c.estimateItemSize(item)
			delete(c.items, key)
		}
	}
}

// Stats 获取统计信息
func (c *MemoryCache) Stats() map[string]interface{} {
	c.mutex.RLock()
	defer c.mutex.RUnlock()

	hitRate := float64(0)
	if c.stats.Hits+c.stats.Misses > 0 {
		hitRate = float64(c.stats.Hits) / float64(c.stats.Hits+c.stats.Misses)
	}

	return map[string]interface{}{
		"items_count":  len(c.items),
		"hits":         c.stats.Hits,
		"misses":       c.stats.Misses,
		"hit_rate":     hitRate,
		"sets":         c.stats.Sets,
		"deletes":      c.stats.Deletes,
		"total_memory": c.stats.TotalMemory,
	}
}

// Close 关闭缓存
func (c *MemoryCache) Close() error {
	return c.Clear()
}

// estimateItemSize 估算缓存项大小
func (c *MemoryCache) estimateItemSize(item *CacheItem) int64 {
	return int64(len(item.Key) + 64) // 简化估算，实际应该序列化后计算
}
