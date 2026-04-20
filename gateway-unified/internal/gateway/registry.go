package gateway

import (
	"sync"
	"time"
)

// ServiceInstance 服务实例
type ServiceInstance struct {
	ID            string                 `json:"id"`
	ServiceName   string                 `json:"service_name"`
	Host          string                 `json:"host"`
	Port          int                    `json:"port"`
	Weight        int                    `json:"weight"`
	Status        string                 `json:"status"`
	Metadata      map[string]interface{} `json:"metadata"`
	CreatedAt     time.Time              `json:"created_at"`
	LastHeartbeat time.Time              `json:"last_heartbeat"`
}

// ServiceRegistry 服务注册表
type ServiceRegistry struct {
	mu           sync.RWMutex
	instances    map[string]*ServiceInstance   // id -> instance
	byService    map[string][]*ServiceInstance // service_name -> instances
	dependencies map[string][]string           // service -> dependencies
}

// NewServiceRegistry 创建服务注册表
func NewServiceRegistry() *ServiceRegistry {
	return &ServiceRegistry{
		instances:    make(map[string]*ServiceInstance),
		byService:    make(map[string][]*ServiceInstance),
		dependencies: make(map[string][]string),
	}
}

// Register 注册服务实例
func (r *ServiceRegistry) Register(instance *ServiceInstance) {
	r.mu.Lock()
	defer r.mu.Unlock()

	r.instances[instance.ID] = instance
	r.byService[instance.ServiceName] = append(r.byService[instance.ServiceName], instance)

	// 只在未设置时才初始化时间戳
	if instance.CreatedAt.IsZero() {
		instance.CreatedAt = time.Now()
	}
	if instance.LastHeartbeat.IsZero() {
		instance.LastHeartbeat = time.Now()
	}
}

// GetByID 根据ID获取实例
func (r *ServiceRegistry) GetByID(id string) *ServiceInstance {
	r.mu.RLock()
	defer r.mu.RUnlock()
	return r.instances[id]
}

// GetByService 根据服务名获取所有实例
func (r *ServiceRegistry) GetByService(serviceName string) []*ServiceInstance {
	r.mu.RLock()
	defer r.mu.RUnlock()

	instances := r.byService[serviceName]
	result := make([]*ServiceInstance, 0, len(instances))
	for _, inst := range instances {
		result = append(result, inst)
	}
	return result
}

// GetAll 获取所有实例
func (r *ServiceRegistry) GetAll() []*ServiceInstance {
	r.mu.RLock()
	defer r.mu.RUnlock()

	result := make([]*ServiceInstance, 0, len(r.instances))
	for _, inst := range r.instances {
		result = append(result, inst)
	}
	return result
}

// Count 返回实例总数
func (r *ServiceRegistry) Count() int {
	r.mu.RLock()
	defer r.mu.RUnlock()
	return len(r.instances)
}

// Delete 删除服务实例
func (r *ServiceRegistry) Delete(id string) bool {
	r.mu.Lock()
	defer r.mu.Unlock()

	inst, exists := r.instances[id]
	if !exists {
		return false
	}

	// 从服务列表中移除
	services := r.byService[inst.ServiceName]
	for i, svc := range services {
		if svc.ID == id {
			r.byService[inst.ServiceName] = append(services[:i], services[i+1:]...)
			break
		}
	}

	delete(r.instances, id)
	return true
}

// Update 更新服务实例
func (r *ServiceRegistry) Update(instance *ServiceInstance) bool {
	r.mu.Lock()
	defer r.mu.Unlock()

	if _, exists := r.instances[instance.ID]; !exists {
		return false
	}

	// 更新实例
	r.instances[instance.ID] = instance

	// 更新byService索引
	for i, inst := range r.byService[instance.ServiceName] {
		if inst.ID == instance.ID {
			r.byService[instance.ServiceName][i] = instance
			break
		}
	}

	return true
}

// SetDependencies 设置服务依赖
func (r *ServiceRegistry) SetDependencies(service string, dependencies []string) {
	r.mu.Lock()
	defer r.mu.Unlock()

	r.dependencies[service] = dependencies
}

// GetDependencies 获取服务依赖
func (r *ServiceRegistry) GetDependencies(service string) []string {
	r.mu.RLock()
	defer r.mu.RUnlock()

	return r.dependencies[service]
}

// GetAllDependencies 获取所有依赖关系
func (r *ServiceRegistry) GetAllDependencies() map[string][]string {
	r.mu.RLock()
	defer r.mu.RUnlock()

	result := make(map[string][]string, len(r.dependencies))
	for k, v := range r.dependencies {
		result[k] = v
	}
	return result
}

// UpdateHeartbeat 更新心跳时间
func (r *ServiceRegistry) UpdateHeartbeat(id string) {
	r.mu.Lock()
	defer r.mu.Unlock()

	if inst, exists := r.instances[id]; exists {
		inst.LastHeartbeat = time.Now()
	}
}

// GetHealthyInstances 获取健康的服务实例
func (r *ServiceRegistry) GetHealthyInstances(serviceName string) []*ServiceInstance {
	instances := r.GetByService(serviceName)
	healthy := make([]*ServiceInstance, 0)

	for _, inst := range instances {
		// 35分钟超时以匹配30分钟心跳间隔
		if inst.Status == "UP" && time.Since(inst.LastHeartbeat) < 35*time.Minute {
			healthy = append(healthy, inst)
		}
	}

	return healthy
}

// SelectInstance 选择一个实例（简单轮询）
func (r *ServiceRegistry) SelectInstance(serviceName string) *ServiceInstance {
	instances := r.GetHealthyInstances(serviceName)
	if len(instances) == 0 {
		return nil
	}

	// 简单的轮询算法
	// 实际应用中可以使用加权轮询、最少连接等算法
	// 这里使用一个静态指针来实现
	pointer := r.getPointer(serviceName)
	idx := int(pointer % uint64(len(instances)))

	r.setPointer(serviceName, pointer+1)

	return instances[idx]
}

// 指针管理（用于轮询）
type registryPointer struct {
	pointer uint64
}

var (
	pointers      = make(map[string]*registryPointer)
	pointersLock sync.Mutex
)

func (r *ServiceRegistry) getPointer(serviceName string) uint64 {
	pointersLock.Lock()
	defer pointersLock.Unlock()

	if ptr, exists := pointers[serviceName]; exists {
		return ptr.pointer
	}

	ptr := &registryPointer{pointer: 0}
	pointers[serviceName] = ptr
	return 0
}

func (r *ServiceRegistry) setPointer(serviceName string, pointer uint64) {
	pointersLock.Lock()
	defer pointersLock.Unlock()

	if ptr, exists := pointers[serviceName]; exists {
		ptr.pointer = pointer
	}
}
