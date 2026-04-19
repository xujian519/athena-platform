// Package cache - 多级缓存系统
// 实现L1(内存) + L2(分布式)两级缓存，支持缓存预热和LRU淘汰
package cache

import (
	"context"
	"encoding/json"
	"fmt"
	"sync"
	"time"

	"github.com/athena-workspace/gateway-unified/internal/logging"
)

// CacheItem 缓存项
type CacheItem struct {
	Key        string
	Value      interface{}
	Expiration time.Time
	Metadata   map[string]string
	createdAt  time.Time
	accessAt   time.Time
	hitCount   int
	// LRU链表指针
	prev *CacheItem
	next *CacheItem
}

// IsExpired 检查是否过期
func (item *CacheItem) IsExpired() bool {
	return !item.Expiration.IsZero() && time.Now().After(item.Expiration)
}

// CacheStats 缓存统计
type CacheStats struct {
	mu               sync.RWMutex
	Hits             uint64
	Misses           uint64
	Evictions        uint64
	TotalSets        uint64
	TotalGets        uint64
	TotalDeletes     uint64
	HitRatio         float64
	AverageAccessTime time.Duration
}

// CacheLevel 缓存级别
type CacheLevel int

const (
	Level1 CacheLevel = iota // 热数据缓存（内存）
	Level2                  // 温数据缓存（分布式）
	Level3                  // 冷数据缓存（持久化）
)

// String 返回缓存级别字符串
func (l CacheLevel) String() string {
	switch l {
	case Level1:
		return "L1"
	case Level2:
		return "L2"
	case Level3:
		return "L3"
	default:
		return "UNKNOWN"
	}
}

// CacheConfig 缓存配置
type CacheConfig struct {
	// L1缓存配置
	L1MaxSize    int           // L1最大条目数
	L1TTL        time.Duration // L1默认TTL
	L1EnableLRU  bool          // 启用LRU淘汰

	// L2缓存配置
	L2Enabled    bool          // 是否启用L2
	L2MaxSize    int           // L2最大条目数
	L2TTL        time.Duration // L2默认TTL

	// 缓存预热配置
	WarmupEnabled    bool                   // 启用缓存预热
	WarmupSources    []WarmupSource         // 预热数据源
	WarmupConcurrency int                   // 预热并发数

	// 清理配置
	CleanupInterval  time.Duration // 清理间隔
	EvictionPolicy   string        // 淘汰策略: lru, lfu, ttl

	// 序列化配置
	Serializer Serializer // 序列化器
}

// WarmupSource 预热数据源
type WarmupSource struct {
	Name     string
	LoadFunc func(ctx context.Context) (map[string]interface{}, error)
	Priority int // 优先级，数字越小越优先
}

// DefaultCacheConfig 返回默认配置
func DefaultCacheConfig() *CacheConfig {
	return &CacheConfig{
		L1MaxSize:       10000,
		L1TTL:           5 * time.Minute,
		L1EnableLRU:     true,

		L2Enabled:       false,
		L2MaxSize:       100000,
		L2TTL:           30 * time.Minute,

		WarmupEnabled:    true,
		WarmupConcurrency: 10,

		CleanupInterval:  1 * time.Minute,
		EvictionPolicy:   "lru",

		Serializer:      JSONSerializer{},
	}
}

// Serializer 序列化器接口
type Serializer interface {
	Serialize(value interface{}) ([]byte, error)
	Deserialize(data []byte, value interface{}) error
}

// JSONSerializer JSON序列化器
type JSONSerializer struct{}

func (j JSONSerializer) Serialize(value interface{}) ([]byte, error) {
	return json.Marshal(value)
}

func (j JSONSerializer) Deserialize(data []byte, value interface{}) error {
	return json.Unmarshal(data, value)
}

// MultiLevelCache 多级缓存
type MultiLevelCache struct {
	config  *CacheConfig
	l1Cache *MemoryCache
	l2Cache CacheInterface // 可选的L2缓存
	stats   *CacheStats
	mu      sync.RWMutex
	closed  bool

	// 缓存预热
	warmupDone bool
	warmupMu   sync.Mutex
}

// CacheInterface 缓存接口
type CacheInterface interface {
	Get(ctx context.Context, key string, value interface{}) error
	Set(ctx context.Context, key string, value interface{}, ttl time.Duration) error
	Delete(ctx context.Context, key string) error
	Clear(ctx context.Context) error
}

// MemoryCache 内存缓存（L1）
type MemoryCache struct {
	items    map[string]*CacheItem
	mu       sync.RWMutex
	lruList  *LRUList
	maxSize  int
	ttl      time.Duration
	enableLRU bool
}

// LRUList LRU链表
type LRUList struct {
	head *CacheItem
	tail *CacheItem
	size int
}

// NewMultiLevelCache 创建多级缓存
func NewMultiLevelCache(cfg *CacheConfig) (*MultiLevelCache, error) {
	if cfg == nil {
		cfg = DefaultCacheConfig()
	}

	// 创建L1内存缓存
	l1Cache := NewMemoryCache(cfg.L1MaxSize, cfg.L1TTL, cfg.L1EnableLRU)

	cache := &MultiLevelCache{
		config:  cfg,
		l1Cache: l1Cache,
		stats:   &CacheStats{},
	}

	// 启动后台清理任务
	go cache.cleanupLoop()

	// 执行缓存预热
	if cfg.WarmupEnabled {
		go cache.warmup()
	}

	logging.LogInfo("多级缓存创建成功",
		logging.String("l1_size", fmt.Sprintf("%d", cfg.L1MaxSize)),
		logging.String("l1_ttl", cfg.L1TTL.String()),
		logging.Bool("l2_enabled", cfg.L2Enabled),
		logging.Bool("warmup_enabled", cfg.WarmupEnabled))

	return cache, nil
}

// NewMemoryCache 创建内存缓存
func NewMemoryCache(maxSize int, ttl time.Duration, enableLRU bool) *MemoryCache {
	return &MemoryCache{
		items:      make(map[string]*CacheItem),
		maxSize:    maxSize,
		ttl:        ttl,
		enableLRU:  enableLRU,
		lruList:    NewLRUList(),
	}
}

// NewLRUList 创建LRU链表
func NewLRUList() *LRUList {
	dummy := &CacheItem{}
	return &LRUList{
		head: dummy,
		tail: dummy,
	}
}

// Get 获取缓存
func (c *MultiLevelCache) Get(ctx context.Context, key string, value interface{}) error {
	startTime := time.Now()
	c.stats.mu.Lock()
	c.stats.TotalGets++
	c.stats.mu.Unlock()

	// 先查L1
	err := c.l1Cache.Get(ctx, key, value)
	if err == nil {
		c.recordHit(Level1)
		c.recordAccessTime(time.Since(startTime))
		return nil
	}

	// L1未命中，查L2
	if c.l2Cache != nil {
		err = c.l2Cache.Get(ctx, key, value)
		if err == nil {
			// 将L2的数据回填到L1
			c.l1Cache.Set(ctx, key, value, c.config.L1TTL)
			c.recordHit(Level2)
			c.recordAccessTime(time.Since(startTime))
			return nil
		}
	}

	c.recordMiss()
	c.recordAccessTime(time.Since(startTime))
	return fmt.Errorf("cache miss: %s", key)
}

// Set 设置缓存
func (c *MultiLevelCache) Set(ctx context.Context, key string, value interface{}, ttl time.Duration) error {
	if ttl == 0 {
		ttl = c.config.L1TTL
	}

	// 设置L1
	err := c.l1Cache.Set(ctx, key, value, ttl)
	if err != nil {
		return fmt.Errorf("L1 cache set failed: %w", err)
	}

	// 设置L2
	if c.l2Cache != nil {
		_ = c.l2Cache.Set(ctx, key, value, c.config.L2TTL)
	}

	c.stats.mu.Lock()
	c.stats.TotalSets++
	c.stats.mu.Unlock()

	return nil
}

// Delete 删除缓存
func (c *MultiLevelCache) Delete(ctx context.Context, key string) error {
	// 删除L1
	err := c.l1Cache.Delete(ctx, key)
	if err != nil {
		return err
	}

	// 删除L2
	if c.l2Cache != nil {
		_ = c.l2Cache.Delete(ctx, key)
	}

	c.stats.mu.Lock()
	c.stats.TotalDeletes++
	c.stats.mu.Unlock()

	return nil
}

// Clear 清空所有缓存
func (c *MultiLevelCache) Clear(ctx context.Context) error {
	c.l1Cache.Clear()
	if c.l2Cache != nil {
		_ = c.l2Cache.Clear(ctx)
	}
	return nil
}

// GetL1 获取L1缓存
func (c *MultiLevelCache) GetL1() *MemoryCache {
	return c.l1Cache
}

// GetStats 获取缓存统计
func (c *MultiLevelCache) GetStats() *CacheStats {
	c.stats.mu.RLock()
	defer c.stats.mu.RUnlock()

	// 计算命中率
	total := c.stats.Hits + c.stats.Misses
	if total > 0 {
		c.stats.HitRatio = float64(c.stats.Hits) / float64(total)
	}

	// 返回统计副本
	statsCopy := &CacheStats{
		Hits:              c.stats.Hits,
		Misses:            c.stats.Misses,
		Evictions:         c.stats.Evictions,
		TotalSets:         c.stats.TotalSets,
		TotalGets:         c.stats.TotalGets,
		TotalDeletes:      c.stats.TotalDeletes,
		HitRatio:          c.stats.HitRatio,
		AverageAccessTime: c.stats.AverageAccessTime,
	}

	return statsCopy
}

// recordHit 记录命中
func (c *MultiLevelCache) recordHit(level CacheLevel) {
	c.stats.mu.Lock()
	defer c.stats.mu.Unlock()
	c.stats.Hits++
	logging.LogDebug("缓存命中",
		logging.String("level", level.String()),
		logging.Uint64("total_hits", c.stats.Hits))
}

// recordMiss 记录未命中
func (c *MultiLevelCache) recordMiss() {
	c.stats.mu.Lock()
	defer c.stats.mu.Unlock()
	c.stats.Misses++
	logging.LogDebug("缓存未命中", logging.Uint64("total_misses", c.stats.Misses))
}

// recordAccessTime 记录访问时间
func (c *MultiLevelCache) recordAccessTime(duration time.Duration) {
	c.stats.mu.Lock()
	defer c.stats.mu.Unlock()

	// 简单的移动平均
	if c.stats.AverageAccessTime == 0 {
		c.stats.AverageAccessTime = duration
	} else {
		c.stats.AverageAccessTime = (c.stats.AverageAccessTime*9 + duration) / 10
	}
}

// cleanupLoop 清理循环
func (c *MultiLevelCache) cleanupLoop() {
	ticker := time.NewTicker(c.config.CleanupInterval)
	defer ticker.Stop()

	for range ticker.C {
		c.cleanup()
	}
}

// cleanup 清理过期缓存
func (c *MultiLevelCache) cleanup() {
	evicted := c.l1Cache.Cleanup()
	if evicted > 0 {
		c.stats.mu.Lock()
		c.stats.Evictions += uint64(evicted)
		c.stats.mu.Unlock()

		logging.LogDebug("清理过期缓存",
			logging.Int("evicted", evicted))
	}
}

// warmup 缓存预热
func (c *MultiLevelCache) warmup() {
	c.warmupMu.Lock()
	defer c.warmupMu.Unlock()

	if c.warmupDone {
		return
	}

	logging.LogInfo("开始缓存预热",
		logging.Int("sources", len(c.config.WarmupSources)))

	ctx, cancel := context.WithTimeout(context.Background(), 5*time.Minute)
	defer cancel()

	// 按优先级排序预热源
	sources := make([]WarmupSource, len(c.config.WarmupSources))
	copy(sources, c.config.WarmupSources)

	// 执行预热
	totalItems := 0
	for _, source := range sources {
		items, err := source.LoadFunc(ctx)
		if err != nil {
			logging.LogWarn("预热数据源加载失败",
				logging.String("source", source.Name),
				logging.Err(err))
			continue
		}

		// 加载到缓存
		for key, value := range items {
			_ = c.Set(ctx, key, value, c.config.L1TTL)
			totalItems++
		}

		logging.LogInfo("预热数据源完成",
			logging.String("source", source.Name),
			logging.Int("items", len(items)))
	}

	c.warmupDone = true

	logging.LogInfo("缓存预热完成",
		logging.Int("total_items", totalItems))
}

// Close 关闭缓存
func (c *MultiLevelCache) Close() error {
	c.mu.Lock()
	defer c.mu.Unlock()

	if c.closed {
		return nil
	}

	c.closed = true
	c.l1Cache.Clear()

	if c.l2Cache != nil {
		_ = c.l2Cache.Clear(context.Background())
	}

	logging.LogInfo("多级缓存已关闭",
		logging.Uint64("total_hits", c.stats.Hits),
		logging.Uint64("total_misses", c.stats.Misses),
		logging.Float64("hit_ratio", c.stats.HitRatio))

	return nil
}

// ========== MemoryCache 实现 ==========

// Get 获取缓存
func (m *MemoryCache) Get(ctx context.Context, key string, value interface{}) error {
	m.mu.RLock()
	item, exists := m.items[key]
	m.mu.RUnlock()

	if !exists || item.IsExpired() {
		return fmt.Errorf("key not found or expired")
	}

	// 更新访问时间（用于LRU）
	m.mu.Lock()
	item.accessAt = time.Now()
	item.hitCount++
	if m.enableLRU {
		m.lruList.MoveToFront(item)
	}
	m.mu.Unlock()

	// 返回值
	switch v := value.(type) {
	case *interface{}:
		*v = item.Value
	default:
		// 尝试类型断言
		data, err := json.Marshal(item.Value)
		if err != nil {
			return err
		}
		return json.Unmarshal(data, v)
	}

	return nil
}

// Set 设置缓存
func (m *MemoryCache) Set(ctx context.Context, key string, value interface{}, ttl time.Duration) error {
	expiration := time.Time{}
	if ttl > 0 {
		expiration = time.Now().Add(ttl)
	}

	item := &CacheItem{
		Key:        key,
		Value:      value,
		Expiration: expiration,
		Metadata:   make(map[string]string),
		createdAt:  time.Now(),
		accessAt:   time.Now(),
		hitCount:   0,
	}

	m.mu.Lock()
	defer m.mu.Unlock()

	// 检查是否需要淘汰
	if m.maxSize > 0 && len(m.items) >= m.maxSize {
		m.evict()
	}

	m.items[key] = item

	if m.enableLRU {
		m.lruList.PushFront(item)
	}

	return nil
}

// Delete 删除缓存
func (m *MemoryCache) Delete(ctx context.Context, key string) error {
	m.mu.Lock()
	defer m.mu.Unlock()

	if item, exists := m.items[key]; exists {
		delete(m.items, key)
		if m.enableLRU {
			m.lruList.Remove(item)
		}
	}

	return nil
}

// Clear 清空缓存
func (m *MemoryCache) Clear() {
	m.mu.Lock()
	defer m.mu.Unlock()

	m.items = make(map[string]*CacheItem)
	m.lruList = NewLRUList()
}

// Cleanup 清理过期缓存
func (m *MemoryCache) Cleanup() int {
	m.mu.Lock()
	defer m.mu.Unlock()

	evicted := 0
	now := time.Now()

	for key, item := range m.items {
		if !item.Expiration.IsZero() && now.After(item.Expiration) {
			delete(m.items, key)
			if m.enableLRU {
				m.lruList.Remove(item)
			}
			evicted++
		}
	}

	return evicted
}

// evict 淘汰缓存项
func (m *MemoryCache) evict() {
	if m.lruList.tail == nil || m.lruList.tail == m.lruList.head {
		return
	}

	// 淘汰LRU链表末尾的项
	item := m.lruList.tail
	if item != nil && item.Key != "" {
		delete(m.items, item.Key)
		m.lruList.Remove(item)
	}
}

// ========== LRUList 实现 ==========

// PushFront 添加到链表头部
func (l *LRUList) PushFront(item *CacheItem) {
	item.prev = nil
	item.next = nil

	if l.head.next == nil {
		// 空链表
		l.head.next = item
		item.prev = l.head
		l.tail = item
	} else {
		// 插入到头部
		item.next = l.head.next
		item.next.prev = item
		l.head.next = item
		item.prev = l.head
	}
	l.size++
}

// MoveToFront 移动到链表头部
func (l *LRUList) MoveToFront(item *CacheItem) {
	if item == l.head.next {
		return // 已经在头部
	}

	l.Remove(item)
	l.PushFront(item)
}

// Remove 从链表中移除
func (l *LRUList) Remove(item *CacheItem) {
	if item.prev != nil {
		item.prev.next = item.next
	}
	if item.next != nil {
		item.next.prev = item.prev
	}

	if item == l.tail {
		l.tail = item.prev
	}

	l.size--
}
