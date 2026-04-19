// Package concurrent - 并发优化工具
// 提供goroutine池、无锁数据结构、并发模式等
package concurrent

import (
	"context"
	"errors"
	"runtime"
	"sync"
	"sync/atomic"
	"time"

	"github.com/athena-workspace/gateway-unified/internal/logging"
)

var (
	ErrPoolClosed   = errors.New("pool is closed")
	ErrTaskTimeout  = errors.New("task timeout")
	ErrQueueFull     = errors.New("task queue is full")
)

// PoolConfig goroutine池配置
type PoolConfig struct {
	// 池配置
	MinWorkers      int           // 最小worker数
	MaxWorkers      int           // 最大worker数
	MaxTasks        int           // 最大任务队列长度
	IdleTimeout     time.Duration // worker空闲超时

	// 任务配置
	TaskTimeout     time.Duration // 单个任务超时时间
	EnableMetrics   bool          // 启用指标收集

	// 伸缩配置
	ScaleUpThreshold   float64 // 扩容阈值（队列使用率）
	ScaleDownThreshold float64 // 缩容阈值（空闲worker比例）
}

// DefaultPoolConfig 返回默认配置
func DefaultPoolConfig() *PoolConfig {
	return &PoolConfig{
		MinWorkers:         runtime.NumCPU(),
		MaxWorkers:         runtime.NumCPU() * 4,
		MaxTasks:           1000,
		IdleTimeout:        30 * time.Second,
		TaskTimeout:        30 * time.Second,
		EnableMetrics:      true,
		ScaleUpThreshold:   0.8,
		ScaleDownThreshold: 0.3,
	}
}

// Task 任务接口
type Task interface {
	Execute(ctx context.Context) error
}

// TaskFunc 函数式任务
type TaskFunc func(ctx context.Context) error

// Execute 实现Task接口
func (f TaskFunc) Execute(ctx context.Context) error {
	return f(ctx)
}

// PoolStats 池统计
type PoolStats struct {
	WorkerCount       int32
	ActiveWorkerCount int32
	TaskCount         int32
	CompletedTasks    int64
	FailedTasks       int64
	RejectedTasks     int64
	AverageTaskTime   time.Duration // 外部使用
}

// GoroutinePool goroutine池
type GoroutinePool struct {
	config  *PoolConfig
	stats   *PoolStats

	// 任务队列
	taskQueue chan Task

	// worker管理
	workers        []*worker
	workerCount    atomic.Int32
	activeCount    atomic.Int32
	averageTaskTime atomic.Int64 // 内部原子操作

	// 生命周期
	ctx      context.Context
	cancel   context.CancelFunc
	wg       sync.WaitGroup
	closed   atomic.Bool
	closeOnce sync.Once

	// 伸缩管理
	scaleTicker *time.Ticker
	scaleMu     sync.Mutex
}

// worker 工作协程
type worker struct {
	id       int
	pool     *GoroutinePool
	taskChan chan Task
	quit     chan struct{}
}

// NewGoroutinePool 创建goroutine池
func NewGoroutinePool(cfg *PoolConfig) (*GoroutinePool, error) {
	if cfg == nil {
		cfg = DefaultPoolConfig()
	}

	ctx, cancel := context.WithCancel(context.Background())

	pool := &GoroutinePool{
		config:    cfg,
		stats:     &PoolStats{},
		taskQueue: make(chan Task, cfg.MaxTasks),
		ctx:       ctx,
		cancel:    cancel,
	}

	// 启动最小数量的worker
	for i := 0; i < cfg.MinWorkers; i++ {
		pool.startWorker(i)
	}

	// 启动伸缩管理
	pool.startScaler()

	logging.LogInfo("goroutine池创建成功",
		logging.Int("min_workers", cfg.MinWorkers),
		logging.Int("max_workers", cfg.MaxWorkers),
		logging.Int("max_tasks", cfg.MaxTasks))

	return pool, nil
}

// startWorker 启动worker
func (p *GoroutinePool) startWorker(id int) {
	w := &worker{
		id:       id,
		pool:     p,
		taskChan: make(chan Task, 1),
		quit:     make(chan struct{}),
	}

	p.workerCount.Add(1)
	p.workers = append(p.workers, w)

	p.wg.Add(1)
	go w.run()
}

// Submit 提交任务
func (p *GoroutinePool) Submit(task Task) error {
	if p.closed.Load() {
		return ErrPoolClosed
	}

	// 检查队列是否已满
	if len(p.taskQueue) >= cap(p.taskQueue) {
		p.stats.RejectedTasks++
		return ErrQueueFull
	}

	p.stats.TaskCount++
	p.taskQueue <- task

	return nil
}

// SubmitFunc 提交函数式任务
func (p *GoroutinePool) SubmitFunc(fn func(ctx context.Context) error) error {
	return p.Submit(TaskFunc(fn))
}

// SubmitWithTimeout 提交带超时的任务
func (p *GoroutinePool) SubmitWithTimeout(task Task, timeout time.Duration) error {
	if p.closed.Load() {
		return ErrPoolClosed
	}

	// 检查队列是否已满
	if len(p.taskQueue) >= cap(p.taskQueue) {
		p.stats.RejectedTasks++
		return ErrQueueFull
	}

	p.stats.TaskCount++

	// 使用超时上下文包装任务
	ctx, cancel := context.WithTimeout(p.ctx, timeout)
	wrappedTask := TaskFunc(func(innerCtx context.Context) error {
		defer cancel()
		return task.Execute(ctx)
	})

	p.taskQueue <- wrappedTask

	return nil
}

// run worker运行循环
func (w *worker) run() {
	defer func() {
		w.pool.workerCount.Add(-1)
		w.pool.wg.Done()
	}()

	for {
		select {
		case task := <-w.pool.taskQueue:
			w.pool.activeCount.Add(1)
			w.executeTask(task)
			w.pool.activeCount.Add(-1)

		case <-w.quit:
			return
		}
	}
}

// executeTask 执行任务
func (w *worker) executeTask(task Task) {
	startTime := time.Now()

	ctx := w.pool.ctx
	if w.pool.config.TaskTimeout > 0 {
		var cancel context.CancelFunc
		ctx, cancel = context.WithTimeout(ctx, w.pool.config.TaskTimeout)
		defer cancel()
	}

	err := task.Execute(ctx)
	duration := time.Since(startTime)

	w.pool.stats.CompletedTasks++

	if err != nil {
		w.pool.stats.FailedTasks++
		logging.LogDebug("任务执行失败",
			logging.Int("worker_id", w.id),
			logging.Err(err))
	}

	// 更新平均任务时间
	if w.pool.config.EnableMetrics {
		old := w.pool.averageTaskTime.Load()
		oldDuration := time.Duration(old)
		newDuration := (oldDuration*9 + duration) / 10
		w.pool.averageTaskTime.Store(int64(newDuration))
	}
}

// startScaler 启动伸缩管理
func (p *GoroutinePool) startScaler() {
	p.scaleTicker = time.NewTicker(5 * time.Second)

	p.wg.Add(1)
	go func() {
		defer p.wg.Done()
		defer p.scaleTicker.Stop()

		for {
			select {
			case <-p.ctx.Done():
				return
			case <-p.scaleTicker.C:
				p.scale()
			}
		}
	}()
}

// scale 动态伸缩worker数量
func (p *GoroutinePool) scale() {
	p.scaleMu.Lock()
	defer p.scaleMu.Unlock()

	currentWorkers := p.workerCount.Load()
	activeWorkers := p.activeCount.Load()

	// 计算队列使用率
	queueUsage := float64(len(p.taskQueue)) / float64(cap(p.taskQueue))

	// 计算空闲worker比例
	idleRatio := 1.0
	if currentWorkers > 0 {
		idleRatio = 1.0 - float64(activeWorkers)/float64(currentWorkers)
	}

	// 扩容条件：队列使用率高且worker数量未达上限
	if queueUsage > p.config.ScaleUpThreshold &&
		currentWorkers < int32(p.config.MaxWorkers) {

		newWorkers := int(float64(currentWorkers) * 1.5) // 增加50%
		if newWorkers > p.config.MaxWorkers {
			newWorkers = p.config.MaxWorkers
		}

		added := 0
		for i := currentWorkers; i < int32(newWorkers); i++ {
			p.startWorker(int(i))
			added++
		}

		if added > 0 {
			logging.LogInfo("池扩容",
				logging.Int("added", added),
				logging.Int("new_total", int(p.workerCount.Load())))
		}
	}

	// 缩容条件：空闲worker比例高且worker数量高于最小值
	if idleRatio > p.config.ScaleDownThreshold &&
		currentWorkers > int32(p.config.MinWorkers) {

		targetWorkers := int(float64(currentWorkers) * 0.7) // 减少30%
		if targetWorkers < p.config.MinWorkers {
			targetWorkers = p.config.MinWorkers
		}

		removed := 0
		for int(p.workerCount.Load()) > targetWorkers {
			// 通过发送quit信号来停止worker
			// 简化实现：实际中可能需要更优雅的机制
			removed++
		}

		if removed > 0 {
			logging.LogInfo("池缩容",
				logging.Int("removed", removed),
				logging.Int("new_total", int(p.workerCount.Load())))
		}
	}
}

// GetStats 获取统计信息
func (p *GoroutinePool) GetStats() *PoolStats {
	return &PoolStats{
		WorkerCount:       p.workerCount.Load(),
		ActiveWorkerCount: p.activeCount.Load(),
		TaskCount:         int32(len(p.taskQueue)),
		CompletedTasks:    atomic.LoadInt64(&p.stats.CompletedTasks),
		FailedTasks:       atomic.LoadInt64(&p.stats.FailedTasks),
		RejectedTasks:     atomic.LoadInt64(&p.stats.RejectedTasks),
		AverageTaskTime:   time.Duration(p.averageTaskTime.Load()),
	}
}

// Close 关闭池
func (p *GoroutinePool) Close() error {
	p.closeOnce.Do(func() {
		p.closed.Store(true)
		p.cancel()

		// 关闭所有worker
		for _, w := range p.workers {
			close(w.quit)
		}

		// 等待所有worker完成
		p.wg.Wait()

		logging.LogInfo("goroutine池已关闭",
			logging.Int64("completed_tasks", p.stats.CompletedTasks),
			logging.Int64("failed_tasks", p.stats.FailedTasks))
	})

	return nil
}

// ========== 并发安全的数据结构 ==========

// AtomicInt 原子整数
type AtomicInt struct {
	value int64
}

// NewAtomicInt 创建原子整数
func NewAtomicInt(initial int64) *AtomicInt {
	return &AtomicInt{value: initial}
}

// Get 获取值
func (a *AtomicInt) Get() int64 {
	return atomic.LoadInt64(&a.value)
}

// Set 设置值
func (a *AtomicInt) Set(value int64) {
	atomic.StoreInt64(&a.value, value)
}

// Add 增加值
func (a *AtomicInt) Add(delta int64) int64 {
	return atomic.AddInt64(&a.value, delta)
}

// CompareAndSwap 比较并交换
func (a *AtomicInt) CompareAndSwap(old, new int64) bool {
	return atomic.CompareAndSwapInt64(&a.value, old, new)
}

// SyncMap 并发安全的Map（封装sync.Map）
type SyncMap struct {
	m sync.Map
}

// NewSyncMap 创建并发安全的Map
func NewSyncMap() *SyncMap {
	return &SyncMap{}
}

// Load 加载值
func (m *SyncMap) Load(key interface{}) (interface{}, bool) {
	return m.m.Load(key)
}

// Store 存储值
func (m *SyncMap) Store(key, value interface{}) {
	m.m.Store(key, value)
}

// LoadOrStore 加载或存储
func (m *SyncMap) LoadOrStore(key, value interface{}) (interface{}, bool) {
	return m.m.LoadOrStore(key, value)
}

// LoadAndDelete 加载并删除
func (m *SyncMap) LoadAndDelete(key interface{}) (interface{}, bool) {
	return m.m.LoadAndDelete(key)
}

// Delete 删除值
func (m *SyncMap) Delete(key interface{}) {
	m.m.Delete(key)
}

// Range 遍历
func (m *SyncMap) Range(f func(key, value interface{}) bool) {
	m.m.Range(f)
}

// ========== 并发模式 ==========

// WaitGroup 等待组封装
type WaitGroup struct {
	wg sync.WaitGroup
}

// NewWaitGroup 创建等待组
func NewWaitGroup() *WaitGroup {
	return &WaitGroup{}
}

// Add 添加计数
func (w *WaitGroup) Add(delta int) {
	w.wg.Add(delta)
}

// Done 完成一个
func (w *WaitGroup) Done() {
	w.wg.Done()
}

// Wait 等待
func (w *WaitGroup) Wait() {
	w.wg.Wait()
}

// Limit 并发限制器
type Limit struct {
	ch chan struct{}
}

// NewLimit 创建并发限制器
func NewLimit(max int) *Limit {
	return &Limit{
		ch: make(chan struct{}, max),
	}
}

// Acquire 获取许可
func (l *Limit) Acquire() {
	l.ch <- struct{}{}
}

// TryAcquire 尝试获取许可
func (l *Limit) TryAcquire() bool {
	select {
	case l.ch <- struct{}{}:
		return true
	default:
		return false
	}
}

// Release 释放许可
func (l *Limit) Release() {
	<-l.ch
}

// Executor 并发执行器
type Executor struct {
	pool *GoroutinePool
}

// NewExecutor 创建执行器
func NewExecutor(cfg *PoolConfig) (*Executor, error) {
	pool, err := NewGoroutinePool(cfg)
	if err != nil {
		return nil, err
	}

	return &Executor{pool: pool}, nil
}

// Execute 执行任务
func (e *Executor) Execute(ctx context.Context, tasks ...Task) error {
	wg := NewWaitGroup()
	errChan := make(chan error, len(tasks))

	for _, task := range tasks {
		wg.Add(1)
		wrappedTask := TaskFunc(func(innerCtx context.Context) error {
			defer wg.Done()
			return task.Execute(innerCtx)
		})

		if err := e.pool.Submit(wrappedTask); err != nil {
			wg.Done()
			return err
		}
	}

	// 等待所有任务完成
	go func() {
		wg.Wait()
		close(errChan)
	}()

	// 收集错误
	var firstErr error
	for err := range errChan {
		if err != nil && firstErr == nil {
			firstErr = err
		}
	}

	return firstErr
}

// ExecuteConcurrent 并发执行任务（限制并发数）
func (e *Executor) ExecuteConcurrent(ctx context.Context, concurrency int, tasks ...Task) error {
	if concurrency <= 0 {
		return e.Execute(ctx, tasks...)
	}

	limiter := NewLimit(concurrency)
	wg := NewWaitGroup()
	errChan := make(chan error, len(tasks))

	for _, task := range tasks {
		limiter.Acquire()
		wg.Add(1)

		wrappedTask := TaskFunc(func(innerCtx context.Context) error {
			defer wg.Done()
			defer limiter.Release()
			return task.Execute(innerCtx)
		})

		if err := e.pool.Submit(wrappedTask); err != nil {
			wg.Done()
			limiter.Release()
			return err
		}
	}

	// 等待所有任务完成
	go func() {
		wg.Wait()
		close(errChan)
	}()

	// 收集错误
	var firstErr error
	for err := range errChan {
		if err != nil && firstErr == nil {
			firstErr = err
		}
	}

	return firstErr
}

// Close 关闭执行器
func (e *Executor) Close() error {
	return e.pool.Close()
}
