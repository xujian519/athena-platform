// Package llm - LLM并发处理模块
// 提供批量并发调用、goroutine池管理
package llm

import (
	"context"
	"fmt"
	"sync"
	"time"

	"log"
)

// ConcurrentConfig 并发配置
type ConcurrentConfig struct {
	MaxConcurrency int           // 最大并发数
	QueueSize      int           // 队列大小
	Timeout        time.Duration // 超时时间
}

// DefaultConcurrentConfig 返回默认并发配置
func DefaultConcurrentConfig() *ConcurrentConfig {
	return &ConcurrentConfig{
		MaxConcurrency: 10,
		QueueSize:      100,
		Timeout:        30 * time.Second,
	}
}

// ConcurrentProcessor 并发处理器
type ConcurrentProcessor struct {
	config     *ConcurrentConfig
	workerPool chan struct{}
	stats      *ConcurrentStats
	mu         sync.RWMutex
}

// ConcurrentStats 并发统计
type ConcurrentStats struct {
	mu             sync.RWMutex
	TotalRequests  uint64
	ProcessedCount uint64
	FailedCount    uint64
	AvgTime        time.Duration
	MaxTime        time.Duration
	MinTime        time.Duration
	ActiveWorkers  int
	QueuedRequests int
}

// NewConcurrentProcessor 创建并发处理器
func NewConcurrentProcessor(cfg *ConcurrentConfig) (*ConcurrentProcessor, error) {
	if cfg == nil {
		cfg = DefaultConcurrentConfig()
	}

	processor := &ConcurrentProcessor{
		config:     cfg,
		workerPool: make(chan struct{}, cfg.MaxConcurrency),
		stats:      &ConcurrentStats{MinTime: time.Hour},
	}

	// 初始化worker池
	for i := 0; i < cfg.MaxConcurrency; i++ {
		processor.workerPool <- struct{}{}
	}

	log.Printf("LLM并发处理器创建成功 max_concurrency=%d queue_size=%d",
		cfg.MaxConcurrency, cfg.QueueSize)

	return processor, nil
}

// BatchChat 批量聊天请求（并发处理）
func (p *ConcurrentProcessor) BatchChat(ctx context.Context, client LLMClient, reqs []*ChatRequest) ([]*ChatResponse, error) {
	if len(reqs) == 0 {
		return nil, fmt.Errorf("请求列表为空")
	}

	startTime := time.Now()

	// 更新统计
	p.stats.mu.Lock()
	p.stats.TotalRequests += uint64(len(reqs))
	p.stats.QueuedRequests = len(reqs)
	p.stats.mu.Unlock()

	log.Printf("开始批量LLM调用 total=%d max_concurrency=%d", len(reqs), p.config.MaxConcurrency)

	// 创建结果通道
	results := make([]*ChatResponse, len(reqs))
	var wg sync.WaitGroup
	var firstErr error
	var mu sync.Mutex
	var errOnce sync.Once

	// 并发处理每个请求
	for i, req := range reqs {
		wg.Add(1)

		// 获取worker
		select {
		case <-p.workerPool:
			// 有可用worker
		case <-ctx.Done():
			// 上下文取消
			mu.Lock()
			if firstErr == nil {
				firstErr = fmt.Errorf("批量处理被取消")
			}
			mu.Unlock()
			wg.Done()
			continue
		}

		// 更新活跃worker数
		p.stats.mu.Lock()
		p.stats.ActiveWorkers++
		p.stats.mu.Unlock()

		// 启动goroutine处理请求
		go func(idx int, r *ChatRequest) {
			defer wg.Done()

			// 处理完成后归还worker
			defer func() {
				p.workerPool <- struct{}{}
				p.stats.mu.Lock()
				p.stats.ActiveWorkers--
				p.stats.QueuedRequests--
				p.stats.mu.Unlock()
			}()

			// 执行请求
			resp, err := client.Chat(ctx, r)
			if err != nil {
				errOnce.Do(func() {
					mu.Lock()
					firstErr = err
					mu.Unlock()

					p.stats.mu.Lock()
					p.stats.FailedCount++
					p.stats.mu.Unlock()
				})
				return
			}

			// 保存结果
			mu.Lock()
			results[idx] = resp
			mu.Unlock()

			p.stats.mu.Lock()
			p.stats.ProcessedCount++
			p.stats.mu.Unlock()

		}(i, req)
	}

	// 等待所有请求完成
	wg.Wait()

	duration := time.Since(startTime)

	// 更新统计
	p.stats.mu.Lock()
	if duration > p.stats.MaxTime {
		p.stats.MaxTime = duration
	}
	if duration < p.stats.MinTime {
		p.stats.MinTime = duration
	}
	p.stats.AvgTime = time.Duration(
		(int64(p.stats.AvgTime)*int64(p.stats.ProcessedCount-1) + int64(duration)) /
			int64(p.stats.ProcessedCount))
	p.stats.mu.Unlock()

	if firstErr != nil {
		return nil, firstErr
	}

	log.Printf("批量LLM调用完成 total=%d duration=%v avg_time_ms=%.2f",
		len(reqs), duration, float64(duration.Milliseconds())/float64(len(reqs)))

	return results, nil
}

// BatchChatWithRetry 批量聊天请求（带重试）
func (p *ConcurrentProcessor) BatchChatWithRetry(ctx context.Context, client LLMClient, reqs []*ChatRequest, maxRetries int) ([]*ChatResponse, error) {
	var allResults []*ChatResponse
	var failedIndices []int
	var failedReqs []*ChatRequest

	// 第一次尝试
	results, err := p.BatchChat(ctx, client, reqs)
	if err == nil {
		return results, nil
	}

	// 收集失败的请求
	for i, resp := range results {
		if resp == nil {
			failedIndices = append(failedIndices, i)
			failedReqs = append(failedReqs, reqs[i])
		} else {
			allResults = append(allResults, resp)
		}
	}

	// 重试失败的请求
	for retry := 1; retry <= maxRetries && len(failedReqs) > 0; retry++ {
		log.Printf("重试失败的LLM请求 retry=%d failed=%d", retry, len(failedReqs))

		retryResults, err := p.BatchChat(ctx, client, failedReqs)
		if err != nil {
			continue
		}

		// 更新结果
		var newFailedIndices []int
		var newFailedReqs []*ChatRequest

		for i, resp := range retryResults {
			if resp == nil {
				newFailedIndices = append(newFailedIndices, failedIndices[i])
				newFailedReqs = append(newFailedReqs, failedReqs[i])
			} else {
				allResults = append(allResults, resp)
			}
		}

		failedIndices = newFailedIndices
		failedReqs = newFailedReqs
	}

	if len(failedReqs) > 0 {
		return allResults, fmt.Errorf("%d个请求失败", len(failedReqs))
	}

	return allResults, nil
}

// StreamChat 流式聊天（并发处理多个流）
func (p *ConcurrentProcessor) StreamChat(ctx context.Context, client LLMClient, reqs []*ChatRequest, callback func(int, string)) error {
	// TODO: 实现流式并发处理
	return fmt.Errorf("流式处理尚未实现")
}

// GetStats 获取并发统计
func (p *ConcurrentProcessor) GetStats() *ConcurrentStats {
	p.stats.mu.RLock()
	defer p.stats.mu.RUnlock()

	return &ConcurrentStats{
		TotalRequests:  p.stats.TotalRequests,
		ProcessedCount: p.stats.ProcessedCount,
		FailedCount:    p.stats.FailedCount,
		AvgTime:        p.stats.AvgTime,
		MaxTime:        p.stats.MaxTime,
		MinTime:        p.stats.MinTime,
		ActiveWorkers:  p.stats.ActiveWorkers,
		QueuedRequests: p.stats.QueuedRequests,
	}
}

// ResetStats 重置统计
func (p *ConcurrentProcessor) ResetStats() {
	p.stats.mu.Lock()
	defer p.stats.mu.Unlock()

	p.stats = &ConcurrentStats{
		MinTime: time.Hour,
	}
}

// Resize 调整并发池大小
func (p *ConcurrentProcessor) Resize(newSize int) error {
	if newSize <= 0 {
		return fmt.Errorf("并发数必须大于0")
	}

	p.mu.Lock()
	defer p.mu.Unlock()

	// 计算差值
	currentSize := cap(p.workerPool)
	diff := newSize - currentSize

	if diff > 0 {
		// 增加worker
		for i := 0; i < diff; i++ {
			p.workerPool <- struct{}{}
		}
	} else if diff < 0 {
		// 减少worker（等待现有worker完成）
		for i := 0; i < -diff; i++ {
			<-p.workerPool
		}
	}

	p.config.MaxConcurrency = newSize

	log.Printf("并发池大小已调整 old_size=%d new_size=%d", currentSize, newSize)

	return nil
}

// Close 关闭处理器
func (p *ConcurrentProcessor) Close() error {
	// 等待所有worker完成
	for len(p.workerPool) < cap(p.workerPool) {
		time.Sleep(100 * time.Millisecond)
	}

	close(p.workerPool)

	log.Printf("并发处理器已关闭")

	return nil
}

// OptimizedBatchChat 优化的批量聊天（自动分批）
func (p *ConcurrentProcessor) OptimizedBatchChat(ctx context.Context, client LLMClient, reqs []*ChatRequest) ([]*ChatResponse, error) {
	if len(reqs) == 0 {
		return nil, fmt.Errorf("请求列表为空")
	}

	// 如果请求数量小于最大并发数，直接处理
	if len(reqs) <= p.config.MaxConcurrency {
		return p.BatchChat(ctx, client, reqs)
	}

	// 分批处理
	batchSize := p.config.MaxConcurrency
	var allResults []*ChatResponse

	for i := 0; i < len(reqs); i += batchSize {
		end := i + batchSize
		if end > len(reqs) {
			end = len(reqs)
		}

		batch := reqs[i:end]
		results, err := p.BatchChat(ctx, client, batch)
		if err != nil {
			return nil, fmt.Errorf("批次[%d:%d]处理失败: %w", i, end, err)
		}

		allResults = append(allResults, results...)

		log.Printf("批次处理完成 batch_start=%d batch_end=%d batch_size=%d", i, end, len(batch))
	}

	return allResults, nil
}
