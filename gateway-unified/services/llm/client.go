// Package llm - LLM调用服务（Go实现）
// 提供高性能的LLM API调用，支持并发、缓存、智能路由
package llm

import (
	"bytes"
	"context"
	"encoding/json"
	"fmt"
	"io"
	"net/http"
	"strings"
	"sync"
	"time"

	"log"
)

// LLMClient LLM客户端接口
type LLMClient interface {
	Chat(ctx context.Context, req *ChatRequest) (*ChatResponse, error)
	Embed(ctx context.Context, text string) (*EmbeddingResponse, error)
	Close() error
}

// ChatRequest 聊天请求
type ChatRequest struct {
	Messages    []Message `json:"messages"`
	Model       string    `json:"model"`
	Temperature float64   `json:"temperature,omitempty"`
	MaxTokens   int       `json:"max_tokens,omitempty"`
	Stream      bool      `json:"stream,omitempty"`
}

// Message 聊天消息
type Message struct {
	Role    string `json:"role"`
	Content string `json:"content"`
}

// ChatResponse 聊天响应
type ChatResponse struct {
	ID      string   `json:"id"`
	Object  string   `json:"object"`
	Created int64    `json:"created"`
	Model   string   `json:"model"`
	Choices []Choice `json:"choices"`
	Usage   Usage    `json:"usage,omitempty"`
}

// Choice 消息选择
type Choice struct {
	Index        int     `json:"index"`
	Message      Message `json:"message"`
	FinishReason string  `json:"finish_reason,omitempty"`
}

// Usage 使用情况
type Usage struct {
	PromptTokens     int `json:"prompt_tokens"`
	CompletionTokens int `json:"completion_tokens"`
	TotalTokens      int `json:"total_tokens"`
}

// EmbeddingRequest 嵌入请求
type EmbeddingRequest struct {
	Input          []string `json:"input"`
	Model          string   `json:"model"`
	EncodingFormat string   `json:"encoding_format,omitempty"`
}

// EmbeddingResponse 嵌入响应
type EmbeddingResponse struct {
	Object string      `json:"object"`
	Data   [][]float32 `json:"data"`
	Model  string      `json:"model"`
	Usage  Usage       `json:"usage"`
}

// HTTPClient HTTP LLM客户端
type HTTPClient struct {
	baseURL    string
	apiKey     string
	httpClient *http.Client
	model      string
	mu         sync.RWMutex
	stats      *LLMStats
}

// LLMStats LLM调用统计
type LLMStats struct {
	mu                 sync.RWMutex
	TotalRequests      uint64
	SuccessfulRequests uint64
	FailedRequests     uint64
	TotalTokens        uint64
	TotalCost          float64
	TotalTime          time.Duration
	AvgTime            time.Duration
	CacheHits          uint64
	CacheMisses        uint64
	TotalCostSaved     float64
}

// Config 客户端配置
type Config struct {
	BaseURL    string
	APIKey     string
	Model      string
	Timeout    time.Duration
	MaxRetries int
}

// NewHTTPClient 创建HTTP客户端
func NewHTTPClient(cfg *Config) (*HTTPClient, error) {
	if cfg == nil {
		cfg = &Config{
			BaseURL:    "https://api.deepseek.com/v1",
			Model:      "deepseek-chat",
			Timeout:    30 * time.Second,
			MaxRetries: 3,
		}
	}

	client := &HTTPClient{
		baseURL: cfg.BaseURL,
		apiKey:  cfg.APIKey,
		model:   cfg.Model,
		httpClient: &http.Client{
			Timeout: cfg.Timeout,
			Transport: &http.Transport{
				MaxIdleConns:        50,
				MaxIdleConnsPerHost: 10,
				IdleConnTimeout:     90 * time.Second,
				DisableCompression:  false,
				ForceAttemptHTTP2:   true,
			},
		},
		stats: &LLMStats{},
	}

	log.Printf("LLM客户端创建成功 base_url=%s model=%s", cfg.BaseURL, cfg.Model)

	return client, nil
}

// Chat 执行聊天请求
func (c *HTTPClient) Chat(ctx context.Context, req *ChatRequest) (*ChatResponse, error) {
	startTime := time.Now()

	// 更新统计
	c.stats.mu.Lock()
	c.stats.TotalRequests++
	c.stats.mu.Unlock()

	// 设置默认模型
	if req.Model == "" {
		req.Model = c.model
	}

	// 构建URL
	url := fmt.Sprintf("%s/chat/completions", c.baseURL)

	// 序列化请求
	jsonData, err := json.Marshal(req)
	if err != nil {
		return nil, fmt.Errorf("序列化请求失败: %w", err)
	}

	// 创建HTTP请求
	httpReq, err := http.NewRequestWithContext(ctx, "POST", url, bytes.NewReader(jsonData))
	if err != nil {
		return nil, fmt.Errorf("创建HTTP请求失败: %w", err)
	}

	// 设置请求头
	httpReq.Header.Set("Content-Type", "application/json")
	httpReq.Header.Set("Authorization", "Bearer "+c.apiKey)

	// 执行请求（支持重试）
	var resp *http.Response
	retryCount := 0

	for retryCount <= c.getMaxRetries() {
		resp, err = c.httpClient.Do(httpReq)
		if err == nil && resp.StatusCode == 200 {
			break
		}

		// 检查是否可重试
		if retryCount < c.getMaxRetries() && c.isRetryable(err) {
			retryCount++
			log.Printf("LLM请求失败，重试中 model=%s retry=%d error=%v", req.Model, retryCount, err)

			// 指数退避
			delay := time.Duration(1<<uint(retryCount)) * 100 * time.Millisecond
			time.Sleep(delay)
			continue
		}

		break
	}

	if err != nil {
		c.updateStatsError(startTime)
		return nil, fmt.Errorf("HTTP请求失败: %w", err)
	}
	defer resp.Body.Close()

	// 检查状态码
	if resp.StatusCode != 200 {
		body, _ := io.ReadAll(resp.Body)
		c.updateStatsError(startTime)
		return nil, fmt.Errorf("LLM API返回错误: %d, %s", resp.StatusCode, string(body))
	}

	// 解析响应
	body, err := io.ReadAll(resp.Body)
	if err != nil {
		c.updateStatsError(startTime)
		return nil, fmt.Errorf("读取响应失败: %w", err)
	}

	var chatResp ChatResponse
	if err := json.Unmarshal(body, &chatResp); err != nil {
		c.updateStatsError(startTime)
		return nil, fmt.Errorf("解析响应失败: %w", err)
	}

	// 更新统计
	c.updateStatsSuccess(startTime, &chatResp.Usage)

	return &chatResp, nil
}

// Embed 执行嵌入请求
func (c *HTTPClient) Embed(ctx context.Context, text string) (*EmbeddingResponse, error) {
	// 实现嵌入逻辑
	return nil, fmt.Errorf("not implemented")
}

// updateStatsSuccess 更新成功统计
func (c *HTTPClient) updateStatsSuccess(startTime time.Time, usage *Usage) {
	c.stats.mu.Lock()
	defer c.stats.mu.Unlock()

	duration := time.Since(startTime)
	c.stats.SuccessfulRequests++
	c.stats.TotalTime += duration

	if usage != nil {
		c.stats.TotalTokens += uint64(usage.TotalTokens)
		// 简化的成本计算（$0.002/1K tokens）
		c.stats.TotalCost += float64(usage.TotalTokens) * 0.002 / 1000.0
	}

	if c.stats.TotalRequests > 0 {
		c.stats.AvgTime = time.Duration(int64(c.stats.TotalTime) / int64(c.stats.TotalRequests))
	}
}

// updateStatsError 更新错误统计
func (c *HTTPClient) updateStatsError(startTime time.Time) {
	c.stats.mu.Lock()
	defer c.stats.mu.Unlock()

	c.stats.FailedRequests++
	duration := time.Since(startTime)
	c.stats.TotalTime += duration
}

// getMaxRetries 获取最大重试次数
func (c *HTTPClient) getMaxRetries() int {
	// 从配置读取，这里简化处理
	return 3
}

// isRetryable 判断错误是否可重试
func (c *HTTPClient) isRetryable(err error) bool {
	if err == nil {
		return false
	}

	// 检查错误类型
	errStr := err.Error()
	return strings.Contains(errStr, "timeout") ||
		strings.Contains(errStr, "connection") ||
		strings.Contains(errStr, "EOF")
}

// GetStats 获取统计信息
func (c *HTTPClient) GetStats() *LLMStats {
	c.stats.mu.RLock()
	defer c.stats.mu.RUnlock()

	return &LLMStats{
		TotalRequests:      c.stats.TotalRequests,
		SuccessfulRequests: c.stats.SuccessfulRequests,
		FailedRequests:     c.stats.FailedRequests,
		TotalTokens:        c.stats.TotalTokens,
		TotalCost:          c.stats.TotalCost,
		TotalTime:          c.stats.TotalTime,
		AvgTime:            c.stats.AvgTime,
		CacheHits:          c.stats.CacheHits,
		CacheMisses:        c.stats.CacheMisses,
		TotalCostSaved:     c.stats.TotalCostSaved,
	}
}

// Close 关闭客户端
func (c *HTTPClient) Close() error {
	c.httpClient.CloseIdleConnections()
	return nil
}
