// Package llm - LLM统一服务层
// 整合客户端、路由、缓存、并发处理
package llm

import (
	"context"
	"fmt"
	"sync"

	"log"
)

// LLMService LLM统一服务
type LLMService struct {
	client    LLMClient
	router    *SmartRouter
	cache     *LLMCache
	processor *ConcurrentProcessor
	mu        sync.RWMutex
	stats     *LLMServiceStats
	enabled   bool
}

// LLMServiceStats 服务统计
type LLMServiceStats struct {
	mu              sync.RWMutex
	TotalRequests   uint64
	CacheHits       uint64
	CacheMisses     uint64
	TotalTokens     uint64
	TotalCost       float64
	CostSaved       float64
	EconomyUsed     uint64
	BalancedUsed    uint64
	PremiumUsed     uint64
	AvgResponseTime float64
}

// LLMServiceConfig 服务配置
type LLMServiceConfig struct {
	ClientConfig     *Config
	RouterConfig     *SmartRouter
	CacheConfig      *LLMCacheConfig
	ConcurrentConfig *ConcurrentConfig
	Enabled          bool
}

// DefaultLLMServiceConfig 返回默认服务配置
func DefaultLLMServiceConfig() *LLMServiceConfig {
	return &LLMServiceConfig{
		ClientConfig: &Config{
			BaseURL:    "https://api.openai.com/v1",
			APIKey:     "",
			Model:      "gpt-3.5-turbo",
			Timeout:    30,
			MaxRetries: 3,
		},
		CacheConfig:      DefaultLLMCacheConfig(),
		ConcurrentConfig: DefaultConcurrentConfig(),
		Enabled:          true,
	}
}

// NewLLMService 创建LLM服务
func NewLLMService(cfg *LLMServiceConfig) (*LLMService, error) {
	if cfg == nil {
		cfg = DefaultLLMServiceConfig()
	}

	service := &LLMService{
		stats:   &LLMServiceStats{},
		enabled: cfg.Enabled,
	}

	// 1. 创建HTTP客户端
	client, err := NewHTTPClient(cfg.ClientConfig)
	if err != nil {
		return nil, fmt.Errorf("创建LLM客户端失败: %w", err)
	}
	service.client = client

	// 2. 创建智能路由器
	service.router = NewSmartRouter()
	if cfg.RouterConfig != nil {
		// 使用自定义路由配置
		service.router = cfg.RouterConfig
	}

	// 3. 创建缓存
	cache, err := NewLLMCache(cfg.CacheConfig)
	if err != nil {
		return nil, fmt.Errorf("创建缓存失败: %w", err)
	}
	service.cache = cache

	// 4. 创建并发处理器
	processor, err := NewConcurrentProcessor(cfg.ConcurrentConfig)
	if err != nil {
		return nil, fmt.Errorf("创建并发处理器失败: %w", err)
	}
	service.processor = processor

	log.Printf("LLM统一服务创建成功 enabled=%v cache=%v max_concurrency=%d",
		service.enabled, cache != nil, cfg.ConcurrentConfig.MaxConcurrency)

	return service, nil
}

// Chat 执行聊天请求（自动路由+缓存）
func (s *LLMService) Chat(ctx context.Context, req *ChatRequest) (*ChatResponse, error) {
	if !s.enabled {
		return nil, fmt.Errorf("LLM服务未启用")
	}

	// 提取prompt用于缓存和路由
	prompt := s.extractPrompt(req)

	// 1. 尝试从缓存获取
	cachedResp, found := s.cache.Get(ctx, prompt, req.Model)
	if found {
		s.stats.mu.Lock()
		s.stats.CacheHits++
		s.stats.TotalRequests++
		s.stats.mu.Unlock()

		return cachedResp, nil
	}

	// 2. 缓存未命中，使用智能路由选择模型
	modelConfig, err := s.router.SelectModel(ctx, prompt, "")
	if err != nil {
		return nil, fmt.Errorf("模型选择失败: %w", err)
	}

	// 更新请求模型
	req.Model = modelConfig.ModelName

	// 3. 调用LLM
	resp, err := s.client.Chat(ctx, req)
	if err != nil {
		s.stats.mu.Lock()
		s.stats.CacheMisses++
		s.stats.mu.Unlock()

		return nil, fmt.Errorf("LLM调用失败: %w", err)
	}

	// 4. 写入缓存
	if err := s.cache.Set(ctx, prompt, req.Model, resp, modelConfig.CostPer1K); err != nil {
		log.Printf("写入缓存失败 error=%v", err)
	}

	// 5. 更新统计
	s.stats.mu.Lock()
	s.stats.TotalRequests++
	s.stats.CacheMisses++
	s.stats.TotalTokens += uint64(resp.Usage.TotalTokens)
	s.stats.TotalCost += float64(resp.Usage.TotalTokens) * modelConfig.CostPer1K / 1000.0

	switch modelConfig.Tier {
	case TierEconomy:
		s.stats.EconomyUsed++
	case TierBalanced:
		s.stats.BalancedUsed++
	case TierPremium:
		s.stats.PremiumUsed++
	}
	s.stats.mu.Unlock()

	log.Printf("LLM请求完成 model=%s tier=%s tokens=%d", req.Model, string(modelConfig.Tier), resp.Usage.TotalTokens)

	return resp, nil
}

// BatchChat 批量聊天请求（自动并发）
func (s *LLMService) BatchChat(ctx context.Context, reqs []*ChatRequest) ([]*ChatResponse, error) {
	if !s.enabled {
		return nil, fmt.Errorf("LLM服务未启用")
	}

	// 使用并发处理器
	return s.processor.BatchChat(ctx, s.client, reqs)
}

// ChatWithModel 使用指定模型聊天（跳过智能路由）
func (s *LLMService) ChatWithModel(ctx context.Context, req *ChatRequest, tier ModelTier) (*ChatResponse, error) {
	if !s.enabled {
		return nil, fmt.Errorf("LLM服务未启用")
	}

	// 提取prompt
	prompt := s.extractPrompt(req)

	// 1. 尝试从缓存获取
	cachedResp, found := s.cache.Get(ctx, prompt, req.Model)
	if found {
		return cachedResp, nil
	}

	// 2. 使用指定模型层级
	modelConfig, err := s.router.SelectModel(ctx, prompt, tier)
	if err != nil {
		return nil, fmt.Errorf("模型选择失败: %w", err)
	}

	req.Model = modelConfig.ModelName

	// 3. 调用LLM
	resp, err := s.client.Chat(ctx, req)
	if err != nil {
		return nil, fmt.Errorf("LLM调用失败: %w", err)
	}

	// 4. 写入缓存
	if err := s.cache.Set(ctx, prompt, req.Model, resp, modelConfig.CostPer1K); err != nil {
		log.Printf("写入缓存失败 error=%v", err)
	}

	return resp, nil
}

// ExtractPrompt 提取提示词
func (s *LLMService) extractPrompt(req *ChatRequest) string {
	if len(req.Messages) == 0 {
		return ""
	}

	// 提取最后一条消息作为prompt
	lastMsg := req.Messages[len(req.Messages)-1]
	return lastMsg.Content
}

// GetStats 获取服务统计
func (s *LLMService) GetStats() map[string]interface{} {
	s.stats.mu.RLock()
	defer s.stats.mu.RUnlock()

	clientStats := s.client.(*HTTPClient).GetStats()
	routerStats := s.router.GetStats()
	cacheStats := s.cache.GetStats()
	processorStats := s.processor.GetStats()

	return map[string]interface{}{
		"service": map[string]interface{}{
			"total_requests":    s.stats.TotalRequests,
			"cache_hits":        s.stats.CacheHits,
			"cache_misses":      s.stats.CacheMisses,
			"total_tokens":      s.stats.TotalTokens,
			"total_cost":        s.stats.TotalCost,
			"cost_saved":        s.stats.CostSaved,
			"avg_response_time": s.stats.AvgResponseTime,
		},
		"client": map[string]interface{}{
			"total_requests":      clientStats.TotalRequests,
			"successful_requests": clientStats.SuccessfulRequests,
			"failed_requests":     clientStats.FailedRequests,
			"total_tokens":        clientStats.TotalTokens,
			"total_cost":          clientStats.TotalCost,
			"avg_time_ms":         clientStats.AvgTime.Milliseconds(),
		},
		"router": map[string]interface{}{
			"total_requests":  routerStats.TotalRequests,
			"economy_count":   routerStats.EconomyCount,
			"balanced_count":  routerStats.BalancedCount,
			"premium_count":   routerStats.PremiumCount,
			"avg_complexity":  routerStats.AvgComplexity,
			"manual_override": routerStats.ManualOverride,
		},
		"cache": map[string]interface{}{
			"hits":       cacheStats.Hits,
			"misses":     cacheStats.Misses,
			"hit_rate":   cacheStats.HitRate,
			"size":       cacheStats.Size,
			"total_cost": cacheStats.TotalCost,
		},
		"processor": map[string]interface{}{
			"total_requests":  processorStats.TotalRequests,
			"processed_count": processorStats.ProcessedCount,
			"failed_count":    processorStats.FailedCount,
			"active_workers":  processorStats.ActiveWorkers,
			"avg_time_ms":     processorStats.AvgTime.Milliseconds(),
		},
	}
}

// GetRouter 获取路由器
func (s *LLMService) GetRouter() *SmartRouter {
	return s.router
}

// GetCache 获取缓存
func (s *LLMService) GetCache() *LLMCache {
	return s.cache
}

// GetProcessor 获取并发处理器
func (s *LLMService) GetProcessor() *ConcurrentProcessor {
	return s.processor
}

// ClearCache 清空缓存
func (s *LLMService) ClearCache(ctx context.Context) error {
	return s.cache.Clear(ctx)
}

// ResetStats 重置统计
func (s *LLMService) ResetStats() {
	s.stats.mu.Lock()
	s.stats = &LLMServiceStats{}
	s.stats.mu.Unlock()

	s.router.ResetStats()
	s.processor.ResetStats()
}

// Enable 启用服务
func (s *LLMService) Enable() {
	s.mu.Lock()
	defer s.mu.Unlock()
	s.enabled = true

	log.Printf("LLM服务已启用")
}

// Disable 禁用服务
func (s *LLMService) Disable() {
	s.mu.Lock()
	defer s.mu.Unlock()
	s.enabled = false

	log.Printf("LLM服务已禁用")
}

// IsEnabled 检查服务是否启用
func (s *LLMService) IsEnabled() bool {
	s.mu.RLock()
	defer s.mu.RUnlock()
	return s.enabled
}

// WarmupCache 预热缓存
func (s *LLMService) WarmupCache(ctx context.Context, prompts []string, model string) error {
	return s.cache.Warmup(ctx, prompts, model, s.client)
}

// ExportMetrics 导出指标（用于监控）
func (s *LLMService) ExportMetrics() map[string]interface{} {
	stats := s.GetStats()

	// 添加计算指标
	cacheHitRate := 0.0
	if cacheStats, ok := stats["cache"].(map[string]interface{}); ok {
		if hits, ok := cacheStats["hits"].(uint64); ok {
			if misses, ok := cacheStats["misses"].(uint64); ok {
				total := hits + misses
				if total > 0 {
					cacheHitRate = float64(hits) / float64(total) * 100
				}
			}
		}
	}

	costSavingRate := 0.0
	if serviceStats, ok := stats["service"].(map[string]interface{}); ok {
		if totalCost, ok := serviceStats["total_cost"].(float64); ok {
			if costSaved, ok := serviceStats["cost_saved"].(float64); ok {
				if totalCost > 0 {
					costSavingRate = costSaved / totalCost * 100
				}
			}
		}
	}

	return map[string]interface{}{
		"cache_hit_rate":      cacheHitRate,
		"cost_saving_rate":    costSavingRate,
		"total_requests":      stats["service"].(map[string]interface{})["total_requests"],
		"total_tokens":        stats["service"].(map[string]interface{})["total_tokens"],
		"economy_usage_rate":  calculateEconomyRate(stats),
		"balanced_usage_rate": calculateBalancedRate(stats),
		"premium_usage_rate":  calculatePremiumRate(stats),
	}
}

// calculateEconomyRate 计算经济型使用率
func calculateEconomyRate(stats map[string]interface{}) float64 {
	routerStats, ok := stats["router"].(map[string]interface{})
	if !ok {
		return 0.0
	}

	total, ok := routerStats["total_requests"].(uint64)
	if !ok || total == 0 {
		return 0.0
	}

	economy, ok := routerStats["economy_count"].(uint64)
	if !ok {
		return 0.0
	}

	return float64(economy) / float64(total) * 100
}

// calculateBalancedRate 计算平衡型使用率
func calculateBalancedRate(stats map[string]interface{}) float64 {
	routerStats, ok := stats["router"].(map[string]interface{})
	if !ok {
		return 0.0
	}

	total, ok := routerStats["total_requests"].(uint64)
	if !ok || total == 0 {
		return 0.0
	}

	balanced, ok := routerStats["balanced_count"].(uint64)
	if !ok {
		return 0.0
	}

	return float64(balanced) / float64(total) * 100
}

// calculatePremiumRate 计算高级型使用率
func calculatePremiumRate(stats map[string]interface{}) float64 {
	routerStats, ok := stats["router"].(map[string]interface{})
	if !ok {
		return 0.0
	}

	total, ok := routerStats["total_requests"].(uint64)
	if !ok || total == 0 {
		return 0.0
	}

	premium, ok := routerStats["premium_count"].(uint64)
	if !ok {
		return 0.0
	}

	return float64(premium) / float64(total) * 100
}

// Close 关闭服务
func (s *LLMService) Close() error {
	var errs []error

	// 关闭并发处理器
	if err := s.processor.Close(); err != nil {
		errs = append(errs, fmt.Errorf("关闭并发处理器失败: %w", err))
	}

	// 关闭缓存
	if err := s.cache.Close(); err != nil {
		errs = append(errs, fmt.Errorf("关闭缓存失败: %w", err))
	}

	// 关闭客户端
	if err := s.client.Close(); err != nil {
		errs = append(errs, fmt.Errorf("关闭客户端失败: %w", err))
	}

	if len(errs) > 0 {
		return fmt.Errorf("关闭服务时发生错误: %v", errs)
	}

	log.Printf("LLM服务已关闭")

	return nil
}
