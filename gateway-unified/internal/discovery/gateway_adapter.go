// Package discovery - Gateway注册表适配器
// 用于桥接discovery.Registry接口和gateway.ServiceRegistry实现
package discovery

import (
	"github.com/athena-workspace/gateway-unified/internal/gateway"
)

// GatewayRegistryAdapter 适配器，让gateway.ServiceRegistry实现discovery.Registry接口
// 用于服务发现模块调用
type GatewayRegistryAdapter struct {
	registry *gateway.ServiceRegistry
}

// NewGatewayRegistryAdapter 创建Gateway注册表适配器
func NewGatewayRegistryAdapter(registry *gateway.ServiceRegistry) *GatewayRegistryAdapter {
	return &GatewayRegistryAdapter{
		registry: registry,
	}
}

// Register 注册服务实例
func (a *GatewayRegistryAdapter) Register(instance *ServiceInstance) {
	// 转换discovery.ServiceInstance到gateway.ServiceInstance
	gwInstance := &gateway.ServiceInstance{
		ID:            instance.ID,
		ServiceName:   instance.ServiceName,
		Host:          instance.Host,
		Port:          instance.Port,
		Weight:        instance.Weight,
		Status:        instance.Status,
		Metadata:      instance.Metadata,
		CreatedAt:     instance.CreatedAt,
		LastHeartbeat: instance.LastHeartbeat,
	}

	a.registry.Register(gwInstance)
}

// GetByID 根据ID获取实例
func (a *GatewayRegistryAdapter) GetByID(id string) *ServiceInstance {
	gwInstance := a.registry.GetByID(id)
	if gwInstance == nil {
		return nil
	}

	return a.convertToDiscoveryInstance(gwInstance)
}

// GetAll 获取所有实例
func (a *GatewayRegistryAdapter) GetAll() []*ServiceInstance {
	gwInstances := a.registry.GetAll()
	instances := make([]*ServiceInstance, 0, len(gwInstances))

	for _, gwInst := range gwInstances {
		instances = append(instances, a.convertToDiscoveryInstance(gwInst))
	}

	return instances
}

// Count 返回实例总数
func (a *GatewayRegistryAdapter) Count() int {
	return a.registry.Count()
}

// Delete 删除服务实例
func (a *GatewayRegistryAdapter) Delete(id string) bool {
	return a.registry.Delete(id)
}

// Update 更新服务实例
func (a *GatewayRegistryAdapter) Update(instance *ServiceInstance) bool {
	// 转换discovery.ServiceInstance到gateway.ServiceInstance
	gwInstance := &gateway.ServiceInstance{
		ID:            instance.ID,
		ServiceName:   instance.ServiceName,
		Host:          instance.Host,
		Port:          instance.Port,
		Weight:        instance.Weight,
		Status:        instance.Status,
		Metadata:      instance.Metadata,
		CreatedAt:     instance.CreatedAt,
		LastHeartbeat: instance.LastHeartbeat,
	}

	return a.registry.Update(gwInstance)
}

// convertToDiscoveryInstance 转换gateway.ServiceInstance到discovery.ServiceInstance
func (a *GatewayRegistryAdapter) convertToDiscoveryInstance(gwInst *gateway.ServiceInstance) *ServiceInstance {
	return &ServiceInstance{
		ID:            gwInst.ID,
		ServiceName:   gwInst.ServiceName,
		Host:          gwInst.Host,
		Port:          gwInst.Port,
		Weight:        gwInst.Weight,
		Status:        gwInst.Status,
		Metadata:      gwInst.Metadata,
		CreatedAt:     gwInst.CreatedAt,
		LastHeartbeat: gwInst.LastHeartbeat,
	}
}

// GetGatewayRegistry 获取底层的Gateway注册表
func (a *GatewayRegistryAdapter) GetGatewayRegistry() *gateway.ServiceRegistry {
	return a.registry
}
