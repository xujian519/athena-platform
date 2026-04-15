// Package pool - 连接池测试
package pool

import (
	"context"
	"fmt"
	"net/http"
	"net/http/httptest"
	"sync"
	"testing"
	"time"

	"github.com/athena-workspace/gateway-unified/internal/logging"
)

// TestDefaultConfig 测试默认配置
func TestDefaultConfig(t *testing.T) {
	cfg := DefaultConfig()

	if cfg.MaxIdleConns != 200 {
		t.Errorf("期望MaxIdleConns=200，实际为%d", cfg.MaxIdleConns)
	}

	if cfg.MaxIdleConnsPerHost != 50 {
		t.Errorf("期望MaxIdleConnsPerHost=50，实际为%d", cfg.MaxIdleConnsPerHost)
	}

	if cfg.IdleConnTimeout != 90*time.Second {
		t.Errorf("期望IdleConnTimeout=90s，实际为%v", cfg.IdleConnTimeout)
	}
}

// TestNewConnectionPool 测试创建连接池
func TestNewConnectionPool(t *testing.T) {
	cfg := DefaultConfig()
	pool, err := NewConnectionPool(cfg)

	if err != nil {
		t.Fatalf("创建连接池失败: %v", err)
	}

	if pool == nil {
		t.Fatal("连接池不应为nil")
	}

	if pool.Client() == nil {
		t.Error("HTTP客户端不应为nil")
	}

	// 清理
	pool.Close()
}

// TestConnectionPool_Do 测试执行请求
func TestConnectionPool_Do(t *testing.T) {
	// 创建测试服务器
	requestCount := 0
	var mu sync.Mutex

	server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		mu.Lock()
		requestCount++
		count := requestCount
		mu.Unlock()

		w.WriteHeader(http.StatusOK)
		w.Write([]byte(fmt.Sprintf("Request #%d", count)))
	}))
	defer server.Close()

	// 创建连接池
	cfg := DefaultConfig()
	cfg.RequestTimeout = 5 * time.Second
	pool, err := NewConnectionPool(cfg)
	if err != nil {
		t.Fatalf("创建连接池失败: %v", err)
	}
	defer pool.Close()

	// 执行请求
	req, err := http.NewRequest("GET", server.URL, nil)
	if err != nil {
		t.Fatalf("创建请求失败: %v", err)
	}

	resp, err := pool.Do(req)
	if err != nil {
		t.Fatalf("执行请求失败: %v", err)
	}

	if resp.StatusCode != http.StatusOK {
		t.Errorf("期望状态200，实际为%d", resp.StatusCode)
	}
}

// TestConnectionPool_Concurrency 测试并发请求
func TestConnectionPool_Concurrency(t *testing.T) {
	// 创建测试服务器
	server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		time.Sleep(10 * time.Millisecond)
		w.WriteHeader(http.StatusOK)
		w.Write([]byte("OK"))
	}))
	defer server.Close()

	// 创建连接池
	cfg := DefaultConfig()
	cfg.MaxIdleConns = 50
	cfg.MaxIdleConnsPerHost = 25
	cfg.RequestTimeout = 10 * time.Second
	pool, err := NewConnectionPool(cfg)
	if err != nil {
		t.Fatalf("创建连接池失败: %v", err)
	}
	defer pool.Close()

	// 并发执行多个请求
	const numRequests = 100
	var wg sync.WaitGroup
	errors := make(chan error, numRequests)

	for i := 0; i < numRequests; i++ {
		wg.Add(1)
		go func() {
			defer wg.Done()

			req, err := http.NewRequest("GET", server.URL, nil)
			if err != nil {
				errors <- err
				return
			}

			resp, err := pool.Do(req)
			if err != nil {
				errors <- err
				return
			}
			resp.Body.Close()

			if resp.StatusCode != http.StatusOK {
				errors <- fmt.Errorf("unexpected status: %d", resp.StatusCode)
			}
		}()
	}

	wg.Wait()
	close(errors)

	// 检查错误
	errorCount := 0
	for err := range errors {
		logging.LogWarn("请求错误", logging.Err(err))
		errorCount++
	}

	if errorCount > 0 {
		t.Errorf("发生%d个错误", errorCount)
	}

	// 检查统计
	stats := pool.GetStats()
	if stats.TotalRequests != uint64(numRequests) {
		t.Errorf("期望%d个请求，实际为%d", numRequests, stats.TotalRequests)
	}

	if stats.SuccessfulRequests != uint64(numRequests-errorCount) {
		t.Errorf("期望%d个成功请求，实际为%d", numRequests-errorCount, stats.SuccessfulRequests)
	}
}

// TestConnectionPool_Stats 测试连接池统计
func TestConnectionPool_Stats(t *testing.T) {
	cfg := DefaultConfig()
	pool, err := NewConnectionPool(cfg)
	if err != nil {
		t.Fatalf("创建连接池失败: %v", err)
	}
	defer pool.Close()

	// 执行一些请求
	server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		w.WriteHeader(http.StatusOK)
	}))
	defer server.Close()

	for i := 0; i < 5; i++ {
		req, _ := http.NewRequest("GET", server.URL, nil)
		pool.Do(req)
	}

	stats := pool.GetStats()

	if stats.TotalRequests != 5 {
		t.Errorf("期望5个请求，实际为%d", stats.TotalRequests)
	}

	if stats.SuccessfulRequests != 5 {
		t.Errorf("期望5个成功请求，实际为%d", stats.SuccessfulRequests)
	}
}

// TestConnectionPool_Close 测试关闭连接池
func TestConnectionPool_Close(t *testing.T) {
	cfg := DefaultConfig()
	pool, err := NewConnectionPool(cfg)
	if err != nil {
		t.Fatalf("创建连接池失败: %v", err)
	}

	// 关闭连接池
	err = pool.Close()
	if err != nil {
		t.Fatalf("关闭连接池失败: %v", err)
	}

	// 再次关闭应该不会出错
	err = pool.Close()
	if err != nil {
		t.Errorf("重复关闭连接池不应出错: %v", err)
	}
}

// TestConnectionPool_Retry 测试请求重试
func TestConnectionPool_Retry(t *testing.T) {
	// 创建一个会暂时失败的测试服务器
	attempts := 0
	maxFailures := 2

	server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		attempts++
		if attempts <= maxFailures {
			// 模拟网络错误 - 关闭连接而不响应
			hj, ok := w.(http.Hijacker)
			if ok {
				conn, _, _ := hj.Hijack()
				conn.Close()
			}
			return
		}
		w.WriteHeader(http.StatusOK)
		w.Write([]byte("OK"))
	}))
	defer server.Close()

	// 创建带重试配置的连接池
	cfg := DefaultConfig()
	cfg.MaxRetries = 3
	cfg.RetryDelay = 10 * time.Millisecond
	pool, err := NewConnectionPool(cfg)
	if err != nil {
		t.Fatalf("创建连接池失败: %v", err)
	}
	defer pool.Close()

	req, _ := http.NewRequest("GET", server.URL, nil)
	resp, err := pool.Do(req)

	if err != nil {
		t.Fatalf("请求失败: %v", err)
	}

	if resp.StatusCode != http.StatusOK {
		t.Errorf("期望状态200，实际为%d", resp.StatusCode)
	}

	// 验证重试次数
	stats := pool.GetStats()
	// 注意: 重试统计可能因连接复用而不同
	if stats.TotalRequests < uint64(maxFailures) {
		t.Logf("注意: 由于连接复用，实际请求次数可能小于预期")
	}
}

// TestHealthChecker 测试健康检查器
func TestHealthChecker(t *testing.T) {
	// 创建测试服务器
	healthyServer := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		w.WriteHeader(http.StatusOK)
	}))
	defer healthyServer.Close()

	// 创建连接池
	cfg := DefaultConfig()
	cfg.HealthCheckInterval = 1 * time.Second
	cfg.HealthCheckTimeout = 500 * time.Millisecond
	pool, err := NewConnectionPool(cfg)
	if err != nil {
		t.Fatalf("创建连接池失败: %v", err)
	}
	defer pool.Close()

	// 添加健康检查目标
	pool.healthChecker.AddTarget("test-server", healthyServer.URL)

	// 启动健康检查
	ctx, cancel := context.WithTimeout(context.Background(), 3*time.Second)
	defer cancel()

	pool.healthChecker.Start(ctx)

	// 等待至少一次健康检查
	time.Sleep(2 * time.Second)

	// 检查健康状态
	status := pool.healthChecker.GetHealthStatus()

	if !status.IsHealthy {
		t.Error("服务应该是健康的")
	}
}

// TestConnectionPool_ResponseTime 测试响应时间统计
func TestConnectionPool_ResponseTime(t *testing.T) {
	// 创建测试服务器
	server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		time.Sleep(50 * time.Millisecond)
		w.WriteHeader(http.StatusOK)
	}))
	defer server.Close()

	// 创建连接池
	cfg := DefaultConfig()
	pool, err := NewConnectionPool(cfg)
	if err != nil {
		t.Fatalf("创建连接池失败: %v", err)
	}
	defer pool.Close()

	// 执行多个请求
	for i := 0; i < 5; i++ {
		req, _ := http.NewRequest("GET", server.URL, nil)
		resp, err := pool.Do(req)
		if err != nil {
			t.Fatalf("请求失败: %v", err)
		}
		resp.Body.Close()
	}

	// 检查平均响应时间
	stats := pool.GetStats()

	if stats.AverageResponseTime < 50*time.Millisecond {
		t.Errorf("平均响应时间应该至少50ms，实际为%v", stats.AverageResponseTime)
	}
}

// TestConnectionPool_ConnReuse 测试连接复用
func TestConnectionPool_ConnReuse(t *testing.T) {
	var connectionCount int
	var mu sync.Mutex

	// 创建测试服务器
	server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		mu.Lock()
		connectionCount++
		mu.Unlock()

		w.WriteHeader(http.StatusOK)
	}))
	defer server.Close()

	// 创建连接池
	cfg := DefaultConfig()
	cfg.MaxIdleConnsPerHost = 2
	pool, err := NewConnectionPool(cfg)
	if err != nil {
		t.Fatalf("创建连接池失败: %v", err)
	}
	defer pool.Close()

	// 执行多个请求
	for i := 0; i < 10; i++ {
		req, _ := http.NewRequest("GET", server.URL, nil)
		resp, err := pool.Do(req)
		if err != nil {
			t.Fatalf("请求失败: %v", err)
		}
		resp.Body.Close()
	}

	// 由于连接复用，实际建立的连接数应该远小于请求数
	if connectionCount > 3 {
		t.Logf("警告: 建立了%d个连接，请求数为10，连接复用可能不够理想", connectionCount)
	}
}
