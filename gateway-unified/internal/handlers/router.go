// Package handlers - API路由注册器
// 集成所有API处理器，统一注册路由
package handlers

import (
	"github.com/gin-gonic/gin"
)

// APIRegistry API注册器
type APIRegistry struct {
	serviceHandler    *ServiceHandler
	dependencyHandler *DependencyHandler
	routeHandler      *RouteHandler
	healthHandler     *HealthHandler
	configHandler     *ConfigHandler
	registry          *ServiceRegistry
}

// NewAPIRegistry 创建API注册器
func NewAPIRegistry(registry *ServiceRegistry) *APIRegistry {
	return &APIRegistry{
		serviceHandler:    NewServiceHandler(registry),
		dependencyHandler: NewDependencyHandler(registry),
		routeHandler:      NewRouteHandler(registry),
		healthHandler:     NewHealthHandler(registry),
		configHandler:     NewConfigHandler(),
		registry:          registry,
	}
}

// RegisterRoutes 注册所有API路由
func (r *APIRegistry) RegisterRoutes(router *gin.Engine) {
	// API v1路由组
	v1 := router.Group("/api/v1")
	{
		// 服务管理
		services := v1.Group("/services")
		{
			services.POST("/batch", r.serviceHandler.BatchRegister)
			services.GET("/instances", r.serviceHandler.ListInstances)
			services.GET("/instances/:inst_id", r.serviceHandler.GetInstance)
			services.PUT("/instances/:inst_id", r.serviceHandler.UpdateInstance)
			services.DELETE("/instances/:inst_id", r.serviceHandler.DeleteInstance)
		}

		// 路由管理
		routes := v1.Group("/routes")
		{
			routes.GET("", r.routeHandler.ListRoutes)
			routes.POST("", r.routeHandler.CreateRoute)
			routes.PATCH("/:route_id", r.routeHandler.UpdateRoute)
			routes.DELETE("/:route_id", r.routeHandler.DeleteRoute)
		}

		// 依赖管理
		deps := v1.Group("/dependencies")
		{
			deps.POST("", r.dependencyHandler.SetDependencies)
			deps.GET("/:service", r.dependencyHandler.GetDependencies)
			deps.GET("", r.dependencyHandler.GetAllDependencies)
			deps.DELETE("/:service", r.dependencyHandler.DeleteDependencies)
		}

		// 配置管理
		config := v1.Group("/config")
		{
			config.POST("/load", r.configHandler.LoadConfig)
			config.GET("", r.configHandler.GetConfig)
			config.POST("/reload", r.configHandler.ReloadConfig)
		}
	}

	// 健康检查和系统状态（不在/api/v1下）
	{
		router.GET("/health", r.healthHandler.Health)
		router.GET("/ready", r.healthHandler.Ready)
		router.GET("/live", r.healthHandler.Live)
		router.POST("/api/v1/health/alerts", r.healthHandler.HealthAlert)
	}
}

// GetServiceHandler 获取服务处理器
func (r *APIRegistry) GetServiceHandler() *ServiceHandler {
	return r.serviceHandler
}

// GetDependencyHandler 获取依赖处理器
func (r *APIRegistry) GetDependencyHandler() *DependencyHandler {
	return r.dependencyHandler
}

// GetRouteHandler 获取路由处理器
func (r *APIRegistry) GetRouteHandler() *RouteHandler {
	return r.routeHandler
}

// GetHealthHandler 获取健康检查处理器
func (r *APIRegistry) GetHealthHandler() *HealthHandler {
	return r.healthHandler
}

// GetRegistry 获取服务注册表
func (r *APIRegistry) GetRegistry() *ServiceRegistry {
	return r.registry
}
