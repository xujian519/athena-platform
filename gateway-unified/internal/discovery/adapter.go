// Package discovery - 服务发现适配器
// 实现Gateway与service_discovery.json的集成，提供动态服务注册和健康检查
package discovery

import (
	"context"
	"encoding/json"
	"fmt"
	"log"
	"os"
	"sync"
	"time"
)

// ServiceDiscoveryConfig 服务发现配置
type ServiceDiscoveryConfig struct {
	ConfigPath     string        `yaml:"config_path" json:"config_path"`
	ScanInterval   time.Duration `yaml:"scan_interval" json:"scan_interval"`
	AutoRegister   bool          `yaml:"auto_register" json:"auto_register"`
	HealthCheck    bool          `yaml:"health_check" json:"health_check"`
	HealthEndpoint string        `yaml:"health_endpoint" json:"health_endpoint"`
}

// ServiceInstance 服务实例（避免循环导入）
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

// Registry 服务注册表接口（避免循环导入）
type Registry interface {
	Register(instance *ServiceInstance)
	GetByID(id string) *ServiceInstance
	GetAll() []*ServiceInstance
	Count() int
	Delete(id string) bool
	Update(instance *ServiceInstance) bool
}

// Adapter 服务发现适配器
// 负责从配置文件加载服务信息并同步到Gateway的服务注册表
type Adapter struct {
	config        *ServiceDiscoveryConfig
	registry      Registry
	configData    *ServiceDiscoveryFile
	ctx           context.Context
	cancel        context.CancelFunc
	healthChecker *HealthChecker
	mu            sync.RWMutex
}

// ServiceDiscoveryFile 服务发现配置文件结构
// 对应config/service_discovery.json的格式
type ServiceDiscoveryFile struct {
	Services []ServiceInfo `json:"services"`
}

// ServiceInfo 服务信息
// 从service_discovery.json中读取的服务配置
type ServiceInfo struct {
	Name           string                 `json:"name"`
	Type           string                 `json:"type"`
	Provider       string                 `json:"provider"`
	Protocol       string                 `json:"protocol"`
	Enabled        bool                   `json:"enabled"`
	Port           int                    `json:"port,omitempty"`
	BaseURL        string                 `json:"base_url,omitempty"`
	HealthEndpoint string                 `json:"health_endpoint,omitempty"`
	Description    string                 `json:"description"`
	Metadata       map[string]interface{} `json:"metadata,omitempty"`
}

// NewAdapter 创建服务发现适配器
func NewAdapter(
	config *ServiceDiscoveryConfig,
	registry Registry,
) *Adapter {
	ctx, cancel := context.WithCancel(context.Background())

	adapter := &Adapter{
		config:        config,
		registry:      registry,
		ctx:           ctx,
		cancel:        cancel,
		healthChecker: NewHealthChecker(config),
	}

	return adapter
}

// LoadConfig 加载服务发现配置文件
// 从config/service_discovery.json读取服务配置
func (a *Adapter) LoadConfig() error {
	data, err := os.ReadFile(a.config.ConfigPath)
	if err != nil {
		return fmt.Errorf("读取配置文件失败: %w", err)
	}

	var configData ServiceDiscoveryFile
	if err := json.Unmarshal(data, &configData); err != nil {
		return fmt.Errorf("解析配置文件失败: %w", err)
	}

	a.mu.Lock()
	a.configData = &configData
	a.mu.Unlock()

	log.Printf("[服务发现] 配置加载完成: %s (%d个服务)",
		a.config.ConfigPath, len(configData.Services))

	return nil
}

// SyncServices 同步服务到注册表
// 根据配置文件更新服务注册表，添加新服务、更新现有服务、删除不存在服务
func (a *Adapter) SyncServices() error {
	a.mu.RLock()
	if a.configData == nil {
		a.mu.RUnlock()
		if err := a.LoadConfig(); err != nil {
			return err
		}
	} else {
		a.mu.RUnlock()
	}

	a.mu.RLock()
	configData := a.configData
	a.mu.RUnlock()

	// 获取当前已注册的服务ID集合
	registeredIDs := make(map[string]bool)
	for _, instance := range a.registry.GetAll() {
		registeredIDs[instance.ID] = true
	}

	// 注册或更新服务
	addedCount := 0
	updatedCount := 0
	for _, svc := range configData.Services {
		if !svc.Enabled {
			continue
		}

		// 生成服务实例
		instance := a.createInstance(svc)

		// 检查是否已注册
		existing := a.registry.GetByID(instance.ID)
		if existing != nil {
			// 更新现有服务
			a.registry.Update(instance)
			updatedCount++
			log.Printf("[服务发现] 服务已更新: %s (id=%s)", instance.ServiceName, instance.ID)
		} else {
			// 注册新服务
			a.registry.Register(instance)
			addedCount++
			log.Printf("[服务发现] 服务已注册: %s (id=%s, host=%s, port=%d)",
				instance.ServiceName, instance.ID, instance.Host, instance.Port)
		}

		delete(registeredIDs, instance.ID)
	}

	// 注销不再存在的服务
	removedCount := 0
	for id := range registeredIDs {
		a.registry.Delete(id)
		removedCount++
		log.Printf("[服务发现] 服务已注销: id=%s", id)
	}

	log.Printf("[服务发现] 同步完成: 新增=%d, 更新=%d, 移除=%d, 总计=%d",
		addedCount, updatedCount, removedCount, a.registry.Count())

	return nil
}

// createInstance 从服务信息创建服务实例
func (a *Adapter) createInstance(svc ServiceInfo) *ServiceInstance {
	// 确定主机和端口
	host := "127.0.0.1"
	port := svc.Port

	// 从BaseURL解析主机和端口（如果提供）
	if svc.BaseURL != "" {
		// 简单解析，实际应用中可以使用url包
		// 例如: http://localhost:8101 -> localhost:8101
		// TODO: 实现完整的URL解析
	}

	// 生成实例ID (格式: serviceName:host:port:0)
	instanceID := fmt.Sprintf("%s:%s:%d:0", svc.Name, host, port)

	// 准备元数据
	metadata := map[string]interface{}{
		"type":        svc.Type,
		"provider":    svc.Provider,
		"protocol":    svc.Protocol,
		"description": svc.Description,
	}

	// 添加健康检查端点
	if svc.HealthEndpoint != "" {
		metadata["health_endpoint"] = svc.HealthEndpoint
	}

	// 合并自定义元数据
	for k, v := range svc.Metadata {
		metadata[k] = v
	}

	instance := &ServiceInstance{
		ID:          instanceID,
		ServiceName: svc.Name,
		Host:        host,
		Port:        port,
		Status:      "UP",
		Weight:      1,
		Metadata:    metadata,
		CreatedAt:   time.Now(),
		LastHeartbeat: time.Now(),
	}

	return instance
}

// Start 启动服务发现适配器
// 执行初始同步并启动后台定期同步和健康检查
func (a *Adapter) Start() error {
	// 初始同步
	if err := a.SyncServices(); err != nil {
		return fmt.Errorf("初始服务同步失败: %w", err)
	}

	// 启动定期同步
	go a.syncLoop()

	// 启动健康检查
	if a.config.HealthCheck {
		go a.healthCheckLoop()
	}

	return nil
}

// syncLoop 定期同步服务配置
// 按照ScanInterval间隔检查配置文件变化
func (a *Adapter) syncLoop() {
	ticker := time.NewTicker(a.config.ScanInterval)
	defer ticker.Stop()

	for {
		select {
		case <-ticker.C:
			if err := a.SyncServices(); err != nil {
				log.Printf("[服务发现] 同步失败: %v", err)
			}
		case <-a.ctx.Done():
			return
		}
	}
}

// healthCheckLoop 健康检查循环
// 定期检查所有已注册服务的健康状态
func (a *Adapter) healthCheckLoop() {
	// 使用更短的间隔进行健康检查
	checkInterval := 30 * time.Second
	if a.config.ScanInterval < checkInterval {
		checkInterval = a.config.ScanInterval
	}

	ticker := time.NewTicker(checkInterval)
	defer ticker.Stop()

	for {
		select {
		case <-ticker.C:
			a.checkAllServices()
		case <-a.ctx.Done():
			return
		}
	}
}

// checkAllServices 检查所有服务健康状态
// 遍历所有已注册服务，执行健康检查并更新状态
func (a *Adapter) checkAllServices() {
	instances := a.registry.GetAll()

	healthyCount := 0
	unhealthyCount := 0

	for _, instance := range instances {
		healthy := a.healthChecker.Check(instance)

		if healthy {
			if instance.Status != "UP" {
				instance.Status = "UP"
				log.Printf("[服务发现] 服务恢复健康: %s (id=%s)", instance.ServiceName, instance.ID)
			}
			healthyCount++
		} else {
			if instance.Status != "DOWN" {
				instance.Status = "DOWN"
				log.Printf("[服务发现] 服务不健康: %s (id=%s)", instance.ServiceName, instance.ID)
			}
			unhealthyCount++
		}
	}

	if unhealthyCount > 0 {
		log.Printf("[服务发现] 健康检查完成: 健康=%d, 不健康=%d", healthyCount, unhealthyCount)
	}
}

// GetRegistry 获取服务注册表
func (a *Adapter) GetRegistry() Registry {
	return a.registry
}

// Close 关闭适配器
// 停止后台同步和健康检查循环
func (a *Adapter) Close() error {
	a.cancel()
	log.Println("[服务发现] 适配器已关闭")
	return nil
}

// UpdateInstance 更新服务实例
// 用于动态更新服务的健康状态或其他属性
func (a *Adapter) UpdateInstance(instance *ServiceInstance) {
	existing := a.registry.GetByID(instance.ID)
	if existing != nil {
		existing.Status = instance.Status
		existing.Host = instance.Host
		existing.Port = instance.Port
		existing.Weight = instance.Weight
		if instance.Metadata != nil {
			if existing.Metadata == nil {
				existing.Metadata = make(map[string]interface{})
			}
			for k, v := range instance.Metadata {
				existing.Metadata[k] = v
			}
		}
	}
}
