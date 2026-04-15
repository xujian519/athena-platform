package performance

import (
	"context"
	"runtime"
	"sync"
	"time"

	"athena-gateway/internal/config"
	"athena-gateway/internal/logging"
	"go.uber.org/zap"
)

// ResourceMonitor 资源监控器
type ResourceMonitor struct {
	config     *config.PerformanceConfig
	stats      *ResourceStats
	stopChan   chan struct{}
	mutex      sync.RWMutex
	thresholds ResourceThresholds
}

// ResourceStats 资源统计
type ResourceStats struct {
	MemoryUsage    MemoryStats `json:"memory_usage"`
	CPUUsage       CPUStats    `json:"cpu_usage"`
	GoroutineCount int64       `json:"goroutine_count"`
	GCStats        GCStats     `json:"gc_stats"`
	LastUpdate     time.Time   `json:"last_update"`
	mutex          sync.RWMutex
}

// MemoryStats 内存统计
type MemoryStats struct {
	Alloc         uint64  `json:"alloc"`
	TotalAlloc    uint64  `json:"total_alloc"`
	Sys           uint64  `json:"sys"`
	Lookups       uint64  `json:"lookups"`
	Mallocs       uint64  `json:"mallocs"`
	Frees         uint64  `json:"frees"`
	HeapAlloc     uint64  `json:"heap_alloc"`
	HeapSys       uint64  `json:"heap_sys"`
	HeapIdle      uint64  `json:"heap_idle"`
	HeapInuse     uint64  `json:"heap_inuse"`
	HeapReleased  uint64  `json:"heap_released"`
	HeapObjects   uint64  `json:"heap_objects"`
	StackInuse    uint64  `json:"stack_inuse"`
	StackSys      uint64  `json:"stack_sys"`
	GCSys         uint64  `json:"gc_sys"`
	OtherSys      uint64  `json:"other_sys"`
	GCCPUFraction float64 `json:"gc_cpu_fraction"`
}

// CPUStats CPU统计
type CPUStats struct {
	UsagePercent float64   `json:"usage_percent"`
	LoadAverage  []float64 `json:"load_average"`
	ProcessTime  float64   `json:"process_time"`
	Cores        int       `json:"cores"`
	LastSample   time.Time `json:"last_sample"`
}

// GCStats GC统计
type GCStats struct {
	NumGC         uint32            `json:"num_gc"`
	NumForcedGC   uint32            `json:"num_forced_gc"`
	GCCPUFraction float64           `json:"gc_cpu_fraction"`
	EnableGC      bool              `json:"enable_gc"`
	DebugGC       bool              `json:"debug_gc"`
	PauseTotalNs  uint64            `json:"pause_total_ns"`
	PauseNs       [256]uint64       `json:"pause_ns"`
	PauseEnd      [256]uint64       `json:"pause_end"`
	LastGC        time.Time         `json:"last_gc"`
	NextGC        uint64            `json:"next_gc"`
	BySize        [61]GCStatsBySize `json:"by_size"`
}

// GCStatsBySize 按大小分类的GC统计
type GCStatsBySize struct {
	Size    uint32 `json:"size"`
	Mallocs uint64 `json:"mallocs"`
	Frees   uint64 `json:"frees"`
}

// ResourceThresholds 资源阈值
type ResourceThresholds struct {
	MemoryUsagePercent float64 `json:"memory_usage_percent"`
	CPUUsagePercent    float64 `json:"cpu_usage_percent"`
	GoroutineCount     int64   `json:"goroutine_count"`
	GCFrequency        int     `json:"gc_frequency"`
}

// ResourceOptimizer 资源优化器
type ResourceOptimizer struct {
	monitor  *ResourceMonitor
	config   *config.PerformanceConfig
	autoTune bool
	stopChan chan struct{}
}

// NewResourceMonitor 创建资源监控器
func NewResourceMonitor(cfg *config.PerformanceConfig) *ResourceMonitor {
	return &ResourceMonitor{
		config:   cfg,
		stats:    &ResourceStats{},
		stopChan: make(chan struct{}),
		thresholds: ResourceThresholds{
			MemoryUsagePercent: 80.0,
			CPUUsagePercent:    75.0,
			GoroutineCount:     int64(cfg.MaxGoroutines),
			GCFrequency:        60,
		},
	}
}

// Start 启动资源监控
func (rm *ResourceMonitor) Start(ctx context.Context) {
	ticker := time.NewTicker(10 * time.Second)
	defer ticker.Stop()

	for {
		select {
		case <-ctx.Done():
			return
		case <-rm.stopChan:
			return
		case <-ticker.C:
			rm.collectStats()
			rm.checkThresholds()
		}
	}
}

// Stop 停止资源监控
func (rm *ResourceMonitor) Stop() {
	close(rm.stopChan)
}

// collectStats 收集资源统计信息
func (rm *ResourceMonitor) collectStats() {
	var m runtime.MemStats
	runtime.ReadMemStats(&m)

	rm.stats.mutex.Lock()
	defer rm.stats.mutex.Unlock()

	rm.stats.MemoryUsage = MemoryStats{
		Alloc:         m.Alloc,
		TotalAlloc:    m.TotalAlloc,
		Sys:           m.Sys,
		Lookups:       m.Lookups,
		Mallocs:       m.Mallocs,
		Frees:         m.Frees,
		HeapAlloc:     m.HeapAlloc,
		HeapSys:       m.HeapSys,
		HeapIdle:      m.HeapIdle,
		HeapInuse:     m.HeapInuse,
		HeapReleased:  m.HeapReleased,
		HeapObjects:   m.HeapObjects,
		StackInuse:    m.StackInuse,
		StackSys:      m.StackSys,
		GCSys:         m.GCSys,
		OtherSys:      m.OtherSys,
		GCCPUFraction: m.GCCPUFraction,
	}

	rm.stats.GoroutineCount = int64(runtime.NumGoroutine())

	rm.stats.CPUUsage = CPUStats{
		Cores:      runtime.NumCPU(),
		LastSample: time.Now(),
	}

	// 更新协程数量
	rm.stats.GoroutineCount = int64(runtime.NumGoroutine())

	// 更新CPU统计
	rm.stats.CPUUsage = CPUStats{
		Cores:      runtime.NumCPU(),
		LastSample: time.Now(),
	}

	rm.stats.LastUpdate = time.Now()
}

// checkThresholds 检查资源阈值
func (rm *ResourceMonitor) checkThresholds() {
	rm.stats.mutex.RLock()
	defer rm.stats.mutex.RUnlock()

	if rm.stats.MemoryUsage.HeapSys > 0 {
		memoryUsagePercent := float64(rm.stats.MemoryUsage.HeapInuse) / float64(rm.stats.MemoryUsage.HeapSys) * 100
		if memoryUsagePercent > rm.thresholds.MemoryUsagePercent {
			logging.LogWarn("内存使用率超过阈值",
				zap.Float64("usage_percent", memoryUsagePercent),
				zap.Float64("threshold", rm.thresholds.MemoryUsagePercent),
				zap.Uint64("heap_inuse", rm.stats.MemoryUsage.HeapInuse),
				zap.Uint64("heap_sys", rm.stats.MemoryUsage.HeapSys),
			)
		}
	}

	if rm.stats.GoroutineCount > rm.thresholds.GoroutineCount {
		logging.LogWarn("协程数量超过阈值",
			zap.Int64("current_count", rm.stats.GoroutineCount),
			zap.Int64("threshold", rm.thresholds.GoroutineCount),
		)
	}

	if rm.stats.GCStats.NumGC > uint32(rm.thresholds.GCFrequency) {
		logging.LogWarn("GC频率过高",
			zap.Uint32("num_gc", rm.stats.GCStats.NumGC),
			zap.Int("threshold", rm.thresholds.GCFrequency),
		)
	}
}

// GetStats 获取资源统计
func (rm *ResourceMonitor) GetStats() *ResourceStats {
	rm.stats.mutex.RLock()
	defer rm.stats.mutex.RUnlock()

	stats := *rm.stats
	return &stats
}

// NewResourceOptimizer 创建资源优化器
func NewResourceOptimizer(monitor *ResourceMonitor, cfg *config.PerformanceConfig) *ResourceOptimizer {
	optimizer := &ResourceOptimizer{
		monitor:  monitor,
		config:   cfg,
		autoTune: true,
		stopChan: make(chan struct{}),
	}

	return optimizer
}

// Start 启动资源优化
func (ro *ResourceOptimizer) Start(ctx context.Context) {
	ticker := time.NewTicker(30 * time.Second)
	defer ticker.Stop()

	for {
		select {
		case <-ctx.Done():
			return
		case <-ro.stopChan:
			return
		case <-ticker.C:
			if ro.autoTune {
				ro.optimizeMemory()
				ro.optimizeGC()
				ro.optimizeGoroutines()
			}
		}
	}
}

// Stop 停止资源优化
func (ro *ResourceOptimizer) Stop() {
	close(ro.stopChan)
}

// optimizeMemory 优化内存使用
func (ro *ResourceOptimizer) optimizeMemory() {
	stats := ro.monitor.GetStats()

	if stats.MemoryUsage.HeapSys > 0 {
		usagePercent := float64(stats.MemoryUsage.HeapInuse) / float64(stats.MemoryUsage.HeapSys) * 100
		if usagePercent > 85 {
			logging.LogInfo("内存使用率过高，执行强制GC",
				zap.Float64("usage_percent", usagePercent),
			)
			runtime.GC()
		}
	}
}

// optimizeGC 优化GC参数
func (ro *ResourceOptimizer) optimizeGC() {
	stats := ro.monitor.GetStats()

	if stats.GCStats.GCCPUFraction > 0.05 {
		logging.LogInfo("GC CPU占用过高，建议调整GC参数",
			zap.Float64("gc_cpu_fraction", stats.GCStats.GCCPUFraction),
		)
	}
}

// optimizeGoroutines 优化协程数量
func (ro *ResourceOptimizer) optimizeGoroutines() {
	stats := ro.monitor.GetStats()

	if stats.GoroutineCount > int64(float64(ro.config.MaxGoroutines)*0.8) {
		logging.LogWarn("协程数量接近上限",
			zap.Int64("current_count", stats.GoroutineCount),
			zap.Int("max_goroutines", ro.config.MaxGoroutines),
		)
	}
}

// SetAutoTune 设置自动调优
func (ro *ResourceOptimizer) SetAutoTune(enabled bool) {
	ro.autoTune = enabled
	logging.LogInfo("设置资源自动调优", zap.Bool("enabled", enabled))
}
