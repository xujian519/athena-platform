package pool

import (
	"context"
	"fmt"
	"net/http"
	"sync"
	"time"

	"athena-gateway/internal/config"
	"athena-gateway/internal/logging"
	"go.uber.org/zap"
)

// HTTPClientPool HTTP客户端连接池
type HTTPClientPool struct {
	clients map[string]*http.Client
	config  *config.HTTPClientConfig
	mutex   sync.RWMutex
}

// NewHTTPClientPool 创建新的HTTP客户端连接池
func NewHTTPClientPool(cfg *config.HTTPClientConfig) *HTTPClientPool {
	pool := &HTTPClientPool{
		clients: make(map[string]*http.Client),
		config:  cfg,
	}

	// 初始化默认客户端
	pool.initDefaultClients()

	// 启动连接池监控
	go pool.monitor()

	logging.LogInfo("HTTP客户端连接池初始化成功",
		zap.Int("max_idle_conns", cfg.MaxIdleConns),
		zap.Int("max_idle_conns_per_host", cfg.MaxIdleConnsPerHost),
		zap.Duration("idle_conn_timeout", time.Duration(cfg.IdleConnTimeout)*time.Second),
	)

	return pool
}

// initDefaultClients 初始化默认客户端
func (p *HTTPClientPool) initDefaultClients() {
	// 创建通用HTTP客户端
	generalClient := &http.Client{
		Timeout: time.Duration(p.config.RequestTimeout) * time.Second,
		Transport: &http.Transport{
			MaxIdleConns:        p.config.MaxIdleConns,
			MaxIdleConnsPerHost: p.config.MaxIdleConnsPerHost,
			IdleConnTimeout:     time.Duration(p.config.IdleConnTimeout) * time.Second,
			DisableCompression:  false,
			ForceAttemptHTTP2:   true,
		},
	}

	p.mutex.Lock()
	p.clients["general"] = generalClient
	p.mutex.Unlock()

	// 创建长连接客户端
	longConnClient := &http.Client{
		Timeout: time.Duration(p.config.RequestTimeout*2) * time.Second,
		Transport: &http.Transport{
			MaxIdleConns:        p.config.MaxIdleConns * 2,
			MaxIdleConnsPerHost: p.config.MaxIdleConnsPerHost * 2,
			IdleConnTimeout:     time.Duration(p.config.IdleConnTimeout*3) * time.Second,
			DisableCompression:  false,
			ForceAttemptHTTP2:   true,
		},
	}

	p.mutex.Lock()
	p.clients["long_conn"] = longConnClient
	p.mutex.Unlock()

	// 创建快速连接客户端
	fastClient := &http.Client{
		Timeout: time.Duration(p.config.RequestTimeout/2) * time.Second,
		Transport: &http.Transport{
			MaxIdleConns:        p.config.MaxIdleConns / 2,
			MaxIdleConnsPerHost: p.config.MaxIdleConnsPerHost / 2,
			IdleConnTimeout:     time.Duration(p.config.IdleConnTimeout/2) * time.Second,
			DisableCompression:  true,
			ForceAttemptHTTP2:   true,
		},
	}

	p.mutex.Lock()
	p.clients["fast"] = fastClient
	p.mutex.Unlock()
}

// GetClient 获取指定类型的HTTP客户端
func (p *HTTPClientPool) GetClient(clientType string) (*http.Client, error) {
	p.mutex.RLock()
	defer p.mutex.RUnlock()

	client, exists := p.clients[clientType]
	if !exists {
		return nil, fmt.Errorf("未找到客户端类型: %s", clientType)
	}

	return client, nil
}

// GetGeneralClient 获取通用HTTP客户端
func (p *HTTPClientPool) GetGeneralClient() *http.Client {
	client, _ := p.GetClient("general")
	return client
}

// GetFastClient 获取快速HTTP客户端
func (p *HTTPClientPool) GetFastClient() *http.Client {
	client, _ := p.GetClient("fast")
	return client
}

// GetLongConnClient 获取长连接HTTP客户端
func (p *HTTPClientPool) GetLongConnClient() *http.Client {
	client, _ := p.GetClient("long_conn")
	return client
}

// AddCustomClient 添加自定义HTTP客户端
func (p *HTTPClientPool) AddCustomClient(name string, client *http.Client) {
	p.mutex.Lock()
	defer p.mutex.Unlock()

	p.clients[name] = client
	logging.LogInfo("添加自定义HTTP客户端", zap.String("name", name))
}

// RemoveClient 移除HTTP客户端
func (p *HTTPClientPool) RemoveClient(name string) {
	p.mutex.Lock()
	defer p.mutex.Unlock()

	if _, exists := p.clients[name]; exists {
		delete(p.clients, name)
		logging.LogInfo("移除HTTP客户端", zap.String("name", name))
	}
}

// Close 关闭所有客户端连接
func (p *HTTPClientPool) Close() {
	p.mutex.Lock()
	defer p.mutex.Unlock()

	for name, client := range p.clients {
		if transport, ok := client.Transport.(*http.Transport); ok {
			transport.CloseIdleConnections()
		}
		logging.LogInfo("关闭HTTP客户端连接", zap.String("name", name))
	}

	p.clients = make(map[string]*http.Client)
}

// Stats 获取连接池统计信息
func (p *HTTPClientPool) Stats() map[string]interface{} {
	p.mutex.RLock()
	defer p.mutex.RUnlock()

	stats := make(map[string]interface{})

	for name, client := range p.clients {
		if transport, ok := client.Transport.(*http.Transport); ok {
			clientStats := map[string]interface{}{
				"max_idle_conns":          transport.MaxIdleConns,
				"max_idle_conns_per_host": transport.MaxIdleConnsPerHost,
				"idle_conn_timeout":       transport.IdleConnTimeout.String(),
				"disable_compression":     transport.DisableCompression,
				"force_attempt_http2":     transport.ForceAttemptHTTP2,
			}
			stats[name] = clientStats
		}
	}

	return stats
}

// monitor 监控连接池状态
func (p *HTTPClientPool) monitor() {
	ticker := time.NewTicker(60 * time.Second)
	defer ticker.Stop()

	for range ticker.C {
		stats := p.Stats()

		for name, clientStats := range stats {
			logging.LogInfo("HTTP客户端连接池状态",
				zap.String("client_name", name),
				zap.Any("stats", clientStats),
			)
		}
	}
}

// HealthCheck 健康检查
func (p *HTTPClientPool) HealthCheck(ctx context.Context) error {
	client := p.GetGeneralClient()

	req, err := http.NewRequestWithContext(ctx, "GET", "https://www.google.com", nil)
	if err != nil {
		return fmt.Errorf("创建健康检查请求失败: %w", err)
	}

	resp, err := client.Do(req)
	if err != nil {
		return fmt.Errorf("HTTP客户端健康检查失败: %w", err)
	}
	defer resp.Body.Close()

	if resp.StatusCode >= 400 {
		return fmt.Errorf("HTTP客户端健康检查返回错误状态码: %d", resp.StatusCode)
	}

	return nil
}
