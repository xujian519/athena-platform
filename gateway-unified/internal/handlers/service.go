// Package handlers - Gateway API处理器
// 提供服务注册、路由管理、依赖管理等API端点
package handlers

import (
	"fmt"
	"net/http"
	"sync"

	"github.com/gin-gonic/gin"
	"github.com/athena-workspace/gateway-unified/internal/logging"
)

// ServiceRegistry 服务注册表（线程安全）
type ServiceRegistry struct {
	mu         sync.RWMutex
	instances  map[string]*ServiceInstance
	routes     map[string]*RouteRule
	dependencies map[string][]string
	counter    uint64
}

// NewServiceRegistry 创建服务注册表
func NewServiceRegistry() *ServiceRegistry {
	return &ServiceRegistry{
		instances:    make(map[string]*ServiceInstance),
		routes:       make(map[string]*RouteRule),
		dependencies: make(map[string][]string),
	}
}

// ServiceInstance 服务实例
type ServiceInstance struct {
	ID          string                 `json:"id"`
	ServiceName string                 `json:"service_name"`
	Host        string                 `json:"host"`
	Port        int                    `json:"port"`
	Weight      int                    `json:"weight"`
	Status      string                 `json:"status"`
	Metadata    map[string]interface{} `json:"metadata"`
}

// ServiceRegistration 服务注册请求
type ServiceRegistration struct {
	Name     string                 `json:"name" binding:"required"`
	Host     string                 `json:"host" binding:"required"`
	Port     int                    `json:"port" binding:"required,min=1,max=65535"`
	Metadata map[string]interface{} `json:"metadata"`
}

// BatchRegisterRequest 批量注册请求
type BatchRegisterRequest struct {
	Services []ServiceRegistration `json:"services" binding:"required,min=1"`
}

// UpdateServiceInstance 更新服务实例请求
type UpdateServiceInstance struct {
	Host     *string                `json:"host"`
	Port     *int                   `json:"port"`
	Weight   *int                   `json:"weight"`
	Metadata *map[string]interface{} `json:"metadata"`
}

// RouteRule 路由规则
type RouteRule struct {
	ID             string   `json:"id"`
	Path           string   `json:"path" binding:"required"`
	TargetService  string   `json:"target_service" binding:"required"`
	Methods        []string `json:"methods"`
	Weight         int      `json:"weight"`
	Enabled        bool     `json:"enabled"`
}

// ServiceHandler 服务API处理器
type ServiceHandler struct {
	registry *ServiceRegistry
}

// NewServiceHandler 创建服务API处理器
func NewServiceHandler(registry *ServiceRegistry) *ServiceHandler {
	return &ServiceHandler{
		registry: registry,
	}
}

// BatchRegister 批量注册服务
// @Summary 批量注册服务实例
// @Tags services
// @Accept json
// @Produce json
// @Param request body BatchRegisterRequest true "批量注册请求"
// @Success 200 {object} map[string]interface{} "成功响应"
// @Router /api/v1/services/batch [post]
func (h *ServiceHandler) BatchRegister(c *gin.Context) {
	var req BatchRegisterRequest
	if err := c.ShouldBindJSON(&req); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{
			"success": false,
			"error":   err.Error(),
		})
		return
	}

	h.registry.mu.Lock()
	defer h.registry.mu.Unlock()

	results := make([]*ServiceInstance, 0, len(req.Services))

	for _, svc := range req.Services {
		h.registry.counter++
		instanceID := fmt.Sprintf("%s:%s:%d:%d", svc.Name, svc.Host, svc.Port, h.registry.counter)

		instance := &ServiceInstance{
			ID:          instanceID,
			ServiceName: svc.Name,
			Host:        svc.Host,
			Port:        svc.Port,
			Weight:      1,
			Status:      "UP",
			Metadata:    svc.Metadata,
		}

		h.registry.instances[instanceID] = instance
		results = append(results, instance)

		logging.LogInfo("服务实例注册",
			logging.String("instance_id", instanceID),
			logging.String("service_name", svc.Name))
	}

	c.JSON(http.StatusOK, gin.H{
		"success": true,
		"data":     results,
	})
}

// ListInstances 列出所有服务实例
// @Summary 列出所有服务实例
// @Tags services
// @Produce json
// @Success 200 {object} map[string]interface{} "成功响应"
// @Router /api/v1/services/instances [get]
func (h *ServiceHandler) ListInstances(c *gin.Context) {
	h.registry.mu.RLock()
	defer h.registry.mu.RUnlock()

	instances := make([]*ServiceInstance, 0, len(h.registry.instances))
	for _, inst := range h.registry.instances {
		instances = append(instances, inst)
	}

	c.JSON(http.StatusOK, gin.H{
		"success": true,
		"data":     instances,
	})
}

// GetInstance 获取单个服务实例
// @Summary 获取服务实例详情
// @Tags services
// @Produce json
// @Param inst_id path string true "实例ID"
// @Success 200 {object} map[string]interface{} "成功响应"
// @Failure 404 {object} map[string]interface{} "实例不存在"
// @Router /api/v1/services/instances/{inst_id} [get]
func (h *ServiceHandler) GetInstance(c *gin.Context) {
	instID := c.Param("inst_id")

	h.registry.mu.RLock()
	inst, exists := h.registry.instances[instID]
	h.registry.mu.RUnlock()

	if !exists {
		c.JSON(http.StatusNotFound, gin.H{
			"success": false,
			"error":   "Instance not found",
		})
		return
	}

	c.JSON(http.StatusOK, gin.H{
		"success": true,
		"data":     inst,
	})
}

// UpdateInstance 更新服务实例
// @Summary 更新服务实例
// @Tags services
// @Accept json
// @Produce json
// @Param inst_id path string true "实例ID"
// @Param request body UpdateServiceInstance true "更新请求"
// @Success 200 {object} map[string]interface{} "成功响应"
// @Failure 404 {object} map[string]interface{} "实例不存在"
// @Router /api/v1/services/instances/{inst_id} [put]
func (h *ServiceHandler) UpdateInstance(c *gin.Context) {
	instID := c.Param("inst_id")

	var req UpdateServiceInstance
	if err := c.ShouldBindJSON(&req); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{
			"success": false,
			"error":   err.Error(),
		})
		return
	}

	h.registry.mu.Lock()
	defer h.registry.mu.Unlock()

	inst, exists := h.registry.instances[instID]
	if !exists {
		c.JSON(http.StatusNotFound, gin.H{
			"success": false,
			"error":   "Instance not found",
		})
		return
	}

	// 更新字段
	if req.Host != nil {
		inst.Host = *req.Host
	}
	if req.Port != nil {
		inst.Port = *req.Port
	}
	if req.Weight != nil {
		inst.Weight = *req.Weight
	}
	if req.Metadata != nil {
		if inst.Metadata == nil {
			inst.Metadata = make(map[string]interface{})
		}
		for k, v := range *req.Metadata {
			inst.Metadata[k] = v
		}
	}

	logging.LogInfo("服务实例更新",
		logging.String("instance_id", instID))

	c.JSON(http.StatusOK, gin.H{
		"success": true,
		"data":     inst,
	})
}

// DeleteInstance 删除服务实例
// @Summary 删除服务实例
// @Tags services
// @Produce json
// @Param inst_id path string true "实例ID"
// @Success 200 {object} map[string]interface{} "成功响应"
// @Failure 404 {object} map[string]interface{} "实例不存在"
// @Router /api/v1/services/instances/{inst_id} [delete]
func (h *ServiceHandler) DeleteInstance(c *gin.Context) {
	instID := c.Param("inst_id")

	h.registry.mu.Lock()
	defer h.registry.mu.Unlock()

	if _, exists := h.registry.instances[instID]; !exists {
		c.JSON(http.StatusNotFound, gin.H{
			"success": false,
			"error":   "Instance not found",
		})
		return
	}

	delete(h.registry.instances, instID)

	logging.LogInfo("服务实例删除",
		logging.String("instance_id", instID))

	c.JSON(http.StatusOK, gin.H{
		"success": true,
		"data": gin.H{
			"deleted": instID,
		},
	})
}

// GetHealthyInstances 获取健康的服务实例
func (h *ServiceHandler) GetHealthyInstances(serviceName string) []*ServiceInstance {
	h.registry.mu.RLock()
	defer h.registry.mu.RUnlock()

	instances := make([]*ServiceInstance, 0)
	for _, inst := range h.registry.instances {
		if inst.ServiceName == serviceName && inst.Status == "UP" {
			instances = append(instances, inst)
		}
	}
	return instances
}

// GetInstanceCount 获取服务实例总数
func (h *ServiceHandler) GetInstanceCount() int {
	h.registry.mu.RLock()
	defer h.registry.mu.RUnlock()
	return len(h.registry.instances)
}

// GetRegistry 获取注册表（用于路由选择）
func (h *ServiceHandler) GetRegistry() *ServiceRegistry {
	return h.registry
}
