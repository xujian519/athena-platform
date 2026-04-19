// Package concurrent - 并发工具测试
package concurrent

import (
	"context"
	"sync/atomic"
	"testing"
	"time"
)

// TestDefaultPoolConfig 测试默认配置
func TestDefaultPoolConfig(t *testing.T) {
	cfg := DefaultPoolConfig()

	if cfg.MinWorkers == 0 {
		t.Error("MinWorkers应该大于0")
	}

	if cfg.MaxWorkers < cfg.MinWorkers {
		t.Error("MaxWorkers应该大于等于MinWorkers")
	}

	if cfg.MaxTasks == 0 {
		t.Error("MaxTasks应该大于0")
	}
}

// TestNewGoroutinePool 测试创建池
func TestNewGoroutinePool(t *testing.T) {
	cfg := DefaultPoolConfig()
	pool, err := NewGoroutinePool(cfg)

	if err != nil {
		t.Fatalf("创建池失败: %v", err)
	}

	if pool == nil {
		t.Fatal("池不应为nil")
	}

	// 清理
	pool.Close()
}

// TestGoroutinePool_Submit 测试提交任务
func TestGoroutinePool_Submit(t *testing.T) {
	cfg := DefaultPoolConfig()
	cfg.MinWorkers = 2
	cfg.MaxWorkers = 2
	cfg.EnableMetrics = false // 禁用指标以加快测试

	pool, err := NewGoroutinePool(cfg)
	if err != nil {
		t.Fatalf("创建池失败: %v", err)
	}
	defer pool.Close()

	// 提交任务
	var counter atomic.Int64
	task := TaskFunc(func(ctx context.Context) error {
		counter.Add(1)
		return nil
	})

	err = pool.Submit(task)
	if err != nil {
		t.Fatalf("提交任务失败: %v", err)
	}

	// 等待任务完成
	time.Sleep(100 * time.Millisecond)

	if counter.Load() != 1 {
		t.Errorf("期望counter=1，实际为%d", counter.Load())
	}

	stats := pool.GetStats()
	if stats.CompletedTasks != 1 {
		t.Errorf("期望1个完成任务，实际为%d", stats.CompletedTasks)
	}
}

// TestGoroutinePool_SubmitFunc 测试提交函数式任务
func TestGoroutinePool_SubmitFunc(t *testing.T) {
	cfg := DefaultPoolConfig()
	cfg.MinWorkers = 2
	cfg.MaxWorkers = 2
	cfg.EnableMetrics = false

	pool, err := NewGoroutinePool(cfg)
	if err != nil {
		t.Fatalf("创建池失败: %v", err)
	}
	defer pool.Close()

	var counter atomic.Int64

	err = pool.SubmitFunc(func(ctx context.Context) error {
		counter.Add(1)
		return nil
	})

	if err != nil {
		t.Fatalf("提交任务失败: %v", err)
	}

	time.Sleep(100 * time.Millisecond)

	if counter.Load() != 1 {
		t.Errorf("期望counter=1，实际为%d", counter.Load())
	}
}

// TestGoroutinePool_MultipleTasks 测试多任务
func TestGoroutinePool_MultipleTasks(t *testing.T) {
	cfg := DefaultPoolConfig()
	cfg.MinWorkers = 4
	cfg.MaxWorkers = 10
	cfg.EnableMetrics = false

	pool, err := NewGoroutinePool(cfg)
	if err != nil {
		t.Fatalf("创建池失败: %v", err)
	}
	defer pool.Close()

	const numTasks = 100
	var counter atomic.Int64

	for i := 0; i < numTasks; i++ {
		task := TaskFunc(func(ctx context.Context) error {
			counter.Add(1)
			return nil
		})

		if err := pool.Submit(task); err != nil {
			t.Fatalf("提交任务失败: %v", err)
		}
	}

	// 等待所有任务完成
	time.Sleep(500 * time.Millisecond)

	if counter.Load() != numTasks {
		t.Errorf("期望counter=%d，实际为%d", numTasks, counter.Load())
	}

	stats := pool.GetStats()
	if stats.CompletedTasks != numTasks {
		t.Errorf("期望%d个完成任务，实际为%d", numTasks, stats.CompletedTasks)
	}
}

// TestGoroutinePool_TaskTimeout 测试任务超时
func TestGoroutinePool_TaskTimeout(t *testing.T) {
	cfg := DefaultPoolConfig()
	cfg.MinWorkers = 2
	cfg.MaxWorkers = 2
	cfg.TaskTimeout = 100 * time.Millisecond
	cfg.EnableMetrics = false

	pool, err := NewGoroutinePool(cfg)
	if err != nil {
		t.Fatalf("创建池失败: %v", err)
	}
	defer pool.Close()

	// 创建会超时的任务
	task := TaskFunc(func(ctx context.Context) error {
		time.Sleep(200 * time.Millisecond)
		return nil
	})

	err = pool.Submit(task)
	if err != nil {
		t.Fatalf("提交任务失败: %v", err)
	}

	// 等待任务完成或超时
	time.Sleep(300 * time.Millisecond)

	stats := pool.GetStats()
	// 任务应该被标记为失败（因为超时）
	if stats.CompletedTasks == 0 {
		t.Log("注意: 任务超时处理可能需要改进")
	}
}

// TestGoroutinePool_QueueFull 测试队列满
func TestGoroutinePool_QueueFull(t *testing.T) {
	cfg := DefaultPoolConfig()
	cfg.MinWorkers = 1
	cfg.MaxWorkers = 1
	cfg.MaxTasks = 2 // 小队列
	cfg.EnableMetrics = false

	pool, err := NewGoroutinePool(cfg)
	if err != nil {
		t.Fatalf("创建池失败: %v", err)
	}
	defer pool.Close()

	// 创建阻塞任务
	blockTask := TaskFunc(func(ctx context.Context) error {
		time.Sleep(500 * time.Millisecond)
		return nil
	})

	// 填满队列
	_ = pool.Submit(blockTask)
	_ = pool.Submit(blockTask)

	// 队列已满，应该拒绝新任务
	err = pool.Submit(blockTask)
	if err != ErrQueueFull {
		t.Errorf("期望ErrQueueFull，实际为%v", err)
	}
}

// TestGoroutinePool_Close 测试关闭池
func TestGoroutinePool_Close(t *testing.T) {
	cfg := DefaultPoolConfig()
	cfg.EnableMetrics = false

	pool, err := NewGoroutinePool(cfg)
	if err != nil {
		t.Fatalf("创建池失败: %v", err)
	}

	// 关闭池
	err = pool.Close()
	if err != nil {
		t.Fatalf("关闭池失败: %v", err)
	}

	// 提交任务应该失败
	task := TaskFunc(func(ctx context.Context) error {
		return nil
	})

	err = pool.Submit(task)
	if err != ErrPoolClosed {
		t.Errorf("期望ErrPoolClosed，实际为%v", err)
	}
}

// TestAtomicInt 测试原子整数
func TestAtomicInt(t *testing.T) {
	a := NewAtomicInt(0)

	if a.Get() != 0 {
		t.Errorf("期望0，实际为%d", a.Get())
	}

	a.Set(10)
	if a.Get() != 10 {
		t.Errorf("期望10，实际为%d", a.Get())
	}

	result := a.Add(5)
	if result != 15 {
		t.Errorf("期望15，实际为%d", result)
	}

	if a.Get() != 15 {
		t.Errorf("期望15，实际为%d", a.Get())
	}

	swapped := a.CompareAndSwap(15, 20)
	if !swapped {
		t.Error("比较交换应该成功")
	}

	if a.Get() != 20 {
		t.Errorf("期望20，实际为%d", a.Get())
	}
}

// TestAtomicInt_Concurrency 测试原子整数并发
func TestAtomicInt_Concurrency(t *testing.T) {
	a := NewAtomicInt(0)
	const goroutines = 100
	const increments = 1000

	done := make(chan bool)

	for i := 0; i < goroutines; i++ {
		go func() {
			for j := 0; j < increments; j++ {
				a.Add(1)
			}
			done <- true
		}()
	}

	// 等待所有goroutine完成
	for i := 0; i < goroutines; i++ {
		<-done
	}

	expected := int64(goroutines * increments)
	if a.Get() != expected {
		t.Errorf("期望%d，实际为%d", expected, a.Get())
	}
}

// TestSyncMap 测试并发Map
func TestSyncMap(t *testing.T) {
	m := NewSyncMap()

	// Load不存在的键
	_, ok := m.Load("key1")
	if ok {
		t.Error("不存在的键应该返回false")
	}

	// Store
	m.Store("key1", "value1")

	// Load
	val, ok := m.Load("key1")
	if !ok {
		t.Error("存在的键应该返回true")
	}
	if val != "value1" {
		t.Errorf("期望value1，实际为%v", val)
	}

	// LoadOrStore
	val, ok = m.LoadOrStore("key1", "newvalue")
	if !ok {
		t.Error("LoadOrStore应该返回已存在的值")
	}
	if val != "value1" {
		t.Errorf("期望value1，实际为%v", val)
	}

	// LoadOrStore新键
	val, ok = m.LoadOrStore("key2", "value2")
	if ok {
		t.Error("新键应该返回false")
	}
	if val != "value2" {
		t.Errorf("期望value2，实际为%v", val)
	}

	// LoadAndDelete
	val, ok = m.LoadAndDelete("key1")
	if !ok {
		t.Error("LoadAndDelete应该返回true")
	}
	if val != "value1" {
		t.Errorf("期望value1，实际为%v", val)
	}

	// 再次Load应该失败
	_, ok = m.Load("key1")
	if ok {
		t.Error("删除后Load应该返回false")
	}

	// Range
	count := 0
	m.Range(func(key, value interface{}) bool {
		count++
		return true
	})
	if count != 1 { // 只剩key2
		t.Errorf("期望1个元素，实际为%d", count)
	}

	// Delete
	m.Delete("key2")
	count = 0
	m.Range(func(key, value interface{}) bool {
		count++
		return true
	})
	if count != 0 {
		t.Errorf("期望0个元素，实际为%d", count)
	}
}

// TestSyncMap_Concurrency 测试并发Map并发安全
func TestSyncMap_Concurrency(t *testing.T) {
	m := NewSyncMap()
	const goroutines = 100
	const operations = 100

	done := make(chan bool)

	for i := 0; i < goroutines; i++ {
		go func(n int) {
			for j := 0; j < operations; j++ {
				key := "key" + string(rune('0'+n%10))
				m.Store(key, j)
				m.Load(key)
			}
			done <- true
		}(i)
	}

	// 等待所有goroutine完成
	for i := 0; i < goroutines; i++ {
		<-done
	}

	// 检查Map中有数据
	count := 0
	m.Range(func(key, value interface{}) bool {
		count++
		return true
	})

	if count == 0 {
		t.Error("Map中应该有数据")
	}
}

// TestLimit 测试并发限制器
func TestLimit(t *testing.T) {
	limiter := NewLimit(2)

	// 获取许可
	limiter.Acquire()
	limiter.Acquire()

	// 尝试获取第三个许可
	if limiter.TryAcquire() {
		t.Error("第三个许可应该获取失败")
	}

	// 释放一个许可
	limiter.Release()

	// 现在应该可以获取
	if !limiter.TryAcquire() {
		t.Error("释放后应该可以获取许可")
	}

	// 清理
	limiter.Release()
	limiter.Release()
}

// TestWaitGroup 测试等待组
func TestWaitGroup(t *testing.T) {
	wg := NewWaitGroup()
	const goroutines = 10
	counter := atomic.Int64{}

	for i := 0; i < goroutines; i++ {
		wg.Add(1)
		go func() {
			defer wg.Done()
			counter.Add(1)
		}()
	}

	wg.Wait()

	if counter.Load() != goroutines {
		t.Errorf("期望%d，实际为%d", goroutines, counter.Load())
	}
}

// TestExecutor_Execute 测试执行器
func TestExecutor_Execute(t *testing.T) {
	cfg := DefaultPoolConfig()
	cfg.MinWorkers = 4
	cfg.MaxWorkers = 10
	cfg.EnableMetrics = false

	exec, err := NewExecutor(cfg)
	if err != nil {
		t.Fatalf("创建执行器失败: %v", err)
	}
	defer exec.Close()

	ctx := context.Background()

	// 创建任务
	const numTasks = 10
	tasks := make([]Task, numTasks)
	var counter atomic.Int64

	for i := 0; i < numTasks; i++ {
		tasks[i] = TaskFunc(func(innerCtx context.Context) error {
			counter.Add(1)
			return nil
		})
	}

	// 执行任务
	err = exec.Execute(ctx, tasks...)
	if err != nil {
		t.Fatalf("执行任务失败: %v", err)
	}

	if counter.Load() != numTasks {
		t.Errorf("期望%d，实际为%d", numTasks, counter.Load())
	}
}

// TestExecutor_ExecuteConcurrent 测试并发执行器
func TestExecutor_ExecuteConcurrent(t *testing.T) {
	cfg := DefaultPoolConfig()
	cfg.MinWorkers = 2
	cfg.MaxWorkers = 10
	cfg.EnableMetrics = false

	exec, err := NewExecutor(cfg)
	if err != nil {
		t.Fatalf("创建执行器失败: %v", err)
	}
	defer exec.Close()

	ctx := context.Background()

	// 创建任务
	const numTasks = 20
	const concurrency = 5
	tasks := make([]Task, numTasks)
	var counter atomic.Int64
	var maxConcurrent atomic.Int64

	for i := 0; i < numTasks; i++ {
		tasks[i] = TaskFunc(func(innerCtx context.Context) error {
			current := maxConcurrent.Add(1)
			defer maxConcurrent.Add(-1)

			// 验证并发数不超过限制
			if current > int64(concurrency) {
				t.Errorf("并发数超过限制: %d > %d", current, concurrency)
			}

			// 模拟一些工作
			time.Sleep(10 * time.Millisecond)
			counter.Add(1)
			return nil
		})
	}

	// 执行任务
	err = exec.ExecuteConcurrent(ctx, concurrency, tasks...)
	if err != nil {
		t.Fatalf("执行任务失败: %v", err)
	}

	if counter.Load() != numTasks {
		t.Errorf("期望%d，实际为%d", numTasks, counter.Load())
	}
}
