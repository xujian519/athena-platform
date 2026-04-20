// Package vector - 向量检索服务
// 整合Qdrant客户端和缓存，提供高性能向量搜索
package vector

import (
	"context"
	"fmt"
	"sync"

	"log"
)

// VectorSearchService 向量检索服务
type VectorSearchService struct {
	qdrant         *QdrantClient
	cache          *VectorCache
	batchOptimizer *BatchOptimizer
	mu             sync.RWMutex
}

// NewVectorSearchService 创建向量检索服务
func NewVectorSearchService(qdrant *QdrantClient, cache *VectorCache) *VectorSearchService {
	batchCfg := &BatchOptimizerConfig{
		VectorDim:           768,
		SimilarityThreshold: 0.95,
		MaxBatchSize:        100,
		MergeEnabled:        true,
	}

	return &VectorSearchService{
		qdrant:         qdrant,
		cache:          cache,
		batchOptimizer: NewBatchOptimizer(batchCfg),
	}
}

// Search 执行向量搜索（带缓存）
func (s *VectorSearchService) Search(ctx context.Context, req *SearchRequest) (*SearchResponse, error) {
	// 1. 尝试从缓存获取
	results, found := s.cache.Get(ctx, req.Collection, req.Vector)
	if found {
		log.Printf("缓存命中 collection=%s num_results=%d", req.Collection, len(results))

		return &SearchResponse{
			Status:     "cached",
			Result:     make([]SearchResult, len(results)),
			NumResults: len(results),
		}, nil
	}

	// 2. 缓存未命中，执行搜索
	searchResp, err := s.qdrant.Search(ctx, req)
	if err != nil {
		return nil, fmt.Errorf("向量搜索失败: %w", err)
	}

	// 3. 将结果写入缓存
	if len(searchResp.Result) > 0 {
		// 转换[]SearchResult为[]*SearchResult
		resultPtrs := make([]*SearchResult, len(searchResp.Result))
		for i := range searchResp.Result {
			resultPtrs[i] = &searchResp.Result[i]
		}
		if err := s.cache.Set(ctx, req.Collection, req.Vector, resultPtrs); err != nil {
			log.Printf("写入缓存失败 error=%v", err)
		}
	}

	return searchResp, nil
}

// BatchSearch 批量向量搜索（带缓存优化）
func (s *VectorSearchService) BatchSearch(ctx context.Context, reqs []*SearchRequest) ([]*SearchResponse, error) {
	results := make([]*SearchResponse, len(reqs))
	var wg sync.WaitGroup
	var mu sync.Mutex
	var firstErr error

	// 并发搜索（每个请求独立处理）
	for i, req := range reqs {
		wg.Add(1)
		go func(idx int, r *SearchRequest) {
			defer wg.Done()

			result, err := s.Search(ctx, r)
			if err != nil {
				mu.Lock()
				if firstErr == nil {
					firstErr = err
				}
				mu.Unlock()
				return
			}

			mu.Lock()
			results[idx] = result
			mu.Unlock()
		}(i, req)
	}

	wg.Wait()

	if firstErr != nil {
		return nil, firstErr
	}

	// 统计缓存命中率
	cacheStats := s.cache.GetStats()
		hitRate := 0.0
		if cacheStats.Hits+cacheStats.Misses > 0 {
			hitRate = float64(cacheStats.Hits) / float64(cacheStats.Hits+cacheStats.Misses) * 100
		}
	log.Printf("批量搜索完成 total=%d cache_hits=%d cache_misses=%d hit_rate=%.2f",
		len(reqs), cacheStats.Hits, cacheStats.Misses, hitRate)

	return results, nil
}

// GetPerformanceStats 获取性能统计
func (s *VectorSearchService) GetPerformanceStats() map[string]interface{} {
	qdrantStats := s.qdrant.GetStats()
	cacheStats := s.cache.GetStats()

	hitRate := 0.0
	if cacheStats.Hits+cacheStats.Misses > 0 {
		hitRate = float64(cacheStats.Hits) / float64(cacheStats.Hits+cacheStats.Misses) * 100
	}

	return map[string]interface{}{
		"search": map[string]interface{}{
			"total_searches": qdrantStats.TotalSearches,
			"avg_time_ms":    qdrantStats.AvgTime.Milliseconds(),
			"min_time_ms":    qdrantStats.MinTime.Milliseconds(),
			"max_time_ms":    qdrantStats.MaxTime.Milliseconds(),
		},
		"cache": map[string]interface{}{
			"hits":      cacheStats.Hits,
			"misses":    cacheStats.Misses,
			"hit_rate":  hitRate,
			"size":      cacheStats.Size,
			"evictions": cacheStats.Evictions,
		},
	}
}

// ClearCache 清空缓存
func (s *VectorSearchService) ClearCache(ctx context.Context) error {
	return s.cache.Clear(ctx)
}

// Close 关闭服务
func (s *VectorSearchService) Close() error {
	if err := s.cache.Close(); err != nil {
		return err
	}
	return s.qdrant.Close()
}
