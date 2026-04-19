package gateway

import (
	"sync"
	"testing"
	"time"
)

// TestNewServiceRegistry 测试创建服务注册表
func TestNewServiceRegistry(t *testing.T) {
	sr := NewServiceRegistry()
	if sr == nil {
		t.Fatal("NewServiceRegistry() returned nil")
	}
	if sr.Count() != 0 {
		t.Errorf("NewRegistry() count = %d, want 0", sr.Count())
	}
}

// TestRegister 测试服务注册
func TestRegister(t *testing.T) {
	sr := NewServiceRegistry()

	instance := &ServiceInstance{
		ID:          "test-instance-1",
		ServiceName: "test-service",
		Host:        "localhost",
		Port:        8001,
		Status:      "UP",
		Weight:      1,
	}

	sr.Register(instance)

	// 验证实例已注册
	if sr.Count() != 1 {
		t.Errorf("Register() count = %d, want 1", sr.Count())
	}

	// 验证可以通过ID获取
	got := sr.GetByID("test-instance-1")
	if got == nil {
		t.Fatal("Register() instance not found by ID")
	}
	if got.ServiceName != "test-service" {
		t.Errorf("Register() ServiceName = %s, want test-service", got.ServiceName)
	}

	// 验证可以通过服务名获取
	instances := sr.GetByService("test-service")
	if len(instances) != 1 {
		t.Errorf("Register() GetByService() count = %d, want 1", len(instances))
	}
}

// TestRegisterMultiple 测试注册多个实例
func TestRegisterMultiple(t *testing.T) {
	sr := NewServiceRegistry()

	// 注册同一服务的多个实例
	for i := 0; i < 3; i++ {
		instance := &ServiceInstance{
			ID:          generateServiceID("test-service", "localhost", 8001, i),
			ServiceName: "test-service",
			Host:        "localhost",
			Port:        8001,
			Status:      "UP",
			Weight:      1,
		}
		sr.Register(instance)
	}

	if sr.Count() != 3 {
		t.Errorf("RegisterMultiple() count = %d, want 3", sr.Count())
	}

	instances := sr.GetByService("test-service")
	if len(instances) != 3 {
		t.Errorf("RegisterMultiple() GetByService() count = %d, want 3", len(instances))
	}
}

// TestGetByID 测试根据ID获取实例
func TestGetByID(t *testing.T) {
	sr := NewServiceRegistry()

	instance := &ServiceInstance{
		ID:          "test-id",
		ServiceName: "test-service",
		Host:        "localhost",
		Port:        8001,
	}
	sr.Register(instance)

	// 测试存在的实例
	got := sr.GetByID("test-id")
	if got == nil {
		t.Fatal("GetByID() existing instance returned nil")
	}
	if got.ID != "test-id" {
		t.Errorf("GetByID() ID = %s, want test-id", got.ID)
	}

	// 测试不存在的实例
	got = sr.GetByID("non-existent")
	if got != nil {
		t.Errorf("GetByID() non-existent = %v, want nil", got)
	}
}

// TestGetByService 测试根据服务名获取实例
func TestGetByService(t *testing.T) {
	sr := NewServiceRegistry()

	// 注册不同服务的实例
	sr.Register(&ServiceInstance{
		ID:          "svc1-inst1",
		ServiceName: "service1",
		Host:        "localhost",
		Port:        8001,
	})
	sr.Register(&ServiceInstance{
		ID:          "svc1-inst2",
		ServiceName: "service1",
		Host:        "localhost",
		Port:        8002,
	})
	sr.Register(&ServiceInstance{
		ID:          "svc2-inst1",
		ServiceName: "service2",
		Host:        "localhost",
		Port:        8003,
	})

	// 测试获取service1的实例
	instances := sr.GetByService("service1")
	if len(instances) != 2 {
		t.Errorf("GetByService() service1 count = %d, want 2", len(instances))
	}

	// 测试获取service2的实例
	instances = sr.GetByService("service2")
	if len(instances) != 1 {
		t.Errorf("GetByService() service2 count = %d, want 1", len(instances))
	}

	// 测试获取不存在的服务
	instances = sr.GetByService("non-existent")
	if len(instances) != 0 {
		t.Errorf("GetByService() non-existent count = %d, want 0", len(instances))
	}
}

// TestGetAll 测试获取所有实例
func TestGetAll(t *testing.T) {
	sr := NewServiceRegistry()

	// 注册3个实例
	for i := 0; i < 3; i++ {
		sr.Register(&ServiceInstance{
			ID:          generateServiceID("svc", "localhost", 8000+i, i),
			ServiceName: "svc",
			Host:        "localhost",
			Port:        8000 + i,
		})
	}

	all := sr.GetAll()
	if len(all) != 3 {
		t.Errorf("GetAll() count = %d, want 3", len(all))
	}
}

// TestDelete 测试删除实例
func TestDelete(t *testing.T) {
	sr := NewServiceRegistry()

	instance := &ServiceInstance{
		ID:          "to-delete",
		ServiceName: "test-service",
		Host:        "localhost",
		Port:        8001,
	}
	sr.Register(instance)

	// 验证已注册
	if sr.Count() != 1 {
		t.Fatalf("Delete() pre-count = %d, want 1", sr.Count())
	}

	// 删除实例
	deleted := sr.Delete("to-delete")
	if !deleted {
		t.Error("Delete() returned false, want true")
	}

	// 验证已删除
	if sr.Count() != 0 {
		t.Errorf("Delete() post-count = %d, want 0", sr.Count())
	}

	// 删除不存在的实例
	deleted = sr.Delete("non-existent")
	if deleted {
		t.Error("Delete() non-existent returned true, want false")
	}
}

// TestSetDependencies 测试设置依赖
func TestSetDependencies(t *testing.T) {
	sr := NewServiceRegistry()

	deps := []string{"service1", "service2"}
	sr.SetDependencies("service3", deps)

	got := sr.GetDependencies("service3")
	if len(got) != 2 {
		t.Errorf("SetDependencies() count = %d, want 2", len(got))
	}
}

// TestGetAllDependencies 测试获取所有依赖
func TestGetAllDependencies(t *testing.T) {
	sr := NewServiceRegistry()

	sr.SetDependencies("svc1", []string{"svc2", "svc3"})
	sr.SetDependencies("svc2", []string{"svc3"})

	all := sr.GetAllDependencies()
	if len(all) != 2 {
		t.Errorf("GetAllDependencies() count = %d, want 2", len(all))
	}
}

// TestUpdateHeartbeat 测试更新心跳
func TestUpdateHeartbeat(t *testing.T) {
	sr := NewServiceRegistry()

	instance := &ServiceInstance{
		ID:            "test-id",
		ServiceName:   "test-service",
		Host:          "localhost",
		Port:          8001,
		LastHeartbeat: time.Now().Add(-1 * time.Minute),
	}
	sr.Register(instance)

	oldHeartbeat := sr.GetByID("test-id").LastHeartbeat

	// 等待一小段时间确保时间戳不同
	time.Sleep(10 * time.Millisecond)

	sr.UpdateHeartbeat("test-id")

	newHeartbeat := sr.GetByID("test-id").LastHeartbeat
	if !newHeartbeat.After(oldHeartbeat) {
		t.Error("UpdateHeartbeat() did not update heartbeat time")
	}
}

// TestGetHealthyInstances 测试获取健康实例
func TestGetHealthyInstances(t *testing.T) {
	sr := NewServiceRegistry()

	// 注册健康实例
	sr.Register(&ServiceInstance{
		ID:            "healthy-1",
		ServiceName:   "test-service",
		Host:          "localhost",
		Port:          8001,
		Status:        "UP",
		LastHeartbeat: time.Now(),
	})

	// 注册不健康实例（状态DOWN）
	sr.Register(&ServiceInstance{
		ID:            "unhealthy-1",
		ServiceName:   "test-service",
		Host:          "localhost",
		Port:          8002,
		Status:        "DOWN",
		LastHeartbeat: time.Now(),
	})

	// 注册过期实例（心跳超时）
	sr.Register(&ServiceInstance{
		ID:            "expired-1",
		ServiceName:   "test-service",
		Host:          "localhost",
		Port:          8003,
		Status:        "UP",
		LastHeartbeat: time.Now().Add(-1 * time.Hour),
	})

	healthy := sr.GetHealthyInstances("test-service")
	if len(healthy) != 1 {
		t.Errorf("GetHealthyInstances() count = %d, want 1", len(healthy))
	}
	if healthy[0].ID != "healthy-1" {
		t.Errorf("GetHealthyInstances() first ID = %s, want healthy-1", healthy[0].ID)
	}
}

// TestSelectInstance 测试负载均衡
func TestSelectInstance(t *testing.T) {
	sr := NewServiceRegistry()

	// 注册3个健康实例
	for i := 0; i < 3; i++ {
		sr.Register(&ServiceInstance{
			ID:            generateServiceID("test", "localhost", 8000+i, i),
			ServiceName:   "test-service",
			Host:          "localhost",
			Port:          8000 + i,
			Status:        "UP",
			LastHeartbeat: time.Now(),
		})
	}

	// 测试轮询
	selected := make(map[string]int)
	for i := 0; i < 9; i++ {
		instance := sr.SelectInstance("test-service")
		if instance == nil {
			t.Fatal("SelectInstance() returned nil")
		}
		selected[instance.ID]++
	}

	// 验证每个实例都被选中了约3次
	if len(selected) != 3 {
		t.Errorf("SelectInstance() selected %d unique instances, want 3", len(selected))
	}

	for id, count := range selected {
		if count < 2 || count > 4 {
			t.Errorf("SelectInstance() %s selected %d times, want ~3", id, count)
		}
	}
}

// TestSelectInstance_NoHealthyInstances 测试无健康实例
func TestSelectInstance_NoHealthyInstances(t *testing.T) {
	sr := NewServiceRegistry()

	// 没有注册任何实例
	instance := sr.SelectInstance("non-existent")
	if instance != nil {
		t.Error("SelectInstance() non-existent returned instance, want nil")
	}

	// 只有不健康的实例
	sr.Register(&ServiceInstance{
		ID:            "unhealthy",
		ServiceName:   "test-service",
		Host:          "localhost",
		Port:          8001,
		Status:        "DOWN",
		LastHeartbeat: time.Now(),
	})

	instance = sr.SelectInstance("test-service")
	if instance != nil {
		t.Error("SelectInstance() all unhealthy returned instance, want nil")
	}
}

// TestConcurrentAccess 测试并发访问
func TestConcurrentAccess(t *testing.T) {
	sr := NewServiceRegistry()
	var wg sync.WaitGroup

	// 并发注册
	for i := 0; i < 10; i++ {
		wg.Add(1)
		go func(index int) {
			defer wg.Done()
			instance := &ServiceInstance{
				ID:          generateServiceID("test", "localhost", 8000, index),
				ServiceName: "test-service",
				Host:        "localhost",
				Port:        8000,
				Status:      "UP",
			}
			sr.Register(instance)
		}(i)
	}

	// 并发读取
	for i := 0; i < 10; i++ {
		wg.Add(1)
		go func() {
			defer wg.Done()
			sr.GetAll()
			sr.GetByService("test-service")
			sr.SelectInstance("test-service")
		}()
	}

	wg.Wait()

	// 验证最终状态
	if sr.Count() != 10 {
		t.Errorf("ConcurrentAccess() final count = %d, want 10", sr.Count())
	}
}
