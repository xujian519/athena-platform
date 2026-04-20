// Package vector - 向量检索批量处理优化
package vector

import (
	"context"
	"fmt"
	"math"
	"sync"
	"time"

	"log"
)

// BatchOptimizer 批量优化器
type BatchOptimizer struct {
	vectorDim           int
	similarityThreshold float64
	maxBatchSize        int
	mergeEnabled        bool
}

// BatchOptimizerConfig 批量优化器配置
type BatchOptimizerConfig struct {
	VectorDim           int     // 向量维度
	SimilarityThreshold float64 // 相似度阈值（用于请求合并）
	MaxBatchSize        int     // 最大批量大小
	MergeEnabled        bool    // 是否启用请求合并
}

// NewBatchOptimizer 创建批量优化器
func NewBatchOptimizer(cfg *BatchOptimizerConfig) *BatchOptimizer {
	if cfg == nil {
		cfg = &BatchOptimizerConfig{
			VectorDim:           1024, // 默认BGE-M3维度
			SimilarityThreshold: 0.95, // 95%相似度
			MaxBatchSize:        100,
			MergeEnabled:        true,
		}
	}

	return &BatchOptimizer{
		vectorDim:           cfg.VectorDim,
		similarityThreshold: cfg.SimilarityThreshold,
		maxBatchSize:        cfg.MaxBatchSize,
		mergeEnabled:        cfg.MergeEnabled,
	}
}

// BatchGroup 批量分组
type BatchGroup struct {
	Requests  []*SearchRequest
	CacheKeys []string
	Priority  int
	CreatedAt time.Time
}

// OptimizedBatchSearch 优化的批量搜索
func (s *VectorSearchService) OptimizedBatchSearch(ctx context.Context, reqs []*SearchRequest) ([]*SearchResponse, error) {
	if len(reqs) == 0 {
		return nil, fmt.Errorf("请求列表为空")
	}

	startTime := time.Now()

	// 1. 请求去重和合并
	optimizedReqs, indexMap := s.deduplicateRequests(ctx, reqs)

	// 2. 智能分组
	groups := s.groupRequests(optimizedReqs)

	log.Printf("批量搜索优化 original_requests=%d deduplicated_requests=%d groups=%d",
		len(reqs), len(optimizedReqs), len(groups))

	// 3. 并发处理每个分组
	optimizedResults := make([]*SearchResponse, len(optimizedReqs))
	var wg sync.WaitGroup
	var mu sync.Mutex
	var firstErr error

	for _, group := range groups {
		wg.Add(1)
		go func(g *BatchGroup) {
			defer wg.Done()

			// 处理分组中的所有请求
			groupResults := s.processBatchGroup(ctx, g)

			// 将结果映射到优化后的请求索引
			mu.Lock()
			for i, result := range groupResults {
				if i < len(g.Requests) {
					optimizedResults[i] = result
				}
			}
			mu.Unlock()
		}(group)
	}

	wg.Wait()

	if firstErr != nil {
		return nil, firstErr
	}

	// 4. 将优化后的结果映射回原始请求
	results := make([]*SearchResponse, len(reqs))
	for originalIdx, optimizedIdx := range indexMap {
		if optimizedIdx < len(optimizedResults) {
			results[originalIdx] = optimizedResults[optimizedIdx]
		}
	}

	duration := time.Since(startTime)

	log.Printf("优化批量搜索完成 total_requests=%d total_duration=%v avg_time_ms=%.2f",
		len(reqs), duration, float64(duration.Milliseconds())/float64(len(reqs)))

	return results, nil
}

// deduplicateRequests 请求去重
func (s *VectorSearchService) deduplicateRequests(ctx context.Context, reqs []*SearchRequest) ([]*SearchRequest, map[int]int) {
	// 使用map存储已见过的向量
	seenVectors := make(map[string]int)
	optimizedReqs := make([]*SearchRequest, 0, len(reqs))
	indexMap := make(map[int]int) // 原始索引 -> 优化后索引

	for i, req := range reqs {
		// 生成向量哈希作为去重键
		cacheKey := s.cache.generateCacheKey(req.Collection, req.Vector)

		if existingIdx, found := seenVectors[cacheKey]; found {
			// 发现重复请求，记录映射
			indexMap[i] = existingIdx
			log.Printf("发现重复请求 original_idx=%d existing_idx=%d", i, existingIdx)
		} else {
			// 新请求，添加到优化列表
			seenVectors[cacheKey] = len(optimizedReqs)
			indexMap[i] = len(optimizedReqs)
			optimizedReqs = append(optimizedReqs, req)
		}
	}

	log.Printf("请求去重完成 original=%d optimized=%d duplicates=%d",
		len(reqs), len(optimizedReqs), len(reqs)-len(optimizedReqs))

	return optimizedReqs, indexMap
}

// groupRequests 智能分组请求
func (s *VectorSearchService) groupRequests(reqs []*SearchRequest) []*BatchGroup {
	groups := make([]*BatchGroup, 0)

	// 按集合名称分组
	collectionGroups := make(map[string][]*SearchRequest)
	for _, req := range reqs {
		collectionGroups[req.Collection] = append(collectionGroups[req.Collection], req)
	}

	// 为每个集合创建分组
	for _, collectionReqs := range collectionGroups {
		// 如果请求过多，拆分为多个子组
		maxGroupSize := 50 // 每组最多50个请求

		for i := 0; i < len(collectionReqs); i += maxGroupSize {
			end := i + maxGroupSize
			if end > len(collectionReqs) {
				end = len(collectionReqs)
			}

			group := &BatchGroup{
				Requests:  collectionReqs[i:end],
				CacheKeys: make([]string, len(collectionReqs[i:end])),
				Priority:  calculatePriority(collectionReqs[i:end]),
				CreatedAt: time.Now(),
			}

			// 预先生成缓存键
			for j, req := range group.Requests {
				group.CacheKeys[j] = s.cache.generateCacheKey(req.Collection, req.Vector)
			}

			groups = append(groups, group)
		}
	}

	return groups
}

// processBatchGroup 处理批量分组
func (s *VectorSearchService) processBatchGroup(ctx context.Context, group *BatchGroup) []*SearchResponse {
	results := make([]*SearchResponse, len(group.Requests))

	// 1. 尝试从缓存获取
	var uncachedIndices []int
	var uncachedReqs []*SearchRequest

	for i, req := range group.Requests {
		cachedResults, found := s.cache.Get(ctx, req.Collection, req.Vector)
		if found {
			// 缓存返回[]*SearchResult，需要转换为[]SearchResult
			resultValues := make([]SearchResult, len(cachedResults))
			for j, ptr := range cachedResults {
				if ptr != nil {
					resultValues[j] = *ptr
				}
			}

			results[i] = &SearchResponse{
				Status:     "cached",
				Result:     resultValues,
				NumResults: len(cachedResults),
			}
		} else {
			uncachedIndices = append(uncachedIndices, i)
			uncachedReqs = append(uncachedReqs, req)
		}
	}

	// 2. 如果全部命中缓存，直接返回
	if len(uncachedReqs) == 0 {
		log.Printf("批量分组全部缓存命中 group_size=%d", len(group.Requests))
		return results
	}

	// 3. 并发处理未缓存的请求
	var wg sync.WaitGroup
	var mu sync.Mutex
	var firstErr error
	var errOnce sync.Once

	for i, req := range uncachedReqs {
		wg.Add(1)
		go func(idx int, r *SearchRequest) {
			defer wg.Done()

			// 执行搜索
			searchResp, err := s.qdrant.Search(ctx, r)
			if err != nil {
				errOnce.Do(func() {
					firstErr = fmt.Errorf("向量搜索失败: %w", err)
				})
				return
			}

			// 写入缓存 - SearchResponse.Result是[]SearchResult，需要转换为[]*SearchResult
			if len(searchResp.Result) > 0 {
				resultPtrs := make([]*SearchResult, len(searchResp.Result))
				for j := range searchResp.Result {
					resultPtrs[j] = &searchResp.Result[j]
				}
				if err := s.cache.Set(ctx, r.Collection, r.Vector, resultPtrs); err != nil {
					log.Printf("写入缓存失败 error=%v", err)
				}
			}

			// 保存结果
			mu.Lock()
			results[uncachedIndices[idx]] = searchResp
			mu.Unlock()
		}(i, req)
	}

	wg.Wait()

	if firstErr != nil {
		log.Printf("批量分组部分失败 failed=%d error=%v", len(uncachedReqs), firstErr)
		return nil
	}

	log.Printf("批量分组处理完成 total=%d cached=%d searched=%d",
		len(group.Requests), len(group.Requests)-len(uncachedReqs), len(uncachedReqs))

	return results
}

// calculatePriority 计算请求优先级
func calculatePriority(reqs []*SearchRequest) int {
	priority := 0

	for _, req := range reqs {
		// 根据Limit调整优先级
		if req.Limit > 10 {
			priority += 10
		} else if req.Limit > 5 {
			priority += 5
		}

		// 根据Threshold调整优先级
		if req.Threshold > 0.8 {
			priority += 5
		} else if req.Threshold > 0.5 {
			priority += 3
		}
	}

	return priority
}

// CalculateSimilarity 计算两个向量的余弦相似度
func (bo *BatchOptimizer) CalculateSimilarity(vec1, vec2 []float64) float64 {
	if len(vec1) != len(vec2) {
		return 0.0
	}

	var dotProduct, norm1, norm2 float64

	for i := 0; i < len(vec1); i++ {
		dotProduct += vec1[i] * vec2[i]
		norm1 += vec1[i] * vec1[i]
		norm2 += vec2[i] * vec2[i]
	}

	if norm1 == 0 || norm2 == 0 {
		return 0.0
	}

	return dotProduct / (math.Sqrt(norm1) * math.Sqrt(norm2))
}

// MergeSimilarVectors 合并相似向量请求
func (bo *BatchOptimizer) MergeSimilarVectors(reqs []*SearchRequest) []*SearchRequest {
	if !bo.mergeEnabled {
		return reqs
	}

	merged := make([]*SearchRequest, 0, len(reqs))
	mergedIndices := make(map[int]bool)

	for i := 0; i < len(reqs); i++ {
		if mergedIndices[i] {
			continue
		}

		currentReq := reqs[i]
		similarIndices := []int{i}

		// 查找相似向量
		for j := i + 1; j < len(reqs); j++ {
			if mergedIndices[j] {
				continue
			}

			similarity := bo.CalculateSimilarity(currentReq.Vector, reqs[j].Vector)
			if similarity >= bo.similarityThreshold {
				similarIndices = append(similarIndices, j)
				mergedIndices[j] = true
			}
		}

		// 如果有相似向量，合并请求
		if len(similarIndices) > 1 {
			// 使用第一个请求作为代表，但增加Limit
			mergedReq := *currentReq
			mergedReq.Limit = currentReq.Limit * len(similarIndices)
			merged = append(merged, &mergedReq)

			log.Printf("合并相似向量请求 merged_count=%d similarity_threshold=%.2f",
				len(similarIndices), bo.similarityThreshold)
		} else {
			merged = append(merged, currentReq)
		}

		mergedIndices[i] = true
	}

	log.Printf("相似向量合并完成 original=%d merged=%d saved=%d",
		len(reqs), len(merged), len(reqs)-len(merged))

	return merged
}

// SmartBatchStrategy 智能批处理策略
type SmartBatchStrategy struct {
	maxBatchSize    int
	maxWaitTime     time.Duration
	minBatchSize    int
	priorityEnabled bool
}

// NewSmartBatchStrategy 创建智能批处理策略
func NewSmartBatchStrategy() *SmartBatchStrategy {
	return &SmartBatchStrategy{
		maxBatchSize:    100,
		maxWaitTime:     10 * time.Millisecond,
		minBatchSize:    10,
		priorityEnabled: true,
	}
}

// OptimizeBatchSize 优化批量大小
func (sbs *SmartBatchStrategy) OptimizeBatchSize(reqs []*SearchRequest) int {
	size := len(reqs)

	// 如果请求数少于最小批量，不拆分
	if size <= sbs.minBatchSize {
		return size
	}

	// 如果请求数超过最大批量，拆分为多个批次
	if size > sbs.maxBatchSize {
		return sbs.maxBatchSize
	}

	// 动态调整批量大小
	// 考虑因素：系统负载、时间约束、资源可用性
	optimalSize := int(math.Sqrt(float64(size))) * 10

	// 限制在合理范围内
	if optimalSize < sbs.minBatchSize {
		optimalSize = sbs.minBatchSize
	}
	if optimalSize > sbs.maxBatchSize {
		optimalSize = sbs.maxBatchSize
	}

	return optimalSize
}

// BatchSearchWithStrategy 使用策略进行批量搜索
func (s *VectorSearchService) BatchSearchWithStrategy(ctx context.Context, reqs []*SearchRequest, strategy *SmartBatchStrategy) ([]*SearchResponse, error) {
	if len(reqs) == 0 {
		return nil, fmt.Errorf("请求列表为空")
	}

	if strategy == nil {
		strategy = NewSmartBatchStrategy()
	}

	// 优化批量大小
	batchSize := strategy.OptimizeBatchSize(reqs)

	// 拆分为多个批次
	var allResults []*SearchResponse

	for i := 0; i < len(reqs); i += batchSize {
		end := i + batchSize
		if end > len(reqs) {
			end = len(reqs)
		}

		batch := reqs[i:end]
		results, err := s.OptimizedBatchSearch(ctx, batch)
		if err != nil {
			return nil, fmt.Errorf("批次[%d:%d]处理失败: %w", i, end, err)
		}

		allResults = append(allResults, results...)
	}

	return allResults, nil
}
