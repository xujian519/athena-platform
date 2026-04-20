// Package vector - 向量检索缓存层
package vector

import (
	"context"
	"crypto/md5"
	"encoding/hex"
	"encoding/json"
	"fmt"
	"sync"
	"time"

	"log"
	"github.com/go-redis/redis/v8"
)

// CacheEntry 缓存条目
type CacheEntry struct {
	Results   []*SearchResult `json:"results"`
	Timestamp time.Time       `json:"timestamp"`
	TTL       time.Duration   `json:"ttl"`
}

// VectorCache 向量检索缓存
type VectorCache struct {
	redisClient *redis.Client
	localCache  *sync.Map // string -> *CacheEntry
	mu          sync.RWMutex
	enabled     bool
	ttl         time.Duration
	stats       *CacheStats
}

// CacheStats 缓存统计
type CacheStats struct {
	mu        sync.RWMutex
	Hits      uint64
	Misses    uint64
	Evictions uint64
	Size      uint64
}

// CacheConfig 缓存配置
type CacheConfig struct {
	RedisAddr     string
	RedisDB       int
	RedisPassword string
	LocalSize     int
	TTL           time.Duration
	Enabled       bool
}

// DefaultCacheConfig 返回默认缓存配置
func DefaultCacheConfig() *CacheConfig {
	return &CacheConfig{
		RedisAddr:     "localhost:16379",
		RedisDB:       0,
		RedisPassword: "",
		LocalSize:     1000, // 本地缓存最多1000条
		TTL:           5 * time.Minute,
		Enabled:       true,
	}
}

// NewVectorCache 创建向量缓存
func NewVectorCache(cfg *CacheConfig) (*VectorCache, error) {
	if cfg == nil {
		cfg = DefaultCacheConfig()
	}

	cache := &VectorCache{
		localCache: &sync.Map{},
		enabled:    cfg.Enabled,
		ttl:        cfg.TTL,
		stats:      &CacheStats{},
	}

	// 初始化Redis客户端
	if cfg.RedisAddr != "" {
		cache.redisClient = redis.NewClient(&redis.Options{
			Addr:     cfg.RedisAddr,
			DB:       cfg.RedisDB,
			Password: cfg.RedisPassword,
			PoolSize: 50,
		})

		// 测试Redis连接
		ctx, cancel := context.WithTimeout(context.Background(), 5*time.Second)
		defer cancel()
		if err := cache.redisClient.Ping(ctx).Err(); err != nil {
			log.Printf("Redis连接失败，仅使用本地缓存 addr=%s error=%v", cfg.RedisAddr, err)
			cache.redisClient = nil
		}
	}

	log.Printf("向量缓存创建成功 enabled=%v redis=%v ttl=%v", cache.enabled, cache.redisClient != nil, cache.ttl)

	return cache, nil
}

// Get 获取缓存
func (c *VectorCache) Get(ctx context.Context, collection string, vector []float64) ([]*SearchResult, bool) {
	if !c.enabled {
		return nil, false
	}

	cacheKey := c.generateCacheKey(collection, vector)

	// 1. 尝试从本地缓存获取
	if val, ok := c.localCache.Load(cacheKey); ok {
		entry := val.(*CacheEntry)
		if time.Since(entry.Timestamp) < entry.TTL {
			c.stats.Hits++
			return entry.Results, true
		}
		// 缓存过期，删除
		c.localCache.Delete(cacheKey)
		c.stats.Evictions++
	}

	// 2. 尝试从Redis获取
	if c.redisClient != nil {
		data, err := c.redisClient.Get(ctx, cacheKey).Bytes()
		if err == nil && len(data) > 0 {
			var entry CacheEntry
			if err := json.Unmarshal(data, &entry); err == nil {
				// 写入本地缓存
				c.localCache.Store(cacheKey, &entry)
				c.stats.Hits++
				return entry.Results, true
			}
		}
	}

	c.stats.Misses++
	return nil, false
}

// Set 设置缓存
func (c *VectorCache) Set(ctx context.Context, collection string, vector []float64, results []*SearchResult) error {
	if !c.enabled {
		return nil
	}

	cacheKey := c.generateCacheKey(collection, vector)
	entry := &CacheEntry{
		Results:   results,
		Timestamp: time.Now(),
		TTL:       c.ttl,
	}

	// 1. 写入本地缓存
	c.localCache.Store(cacheKey, entry)

	// 2. 异步写入Redis
	if c.redisClient != nil {
		go func() {
			ctx, cancel := context.WithTimeout(context.Background(), 2*time.Second)
			defer cancel()

			data, err := json.Marshal(entry)
			if err != nil {
				log.Printf("序列化缓存数据失败 error=%v", err)
				return
			}

			if err := c.redisClient.Set(ctx, cacheKey, data, c.ttl).Err(); err != nil {
				log.Printf("写入Redis缓存失败 error=%v", err)
			}
		}()
	}

	c.stats.Size++

	return nil
}

// Delete 删除缓存
func (c *VectorCache) Delete(ctx context.Context, collection string, vector []float64) error {
	cacheKey := c.generateCacheKey(collection, vector)

	// 从本地缓存删除
	c.localCache.Delete(cacheKey)

	// 从Redis删除
	if c.redisClient != nil {
		if err := c.redisClient.Del(ctx, cacheKey).Err(); err != nil {
			return fmt.Errorf("删除Redis缓存失败: %w", err)
		}
	}

	c.stats.Size--

	return nil
}

// Clear 清空所有缓存
func (c *VectorCache) Clear(ctx context.Context) error {
	// 清空本地缓存
	c.localCache.Range(func(key, value interface{}) bool {
		c.localCache.Delete(key)
		return true
	})

	// 清空Redis缓存（使用SCAN避免阻塞）
	if c.redisClient != nil {
		iter := c.redisClient.Scan(ctx, 0, "athena:vector:*", 0).Iterator()
		for iter.Next(ctx) {
			keys := iter.Val()
			if err := c.redisClient.Del(ctx, keys).Err(); err != nil {
				log.Printf("删除Redis缓存失败 error=%v", err)
			}
		}
	}

	c.stats.Size = 0

	log.Printf("向量缓存已清空")

	return nil
}

// generateCacheKey 生成缓存键
func (c *VectorCache) generateCacheKey(collection string, vector []float64) string {
	// 使用向量hash作为缓存键
	h := md5.New()
	h.Write([]byte(collection))

	// 为了性能，只对向量的一部分进行hash
	for i, v := range vector {
		if i >= 10 {
			break
		}
		h.Write([]byte(fmt.Sprintf("%.6f", v)))
	}

	return fmt.Sprintf("athena:vector:%s:%s", collection, hex.EncodeToString(h.Sum(nil)))
}

// GetStats 获取缓存统计
func (c *VectorCache) GetStats() *CacheStats {
	c.stats.mu.RLock()
	defer c.stats.mu.RUnlock()

	return &CacheStats{
		Hits:      c.stats.Hits,
		Misses:    c.stats.Misses,
		Evictions: c.stats.Evictions,
		Size:      c.stats.Size,
	}
}

// GetHitRate 获取缓存命中率
func (c *VectorCache) GetHitRate() float64 {
	stats := c.GetStats()
	hits := stats.Hits
	misses := stats.Misses
	total := hits + misses

	if total == 0 {
		return 0.0
	}

	return float64(hits) / float64(total) * 100
}

// Close 关闭缓存
func (c *VectorCache) Close() error {
	if c.redisClient != nil {
		return c.redisClient.Close()
	}
	return nil
}
