package cache

import (
	"encoding/json"
	"fmt"
	"os"
	"path/filepath"
	"sync"
	"time"
)

// PersistentCache L3持久化缓存
type PersistentCache struct {
	basePath string
	items    map[string]*CacheItem
	mutex    sync.RWMutex
}

// NewPersistentCache 创建持久化缓存
func NewPersistentCache() *PersistentCache {
	basePath := filepath.Join(os.TempDir(), "athena_gateway_cache")

	cache := &PersistentCache{
		basePath: basePath,
		items:    make(map[string]*CacheItem),
	}

	// 创建缓存目录
	if err := os.MkdirAll(basePath, 0755); err != nil {
		fmt.Printf("创建缓存目录失败: %v\n", err)
		return cache
	}

	// 加载现有缓存
	cache.loadFromDisk()

	// 启动定期保存
	go cache.periodicSave()

	return cache
}

// Set 设置缓存项
func (c *PersistentCache) Set(key string, item *CacheItem) error {
	c.mutex.Lock()
	defer c.mutex.Unlock()

	c.items[key] = item
	return c.saveItemToDisk(key, item)
}

// Get 获取缓存项
func (c *PersistentCache) Get(key string) (*CacheItem, error) {
	c.mutex.RLock()
	defer c.mutex.RUnlock()

	item, exists := c.items[key]
	if !exists {
		// 尝试从磁盘加载
		if item, err := c.loadItemFromDisk(key); err == nil {
			c.items[key] = item
			return item, nil
		}
		return nil, ErrCacheNotFound
	}

	// 检查内存中的项是否过期
	if item.IsExpired() {
		delete(c.items, key)
		c.removeItemFromDisk(key)
		return nil, ErrCacheNotFound
	}

	return item, nil
}

// Update 更新缓存项
func (c *PersistentCache) Update(key string, item *CacheItem) error {
	c.mutex.Lock()
	defer c.mutex.Unlock()

	if _, exists := c.items[key]; !exists {
		return ErrCacheNotFound
	}

	c.items[key] = item
	return c.saveItemToDisk(key, item)
}

func (c *PersistentCache) Delete(key string) error {
	c.mutex.Lock()
	defer c.mutex.Unlock()

	if _, exists := c.items[key]; !exists {
		return ErrCacheNotFound
	}

	delete(c.items, key)
	return c.removeItemFromDisk(key)
}

// Clear 清空缓存
func (c *PersistentCache) Clear() error {
	c.mutex.Lock()
	defer c.mutex.Unlock()

	c.items = make(map[string]*CacheItem)

	// 清空磁盘缓存
	if err := os.RemoveAll(c.basePath); err != nil {
		return fmt.Errorf("清空磁盘缓存失败: %w", err)
	}

	return os.MkdirAll(c.basePath, 0755)
}

// Stats 获取统计信息
func (c *PersistentCache) Stats() map[string]interface{} {
	c.mutex.RLock()
	defer c.mutex.RUnlock()

	var totalSize int64
	expiredCount := 0

	for _, item := range c.items {
		if item.IsExpired() {
			expiredCount++
		}
		totalSize += int64(len(item.Key) + 100) // 简化估算
	}

	var diskSize int64
	if fileInfos, err := os.ReadDir(c.basePath); err == nil {
		for _, fileInfo := range fileInfos {
			if fileInfo.IsDir() {
				continue
			}
			if fileInfoInfo, err := fileInfo.Info(); err == nil {
				diskSize += fileInfoInfo.Size()
			}
		}
	}

	return map[string]interface{}{
		"items_count":   len(c.items),
		"expired_count": expiredCount,
		"total_memory":  totalSize,
		"disk_usage":    diskSize,
		"cache_path":    c.basePath,
	}
}

// Close 关闭缓存
func (c *PersistentCache) Close() error {
	return c.saveToDisk()
}

// saveItemToDisk 保存单项到磁盘
func (c *PersistentCache) saveItemToDisk(key string, item *CacheItem) error {
	data, err := json.Marshal(item)
	if err != nil {
		return fmt.Errorf("序列化缓存项失败: %w", err)
	}

	filename := filepath.Join(c.basePath, key+".cache")
	return os.WriteFile(filename, data, 0644)
}

// loadItemFromDisk 从磁盘加载单项
func (c *PersistentCache) loadItemFromDisk(key string) (*CacheItem, error) {
	filename := filepath.Join(c.basePath, key+".cache")

	data, err := os.ReadFile(filename)
	if err != nil {
		return nil, err
	}

	var item CacheItem
	if err := json.Unmarshal(data, &item); err != nil {
		return nil, err
	}

	// 检查是否过期
	if item.IsExpired() {
		c.removeItemFromDisk(key)
		return nil, ErrCacheNotFound
	}

	return &item, nil
}

// removeItemFromDisk 从磁盘删除单项
func (c *PersistentCache) removeItemFromDisk(key string) error {
	filename := filepath.Join(c.basePath, key+".cache")
	return os.Remove(filename)
}

// saveToDisk 保存所有缓存到磁盘
func (c *PersistentCache) saveToDisk() error {
	c.mutex.RLock()
	defer c.mutex.RUnlock()

	for key, item := range c.items {
		if err := c.saveItemToDisk(key, item); err != nil {
			return err
		}
	}

	return nil
}

func (c *PersistentCache) loadFromDisk() {
	fileInfos, err := os.ReadDir(c.basePath)
	if err != nil {
		return
	}

	for _, fileInfo := range fileInfos {
		if fileInfo.IsDir() || filepath.Ext(fileInfo.Name()) != ".cache" {
			continue
		}

		key := fileInfo.Name()[:len(fileInfo.Name())-6]
		if item, err := c.loadItemFromDisk(key); err == nil {
			c.items[key] = item
		}
	}
}

// periodicSave 定期保存
func (c *PersistentCache) periodicSave() {
	ticker := time.NewTicker(5 * time.Minute)
	defer ticker.Stop()

	for range ticker.C {
		if err := c.saveToDisk(); err != nil {
			fmt.Printf("定期保存缓存失败: %v\n", err)
		}
	}
}
