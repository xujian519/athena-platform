// Package llm - LLM响应缓存层
// 提供语义缓存功能，减少重复LLM调用
package llm

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
	Response   *ChatResponse `json:"response"`
	Prompt     string        `json:"prompt"`
	Model      string        `json:"model"`
	Timestamp  time.Time     `json:"timestamp"`
	TTL        time.Duration `json:"ttl"`
	HitCount   int           `json:"hit_count"`
	TokensUsed int           `json:"tokens_used"`
	CostSaved  float64       `json:"cost_saved"`
}

// LLMCache LLM响应缓存
type LLMCache struct {
	redisClient *redis.Client
	localCache  *sync.Map // string -> *CacheEntry
	mu          sync.RWMutex
	enabled     bool
	ttl         time.Duration
	stats       *LLMCacheStats
	config      *LLMCacheConfig
}

// LLMCacheStats 缓存统计
type LLMCacheStats struct {
	mu          sync.RWMutex
	Hits        uint64
	Misses      uint64
	Evictions   uint64
	Size        uint64
	TotalTokens uint64
	TotalCost   float64
	HitRate     float64
}

// LLMCacheConfig 缓存配置
type LLMCacheConfig struct {
	RedisAddr     string
	RedisDB       int
	RedisPassword string
	LocalSize     int
	TTL           time.Duration
	Enabled       bool
	MinTokens     int // 最小token数才缓存（避免缓存简单响应）
	MaxEntrySize  int // 最大缓存条目大小（字节）
}

// DefaultLLMCacheConfig 返回默认缓存配置
func DefaultLLMCacheConfig() *LLMCacheConfig {
	return &LLMCacheConfig{
		RedisAddr:     "localhost:16379",
		RedisDB:       0,
		RedisPassword: "",
		LocalSize:     500,            // 本地缓存最多500条
		TTL:           24 * time.Hour, // LLM响应缓存24小时
		Enabled:       true,
		MinTokens:     50,        // 至少50 tokens才缓存
		MaxEntrySize:  10 * 1024, // 10KB
	}
}

// NewLLMCache 创建LLM缓存
func NewLLMCache(cfg *LLMCacheConfig) (*LLMCache, error) {
	if cfg == nil {
		cfg = DefaultLLMCacheConfig()
	}

	cache := &LLMCache{
		localCache: &sync.Map{},
		enabled:    cfg.Enabled,
		ttl:        cfg.TTL,
		stats:      &LLMCacheStats{},
		config:     cfg,
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

	log.Printf("LLM响应缓存创建成功 enabled=%v redis=%v ttl=%v min_tokens=%d",
		cache.enabled, cache.redisClient != nil, cache.ttl, cfg.MinTokens)

	return cache, nil
}

// Get 获取缓存
func (c *LLMCache) Get(ctx context.Context, prompt string, model string) (*ChatResponse, bool) {
	if !c.enabled {
		return nil, false
	}

	cacheKey := c.generateCacheKey(prompt, model)

	// 1. 尝试从本地缓存获取
	if val, ok := c.localCache.Load(cacheKey); ok {
		entry := val.(*CacheEntry)
		if time.Since(entry.Timestamp) < entry.TTL {
			c.stats.Hits++
			entry.HitCount++

			c.updateHitRate()

			log.Printf("LLM缓存命中(本地) model=%s hit_count=%d tokens_saved=%d",
				model, entry.HitCount, entry.TokensUsed)

			return entry.Response, true
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
				entry.HitCount++

				c.updateHitRate()

				log.Printf("LLM缓存命中(Redis) model=%s hit_count=%d tokens_saved=%d",
					model, entry.HitCount, entry.TokensUsed)

				return entry.Response, true
			}
		}
	}

	c.stats.Misses++
	c.updateHitRate()

	return nil, false
}

// Set 设置缓存
func (c *LLMCache) Set(ctx context.Context, prompt string, model string, response *ChatResponse, costPer1K float64) error {
	if !c.enabled {
		return nil
	}

	// 检查是否满足缓存条件
	if response.Usage.TotalTokens < c.config.MinTokens {
		return nil // 太简单，不缓存
	}

	cacheKey := c.generateCacheKey(prompt, model)

	// 计算节省的成本
	costSaved := float64(response.Usage.TotalTokens) * costPer1K / 1000.0

	entry := &CacheEntry{
		Response:   response,
		Prompt:     prompt,
		Model:      model,
		Timestamp:  time.Now(),
		TTL:        c.ttl,
		HitCount:   0,
		TokensUsed: response.Usage.TotalTokens,
		CostSaved:  costSaved,
	}

	// 检查条目大小
	data, err := json.Marshal(entry)
	if err != nil {
		return fmt.Errorf("序列化缓存数据失败: %w", err)
	}

	if len(data) > c.config.MaxEntrySize {
		log.Printf("缓存条目过大，跳过缓存 size=%d max_size=%d", len(data), c.config.MaxEntrySize)
		return nil
	}

	// 1. 写入本地缓存
	c.localCache.Store(cacheKey, entry)

	// 2. 异步写入Redis
	if c.redisClient != nil {
		go func() {
			ctx, cancel := context.WithTimeout(context.Background(), 2*time.Second)
			defer cancel()

			if err := c.redisClient.Set(ctx, cacheKey, data, c.ttl).Err(); err != nil {
				log.Printf("写入Redis缓存失败 error=%v", err)
			}
		}()
	}

	// 3. 更新统计
	c.stats.mu.Lock()
	c.stats.Size++
	c.stats.TotalTokens += uint64(response.Usage.TotalTokens)
	c.stats.TotalCost += costSaved
	c.stats.mu.Unlock()

	log.Printf("LLM缓存已保存 model=%s tokens=%d cost_saved=%.4f",
		model, response.Usage.TotalTokens, costSaved)

	return nil
}

// Delete 删除缓存
func (c *LLMCache) Delete(ctx context.Context, prompt string, model string) error {
	cacheKey := c.generateCacheKey(prompt, model)

	// 从本地缓存删除
	c.localCache.Delete(cacheKey)

	// 从Redis删除
	if c.redisClient != nil {
		if err := c.redisClient.Del(ctx, cacheKey).Err(); err != nil {
			return fmt.Errorf("删除Redis缓存失败: %w", err)
		}
	}

	c.stats.mu.Lock()
	c.stats.Size--
	c.stats.mu.Unlock()

	return nil
}

// Clear 清空所有缓存
func (c *LLMCache) Clear(ctx context.Context) error {
	// 清空本地缓存
	c.localCache.Range(func(key, value interface{}) bool {
		c.localCache.Delete(key)
		return true
	})

	// 清空Redis缓存（使用SCAN避免阻塞）
	if c.redisClient != nil {
		iter := c.redisClient.Scan(ctx, 0, "athena:llm:*", 0).Iterator()
		for iter.Next(ctx) {
			keys := iter.Val()
			if err := c.redisClient.Del(ctx, keys).Err(); err != nil {
				log.Printf("删除Redis缓存失败 error=%v", err)
			}
		}
	}

	c.stats.mu.Lock()
	c.stats.Size = 0
	c.stats.mu.Unlock()

	log.Printf("LLM缓存已清空")

	return nil
}

// generateCacheKey 生成缓存键
func (c *LLMCache) generateCacheKey(prompt string, model string) string {
	// 使用prompt hash作为缓存键
	h := md5.New()
	h.Write([]byte(prompt))
	h.Write([]byte(model))

	return fmt.Sprintf("athena:llm:%s:%s", model, hex.EncodeToString(h.Sum(nil)))
}

// updateHitRate 更新缓存命中率
func (c *LLMCache) updateHitRate() {
	c.stats.mu.RLock()
	hits := c.stats.Hits
	misses := c.stats.Misses
	c.stats.mu.RUnlock()

	total := hits + misses
	if total > 0 {
		c.stats.HitRate = float64(hits) / float64(total) * 100
	}
}

// GetStats 获取缓存统计
func (c *LLMCache) GetStats() *LLMCacheStats {
	c.stats.mu.RLock()
	defer c.stats.mu.RUnlock()

	return &LLMCacheStats{
		Hits:        c.stats.Hits,
		Misses:      c.stats.Misses,
		Evictions:   c.stats.Evictions,
		Size:        c.stats.Size,
		TotalTokens: c.stats.TotalTokens,
		TotalCost:   c.stats.TotalCost,
		HitRate:     c.stats.HitRate,
	}
}

// GetHitRate 获取缓存命中率
func (c *LLMCache) GetHitRate() float64 {
	stats := c.GetStats()
	return stats.HitRate
}

// Warmup 预热缓存
func (c *LLMCache) Warmup(ctx context.Context, prompts []string, model string, llmClient LLMClient) error {
	log.Printf("开始预热LLM缓存 prompts=%d model=%s", len(prompts), model)

	for i, prompt := range prompts {
		// 检查是否已缓存
		if _, found := c.Get(ctx, prompt, model); found {
			continue
		}

		// 调用LLM
		req := &ChatRequest{
			Messages: []Message{
				{Role: "user", Content: prompt},
			},
			Model: model,
		}

		resp, err := llmClient.Chat(ctx, req)
		if err != nil {
			log.Printf("预热缓存失败 index=%d error=%v", i, err)
			continue
		}

		// 获取模型配置
		config, _ := getDefaultModelConfig(model)

		// 写入缓存
		if err := c.Set(ctx, prompt, model, resp, config.CostPer1K); err != nil {
			log.Printf("预热缓存写入失败 index=%d error=%v", i, err)
		}

		// 避免过快请求
		time.Sleep(100 * time.Millisecond)
	}

	log.Printf("LLM缓存预热完成")

	return nil
}

// getDefaultModelConfig 获取默认模型配置（简化版）
func getDefaultModelConfig(model string) (*ModelConfig, error) {
	// 简化的模型成本配置
	costs := map[string]float64{
		"gpt-3.5-turbo": 0.002,
		"gpt-4o-mini":   0.15,
		"gpt-4o":        2.50,
	}

	cost, ok := costs[model]
	if !ok {
		cost = 0.002 // 默认成本
	}

	return &ModelConfig{
		ModelName: model,
		CostPer1K: cost,
	}, nil
}

// Close 关闭缓存
func (c *LLMCache) Close() error {
	if c.redisClient != nil {
		return c.redisClient.Close()
	}
	return nil
}

// ExportMetrics 导出指标（用于监控）
func (c *LLMCache) ExportMetrics() map[string]interface{} {
	stats := c.GetStats()

	return map[string]interface{}{
		"hits":         stats.Hits,
		"misses":       stats.Misses,
		"evictions":    stats.Evictions,
		"size":         stats.Size,
		"hit_rate":     stats.HitRate,
		"total_tokens": stats.TotalTokens,
		"total_cost":   stats.TotalCost,
	}
}
