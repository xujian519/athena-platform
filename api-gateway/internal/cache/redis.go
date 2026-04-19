package cache

import (
	"context"
	"encoding/json"
	"fmt"
	"time"

	"athena-gateway/internal/config"
	"athena-gateway/internal/logging"
	"github.com/go-redis/redis/v8"
	"go.uber.org/zap"
)

// RedisCache L2 Redis缓存
type RedisCache struct {
	client *redis.Client
	config *config.RedisConfig
}

// NewRedisCache 创建Redis缓存
func NewRedisCache(cfg *config.RedisConfig) (*RedisCache, error) {
	rdb := redis.NewClient(&redis.Options{
		Addr:         fmt.Sprintf("%s:%d", cfg.Host, cfg.Port),
		Password:     cfg.Password,
		DB:           cfg.Database,
		PoolSize:     cfg.PoolSize,
		MinIdleConns: cfg.MinIdleConns,
	})

	ctx, cancel := context.WithTimeout(context.Background(), 5*time.Second)
	defer cancel()

	if err := rdb.Ping(ctx).Err(); err != nil {
		return nil, fmt.Errorf("Redis连接测试失败: %w", err)
	}

	cache := &RedisCache{
		client: rdb,
		config: cfg,
	}

	// 启动连接池监控
	go cache.monitor()

	logging.LogInfo("Redis缓存初始化成功",
		zap.String("addr", fmt.Sprintf("%s:%d", cfg.Host, cfg.Port)),
		zap.Int("pool_size", cfg.PoolSize),
		zap.Int("min_idle_conns", cfg.MinIdleConns),
	)

	return cache, nil
}

// Set 设置缓存项
func (c *RedisCache) Set(ctx context.Context, key string, item *CacheItem, ttl time.Duration) error {
	data, err := json.Marshal(item)
	if err != nil {
		return fmt.Errorf("序列化缓存项失败: %w", err)
	}

	if err := c.client.Set(ctx, key, data, ttl).Err(); err != nil {
		return fmt.Errorf("设置Redis缓存失败: %w", err)
	}

	return nil
}

// Get 获取缓存项
func (c *RedisCache) Get(ctx context.Context, key string) (*CacheItem, error) {
	data, err := c.client.Get(ctx, key).Result()
	if err != nil {
		if err == redis.Nil {
			return nil, ErrCacheNotFound
		}
		return nil, fmt.Errorf("获取Redis缓存失败: %w", err)
	}

	var item CacheItem
	if err := json.Unmarshal([]byte(data), &item); err != nil {
		return nil, fmt.Errorf("反序列化缓存项失败: %w", err)
	}

	return &item, nil
}

// Update 更新缓存项
func (c *RedisCache) Update(ctx context.Context, key string, item *CacheItem) error {
	data, err := json.Marshal(item)
	if err != nil {
		return fmt.Errorf("序列化缓存项失败: %w", err)
	}

	if err := c.client.Set(ctx, key, data, time.Until(item.ExpiresAt)).Err(); err != nil {
		return fmt.Errorf("更新Redis缓存失败: %w", err)
	}

	return nil
}

func (c *RedisCache) Delete(ctx context.Context, key string) error {
	if err := c.client.Del(ctx, key).Err(); err != nil {
		return fmt.Errorf("删除Redis缓存失败: %w", err)
	}
	return nil
}

// Clear 清空缓存
func (c *RedisCache) Clear(ctx context.Context) error {
	if err := c.client.FlushDB(ctx).Err(); err != nil {
		return fmt.Errorf("清空Redis缓存失败: %w", err)
	}
	return nil
}

// Stats 获取统计信息
func (c *RedisCache) Stats(ctx context.Context) map[string]interface{} {
	info := c.client.Info(ctx, "memory", "keyspace", "clients").Val()

	poolStats := c.client.PoolStats()

	return map[string]interface{}{
		"redis_info": info,
		"pool_stats": map[string]interface{}{
			"hits":        poolStats.Hits,
			"misses":      poolStats.Misses,
			"timeouts":    poolStats.Timeouts,
			"total_conns": poolStats.TotalConns,
			"idle_conns":  poolStats.IdleConns,
			"stale_conns": poolStats.StaleConns,
		},
	}
}

// monitor 监控Redis连接状态
func (c *RedisCache) monitor() {
	ticker := time.NewTicker(30 * time.Second)
	defer ticker.Stop()

	for range ticker.C {
		ctx, cancel := context.WithTimeout(context.Background(), 3*time.Second)

		stats := c.Stats(ctx)
		logging.LogInfo("Redis缓存状态",
			zap.Any("stats", stats),
		)

		cancel()
	}
}

// Close 关闭Redis缓存
func (c *RedisCache) Close(ctx context.Context) error {
	if err := c.client.Close(); err != nil {
		return fmt.Errorf("关闭Redis连接失败: %w", err)
	}
	return nil
}
