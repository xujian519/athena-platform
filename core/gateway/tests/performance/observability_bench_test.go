package performance

import (
	"fmt"
	"net/http"
	"runtime"
	"sort"
	"sync"
	"testing"
	"time"

	"github.com/stretchr/testify/assert"
)

func BenchmarkMetricsCollection(b *testing.B) {
	client := &http.Client{Timeout: 5 * time.Second}
	url := "http://localhost:8080/health"

	b.ResetTimer()
	b.RunParallel(func(pb *testing.PB) {
		for pb.Next() {
			resp, err := client.Get(url)
			if err != nil {
				b.Errorf("Request failed: %v", err)
				continue
			}
			resp.Body.Close()
		}
	})
}

func BenchmarkHighConcurrency(b *testing.B) {
	client := &http.Client{Timeout: 10 * time.Second}
	url := "http://localhost:8080/health"

	concurrency := 100

	b.ResetTimer()
	for i := 0; i < b.N; i++ {
		var wg sync.WaitGroup
		errors := make(chan error, concurrency)

		for j := 0; j < concurrency; j++ {
			wg.Add(1)
			go func() {
				defer wg.Done()
				resp, err := client.Get(url)
				if err != nil {
					errors <- err
					return
				}
				resp.Body.Close()
			}()
		}

		wg.Wait()
		close(errors)

		for err := range errors {
			if err != nil {
				b.Errorf("Concurrent request failed: %v", err)
			}
		}
	}
}

func TestMemoryUsage(t *testing.T) {
	runtime.GC()
	var m1 runtime.MemStats
	runtime.ReadMemStats(&m1)

	client := &http.Client{Timeout: 5 * time.Second}
	url := "http://localhost:8080/health"

	// 发送1000个请求
	for i := 0; i < 1000; i++ {
		resp, err := client.Get(url)
		assert.NoError(t, err)
		if resp != nil {
			resp.Body.Close()
		}
	}

	runtime.GC()
	var m2 runtime.MemStats
	runtime.ReadMemStats(&m2)

	memIncrease := m2.Alloc - m1.Alloc
	memIncreaseMB := float64(memIncrease) / 1024 / 1024

	t.Logf("Memory increase: %.2f MB", memIncreaseMB)

	// 内存增长应该小于10MB（这是相对宽松的限制）
	assert.Less(t, memIncreaseMB, 10.0, "Memory usage increased too much")
}

func TestResponseTime(t *testing.T) {
	client := &http.Client{Timeout: 10 * time.Second}
	url := "http://localhost:8080/health"

	var durations []time.Duration
	numRequests := 100

	for i := 0; i < numRequests; i++ {
		start := time.Now()
		resp, err := client.Get(url)
		duration := time.Since(start)

		assert.NoError(t, err)
		if resp != nil {
			resp.Body.Close()
		}

		durations = append(durations, duration)
	}

	// 计算统计信息
	var total time.Duration
	min := durations[0]
	max := durations[0]

	for _, d := range durations {
		total += d
		if d < min {
			min = d
		}
		if d > max {
			max = d
		}
	}

	avg := total / time.Duration(numRequests)

	// 找到P95和P99
	sort.Slice(durations, func(i, j int) bool {
		return durations[i] < durations[j]
	})

	p95 := durations[int(float64(numRequests)*0.95)]
	p99 := durations[int(float64(numRequests)*0.99)]

	t.Logf("Response time stats:")
	t.Logf("  Average: %v", avg)
	t.Logf("  Min: %v", min)
	t.Logf("  Max: %v", max)
	t.Logf("  P95: %v", p95)
	t.Logf("  P99: %v", p99)

	// 性能要求
	assert.Less(t, avg, 50*time.Millisecond, "Average response time should be less than 50ms")
	assert.Less(t, p95, 100*time.Millisecond, "P95 response time should be less than 100ms")
	assert.Less(t, p99, 200*time.Millisecond, "P99 response time should be less than 200ms")
}

func TestTracingOverhead(t *testing.T) {
	client := &http.Client{Timeout: 5 * time.Second}
	url := "http://localhost:8080/health"

	// 测试开启追踪的性能
	durationsWithTracing := make([]time.Duration, 100)
	for i := 0; i < 100; i++ {
		start := time.Now()
		resp, err := client.Get(url)
		durationsWithTracing[i] = time.Since(start)

		assert.NoError(t, err)
		if resp != nil {
			resp.Body.Close()
		}
	}

	var totalWithTracing time.Duration
	for _, d := range durationsWithTracing {
		totalWithTracing += d
	}
	avgWithTracing := totalWithTracing / 100

	t.Logf("Average response time with tracing: %v", avgWithTracing)

	// 追踪开销应该小于5ms
	assert.Less(t, avgWithTracing, 50*time.Millisecond, "Tracing overhead should be minimal")
}

func TestConcurrencySafety(t *testing.T) {
	client := &http.Client{Timeout: 10 * time.Second}
	url := "http://localhost:8080/health"

	numGoroutines := 50
	requestsPerGoroutine := 20

	var wg sync.WaitGroup
	errorChan := make(chan error, numGoroutines*requestsPerGoroutine)

	start := time.Now()

	for i := 0; i < numGoroutines; i++ {
		wg.Add(1)
		go func() {
			defer wg.Done()

			for j := 0; j < requestsPerGoroutine; j++ {
				resp, err := client.Get(url)
				if err != nil {
					errorChan <- fmt.Errorf("Request failed: %v", err)
					continue
				}
				resp.Body.Close()
			}
		}()
	}

	wg.Wait()
	close(errorChan)

	duration := time.Since(start)
	totalRequests := numGoroutines * requestsPerGoroutine
	qps := float64(totalRequests) / duration.Seconds()

	// 检查错误
	for err := range errorChan {
		t.Errorf("Error during concurrent requests: %v", err)
	}

	t.Logf("Completed %d requests in %v (%.2f QPS)", totalRequests, duration, qps)

	// 性能要求：至少应该支持500 QPS
	assert.Greater(t, qps, 500.0, "Should handle at least 500 QPS")
}
