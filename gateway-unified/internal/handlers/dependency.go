// Package handlers - 依赖关系管理API
package handlers

import (
	"net/http"

	"github.com/gin-gonic/gin"
	"github.com/athena-workspace/gateway-unified/internal/logging"
)

// DependencySpec 依赖规范
type DependencySpec struct {
	Service    string   `json:"service" binding:"required"`
	DependsOn  []string `json:"depends_on"`
}

// DependencyHandler 依赖管理API处理器
type DependencyHandler struct {
	registry *ServiceRegistry
}

// NewDependencyHandler 创建依赖管理处理器
func NewDependencyHandler(registry *ServiceRegistry) *DependencyHandler {
	return &DependencyHandler{
		registry: registry,
	}
}

// SetDependencies 设置服务依赖关系
// @Summary 设置服务依赖关系
// @Tags dependencies
// @Accept json
// @Produce json
// @Param request body DependencySpec true "依赖规范"
// @Success 200 {object} map[string]interface{} "成功响应"
// @Router /api/v1/dependencies [post]
func (h *DependencyHandler) SetDependencies(c *gin.Context) {
	var req DependencySpec
	if err := c.ShouldBindJSON(&req); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{
			"success": false,
			"error":   err.Error(),
		})
		return
	}

	h.registry.mu.Lock()
	defer h.registry.mu.Unlock()

	// 初始化依赖列表（如果不存在）
	if h.registry.dependencies[req.Service] == nil {
		h.registry.dependencies[req.Service] = make([]string, 0)
	}

	// 添加新的依赖（避免重复）
	for _, dep := range req.DependsOn {
		exists := false
		for _, existing := range h.registry.dependencies[req.Service] {
			if existing == dep {
				exists = true
				break
			}
		}
		if !exists {
			h.registry.dependencies[req.Service] = append(h.registry.dependencies[req.Service], dep)
		}
	}

	logging.LogInfo("服务依赖设置",
		logging.String("service", req.Service),
		logging.Strings("dependencies", req.DependsOn))

	c.JSON(http.StatusOK, gin.H{
		"success": true,
		"data": gin.H{
			"service":      req.Service,
			"dependencies": h.registry.dependencies[req.Service],
		},
	})
}

// GetDependencies 获取服务依赖关系
// @Summary 获取服务依赖关系
// @Tags dependencies
// @Produce json
// @Param service path string true "服务名"
// @Success 200 {object} map[string]interface{} "成功响应"
// @Router /api/v1/dependencies/{service} [get]
func (h *DependencyHandler) GetDependencies(c *gin.Context) {
	service := c.Param("service")

	h.registry.mu.RLock()
	deps, exists := h.registry.dependencies[service]
	h.registry.mu.RUnlock()

	if !exists {
		deps = []string{}
	}

	c.JSON(http.StatusOK, gin.H{
		"success": true,
		"data": gin.H{
			"service":      service,
			"dependencies": deps,
		},
	})
}

// GetAllDependencies 获取所有依赖关系
// @Summary 获取所有依赖关系
// @Tags dependencies
// @Produce json
// @Success 200 {object} map[string]interface{} "成功响应"
// @Router /api/v1/dependencies [get]
func (h *DependencyHandler) GetAllDependencies(c *gin.Context) {
	h.registry.mu.RLock()
	defer h.registry.mu.RUnlock()

	// 创建依赖关系图的副本
	depsCopy := make(map[string][]string, len(h.registry.dependencies))
	for service, deps := range h.registry.dependencies {
		depsCopy[service] = make([]string, len(deps))
		copy(depsCopy[service], deps)
	}

	c.JSON(http.StatusOK, gin.H{
		"success": true,
		"data":     depsCopy,
	})
}

// CheckDependencies 检查服务依赖是否满足
// 返回未满足的依赖列表
func (h *DependencyHandler) CheckDependencies(service string) []string {
	h.registry.mu.RLock()
	defer h.registry.mu.RUnlock()

	var missing []string

	deps := h.registry.dependencies[service]
	for _, dep := range deps {
		// 检查依赖服务是否有健康的实例
		hasHealthy := false
		for _, inst := range h.registry.instances {
			if inst.ServiceName == dep && inst.Status == "UP" {
				hasHealthy = true
				break
			}
		}
		if !hasHealthy {
			missing = append(missing, dep)
		}
	}

	return missing
}

// ValidateDependencies 验证所有服务的依赖关系
// 返回依赖关系问题的服务列表
func (h *DependencyHandler) ValidateDependencies() map[string][]string {
	h.registry.mu.RLock()
	defer h.registry.mu.RUnlock()

	issues := make(map[string][]string)

	// 检查每个服务的依赖
	for service, deps := range h.registry.dependencies {
		var missing []string
		for _, dep := range deps {
			hasHealthy := false
			for _, inst := range h.registry.instances {
				if inst.ServiceName == dep && inst.Status == "UP" {
					hasHealthy = true
					break
				}
			}
			if !hasHealthy {
				missing = append(missing, dep)
			}
		}

		if len(missing) > 0 {
			issues[service] = missing
		}
	}

	return issues
}

// DeleteDependencies 删除服务依赖关系
// @Summary 删除服务依赖关系
// @Tags dependencies
// @Produce json
// @Param service path string true "服务名"
// @Success 200 {object} map[string]interface{} "成功响应"
// @Router /api/v1/dependencies/{service} [delete]
func (h *DependencyHandler) DeleteDependencies(c *gin.Context) {
	service := c.Param("service")

	h.registry.mu.Lock()
	defer h.registry.mu.Unlock()

	if _, exists := h.registry.dependencies[service]; exists {
		delete(h.registry.dependencies, service)

		logging.LogInfo("服务依赖删除",
			logging.String("service", service))

		c.JSON(http.StatusOK, gin.H{
			"success": true,
			"data": gin.H{
				"deleted": service,
			},
		})
		return
	}

	c.JSON(http.StatusNotFound, gin.H{
		"success": false,
		"error":   "Dependencies not found",
	})
}
