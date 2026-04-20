// Package vector - 向量检索服务（Go实现）
// 提供高性能的Qdrant向量搜索客户端
package vector

import (
	"bytes"
	"context"
	"encoding/json"
	"fmt"
	"io"
	"net/http"
	"sync"
	"time"

	"log"
)

// QdrantClient Qdrant向量数据库客户端
type QdrantClient struct {
	baseURL    string
	httpClient *http.Client
	mu         sync.RWMutex
	stats      *SearchStats
}

// SearchStats 搜索统计
type SearchStats struct {
	mu            sync.RWMutex
	TotalSearches uint64
	TotalTime     time.Duration
	AvgTime       time.Duration
	MinTime       time.Duration
	MaxTime       time.Duration
	CacheHits     uint64
	CacheMisses   uint64
}

// SearchRequest 搜索请求
type SearchRequest struct {
	Collection string    `json:"collection"`
	Vector     []float64 `json:"vector"`
	Limit      int       `json:"limit"`
	Threshold  float64   `json:"threshold,omitempty"`
}

// SearchResult 搜索结果
type SearchResult struct {
	ID       string  `json:"id"`
	Score    float64 `json:"score"`
	Payload  any     `json:"payload,omitempty"`
	Metadata any     `json:"metadata,omitempty"`
}

// SearchResponse 搜索响应
type SearchResponse struct {
	Status     string         `json:"status"`
	Time       float64        `json:"time"`
	Result     []SearchResult `json:"result"`
	NumResults int            `json:"num_results"`
}

// Config 客户端配置
type Config struct {
	Host            string
	Port            int
	Timeout         time.Duration
	MaxIdleConns    int
	MaxConnsPerHost int
}

// DefaultConfig 返回默认配置
func DefaultConfig() *Config {
	return &Config{
		Host:            "localhost",
		Port:            16333, // Qdrant默认端口
		Timeout:         30 * time.Second,
		MaxIdleConns:    100,
		MaxConnsPerHost: 10,
	}
}

// NewQdrantClient 创建Qdrant客户端
func NewQdrantClient(cfg *Config) (*QdrantClient, error) {
	if cfg == nil {
		cfg = DefaultConfig()
	}

	baseURL := fmt.Sprintf("http://%s:%d", cfg.Host, cfg.Port)

	// 创建优化的HTTP客户端
	client := &http.Client{
		Timeout: cfg.Timeout,
		Transport: &http.Transport{
			MaxIdleConns:        cfg.MaxIdleConns,
			MaxIdleConnsPerHost: cfg.MaxConnsPerHost,
			IdleConnTimeout:     90 * time.Second,
			DisableCompression:  false,
			ForceAttemptHTTP2:   true,
		},
	}

	qdrant := &QdrantClient{
		baseURL:    baseURL,
		httpClient: client,
		stats:      &SearchStats{},
	}

	log.Printf("Qdrant客户端创建成功 url=%s port=%d max_idle_conns=%d max_conns_per_host=%d",
		baseURL, cfg.Port, cfg.MaxIdleConns, cfg.MaxConnsPerHost)

	return qdrant, nil
}

// Search 执行向量搜索
func (q *QdrantClient) Search(ctx context.Context, req *SearchRequest) (*SearchResponse, error) {
	startTime := time.Now()

	// 记录搜索次数
	q.stats.mu.Lock()
	q.stats.TotalSearches++
	q.stats.mu.Unlock()

	// 构建搜索URL
	url := fmt.Sprintf("%s/collections/%s/points/search", q.baseURL, req.Collection)

	// 构建请求体
	searchBody := map[string]interface{}{
		"vector": req.Vector,
		"limit":  req.Limit,
	}

	if req.Threshold > 0 {
		searchBody["score_threshold"] = req.Threshold
	}

	jsonData, err := json.Marshal(searchBody)
	if err != nil {
		return nil, fmt.Errorf("序列化请求失败: %w", err)
	}

	// 创建HTTP请求
	httpReq, err := http.NewRequestWithContext(ctx, "POST", url, bytes.NewReader(jsonData))
	if err != nil {
		return nil, fmt.Errorf("创建HTTP请求失败: %w", err)
	}

	httpReq.Header.Set("Content-Type", "application/json")

	// 执行请求
	resp, err := q.httpClient.Do(httpReq)
	if err != nil {
		return nil, fmt.Errorf("HTTP请求失败: %w", err)
	}
	defer resp.Body.Close()

	// 读取响应
	body, err := io.ReadAll(resp.Body)
	if err != nil {
		return nil, fmt.Errorf("读取响应失败: %w", err)
	}

	// 检查HTTP状态码
	if resp.StatusCode != http.StatusOK {
		return nil, fmt.Errorf("Qdrant返回错误: %d, %s", resp.StatusCode, string(body))
	}

	// 解析响应
	var searchResp SearchResponse
	if err := json.Unmarshal(body, &searchResp); err != nil {
		return nil, fmt.Errorf("解析响应失败: %w", err)
	}

	// 更新统计
	duration := time.Since(startTime)
	q.updateStats(duration)

	if len(searchResp.Result) > 0 {
		log.Printf("向量搜索完成 collection=%s num_results=%d duration=%v",
			req.Collection, len(searchResp.Result), duration)
	}

	return &searchResp, nil
}

// BatchSearch 批量向量搜索（优化版）
func (q *QdrantClient) BatchSearch(ctx context.Context, reqs []*SearchRequest) ([]*SearchResponse, error) {
	startTime := time.Now()
	results := make([]*SearchResponse, len(reqs))
	var wg sync.WaitGroup
	var mu sync.Mutex
	var firstErr error

	// 使用goroutine池并发搜索
	semaphore := make(chan struct{}, 10) // 限制并发数为10

	for i, req := range reqs {
		wg.Add(1)
		semaphore <- struct{}{}

		go func(idx int, r *SearchRequest) {
			defer wg.Done()
			defer func() { <-semaphore }()

			result, err := q.Search(ctx, r)
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

	log.Printf("批量搜索完成 total=%d total_time=%v", len(reqs), time.Since(startTime))

	return results, nil
}

// updateStats 更新统计信息
func (q *QdrantClient) updateStats(duration time.Duration) {
	q.stats.mu.Lock()
	defer q.stats.mu.Unlock()

	q.stats.TotalTime += duration
	totalSearches := q.stats.TotalSearches

	if totalSearches == 1 {
		q.stats.MinTime = duration
		q.stats.MaxTime = duration
	} else {
		if duration < q.stats.MinTime {
			q.stats.MinTime = duration
		}
		if duration > q.stats.MaxTime {
			q.stats.MaxTime = duration
		}
	}

	q.stats.AvgTime = time.Duration(int64(q.stats.TotalTime) / int64(totalSearches))
}

// GetStats 获取统计信息
func (q *QdrantClient) GetStats() *SearchStats {
	q.stats.mu.RLock()
	defer q.stats.mu.RUnlock()

	// 返回副本
	return &SearchStats{
		TotalSearches: q.stats.TotalSearches,
		TotalTime:     q.stats.TotalTime,
		AvgTime:       q.stats.AvgTime,
		MinTime:       q.stats.MinTime,
		MaxTime:       q.stats.MaxTime,
		CacheHits:     q.stats.CacheHits,
		CacheMisses:   q.stats.CacheMisses,
	}
}

// Close 关闭客户端
func (q *QdrantClient) Close() error {
	q.httpClient.CloseIdleConnections()
	log.Printf("Qdrant客户端已关闭")
	return nil
}
