// Package metrics - 系统指标收集器
// 自动收集Go运行时系统指标，包括goroutines、内存、GC等
package metrics

import (
	"context"
	"runtime"
	"time"

	"github.com/prometheus/client_golang/prometheus"
	"github.com/prometheus/client_golang/prometheus/promauto"
)

// 系统指标定义

var (
	// ==================== Go运行时指标 ====================

	// GoGoroutines 当前goroutine数量
	GoGoroutines = promauto.NewGauge(prometheus.GaugeOpts{
		Namespace: "athena_gateway",
		Subsystem: "go",
		Name:      "goroutines",
		Help:      "当前goroutine数量",
	})

	// GoMemory Go内存使用情况（字节）
	GoMemory = promauto.NewGaugeVec(prometheus.GaugeOpts{
		Namespace: "athena_gateway",
		Subsystem: "go",
		Name:      "memory_bytes",
		Help:      "Go内存使用情况（字节）",
	}, []string{"type"})

	// GoGCStats Go GC统计信息
	GoGCStats = promauto.NewGaugeVec(prometheus.GaugeOpts{
		Namespace: "athena_gateway",
		Subsystem: "go",
		Name:      "gc_stats",
		Help:      "Go GC统计信息",
	}, []string{"stat"})

	// GoGCDuration GC暂停持续时间
	GoGCDuration = promauto.NewHistogramVec(prometheus.HistogramOpts{
		Namespace: "athena_gateway",
		Subsystem: "go",
		Name:      "gc_duration_seconds",
		Help:      "Go GC暂停持续时间（秒）",
		Buckets:   []float64{0.00001, 0.00005, 0.0001, 0.0005, 0.001, 0.005, 0.01},
	}, []string{"gc_type"})

	// ==================== HTTP连接指标 ====================

	// HTTPConnections HTTP连接数
	HTTPConnections = promauto.NewGaugeVec(prometheus.GaugeOpts{
		Namespace: "athena_gateway",
		Subsystem: "http",
		Name:      "connections",
		Help:      "HTTP连接数",
	}, []string{"state"})
)

// SystemMetricsCollector 系统指标收集器
// 定期收集Go运行时系统指标
type SystemMetricsCollector struct {
	ctx    context.Context
	cancel context.CancelFunc
	ticker *time.Ticker
}

// NewSystemMetricsCollector 创建系统指标收集器
func NewSystemMetricsCollector() *SystemMetricsCollector {
	ctx, cancel := context.WithCancel(context.Background())
	return &SystemMetricsCollector{
		ctx:    ctx,
		cancel: cancel,
	}
}

// Start 启动系统指标收集
func (c *SystemMetricsCollector) Start() {
	if c.ticker != nil {
		return // 已经启动
	}

	c.ticker = time.NewTicker(10 * time.Second)
	go c.collect()
}

// collect 定期收集系统指标
func (c *SystemMetricsCollector) collect() {
	for {
		select {
		case <-c.ctx.Done():
			return
		case <-c.ticker.C:
			c.collectSystemMetrics()
		}
	}
}

// collectSystemMetrics 收集系统指标
func (c *SystemMetricsCollector) collectSystemMetrics() {
	var m runtime.MemStats
	runtime.ReadMemStats(&m)

	// Goroutine数量
	GoGoroutines.Set(float64(runtime.NumGoroutine()))

	// 内存使用
	GoMemory.WithLabelValues("heap_alloc").Set(float64(m.HeapAlloc))
	GoMemory.WithLabelValues("heap_sys").Set(float64(m.HeapSys))
	GoMemory.WithLabelValues("heap_inuse").Set(float64(m.HeapInuse))
	GoMemory.WithLabelValues("heap_idle").Set(float64(m.HeapIdle))
	GoMemory.WithLabelValues("heap_released").Set(float64(m.HeapReleased))
	GoMemory.WithLabelValues("stack_inuse").Set(float64(m.StackInuse))
	GoMemory.WithLabelValues("stack_sys").Set(float64(m.StackSys))
	GoMemory.WithLabelValues("mspan_inuse").Set(float64(m.MSpanInuse))
	GoMemory.WithLabelValues("mspan_sys").Set(float64(m.MSpanSys))
	GoMemory.WithLabelValues("mcache_inuse").Set(float64(m.MCacheInuse))
	GoMemory.WithLabelValues("mcache_sys").Set(float64(m.MCacheSys))
	GoMemory.WithLabelValues("sys").Set(float64(m.Sys))

	// GC统计
	GoGCStats.WithLabelValues("num_gc").Set(float64(m.NumGC))
	GoGCStats.WithLabelValues("pause_total_ns").Set(float64(m.PauseTotalNs))
	GoGCStats.WithLabelValues("next_gc").Set(float64(m.NextGC))

	// 最近的GC暂停时间
	if m.NumGC > 0 {
		// 获取最近一次GC的暂停时间
		lastPause := float64(m.PauseNs[(m.NumGC+255)%256]) / 1e9 // 转换为秒
		GoGCDuration.WithLabelValues("last").Observe(lastPause)
	}
}

// Stop 停止系统指标收集
func (c *SystemMetricsCollector) Stop() {
	if c.cancel != nil {
		c.cancel()
	}
	if c.ticker != nil {
		c.ticker.Stop()
		c.ticker = nil
	}
}

// RecordHTTPConnection 记录HTTP连接状态变化
func RecordHTTPConnection(state string, delta float64) {
	HTTPConnections.WithLabelValues(state).Add(delta)
}

// SetHTTPConnection 设置HTTP连接数
func SetHTTPConnection(state string, count float64) {
	HTTPConnections.WithLabelValues(state).Set(count)
}

// GetMemoryStats 获取内存统计信息（用于调试和监控）
func GetMemoryStats() runtime.MemStats {
	var m runtime.MemStats
	runtime.ReadMemStats(&m)
	return m
}

// GetGCStats 获取GC统计信息（用于调试和监控）
func GetGCStats() map[string]interface{} {
	var m runtime.MemStats
	runtime.ReadMemStats(&m)

	return map[string]interface{}{
		"num_gc":            m.NumGC,
		"pause_total_ns":    m.PauseTotalNs,
		"pause_ns":          m.PauseNs,
		"next_gc":           m.NextGC,
		"last_gc":           m.LastGC,
		"gc_cpu_fraction":   m.GCCPUFraction,
		"enable_gc":         m.EnableGC,
		"debug_gc":          m.DebugGC,
		"heap_alloc":        m.HeapAlloc,
		"heap_sys":          m.HeapSys,
		"heap_inuse":        m.HeapInuse,
		"heap_idle":         m.HeapIdle,
		"heap_released":     m.HeapReleased,
		"heap_objects":      m.HeapObjects,
		"stack_inuse":       m.StackInuse,
		"stack_sys":         m.StackSys,
		"mspan_inuse":       m.MSpanInuse,
		"mspan_sys":         m.MSpanSys,
		"mcache_inuse":      m.MCacheInuse,
		"mcache_sys":        m.MCacheSys,
		"other_sys":         m.OtherSys,
		"goroutines":        runtime.NumGoroutine(),
		"num_cpu":           runtime.NumCPU(),
		"lookups":           m.Lookups,
		"mallocs":           m.Mallocs,
		"frees":             m.Frees,
		"live_objects":      m.Mallocs - m.Frees,
	}
}
