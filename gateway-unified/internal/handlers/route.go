// Package handlers - 路由管理API
package handlers

import (
	"net/http"

	"github.com/gin-gonic/gin"
	"github.com/athena-workspace/gateway-unified/internal/logging"
)

// RouteHandler 路由管理API处理器
type RouteHandler struct {
	registry *ServiceRegistry
}

// NewRouteHandler 创建路由管理处理器
func NewRouteHandler(registry *ServiceRegistry) *RouteHandler {
	return &RouteHandler{
		registry: registry,
	}
}

// ListRoutes 列出所有路由
// @Summary 列出所有路由
// @Tags routes
// @Produce json
// @Success 200 {object} map[string]interface{} "成功响应"
// @Router /api/v1/routes [get]
func (h *RouteHandler) ListRoutes(c *gin.Context) {
	h.registry.mu.RLock()
	defer h.registry.mu.RUnlock()

	routes := make([]*RouteRule, 0, len(h.registry.routes))
	for _, route := range h.registry.routes {
		routes = append(routes, route)
	}

	c.JSON(http.StatusOK, gin.H{
		"success": true,
		"data":     routes,
	})
}

// CreateRoute 创建路由
// @Summary 创建路由
// @Tags routes
// @Accept json
// @Produce json
// @Param request body RouteRule true "路由规则"
// @Success 200 {object} map[string]interface{} "成功响应"
// @Failure 400 {object} map[string]interface{} "错误响应"
// @Router /api/v1/routes [post]
func (h *RouteHandler) CreateRoute(c *gin.Context) {
	var route RouteRule
	if err := c.ShouldBindJSON(&route); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{
			"success": false,
			"error":   err.Error(),
		})
		return
	}

	// 检查路由ID是否已存在
	h.registry.mu.Lock()
	defer h.registry.mu.Unlock()

	if _, exists := h.registry.routes[route.ID]; exists {
		c.JSON(http.StatusBadRequest, gin.H{
			"success": false,
			"error":   "Route ID already exists",
		})
		return
	}

	// 验证目标服务是否存在
	hasTarget := false
	for _, inst := range h.registry.instances {
		if inst.ServiceName == route.TargetService {
			hasTarget = true
			break
		}
	}

	if !hasTarget {
		c.JSON(http.StatusBadRequest, gin.H{
			"success": false,
			"error":   "Target service not found",
		})
		return
	}

	// 设置默认值
	if route.Methods == nil || len(route.Methods) == 0 {
		route.Methods = []string{"GET"}
	}
	if route.Weight == 0 {
		route.Weight = 1
	}
	route.Enabled = true

	h.registry.routes[route.ID] = &route

	logging.LogInfo("路由创建",
		logging.String("route_id", route.ID),
		logging.String("path", route.Path),
		logging.String("target_service", route.TargetService))

	c.JSON(http.StatusOK, gin.H{
		"success": true,
		"data":     route,
	})
}

// UpdateRoute 更新路由
// @Summary 更新路由
// @Tags routes
// @Accept json
// @Produce json
// @Param route_id path string true "路由ID"
// @Param request body RouteRule true "路由规则"
// @Success 200 {object} map[string]interface{} "成功响应"
// @Failure 404 {object} map[string]interface{} "路由不存在"
// @Router /api/v1/routes/{route_id} [patch]
func (h *RouteHandler) UpdateRoute(c *gin.Context) {
	routeID := c.Param("route_id")

	var route RouteRule
	if err := c.ShouldBindJSON(&route); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{
			"success": false,
			"error":   err.Error(),
		})
		return
	}

	h.registry.mu.Lock()
	defer h.registry.mu.Unlock()

	existing, exists := h.registry.routes[routeID]
	if !exists {
		c.JSON(http.StatusNotFound, gin.H{
			"success": false,
			"error":   "Route not found",
		})
		return
	}

	// 更新字段
	if route.Path != "" && route.Path != existing.Path {
		existing.Path = route.Path
	}
	if route.TargetService != "" {
		existing.TargetService = route.TargetService
	}
	if route.Methods != nil {
		existing.Methods = route.Methods
	}
	if route.Weight > 0 {
		existing.Weight = route.Weight
	}
	existing.Enabled = route.Enabled

	logging.LogInfo("路由更新",
		logging.String("route_id", routeID))

	c.JSON(http.StatusOK, gin.H{
		"success": true,
		"data":     existing,
	})
}

// DeleteRoute 删除路由
// @Summary 删除路由
// @Tags routes
// @Produce json
// @Param route_id path string true "路由ID"
// @Success 200 {object} map[string]interface{} "成功响应"
// @Failure 404 {object} map[string]interface{} "路由不存在"
// @Router /api/v1/routes/{route_id} [delete]
func (h *RouteHandler) DeleteRoute(c *gin.Context) {
	routeID := c.Param("route_id")

	h.registry.mu.Lock()
	defer h.registry.mu.Unlock()

	if _, exists := h.registry.routes[routeID]; !exists {
		c.JSON(http.StatusNotFound, gin.H{
			"success": false,
			"error":   "Route not found",
		})
		return
	}

	delete(h.registry.routes, routeID)

	logging.LogInfo("路由删除",
		logging.String("route_id", routeID))

	c.JSON(http.StatusOK, gin.H{
		"success": true,
		"data": gin.H{
			"deleted": routeID,
		},
	})
}

// FindRoute 根据路径和方法查找路由
func (h *RouteHandler) FindRoute(path string, method string) *RouteRule {
	h.registry.mu.RLock()
	defer h.registry.mu.RUnlock()

	for _, route := range h.registry.routes {
		if !route.Enabled {
			continue
		}
		if route.Path == path {
			// 检查方法是否匹配
			for _, m := range route.Methods {
				if m == method || m == "*" {
					return route
				}
			}
		}
	}
	return nil
}

// GetRouteCount 获取路由总数
func (h *RouteHandler) GetRouteCount() int {
	h.registry.mu.RLock()
	defer h.registry.mu.RUnlock()
	return len(h.registry.routes)
}
